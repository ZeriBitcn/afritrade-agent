import streamlit as st
from embeddings import MiniLMEmbeddingModel
from qdrant_client import QdrantClient
import os

# Configuration
COLLECTION_NAME = "ecowas_tariffs"

# Cache the model and qdrant client so they load only once
@st.cache_resource
def load_model():
    return MiniLMEmbeddingModel('sentence-transformers/all-MiniLM-L6-v2')

@st.cache_resource
def load_qdrant():
    url = st.secrets.get("QDRANT_URL")
    api_key = st.secrets.get("QDRANT_API_KEY")
    if not url or not api_key:
        url = os.getenv("QDRANT_URL")
        api_key = os.getenv("QDRANT_API_KEY")
    return QdrantClient(url=url, api_key=api_key)

# 1. Page Configuration
st.set_page_config(
    page_title="AfriTrade Agent | ECOWAS Tariff Lookup",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Premium Custom CSS Injection
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');

/* Font overrides */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif;
}

/* Background layout gradient */
.stApp {
    background: radial-gradient(circle at 90% 10%, rgba(37, 99, 235, 0.08), transparent 40%),
                radial-gradient(circle at 10% 90%, rgba(139, 92, 246, 0.08), transparent 40%),
                #0f172a;
    color: #f1f5f9;
}

/* Custom Scrollbars */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: rgba(15, 23, 42, 0.5);
}
::-webkit-scrollbar-thumb {
    background: rgba(99, 102, 241, 0.3);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(99, 102, 241, 0.5);
}

/* Hide default streamlit elements for custom branding */
header {visibility: hidden;}
footer {visibility: hidden;}

/* Custom Hero Layout */
.hero-container {
    text-align: center;
    padding: 2.5rem 1rem;
    margin-bottom: 2rem;
    background: rgba(30, 41, 59, 0.4);
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    backdrop-filter: blur(10px);
}

.hero-title {
    background: linear-gradient(135deg, #60a5fa, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3.2rem;
    font-weight: 800;
    margin: 0;
    line-height: 1.2;
}

.hero-subtitle {
    color: #94a3b8;
    font-size: 1.25rem;
    margin-top: 0.75rem;
    font-weight: 400;
}

/* Glassmorphic result cards */
.result-card {
    background: rgba(30, 41, 59, 0.35);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.result-card:hover {
    transform: translateY(-3px);
    border-color: rgba(96, 165, 250, 0.25);
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.3);
}

/* Result Badges */
.badge-container {
    margin-bottom: 14px;
}
.badge {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-right: 8px;
    margin-bottom: 8px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.badge-score {
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
}
.badge-source {
    background: rgba(59, 130, 246, 0.15);
    color: #60a5fa;
    border: 1px solid rgba(59, 130, 246, 0.3);
}
.badge-page {
    background: rgba(148, 163, 184, 0.12);
    color: #cbd5e1;
    border: 1px solid rgba(148, 163, 184, 0.2);
}

/* Styled text block */
.content-text {
    line-height: 1.6;
    color: #cbd5e1;
    font-size: 0.98rem;
    border-left: 3px solid #6366f1;
    padding-left: 16px;
    margin-top: 12px;
    white-space: pre-wrap;
}

/* Custom styled suggestion chips style for standard Streamlit columns */
div[data-testid="stHorizontalBlock"] button {
    background-color: rgba(30, 41, 59, 0.6) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 30px !important;
    color: #a5b4fc !important;
    font-size: 0.85rem !important;
    padding: 6px 16px !important;
    transition: all 0.25s ease !important;
    width: 100% !important;
    text-overflow: ellipsis !important;
    overflow: hidden !important;
    white-space: nowrap !important;
}
div[data-testid="stHorizontalBlock"] button:hover {
    background-color: rgba(99, 102, 241, 0.15) !important;
    border-color: rgba(99, 102, 241, 0.4) !important;
    color: #e0e7ff !important;
    transform: scale(1.02);
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #090d16 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}

.status-indicator {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    border-radius: 8px;
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.05);
    font-size: 0.85rem;
    color: #94a3b8;
}

.dot-green {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #10b981;
    box-shadow: 0 0 10px #10b981;
}

.dot-red {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #ef4444;
    box-shadow: 0 0 10px #ef4444;
}

.cet-table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
}
.cet-table th {
    background-color: rgba(99, 102, 241, 0.1);
    color: #818cf8;
    text-align: left;
    padding: 10px;
    border-bottom: 2px solid rgba(99, 102, 241, 0.2);
}
.cet-table td {
    padding: 10px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
</style>
""", unsafe_allow_html=True)

# 3. Sidebar Setup
with st.sidebar:
    st.image("https://img.icons8.com/isometric/512/globe.png", width=80)
    st.markdown("### AfriTrade Portal")
    st.caption("ECOWAS Trader Intelligence Platform")
    
    st.markdown("---")
    
    # Connection Health Check
    try:
        qdrant_client = load_qdrant()
        health = qdrant_client.get_collections()
        st.markdown("""
        <div class="status-indicator">
            <span class="dot-green"></span>
            <span>Qdrant Cloud: Connected</span>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f"""
        <div class="status-indicator">
            <span class="dot-red"></span>
            <span>Qdrant Cloud: Offline</span>
        </div>
        """, unsafe_allow_html=True)
        st.caption(f"Error: {e}")
        
    st.markdown("---")
    st.markdown("### 📘 How to Use")
    st.markdown("""
    1. Ask semantic questions about tariffs, commodity bands, import restrictions, or trade routes.
    2. Click any suggestion chip on the dashboard to pre-fill search requests.
    3. Review the parsed relevant document sections, source files, and page numbers.
    """)
    st.markdown("---")
    st.caption("Powered by Qdrant Vector Search + Sentence Transformers Model")

# 4. Hero Section
st.markdown("""
<div class="hero-container">
    <div class="hero-title">🌍 AfriTrade Agent</div>
    <div class="hero-subtitle">Intelligent Semantic Tariff Lookup for ECOWAS Cross-Border Commerce</div>
</div>
""", unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3 = st.tabs(["🔍 Tariff Semantic Search", "📋 CET Bands Reference", "💡 Senegal & Regional Rules"])

with tab1:
    # Query logic using Streamlit session state
    if "search_query" not in st.session_state:
        st.session_state.search_query = ""
    if "trigger_search" not in st.session_state:
        st.session_state.trigger_search = False

    # Suggestion Chips section
    st.markdown("<p style='color: #94a3b8; font-weight: 500; font-size: 0.95rem; margin-bottom: 8px;'>💡 Quick Queries:</p>", unsafe_allow_html=True)
    suggestions = [
        "What is the tariff on rice under ECOWAS CET?",
        "Explain the 5-band tariff structure",
        "What products fall under the 35% duty band?"
    ]
    
    cols = st.columns(3)
    for idx, sug in enumerate(suggestions):
        with cols[idx]:
            if st.button(sug, key=f"sug_btn_{idx}"):
                st.session_state.search_query = sug
                st.session_state.trigger_search = True
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Search Form
    with st.form(key="search_form"):
        query = st.text_input(
            "Enter tariff query:",
            value=st.session_state.search_query,
            placeholder="e.g. rate for polished rice import or ECOWAS customs duties...",
            label_visibility="collapsed"
        )
        submit_button = st.form_submit_button(label="🔍 Search Documents", type="primary")

    # Invalidate suggestion trigger if search button or standard submit occurs
    if submit_button:
        st.session_state.search_query = query
        st.session_state.trigger_search = True

    if st.session_state.trigger_search:
        if not st.session_state.search_query.strip():
            st.warning("Please write a search term or click a quick suggestion.")
            st.session_state.trigger_search = False
        else:
            with st.spinner("Analyzing ECOWAS CET files & computing embeddings..."):
                try:
                    # Initialize models
                    model = load_model()
                    qdrant = load_qdrant()
                    
                    # Compute vector representation of search
                    query_vector = model.encode(st.session_state.search_query).tolist()
                    
                    # Search vector DB
                    response = qdrant.query_points(
                        collection_name=COLLECTION_NAME,
                        query=query_vector,
                        limit=5
                    )
                    results = response.points
                    
                    st.markdown("<br><h3>🔍 Search Results</h3>", unsafe_allow_html=True)
                    
                    if results and results[0].score > 0.4:
                        # Top Match Hero display
                        best = results[0]
                        score = best.score
                        text = best.payload.get("text", "No text payload")
                        source = best.payload.get("source", "Unknown PDF")
                        page = best.payload.get("page", "N/A")
                        
                        st.markdown(f"""
                        <div class="result-card" style="border: 1px solid rgba(16, 185, 129, 0.3); background: rgba(16, 185, 129, 0.02);">
                            <div class="badge-container">
                                <span class="badge badge-score">🏆 Best Match (Score: {score:.2f})</span>
                                <span class="badge badge-source">📄 Source: {source}</span>
                                <span class="badge badge-page">Page: {page}</span>
                            </div>
                            <div class="content-text" style="border-left-color: #10b981;">{text}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Sub-matches
                        if len(results) > 1:
                            st.markdown("<h4>📚 Other Highly Relevant Sections</h4>", unsafe_allow_html=True)
                            for i, res in enumerate(results[1:], 2):
                                sub_score = res.score
                                sub_text = res.payload.get("text", "")
                                sub_source = res.payload.get("source", "Unknown PDF")
                                sub_page = res.payload.get("page", "N/A")
                                
                                st.markdown(f"""
                                <div class="result-card">
                                    <div class="badge-container">
                                        <span class="badge badge-score">Match {i} (Score: {sub_score:.2f})</span>
                                        <span class="badge badge-source">📄 {sub_source}</span>
                                        <span class="badge badge-page">Page {sub_page}</span>
                                    </div>
                                    <div class="content-text">{sub_text}</div>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.warning("Could not find highly matching segments. Try using different keywords or rephrasing your search.")
                        
                except Exception as e:
                    st.error(f"Failed to query database: {e}")
                    st.info("Ensure you have run the ingestion pipeline (`python ingest.py`) to initialize the database and upload vectors.")
            
            # Reset triggers
            st.session_state.trigger_search = False

with tab2:
    st.markdown("## 📋 ECOWAS Common External Tariff (CET)")
    st.markdown("""
    The ECOWAS CET contains a **5-band tariff structure** designed to harmonize customs duties across the West African sub-region (including Senegal, Mali, Côte d'Ivoire, and Nigeria).
    
    Below is the standard categorization of tariff rates under the ECOWAS framework:
    """)
    
    st.markdown("""
    <table class="cet-table">
        <thead>
            <tr>
                <th>Band</th>
                <th>Category</th>
                <th>Duty Rate</th>
                <th>Product Examples</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Band 0</strong></td>
                <td>Essential Social Goods</td>
                <td>0%</td>
                <td>Books, educational materials, medicines, specific medical supplies.</td>
            </tr>
            <tr>
                <td><strong>Band 1</strong></td>
                <td>Essential Goods & Raw Materials</td>
                <td>5%</td>
                <td>Unprocessed raw materials, capital equipment, industrial machinery.</td>
            </tr>
            <tr>
                <td><strong>Band 2</strong></td>
                <td>Intermediate Products</td>
                <td>10%</td>
                <td>Semi-finished products, industrial inputs, chemical agents.</td>
            </tr>
            <tr>
                <td><strong>Band 3</strong></td>
                <td>Finished Consumer Goods</td>
                <td>20%</td>
                <td>Standard finished goods, apparel, processed foods, retail products.</td>
            </tr>
            <tr>
                <td><strong>Band 4</strong></td>
                <td>Specific Goods for Economic Development</td>
                <td>35%</td>
                <td>Sensitive commodities, domestic manufacturing competitors (e.g., specific agricultural products like rice to protect local production).</td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)

    st.info("💡 **Rice Tariff Note:** Rice trade has experienced specific national variations. While the regional CET standard sets import tariffs to protect domestic agricultural sectors (often Band 4 at 35% or Band 2 depending on the category of raw/polished status), member countries frequently implement national adjustments or exemptions to control local inflation.")

with tab3:
    st.markdown("## 💡 Senegal Customs & ECOWAS Trade Rules")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🇸🇳 Senegal Specific Import Regimes")
        st.markdown("""
        Senegal implements a set of specific import regulations regarding sensitive food products:
        - **Rice Import Licensing:** Senegal operates a joint import quota system. To import rice from non-ECOWAS countries, traders must coordinate with the *Direction du Commerce Extérieur* (DCE) to obtain import authorizations.
        - **Taxes and levies (other than Customs Duties):**
            - **VAT (TVA):** Standard VAT rate is 18% (some essential agricultural products can be exempt).
            - **Statistical Fee (Redevance Statistique):** 1% of the CIF value.
            - **Community Levy (Prélèvement Communautaire - PCS/PCC):** 1% community levy for ECOWAS/UEMOA.
        """)
        
    with col2:
        st.markdown("### 🌍 ECOWAS Trade Liberalization Scheme (ETLS)")
        st.markdown("""
        The **ETLS** is the main tool of ECOWAS for establishing a Free Trade Area:
        - **Duty-Free Trade:** Products originating from ECOWAS member states are theoretically exempt from all customs duties and equivalent taxes when traded across borders (e.g. Senegal to Mali).
        - **Rules of Origin:** To benefit from ETLS duty-free status, the trader must supply a **Certificate of Origin** issued by the national authority, proving the goods are:
            - Wholly obtained in the region (e.g., agricultural products grown in Senegal), OR
            - Have undergone substantial local processing (at least 30-35% regional value-added).
        """)
        
    st.warning("⚠️ **Notice to Traders:** Although ETLS promotes 0% duty for local goods, national authorities still apply internal taxes (such as VAT or statistical fees) and border controls. Always verify details with official Customs authorities or the MENDEL database before cargo departure.")
