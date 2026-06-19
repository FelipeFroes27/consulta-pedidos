from html import escape

import pandas as pd
import streamlit as st

from utils.display_mode import ativar_modo_exibicao, render_menu_lateral
from utils.sheets import localizar_pedido, recebimento_ja_registrado, registrar_recebimento


st.set_page_config(
    page_title="Confirmar Recebimento",
    page_icon="icones/consulta-logo-refinado.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

ativar_modo_exibicao("confirmar_recebimento")

st.markdown(
    """
    <style>
    header,
    header[data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
        height: 0rem !important;
        min-height: 0rem !important;
        background: transparent !important;
        box-shadow: none !important;
        border: 0 !important;
    }

    [data-testid="stStatusWidget"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stHeaderActionElements"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
    }

    #MainMenu,
    footer {
        visibility: hidden;
    }

    .block-container,
    [data-testid="stMainBlockContainer"] {
        max-width: 1180px;
        padding-top: .7rem;
        padding-bottom: 1.25rem;
    }

    div[data-testid="stVerticalBlock"] {
        gap: .3cm !important;
    }

    .stApp,
    [data-testid="stAppViewContainer"] {
        background: #ffffff;
        color: #000000;
    }

    [data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid #000000;
    }

    [data-testid="stSidebarNav"] {
        display: none !important;
    }

    [data-testid="stSidebar"] a,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    label,
    .stMarkdown,
    .stCaptionContainer {
        color: #000000 !important;
    }

    .sidebar-logo {
        display: flex;
        justify-content: center;
        padding: 8px 0 18px 0;
    }

    .sidebar-logo img {
        background: #ffffff;
        border: 0;
        border-radius: 0;
        padding: 0;
    }

    .page-head {
        margin: 2.7rem 0 1rem 0;
    }

    .page-title h1 {
        margin: 0;
        color: #000000;
        font-size: 29px;
        line-height: 1.05;
        font-weight: 850;
        letter-spacing: 0;
    }

    .page-title p {
        margin: 6px 0 0 0;
        color: #333333;
        font-size: 14px;
    }

    .panel,
    div[data-testid="stDataFrame"] {
        border: 2px solid #000000;
        border-radius: 8px;
        background: #ffffff;
        box-shadow: none;
    }

    .panel {
        padding: 14px;
    }

    .detail-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: .3cm;
        margin-top: .3cm;
    }

    .detail-box {
        min-height: 72px;
        padding: 10px;
        border: 2px solid #000000;
        border-radius: 8px;
        background: #ffffff;
        overflow: hidden;
    }

    .detail-label {
        color: #333333;
        font-size: 11px;
        font-weight: 850;
        text-transform: uppercase;
    }

    .detail-value {
        margin-top: 6px;
        color: #000000;
        font-size: 15px;
        line-height: 1.25;
        font-weight: 900;
        overflow-wrap: anywhere;
    }

    .status-box {
        margin-top: .3cm;
        padding: 10px 12px;
        border: 2px solid #000000;
        border-radius: 8px;
        background: #fff7d6;
        color: #000000;
        font-size: 14px;
        font-weight: 850;
    }

    .stButton > button,
    div[data-baseweb="select"] > div,
    div[data-testid="stTextInput"] input {
        border: 2px solid #000000 !important;
        background: #ffffff !important;
        color: #000000 !important;
        border-radius: 7px !important;
        box-shadow: none !important;
    }

    .stButton > button {
        font-weight: 850 !important;
    }

    @media (max-width: 900px) {
        .detail-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
    }

    @media (max-width: 640px) {
        .detail-grid {
            grid-template-columns: 1fr;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

render_menu_lateral()

with st.sidebar:
    st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
    st.image("Logo Branco.bmp", width=72)
    st.image("logo preto goper.png", width=32)
    st.markdown("</div>", unsafe_allow_html=True)
    st.page_link("app.py", label="Início")
    st.page_link("pages/Consulta_Pedidos.py", label="Consulta de Pedidos")
    st.page_link("pages/Confirmar_Recebimento.py", label="Confirmar Recebimento")
    st.page_link("pages/Cronograma.py", label="Recebimentos")
    st.page_link("pages/Embarques.py", label="Embarques")


def texto(valor):
    return escape(str(valor or "").strip() or "-")


def formatar_data(valor):
    data = pd.to_datetime(valor, errors="coerce", dayfirst=True)
    if pd.isna(data):
        return texto(valor)
    return data.strftime("%d/%m/%Y")


def formatar_numero(valor):
    numero = pd.to_numeric(str(valor or "").replace(",", "."), errors="coerce")
    if pd.isna(numero):
        return texto(valor)
    if float(numero).is_integer():
        return str(int(numero))
    return str(round(float(numero), 2)).replace(".", ",")


def render_pedido(pedido):
    numero = str(pedido.get("Numero do Pedido", "")).strip()
    recebido = recebimento_ja_registrado(numero)

    st.markdown(
        f"""
        <div class="panel">
            <strong>Informações do pedido</strong>
            <div class="detail-grid">
                <div class="detail-box">
                    <div class="detail-label">Pedido</div>
                    <div class="detail-value">{texto(numero)}</div>
                </div>
                <div class="detail-box">
                    <div class="detail-label">Fornecedor</div>
                    <div class="detail-value">{texto(pedido.get("Fornecedor", ""))}</div>
                </div>
                <div class="detail-box">
                    <div class="detail-label">Data entrega</div>
                    <div class="detail-value">{escape(formatar_data(pedido.get("Data Entrega", "")))}</div>
                </div>
                <div class="detail-box">
                    <div class="detail-label">Quantidade</div>
                    <div class="detail-value">{escape(formatar_numero(pedido.get("Qtde", "")))}</div>
                </div>
                <div class="detail-box">
                    <div class="detail-label">Código</div>
                    <div class="detail-value">{texto(pedido.get("Codigo", ""))}</div>
                </div>
                <div class="detail-box">
                    <div class="detail-label">Descrição</div>
                    <div class="detail-value">{texto(pedido.get("Descricao", ""))}</div>
                </div>
                <div class="detail-box">
                    <div class="detail-label">Marca</div>
                    <div class="detail-value">{texto(pedido.get("Marca", ""))}</div>
                </div>
                <div class="detail-box">
                    <div class="detail-label">Tipo</div>
                    <div class="detail-value">{texto(pedido.get("Tipo", ""))}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if recebido:
        st.markdown(
            '<div class="status-box">Recebimento já registrado para este pedido.</div>',
            unsafe_allow_html=True,
        )
        return

    if st.button("Confirmar recebimento", key="confirmar_recebimento", use_container_width=True):
        try:
            registrar_recebimento(numero, pedido)
        except Exception as exc:
            st.error(str(exc))
        else:
            st.success("Recebimento registrado no Histórico.")
            st.rerun()


st.markdown(
    """
    <div class="page-head">
        <div class="page-title">
            <h1>Confirmar Recebimento</h1>
            <p>Digite o número do pedido para consultar os dados e registrar o recebimento.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("form_busca_recebimento"):
    pedido_digitado = st.text_input(
        "Número do pedido",
        value=st.session_state.get("pedido_recebimento", ""),
    )
    consultar = st.form_submit_button("Consultar", use_container_width=True)

if consultar:
    st.session_state.pedido_recebimento = pedido_digitado.strip()

numero_pedido = st.session_state.get("pedido_recebimento", "").strip()

if not numero_pedido:
    st.markdown(
        '<div class="status-box">Informe um número de pedido para consultar.</div>',
        unsafe_allow_html=True,
    )
    st.stop()

try:
    encontrados = localizar_pedido(numero_pedido)
except Exception as exc:
    st.error("Não foi possível consultar a planilha.")
    st.caption(str(exc))
    st.stop()

if encontrados.empty:
    st.markdown(
        '<div class="status-box">Nenhum pedido encontrado com este número.</div>',
        unsafe_allow_html=True,
    )
    st.stop()

if len(encontrados) > 1:
    opcoes = {
        f"{linha.get('Numero do Pedido', '')} | {linha.get('Codigo', '')} | {str(linha.get('Descricao', ''))[:80]}": linha
        for _, linha in encontrados.iterrows()
    }
    selecionado = st.selectbox("Itens encontrados", list(opcoes.keys()))
    pedido = opcoes[selecionado]
else:
    pedido = encontrados.iloc[0]

render_pedido(pedido)
