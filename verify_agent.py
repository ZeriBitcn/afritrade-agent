"""
AfriTrade Agent — Week 3 Verification Script
Tests: graph_db, tools (route_finder), agentic_flow (full pipeline)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = "[PASS]"
FAIL = "[FAIL]"
INFO = "[INFO]"

def section(title):
    print(f"\n{'-'*55}")
    print(f"  {title}")
    print('-'*55)

# ── 1. graph_db.py ──────────────────────────────────────
section("Test 1: graph_db — Local NetworkX Graph")

try:
    from tools import load_secrets
    secrets = load_secrets()
    uri = secrets.get("NEO4J_URI") or os.getenv("NEO4J_URI")
    user = secrets.get("NEO4J_USER") or secrets.get("NEO4J_USERNAME") or os.getenv("NEO4J_USER")
    password = secrets.get("NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD")

    from graph_db import WestAfricaTradeGraph
    g = WestAfricaTradeGraph(uri, user, password)

    # Check nodes loaded
    nodes = list(g.fallback_graph.nodes)
    assert "Lagos" in nodes and "Accra" in nodes, "Expected Lagos and Accra"
    print(f"{PASS} WestAfricaTradeGraph initialised with {len(nodes)} hubs: {nodes}")

    # Find path Lagos → Accra
    result = g.find_shortest_path("Lagos", "Accra")
    assert result is not None, "Path result is None"
    assert len(result["path"]) >= 2, "Path must have at least 2 nodes"
    print(f"{PASS} Path Lagos -> Accra: {' -> '.join(result['path'])}")
    print(f"{INFO} Distance: {result['total_distance_km']} km | "
          f"Time: {result['total_time_hours']} hrs | "
          f"Checkpoints: {result['total_checkpoints']} | "
          f"Source: {result['source']}")

    # Test Dakar → Bamako
    result2 = g.find_shortest_path("Dakar", "Bamako")
    assert result2 is not None, "Dakar -> Bamako path not found"
    print(f"{PASS} Path Dakar -> Bamako: {' -> '.join(result2['path'])}")

    # New Multi-modal & Border tests
    print(f"\n{INFO} --- Running new multi-modal, border, and port tests ---")
    borders = g.find_bordering_countries("Nigeria")
    print(f"{PASS} find_bordering_countries('Nigeria'): {borders}")
    assert "BEN" in borders or "Benin" in borders, "Benin should border Nigeria"
    
    route_mm = g.find_route_between_cities("Bamako", "Lagos", "rail")
    print(f"{PASS} find_route_between_cities('Bamako', 'Lagos', 'rail'):\n{route_mm}")
    assert "Lagos" in route_mm, "Lagos must be in the route output"
    
    ports = g.get_top_ports(1000000)
    print(f"{PASS} get_top_ports(1000000):\n{ports}")
    assert "Tema" in ports or "Lome" in ports or "Abidjan" in ports or "Lagos" in ports, "Should list major ports"

    g.close()
except Exception as e:
    print(f"{FAIL} graph_db error: {e}")
    import traceback; traceback.print_exc()

# ── 2. tools.py — route_finder_tool ─────────────────────
section("Test 2: tools.py — route_finder_tool (no Neo4j)")

try:
    from tools import route_finder_tool
    route = route_finder_tool("Lagos", "Accra", neo4j_config=None)
    assert "error" not in route or route.get("path"), "Route returned error with no path"
    if route.get("path"):
        print(f"{PASS} route_finder_tool: {' -> '.join(route['path'])} "
              f"({route['total_distance_km']} km)")
    else:
        print(f"{FAIL} route_finder_tool returned: {route}")
except Exception as e:
    print(f"{FAIL} tools.route_finder_tool error: {e}")
    import traceback; traceback.print_exc()

# ── 3. agentic_flow.py — Router Node ────────────────────
section("Test 3: agentic_flow — Router Node (no LLM)")

try:
    from agentic_flow import router_node, AgentState

    test_state: AgentState = {
        "query": "What's the tariff on smartphones from Lagos to Accra and fastest route?",
        "gemini_api_key": None,
        "neo4j_config": None,
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

    router_out = router_node(test_state)
    print(f"{PASS} Router extracted:")
    print(f"       commodity={router_out.get('commodity')} | "
          f"start={router_out.get('start_hub')} | end={router_out.get('end_hub')}")
    print(f"       tariff_requested={router_out.get('tariff_requested')} | "
          f"route_requested={router_out.get('route_requested')}")
    for step in router_out.get("steps", []):
        print(f"       {INFO} {step}")
except Exception as e:
    print(f"{FAIL} agentic_flow.router_node error: {e}")
    import traceback; traceback.print_exc()

# ── 4. Full End-to-End Pipeline (no LLM, no Qdrant check) ─
section("Test 4: agentic_flow — Full pipeline (no LLM/Qdrant)")

try:
    from agentic_flow import run_agentic_flow

    # Use a route-only query that doesn't depend on Qdrant being reachable
    # We patch the tariff tool to avoid real API calls
    import agentic_flow
    _real_tariff = None

    # Monkey-patch tariff tool to return a mock result
    import tools as tools_mod
    _real_tariff_fn = tools_mod.tariff_search_tool

    def mock_tariff_search(query):
        return [{
            "score": 0.92,
            "text": "Smartphones fall under ECOWAS CET Band 3 – 20% import duty (Finished Consumer Goods).",
            "source": "mock_cet.pdf",
            "page": 12
        }]

    tools_mod.tariff_search_tool = mock_tariff_search

    result = run_agentic_flow(
        query="What tariff applies to smartphones shipped from Lagos to Accra?",
        gemini_api_key=None,
        neo4j_config=None
    )

    # Restore
    tools_mod.tariff_search_tool = _real_tariff_fn

    assert result.get("final_answer"), "No final_answer in result"
    print(f"{PASS} Full pipeline completed successfully.")
    print(f"{INFO} Steps executed: {len(result.get('steps', []))}")
    
    def safe_print(text):
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode('ascii', errors='replace').decode('ascii'))
            
    safe_print(f"{INFO} Answer preview: {result['final_answer'][:120].strip()}...")
    safe_print(f"{INFO} Metadata: commodity={result['metadata'].get('commodity')}, "
               f"route={result['metadata'].get('route_results', {}).get('path', [])[:3]}")

except Exception as e:
    print(f"{FAIL} Full pipeline error: {e}")
    import traceback; traceback.print_exc()

# ── 5. LangGraph imports ─────────────────────────────────
section("Test 5: LangGraph & dependencies")

try:
    import importlib.metadata as _meta
    import langgraph
    import langchain_core
    import neo4j
    import networkx

    def _ver(pkg):
        try:
            return _meta.version(pkg)
        except Exception:
            return "installed"

    print(f"{PASS} langgraph v{_ver('langgraph')} installed")
    print(f"{PASS} langchain-core v{_ver('langchain-core')} installed")
    print(f"{PASS} neo4j v{_ver('neo4j')} installed")
    print(f"{PASS} networkx v{networkx.__version__} installed")
except ImportError as e:
    print(f"{FAIL} Missing dependency: {e}")

print(f"\n{'-'*55}")
print("  Verification complete.")
print('-'*55 + "\n")
