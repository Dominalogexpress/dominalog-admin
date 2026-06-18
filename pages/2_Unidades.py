"""Gestao da tabela dim_unidades (BD UNIDADES do Excel)."""

import streamlit as st
import pandas as pd
from utils.auth_check import require_login
from utils.ui import page_header, sidebar_nav
from utils.bq import read_table, insert_row, upsert_dataframe

st.set_page_config(page_title="Unidades · Dominalog Admin", page_icon="🏢", layout="wide")
require_login()
sidebar_nav()

TABLE = "bd_unidades"

page_header("Unidades", "Filiais, hubs e parceiros da rede Dominalog", "🏢")

tab_ver, tab_add = st.tabs(["Visualizar / Editar", "Adicionar Nova Unidade"])

with tab_ver:
    c1, c2, c3 = st.columns([2, 2, 2])
    busca    = c1.text_input("Buscar unidade", placeholder="Sigla ou cidade...")
    uf_filt  = c2.text_input("UF", max_chars=2, placeholder="Ex: SP")
    tipo_f   = c3.selectbox("Tipo", ["Todos", "PROPRIO", "PARCEIRO", "HUB", "FRANQUIA"])

    with st.spinner("Carregando unidades..."):
        df = read_table(TABLE, order_by="unidade")

    if not df.empty:
        if busca:
            df = df[df.astype(str).apply(lambda c: c.str.contains(busca, case=False, na=False)).any(axis=1)]
        if uf_filt:
            df = df[df["uf"].str.upper() == uf_filt.upper()] if "uf" in df.columns else df
        if tipo_f != "Todos" and "tipo_unidade" in df.columns:
            df = df[df["tipo_unidade"].str.upper() == tipo_f]

        st.caption(f"{len(df):,} unidades")

        edited = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
            column_config={
                "unidade":        st.column_config.TextColumn("Sigla", width="small"),
                "grupo_unidade":  st.column_config.TextColumn("Grupo", width="small"),
                "uf":             st.column_config.TextColumn("UF", width="small", max_chars=2),
                "regional":       st.column_config.TextColumn("Regional", width="medium"),
                "dono":           st.column_config.TextColumn("Dono", width="medium"),
                "responsavel":    st.column_config.TextColumn("Responsavel", width="medium"),
                "tipo_unidade":   st.column_config.SelectboxColumn("Tipo", options=["PROPRIO","PARCEIRO","HUB","FRANQUIA","FILIAL"]),
            },
            key="editor_unidades",
        )

        if st.button("Salvar alteracoes", type="primary"):
            ok = upsert_dataframe(TABLE, edited)
            if ok:
                st.success("Unidades atualizadas!")
    else:
        st.info("Tabela ainda nao carregada.")

with tab_add:
    st.markdown("##### Nova Unidade")
    with st.form("form_unidade", clear_on_submit=True):
        c1, c2 = st.columns(2)
        sigla    = c1.text_input("Sigla *", max_chars=5, placeholder="Ex: SPO")
        grupo    = c2.text_input("Grupo Unidade")
        c3, c4   = st.columns(2)
        uf       = c3.text_input("UF *", max_chars=2)
        regional = c4.text_input("Regional")
        c5, c6   = st.columns(2)
        dono     = c5.text_input("Dono")
        resp     = c6.text_input("Responsavel")
        tipo     = st.selectbox("Tipo", ["PROPRIO","PARCEIRO","HUB","FRANQUIA","FILIAL"])
        sub = st.form_submit_button("Adicionar Unidade", type="primary")

    if sub:
        if not sigla or not uf:
            st.error("Sigla e UF sao obrigatorios.")
        else:
            ok = insert_row(TABLE, {
                "unidade": sigla.upper(), "grupo_unidade": grupo,
                "uf": uf.upper(), "regional": regional,
                "dono": dono, "responsavel": resp, "tipo_unidade": tipo,
            })
            if ok:
                st.success(f"Unidade '{sigla.upper()}' adicionada!")
