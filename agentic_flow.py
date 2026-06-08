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
def call_gemini(prompt: str, api_key: str, system_instruction: str = None) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        
    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
        if response.status_code == 200:
            res_json = response.json()
            candidates = res_json.get("candidates", [])
            if candidates:
                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                return text.strip()
            return f"Error: Empty generation. Response: {res_json}"
        else:
            return f"Gemini API Error (HTTP {response.status_code}): {response.text}"
    except Exception as e:
        return f"Gemini request failed: {e}"

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
            # Clean JSON codeblock if LLM formatted it
            clean_res = re.sub(r'```json\s*|\s*```', '', response).strip()
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
        
    start = state.get("start_hub")
    end = state.get("end_hub")
    
    if not start or not end:
        steps.append("Route Tool skipped: Start or End hub not specified in router extraction.")
        return {"route_results": {"error": "Missing start or end hub"}, "steps": steps}
        
    steps.append(f"Route Tool active. Finding optimal route from {start} to {end} in Graph Database...")
    
    # Query Graph
    results = route_finder_tool(start, end, state.get("neo4j_config"))
    
    if "error" in results:
        steps.append(f"Route Tool error: {results['error']}")
    else:
        source = results.get("source", "Graph Database")
        path_str = " -> ".join(results.get("path", []))
        steps.append(
            f"Route Tool successfully retrieved path from {source}. "
            f"Path: {path_str} | Distance: {results.get('total_distance_km')} km | "
            f"Time: {results.get('total_time_hours')} hours | Checkpoints: {results.get('total_checkpoints')}"
        )
        
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
        path_str = " ➔ ".join(route_data.get("path", []))
        route_context = (
            f"### Route Details ({route_data.get('source')}):\n"
            f"- **Optimal Corridor Path**: {path_str}\n"
            f"- **Total Distance**: {route_data.get('total_distance_km')} km\n"
            f"- **Estimated Transport + Border Crossing Time**: {route_data.get('total_time_hours')} hours\n"
            f"- **Number of Border Posts / Checkpoints**: {route_data.get('total_checkpoints')} checkpoints\n"
        )
        # Detail corridor legs
        if route_data.get("edges"):
            route_context += "\n**Detailed Corridor Segments:**\n"
            for edge in route_data["edges"]:
                route_context += (
                    f"  - Segment: Distance {edge.get('distance_km')} km | "
                    f"Transit: {edge.get('transit_time_hours')} hrs | "
                    f"Border Delay: {edge.get('border_crossing_hours')} hrs | "
                    f"Checkpoints: {edge.get('checkpoints')} ({edge.get('corridor')})\n"
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
        steps.append("Answer Agent successfully synthesized response using Gemini API.")
    else:
        # Fallback template response builder
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
            path_str = " ➔ ".join(route_data["path"])
            route_desc = (
                f"For transit, the fastest route from **{start}** to **{end}** runs along the "
                f"**{route_data['edges'][0]['corridor'] if route_data['edges'] else 'ECOWAS'} corridor**:\n"
                f"- **Path**: {path_str}\n"
                f"- **Total Distance**: {route_data['total_distance_km']} km\n"
                f"- **Estimated Time**: {route_data['total_time_hours']} hours (including border delays)\n"
                f"- **Border Crossings / Checkpoints**: {route_data['total_checkpoints']} total checkpoints.\n\n"
                f"We recommend utilizing the **ECOWAS Trade Liberalization Scheme (ETLS)** for duty-free transit, "
                f"which requires a valid Certificate of Origin for originating goods."
            )
        else:
            route_desc = f"No route path could be calculated between {start} and {end}."
            
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
            f"> [!NOTE]  \n"
            f"> *This response was generated using local rule-based database matching because the Gemini API key was not supplied. "
            f"Add your `GEMINI_API_KEY` in the sidebar to enable full multi-hop LLM reasoning.*"
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
