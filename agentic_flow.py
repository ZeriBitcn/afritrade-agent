from typing import TypedDict, List, Dict, Any, Optional
import os
import re
import json
import httpx
from langgraph.graph import StateGraph, END

# Import tools
from tools import tariff_search_tool, route_finder_tool

# Define State Schema
class AgentState(TypedDict):
    query: str
    gemini_api_key: Optional[str]
    neo4j_config: Optional[dict]
    
    # Router extracted parameters
    route_requested: bool
    tariff_requested: bool
    start_hub: Optional[str]
    end_hub: Optional[str]
    commodity: Optional[str]
    
    # Tool outputs
    tariff_results: List[dict]
    route_results: dict
    
    # Reasoning execution logs
    steps: List[str]
    
    # Final answer
    final_answer: str

# Helper to call Gemini API
# Uses gemini-2.5-flash with automatic retry on 429 quota errors
_GEMINI_MODEL = "gemini-2.5-flash"

def call_gemini(prompt: str, api_key: str, system_instruction: str = None, max_retries: int = 3) -> str:
    import time
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{_GEMINI_MODEL}:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

    for attempt in range(max_retries):
        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
            if response.status_code == 200:
                res_json = response.json()
                candidates = res_json.get("candidates", [])
                if candidates:
                    text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    return text.strip()
                return "Error: Empty generation response from Gemini."
            elif response.status_code == 429:
                # Quota exceeded — extract retry delay and wait
                try:
                    retry_info = response.json()
                    delay_str = ""
                    for detail in retry_info.get("error", {}).get("details", []):
                        if detail.get("@type", "").endswith("RetryInfo"):
                            delay_str = detail.get("retryDelay", "")
                            break
                    wait_secs = int(delay_str.replace("s", "")) if delay_str else (2 ** attempt) * 5
                except Exception:
                    wait_secs = (2 ** attempt) * 5
                wait_secs = min(wait_secs, 60)  # cap at 60s
                if attempt < max_retries - 1:
                    time.sleep(wait_secs)
                    continue
                return (
                    "⚠️ The Gemini AI quota has been reached for today (free tier: 1,500 req/day). "
                    "The route and tariff data below are sourced directly from the trade database."
                )
            else:
                return f"Gemini API Error (HTTP {response.status_code}): {response.text}"
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return f"Gemini request failed: {e}"
    return "Gemini API unavailable after retries."

# 1. ROUTER NODE
def router_node(state: AgentState) -> dict:
    query = state["query"]
    api_key = state.get("gemini_api_key")
    
    route_requested = False
    tariff_requested = False
    start_hub = None
    end_hub = None
    commodity = None
    
    steps = list(state.get("steps", []))
    steps.append("Router Agent activated. Analyzing query details...")
    
    # Define rule-based extraction for fallback or quick parse
    query_lower = query.lower()
    cities = ["Lagos", "Cotonou", "Lome", "Accra", "Abidjan", "Ouagadougou", "Niamey", "Bamako", "Dakar"]
    found_cities = []
    
    # Match cities in order they appear in the query
    words = re.findall(r'\b\w+\b', query)
    for word in words:
        word_title = word.title()
        if word_title == "Lome":
            word_title = "Lome"
        if word_title in cities and word_title not in found_cities:
            found_cities.append(word_title)
            
    rule_start = found_cities[0] if len(found_cities) > 0 else None
    rule_end = found_cities[1] if len(found_cities) > 1 else None
    
    # If only one city found, make an intelligent guess for corridor endpoint
    if rule_start and not rule_end:
        rule_end = "Accra" if rule_start == "Lagos" else "Bamako"
        
    # Standard rule check for routing keywords
    if any(k in query_lower for k in ["route", "fastest", "how to get", "travel", "border", "corridor", "distance", "hubs"]):
        route_requested = True
    if any(k in query_lower for k in ["tariff", "duty", "rate", "cost", "tax", "fee", "band", "exempt", "cet"]):
        tariff_requested = True
        
    # Identify commodity
    commodities = ["smartphone", "phone", "rice", "book", "medicine", "cargo", "vehicle", "computer", "crop"]
    rule_commodity = "smartphones"
    for comm in commodities:
        if comm in query_lower:
            rule_commodity = comm + "s" if not comm.endswith("s") else comm
            break
            
    # Default to both if unclear
    if not route_requested and not tariff_requested:
        route_requested = True
        tariff_requested = True

    # Use LLM router if API Key is set
    if api_key:
        system_instruction = (
            "You are the Router Agent of AfriTrade Agent. Your task is to analyze the user's trade query "
            "and output a JSON object with: route_requested (bool), tariff_requested (bool), "
            "start_hub (string or null), end_hub (string or null), and commodity (string or null). "
            "Supported hubs are: Lagos, Cotonou, Lome, Accra, Abidjan, Ouagadougou, Niamey, Bamako, Dakar. "
            "Output ONLY valid JSON."
        )
        prompt = f"Query: {query}"
        
        response = call_gemini(prompt, api_key, system_instruction)
        try:
            # Robustly extract JSON block if conversational text wraps it
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                clean_res = json_match.group(0).strip()
            else:
                clean_res = response.strip()
            parsed = json.loads(clean_res)
            
            route_requested = parsed.get("route_requested", route_requested)
            tariff_requested = parsed.get("tariff_requested", tariff_requested)
            start_hub = parsed.get("start_hub", start_hub) or rule_start
            end_hub = parsed.get("end_hub", end_hub) or rule_end
            commodity = parsed.get("commodity", commodity) or rule_commodity
            steps.append("Router Agent completed analysis using Gemini LLM parser.")
        except Exception as err:
            steps.append(f"Router Agent LLM parse failed ({err}). Falling back to pattern-based routing.")
            start_hub = rule_start
            end_hub = rule_end
            commodity = rule_commodity
    else:
        # Set to rule-based parser results
        start_hub = rule_start
        end_hub = rule_end
        commodity = rule_commodity
        steps.append("Router Agent completed analysis using pattern-based routing (No LLM key).")
        
    # Ensure hubs are valid
    if start_hub: start_hub = start_hub.title()
    if end_hub: end_hub = end_hub.title()
    
    steps.append(
        f"Extracted values: Tariff requested: {tariff_requested}, Route requested: {route_requested}, "
        f"Start: {start_hub}, End: {end_hub}, Commodity: {commodity}"
    )
    
    return {
        "route_requested": route_requested,
        "tariff_requested": tariff_requested,
        "start_hub": start_hub,
        "end_hub": end_hub,
        "commodity": commodity,
        "steps": steps
    }

# 2. TARIFF TOOL NODE
def tariff_tool_node(state: AgentState) -> dict:
    steps = list(state.get("steps", []))
    
    if not state.get("tariff_requested"):
        return {"tariff_results": [], "steps": steps}
        
    steps.append(f"Tariff Tool active. Querying Qdrant database for commodity details: '{state.get('commodity')}'...")
    
    # Search query formatting
    search_query = f"{state.get('commodity')} tariff rate ECOWAS CET rules import duty"
    results = tariff_search_tool(search_query)
    
    if "error" in results[0] if results else False:
        steps.append(f"Tariff Tool encounter error: {results[0]['error']}")
        tariff_results = []
    else:
        tariff_results = results
        steps.append(f"Tariff Tool successfully retrieved {len(results)} relevant documents from Qdrant.")
        
    return {
        "tariff_results": tariff_results,
        "steps": steps
    }

# 3. ROUTE TOOL NODE
def route_tool_node(state: AgentState) -> dict:
    steps = list(state.get("steps", []))
    
    if not state.get("route_requested"):
        return {"route_results": {}, "steps": steps}
        
    query_lower = state["query"].lower()
    neo4j_config = state.get("neo4j_config")
    
    # 1. Border Query check
    if any(k in query_lower for k in ["border", "neighbor", "neighbour"]):
        # Extract country name or code
        countries = {
            "nigeria": "NGA", "benin": "BEN", "togo": "TGO", "ghana": "GHA",
            "cote d'ivoire": "CIV", "ivory coast": "CIV", "burkina faso": "BFA",
            "niger": "NER", "mali": "MLI", "senegal": "SEN"
        }
        target_country = "Nigeria"
        target_code = "NGA"
        for name, code in countries.items():
            if name in query_lower or code.lower() in query_lower:
                target_country = name.title()
                target_code = code
                break
        steps.append(f"Route Tool active. Querying border relationships for country: {target_country} ({target_code})...")
        from tools import border_finder_tool
        border_info = border_finder_tool(target_code, neo4j_config)
        steps.append("Border info retrieved successfully.")
        return {
            "route_results": {
                "type": "border",
                "output": border_info,
                "source": "Graph Database"
            },
            "steps": steps
        }

    # 2. Port / Airport Query check
    if any(k in query_lower for k in ["port", "seaport", "airport", "teu"]):
        # Parse TEU threshold if mentioned
        min_teu = 1000000
        if "1 million" in query_lower or "1m" in query_lower:
            min_teu = 1000000
        elif "500,000" in query_lower or "500k" in query_lower:
            min_teu = 500000
        elif "1.5 million" in query_lower or "1.5m" in query_lower:
            min_teu = 1500000
        
        steps.append(f"Route Tool active. Querying seaports handling >= {min_teu:,} TEU...")
        from tools import port_throughput_tool
        port_info = port_throughput_tool(min_teu, neo4j_config)
        steps.append("Port throughput info retrieved successfully.")
        return {
            "route_results": {
                "type": "port",
                "output": port_info,
                "source": "Graph Database"
            },
            "steps": steps
        }
        
    # 3. Standard City-to-City Route Query
    start = state.get("start_hub")
    end = state.get("end_hub")
    
    # If not extracted but in text, try a quick regex search
    if not start or not end:
        cities = ["Lagos", "Cotonou", "Lome", "Accra", "Abidjan", "Ouagadougou", "Niamey", "Bamako", "Dakar"]
        found = []
        for city in cities:
            if city.lower() in query_lower:
                found.append(city)
        if len(found) >= 2:
            start = found[0]
            end = found[1]
        elif len(found) == 1:
            start = found[0]
            end = "Accra" if start != "Accra" else "Lagos"
            
    if not start or not end:
        steps.append("Route Tool skipped: Start or End city not found in query.")
        return {"route_results": {"error": "Missing start or end city"}, "steps": steps}
        
    # Determine mode constraints
    modes_found = []
    if "road" in query_lower:
        modes_found.append("road")
    if "rail" in query_lower:
        modes_found.append("rail")
    if "air" in query_lower:
        modes_found.append("air")
    if "maritime" in query_lower or "sea" in query_lower:
        modes_found.append("maritime")
        
    mode = "+".join(modes_found) if modes_found else None
        
    steps.append(f"Route Tool active. Finding optimal route from {start} to {end} (Mode: {mode or 'Any'}) in Graph Database...")
    
    from tools import multi_modal_route_tool, route_finder_tool
    route_info = multi_modal_route_tool(start, end, mode, neo4j_config)
    legacy_details = route_finder_tool(start, end, neo4j_config)
    
    results = {
        "type": "route",
        "output": route_info,
        "legacy": legacy_details,
        "source": legacy_details.get("source", "Graph Database"),
        "path": legacy_details.get("path", []),
        "edges": legacy_details.get("edges", []),
        "total_distance_km": legacy_details.get("total_distance_km", 0.0),
        "total_time_hours": legacy_details.get("total_time_hours", 0.0),
        "total_checkpoints": legacy_details.get("total_checkpoints", 0)
    }
    steps.append("City route details retrieved successfully.")
    return {
        "route_results": results,
        "steps": steps
    }

# 4. ANSWER SYNTHESIS NODE
def answer_node(state: AgentState) -> dict:
    steps = list(state.get("steps", []))
    steps.append("Answer Agent active. Synthesizing final answer...")
    
    query = state["query"]
    commodity = state.get("commodity", "goods")
    start = state.get("start_hub")
    end = state.get("end_hub")
    
    # Compile factual context from tools
    tariff_context = ""
    if state.get("tariff_results"):
        tariff_context = "### Tariff Information (Qdrant Vector Database):\n"
        for i, res in enumerate(state["tariff_results"], 1):
            tariff_context += (
                f"{i}. [Score: {res['score']:.2f}] (Source: {res['source']}, Page: {res['page']}):\n"
                f"   \"{res['text']}\"\n\n"
            )
    else:
        tariff_context = "No direct vector search documents retrieved.\n"
        
    route_context = ""
    route_data = state.get("route_results", {})
    if route_data and "error" not in route_data:
        r_type = route_data.get("type", "route")
        if r_type == "border":
            route_context = (
                f"### Border Relationships ({route_data.get('source')}):\n"
                f"{route_data.get('output')}\n"
            )
        elif r_type == "port":
            route_context = (
                f"### Ports and Throughput Information ({route_data.get('source')}):\n"
                f"{route_data.get('output')}\n"
            )
        else:
            # Standard city-to-city route
            route_context = (
                f"### Route Details:\n"
                f"{route_data.get('output')}\n"
            )
            if "legacy" in route_data and "error" not in route_data["legacy"]:
                leg = route_data["legacy"]
                path_str = " ➔ ".join(leg.get("path", []))
                route_context += (
                    f"\n**Leg Details ({leg.get('source')}):**\n"
                    f"- **Legacy Path**: {path_str}\n"
                    f"- **Total Distance**: {leg.get('total_distance_km')} km\n"
                    f"- **Estimated Time**: {leg.get('total_time_hours')} hours\n"
                    f"- **Checkpoints**: {leg.get('total_checkpoints')} border checkpoints\n"
                )
    else:
        route_context = "No corridor routing data found.\n"
        
    api_key = state.get("gemini_api_key")
    
    if api_key:
        system_instruction = (
            "You are the Answer Agent of AfriTrade Agent. Your task is to synthesize information from "
            "Tariff and Route tools into a single, cohesive, professional response. The response must answer "
            "the user's query exactly, using the provided database results. Highlight duty rates (CET bands 0-4), "
            "VAT, transit corridors, total time (including border delays), and checkpoints. Be structured, readable, and authoritative."
        )
        
        prompt = (
            f"User Query: {query}\n\n"
            f"--- DATABASE CONTEXT ---\n"
            f"{tariff_context}\n"
            f"{route_context}\n"
            f"------------------------\n\n"
            f"Synthesize the final natural-language response based ONLY on the context details above."
        )
        
        final_answer = call_gemini(prompt, api_key, system_instruction)
        
        # Check if the response returned an error indicating API failure or quota limits
        is_error = False
        for err_marker in ["Error", "Gemini", "⚠️", "api", "failed"]:
            if final_answer.strip().lower().startswith(err_marker.lower()):
                is_error = True
                break
                
        if not is_error:
            steps.append("Answer Agent successfully synthesized response using Gemini API.")
        else:
            steps.append(f"Answer Agent: Gemini API call failed ({final_answer[:60]}...). Falling back to template-based synthesizer.")
            api_key = None  # Force template response generation below with the error message prepended
    
    if not api_key:
        # Fallback template response builder
        if route_data.get("type") == "border":
            final_answer = (
                f"### 🌍 AfriTrade Agent Intelligence Report\n\n"
                f"**Query**: \"{query}\"\n\n"
                f"**Border Information**:\n"
                f"{route_data.get('output')}\n\n"
                f"This information is retrieved from the West Africa Regional Trade Graph."
            )
        elif route_data.get("type") == "port":
            final_answer = (
                f"### 🌍 AfriTrade Agent Intelligence Report\n\n"
                f"**Query**: \"{query}\"\n\n"
                f"**Port & Infrastructure Information**:\n"
                f"{route_data.get('output')}\n\n"
                f"This throughput information is retrieved from the West Africa Regional Trade Graph."
            )
        else:
            # Calculate tariff band based on commodity
            tariff_desc = ""
            rate_found = "20%"
            band_found = "Band 3 (Finished Consumer Goods)"
            
            if "rice" in commodity.lower():
                rate_found = "35%"
                band_found = "Band 4 (Specific Goods for Economic Development - Sensitive agricultural sector)"
                tariff_desc = (
                    "Under the ECOWAS Common External Tariff (CET), rice is subject to a 35% duty (Band 4) to protect local farming. "
                    "However, note that Senegal requires joint import licenses from the Direction du Commerce Extérieur (DCE)."
                )
            elif "smartphone" in commodity.lower() or "phone" in commodity.lower():
                rate_found = "20%"
                band_found = "Band 3 (Finished Consumer Goods)"
                tariff_desc = (
                    "Smartphones fall under ECOWAS CET Band 3 (Finished Consumer Goods), subject to a 20% customs duty. "
                    "Additionally, imports into most ECOWAS ports incur regional taxes, such as Senegal's 18% standard VAT "
                    "and the 1% Statistical Fee (Redevance Statistique)."
                )
            elif "book" in commodity.lower() or "medicine" in commodity.lower():
                rate_found = "0%"
                band_found = "Band 0 (Essential Social Goods)"
                tariff_desc = "Books and essential medicines are classified under Band 0 (0% duty) to encourage education and health access."
            else:
                tariff_desc = "Standard finished commodities are classified under Band 3 (20% import duty)."
                
            # Format the route fallback details
            route_desc = ""
            if route_data and "error" not in route_data:
                legacy = route_data.get("legacy", {})
                path_str = " ➔ ".join(legacy.get("path", [])) if legacy.get("path") else ""
                route_desc = (
                    f"For transit, the route is:\n"
                    f"{route_data.get('output')}\n\n"
                    f"- **Legacy Route Checkpoints**: {legacy.get('total_checkpoints')} total checkpoints.\n\n"
                    f"We recommend utilizing the **ECOWAS Trade Liberalization Scheme (ETLS)** for duty-free transit, "
                    f"which requires a valid Certificate of Origin for originating goods."
                )
            else:
                route_desc = f"No route path could be calculated between {start} and {end}."
                
            # Determine appropriate warning/fallback note
            if "final_answer" in locals() and any(k in str(final_answer).lower() for k in ["error", "gemini", "⚠️", "api", "failed"]):
                note_content = (
                    f"> [!WARNING]  \n"
                    f"> **Gemini API Error**: {final_answer}\n"
                    f"> \n"
                    f"> *The agent has successfully fallen back to rule-based database matching to provide factual information from the West Africa Regional Trade Graph and Qdrant.*"
                )
            else:
                note_content = (
                    f"> [!NOTE]  \n"
                    f"> *This response was generated using local rule-based database matching because the Gemini API key was not supplied. "
                    f"Add your `GEMINI_API_KEY` in the sidebar to enable full multi-hop LLM reasoning.*"
                )

            final_answer = (
                f"### 🌍 AfriTrade Agent Intelligence Report\n\n"
                f"**Query**: \"{query}\"\n\n"
                f"#### 📋 Customs & Tariff Classification\n"
                f"- **Commodity**: {commodity.title()}\n"
                f"- **ECOWAS CET Classification**: **{band_found}**\n"
                f"- **Customs Import Duty**: **{rate_found}**\n\n"
                f"{tariff_desc}\n\n"
                f"#### 🛣️ Corridor Logistics & Routing\n"
                f"{route_desc}\n\n"
                f"---  \n"
                f"{note_content}"
            )
        steps.append("Answer Agent synthesized response using local rules and template fallback.")
    
    return {
        "final_answer": final_answer,
        "steps": steps
    }

# Build LangGraph workflow
def build_agent_graph():
    builder = StateGraph(AgentState)
    
    # Add Nodes
    builder.add_node("router", router_node)
    builder.add_node("tariff_tool", tariff_tool_node)
    builder.add_node("route_tool", route_tool_node)
    builder.add_node("answer_generator", answer_node)
    
    # Establish Entry
    builder.set_entry_point("router")
    
    # Flow transitions: run router, then run tariff tool, then run route tool, then compile answer
    # This sequential execution is completely safe and guarantees all requested tool data is loaded before synthesis
    builder.add_edge("router", "tariff_tool")
    builder.add_edge("tariff_tool", "route_tool")
    builder.add_edge("route_tool", "answer_generator")
    builder.add_edge("answer_generator", END)
    
    return builder.compile()

# Entry function to run reasoning loop
def run_agentic_flow(query: str, gemini_api_key: str = None, neo4j_config: dict = None) -> dict:
    graph = build_agent_graph()
    
    # Initialize state
    initial_state = {
        "query": query,
        "gemini_api_key": gemini_api_key,
        "neo4j_config": neo4j_config,
        "route_requested": False,
        "tariff_requested": False,
        "start_hub": None,
        "end_hub": None,
        "commodity": None,
        "tariff_results": [],
        "route_results": {},
        "steps": [],
        "final_answer": ""
    }
    
    result = graph.invoke(initial_state)
    return {
        "final_answer": result.get("final_answer"),
        "steps": result.get("steps", []),
        "metadata": {
            "commodity": result.get("commodity"),
            "start_hub": result.get("start_hub"),
            "end_hub": result.get("end_hub"),
            "route_requested": result.get("route_requested"),
            "tariff_requested": result.get("tariff_requested"),
            "tariff_results": result.get("tariff_results"),
            "route_results": result.get("route_results")
        }
    }
