"""Gestao de usuarios do admin app (somente ADMIN)."""

import yaml
import bcrypt
import streamlit as st
from pathlib import Path
from yaml.loader import SafeLoader
from utils.auth_check import require_admin
from utils.ui import page_header, sidebar_nav

st.set_page_config(page_title="Usuarios · Dominalog Admin", page_icon="👤", layout="wide")
require_admin()
sidebar_nav()

page_header("Gestao de Usuarios", "Controle de acesso ao painel admin — somente administradores", "👤")

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.yaml"

def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.load(f, Loader=SafeLoader)

def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True)

config = load_config()
users = config["credentials"]["usernames"]

# ── Lista de usuarios ─────────────────────────────────────────────────────────
st.markdown(f"**{len(users)} usuario(s) cadastrado(s)**")

for uname, udata in list(users.items()):
    with st.expander(f"👤 {udata.get('name', uname)} ({uname}) — {'ADMIN' if udata.get('role')=='admin' else 'OPERADOR'}"):
        col1, col2, col3 = st.columns([2, 2, 1])
        col1.markdown(f"**Email:** {udata.get('email', '–')}")
        col2.markdown(f"**Role:** {udata.get('role', 'user')}")

        if uname != "admin":
            if col3.button("Remover", key=f"del_{uname}", type="primary"):
                del config["credentials"]["usernames"][uname]
                save_config(config)
                st.success(f"Usuario '{uname}' removido.")
                st.rerun()

st.divider()

# ── Adicionar usuario ─────────────────────────────────────────────────────────
st.markdown("#### Adicionar Novo Usuario")
with st.form("form_novo_usuario", clear_on_submit=True):
    c1, c2 = st.columns(2)
    novo_user  = c1.text_input("Username *", placeholder="joao.silva")
    novo_nome  = c2.text_input("Nome completo *")
    c3, c4     = st.columns(2)
    novo_email = c3.text_input("Email *")
    novo_role  = c4.selectbox("Permissao", ["user", "admin"])
    nova_senha = st.text_input("Senha inicial *", type="password")
    sub = st.form_submit_button("Criar Usuario", type="primary")

if sub:
    if not all([novo_user, novo_nome, novo_email, nova_senha]):
        st.error("Todos os campos sao obrigatorios.")
    elif novo_user in users:
        st.error(f"Username '{novo_user}' ja existe.")
    else:
        hashed = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt(12)).decode()
        config["credentials"]["usernames"][novo_user] = {
            "email": novo_email,
            "name": novo_nome,
            "password": hashed,
            "role": novo_role,
            "failed_login_attempts": 0,
            "logged_in": False,
        }
        save_config(config)
        st.success(f"Usuario '{novo_user}' criado! Senha inicial: {nova_senha}")

st.divider()

# ── Alterar senha ─────────────────────────────────────────────────────────────
st.markdown("#### Alterar Senha")
with st.form("form_senha", clear_on_submit=True):
    user_sel  = st.selectbox("Usuario", list(users.keys()))
    nova_s    = st.text_input("Nova senha *", type="password")
    conf_s    = st.text_input("Confirmar senha *", type="password")
    sub2 = st.form_submit_button("Alterar Senha", type="primary")

if sub2:
    if not nova_s or nova_s != conf_s:
        st.error("As senhas nao coincidem ou estao em branco.")
    else:
        hashed = bcrypt.hashpw(nova_s.encode(), bcrypt.gensalt(12)).decode()
        config["credentials"]["usernames"][user_sel]["password"] = hashed
        save_config(config)
        st.success(f"Senha de '{user_sel}' alterada com sucesso!")
