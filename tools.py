from embeddings import MiniLMEmbeddingModel
from qdrant_client import QdrantClient
from graph_db import WestAfricaTradeGraph
import os
import re
import json
import time

COLLECTION_NAME = "ecowas_tariffs"

def load_secrets():
    """Load secrets from .streamlit/secrets.toml if available."""
    secrets = {}
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    if os.path.exists(secrets_path):
        with open(secrets_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                match = re.match(r'^\s*([A-Za-z0-9_]+)\s*=\s*["\'](.*)["\']\s*$', line)
                if match:
                    secrets[match.group(1)] = match.group(2)
    return secrets

def get_qdrant_client():
    secrets = load_secrets()
    url = secrets.get("QDRANT_URL") or os.getenv("QDRANT_URL")
    api_key = secrets.get("QDRANT_API_KEY") or os.getenv("QDRANT_API_KEY")
    if not url or not api_key:
        raise ValueError("Qdrant credentials (QDRANT_URL, QDRANT_API_KEY) not found in secrets.toml or environment.")
    return QdrantClient(url=url, api_key=api_key)

def tariff_search_tool(query: str, limit: int = 5) -> list:
    """
    Search the Qdrant vector database for tariff information.
    Returns up to `limit` relevant document chunks ranked by similarity score.
    """
    try:
        model = MiniLMEmbeddingModel('sentence-transformers/all-MiniLM-L6-v2')
        qdrant = get_qdrant_client()
        
        # Compute embedding
        query_vector = model.encode(query).tolist()
        
        # Search Qdrant
        response = qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=limit
        )
        
        results = []
        for point in response.points:
            results.append({
                "score": point.score,
                "text": point.payload.get("text", ""),
                "source": point.payload.get("source", ""),
                "page": point.payload.get("page", "")
            })
        return results
    except Exception as e:
        print(f"Error in tariff_search_tool: {e}")
        return [{"error": str(e)}]


def graded_tariff_search_tool(query: str, api_key: str, logger=None) -> dict:
    """
    Multi-hop RAG with LLM-based document grading.
    
    Flow:
      1. First retrieval: Qdrant top-5 chunks
      2. LLM Grading: Gemini scores each chunk 0-10 for relevance
      3. Adaptive re-query: if < 2 chunks pass (grade >= 5), reformulate and search again
      4. Merge & deduplicate: combine both hops, remove duplicates, return graded results
    
    Returns:
      {
        "graded_results": [...],  # chunks with grade scores
        "hops_performed": int,
        "total_retrieved": int,
        "total_passed": int,
        "steps": [...]  # logging steps for the agent
      }
    """
    from agentic_flow import call_gemini
    
    steps = []
    all_graded = []
    seen_texts = set()
    hops = 0
    
    # ── Hop 1: Initial retrieval ──
    hops += 1
    steps.append(f"RAG Hop 1: Searching Qdrant for '{query[:60]}...'")
    hop1_results = tariff_search_tool(query, limit=5)
    
    # Filter out error results
    if hop1_results and "error" in hop1_results[0]:
        return {
            "graded_results": [],
            "hops_performed": 1,
            "total_retrieved": 0,
            "total_passed": 0,
            "steps": steps + [f"Retrieval error: {hop1_results[0]['error']}"]
        }
    
    steps.append(f"RAG Hop 1: Retrieved {len(hop1_results)} chunks from Qdrant")
    
    # ── Grade chunks with LLM ──
    graded_hop1 = _grade_chunks(hop1_results, query, api_key, steps)
    
    # Track what we've seen to avoid duplicates
    for item in graded_hop1:
        text_key = item["text"][:100].strip()
        if text_key not in seen_texts:
            seen_texts.add(text_key)
            all_graded.append(item)
    
    passed_count = sum(1 for g in all_graded if g.get("grade", 0) >= 5)
    steps.append(f"RAG Hop 1 Grading: {passed_count}/{len(all_graded)} chunks passed (grade ≥ 5)")
    
    if logger:
        grade_scores = [g.get("grade", 0) for g in all_graded]
        logger.log_retrieval_hop(1, len(hop1_results), passed_count, grade_scores)
    
    # ── Hop 2: Adaptive re-query if too few chunks passed ──
    if passed_count < 2 and api_key:
        hops += 1
        steps.append("RAG Hop 2: Too few relevant chunks. Reformulating query...")
        
        # Ask Gemini to reformulate the query for better retrieval
        reformulate_prompt = (
            f"The following search query did not return enough relevant results about "
            f"ECOWAS trade tariffs and regulations:\n\n"
            f"Original query: \"{query}\"\n\n"
            f"Generate a single reformulated search query that would better match "
            f"ECOWAS CET tariff documents, customs rules, or trade corridor information. "
            f"Output ONLY the reformulated query text, nothing else."
        )
        
        refined_query = call_gemini(reformulate_prompt, api_key)
        refined_query = refined_query.strip().strip('"').strip("'")
        
        if refined_query and not refined_query.startswith("Error"):
            steps.append(f"RAG Hop 2: Refined query — '{refined_query[:60]}...'")
            hop2_results = tariff_search_tool(refined_query, limit=5)
            
            if hop2_results and "error" not in hop2_results[0]:
                steps.append(f"RAG Hop 2: Retrieved {len(hop2_results)} additional chunks")
                graded_hop2 = _grade_chunks(hop2_results, query, api_key, steps)
                
                for item in graded_hop2:
                    text_key = item["text"][:100].strip()
                    if text_key not in seen_texts:
                        seen_texts.add(text_key)
                        all_graded.append(item)
                
                new_passed = sum(1 for g in all_graded if g.get("grade", 0) >= 5)
                steps.append(f"RAG Hop 2 Grading: {new_passed}/{len(all_graded)} total chunks now pass")
                
                if logger:
                    hop2_scores = [g.get("grade", 0) for g in graded_hop2]
                    logger.log_retrieval_hop(2, len(hop2_results),
                                            new_passed - passed_count, hop2_scores)
        else:
            steps.append("RAG Hop 2: Query reformulation failed, skipping second hop")
    
    # ── Sort by grade (descending), then by vector score ──
    all_graded.sort(key=lambda x: (x.get("grade", 0), x.get("score", 0)), reverse=True)
    
    # Only keep chunks that passed grading (grade >= 5), or top-3 if none passed
    passed = [g for g in all_graded if g.get("grade", 0) >= 5]
    if not passed:
        passed = all_graded[:3]  # Fallback: return top-3 by vector score even if ungraded
    
    return {
        "graded_results": passed,
        "hops_performed": hops,
        "total_retrieved": len(all_graded),
        "total_passed": len(passed),
        "steps": steps
    }


def _grade_chunks(chunks: list, query: str, api_key: str, steps: list) -> list:
    """
    Use Gemini to grade a batch of retrieved chunks for relevance to the query.
    Returns the same chunks with an added 'grade' field (0-10).
    """
    from agentic_flow import call_gemini
    
    if not api_key or not chunks:
        # No API key — assign neutral grade of 6 to all (pass-through)
        for c in chunks:
            c["grade"] = 6
        return chunks
    
    # Build grading prompt
    chunk_texts = ""
    for i, c in enumerate(chunks):
        chunk_texts += f"[Chunk {i+1}] (score={c['score']:.2f}, source={c['source']}):\n{c['text'][:300]}\n\n"
    
    grading_prompt = (
        f"You are a relevance grader for an ECOWAS trade intelligence system.\n\n"
        f"User query: \"{query}\"\n\n"
        f"Below are {len(chunks)} document chunks retrieved from a vector database. "
        f"Grade EACH chunk from 0 to 10 based on how relevant it is to answering the user's query.\n"
        f"- 0 = completely irrelevant\n"
        f"- 5 = marginally relevant\n"
        f"- 10 = directly answers the query\n\n"
        f"{chunk_texts}\n"
        f"Output ONLY a JSON array of integers, e.g. [8, 3, 7, 2, 9]. "
        f"The array must have exactly {len(chunks)} elements."
    )
    
    start_t = time.time()
    response = call_gemini(grading_prompt, api_key)
    grading_latency = round((time.time() - start_t) * 1000, 1)
    
    # Parse grades
    try:
        # Extract JSON array from response
        json_match = re.search(r'\[[\d,\s]+\]', response)
        if json_match:
            grades = json.loads(json_match.group(0))
        else:
            grades = json.loads(response.strip())
        
        if len(grades) == len(chunks):
            for i, c in enumerate(chunks):
                c["grade"] = max(0, min(10, int(grades[i])))
            steps.append(f"Grading complete ({grading_latency}ms): scores = {grades}")
        else:
            # Length mismatch — assign neutral grades
            for c in chunks:
                c["grade"] = 6
            steps.append(f"Grading returned {len(grades)} scores for {len(chunks)} chunks — using neutral grade 6")
    except Exception as e:
        # Parse failure — assign neutral grades
        for c in chunks:
            c["grade"] = 6
        steps.append(f"Grading parse failed ({e}) — using neutral grade 6")
    
    return chunks

def route_finder_tool(start_hub: str, end_hub: str, neo4j_config: dict = None) -> dict:
    """
    Query the graph database (Neo4j or local NetworkX fallback) for the fastest route,
    returns nodes list, distance, checkpoints, and transit times.
    """
    uri = None
    user = None
    password = None
    
    # Check config passed in, then secrets.toml, then environment
    if neo4j_config:
        uri = neo4j_config.get("uri")
        user = neo4j_config.get("user")
        password = neo4j_config.get("password")
        
    if not uri:
        secrets = load_secrets()
        uri = secrets.get("NEO4J_URI") or os.getenv("NEO4J_URI")
        user = secrets.get("NEO4J_USER") or secrets.get("NEO4J_USERNAME") or os.getenv("NEO4J_USER")
        password = secrets.get("NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD")
        
    graph = WestAfricaTradeGraph(uri, user, password)
    path_details = graph.find_shortest_path(start_hub, end_hub)
    graph.close()
    
    if path_details:
        return path_details
    else:
        return {
            "error": f"Could not find a valid route between {start_hub} and {end_hub}.",
            "path": [],
            "edges": [],
            "total_distance_km": 0.0,
            "total_time_hours": 0.0,
            "total_checkpoints": 0
        }

def border_finder_tool(country: str, neo4j_config: dict = None) -> str:
    """
    Query the graph database for all countries bordering the target country.
    """
    uri = None
    user = None
    password = None
    if neo4j_config:
        uri = neo4j_config.get("uri")
        user = neo4j_config.get("user")
        password = neo4j_config.get("password")
    if not uri:
        secrets = load_secrets()
        uri = secrets.get("NEO4J_URI") or os.getenv("NEO4J_URI")
        user = secrets.get("NEO4J_USER") or secrets.get("NEO4J_USERNAME") or os.getenv("NEO4J_USER")
        password = secrets.get("NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD")
        
    graph = WestAfricaTradeGraph(uri, user, password)
    res = graph.find_bordering_countries(country)
    graph.close()
    return res

def multi_modal_route_tool(from_city: str, to_city: str, mode: str = None, neo4j_config: dict = None) -> str:
    """
    Query the graph database for a route between two cities with optional mode filtering.
    """
    uri = None
    user = None
    password = None
    if neo4j_config:
        uri = neo4j_config.get("uri")
        user = neo4j_config.get("user")
        password = neo4j_config.get("password")
    if not uri:
        secrets = load_secrets()
        uri = secrets.get("NEO4J_URI") or os.getenv("NEO4J_URI")
        user = secrets.get("NEO4J_USER") or secrets.get("NEO4J_USERNAME") or os.getenv("NEO4J_USER")
        password = secrets.get("NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD")
        
    graph = WestAfricaTradeGraph(uri, user, password)
    res = graph.find_route_between_cities(from_city, to_city, mode)
    graph.close()
    return res

def port_throughput_tool(min_teu: int = 1000000, neo4j_config: dict = None) -> str:
    """
    Query the graph database for ports handling at least the specified TEU.
    """
    uri = None
    user = None
    password = None
    if neo4j_config:
        uri = neo4j_config.get("uri")
        user = neo4j_config.get("user")
        password = neo4j_config.get("password")
    if not uri:
        secrets = load_secrets()
        uri = secrets.get("NEO4J_URI") or os.getenv("NEO4J_URI")
        user = secrets.get("NEO4J_USER") or secrets.get("NEO4J_USERNAME") or os.getenv("NEO4J_USER")
        password = secrets.get("NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD")
        
    graph = WestAfricaTradeGraph(uri, user, password)
    res = graph.get_top_ports(min_teu)
    graph.close()
    return res
