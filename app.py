"""
app.py

Streamlit frontend for the Multi-Modal Graph-Augmented RAG Engine.
Wraps the full backend pipeline (ingestion, graph building, retrieval, QA)
with an interactive UI and PyVis-based knowledge graph visualization.
"""
import os
import tempfile
import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
from pyvis.network import Network

# Backend imports
from ingestion_pipeline import process_document
from graph_builder import build_graph_and_index
from retriever import retrieve_context
from qa_generator import generate_answer

# ─────────────────────────────────────────────
# Page Configuration
# ─────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="Multi-Modal GraphRAG Engine",
    page_icon="🔬",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────
# Custom CSS for a polished, professional look
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Global font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .main-header h1 {
        margin: 0; font-size: 1.8rem; font-weight: 700;
        background: linear-gradient(90deg, #00f5a0, #00d9f5);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .main-header p { margin: 0.3rem 0 0 0; font-size: 0.9rem; opacity: 0.75; color: #ccc; }

    /* Answer card */
    .answer-card {
        background: linear-gradient(145deg, #1a1a2e, #16213e);
        border: 1px solid rgba(0, 245, 160, 0.25);
        border-radius: 12px;
        padding: 1.5rem;
        margin-top: 1rem;
        color: #e0e0e0;
        line-height: 1.7;
    }
    .answer-card strong { color: #00f5a0; }

    /* Citation badge */
    .citation-badge {
        display: inline-block;
        background: rgba(0, 245, 160, 0.15);
        border: 1px solid rgba(0, 245, 160, 0.4);
        color: #00f5a0;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-family: 'Courier New', monospace;
        margin: 2px 4px;
    }

    /* Status pill */
    .status-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    .status-ready {
        background: rgba(0, 245, 160, 0.15);
        color: #00f5a0;
        border: 1px solid rgba(0, 245, 160, 0.3);
    }
    .status-waiting {
        background: rgba(255, 193, 7, 0.15);
        color: #ffc107;
        border: 1px solid rgba(255, 193, 7, 0.3);
    }

    /* Graph container */
    .graph-container {
        border: 1px solid rgba(0, 217, 245, 0.2);
        border-radius: 12px;
        overflow: hidden;
        background: #0d1117;
    }

    /* Stats row */
    .stat-box {
        background: linear-gradient(145deg, #1a1a2e, #16213e);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .stat-box .stat-value {
        font-size: 1.6rem; font-weight: 700;
        background: linear-gradient(90deg, #00f5a0, #00d9f5);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .stat-box .stat-label { font-size: 0.75rem; color: #888; margin-top: 2px; }

    /* Streamlit overrides */
    .stTextInput > div > div > input {
        background-color: #1a1a2e !important;
        border: 1px solid rgba(0, 245, 160, 0.3) !important;
        color: white !important;
        border-radius: 8px !important;
    }
    div[data-testid="stFileUploader"] {
        border: 2px dashed rgba(0, 217, 245, 0.3) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Session State Initialization
# ─────────────────────────────────────────────
if "graph" not in st.session_state:
    st.session_state.graph = None
if "collection" not in st.session_state:
    st.session_state.collection = None
if "elements" not in st.session_state:
    st.session_state.elements = None
if "answer_result" not in st.session_state:
    st.session_state.answer_result = None
if "cited_ids" not in st.session_state:
    st.session_state.cited_ids = []
if "doc_name" not in st.session_state:
    st.session_state.doc_name = None
if "context_str" not in st.session_state:
    st.session_state.context_str = None


# ─────────────────────────────────────────────
# PyVis Graph Rendering with Explainability
# ─────────────────────────────────────────────
def render_interactive_graph(nx_graph: nx.DiGraph, highlighted_nodes=None) -> str:
    """
    Converts a NetworkX DiGraph into a PyVis interactive graph and returns the HTML string.
    
    If highlighted_nodes (a list of UUID strings) is provided, those nodes are
    rendered with neon green color and increased size for explainability.
    """
    if highlighted_nodes is None:
        highlighted_nodes = []

    highlighted_set = set(highlighted_nodes)

    net = Network(
        height="600px",
        width="100%",
        bgcolor="#0d1117",
        font_color="#c9d1d9",
        directed=True,
        notebook=False,
    )
    # Physics settings for a clean layout
    net.set_options("""
    {
        "nodes": {
            "borderWidth": 2,
            "borderWidthSelected": 4,
            "font": { "size": 11, "face": "Inter, sans-serif" }
        },
        "edges": {
            "color": { "inherit": false },
            "smooth": { "type": "curvedCW", "roundness": 0.2 },
            "arrows": { "to": { "enabled": true, "scaleFactor": 0.6 } }
        },
        "physics": {
            "forceAtlas2Based": {
                "gravitationalConstant": -80,
                "centralGravity": 0.015,
                "springLength": 120,
                "springConstant": 0.04,
                "damping": 0.85
            },
            "solver": "forceAtlas2Based",
            "stabilization": { "iterations": 150 }
        },
        "interaction": {
            "hover": true,
            "tooltipDelay": 100,
            "zoomView": true,
            "dragView": true
        }
    }
    """)

    # Color/shape map per element type
    type_config = {
        "TextElement":  {"color": "#58a6ff", "shape": "dot",     "base_size": 14},
        "TableElement": {"color": "#f78166", "shape": "diamond", "base_size": 20},
        "ImageElement": {"color": "#d2a8ff", "shape": "star",    "base_size": 22},
    }

    for node_id in nx_graph.nodes:
        data = nx_graph.nodes[node_id]
        el_type = data.get("element_type", "TextElement")
        cfg = type_config.get(el_type, type_config["TextElement"])
        page = data.get("page_number", "?")
        content_preview = data.get("content", "")[:80]

        is_highlighted = node_id in highlighted_set
        color = "#00f5a0" if is_highlighted else cfg["color"]
        size = cfg["base_size"] * (2.2 if is_highlighted else 1.0)
        border_color = "#00ff88" if is_highlighted else "#30363d"
        border_width = 4 if is_highlighted else 1

        label = f"P{page} | {el_type.replace('Element', '')}"
        title = (
            f"<b>{'⭐ CITED NODE' if is_highlighted else el_type}</b><br>"
            f"<b>ID:</b> {node_id[:12]}…<br>"
            f"<b>Page:</b> {page}<br>"
            f"<b>Preview:</b> {content_preview}…"
        )

        net.add_node(
            node_id,
            label=label,
            title=title,
            color={"background": color, "border": border_color,
                   "highlight": {"background": "#00f5a0", "border": "#00ff88"}},
            size=size,
            shape=cfg["shape"],
            borderWidth=border_width,
        )

    # Edge styling
    edge_colors = {
        "structural":       {"color": "#30363d", "width": 1.5},
        "semantic_support":  {"color": "#f0883e", "width": 2.5},
        "cross_reference":   {"color": "#00d9f5", "width": 3.0},
    }

    for u, v, data in nx_graph.edges(data=True):
        rel = data.get("relation_type", "structural")
        ecfg = edge_colors.get(rel, edge_colors["structural"])
        sim = data.get("similarity_score", None)
        edge_label = f"{sim:.2f}" if sim else ""

        net.add_edge(
            u, v,
            color=ecfg["color"],
            width=ecfg["width"],
            title=f"{rel}" + (f" (sim: {sim:.2f})" if sim else ""),
            label=edge_label,
        )

    # Generate HTML string
    html = net.generate_html()
    return html


# ─────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🔬 Multi-Modal GraphRAG Engine</h1>
    <p>Graph-Augmented Retrieval · Multimodal Document Intelligence · Explainable AI</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Two-Column Layout
# ─────────────────────────────────────────────
col1, col2 = st.columns([1, 1.4], gap="large")

# ═══════════════════════════════════════════════
# COLUMN 1 — Chat & Controls
# ═══════════════════════════════════════════════
with col1:
    st.markdown("### 📄 Document Upload")

    uploaded_file = st.file_uploader(
        "Upload a PDF document for analysis",
        type=["pdf"],
        key="pdf_uploader",
        help="The document will be parsed for text, tables, and images.",
    )

    # ── Ingestion trigger ──
    if uploaded_file is not None and uploaded_file.name != st.session_state.doc_name:
        with st.spinner("🔬 Processing document... Extracting text, tables & images..."):
            try:
                # Write uploaded file to a temporary location
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name

                # Phase 1: Ingestion
                elements = process_document(tmp_path)
                if not elements:
                    st.error("No elements could be extracted from this document.")
                    st.stop()

                st.session_state.elements = elements

                # Phase 2: Build graph and vector index
                graph, collection = build_graph_and_index(elements)
                st.session_state.graph = graph
                st.session_state.collection = collection
                st.session_state.doc_name = uploaded_file.name

                # Reset previous answer state
                st.session_state.answer_result = None
                st.session_state.cited_ids = []
                st.session_state.context_str = None

                # Cleanup temp file
                os.unlink(tmp_path)

                st.success(f"✅ Ingested **{len(elements)}** elements from `{uploaded_file.name}`")
            except Exception as e:
                st.error(f"Pipeline ingestion failed: {str(e)}")

    # ── Stats bar ──
    if st.session_state.graph is not None:
        g = st.session_state.graph
        els = st.session_state.elements or []

        text_count = sum(1 for e in els if type(e).__name__ == "TextElement")
        table_count = sum(1 for e in els if type(e).__name__ == "TableElement")
        image_count = sum(1 for e in els if type(e).__name__ == "ImageElement")

        s1, s2, s3, s4, s5 = st.columns(5)
        with s1:
            st.markdown(f'<div class="stat-box"><div class="stat-value">{g.number_of_nodes()}</div><div class="stat-label">Nodes</div></div>', unsafe_allow_html=True)
        with s2:
            st.markdown(f'<div class="stat-box"><div class="stat-value">{g.number_of_edges()}</div><div class="stat-label">Edges</div></div>', unsafe_allow_html=True)
        with s3:
            st.markdown(f'<div class="stat-box"><div class="stat-value">{text_count}</div><div class="stat-label">Text</div></div>', unsafe_allow_html=True)
        with s4:
            st.markdown(f'<div class="stat-box"><div class="stat-value">{table_count}</div><div class="stat-label">Tables</div></div>', unsafe_allow_html=True)
        with s5:
            st.markdown(f'<div class="stat-box"><div class="stat-value">{image_count}</div><div class="stat-label">Images</div></div>', unsafe_allow_html=True)

        st.markdown("---")

    # ── Query input ──
    st.markdown("### 💬 Ask a Question")

    pipeline_ready = st.session_state.graph is not None
    if pipeline_ready:
        st.markdown('<span class="status-pill status-ready">● Pipeline Ready</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-pill status-waiting">● Awaiting Document</span>', unsafe_allow_html=True)

    query = st.text_input(
        "Enter your question about the document:",
        placeholder="e.g. Why doesn't the regional revenue total match the quarterly total in the chart?",
        disabled=not pipeline_ready,
        key="query_input",
    )

    if st.button("🚀 Run Query", disabled=not pipeline_ready or not query, use_container_width=True):
        with st.spinner("🧠 Retrieving context & generating answer..."):
            try:
                context_str = retrieve_context(
                    query,
                    st.session_state.collection,
                    st.session_state.graph,
                )
                st.session_state.context_str = context_str

                result = generate_answer(query, context_str)
                st.session_state.answer_result = result
                st.session_state.cited_ids = result.get("cited_ids", [])
            except Exception as e:
                st.error(f"Query execution failed: {str(e)}")

    # ── Answer display ──
    if st.session_state.answer_result is not None:
        result = st.session_state.answer_result
        answer = result.get("answer", "No answer generated.")
        cited = result.get("cited_ids", [])

        st.markdown(f"""
        <div class="answer-card">
            <strong>Answer:</strong><br>
            {answer}
        </div>
        """, unsafe_allow_html=True)

        if cited:
            st.markdown("**📌 Cited Sources:**")
            for cid in cited:
                st.markdown(f'<span class="citation-badge">{cid[:12]}…</span>', unsafe_allow_html=True)

        # Expandable raw context view
        with st.expander("🔍 View Raw Context Payload sent to LLM"):
            st.code(st.session_state.context_str or "(empty)", language="text")


# ═══════════════════════════════════════════════
# COLUMN 2 — Graph Visualization
# ═══════════════════════════════════════════════
with col2:
    st.markdown("### 🕸️ Knowledge Graph")

    if st.session_state.graph is not None:
        g = st.session_state.graph
        cited = st.session_state.cited_ids

        if cited:
            st.markdown(
                f'Showing **{g.number_of_nodes()}** nodes · '
                f'**{len(cited)}** cited nodes <span class="status-pill status-ready">highlighted</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(f'Showing **{g.number_of_nodes()}** nodes · Submit a query to highlight cited sources.')

        # Render the interactive graph
        graph_html = render_interactive_graph(g, highlighted_nodes=cited)
        st.markdown('<div class="graph-container">', unsafe_allow_html=True)
        components.html(graph_html, height=620, scrolling=False)
        st.markdown('</div>', unsafe_allow_html=True)

        # Legend
        st.markdown("""
        <div style="display: flex; gap: 1.5rem; margin-top: 0.8rem; flex-wrap: wrap;">
            <span style="color: #58a6ff;">● Text</span>
            <span style="color: #f78166;">◆ Table</span>
            <span style="color: #d2a8ff;">★ Image</span>
            <span style="color: #00f5a0;">● Cited</span>
            <span style="color: #30363d;">─ Structural</span>
            <span style="color: #f0883e;">─ Semantic</span>
            <span style="color: #00d9f5;">─ Cross-Ref</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="
            display: flex; align-items: center; justify-content: center;
            height: 500px; border: 2px dashed rgba(0, 217, 245, 0.2);
            border-radius: 12px; color: #555; text-align: center;
        ">
            <div>
                <p style="font-size: 3rem; margin-bottom: 0.5rem;">🕸️</p>
                <p style="font-size: 1.1rem;">Upload a PDF to visualize<br>the Knowledge Graph</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
