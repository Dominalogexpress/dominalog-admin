"""
Dominalog Admin — Gestao de Tabelas de Apoio
Ponto de entrada: autenticacao + dashboard home.
"""

import yaml
import streamlit as st
import streamlit_authenticator as stauth
from yaml.loader import SafeLoader
from pathlib import Path
from utils.ui import inject_css, LOGO, metric_row
from utils.bq import count_rows, table_exists

st.set_page_config(
    page_title="Dominalog Admin",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Carrega config de usuarios ────────────────────────────────────────────────
CONFIG_PATH = Path(__file__).parent / "config.yaml"

with open(CONFIG_PATH, encoding="utf-8") as f:
    config = yaml.load(f, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

# ── Login ─────────────────────────────────────────────────────────────────────
inject_css()

# Slot reservado no topo — preenchido só quando nao autenticado
header_slot = st.empty()

authenticator.login()

auth_status = st.session_state.get("authentication_status")
name       = st.session_state.get("name") or ""
username   = st.session_state.get("username") or ""

if not auth_status:
    with header_slot.container():
        st.markdown(LOGO, unsafe_allow_html=True)
        st.markdown("### Acesso Restrito")
        st.markdown("Entre com suas credenciais para acessar o painel de gestao.")
    if auth_status is False:
        st.error("Usuario ou senha incorretos.")
    st.stop()

# ── Salva role na session ─────────────────────────────────────────────────────
user_cfg = config["credentials"]["usernames"].get(username, {})
st.session_state["role"] = user_cfg.get("role", "user")
st.session_state["name"] = name

# ── Sidebar ───────────────────────────────────────────────────────────────────
from utils.ui import sidebar_nav
sidebar_nav()

with st.sidebar:
    st.markdown("---")
    authenticator.logout("Sair", "sidebar")

# ── Home Dashboard ────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom:1.5rem;">
    <h1 style="color:#0A2342; margin:0;">Painel de Gestao</h1>
    <p style="color:#666; margin:0;">Bem-vindo, <b>{name}</b>. Gerencie as tabelas de apoio da Dominalog Express.</p>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Contagem de registros ─────────────────────────────────────────────────────
st.markdown("#### Status das Tabelas Principais")

TABELAS_PRINCIPAIS = [
    ("bd_clientes",        "Clientes"),
    ("bd_unidades",        "Unidades"),
    ("centralizador",      "Centralizador"),
    ("405_entrega",        "Ocorr. Entrega"),
    ("519_coleta",         "Ocorr. Coleta"),
    ("prazo_de_entrega",   "Prazos Entrega"),
    ("feriados",           "Feriados"),
    ("pracas",             "Pracas"),
]

cols = st.columns(4)
for i, (tbl, label) in enumerate(TABELAS_PRINCIPAIS):
    with cols[i % 4]:
        if table_exists(tbl):
            n = count_rows(tbl)
            st.metric(label, f"{n:,}".replace(",", "."), "BQ")
        else:
            st.metric(label, "–", "nao carregada")

st.divider()

# ── Links rapidos ─────────────────────────────────────────────────────────────
st.markdown("#### Acesso Rapido")

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    **Operacional**
    - [👥 Clientes](/Clientes)
    - [🏢 Unidades](/Unidades)
    - [🗺 Centralizador](/Centralizador)
    """)
with col2:
    st.markdown("""
    **Configuracoes**
    - [📋 Ocorrencias](/Ocorrencias)
    - [⏱ Prazos](/Prazos)
    - [📅 Feriados](/Feriados)
    """)
with col3:
    st.markdown("""
    **Avancado / Admin**
    - [🗂 Outras Tabelas](/Avancado)
    - [👤 Usuarios](/Usuarios)
    """)

st.divider()
st.caption("Dominalog Express Logistica Integrada · Admin v2.0 · 2025")
