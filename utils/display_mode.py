import time

import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh


INATIVIDADE_SEGUNDOS = 2 * 60
TROCA_TELA_SEGUNDOS = 60
REFRESH_MS = 5 * 1000
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
    _registrar_atividade_do_navegador()

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

    atividade_navegador = _atividade_navegador_recente()
    if atividade_navegador is not None:
        _registrar_atividade(atividade_navegador)

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


def _registrar_atividade_do_navegador():
    components.html(
        """
        <script>
        (() => {
            const THROTTLE_MS = 1000;
            let last = 0;

            const markActivity = () => {
                const now = Date.now();
                if (now - last < THROTTLE_MS) return;
                last = now;

                const url = new URL(window.parent.location.href);
                url.searchParams.set("_atividade", String(now));
                window.parent.history.replaceState(null, "", url.toString());
            };

            const events = ["click", "mousemove", "keydown", "scroll", "wheel", "touchstart", "touchmove"];
            events.forEach((eventName) => {
                window.parent.addEventListener(eventName, markActivity, { passive: true });
                window.parent.document.addEventListener(eventName, markActivity, { passive: true });
            });
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def _atividade_navegador_recente():
    valor = st.query_params.get("_atividade")
    if isinstance(valor, list):
        valor = valor[-1] if valor else None
    if not valor:
        return None

    try:
        atividade_ms = int(valor)
    except (TypeError, ValueError):
        return None

    ultima_lida = st.session_state.get("modo_exibicao_atividade_navegador_lida")
    if ultima_lida is not None and atividade_ms <= ultima_lida:
        return None

    st.session_state.modo_exibicao_atividade_navegador_lida = atividade_ms
    return atividade_ms / 1000


def _ocultar_sidebar():
    st.session_state.menu_lateral_aberto = False


def _aplicar_layout_menu(menu_aberto):
    left = "19.25rem" if menu_aberto else "0.9rem"
    sidebar_css = (
        """
        [data-testid="stSidebar"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            transform: translateX(0) !important;
            min-width: 18rem !important;
            width: 18rem !important;
            max-width: 18rem !important;
            background: #ffffff !important;
            border-right: 1px solid #000000 !important;
            z-index: 999998 !important;
        }

        [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
            display: block !important;
            visibility: visible !important;
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
            top: 0.75rem !important;
            left: {left} !important;
            z-index: 999999 !important;
            width: 82px !important;
        }}

        .st-key-menu_lateral_toggle button {{
            min-height: 38px !important;
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
            padding-top: 3.2rem !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
