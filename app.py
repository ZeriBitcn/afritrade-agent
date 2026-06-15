import streamlit as st
from embeddings import MiniLMEmbeddingModel
from qdrant_client import QdrantClient
import os
import base64
import uuid
import time
import analytics_tracker
import re
import io

# Helper to clean markdown for Text-To-Speech
def clean_markdown_for_tts(text: str) -> str:
    # Remove HTML tags if any
    text = re.sub(r'<[^>]*>', '', text)
    # Remove markdown link text brackets but keep the text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove bold, italics, code blocks formatting
    text = text.replace('**', '').replace('*', '').replace('`', '').replace('___', '').replace('__', '')
    # Remove headers formatting
    text = re.sub(r'#+\s+', '', text)
    # Remove bullets and list symbols
    text = re.sub(r'^\s*[-*+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
    # Remove excessive white spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
COLLECTION_NAME = "ecowas_tariffs"
groq_key_input = None

@st.cache_resource
def load_model():
    return MiniLMEmbeddingModel('sentence-transformers/all-MiniLM-L6-v2')

@st.cache_resource
def load_qdrant():
    url = st.secrets.get("QDRANT_URL") or os.getenv("QDRANT_URL") or "https://6350b241-255b-4967-b6fd-b6ba19d0bf47.sa-east-1-0.aws.cloud.qdrant.io"
    fallback_key_b64 = "ZXlKaGJHY2lPaUpJVXpJMU5pSXNJbkI1Y0NJNklrcFhWQ0o5LmV5SmhZMjRsY3NNaU9pSnRMV2xpWVdSMWNtVnlJanBiSW1Gd2FTMXJaWGk2TVRCbVlUWjJPRDF0T1RoaUxUUHlMVGd4WVRndE9EZG1ZekJqT1dKbE5UZzNJajAuT0h0YVFFUFhlbTZaVFpfY0taUGQ0Z0RvSW03R1FkZUZFSGtrV3EzQ2MxNA=="
    api_key = st.secrets.get("QDRANT_API_KEY") or os.getenv("QDRANT_API_KEY") or base64.b64decode(fallback_key_b64).decode("utf-8")
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
# Initialize Analytics
# ──────────────────────────────────────────────
analytics_tracker.init_db()

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

utm_source = None
try:
    utm_source = st.query_params.get("utm_source") or st.query_params.get("ref")
except AttributeError:
    try:
        params = st.experimental_get_query_params()
        utm_source = params.get("utm_source", [None])[0] or params.get("ref", [None])[0]
    except Exception:
        pass

referrer = "Direct/Organic"
if utm_source:
    if "whatsapp" in utm_source.lower() or "telegram" in utm_source.lower():
        referrer = "WhatsApp/Telegram Outreach"
    elif "linkedin" in utm_source.lower():
        referrer = "LinkedIn Campaign"
    elif "ambassador" in utm_source.lower() or "campus" in utm_source.lower():
        referrer = "Campus Ambassadors"
    else:
        referrer = utm_source

analytics_tracker.log_visitor(st.session_state.session_id, referrer)

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
        radial-gradient(circle at 85% 5%,  rgba(99,102,241,0.07), transparent 45%),
        radial-gradient(circle at 10% 95%, rgba(139,92,246,0.07), transparent 45%),
        #090d16;
    color: #f1f5f9;
}

/* Scrollbars */
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background: rgba(15,23,42,0.2); }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.25); border-radius:4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(99,102,241,0.45); }

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
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-left: none !important;
}
[data-testid="collapsedControl"]:hover,
[data-testid="stSidebarCollapsedControl"]:hover {
    background: rgba(99,102,241,0.2) !important;
    color: #a5b4fc !important;
}

/* ── Hero ── */
.hero-container {
    text-align: center;
    padding: 2.2rem 1rem 1.8rem;
    margin-bottom: 2rem;
    background: rgba(30,41,59,0.25);
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.05);
    backdrop-filter: blur(12px);
}
.hero-title {
    background: linear-gradient(135deg, #60a5fa, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.6rem;
    font-weight: 800;
    margin: 0;
    line-height: 1.2;
}
.hero-subtitle {
    color: #94a3b8;
    font-size: 1.05rem;
    margin-top: 0.6rem;
    font-weight: 400;
}

/* ── Suggestion chips ── */
div[data-testid="stHorizontalBlock"] button {
    background-color: rgba(30,41,59,0.4) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 20px !important;
    color: #a5b4fc !important;
    font-size: 0.8rem !important;
    padding: 6px 12px !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
}
div[data-testid="stHorizontalBlock"] button:hover {
    background-color: rgba(99,102,241,0.12) !important;
    border-color: rgba(99,102,241,0.3) !important;
    color: #e0e7ff !important;
    transform: translateY(-1px);
}

/* ── Response Box (ChatGPT / Perplexity style) ── */
.response-box {
    padding: 24px 28px;
    border-radius: 16px;
    background: rgba(30,41,59,0.35);
    border: 1px solid rgba(255,255,255,0.06);
    backdrop-filter: blur(12px);
    box-shadow: 0 12px 36px rgba(0,0,0,0.25);
    margin-top: 20px;
}
.response-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
.response-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.1rem;
    font-weight: 600;
    color: #e2e8f0;
}

/* ── Custom input styling ── */
div[data-testid="stTextArea"] textarea {
    background-color: rgba(30,41,59,0.5) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 12px !important;
    color: #f1f5f9 !important;
    font-size: 0.95rem !important;
    padding: 12px !important;
    transition: all 0.2s ease !important;
}
div[data-testid="stTextArea"] textarea:focus {
    border-color: rgba(99,102,241,0.4) !important;
    box-shadow: 0 0 0 2px rgba(99,102,241,0.2) !important;
}

/* ── Primary run button ── */
button[kind="primary"] {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    color: white !important;
    padding: 10px 24px !important;
    transition: all 0.25s ease !important;
}
button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(99,102,241,0.3) !important;
}

/* ── Result Cards ── */
.result-card {
    background: rgba(30,41,59,0.25);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 15px;
    transition: all 0.25s ease;
}
.result-card:hover {
    border-color: rgba(96,165,250,0.2);
    transform: translateY(-2px);
}
.badge-container { margin-bottom: 10px; }
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 600;
    margin-right: 6px;
    margin-bottom: 6px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.badge-score  { background:rgba(16,185,129,0.1); color:#34d399; border:1px solid rgba(16,185,129,0.2); }
.badge-source { background:rgba(59,130,246,0.1);  color:#60a5fa; border:1px solid rgba(59,130,246,0.2); }
.badge-page   { background:rgba(148,163,184,0.08); color:#cbd5e1; border:1px solid rgba(148,163,184,0.15); }
.content-text {
    line-height: 1.6;
    color: #cbd5e1;
    font-size: 0.92rem;
    border-left: 2px solid #6366f1;
    padding-left: 12px;
    margin-top: 8px;
    white-space: pre-wrap;
}

/* ── CET Table ── */
.cet-table { width:100%; border-collapse:collapse; margin:14px 0; font-size:0.9rem; }
.cet-table th {
    background-color: rgba(99,102,241,0.08);
    color: #818cf8;
    text-align: left;
    padding: 10px;
    border-bottom: 2px solid rgba(99,102,241,0.15);
}
.cet-table td { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.04); }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #060910 !important;
    border-right: 1px solid rgba(255,255,255,0.04);
}
.status-indicator {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 5px 10px;
    border-radius: 6px;
    background: rgba(30,41,59,0.4);
    border: 1px solid rgba(255,255,255,0.04);
    font-size: 0.8rem;
    color: #94a3b8;
    margin-bottom: 6px;
    width: 100%;
}
.dot-green { width:7px;height:7px;border-radius:50%;background:#10b981;box-shadow:0 0 6px #10b981; }
.dot-red   { width:7px;height:7px;border-radius:50%;background:#ef4444;box-shadow:0 0 6px #ef4444; }
.dot-yellow{ width:7px;height:7px;border-radius:50%;background:#f59e0b;box-shadow:0 0 6px #f59e0b; }

/* ── Footer ── */
.footer-container {
    text-align: center;
    margin-top: 60px;
    padding: 24px;
    border-top: 1px solid rgba(255, 255, 255, 0.04);
    color: #475569;
    font-size: 0.8rem;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 3. Sidebar
# ──────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/isometric/512/globe.png", width=64)
    st.markdown("### 🌍 AfriTrade AI")
    st.caption("Intelligent ECOWAS Trade Assistant")
    st.markdown("""
    AfriTrade AI helps custom brokers, cross-border traders, and logistics teams analyze import tariffs, discover optimal corridors, and understand customs rules across West Africa.
    """)

    st.markdown("---")
    st.markdown("#### 💡 Example Prompts")
    suggestions_sidebar = [
        "What's the tariff on 50 smartphones from Lagos to Accra?",
        "Explain rice import duties and trade route from Abidjan to Bamako",
        "How do I ship from Lagos to Dakar and what rules apply?"
    ]
    for idx, sug in enumerate(suggestions_sidebar):
        if st.button(sug, key=f"sidebar_chip_{idx}", use_container_width=True):
            st.session_state.agent_query = sug
            st.session_state.trigger_agent = True
            st.session_state.agent_result = None
            st.rerun()

    st.markdown("---")
    if st.button("🧹 Reset Assistant", use_container_width=True):
        st.session_state.agent_query = ""
        st.session_state.trigger_agent = False
        st.session_state.agent_result = None
        st.session_state.last_processed_audio_hash = None
        st.rerun()

    st.markdown("---")
    with st.expander("⚙️ System Status & Credentials"):
        # ── Qdrant Health ──
        st.markdown("**🔗 Connection Health**")
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
        st.markdown("**🤖 AI Reasoning**")
        _gemini_fallback_b64 = "QVEuQWI4Uk42SjIxb3ZXMllfMDlLdHFCVzBOeFBSQTlqQmxmbFJOVFVqZlBNOFl2R2NxRkE="
        _gemini_from_secrets = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or base64.b64decode(_gemini_fallback_b64).decode("utf-8")

        if _gemini_from_secrets:
            gemini_key_input = _gemini_from_secrets
            st.markdown("""
            <div class="status-indicator">
                <span class="dot-green"></span><span>Gemini: Auto-configured ✓</span>
            </div>""", unsafe_allow_html=True)
        else:
            gemini_key_input = st.text_input(
                "Gemini API Key",
                type="password",
                placeholder="AIza...",
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
                    <span class="dot-yellow"></span><span>Gemini: Fallback active</span>
                </div>""", unsafe_allow_html=True)

        # ── Neo4j Config — auto-load from secrets, fallback to manual input ──
        st.markdown("**🗄️ Graph Database**")
        _neo4j_uri_secret  = st.secrets.get("NEO4J_URI")      or os.getenv("NEO4J_URI", "")
        _neo4j_user_secret = st.secrets.get("NEO4J_USER")     or st.secrets.get("NEO4J_USERNAME") or os.getenv("NEO4J_USER", "")
        _neo4j_pass_secret = st.secrets.get("NEO4J_PASSWORD") or os.getenv("NEO4J_PASSWORD", "")

        if _neo4j_uri_secret and _neo4j_user_secret and _neo4j_pass_secret:
            neo4j_cfg = {"uri": _neo4j_uri_secret, "user": _neo4j_user_secret, "password": _neo4j_pass_secret}
            st.markdown("""
            <div class="status-indicator">
                <span class="dot-green"></span><span>Neo4j: Auto-configured ✓</span>
            </div>""", unsafe_allow_html=True)
        else:
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
                    <span class="dot-yellow"></span><span>Neo4j: Local graph active</span>
                </div>""", unsafe_allow_html=True)

        # ── Groq API Key — auto-load from secrets, fallback to manual input ──
        st.markdown("**🎙️ Voice Settings**")
        _groq_from_secrets = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

        if _groq_from_secrets:
            groq_key_input = _groq_from_secrets
            st.markdown("""
            <div class="status-indicator">
                <span class="dot-green"></span><span>Groq: Auto-configured ✓</span>
            </div>""", unsafe_allow_html=True)
        else:
            groq_key_input = st.text_input(
                "Groq API Key",
                type="password",
                placeholder="gsk_...",
                key="groq_key"
            )
            if groq_key_input:
                st.markdown("""
                <div class="status-indicator">
                    <span class="dot-green"></span><span>Groq: Key Provided ✓</span>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="status-indicator">
                    <span class="dot-yellow"></span><span>Voice Input: Disabled</span>
                </div>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 4. Hero Section
# ──────────────────────────────────────────────
st.markdown("""
<div class="hero-container">
    <div class="hero-title">🌍 AfriTrade AI</div>
    <div class="hero-subtitle">Intelligent ECOWAS Cross-Border Trade Assistant</div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 5. Tabs
# ──────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "💬 Chat Assistant",
    "📋 CET Tariff Reference",
    "📊 Analytics Insights"
])

# ──────────────────────────────────────────────
# TAB 1 — Chat Assistant
# ──────────────────────────────────────────────
with tab1:
    # Session state init
    for key, default in [
        ("agent_query", ""),
        ("trigger_agent", False),
        ("agent_result", None),
        ("last_processed_audio_hash", None)
    ]:
        if key not in st.session_state:
            st.session_state[key] = default

    # ── Suggestion Chips ──
    st.markdown("<p style='color:#94a3b8;font-weight:500;font-size:0.93rem;margin-bottom:8px;'>💡 Quick Queries:</p>", unsafe_allow_html=True)
    suggestions = [
        "What's the tariff on 50 smartphones from Lagos to Accra?",
        "Explain rice import duties and trade route from Abidjan to Bamako",
        "How do I ship from Lagos to Dakar and what rules apply?"
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

    # ── Voice Input & Speech-to-Text ──
    with st.expander("🎙️ Speak Your Query"):
        audio_value = st.audio_input("Record a voice message")
        if audio_value:
            audio_hash = hash(audio_value.getvalue())
            if st.session_state.get("last_processed_audio_hash") != audio_hash:
                if not groq_key_input:
                    st.error("Please configure a Groq API Key in the settings sidebar to use voice transcription.")
                else:
                    with st.spinner("🎙️ Transcribing voice query..."):
                        try:
                            from groq import Groq
                            client = Groq(api_key=groq_key_input)
                            transcription = client.audio.transcriptions.create(
                                file=("audio.wav", audio_value.getvalue(), "audio/wav"),
                                model="whisper-large-v3",
                                prompt="ECOWAS trade, tariffs, routes, Lagos, Accra, Abidjan, Bamako, Dakar, Lome, Cotonou",
                            )
                            text = transcription.text.strip()
                            if text:
                                st.session_state.agent_query = text
                                st.session_state.trigger_agent = True
                                st.session_state.agent_result = None
                                st.session_state.last_processed_audio_hash = audio_hash
                                st.rerun()
                        except Exception as e:
                            st.error(f"Transcription failed: {e}")

    # ── Query Form ──
    with st.form(key="agent_form"):
        query_input = st.text_area(
            "Ask the agent:",
            value=st.session_state.agent_query,
            placeholder="Ask anything about West African tariffs, custom rules, or transport routes...",
            height=90,
            label_visibility="collapsed"
        )
        submitted = st.form_submit_button("🤖 Analyze Trade Query", type="primary", use_container_width=True)

    if submitted:
        st.session_state.agent_query = query_input
        st.session_state.trigger_agent = True
        st.session_state.agent_result = None

        # ── Agent Execution ──
        if st.session_state.trigger_agent:
            q = st.session_state.agent_query.strip()
            if not q:
                st.warning("Please enter a query or click a suggestion prompt.")
                st.session_state.trigger_agent = False
            else:
                with st.spinner("Analyzing your request..."):
                    start_time = time.time()
                    success = True
                    err_msg = None
                    try:
                        from agentic_flow import run_agentic_flow
                        result = run_agentic_flow(
                            query=q,
                            gemini_api_key=gemini_key_input if gemini_key_input else None,
                            neo4j_config=neo4j_cfg
                        )
                        st.session_state.agent_result = result
                    except Exception as e:
                        success = False
                        err_msg = str(e)
                        st.session_state.agent_result = {
                            "final_answer": f"Analysis execution error: {e}",
                            "steps": [],
                            "metadata": {}
                        }
                    
                    latency = time.time() - start_time
                    meta = st.session_state.agent_result.get("metadata", {})
                    analytics_tracker.log_query(
                        session_id=st.session_state.session_id,
                        query=q,
                        latency=latency,
                        route_requested=meta.get("route_requested", False),
                        tariff_requested=meta.get("tariff_requested", False),
                        start_hub=meta.get("start_hub", ""),
                        end_hub=meta.get("end_hub", ""),
                        commodity=meta.get("commodity", ""),
                        success=success,
                        error_message=err_msg
                    )

                st.session_state.trigger_agent = False

    # ── Display Agent Results ──
    if st.session_state.agent_result:
        result = st.session_state.agent_result
        answer = result.get("final_answer", "")

        st.markdown(f"""
        <div class="response-box">
            <div class="response-header">
                <span style="font-size:1.3rem;">💬</span>
                <span class="response-title">Analysis Result</span>
            </div>
        """, unsafe_allow_html=True)
        st.markdown(answer)
        st.markdown("</div>", unsafe_allow_html=True)

        # ── Text-to-Speech Playback ──
        st.markdown("<br>", unsafe_allow_html=True)
        col_play, _ = st.columns([1, 2])
        with col_play:
            if st.button("🔊 Read Response Aloud", key="play_tts_button", use_container_width=True):
                with st.spinner("Synthesizing speech..."):
                    try:
                        from gtts import gTTS
                        import io
                        
                        clean_text = clean_markdown_for_tts(answer)
                        tts = gTTS(text=clean_text, lang='en', slow=False)
                        
                        fp = io.BytesIO()
                        tts.write_to_fp(fp)
                        fp.seek(0)
                        
                        st.audio(fp, format="audio/mp3", autoplay=True)
                    except Exception as tts_err:
                        st.error(f"Failed to generate audio: {tts_err}")

# ──────────────────────────────────────────────
# TAB 2 — CET Tariff Reference
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

    st.info("💡 **Rice Tariff Note:** Rice is classified at Band 4 (35%) to protect domestic farming. Member countries frequently apply national exemptions or quota systems — always verify with official customs authorities before cargo departure.")

    st.markdown("---")
    st.markdown("## 🇸🇳 Senegal & Regional Customs Rules")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Import Regimes & Fees")
        st.markdown("""
- **Rice Import Licensing:** Traders must coordinate with the *Direction du Commerce Extérieur* (DCE) to obtain import authorisations.
- **VAT (TVA):** Standard rate is 18% (essential agricultural products may be exempt).
- **Statistical Fee (Redevance Statistique):** 1% of CIF value.
- **Community Levy (PCS/PCC):** 1% ECOWAS/UEMOA community levy.
        """)
    with col2:
        st.markdown("### ECOWAS Trade Liberalization Scheme (ETLS)")
        st.markdown("""
The **ETLS** is the primary tool for establishing a Free Trade Area:
- **Duty-Free Trade:** ECOWAS-originating products are exempt from customs duties when traded cross-border.
- **Rules of Origin:** To benefit, the trader must supply a **Certificate of Origin**, proving goods are:
  - Wholly obtained in the region (e.g. agricultural products), OR
  - Have undergone substantial local processing (≥30–35% regional value-added).
        """)

    st.warning("⚠️ **Notice to Traders:** Although ETLS promotes 0% duty for local goods, national authorities still apply internal taxes (VAT, statistical fees) and border controls. Always verify with official Customs authorities before departure.")

# ──────────────────────────────────────────────
# TAB 3 — Analytics Insights
# ──────────────────────────────────────────────
with tab3:
    st.markdown("## 📊 Analytics Dashboard")
    st.markdown("Real-time usage metrics and organic distribution results for the AfriTrade Agent.")
    
    # Fetch metrics from database
    metrics = analytics_tracker.get_metrics()
    
    # Custom CSS for metrics cards
    st.markdown("""
    <style>
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin-bottom: 25px;
    }
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.75), rgba(15, 23, 42, 0.85));
        border: 1px solid rgba(99, 102, 241, 0.25);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        border-color: rgba(192, 132, 252, 0.45);
        box-shadow: 0 12px 40px rgba(99, 102, 241, 0.15);
    }
    .metric-val {
        font-family: 'Outfit', sans-serif;
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #60a5fa, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 4px;
    }
    .metric-lbl {
        font-family: 'Inter', sans-serif;
        color: #94a3b8;
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Metrics cards row
    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card">
            <div class="metric-val">{metrics["total_visitors"]}</div>
            <div class="metric-lbl">👥 Unique Visitors</div>
        </div>
        <div class="metric-card">
            <div class="metric-val">{metrics["total_queries"]}</div>
            <div class="metric-lbl">⚡ Queries Processed</div>
        </div>
        <div class="metric-card">
            <div class="metric-val">{metrics["avg_latency"]}s</div>
            <div class="metric-lbl">⏱️ Avg Latency</div>
        </div>
        <div class="metric-card">
            <div class="metric-val">{metrics["success_rate"]}%</div>
            <div class="metric-lbl">✅ Success Rate</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Visualizations row
    col_vis1, col_vis2 = st.columns(2)
    
    with col_vis1:
        st.markdown("### 🛣️ Top Queried Routes")
        if metrics["top_routes"]:
            import pandas as pd
            import plotly.express as px
            
            df_routes = pd.DataFrame(metrics["top_routes"])
            fig = px.bar(
                df_routes, 
                x="count", 
                y="route", 
                orientation="h",
                labels={"count": "Number of Queries", "route": "Route"},
                color="count",
                color_continuous_scale=["#60a5fa", "#c084fc"]
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#cbd5e1',
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(showgrid=False, autorange="reversed"),
                coloraxis_showscale=False,
                margin=dict(l=10, r=10, t=10, b=10),
                height=260
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No query route logs recorded yet.")
            
    with col_vis2:
        st.markdown("### 📢 User Acquisition by Referral Channel")
        if metrics["traffic_sources"]:
            import pandas as pd
            import plotly.express as px
            
            df_src = pd.DataFrame([
                {"Source": k, "Visitors": v} for k, v in metrics["traffic_sources"].items()
            ])
            fig_pie = px.pie(
                df_src, 
                values="Visitors", 
                names="Source",
                color_discrete_sequence=["#60a5fa", "#c084fc", "#34d399", "#f59e0b"]
            )
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#cbd5e1',
                margin=dict(l=10, r=10, t=10, b=10),
                height=260
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No traffic source logs recorded yet.")
            
    # Feature usage and recent logs row
    col_feat, col_log = st.columns([1, 2])
    
    with col_feat:
        st.markdown("### ⚙️ Feature Usage Breakdown")
        feat_data = metrics["feature_usage"]
        if sum(feat_data.values()) > 0:
            import pandas as pd
            import plotly.express as px
            
            df_feat = pd.DataFrame([
                {"Feature": k, "Queries": v} for k, v in feat_data.items()
            ])
            fig_feat = px.bar(
                df_feat,
                x="Feature",
                y="Queries",
                color="Feature",
                color_discrete_map={"Tariff Lookup": "#34d399", "Route Finder": "#fb923c"}
            )
            fig_feat.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#cbd5e1',
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                xaxis=dict(showgrid=False),
                showlegend=False,
                margin=dict(l=10, r=10, t=10, b=10),
                height=250
            )
            st.plotly_chart(fig_feat, use_container_width=True)
        else:
            st.info("No feature usage logs recorded yet.")
            
    with col_log:
        st.markdown("### 🕒 Recent User Queries")
        if metrics["recent_queries"]:
            import pandas as pd
            df_q = pd.DataFrame(metrics["recent_queries"])
            df_q.columns = ["Query", "Timestamp", "Latency", "Status", "Source Channel"]
            st.dataframe(df_q, use_container_width=True, hide_index=True)
        else:
            st.info("No queries logged yet.")

# ──────────────────────────────────────────────
# 6. Footer Section
# ──────────────────────────────────────────────
st.markdown("""
<div class="footer-container">
    <p>🌍 AfriTrade AI Agent · Powered by Africod Team</p>
</div>
""", unsafe_allow_html=True)
