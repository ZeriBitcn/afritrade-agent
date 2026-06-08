import streamlit as st
from embeddings import MiniLMEmbeddingModel
from qdrant_client import QdrantClient
import os

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
COLLECTION_NAME = "ecowas_tariffs"

@st.cache_resource
def load_model():
    return MiniLMEmbeddingModel('sentence-transformers/all-MiniLM-L6-v2')

@st.cache_resource
def load_qdrant():
    url = st.secrets.get("QDRANT_URL") or os.getenv("QDRANT_URL")
    api_key = st.secrets.get("QDRANT_API_KEY") or os.getenv("QDRANT_API_KEY")
    return QdrantClient(url=url, api_key=api_key)

# ──────────────────────────────────────────────
# 1. Page Configuration
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="AfriTrade Agent | Intelligent ECOWAS Trade Intelligence",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────
# 2. Premium CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4, h5, h6    { font-family: 'Outfit', sans-serif; }

/* Background */
.stApp {
    background:
        radial-gradient(circle at 85% 5%,  rgba(37,99,235,0.10), transparent 40%),
        radial-gradient(circle at 10% 95%, rgba(139,92,246,0.10), transparent 40%),
        #0b1120;
    color: #f1f5f9;
}

/* Scrollbars */
::-webkit-scrollbar { width:7px; height:7px; }
::-webkit-scrollbar-track { background: rgba(15,23,42,0.4); }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.35); border-radius:4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(99,102,241,0.55); }

/* Hide Streamlit branding/toolbar but keep sidebar toggle arrow */
[data-testid="stToolbar"]     { display: none !important; }
[data-testid="stDecoration"]  { display: none !important; }
[data-testid="stStatusWidget"]{ display: none !important; }
#MainMenu                     { display: none !important; }
footer                        { visibility: hidden; }

/* Ensure sidebar collapse/expand arrow stays visible */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    color: #94a3b8 !important;
    background: rgba(30,41,59,0.8) !important;
    border-radius: 0 8px 8px 0 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-left: none !important;
}
[data-testid="collapsedControl"]:hover,
[data-testid="stSidebarCollapsedControl"]:hover {
    background: rgba(99,102,241,0.2) !important;
    color: #a5b4fc !important;
}

/* ── Hero ── */
.hero-container {
    text-align:center;
    padding: 2.5rem 1rem 2rem;
    margin-bottom: 1.5rem;
    background: rgba(30,41,59,0.45);
    border-radius: 24px;
    border: 1px solid rgba(255,255,255,0.06);
    backdrop-filter: blur(14px);
}
.hero-title {
    background: linear-gradient(135deg, #60a5fa, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3.4rem;
    font-weight: 800;
    margin: 0;
    line-height: 1.15;
}
.hero-subtitle {
    color: #94a3b8;
    font-size: 1.2rem;
    margin-top: 0.7rem;
    font-weight: 400;
}
.hero-badge {
    display: inline-block;
    margin-top: 1rem;
    padding: 5px 16px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    background: rgba(99,102,241,0.12);
    border: 1px solid rgba(99,102,241,0.3);
    color: #a5b4fc;
    letter-spacing: 0.06em;
}

/* ── Suggestion chips ── */
div[data-testid="stHorizontalBlock"] button {
    background-color: rgba(30,41,59,0.65) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 30px !important;
    color: #a5b4fc !important;
    font-size: 0.82rem !important;
    padding: 6px 14px !important;
    transition: all 0.25s ease !important;
    width: 100% !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
div[data-testid="stHorizontalBlock"] button:hover {
    background-color: rgba(99,102,241,0.18) !important;
    border-color: rgba(99,102,241,0.45) !important;
    color: #e0e7ff !important;
    transform: scale(1.02);
}

/* ── Agent Step Cards ── */
.step-card {
    display: flex;
    align-items: flex-start;
    gap: 12px;
    padding: 14px 18px;
    margin-bottom: 10px;
    border-radius: 12px;
    background: rgba(30,41,59,0.5);
    border: 1px solid rgba(255,255,255,0.05);
    animation: fadeSlideIn 0.4s ease forwards;
}
.step-icon {
    font-size: 1.3rem;
    flex-shrink: 0;
    margin-top: 1px;
}
.step-text {
    font-size: 0.88rem;
    color: #cbd5e1;
    line-height: 1.5;
    font-family: 'JetBrains Mono', monospace;
}
.step-card.router   { border-left: 3px solid #818cf8; }
.step-card.tariff   { border-left: 3px solid #34d399; }
.step-card.route    { border-left: 3px solid #fb923c; }
.step-card.answer   { border-left: 3px solid #c084fc; }
.step-card.info     { border-left: 3px solid #60a5fa; }

@keyframes fadeSlideIn {
    from { opacity:0; transform: translateY(6px); }
    to   { opacity:1; transform: translateY(0);   }
}

/* ── Final Answer Box ── */
.answer-box {
    padding: 28px 32px;
    border-radius: 18px;
    background: rgba(30,41,59,0.55);
    border: 1px solid rgba(99,102,241,0.25);
    backdrop-filter: blur(14px);
    box-shadow: 0 16px 40px rgba(0,0,0,0.35);
    margin-top: 12px;
}
.answer-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 18px;
    padding-bottom: 14px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}
.answer-label {
    font-family: 'Outfit', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    color: #e2e8f0;
}

/* ── Result Cards (Search tab) ── */
.result-card {
    background: rgba(30,41,59,0.35);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 22px;
    margin-bottom: 18px;
    transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
}
.result-card:hover {
    transform: translateY(-3px);
    border-color: rgba(96,165,250,0.25);
    box-shadow: 0 12px 30px rgba(0,0,0,0.3);
}
.badge-container { margin-bottom: 12px; }
.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.73rem;
    font-weight: 600;
    margin-right: 7px;
    margin-bottom: 7px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.badge-score  { background:rgba(16,185,129,0.14); color:#34d399; border:1px solid rgba(16,185,129,0.3); }
.badge-source { background:rgba(59,130,246,0.14);  color:#60a5fa; border:1px solid rgba(59,130,246,0.3); }
.badge-page   { background:rgba(148,163,184,0.12); color:#cbd5e1; border:1px solid rgba(148,163,184,0.2); }
.content-text {
    line-height: 1.65;
    color: #cbd5e1;
    font-size: 0.95rem;
    border-left: 3px solid #6366f1;
    padding-left: 14px;
    margin-top: 10px;
    white-space: pre-wrap;
}

/* ── CET Table ── */
.cet-table { width:100%; border-collapse:collapse; margin:14px 0; }
.cet-table th {
    background-color: rgba(99,102,241,0.1);
    color: #818cf8;
    text-align: left;
    padding: 10px;
    border-bottom: 2px solid rgba(99,102,241,0.2);
}
.cet-table td { padding:10px; border-bottom:1px solid rgba(255,255,255,0.05); }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #080d18 !important;
    border-right: 1px solid rgba(255,255,255,0.05);
}
.status-indicator {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    border-radius: 8px;
    background: rgba(30,41,59,0.6);
    border: 1px solid rgba(255,255,255,0.05);
    font-size: 0.83rem;
    color: #94a3b8;
    margin-bottom: 6px;
}
.dot-green { width:8px;height:8px;border-radius:50%;background:#10b981;box-shadow:0 0 8px #10b981; }
.dot-red   { width:8px;height:8px;border-radius:50%;background:#ef4444;box-shadow:0 0 8px #ef4444; }
.dot-yellow{ width:8px;height:8px;border-radius:50%;background:#f59e0b;box-shadow:0 0 8px #f59e0b; }

/* ── Agent pipeline diagram ── */
.pipeline {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-wrap: wrap;
    gap: 6px;
    padding: 18px;
    margin: 16px 0;
    background: rgba(15,23,42,0.5);
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.05);
}
.pipe-node {
    padding: 8px 16px;
    border-radius: 10px;
    font-size: 0.82rem;
    font-weight: 600;
    font-family: 'Outfit', sans-serif;
}
.pipe-arrow { color: #475569; font-size: 1.2rem; }
.pipe-router  { background:rgba(129,140,248,0.15);border:1px solid rgba(129,140,248,0.35);color:#a5b4fc; }
.pipe-tariff  { background:rgba(52,211,153,0.12);border:1px solid rgba(52,211,153,0.3);color:#6ee7b7; }
.pipe-route   { background:rgba(251,146,60,0.12);border:1px solid rgba(251,146,60,0.3);color:#fdba74; }
.pipe-llm     { background:rgba(192,132,252,0.12);border:1px solid rgba(192,132,252,0.3);color:#d8b4fe; }
.pipe-out     { background:rgba(96,165,250,0.12);border:1px solid rgba(96,165,250,0.3);color:#93c5fd; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 3. Sidebar
# ──────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/isometric/512/globe.png", width=76)
    st.markdown("### AfriTrade Agent")
    st.caption("ECOWAS Trader Intelligence Platform · Week 3")

    st.markdown("---")

    # ── Qdrant Health ──
    st.markdown("#### 🔗 Connections")
    try:
        qdrant_client = load_qdrant()
        qdrant_client.get_collections()
        st.markdown("""
        <div class="status-indicator">
            <span class="dot-green"></span><span>Qdrant Cloud: Connected</span>
        </div>""", unsafe_allow_html=True)
    except Exception as e:
        st.markdown("""
        <div class="status-indicator">
            <span class="dot-red"></span><span>Qdrant Cloud: Offline</span>
        </div>""", unsafe_allow_html=True)
        st.caption(f"Error: {e}")

    # ── Gemini API Key — auto-load from secrets, fallback to manual input ──
    st.markdown("---")
    st.markdown("#### 🤖 AI Reasoning")

    _gemini_from_secrets = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY", "")

    if _gemini_from_secrets:
        gemini_key_input = _gemini_from_secrets
        st.markdown("""
        <div class="status-indicator">
            <span class="dot-green"></span><span>Gemini: Auto-configured ✓</span>
        </div>""", unsafe_allow_html=True)
        st.caption("Key loaded from secrets.toml")
    else:
        gemini_key_input = st.text_input(
            "Gemini API Key",
            type="password",
            placeholder="AIza...",
            help="Paste your Google Gemini API key to enable LLM-powered reasoning and synthesis.",
            key="gemini_key"
        )
        if gemini_key_input:
            st.markdown("""
            <div class="status-indicator">
                <span class="dot-green"></span><span>Gemini: Key Provided ✓</span>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-indicator">
                <span class="dot-yellow"></span><span>Gemini: Rule-based fallback</span>
            </div>""", unsafe_allow_html=True)

    # ── Neo4j Config — auto-load from secrets, fallback to manual input ──
    st.markdown("---")
    st.markdown("#### 🗄️ Graph Database")

    _neo4j_uri_secret  = st.secrets.get("NEO4J_URI")      or os.getenv("NEO4J_URI", "")
    _neo4j_user_secret = st.secrets.get("NEO4J_USER")     or os.getenv("NEO4J_USER", "")
    _neo4j_pass_secret = st.secrets.get("NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD", "")

    if _neo4j_uri_secret and _neo4j_user_secret and _neo4j_pass_secret:
        neo4j_cfg = {"uri": _neo4j_uri_secret, "user": _neo4j_user_secret, "password": _neo4j_pass_secret}
        st.markdown("""
        <div class="status-indicator">
            <span class="dot-green"></span><span>Neo4j: Auto-configured ✓</span>
        </div>""", unsafe_allow_html=True)
        st.caption("Credentials loaded from secrets.toml")
    else:
        with st.expander("Configure Neo4j"):
            neo4j_uri   = st.text_input("Neo4j URI",      placeholder="neo4j+s://xxx.databases.neo4j.io", key="neo4j_uri")
            neo4j_user  = st.text_input("Neo4j Username", placeholder="neo4j", key="neo4j_user")
            neo4j_pass  = st.text_input("Neo4j Password", type="password", key="neo4j_pass")

        neo4j_cfg = None
        if neo4j_uri and neo4j_user and neo4j_pass:
            neo4j_cfg = {"uri": neo4j_uri, "user": neo4j_user, "password": neo4j_pass}
            st.markdown("""
            <div class="status-indicator">
                <span class="dot-green"></span><span>Neo4j: Config Provided ✓</span>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-indicator">
                <span class="dot-yellow"></span><span>Neo4j: Local graph fallback</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📘 How to Use")
    st.markdown("""
1. Type any trade question or click a quick query chip.
2. The **Router Agent** plans which tools to activate.
3. The **Tariff Tool** searches Qdrant; the **Route Tool** queries the graph database.
4. The **Answer Agent** synthesizes a final natural-language response.
    """)
    st.markdown("---")
    st.caption("Powered by LangGraph · Qdrant · NetworkX · Gemini")

# ──────────────────────────────────────────────
# 4. Hero Section
# ──────────────────────────────────────────────
st.markdown("""
<div class="hero-container">
    <div class="hero-title">🌍 AfriTrade Agent</div>
    <div class="hero-subtitle">Intelligent Agentic Trade Intelligence for ECOWAS Cross-Border Commerce</div>
    <span class="hero-badge">⚡ WEEK 3 — Powered by LangGraph Agentic Reasoning</span>
</div>
""", unsafe_allow_html=True)

# ── Agent Pipeline Diagram ──
st.markdown("""
<div class="pipeline">
    <div class="pipe-node pipe-out">User Query</div>
    <span class="pipe-arrow">→</span>
    <div class="pipe-node pipe-router">🧭 Router Agent</div>
    <span class="pipe-arrow">→</span>
    <div class="pipe-node pipe-tariff">📋 Tariff Tool<br><small>Qdrant VectorDB</small></div>
    <span class="pipe-arrow">+</span>
    <div class="pipe-node pipe-route">🛣️ Route Tool<br><small>Neo4j / NetworkX</small></div>
    <span class="pipe-arrow">→</span>
    <div class="pipe-node pipe-llm">🤖 Answer Agent<br><small>Gemini / Rules</small></div>
    <span class="pipe-arrow">→</span>
    <div class="pipe-node pipe-out">💬 Final Answer</div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 5. Tabs
# ──────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🤖 Agent Reasoning",
    "📋 CET Bands Reference",
    "💡 Senegal & Regional Rules"
])

# ──────────────────────────────────────────────
# TAB 1 — Agentic Reasoning
# ──────────────────────────────────────────────
with tab1:
    # Session state init
    for key, default in [
        ("agent_query", ""),
        ("trigger_agent", False),
        ("agent_result", None)
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # ── Suggestion Chips ──
    st.markdown("<p style='color:#94a3b8;font-weight:500;font-size:0.93rem;margin-bottom:8px;'>💡 Quick Queries:</p>", unsafe_allow_html=True)
    suggestions = [
        "What's the tariff on 50 smartphones from Lagos to Accra and the fastest route?",
        "Explain rice import duties and trade route from Abidjan to Bamako",
        "What products fall under the 35% duty band and how do I ship from Lagos to Dakar?"
    ]

    cols = st.columns(3)
    for idx, sug in enumerate(suggestions):
        with cols[idx]:
            if st.button(sug, key=f"chip_{idx}"):
                st.session_state.agent_query = sug
                st.session_state.trigger_agent = True
                st.session_state.agent_result = None
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Query Form ──
    with st.form(key="agent_form"):
        query_input = st.text_area(
            "Ask the agent:",
            value=st.session_state.agent_query,
            placeholder="e.g. What's the tariff on smartphones from Lagos to Accra and the fastest route?",
            height=90,
            label_visibility="collapsed"
        )
        submitted = st.form_submit_button("🤖 Run Agent Analysis", type="primary", use_container_width=True)

    if submitted:
        st.session_state.agent_query = query_input
        st.session_state.trigger_agent = True
        st.session_state.agent_result = None

    # ── Agent Execution ──
    if st.session_state.trigger_agent:
        q = st.session_state.agent_query.strip()
        if not q:
            st.warning("Please enter a query or click a suggestion chip.")
            st.session_state.trigger_agent = False
        else:
            # Animated thinking header
            with st.spinner("🔍 AfriTrade Agent is reasoning through your query…"):
                try:
                    from agentic_flow import run_agentic_flow
                    result = run_agentic_flow(
                        query=q,
                        gemini_api_key=gemini_key_input if gemini_key_input else None,
                        neo4j_config=neo4j_cfg
                    )
                    st.session_state.agent_result = result
                except Exception as e:
                    st.session_state.agent_result = {
                        "final_answer": f"Agent execution error: {e}",
                        "steps": [f"Critical error: {e}"],
                        "metadata": {}
                    }

            st.session_state.trigger_agent = False

    # ── Display Agent Results ──
    if st.session_state.agent_result:
        result = st.session_state.agent_result
        steps  = result.get("steps", [])
        answer = result.get("final_answer", "")
        meta   = result.get("metadata", {})

        st.markdown("---")
        st.markdown("### 🧠 Agent Reasoning Chain")

        # Map step keywords to icon + colour class
        def classify_step(text: str):
            t = text.lower()
            if "router"   in t: return ("🧭", "router")
            if "tariff"   in t: return ("📋", "tariff")
            if "route"    in t: return ("🛣️", "route")
            if "answer"   in t: return ("🤖", "answer")
            return ("ℹ️", "info")

        for step_text in steps:
            icon, cls = classify_step(step_text)
            st.markdown(f"""
            <div class="step-card {cls}">
                <div class="step-icon">{icon}</div>
                <div class="step-text">{step_text}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Final Answer ──
        st.markdown("""
        <div class="answer-box">
            <div class="answer-header">
                <span style="font-size:1.5rem;">💬</span>
                <span class="answer-label">AfriTrade Agent — Final Answer</span>
            </div>
        """, unsafe_allow_html=True)
        st.markdown(answer)
        st.markdown("</div>", unsafe_allow_html=True)

        # ── Metadata Expander ──
        with st.expander("🔍 Show Raw Tool Outputs"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Router Extraction**")
                st.json({
                    "commodity":        meta.get("commodity"),
                    "start_hub":        meta.get("start_hub"),
                    "end_hub":          meta.get("end_hub"),
                    "tariff_requested": meta.get("tariff_requested"),
                    "route_requested":  meta.get("route_requested"),
                })
            with col_b:
                st.markdown("**Route Results**")
                route_r = meta.get("route_results", {})
                st.json({
                    "path":             route_r.get("path", []),
                    "total_distance_km": route_r.get("total_distance_km"),
                    "total_time_hours": route_r.get("total_time_hours"),
                    "total_checkpoints": route_r.get("total_checkpoints"),
                    "source":           route_r.get("source"),
                })

            st.markdown("**Tariff Tool — Top Qdrant Matches**")
            tariff_r = meta.get("tariff_results", [])
            if tariff_r:
                for i, tr in enumerate(tariff_r, 1):
                    st.markdown(f"**{i}.** Score `{tr.get('score', 0):.2f}` · "
                                f"`{tr.get('source')}` p.{tr.get('page')}  ")
                    st.caption(tr.get("text", "")[:300])
            else:
                st.info("No Qdrant results retrieved.")

# ──────────────────────────────────────────────
# TAB 2 — CET Bands Reference
# ──────────────────────────────────────────────
with tab2:
    st.markdown("## 📋 ECOWAS Common External Tariff (CET)")
    st.markdown("""
The ECOWAS CET contains a **5-band tariff structure** designed to harmonise customs duties
across the West African sub-region (including Senegal, Mali, Côte d'Ivoire, and Nigeria).
    """)

    st.markdown("""
<table class="cet-table">
    <thead><tr>
        <th>Band</th><th>Category</th><th>Duty Rate</th><th>Product Examples</th>
    </tr></thead>
    <tbody>
        <tr><td><strong>Band 0</strong></td><td>Essential Social Goods</td><td>0%</td>
            <td>Books, educational materials, medicines, medical supplies.</td></tr>
        <tr><td><strong>Band 1</strong></td><td>Essential Goods & Raw Materials</td><td>5%</td>
            <td>Unprocessed raw materials, capital equipment, industrial machinery.</td></tr>
        <tr><td><strong>Band 2</strong></td><td>Intermediate Products</td><td>10%</td>
            <td>Semi-finished products, industrial inputs, chemical agents.</td></tr>
        <tr><td><strong>Band 3</strong></td><td>Finished Consumer Goods</td><td>20%</td>
            <td>Apparel, processed foods, smartphones, electronics, retail products.</td></tr>
        <tr><td><strong>Band 4</strong></td><td>Specific Goods for Economic Development</td><td>35%</td>
            <td>Sensitive commodities protecting local manufacturing (e.g. rice, poultry).</td></tr>
    </tbody>
</table>
    """, unsafe_allow_html=True)

    st.info("💡 **Rice Tariff Note:** Rice is typically classified at Band 4 (35%) to protect domestic farming. Member countries frequently apply national exemptions or quota systems — always verify with official customs authorities before cargo departure.")

# ──────────────────────────────────────────────
# TAB 3 — Senegal & Regional Rules
# ──────────────────────────────────────────────
with tab3:
    st.markdown("## 💡 Senegal Customs & ECOWAS Trade Rules")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🇸🇳 Senegal Specific Import Regimes")
        st.markdown("""
- **Rice Import Licensing:** Traders must coordinate with the *Direction du Commerce Extérieur* (DCE) to obtain import authorisations.
- **VAT (TVA):** Standard rate is 18% (essential agricultural products may be exempt).
- **Statistical Fee (Redevance Statistique):** 1% of CIF value.
- **Community Levy (PCS/PCC):** 1% ECOWAS/UEMOA community levy.
        """)

    with col2:
        st.markdown("### 🌍 ECOWAS Trade Liberalization Scheme (ETLS)")
        st.markdown("""
The **ETLS** is the primary tool for establishing a Free Trade Area:
- **Duty-Free Trade:** ECOWAS-originating products are exempt from customs duties when traded cross-border.
- **Rules of Origin:** To benefit, the trader must supply a **Certificate of Origin**, proving goods are:
  - Wholly obtained in the region (e.g. agricultural products), OR
  - Have undergone substantial local processing (≥30–35% regional value-added).
        """)

    st.warning("⚠️ **Notice to Traders:** Although ETLS promotes 0% duty for local goods, national authorities still apply internal taxes (VAT, statistical fees) and border controls. Always verify with official Customs authorities before departure.")
