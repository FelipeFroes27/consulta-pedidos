# utils/sheets.py

import streamlit as st
import pandas as pd
import gspread
import unicodedata
from datetime import datetime
from google.oauth2.service_account import Credentials


SPREADSHEET_ID = "1JU-8v_mxydxgDFwWg_aSURHBeM0PyOQPkUBe-LqitXk"

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


@st.cache_resource
def abrir_planilha():
    return conectar().open_by_key(SPREADSHEET_ID)


@st.cache_data(ttl=300)
def carregar_dados():

    planilha = abrir_planilha()

    aba = planilha.worksheet("Pedidos")

    dados = aba.get_all_records(numericise_ignore=["all"])

    return pd.DataFrame(dados)


def carregar_historico_recebimentos():
    planilha = abrir_planilha()
    aba = planilha.worksheet("Histórico")
    dados = aba.get_all_records(numericise_ignore=["all"])
    return pd.DataFrame(dados)


@st.cache_data(ttl=300)
def carregar_volumetria():
    planilha = abrir_planilha()

    try:
        aba = planilha.worksheet("volumetria")
    except gspread.WorksheetNotFound:
        aba = planilha.worksheet("Volumetria")

    dados = aba.get_all_records(numericise_ignore=["all"])
    return pd.DataFrame(dados)


@st.cache_data(ttl=300)
def carregar_bd_produto():
    planilha = abrir_planilha()

    try:
        aba = planilha.worksheet("Bd_Produto")
    except gspread.WorksheetNotFound:
        aba = planilha.worksheet("Bd_Produtos")

    dados = aba.get_all_records(numericise_ignore=["all"])
    return pd.DataFrame(dados)


def localizar_pedido(numero_pedido):
    numero_pedido = str(numero_pedido or "").strip()
    if not numero_pedido:
        return pd.DataFrame()

    df = carregar_dados().copy()
    coluna_pedido = _encontrar_coluna(df, ["Numero do Pedido", "Número do Pedido", "Pedido"])
    if coluna_pedido is None:
        return pd.DataFrame()

    filtro = df[coluna_pedido].fillna("").astype(str).str.strip() == numero_pedido
    return df[filtro].copy()


def recebimento_ja_registrado(numero_pedido):
    numero_pedido = str(numero_pedido or "").strip()
    if not numero_pedido:
        return False

    historico = carregar_historico_recebimentos()
    if historico.empty:
        return False

    coluna_pedido = _encontrar_coluna(historico, ["Pedido", "Numero do Pedido", "Número do Pedido"])
    if coluna_pedido is None:
        return False

    return bool((historico[coluna_pedido].fillna("").astype(str).str.strip() == numero_pedido).any())


def registrar_recebimento(numero_pedido, pedido):
    numero_pedido = str(numero_pedido or "").strip()
    if not numero_pedido:
        raise ValueError("Informe o numero do pedido.")

    if recebimento_ja_registrado(numero_pedido):
        raise ValueError("Este pedido ja possui recebimento registrado.")

    planilha = abrir_planilha()
    aba = planilha.worksheet("Histórico")
    headers = aba.row_values(1)
    linha = []

    data_recebimento = datetime.now().strftime("%d/%m/%Y")

    for header in headers:
        header_normalizado = _normalizar_nome_coluna(header)
        if header_normalizado in ["pedido", "numero do pedido"]:
            linha.append(numero_pedido)
        elif header_normalizado == "data de entrega (sistema)":
            linha.append(data_recebimento)
        elif header_normalizado == "data de recebimento":
            linha.append(data_recebimento)
        else:
            linha.append("")

    aba.append_row(linha, value_input_option="RAW")


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


def _colunas_deduplicacao_embarques(df):
    coluna_numero = _encontrar_coluna(df, ["Numero", "NF", "Nota Fiscal"])
    coluna_embarque = _encontrar_coluna(df, ["Numero do embarque", "Embarque"])
    coluna_pedido_venda = _encontrar_coluna(df, ["Pedido de venda", "Pedido venda", "PV"])
    coluna_codigo_nome = _encontrar_coluna(df, ["Código - nome", "Codigo - nome", "Codigo nome", "Código nome"])
    colunas = [coluna_numero, coluna_embarque, coluna_pedido_venda, coluna_codigo_nome]
    return colunas if all(colunas) else None


def _adicionar_chaves_deduplicacao(df, colunas):
    coluna_numero, coluna_embarque, coluna_pedido_venda, coluna_codigo_nome = colunas
    df = df.copy()
    df["_dedup_numero"] = _texto_chave(df[coluna_numero])
    df["_dedup_embarque"] = _texto_chave(df[coluna_embarque])
    df["_dedup_pedido_venda"] = _texto_chave(df[coluna_pedido_venda])
    df["_dedup_codigo_nome"] = _texto_chave(df[coluna_codigo_nome])
    return df


def _remover_duplicados_embarques(df):
    colunas = _colunas_deduplicacao_embarques(df)

    if not colunas:
        return df

    linhas_antes = len(df)
    df = _adicionar_chaves_deduplicacao(df, colunas)
    df = (
        df.drop_duplicates(
            subset=["_dedup_numero", "_dedup_embarque", "_dedup_pedido_venda", "_dedup_codigo_nome"],
            keep="first",
        )
        .drop(columns=["_dedup_numero", "_dedup_embarque", "_dedup_pedido_venda", "_dedup_codigo_nome"])
        .copy()
    )
    st.session_state["embarques_duplicados_removidos"] = (
        st.session_state.get("embarques_duplicados_removidos", 0) + linhas_antes - len(df)
    )
    return df


def _linhas_duplicadas_embarques(df):
    colunas = _colunas_deduplicacao_embarques(df)
    if not colunas:
        return []

    df_chaves = _adicionar_chaves_deduplicacao(df, colunas)
    duplicadas = df_chaves.duplicated(
        subset=["_dedup_numero", "_dedup_embarque", "_dedup_pedido_venda", "_dedup_codigo_nome"],
        keep="first",
    )
    return [indice + 2 for indice, duplicada in enumerate(duplicadas) if duplicada]


def _agrupar_linhas_contiguas(linhas):
    if not linhas:
        return []

    ranges = []
    inicio = fim = linhas[0]

    for linha in linhas[1:]:
        if linha == fim + 1:
            fim = linha
        else:
            ranges.append((inicio, fim))
            inicio = fim = linha

    ranges.append((inicio, fim))
    return ranges


def _excluir_linhas_duplicadas_na_aba(aba, linhas):
    removidas = 0
    for inicio, fim in reversed(_agrupar_linhas_contiguas(sorted(linhas))):
        aba.delete_rows(inicio, fim)
        removidas += fim - inicio + 1
    return removidas


@st.cache_data(ttl=300)
def carregar_embarques():

    planilha = abrir_planilha()

    aba = planilha.worksheet("Embarques")

    dados = aba.get_all_records(numericise_ignore=["all"])
    df = pd.DataFrame(dados)
    st.session_state["embarques_duplicados_removidos"] = 0

    linhas_duplicadas = _linhas_duplicadas_embarques(df)
    if linhas_duplicadas:
        removidas = _excluir_linhas_duplicadas_na_aba(aba, linhas_duplicadas)
        st.session_state["embarques_duplicados_removidos"] = removidas
        dados = aba.get_all_records(numericise_ignore=["all"])
        df = pd.DataFrame(dados)

    return _remover_duplicados_embarques(df)
