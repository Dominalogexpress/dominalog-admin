"""Componentes de UI reutilizaveis e CSS do Dominalog Admin."""

import streamlit as st

LOGO = """
<div style="
    background: linear-gradient(135deg, #0A2342 0%, #1a3a5c 100%);
    padding: 1.2rem 1.5rem;
    border-radius: 10px;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1rem;
">
    <div style="font-size:2rem;">🚛</div>
    <div>
        <div style="color:#FF6B00; font-size:1.4rem; font-weight:800; letter-spacing:2px;">DOMINALOG</div>
        <div style="color:#ffffff99; font-size:0.75rem; letter-spacing:1px;">EXPRESS LOGÍSTICA · GESTÃO DE DADOS</div>
    </div>
</div>
"""

CSS = """
<style>
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0A2342 0%, #0d2d52 100%);
    }
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stRadio label {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] hr { border-color: #ffffff30; }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: #F0F4F8;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        border-left: 4px solid #FF6B00;
    }

    /* Buttons */
    .stButton > button[kind="primary"] {
        background-color: #FF6B00;
        border: none;
        border-radius: 6px;
        font-weight: 600;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #e05a00;
    }

    /* Success / Error toasts */
    .success-box {
        background: #d4edda; color: #155724;
        border: 1px solid #c3e6cb; border-radius: 6px;
        padding: 0.75rem 1rem; margin: 0.5rem 0;
    }
    .error-box {
        background: #f8d7da; color: #721c24;
        border: 1px solid #f5c6cb; border-radius: 6px;
        padding: 0.75rem 1rem; margin: 0.5rem 0;
    }

    /* Table header */
    .page-header {
        border-bottom: 3px solid #FF6B00;
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem;
    }
    .page-header h2 { color: #0A2342; margin: 0; }
    .page-header p { color: #666; margin: 0.2rem 0 0 0; font-size: 0.9rem; }

    /* Hide streamlit menu in prod */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }

    /* Data editor */
    [data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", icon: str = ""):
    inject_css()
    st.markdown(f"""
    <div class="page-header">
        <h2>{icon} {title}</h2>
        {"<p>" + subtitle + "</p>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)


def sidebar_nav():
    inject_css()
    with st.sidebar:
        st.markdown(LOGO, unsafe_allow_html=True)
        name = st.session_state.get("name", "Usuário")
        role = st.session_state.get("role", "user")
        st.markdown(f"""
        <div style="color:#fff; padding:0.5rem 0; border-bottom:1px solid #ffffff30; margin-bottom:1rem;">
            <b>{name}</b><br>
            <span style="font-size:0.75rem; color:#FF6B00;">{'ADMIN' if role=='admin' else 'OPERADOR'}</span>
        </div>
        """, unsafe_allow_html=True)


def metric_row(metrics: list):
    """metrics: list of (label, value, delta=None)"""
    cols = st.columns(len(metrics))
    for col, (label, value, *rest) in zip(cols, metrics):
        delta = rest[0] if rest else None
        col.metric(label, value, delta)


def confirm_delete(key: str) -> bool:
    """Returns True when user confirms deletion."""
    if st.session_state.get(f"confirm_{key}"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirmar exclusao", key=f"yes_{key}", type="primary"):
                st.session_state.pop(f"confirm_{key}", None)
                return True
        with col2:
            if st.button("Cancelar", key=f"no_{key}"):
                st.session_state.pop(f"confirm_{key}", None)
                st.rerun()
    return False
