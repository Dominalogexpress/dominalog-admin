"""Gestao da tabela dim_clientes (BD CLIENTES do Excel)."""

import streamlit as st
import pandas as pd
from utils.auth_check import require_login
from utils.ui import page_header, sidebar_nav
from utils.bq import read_table, insert_row, update_row, delete_row, upsert_dataframe

st.set_page_config(page_title="Clientes · Dominalog Admin", page_icon="👥", layout="wide")
require_login()
sidebar_nav()

TABLE = "bd_clientes"

page_header("Clientes", "Base de clientes pagadores — 1.500+ registros", "👥")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_ver, tab_add, tab_imp = st.tabs(["Visualizar / Editar", "Adicionar Novo", "Importar CSV"])

# ── Tab 1: Visualizar ─────────────────────────────────────────────────────────
with tab_ver:
    col_bus, col_grp, col_dep = st.columns([3, 2, 2])
    busca  = col_bus.text_input("Buscar cliente / CNPJ", placeholder="Digite parte do nome ou CNPJ...")
    grupos = col_grp.selectbox("Grupo", ["Todos", "GRUPO A", "GRUPO B", "GRUPO C", "GRUPO D"])
    dept   = col_dep.text_input("Departamento", placeholder="Ex: Eletrodomestico")

    with st.spinner("Carregando clientes..."):
        df = read_table(TABLE, order_by="cnpj_pagador")

    if df.empty:
        st.info("Nenhum registro encontrado. A tabela pode ainda nao ter sido carregada.")
    else:
        # Filtros
        if busca:
            mask = (
                df.astype(str).apply(lambda col: col.str.contains(busca, case=False, na=False)).any(axis=1)
            )
            df = df[mask]
        if grupos != "Todos":
            df = df[df["grupo"].str.upper() == grupos.upper()] if "grupo" in df.columns else df
        if dept:
            df = df[df["departamento"].str.contains(dept, case=False, na=False)] if "departamento" in df.columns else df

        st.caption(f"{len(df):,} registros exibidos")

        edited = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
            column_config={
                "cnpj_pagador":      st.column_config.TextColumn("CNPJ Pagador", width="medium"),
                "cliente_pagador":   st.column_config.TextColumn("Cliente Pagador", width="large"),
                "cliente_comercial": st.column_config.TextColumn("Nome Comercial", width="medium"),
                "cliente_chave":     st.column_config.TextColumn("Chave", width="medium"),
                "grupo":             st.column_config.SelectboxColumn("Grupo", options=["GRUPO A","GRUPO B","GRUPO C","GRUPO D","GRUPO E"]),
                "analista":          st.column_config.TextColumn("Analista", width="medium"),
                "departamento":      st.column_config.TextColumn("Departamento", width="medium"),
            },
            key="editor_clientes",
        )

        if st.button("Salvar alteracoes", type="primary", key="save_clientes"):
            with st.spinner("Salvando no BigQuery..."):
                ok = upsert_dataframe(TABLE, edited)
            if ok:
                st.success(f"Tabela atualizada com {len(edited):,} registros.")
                st.cache_resource.clear()

# ── Tab 2: Adicionar novo ─────────────────────────────────────────────────────
with tab_add:
    st.markdown("##### Novo Cliente")
    with st.form("form_novo_cliente", clear_on_submit=True):
        c1, c2 = st.columns(2)
        cnpj      = c1.text_input("CNPJ Pagador *", max_chars=20)
        nome_pag  = c2.text_input("Cliente Pagador *")
        c3, c4    = st.columns(2)
        nom_com   = c3.text_input("Nome Comercial")
        chave     = c4.text_input("Cliente Chave")
        c5, c6, c7 = st.columns(3)
        grupo     = c5.selectbox("Grupo", ["GRUPO A","GRUPO B","GRUPO C","GRUPO D","GRUPO E"])
        analista  = c6.text_input("Analista")
        depto     = c7.text_input("Departamento")
        hub_dev   = st.text_input("Hub Devolucao")
        submitted = st.form_submit_button("Adicionar Cliente", type="primary")

    if submitted:
        if not cnpj or not nome_pag:
            st.error("CNPJ e Nome do Cliente sao obrigatorios.")
        else:
            ok = insert_row(TABLE, {
                "cnpj_pagador": cnpj, "cliente_pagador": nome_pag,
                "cliente_comercial": nom_com, "cliente_chave": chave,
                "grupo": grupo, "analista": analista,
                "departamento": depto, "hub_devolucao": hub_dev,
            })
            if ok:
                st.success(f"Cliente '{nome_pag}' adicionado com sucesso!")

# ── Tab 3: Importar CSV ───────────────────────────────────────────────────────
with tab_imp:
    st.markdown("""
    ##### Importar lista de clientes via CSV
    O arquivo deve ter as colunas: `cnpj_pagador`, `cliente_pagador`, `cliente_comercial`, `cliente_chave`, `grupo`, `analista`, `departamento`
    """)
    uploaded = st.file_uploader("Selecione o arquivo CSV", type=["csv"])
    if uploaded:
        try:
            df_imp = pd.read_csv(uploaded, dtype=str)
            st.dataframe(df_imp.head(10), use_container_width=True)
            st.caption(f"{len(df_imp)} registros no arquivo")
            modo = st.radio("Modo de importacao", ["Adicionar aos existentes (APPEND)", "Substituir tudo (TRUNCATE)"])
            if st.button("Confirmar importacao", type="primary"):
                with st.spinner("Enviando para BigQuery..."):
                    if "TRUNCATE" in modo:
                        ok = upsert_dataframe(TABLE, df_imp)
                    else:
                        existing = read_table(TABLE)
                        combined = pd.concat([existing, df_imp], ignore_index=True)
                        ok = upsert_dataframe(TABLE, combined)
                if ok:
                    st.success(f"{len(df_imp)} clientes importados!")
        except Exception as e:
            st.error(f"Erro ao ler CSV: {e}")
