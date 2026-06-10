import time

import streamlit as st
from streamlit_autorefresh import st_autorefresh


INATIVIDADE_SEGUNDOS = 5 * 60
TROCA_TELA_SEGUNDOS = 60
REFRESH_MS = 30 * 1000
MENU_ABERTO_PADRAO = True


def render_menu_lateral():
    if "menu_lateral_aberto" not in st.session_state:
        st.session_state.menu_lateral_aberto = MENU_ABERTO_PADRAO

    if st.button("Menu", key="menu_lateral_toggle"):
        st.session_state.menu_lateral_aberto = not st.session_state.menu_lateral_aberto
        _registrar_atividade(time.time())
        st.rerun()

    _aplicar_layout_menu(st.session_state.menu_lateral_aberto)


def ativar_modo_exibicao(pagina_atual):
    _aplicar_css_base()

    contador = st_autorefresh(
        interval=REFRESH_MS,
        key="modo_exibicao_refresh",
    )
    agora = time.time()

    pagina_anterior = st.session_state.get("modo_exibicao_pagina_atual")
    navegacao_automatica = st.session_state.get("modo_exibicao_navegando", False)
    st.session_state.modo_exibicao_pagina_atual = pagina_atual

    if pagina_anterior is not None and pagina_anterior != pagina_atual:
        if navegacao_automatica:
            st.session_state.modo_exibicao_navegando = False
        else:
            _registrar_atividade(agora)

    ultimo_contador = st.session_state.get("modo_exibicao_contador")
    st.session_state.modo_exibicao_contador = contador

    foi_refresh_automatico = ultimo_contador is not None and contador != ultimo_contador

    if "modo_exibicao_ultima_atividade" not in st.session_state:
        st.session_state.modo_exibicao_ultima_atividade = agora

    if not foi_refresh_automatico:
        _registrar_atividade(agora)

    tempo_parado = agora - st.session_state.modo_exibicao_ultima_atividade

    if tempo_parado < INATIVIDADE_SEGUNDOS:
        return

    st.session_state.modo_exibicao_ativo = True
    _ocultar_sidebar()

    proxima_troca = st.session_state.get("modo_exibicao_proxima_troca")
    if proxima_troca is not None and agora < proxima_troca:
        return

    st.session_state.modo_exibicao_proxima_troca = agora + TROCA_TELA_SEGUNDOS
    st.session_state.modo_exibicao_navegando = True
    st.switch_page(_proxima_pagina(pagina_atual))


def _proxima_pagina(pagina_atual):
    if pagina_atual == "recebimentos":
        return "pages/Embarques.py"

    return "pages/Cronograma.py"


def _registrar_atividade(agora):
    st.session_state.modo_exibicao_ultima_atividade = agora
    st.session_state.modo_exibicao_ativo = False
    st.session_state.modo_exibicao_navegando = False
    st.session_state.modo_exibicao_proxima_troca = None


def _ocultar_sidebar():
    st.session_state.menu_lateral_aberto = False


def _aplicar_css_base():
    st.markdown(
        """
        <style>
        header,
        header[data-testid="stHeader"],
        [data-testid="stHeader"],
        [data-testid="stHeaderActionElements"],
        [data-testid="stToolbar"],
        [data-testid="stStatusWidget"],
        [data-testid="stDecoration"] {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            min-height: 0 !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }

        #MainMenu,
        footer {
            visibility: hidden !important;
        }

        iframe[title*="streamlit_autorefresh"],
        div[data-testid="stIFrame"]:has(iframe[title*="streamlit_autorefresh"]),
        div[data-testid="stElementContainer"]:has(iframe[title*="streamlit_autorefresh"]) {
            position: fixed !important;
            width: 0 !important;
            height: 0 !important;
            min-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            border: 0 !important;
            opacity: 0 !important;
            overflow: hidden !important;
            pointer-events: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _aplicar_layout_menu(menu_aberto):
    left = "19.25rem" if menu_aberto else "0.9rem"
    sidebar_css = (
        """
        [data-testid="stAppViewContainer"] {
            overflow-x: visible !important;
        }

        [data-testid="stSidebar"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: fixed !important;
            left: 0 !important;
            top: 0 !important;
            bottom: 0 !important;
            transform: translateX(0) !important;
            min-width: 18rem !important;
            width: 18rem !important;
            max-width: 18rem !important;
            height: 100vh !important;
            background: #ffffff !important;
            border-right: 1px solid #000000 !important;
            z-index: 999998 !important;
            overflow-y: auto !important;
        }

        [data-testid="stSidebar"] > div,
        [data-testid="stSidebar"] [data-testid="stSidebarUserContent"],
        [data-testid="stSidebarContent"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: 100% !important;
            min-width: 100% !important;
        }

        [data-testid="stSidebar"] a,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] .sidebar-logo {
            visibility: visible !important;
            opacity: 1 !important;
        }
        """
        if menu_aberto
        else """
        [data-testid="stSidebar"] {
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
        }

        [data-testid="stAppViewContainer"] > .main {
            margin-left: 0 !important;
        }
        """
    )

    st.markdown(
        f"""
        <style>
        header,
        header[data-testid="stHeader"],
        [data-testid="stHeader"],
        [data-testid="stHeaderActionElements"],
        [data-testid="stToolbar"],
        [data-testid="stStatusWidget"],
        [data-testid="stDecoration"] {{
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            min-height: 0 !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }}

        #MainMenu,
        footer {{
            visibility: hidden !important;
        }}

        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapsedControl"] {{
            display: none !important;
            visibility: hidden !important;
        }}

        {sidebar_css}

        .st-key-menu_lateral_toggle {{
            position: fixed !important;
            top: 0.55rem !important;
            left: {left} !important;
            z-index: 999999 !important;
            width: 82px !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }}

        .st-key-menu_lateral_toggle button {{
            min-height: 36px !important;
            padding: 0 14px !important;
            border: 2px solid #000000 !important;
            border-radius: 8px !important;
            background: #ffffff !important;
            color: #000000 !important;
            font-weight: 700 !important;
            box-shadow: none !important;
        }}

        .st-key-menu_lateral_toggle button:hover {{
            border-color: #000000 !important;
            color: #000000 !important;
            background: #f2f4f7 !important;
        }}

        .block-container,
        [data-testid="stMainBlockContainer"] {{
            max-width: min(1920px, calc(100vw - 2.5rem)) !important;
            width: 100% !important;
            padding-left: 1.25rem !important;
            padding-right: 1.25rem !important;
            padding-top: 1.15rem !important;
        }}

        div[data-testid="stVerticalBlock"]:has(.st-key-menu_lateral_toggle),
        div[data-testid="stElementContainer"]:has(.st-key-menu_lateral_toggle),
        div[data-testid="stButton"]:has(#menu_lateral_toggle) {{
            height: 0 !important;
            min-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: visible !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
