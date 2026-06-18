"""Gestao do Centralizador de rotas."""

import streamlit as st
import pandas as pd
from utils.auth_check import require_login
from utils.ui import page_header, sidebar_nav
from utils.bq import read_table, insert_row, upsert_dataframe, append_dataframe, run_query

st.set_page_config(page_title="Centralizador · Dominalog Admin", page_icon="🗺", layout="wide")
require_login()
sidebar_nav()

TABLE = "centralizador"

page_header("Centralizador", "Rotas de entrega: origem, destino, prazo e frequencia", "🗺")

tab_ver, tab_add, tab_rep, tab_imp = st.tabs(["Visualizar / Editar", "Nova Rota", "Replicar Rota", "Importar CSV"])


@st.cache_data(ttl=300, show_spinner=False)
def listar_unidades():
    df_all = run_query(
        "SELECT DISTINCT origem AS und FROM `analytics-logistica.dw.centralizador` "
        "UNION DISTINCT "
        "SELECT DISTINCT destino AS und FROM `analytics-logistica.dw.centralizador` "
        "ORDER BY und"
    )
    if df_all.empty:
        return []
    return sorted(df_all["und"].dropna().tolist())

# ── Visualizar / Editar ───────────────────────────────────────────────────────
with tab_ver:
    c1, c2, c3 = st.columns([2, 2, 2])
    origem = c1.text_input("Origem", max_chars=5, placeholder="Ex: SAO")
    dest   = c2.text_input("Destino", max_chars=5, placeholder="Ex: CWB")
    canal  = c3.text_input("Canal", placeholder="Ex: ADR")

    with st.spinner("Carregando rotas..."):
        df = read_table(TABLE, order_by="rota", limit=3000)

    if not df.empty:
        cols_show = [c for c in ["rota","origem","destino","canal","frequencia","tempo_de_hub",
                                  "tempo_black_friday","hub_entrega","responsavel"] if c in df.columns]
        df_show = df[cols_show] if cols_show else df

        if origem:
            df_show = df_show[df_show["origem"].str.upper() == origem.upper()] if "origem" in df_show.columns else df_show
        if dest:
            df_show = df_show[df_show["destino"].str.upper() == dest.upper()] if "destino" in df_show.columns else df_show
        if canal:
            df_show = df_show[df_show["canal"].str.upper().str.contains(canal.upper(), na=False)] if "canal" in df_show.columns else df_show

        st.caption(f"{len(df_show):,} rotas")

        edited = st.data_editor(
            df_show,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
            column_config={
                "rota":               st.column_config.TextColumn("Rota", width="medium"),
                "origem":             st.column_config.TextColumn("Origem", width="small"),
                "destino":            st.column_config.TextColumn("Destino", width="small"),
                "canal":              st.column_config.TextColumn("Canal", width="small"),
                "frequencia":         st.column_config.NumberColumn("Freq/semana", min_value=0, max_value=7),
                "tempo_de_hub":       st.column_config.NumberColumn("Tempo Hub (dias)", min_value=0),
                "tempo_black_friday": st.column_config.NumberColumn("Tempo BF", min_value=0),
                "hub_entrega":        st.column_config.TextColumn("Hub Entrega", width="small"),
                "responsavel":        st.column_config.TextColumn("Responsavel", width="medium"),
            },
            key="editor_centralizador",
        )

        if st.button("Salvar alteracoes", type="primary"):
            if upsert_dataframe(TABLE, edited):
                st.success("Centralizador atualizado!")
    else:
        st.info("Tabela ainda nao carregada.")

# ── Nova Rota ─────────────────────────────────────────────────────────────────
with tab_add:
    st.markdown("##### Nova Rota")
    with st.form("form_rota", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        orig  = c1.text_input("Origem *", max_chars=5)
        dst   = c2.text_input("Destino *", max_chars=5)
        can   = c3.text_input("Canal *", max_chars=10)
        c4, c5, c6 = st.columns(3)
        freq  = c4.number_input("Frequencia/semana", min_value=0, max_value=7, value=3)
        t_hub = c5.number_input("Tempo de Hub (dias)", min_value=0, value=1)
        t_bf  = c6.number_input("Tempo Black Friday (dias)", min_value=0, value=2)
        c7, c8 = st.columns(2)
        hub_e = c7.text_input("Hub Entrega", max_chars=5)
        resp  = c8.text_input("Responsavel")
        sub   = st.form_submit_button("Adicionar Rota", type="primary")

    if sub:
        if not orig or not dst or not can:
            st.error("Origem, Destino e Canal sao obrigatorios.")
        else:
            rota_key = f"{orig.upper()}_{dst.upper()}"
            if insert_row(TABLE, {
                "rota": rota_key, "origem": orig.upper(), "destino": dst.upper(),
                "canal": can.upper(), "frequencia": str(freq),
                "tempo_de_hub": str(t_hub), "tempo_black_friday": str(t_bf),
                "hub_entrega": hub_e.upper(), "responsavel": resp,
            }):
                st.success(f"Rota '{rota_key}' adicionada!")

# ── Replicar Rota ─────────────────────────────────────────────────────────────
with tab_rep:
    st.markdown("""
    ##### Replicar rotas de uma unidade existente para uma nova unidade
    Copia todas as rotas de origem **ou** destino de uma unidade base e substitui
    apenas aquele campo pelo codigo da nova unidade. Os demais dados (canal, frequencia,
    tempo de hub, etc.) sao mantidos identicos.
    """)

    st.divider()

    col1, col2, col3 = st.columns([2, 2, 2])

    unidades = listar_unidades()

    nova_und  = col1.text_input("Nova unidade *", max_chars=5, placeholder="Ex: AAA",
                                 help="Codigo da nova unidade a ser criada").upper().strip()
    base_und  = col2.selectbox("Unidade base *", [""] + unidades,
                                help="Unidade cujas rotas serao copiadas")
    tipo_rep  = col3.radio("Replicar como", ["Origem", "Destino"],
                            help="Origem: copia rotas onde a base eh a origem, substituindo pelo novo codigo\n"
                                 "Destino: copia rotas onde a base eh o destino, substituindo pelo novo codigo")

    if nova_und and base_und:
        # Busca rotas da unidade base
        campo = "origem" if tipo_rep == "Origem" else "destino"
        df_base = run_query(
            f"SELECT * FROM `analytics-logistica.dw.centralizador` "
            f"WHERE {campo} = '{base_und}' ORDER BY rota"
        )

        if df_base.empty:
            st.warning(f"Nenhuma rota encontrada com {campo} = '{base_und}'.")
        else:
            # Gera preview das novas rotas
            df_novas = df_base.copy()
            df_novas[campo] = nova_und

            if tipo_rep == "Origem":
                df_novas["rota"] = nova_und + "_" + df_novas["destino"].astype(str)
            else:
                df_novas["rota"] = df_novas["origem"].astype(str) + "_" + nova_und

            # Verifica duplicatas
            rotas_novas = df_novas["rota"].tolist()
            df_exist = run_query(
                f"SELECT rota FROM `analytics-logistica.dw.centralizador` "
                f"WHERE rota IN ({', '.join(repr(r) for r in rotas_novas)})"
            )
            ja_existem = set(df_exist["rota"].tolist()) if not df_exist.empty else set()
            df_inserir  = df_novas[~df_novas["rota"].isin(ja_existem)]
            df_duplicadas = df_novas[df_novas["rota"].isin(ja_existem)]

            # Preview
            st.markdown(f"**Preview:** {len(df_base)} rotas de `{base_und}` → `{nova_und}` ({tipo_rep})")

            cols_prev = [c for c in ["rota","origem","destino","canal","frequencia","tempo_de_hub","hub_entrega"] if c in df_inserir.columns]
            st.dataframe(df_inserir[cols_prev], use_container_width=True, hide_index=True)

            if not df_duplicadas.empty:
                st.warning(f"{len(df_duplicadas)} rota(s) ja existem e serao ignoradas: {', '.join(df_duplicadas['rota'].tolist()[:10])}")

            if df_inserir.empty:
                st.error("Todas as rotas geradas ja existem. Nenhuma sera inserida.")
            else:
                st.info(f"**{len(df_inserir)} nova(s) rota(s)** serao inseridas.")

                if st.button(f"Confirmar — inserir {len(df_inserir)} rotas de {nova_und}", type="primary", key="btn_replicar"):
                    with st.spinner("Inserindo rotas no BigQuery..."):
                        ok = append_dataframe(TABLE, df_inserir)
                    if ok:
                        st.success(f"{len(df_inserir)} rotas de '{nova_und}' inseridas com sucesso!")
                        st.cache_data.clear()
                        st.balloons()
    elif nova_und and not base_und:
        st.info("Selecione a unidade base para visualizar o preview.")
    elif base_und and not nova_und:
        st.info("Digite o codigo da nova unidade.")

# ── Importar CSV ──────────────────────────────────────────────────────────────
with tab_imp:
    st.markdown("##### Importar rotas via CSV")
    st.markdown("Colunas esperadas: `rota`, `origem`, `destino`, `canal`, `frequencia`, `tempo_de_hub`, `hub_entrega`, `responsavel`")
    up = st.file_uploader("CSV de rotas", type=["csv"])
    if up:
        df_imp = pd.read_csv(up, dtype=str)
        st.dataframe(df_imp.head(10), use_container_width=True)
        modo = st.radio("Modo", ["Adicionar (APPEND)", "Substituir tudo (TRUNCATE)"])
        if st.button("Importar", type="primary"):
            if "TRUNCATE" in modo:
                ok = upsert_dataframe(TABLE, df_imp)
            else:
                existing = read_table(TABLE)
                ok = upsert_dataframe(TABLE, pd.concat([existing, df_imp], ignore_index=True))
            if ok:
                st.success(f"{len(df_imp)} rotas importadas!")
