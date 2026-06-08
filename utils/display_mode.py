import time

import streamlit as st
from streamlit_autorefresh import st_autorefresh


INATIVIDADE_SEGUNDOS = 2 * 60
TROCA_TELA_SEGUNDOS = 60
REFRESH_MS = 5 * 1000


def ativar_modo_exibicao(pagina_atual):
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
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            transform: none !important;
            min-width: 3.25rem !important;
            width: 3.25rem !important;
            max-width: 3.25rem !important;
            overflow: visible !important;
            border-right: 1px solid #000000 !important;
            background: #ffffff !important;
        }

        [data-testid="stSidebar"] [data-testid="stSidebarUserContent"],
        [data-testid="stSidebar"] [data-testid="stSidebarNav"],
        [data-testid="stSidebar"] .sidebar-logo,
        [data-testid="stSidebar"] a {
            display: none !important;
        }

        [data-testid="stSidebarCollapseButton"],
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            pointer-events: auto !important;
            position: fixed !important;
            top: 0.55rem !important;
            left: 0.55rem !important;
            z-index: 999999 !important;
            color: #000000 !important;
            background: #ffffff !important;
            border: 1px solid #000000 !important;
            border-radius: 8px !important;
        }

        [data-testid="stAppViewContainer"] > .main {
            margin-left: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
