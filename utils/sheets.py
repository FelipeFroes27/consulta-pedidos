# utils/sheets.py

import streamlit as st
import pandas as pd
import gspread
import unicodedata
from datetime import date, datetime, timedelta, timezone
from google.oauth2.service_account import Credentials


SPREADSHEET_ID_PADRAO = "1JU-8v_mxydxgDFwWg_aSURHBeM0PyOQPkUBe-LqitXk"


def _spreadsheet_id():
    # Defina spreadsheet_id = "..." no secrets.toml (local e Streamlit Cloud) para trocar de base.
    return st.secrets.get("spreadsheet_id", SPREADSHEET_ID_PADRAO)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

# Linhas do Historico com "Data de recebimento" anterior a esta data foram gravadas
# pela versao antiga, que salvava a data do clique em "Data de entrega (sistema)".
# Para elas, o recebimento cobre todas as entregas do pedido agendadas ate aquela data.
INICIO_CONFIRMACAO_POR_DATA = date(2026, 11, 12)


class PlanilhaIndisponivel(RuntimeError):
    """A conta de servico nao consegue abrir a planilha configurada."""


@st.cache_resource
def conectar():

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )

    return gspread.authorize(creds)


@st.cache_resource
def abrir_planilha():
    try:
        return conectar().open_by_key(_spreadsheet_id())
    except (gspread.SpreadsheetNotFound, PermissionError) as exc:
        email = st.secrets["gcp_service_account"].get("client_email", "da conta de servico")
        raise PlanilhaIndisponivel(
            "Planilha não encontrada. Verifique se o spreadsheet_id nos secrets está correto "
            f"e se a planilha está compartilhada como Editor com {email}."
        ) from exc


ABA_PEDIDOS = ["Pedidos", "Pedido de compra"]
ABA_HISTORICO = "Histórico"
CABECALHO_HISTORICO = ["Pedido", "Data de entrega (sistema)", "Data de recebimento"]
ABA_PRODUTOS = "Produtos"
ABA_ETIQUETAS = "Etiquetas"
CABECALHO_ETIQUETAS = ["Gerado em", "Pedido", "Data agendada", "Codigo", "EAN", "Quantidade", "Copias"]


def _aba(*nomes, obrigatoria=True):
    planilha = abrir_planilha()
    for nome in nomes:
        try:
            return planilha.worksheet(nome)
        except gspread.WorksheetNotFound:
            continue
    if not obrigatoria:
        return None
    opcoes = " ou ".join(f'"{nome}"' for nome in nomes)
    raise PlanilhaIndisponivel(f"A planilha não tem a aba {opcoes}.")


def _registros(aba):
    if aba is None:
        return pd.DataFrame()
    return pd.DataFrame(aba.get_all_records(numericise_ignore=["all"]))


@st.cache_data(ttl=300)
def carregar_dados():

    return _registros(_aba(*ABA_PEDIDOS))


@st.cache_data(ttl=3600)
def carregar_produtos():
    """Cadastro de produtos com EAN, gravado pelo atualizar_pedidos_compra.py. Indexado pelo codigo."""
    df = _registros(_aba(ABA_PRODUTOS, obrigatoria=False))
    if df.empty or "Codigo" not in df.columns:
        return pd.DataFrame(columns=["Descricao", "Referencia", "EAN", "Outros EAN"])
    df["Codigo"] = df["Codigo"].fillna("").astype(str).str.strip().str.zfill(5)
    return df.drop_duplicates("Codigo").set_index("Codigo")


def registrar_etiquetas(linhas):
    """Historico de geracao: uma linha por item impresso (pedido, data, codigo, EAN, qtd, copias)."""
    if not linhas:
        return
    aba = _aba(ABA_ETIQUETAS, obrigatoria=False)
    if aba is None:
        aba = abrir_planilha().add_worksheet(ABA_ETIQUETAS, rows=1000, cols=len(CABECALHO_ETIQUETAS))
        aba.update([CABECALHO_ETIQUETAS], "A1")
    # Horario de Brasilia mesmo quando o app roda num servidor em UTC.
    gerado_em = datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")
    aba.append_rows([[gerado_em, *linha] for linha in linhas], value_input_option="RAW")


@st.cache_data(ttl=60)
def carregar_historico_recebimentos():
    return _registros(_aba(ABA_HISTORICO, obrigatoria=False))


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


# ==================================================
# RECEBIMENTOS (confirmacao por pedido + data agendada)
# ==================================================

def _para_data(valor):
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    convertida = pd.to_datetime(str(valor or "").strip(), errors="coerce", dayfirst=True)
    return None if pd.isna(convertida) else convertida.date()


class RecebimentosRegistrados:
    """Indice do Historico para saber se uma entrega (pedido + data) ja foi confirmada."""

    def __init__(self, historico):
        self._exatos = set()
        self._legado = {}
        self._sem_data = set()

        if historico is None or historico.empty:
            return

        coluna_pedido = _encontrar_coluna(historico, ["Pedido", "Numero do Pedido", "Número do Pedido"])
        if coluna_pedido is None:
            return
        coluna_entrega = _encontrar_coluna(historico, ["Data de entrega (sistema)"])
        coluna_recebimento = _encontrar_coluna(historico, ["Data de recebimento"])

        for _, linha in historico.iterrows():
            pedido = str(linha.get(coluna_pedido, "") or "").strip()
            if not pedido:
                continue

            entrega = _para_data(linha.get(coluna_entrega)) if coluna_entrega else None
            recebimento = _para_data(linha.get(coluna_recebimento)) if coluna_recebimento else None

            if entrega is None and recebimento is None:
                self._sem_data.add(pedido)
                continue

            if entrega is not None:
                self._exatos.add((pedido, entrega))

            referencia = recebimento or entrega
            if referencia < INICIO_CONFIRMACAO_POR_DATA:
                self._legado[pedido] = max(referencia, self._legado.get(pedido, referencia))

    def contem(self, pedido, data_agendada):
        pedido = str(pedido or "").strip()
        data_agendada = _para_data(data_agendada)
        if not pedido:
            return False
        if pedido in self._sem_data:
            return True
        if data_agendada is None:
            return False
        if (pedido, data_agendada) in self._exatos:
            return True
        limite_legado = self._legado.get(pedido)
        return limite_legado is not None and data_agendada <= limite_legado


def recebimentos_registrados():
    return RecebimentosRegistrados(carregar_historico_recebimentos())


def registrar_recebimentos(entregas):
    """Grava no Historico uma linha por (pedido, data agendada) ainda nao confirmada.

    Faz uma leitura do Historico e uma unica escrita em lote. Retorna quantas
    linhas foram gravadas.
    """
    pendentes = []
    vistos = set()
    for pedido, data_agendada in entregas:
        pedido = str(pedido or "").strip()
        data_agendada = _para_data(data_agendada)
        if not pedido or data_agendada is None or (pedido, data_agendada) in vistos:
            continue
        vistos.add((pedido, data_agendada))
        pendentes.append((pedido, data_agendada))

    if not pendentes:
        return 0

    aba = _aba(ABA_HISTORICO, obrigatoria=False)
    if aba is None:
        aba = abrir_planilha().add_worksheet(ABA_HISTORICO, rows=1000, cols=len(CABECALHO_HISTORICO))
        aba.update([CABECALHO_HISTORICO], "A1")
    valores = aba.get_all_values()
    headers = valores[0] if valores else []
    if not headers:
        raise ValueError("A aba Histórico está sem cabeçalho.")

    registrados = RecebimentosRegistrados(pd.DataFrame(valores[1:], columns=headers))
    pendentes = [(pedido, data_agendada) for pedido, data_agendada in pendentes if not registrados.contem(pedido, data_agendada)]
    if not pendentes:
        carregar_historico_recebimentos.clear()
        return 0

    data_recebimento = datetime.now().strftime("%d/%m/%Y")
    linhas = []
    for pedido, data_agendada in pendentes:
        linha = []
        for header in headers:
            header_normalizado = _normalizar_nome_coluna(header)
            if header_normalizado in ["pedido", "numero do pedido"]:
                linha.append(pedido)
            elif header_normalizado == "data de entrega (sistema)":
                linha.append(data_agendada.strftime("%d/%m/%Y"))
            elif header_normalizado == "data de recebimento":
                linha.append(data_recebimento)
            else:
                linha.append("")
        linhas.append(linha)

    aba.append_rows(linhas, value_input_option="RAW")
    carregar_historico_recebimentos.clear()
    return len(linhas)


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
