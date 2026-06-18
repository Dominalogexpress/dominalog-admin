"""Gestao das tabelas de prazos: Entrega, Transferencia, Devolucao."""

import streamlit as st
import pandas as pd
from utils.auth_check import require_login
from utils.ui import page_header, sidebar_nav
from utils.bq import read_table, insert_row, upsert_dataframe

st.set_page_config(page_title="Prazos · Dominalog Admin", page_icon="⏱", layout="wide")
require_login()
sidebar_nav()

page_header("Prazos", "Prazos SLA de entrega, transferencia e devolucao por rota/unidade", "⏱")

tab_ent, tab_transf, tab_dev, tab_devAmz, tab_col = st.tabs([
    "Entrega (P/R/I)", "Transferencia", "Devolucao", "Devolucao Amazon", "Coleta"
])

# ── Prazo de Entrega ──────────────────────────────────────────────────────────
with tab_ent:
    TABLE = "prazo_de_entrega"
    c1, c2 = st.columns([3, 1])
    busca = c1.text_input("Buscar unidade", key="bpe")

    with st.spinner("Carregando prazos de entrega..."):
        df = read_table(TABLE, order_by="unidade")

    if not df.empty:
        if busca:
            df = df[df["unidade"].str.contains(busca, case=False, na=False)] if "unidade" in df.columns else df
        st.caption(f"{len(df):,} unidades configuradas")
        edited = st.data_editor(
            df, use_container_width=True, num_rows="dynamic", hide_index=True,
            column_config={
                "unidade": st.column_config.TextColumn("Unidade", width="small"),
                "p":       st.column_config.NumberColumn("P (Propria)", min_value=0),
                "r":       st.column_config.NumberColumn("R (Retirada)", min_value=0),
                "i":       st.column_config.NumberColumn("I (Interior)", min_value=0),
            },
            key="editor_prazos_entrega",
        )
        if st.button("Salvar prazos de entrega", type="primary", key="s_pe"):
            if upsert_dataframe(TABLE, edited):
                st.success("Prazos de entrega atualizados!")
    else:
        st.info("Tabela ainda nao carregada.")
        with st.form("f_pe"):
            c1, c2, c3, c4 = st.columns(4)
            u = c1.text_input("Unidade")
            p = c2.number_input("P", min_value=0)
            r = c3.number_input("R", min_value=0)
            i = c4.number_input("I", min_value=0)
            if st.form_submit_button("Adicionar"):
                insert_row(TABLE, {"unidade": u, "p": str(p), "r": str(r), "i": str(i)})

# ── Prazo Transferencia ───────────────────────────────────────────────────────
with tab_transf:
    TABLE2 = "prazo_transferencia"
    c1, c2 = st.columns(2)
    orig = c1.text_input("Origem", max_chars=5, key="pt_or")
    dst  = c2.text_input("Destino", max_chars=5, key="pt_ds")

    with st.spinner("Carregando prazos de transferencia..."):
        df2 = read_table(TABLE2, order_by="chave")

    if not df2.empty:
        if orig:
            df2 = df2[df2["origem"].str.upper() == orig.upper()] if "origem" in df2.columns else df2
        if dst:
            df2 = df2[df2["destino"].str.upper() == dst.upper()] if "destino" in df2.columns else df2
        st.caption(f"{len(df2):,} rotas")
        edited2 = st.data_editor(
            df2, use_container_width=True, num_rows="dynamic", hide_index=True,
            column_config={
                "chave":   st.column_config.TextColumn("Chave", width="medium"),
                "origem":  st.column_config.TextColumn("Origem", width="small"),
                "destino": st.column_config.TextColumn("Destino", width="small"),
                "prazo":   st.column_config.NumberColumn("Prazo (dias)", min_value=0),
            },
            key="editor_transf",
        )
        if st.button("Salvar transferencia", type="primary", key="s_tr"):
            if upsert_dataframe(TABLE2, edited2):
                st.success("Prazos de transferencia atualizados!")

# ── Prazo Devolucao ───────────────────────────────────────────────────────────
with tab_dev:
    TABLE3 = "prazos_dev"
    c1, c2 = st.columns(2)
    cid = c1.text_input("Cidade", key="pd_cid")
    uf  = c2.text_input("UF", max_chars=2, key="pd_uf")

    with st.spinner("Carregando prazos devolucao..."):
        df3 = read_table(TABLE3, order_by="cidade", limit=2000)

    if not df3.empty:
        if cid:
            df3 = df3[df3["cidade"].str.contains(cid, case=False, na=False)] if "cidade" in df3.columns else df3
        if uf:
            df3 = df3[df3["uf"].str.upper() == uf.upper()] if "uf" in df3.columns else df3
        st.caption(f"{len(df3):,} registros")
        edited3 = st.data_editor(
            df3, use_container_width=True, num_rows="dynamic", hide_index=True,
            column_config={
                "cidade":     st.column_config.TextColumn("Cidade", width="large"),
                "uf":         st.column_config.TextColumn("UF", width="small"),
                "devolucao":  st.column_config.NumberColumn("Devolucao (dias)", min_value=0),
                "reversa":    st.column_config.NumberColumn("Reversa (dias)", min_value=0),
            },
            key="editor_dev",
        )
        if st.button("Salvar devolucao", type="primary", key="s_dev"):
            if upsert_dataframe(TABLE3, edited3):
                st.success("Prazos de devolucao atualizados!")

# ── Amazon ────────────────────────────────────────────────────────────────────
with tab_devAmz:
    TABLE4 = "prazos_dev_amazon"
    with st.spinner("Carregando Amazon..."):
        df4 = read_table(TABLE4, order_by="cidade", limit=2000)
    if not df4.empty:
        st.caption(f"{len(df4):,} registros Amazon")
        edited4 = st.data_editor(df4, use_container_width=True, num_rows="dynamic", hide_index=True, key="editor_amz")
        if st.button("Salvar Amazon", type="primary", key="s_amz"):
            if upsert_dataframe(TABLE4, edited4):
                st.success("Prazos Amazon atualizados!")

# ── Prazos Coleta ─────────────────────────────────────────────────────────────
with tab_col:
    TABLE5 = "prazos_coleta"
    with st.spinner("Carregando prazos coleta..."):
        df5 = read_table(TABLE5, order_by="chave")
    if not df5.empty:
        st.caption(f"{len(df5):,} registros")
        edited5 = st.data_editor(df5, use_container_width=True, num_rows="dynamic", hide_index=True, key="editor_pcol")
        if st.button("Salvar coleta", type="primary", key="s_pcol"):
            if upsert_dataframe(TABLE5, edited5):
                st.success("Prazos de coleta atualizados!")
