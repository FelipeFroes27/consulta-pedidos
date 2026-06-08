# utils/sheets.py

import streamlit as st
import pandas as pd
import gspread
import unicodedata
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


@st.cache_resource
def conectar():

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )

    return gspread.authorize(creds)


@st.cache_data(ttl=300)
def carregar_dados():

    gc = conectar()

    planilha = gc.open_by_key(
        "1JU-8v_mxydxgDFwWg_aSURHBeM0PyOQPkUBe-LqitXk"
    )

    aba = planilha.worksheet("Pedidos")

    dados = aba.get_all_records(numericise_ignore=["all"])

    return pd.DataFrame(dados)


def _texto_chave(serie):
    return (
        serie.fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
        .str.replace(r"\s+", "", regex=True)
    )


def _normalizar_nome_coluna(nome):
    texto = unicodedata.normalize("NFKD", str(nome).strip().lower())
    return "".join(char for char in texto if not unicodedata.combining(char))


def _encontrar_coluna(df, nomes):
    mapa = {_normalizar_nome_coluna(coluna): coluna for coluna in df.columns}
    for nome in nomes:
        coluna = mapa.get(_normalizar_nome_coluna(nome))
        if coluna is not None:
            return coluna
    return None


def _remover_duplicados_embarques(df):
    coluna_numero = _encontrar_coluna(df, ["Numero", "NF", "Nota Fiscal"])
    coluna_codigo = _encontrar_coluna(df, ["Código", "Codigo", "Cdigo", "C?digo"])
    coluna_descricao = _encontrar_coluna(df, ["Descrição", "Descricao", "Descrio", "Descri??o"])
    coluna_quantidade = _encontrar_coluna(df, ["Quantidade", "Qtde", "Qtd"])

    st.session_state["embarques_duplicados_removidos"] = 0

    if not all([coluna_numero, coluna_codigo, coluna_descricao, coluna_quantidade]):
        return df

    df = df.copy()
    linhas_antes = len(df)
    df["_dedup_numero"] = _texto_chave(df[coluna_numero])
    df["_dedup_codigo"] = _texto_chave(df[coluna_codigo])
    df["_dedup_descricao"] = _texto_chave(df[coluna_descricao])
    df["_dedup_quantidade"] = pd.to_numeric(df[coluna_quantidade], errors="coerce").fillna(0).round(6)

    df = (
        df.drop_duplicates(
            subset=["_dedup_numero", "_dedup_codigo", "_dedup_descricao", "_dedup_quantidade"],
            keep="first",
        )
        .drop(columns=["_dedup_numero", "_dedup_codigo", "_dedup_descricao", "_dedup_quantidade"])
        .copy()
    )
    st.session_state["embarques_duplicados_removidos"] = linhas_antes - len(df)
    return df


@st.cache_data(ttl=300)
def carregar_embarques():

    gc = conectar()

    planilha = gc.open_by_key(
        "1JU-8v_mxydxgDFwWg_aSURHBeM0PyOQPkUBe-LqitXk"
    )

    aba = planilha.worksheet("Embarques")

    dados = aba.get_all_records(numericise_ignore=["all"])

    return _remover_duplicados_embarques(pd.DataFrame(dados))
