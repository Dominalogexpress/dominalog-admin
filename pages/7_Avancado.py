"""Tabelas avancadas: Pracas, CTRCs especiais, Prazos ajustados, Tempo Viagem/Hub, Placas."""

import streamlit as st
import pandas as pd
from utils.auth_check import require_login
from utils.ui import page_header, sidebar_nav
from utils.bq import read_table, upsert_dataframe, insert_row, run_query, table_exists

st.set_page_config(page_title="Avancado · Dominalog Admin", page_icon="🗂", layout="wide")
require_login()
sidebar_nav()

page_header("Tabelas Avancadas", "Pracas, CTRCs especiais, Prazos ajustados, Rotas e Placas fictícias", "🗂")

tabs = st.tabs(["Pracas", "CTRCs Especiais", "Prazos Ajustados", "Tempo Viagem", "Tempo Hub", "Placas Fictícias", "Dominio"])

# ── Pracas ────────────────────────────────────────────────────────────────────
with tabs[0]:
    with st.spinner("Carregando pracas..."):
        df = read_table("pracas", order_by="cidade", limit=2000)
    if not df.empty:
        c1, c2 = st.columns(2)
        cid = c1.text_input("Cidade", key="pc")
        uf  = c2.text_input("UF", max_chars=2, key="pu")
        if cid:
            df = df[df["cidade"].str.contains(cid, case=False, na=False)] if "cidade" in df.columns else df
        if uf:
            df = df[df["uf"].str.upper() == uf.upper()] if "uf" in df.columns else df
        st.caption(f"{len(df):,} pracas")
        ed = st.data_editor(df, use_container_width=True, num_rows="dynamic", hide_index=True, key="ed_prac")
        if st.button("Salvar Pracas", type="primary", key="sp"):
            if upsert_dataframe("pracas", ed):
                st.success("Pracas atualizadas!")

# ── CTRCs Especiais ───────────────────────────────────────────────────────────
with tabs[1]:
    st.info("CTRCs com TDE (Tempo de Entrega Especial) — 129K+ registros. Use busca por CTRC.")
    ctrc_bus = st.text_input("Buscar CTRC", key="ctrc_s")
    if ctrc_bus:
        df2 = run_query(f"""
            SELECT ctrc, tde FROM `analytics-logistica.dw.extras_ctrcs`
            WHERE ctrc LIKE '%{ctrc_bus}%' LIMIT 100
        """)
        if not df2.empty:
            st.dataframe(df2, use_container_width=True, hide_index=True)
        else:
            st.warning("CTRC nao encontrado.")

    st.divider()
    st.markdown("##### Adicionar CTRC especial")
    with st.form("f_ctrc", clear_on_submit=True):
        c1, c2 = st.columns(2)
        ctrc_n = c1.text_input("CTRC *")
        tden  = c2.number_input("TDE (dias)", min_value=0, max_value=365)
        if st.form_submit_button("Adicionar", type="primary"):
            if ctrc_n:
                if insert_row("extras_ctrcs", {"ctrc": ctrc_n, "tde": str(tden)}):
                    st.success(f"CTRC {ctrc_n} adicionado (TDE={tden})")

    st.divider()
    st.markdown("##### Importar lista de CTRCs via CSV")
    up = st.file_uploader("CSV com colunas: ctrc, tde", type=["csv"], key="up_ctrc")
    if up:
        df_up = pd.read_csv(up, dtype=str)
        st.dataframe(df_up.head(5), use_container_width=True)
        if st.button("Importar CTRCs (APPEND)", type="primary"):
            existing = read_table("extras_ctrcs")
            combined = pd.concat([existing, df_up], ignore_index=True)
            if upsert_dataframe("extras_ctrcs", combined):
                st.success(f"{len(df_up)} CTRCs importados!")

# ── Prazos Ajustados ──────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown("CTRCs com prazo de hub customizado (Prazo Ajustado).")
    ctrc_pa = st.text_input("Buscar CTRC", key="pa_s")
    if ctrc_pa:
        df3 = run_query(f"""
            SELECT ctrc, prazo_de_hub_novo FROM `analytics-logistica.dw.prazo_ajustado`
            WHERE ctrc LIKE '%{ctrc_pa}%' LIMIT 50
        """)
        if not df3.empty:
            ed3 = st.data_editor(df3, use_container_width=True, num_rows="dynamic", hide_index=True, key="ed_pa")
            if st.button("Salvar", type="primary", key="s_pa"):
                if upsert_dataframe("prazo_ajustado", ed3):
                    st.success("Prazos ajustados salvos!")
    st.divider()
    with st.form("f_pa", clear_on_submit=True):
        st.markdown("##### Adicionar prazo ajustado")
        c1, c2 = st.columns(2)
        ctrc_a = c1.text_input("CTRC *")
        prazo_a = c2.number_input("Novo Prazo (dias)", min_value=0)
        if st.form_submit_button("Adicionar", type="primary"):
            if ctrc_a:
                if insert_row("prazo_ajustado", {"ctrc": ctrc_a, "prazo_de_hub_novo": str(prazo_a)}):
                    st.success(f"Prazo ajustado para {ctrc_a}: {prazo_a} dias")

# ── Tempo Viagem ──────────────────────────────────────────────────────────────
with tabs[3]:
    with st.spinner("Carregando tempo de viagem..."):
        df4 = read_table("tempo_viagem", order_by="rota")
    if not df4.empty:
        st.caption(f"{len(df4):,} rotas")
        ed4 = st.data_editor(df4, use_container_width=True, num_rows="dynamic", hide_index=True,
            column_config={
                "origem":          st.column_config.TextColumn("Origem", width="small"),
                "destino":         st.column_config.TextColumn("Destino", width="small"),
                "rota":            st.column_config.TextColumn("Rota", width="medium"),
                "tempo_de_viagem": st.column_config.NumberColumn("Tempo (dias)", min_value=0),
            }, key="ed_tv")
        if st.button("Salvar Tempo Viagem", type="primary", key="s_tv"):
            if upsert_dataframe("tempo_viagem", ed4):
                st.success("Tempo de viagem atualizado!")

# ── Tempo Hub ─────────────────────────────────────────────────────────────────
with tabs[4]:
    with st.spinner("Carregando tempo de hub..."):
        df5 = read_table("tempo_hub", order_by="rota")
    if not df5.empty:
        st.caption(f"{len(df5):,} registros")
        ed5 = st.data_editor(df5, use_container_width=True, num_rows="dynamic", hide_index=True,
            column_config={
                "origem":      st.column_config.TextColumn("Origem", width="small"),
                "base":        st.column_config.TextColumn("Base", width="small"),
                "rota":        st.column_config.TextColumn("Rota", width="medium"),
                "frequencia":  st.column_config.NumberColumn("Frequencia", min_value=0),
                "tempo_de_hub":st.column_config.NumberColumn("Tempo Hub (dias)", min_value=0),
            }, key="ed_th")
        if st.button("Salvar Tempo Hub", type="primary", key="s_th"):
            if upsert_dataframe("tempo_hub", ed5):
                st.success("Tempo de hub atualizado!")

# ── Placas Fictícias ──────────────────────────────────────────────────────────
with tabs[5]:
    with st.spinner("Carregando placas fictícias..."):
        df6 = read_table("placas_ficticias", order_by="placa")
    if not df6.empty:
        st.caption(f"{len(df6):,} placas cadastradas")
        ed6 = st.data_editor(df6, use_container_width=True, num_rows="dynamic", hide_index=True,
            column_config={
                "placa":  st.column_config.TextColumn("Placa", width="small"),
                "status": st.column_config.SelectboxColumn("Status", options=["Placa Ficticia","Verificar","OK"]),
            }, key="ed_pf")
        if st.button("Salvar Placas", type="primary", key="s_pf"):
            if upsert_dataframe("placas_ficticias", ed6):
                st.success("Placas fictícias atualizadas!")

    with st.form("f_placa", clear_on_submit=True):
        st.markdown("##### Adicionar Placa")
        c1, c2 = st.columns(2)
        placa_n = c1.text_input("Placa *")
        stat_n  = c2.selectbox("Status", ["Placa Ficticia","Verificar"])
        if st.form_submit_button("Adicionar", type="primary"):
            if placa_n:
                if insert_row("placas_ficticias", {"placa": placa_n.upper(), "status": stat_n}):
                    st.success(f"Placa {placa_n.upper()} adicionada!")

# ── Dominio ───────────────────────────────────────────────────────────────────
with tabs[6]:
    with st.spinner("Carregando dominios..."):
        df7 = read_table("dominio", order_by="dominio")
    if not df7.empty:
        ed7 = st.data_editor(df7, use_container_width=True, num_rows="dynamic", hide_index=True, key="ed_dom")
        if st.button("Salvar Dominio", type="primary", key="s_dom"):
            if upsert_dataframe("dominio", ed7):
                st.success("Dominio atualizado!")
