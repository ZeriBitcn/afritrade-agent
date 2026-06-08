from embeddings import MiniLMEmbeddingModel
from qdrant_client import QdrantClient
from graph_db import WestAfricaTradeGraph
import os
import re

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

def tariff_search_tool(query: str) -> list:
    """
    Search the Qdrant vector database for tariff information, returns relevant document chunks.
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
            limit=3
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
        user = secrets.get("NEO4J_USER") or os.getenv("NEO4J_USER")
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
