"""Gestao das tabelas de ocorrencias (405-Entrega e 519-Coleta)."""

import streamlit as st
from utils.auth_check import require_login
from utils.ui import page_header, sidebar_nav
from utils.bq import read_table, update_row, upsert_dataframe

st.set_page_config(page_title="Ocorrencias · Dominalog Admin", page_icon="📋", layout="wide")
require_login()
sidebar_nav()

page_header("Ocorrencias", "Tabela de codigos 405-Entrega e 519-Coleta — status, etapa e classificacao", "📋")

tab405, tab519 = st.tabs(["405 - Entrega", "519 - Coleta"])

# ── 405 Entrega ───────────────────────────────────────────────────────────────
with tab405:
    TABLE = "405_entrega"

    c1, c2, c3 = st.columns([2, 2, 2])
    busca   = c1.text_input("Buscar codigo ou descricao", key="b405")
    status  = c2.selectbox("Status", ["Todos","em aberto","finalizado","cancelado"], key="s405")
    insuc   = c3.selectbox("Insucesso?", ["Todos","Sim","Nao"], key="i405")

    with st.spinner("Carregando ocorrencias 405..."):
        df = read_table(TABLE, order_by="codigo")

    if not df.empty:
        if busca:
            df = df[df.astype(str).apply(lambda c: c.str.contains(busca, case=False, na=False)).any(axis=1)]
        if status != "Todos" and "status" in df.columns:
            df = df[df["status"].str.lower() == status.lower()]
        if insuc != "Todos" and "insucesso_" in df.columns:
            df = df[df["insucesso_"].str.lower().str.contains(insuc[:3].lower(), na=False)]

        st.caption(f"{len(df):,} ocorrencias")

        edited = st.data_editor(
            df,
            use_container_width=True,
            num_rows="fixed",
            hide_index=True,
            column_config={
                "codigo":                    st.column_config.NumberColumn("Cod", width="small"),
                "descricao":                 st.column_config.TextColumn("Descricao", width="large"),
                "status":                    st.column_config.SelectboxColumn("Status", options=["em aberto","finalizado","cancelado"]),
                "etapa__perf_":              st.column_config.TextColumn("Etapa (Perf)", width="medium"),
                "situacao_agrupada":         st.column_config.TextColumn("Situacao Agrupada", width="medium"),
                "situacao":                  st.column_config.TextColumn("Situacao", width="medium"),
                "local":                     st.column_config.TextColumn("Local", width="medium"),
                "insucesso_":                st.column_config.TextColumn("Insucesso?", width="small"),
                "responsabilidade":          st.column_config.TextColumn("Responsabilidade", width="medium"),
                "status_indenizacao":        st.column_config.TextColumn("Status Indenizacao", width="medium"),
                "chamado":                   st.column_config.TextColumn("Chamado", width="medium"),
                "etapa__em_aberto__":        st.column_config.TextColumn("Etapa (Em Aberto)", width="medium"),
            },
            key="editor_405",
        )

        if st.button("Salvar 405", type="primary", key="save405"):
            ok = upsert_dataframe(TABLE, edited)
            if ok:
                st.success("Ocorrencias 405 atualizadas!")
    else:
        st.info("Tabela 405 ainda nao carregada.")

# ── 519 Coleta ────────────────────────────────────────────────────────────────
with tab519:
    TABLE2 = "519_coleta"

    with st.spinner("Carregando ocorrencias 519..."):
        df2 = read_table(TABLE2, order_by="codigo")

    if not df2.empty:
        edited2 = st.data_editor(
            df2,
            use_container_width=True,
            num_rows="fixed",
            hide_index=True,
            column_config={
                "codigo":             st.column_config.NumberColumn("Cod", width="small"),
                "descricao":          st.column_config.TextColumn("Descricao", width="large"),
                "status":             st.column_config.SelectboxColumn("Status", options=["finalizado","em aberto","cancelado"]),
                "situacao_agrupada":  st.column_config.TextColumn("Situacao Agrupada", width="medium"),
                "situacao":           st.column_config.TextColumn("Situacao", width="medium"),
                "etapa2":             st.column_config.TextColumn("Etapa", width="medium"),
            },
            key="editor_519",
        )

        if st.button("Salvar 519", type="primary", key="save519"):
            ok = upsert_dataframe(TABLE2, edited2)
            if ok:
                st.success("Ocorrencias 519 atualizadas!")
    else:
        st.info("Tabela 519 ainda nao carregada.")
