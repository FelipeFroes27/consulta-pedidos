# utils/sheets.py

import streamlit as st
import pandas as pd
import gspread
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


@st.cache_data(ttl=300)
def carregar_embarques():

    gc = conectar()

    planilha = gc.open_by_key(
        "1JU-8v_mxydxgDFwWg_aSURHBeM0PyOQPkUBe-LqitXk"
    )

    aba = planilha.worksheet("Embarques")

    dados = aba.get_all_records(numericise_ignore=["all"])

    return pd.DataFrame(dados)
