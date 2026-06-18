"""Gestao da tabela de feriados por unidade e UF."""

import streamlit as st
import pandas as pd
from datetime import date
from utils.auth_check import require_login
from utils.ui import page_header, sidebar_nav
from utils.bq import read_table, insert_row, upsert_dataframe

st.set_page_config(page_title="Feriados · Dominalog Admin", page_icon="📅", layout="wide")
require_login()
sidebar_nav()

TABLE = "feriados"

page_header("Feriados", "Calendario de feriados nacionais, estaduais e locais por unidade", "📅")

tab_ver, tab_add = st.tabs(["Visualizar / Editar", "Adicionar Feriado"])

# ── Visualizar ────────────────────────────────────────────────────────────────
with tab_ver:
    c1, c2, c3 = st.columns([2, 1, 2])
    ano  = c1.number_input("Ano", min_value=2020, max_value=2030, value=date.today().year)
    uf_f = c2.text_input("UF", max_chars=2, placeholder="Ex: SP")
    tipo_f = c3.selectbox("Tipo", ["Todos", "Nacional", "Estadual/Local"])

    # A tabela de feriados tem estrutura complexa — usamos apenas as colunas principais
    SQL = f"""
        SELECT
            feriados AS data,
            nome_do_feriado,
            tipo,
            abrangencia,
            uf_referencia,
            observacoes
        FROM `analytics-logistica.dw.{TABLE}`
        WHERE CAST(feriados AS STRING) LIKE '{ano}%'
           OR feriados IS NULL
        LIMIT 2000
    """

    from utils.bq import run_query
    with st.spinner("Carregando feriados..."):
        df = run_query(SQL)

    if df.empty:
        # Fallback: leitura simples
        df = read_table(TABLE, limit=500)
        # Tenta pegar colunas relevantes
        base_cols = ["feriados","nome_do_feriado","tipo","abrangencia","uf_referencia","observacoes"]
        df = df[[c for c in base_cols if c in df.columns]]

    if not df.empty:
        if uf_f and "uf_referencia" in df.columns:
            df = df[df["uf_referencia"].str.upper().str.contains(uf_f.upper(), na=False)]
        if tipo_f != "Todos" and "tipo" in df.columns:
            df = df[df["tipo"].str.contains(tipo_f[:8], case=False, na=False)]

        st.caption(f"{len(df):,} feriados em {ano}")
        edited = st.data_editor(
            df, use_container_width=True, num_rows="dynamic", hide_index=True,
            column_config={
                "data":             st.column_config.DateColumn("Data"),
                "nome_do_feriado":  st.column_config.TextColumn("Nome do Feriado", width="large"),
                "tipo":             st.column_config.SelectboxColumn("Tipo", options=["Nacional","Estadual/Local","Municipal"]),
                "abrangencia":      st.column_config.TextColumn("Abrangencia", width="medium"),
                "uf_referencia":    st.column_config.TextColumn("UF", width="small"),
                "observacoes":      st.column_config.TextColumn("Observacoes", width="medium"),
            },
            key="editor_feriados",
        )
        if st.button("Salvar feriados", type="primary"):
            if upsert_dataframe(TABLE, edited):
                st.success("Feriados atualizados!")
    else:
        st.info("Tabela de feriados ainda nao carregada.")

# ── Adicionar feriado ─────────────────────────────────────────────────────────
with tab_add:
    st.markdown("##### Novo Feriado")
    with st.form("form_feriado", clear_on_submit=True):
        c1, c2 = st.columns(2)
        dt_fer  = c1.date_input("Data *", value=date.today())
        nome    = c2.text_input("Nome do Feriado *")
        c3, c4, c5 = st.columns(3)
        tipo    = c3.selectbox("Tipo", ["Nacional","Estadual/Local","Municipal"])
        abrang  = c4.text_input("Abrangencia", placeholder="Ex: Unidades na BA")
        uf_ref  = c5.text_input("UF Referencia", max_chars=2, placeholder="Ex: BA ou Todos")
        obs     = st.text_area("Observacoes", height=80)
        sub     = st.form_submit_button("Adicionar Feriado", type="primary")

    if sub:
        if not nome:
            st.error("Nome do feriado e obrigatorio.")
        else:
            ok = insert_row(TABLE, {
                "feriados": str(dt_fer), "nome_do_feriado": nome,
                "tipo": tipo, "abrangencia": abrang,
                "uf_referencia": uf_ref, "observacoes": obs,
            })
            if ok:
                st.success(f"Feriado '{nome}' adicionado para {dt_fer.strftime('%d/%m/%Y')}!")
