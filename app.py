import base64
from pathlib import Path

import streamlit as st

from utils.display_mode import ativar_modo_exibicao, render_menu_lateral


st.set_page_config(
    page_title="Logistica Trendx",
    page_icon="icones/consulta-logo-refinado.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

ativar_modo_exibicao("inicio")

st.markdown(
    """
    <style>
    header,
    header[data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        min-height: 0 !important;
        background: transparent !important;
        box-shadow: none !important;
        border: 0 !important;
    }

    [data-testid="stStatusWidget"] {
        display: none !important;
    }

    footer, #MainMenu {visibility: hidden;}
    [data-testid="stDecoration"] {display: none !important;}

    .stApp {
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
    [data-testid="stSidebar"] span {
        color: #000000 !important;
    }

    .block-container,
    [data-testid="stMainBlockContainer"] {
        max-width: 1180px;
        padding-top: .25rem;
        padding-bottom: 1.25rem;
    }

    .home-hero {
        min-height: 330px;
        display: grid;
        grid-template-columns: 1.1fr .9fr;
        gap: 24px;
        align-items: center;
        padding: 28px;
        border: 2px solid #000000;
        border-radius: 22px;
        background: #ffffff;
        box-shadow: none;
    }

    .brand-row {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 12px;
        margin-bottom: 22px;
    }

    .brand-row img {
        max-height: 30px;
        max-width: 104px;
        object-fit: contain;
    }

    .home-title {
        margin: 0;
        color: #000000;
        font-size: 34px;
        line-height: 1.08;
        font-weight: 850;
        letter-spacing: 0;
    }

    .home-copy {
        max-width: 620px;
        margin: 12px 0 0 0;
        color: #333333;
        font-size: 16px;
        line-height: 1.55;
    }

    .home-panel {
        padding: 18px;
        border: 2px solid #000000;
        border-radius: 14px;
        background: #ffffff;
    }

    .home-panel-title {
        margin: 0 0 14px 0;
        color: #000000;
        font-size: 16px;
        font-weight: 850;
    }

    .home-section {
        display: block;
        padding: 12px 14px;
        margin-top: 10px;
        border-radius: 7px;
        border: 2px solid #000000;
        background: #ffffff;
        color: #000000;
        font-size: 14px;
        font-weight: 800;
    }

    .home-section span {
        display: block;
        margin-top: 3px;
        color: #333333;
        font-size: 12px;
        font-weight: 600;
    }

    .sidebar-logo {
        display: flex;
        gap: 8px;
        align-items: center;
        justify-content: center;
        padding: 8px 0 16px 0;
    }

    .sidebar-logo img {
        background: #ffffff;
        border: 0;
        border-radius: 0;
        padding: 0;
        max-height: 24px;
        width: auto;
    }

    @media (max-width: 900px) {
        .home-hero {
            grid-template-columns: 1fr;
            padding: 24px;
        }

        .home-title {
            font-size: 28px;
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

logo_branco = base64.b64encode(Path("Logo Branco.bmp").read_bytes()).decode("utf-8")
logo_preto = base64.b64encode(Path("logo preto goper.png").read_bytes()).decode("utf-8")

st.markdown(
    f"""
    <div class="brand-row">
        <img src="data:image/bmp;base64,{logo_branco}" alt="Trendx">
        <img src="data:image/png;base64,{logo_preto}" alt="Goper">
    </div>
    <div class="home-hero">
        <div>
            <h1 class="home-title">Sistema Logístico</h1>
            <p class="home-copy">
                Monitore pedidos, recebimentos e embarques em uma visão operacional única,
                com foco em datas, fornecedores, transportadoras e volumes.
            </p>
        </div>
        <div class="home-panel">
            <div class="home-panel-title">Abas do sistema</div>
            <div class="home-section">
                Aba Consulta de Pedidos
                <span>Filtros e detalhe dos pedidos importados do Sheets.</span>
            </div>
            <div class="home-section">
                Aba Confirmar Recebimento
                <span>Consulta o pedido e registra a data de recebimento no Histórico.</span>
            </div>
            <div class="home-section">
                Aba Recebimentos
                <span>Mostra próximos recebimentos, alertas por prazo, fornecedores e gráficos de recebimento.</span>
            </div>
            <div class="home-section">
                Aba Embarques
                <span>Acompanha próximas saídas, volumes, transportadoras e análises dos embarques programados.</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
