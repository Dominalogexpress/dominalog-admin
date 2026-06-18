"""Verificacao de autenticacao para cada pagina."""

import streamlit as st


def require_login():
    """Redireciona para home se nao autenticado."""
    if not st.session_state.get("authentication_status"):
        st.warning("Voce precisa fazer login para acessar esta pagina.")
        st.page_link("app.py", label="Ir para o Login", icon="🔐")
        st.stop()


def is_admin() -> bool:
    return st.session_state.get("role") == "admin"


def require_admin():
    require_login()
    if not is_admin():
        st.error("Acesso restrito a administradores.")
        st.stop()
