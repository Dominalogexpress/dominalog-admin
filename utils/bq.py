"""BigQuery client e operacoes CRUD para o admin app."""

import os
from pathlib import Path
import pandas as pd
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

PROJECT  = "analytics-logistica"
DATASET  = "dw"
KEY_PATH = Path(__file__).resolve().parents[1] / "credentials" / "gcp-key.json"


@st.cache_resource(show_spinner=False)
def get_client() -> bigquery.Client:
    if KEY_PATH.exists():
        creds = service_account.Credentials.from_service_account_file(str(KEY_PATH))
        return bigquery.Client(project=PROJECT, credentials=creds)
    # Streamlit Cloud: usa st.secrets
    if "gcp" not in st.secrets:
        st.error("Credenciais GCP nao configuradas. Acesse Manage App > Settings > Secrets e adicione a secao [gcp].")
        st.stop()
    gcp_info = dict(st.secrets["gcp"])
    # Garante que private_key tem quebras de linha reais
    if "private_key" in gcp_info:
        gcp_info["private_key"] = gcp_info["private_key"].replace("\\n", "\n")
    creds = service_account.Credentials.from_service_account_info(gcp_info)
    return bigquery.Client(project=PROJECT, credentials=creds)


def read_table(table: str, order_by: str = None, limit: int = 5000) -> pd.DataFrame:
    client = get_client()
    sql = f"SELECT * FROM `{PROJECT}.{DATASET}.{table}`"
    if order_by:
        sql += f" ORDER BY {order_by}"
    if limit:
        sql += f" LIMIT {limit}"
    try:
        return client.query(sql).to_dataframe()
    except Exception as e:
        st.error(f"Erro ao ler tabela {table}: {e}")
        return pd.DataFrame()


def run_query(sql: str) -> pd.DataFrame:
    client = get_client()
    try:
        return client.query(sql).to_dataframe()
    except Exception as e:
        st.error(f"Erro na query: {e}")
        return pd.DataFrame()


def table_exists(table: str) -> bool:
    client = get_client()
    try:
        client.get_table(f"{PROJECT}.{DATASET}.{table}")
        return True
    except Exception:
        return False


def insert_row(table: str, row: dict) -> bool:
    client = get_client()
    cols = ", ".join(f"`{k}`" for k in row.keys())
    vals = ", ".join(
        f"NULL" if v is None or v == ""
        else f"'{str(v).replace(chr(39), chr(39)*2)}'"
        for v in row.values()
    )
    sql = f"INSERT INTO `{PROJECT}.{DATASET}.{table}` ({cols}) VALUES ({vals})"
    try:
        client.query(sql).result()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir: {e}")
        return False


def update_row(table: str, updates: dict, where: dict) -> bool:
    client = get_client()
    set_clause = ", ".join(
        f"`{k}` = NULL" if v is None or v == ""
        else f"`{k}` = '{str(v).replace(chr(39), chr(39)*2)}'"
        for k, v in updates.items()
    )
    where_clause = " AND ".join(
        f"`{k}` = '{str(v).replace(chr(39), chr(39)*2)}'"
        for k, v in where.items()
    )
    sql = f"UPDATE `{PROJECT}.{DATASET}.{table}` SET {set_clause} WHERE {where_clause}"
    try:
        client.query(sql).result()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")
        return False


def delete_row(table: str, where: dict) -> bool:
    client = get_client()
    where_clause = " AND ".join(
        f"`{k}` = '{str(v).replace(chr(39), chr(39)*2)}'"
        for k, v in where.items()
    )
    sql = f"DELETE FROM `{PROJECT}.{DATASET}.{table}` WHERE {where_clause}"
    try:
        client.query(sql).result()
        return True
    except Exception as e:
        st.error(f"Erro ao deletar: {e}")
        return False


def upsert_dataframe(table: str, df: pd.DataFrame) -> bool:
    """Substitui a tabela inteira pelo dataframe (WRITE_TRUNCATE)."""
    client = get_client()
    table_id = f"{PROJECT}.{DATASET}.{table}"
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_TRUNCATE",
        autodetect=True,
    )
    try:
        client.load_table_from_dataframe(df, table_id, job_config=job_config).result()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar tabela: {e}")
        return False


def count_rows(table: str) -> int:
    client = get_client()
    try:
        rows = client.query(
            f"SELECT COUNT(*) as n FROM `{PROJECT}.{DATASET}.{table}`"
        ).to_dataframe()
        return int(rows["n"].iloc[0])
    except Exception:
        return 0
