import base64
import calendar
import unicodedata
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from utils.display_mode import ativar_modo_exibicao, render_menu_lateral
from utils.sheets import carregar_dados, carregar_embarques


st.set_page_config(page_title="Agenda Logistica", layout="wide", initial_sidebar_state="expanded")
ativar_modo_exibicao("agenda")


MESES_PT = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Marco",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

DIAS_SEMANA = ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"]


def normalizar_coluna(nome):
    texto = unicodedata.normalize("NFKD", str(nome or "").strip().lower())
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    return " ".join(texto.split())


def encontrar_coluna(df, opcoes):
    mapa = {normalizar_coluna(coluna): coluna for coluna in df.columns}
    for opcao in opcoes:
        coluna = mapa.get(normalizar_coluna(opcao))
        if coluna is not None:
            return coluna
    return None


def texto_serie(serie, padrao="Nao informado"):
    return serie.fillna("").astype(str).str.strip().replace("", padrao)


def numero(valor):
    return f"{int(valor):,}".replace(",", ".")


def formatar_data(data):
    if hasattr(data, "strftime"):
        return data.strftime("%d/%m/%Y")
    data_convertida = pd.to_datetime(data, errors="coerce", dayfirst=True)
    if pd.isna(data_convertida):
        return str(data or "")
    return data_convertida.strftime("%d/%m/%Y")


def mes_formatado(periodo):
    return f"{MESES_PT[periodo.month]} {periodo.year}"


def preparar_recebimentos(df_original):
    df = df_original.copy()
    coluna_data = encontrar_coluna(df, ["Data Entrega", "Data de entrega", "Entrega"])
    coluna_pedido = encontrar_coluna(df, ["Numero do Pedido", "Numero Pedido", "Pedido"])
    coluna_fornecedor = encontrar_coluna(df, ["Subgrupo", "Fornecedor"])
    coluna_grupo = encontrar_coluna(df, ["Grupo"])
    coluna_codigo = encontrar_coluna(df, ["Codigo", "Codigo Produto", "Cod"])
    coluna_descricao = encontrar_coluna(df, ["Descricao", "Descricao Produto", "Produto"])
    coluna_qtde = encontrar_coluna(df, ["Qtde", "Quantidade", "Qtd"])

    obrigatorias = [coluna_data, coluna_pedido]
    if df.empty or any(coluna is None for coluna in obrigatorias):
        return pd.DataFrame(
            columns=[
                "Data Agenda",
                "Pedido",
                "Fornecedor",
                "Grupo",
                "Codigo",
                "Descricao",
                "Quantidade",
            ]
        )

    df["Data Agenda"] = pd.to_datetime(df[coluna_data], errors="coerce", dayfirst=True).dt.date
    df = df[df["Data Agenda"].notna()].copy()

    if df.empty:
        return df

    df["Pedido"] = texto_serie(df[coluna_pedido], "")
    df["Fornecedor"] = texto_serie(df[coluna_fornecedor]) if coluna_fornecedor else "Nao informado"
    df["Grupo"] = texto_serie(df[coluna_grupo]) if coluna_grupo else "Nao informado"
    df["Codigo"] = texto_serie(df[coluna_codigo], "") if coluna_codigo else ""
    df["Descricao"] = texto_serie(df[coluna_descricao], "") if coluna_descricao else ""
    df["Quantidade"] = pd.to_numeric(df[coluna_qtde], errors="coerce").fillna(0) if coluna_qtde else 1

    return df[
        [
            "Data Agenda",
            "Pedido",
            "Fornecedor",
            "Grupo",
            "Codigo",
            "Descricao",
            "Quantidade",
        ]
    ].copy()


def preparar_embarques(df_original):
    df = df_original.copy()
    coluna_data = encontrar_coluna(df, ["Data"])
    coluna_embarque = encontrar_coluna(df, ["Numero do embarque", "Embarque"])
    coluna_nf = encontrar_coluna(df, ["Numero", "NF", "Nota Fiscal"])
    coluna_transportadora = encontrar_coluna(df, ["Nome do transportadora", "Transportadora"])
    coluna_codigo = encontrar_coluna(df, ["Codigo", "Codigo Produto", "Cod"])
    coluna_descricao = encontrar_coluna(df, ["Descricao", "Descrição", "Produto"])
    coluna_qtde = encontrar_coluna(df, ["Quantidade", "Qtde", "Qtd"])
    coluna_placa = encontrar_coluna(df, ["Placa"])

    obrigatorias = [coluna_data, coluna_embarque, coluna_nf]
    if df.empty or any(coluna is None for coluna in obrigatorias):
        return pd.DataFrame(
            columns=[
                "Data Agenda",
                "Embarque",
                "NF",
                "Transportadora",
                "Placa",
                "Codigo",
                "Descricao",
                "Quantidade",
            ]
        )

    df["Data Agenda"] = pd.to_datetime(df[coluna_data], errors="coerce", dayfirst=True).dt.date
    df = df[df["Data Agenda"].notna()].copy()

    if df.empty:
        return df

    df["Embarque"] = texto_serie(df[coluna_embarque], "")
    df["NF"] = texto_serie(df[coluna_nf], "")
    df["Transportadora"] = texto_serie(df[coluna_transportadora]) if coluna_transportadora else "Nao informado"
    df["Placa"] = texto_serie(df[coluna_placa], "") if coluna_placa else ""
    df["Codigo"] = texto_serie(df[coluna_codigo], "") if coluna_codigo else ""
    df["Descricao"] = texto_serie(df[coluna_descricao], "") if coluna_descricao else ""
    df["Quantidade"] = pd.to_numeric(df[coluna_qtde], errors="coerce").fillna(0) if coluna_qtde else 1

    return df[
        [
            "Data Agenda",
            "Embarque",
            "NF",
            "Transportadora",
            "Placa",
            "Codigo",
            "Descricao",
            "Quantidade",
        ]
    ].copy()


def classe_prazo(data):
    hoje = pd.Timestamp.today().normalize().date()
    dias = (data - hoje).days

    if dias < 0:
        return "late"
    if dias == 0:
        return "today"
    if dias <= 3:
        return "soon"
    return "future"


def label_prazo(data):
    hoje = pd.Timestamp.today().normalize().date()
    dias = (data - hoje).days

    if dias < 0:
        return f"Atrasado {abs(dias)}d"
    if dias == 0:
        return "Hoje"
    if dias == 1:
        return "Amanha"
    return f"Em {dias} dias"


def icone_svg(tipo):
    icones = {
        "recebimento": """
            <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 3v12"></path>
                <path d="m7 10 5 5 5-5"></path>
                <path d="M5 21h14"></path>
            </svg>
        """,
        "embarque": """
            <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 21V9"></path>
                <path d="m7 14 5-5 5 5"></path>
                <path d="M5 21h14"></path>
            </svg>
        """,
        "caixa": """
            <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M3 7h18v14H3z"></path>
                <path d="M3 7l3-4h12l3 4"></path>
                <path d="M12 3v18"></path>
            </svg>
        """,
        "caminhao": """
            <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M3 6h11v10H3z"></path>
                <path d="M14 10h4l3 3v3h-7z"></path>
                <circle cx="7" cy="18" r="2"></circle>
                <circle cx="17" cy="18" r="2"></circle>
            </svg>
        """,
    }
    return icones.get(tipo, icones["caixa"])


def render_kpi(titulo, valor, nota, classe, icone):
    st.markdown(
        f"""
        <div class="kpi-card {classe}">
            <div class="kpi-icon">{icone_svg(icone)}</div>
            <div>
                <div class="kpi-label">{escape(titulo)}</div>
                <div class="kpi-value">{escape(str(valor))}</div>
                <div class="kpi-note">{escape(nota)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def resumo_data(recebimentos, embarques, data):
    recebimentos_dia = recebimentos[recebimentos["Data Agenda"] == data].copy()
    embarques_dia = embarques[embarques["Data Agenda"] == data].copy()
    return recebimentos_dia, embarques_dia


def resumo_mes(recebimentos, embarques, periodo):
    recebimentos_mes = recebimentos[pd.to_datetime(recebimentos["Data Agenda"]).dt.to_period("M") == periodo]
    embarques_mes = embarques[pd.to_datetime(embarques["Data Agenda"]).dt.to_period("M") == periodo]
    return recebimentos_mes, embarques_mes


def proximos_eventos(df, tipo, limite=4):
    hoje = pd.Timestamp.today().normalize().date()
    df_futuro = df[df["Data Agenda"] >= hoje].copy()
    if df_futuro.empty:
        return pd.DataFrame(columns=["Data Agenda", "Titulo", "Qtd", "Tipo"])

    if tipo == "recebimento":
        resumo = (
            df_futuro.groupby("Data Agenda")
            .agg(Titulo=("Fornecedor", lambda s: s.value_counts().index[0]), Qtd=("Pedido", "nunique"))
            .reset_index()
        )
    else:
        resumo = (
            df_futuro.groupby("Data Agenda")
            .agg(Titulo=("Transportadora", lambda s: s.value_counts().index[0]), Qtd=("NF", "nunique"))
            .reset_index()
        )

    resumo["Tipo"] = tipo
    return resumo.sort_values("Data Agenda").head(limite)


def render_proximos(recebimentos, embarques):
    proximos_recebimentos = proximos_eventos(recebimentos, "recebimento")
    proximos_embarques = proximos_eventos(embarques, "embarque")
    eventos = pd.concat([proximos_recebimentos, proximos_embarques], ignore_index=True)

    st.markdown(
        '<div class="events-head"><div class="section-title">Proximos eventos</div><button type="button">Ver todos</button></div>',
        unsafe_allow_html=True,
    )

    if eventos.empty:
        st.markdown('<div class="empty">Nenhum evento futuro encontrado.</div>', unsafe_allow_html=True)
        return

    eventos = eventos.sort_values(["Data Agenda", "Tipo"]).head(8)
    for _, linha in eventos.iterrows():
        tipo = "Recebimento" if linha["Tipo"] == "recebimento" else "Embarque"
        classe = "event-recebimento" if linha["Tipo"] == "recebimento" else "event-embarque"
        icone = "recebimento" if linha["Tipo"] == "recebimento" else "embarque"
        unidade = "pedido" if linha["Tipo"] == "recebimento" and int(linha["Qtd"]) == 1 else "pedidos"
        if linha["Tipo"] == "embarque":
            unidade = "nota" if int(linha["Qtd"]) == 1 else "notas"
        st.markdown(
            f"""
            <div class="mini-event {classe}">
                <div class="mini-event-icon">{icone_svg(icone)}</div>
                <div>
                    <strong>{escape(tipo)}</strong>
                    <span>{escape(label_prazo(linha["Data Agenda"]))} - {formatar_data(linha["Data Agenda"])}</span>
                    <small title="{escape(str(linha["Titulo"]))}">{escape(str(linha["Titulo"]))}</small>
                </div>
                <div class="mini-event-total"><b>{numero(linha["Qtd"])}</b><span>{escape(unidade)}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_tabela_html(df, colunas):
    cabecalho = "".join(f"<th>{escape(str(coluna))}</th>" for coluna in colunas)
    linhas = []
    for _, linha in df[colunas].head(80).iterrows():
        celulas = "".join(f"<td>{escape(str(linha.get(coluna, '')))}</td>" for coluna in colunas)
        linhas.append(f"<tr>{celulas}</tr>")

    if not linhas:
        linhas.append(f'<tr><td colspan="{len(colunas)}">Sem registros.</td></tr>')

    st.markdown(
        f"""
        <table class="detail-table">
            <thead><tr>{cabecalho}</tr></thead>
            <tbody>{"".join(linhas)}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


@st.dialog("Detalhes do dia", width="large")
def abrir_detalhe_dia(data, recebimentos, embarques):
    recebimentos_dia, embarques_dia = resumo_data(recebimentos, embarques, data)

    st.markdown(
        f"""
        <div class="dialog-head">
            <h2>{formatar_data(data)}</h2>
            <p>{escape(label_prazo(data))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if recebimentos_dia.empty and embarques_dia.empty:
        st.info("Nao ha recebimentos ou embarques cadastrados para este dia.")
        return

    abas = []
    if not recebimentos_dia.empty:
        abas.append("Recebimentos")
    if not embarques_dia.empty:
        abas.append("Embarques")

    tabs = st.tabs(abas) if len(abas) > 1 else [st.container()]

    indice = 0
    if not recebimentos_dia.empty:
        with tabs[indice]:
            render_detalhe_recebimentos(recebimentos_dia)
        indice += 1

    if not embarques_dia.empty:
        with tabs[indice]:
            render_detalhe_embarques(embarques_dia)


def render_detalhe_recebimentos(df):
    pedidos = df["Pedido"].nunique()
    itens = int(df["Quantidade"].sum())
    fornecedores = df["Fornecedor"].nunique()

    st.markdown(
        f"""
        <div class="detail-metrics">
            <div class="detail-metric"><span>Pedidos</span><strong>{numero(pedidos)}</strong></div>
            <div class="detail-metric"><span>Itens</span><strong>{numero(itens)}</strong></div>
            <div class="detail-metric"><span>Fornecedores</span><strong>{numero(fornecedores)}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    por_fornecedor = (
        df.groupby("Fornecedor")
        .agg(Pedidos=("Pedido", "nunique"), Itens=("Quantidade", "sum"))
        .reset_index()
        .sort_values(["Pedidos", "Itens"], ascending=False)
    )
    st.markdown("**Resumo por fornecedor**")
    render_tabela_html(por_fornecedor, ["Fornecedor", "Pedidos", "Itens"])

    detalhes = df[["Pedido", "Fornecedor", "Grupo", "Codigo", "Descricao", "Quantidade"]].copy()
    st.markdown("**Itens do dia**")
    render_tabela_html(detalhes, ["Pedido", "Fornecedor", "Grupo", "Codigo", "Descricao", "Quantidade"])


def render_detalhe_embarques(df):
    notas = df["NF"].nunique()
    volumes = int(df["Quantidade"].sum())
    transportadoras = df["Transportadora"].nunique()

    st.markdown(
        f"""
        <div class="detail-metrics">
            <div class="detail-metric"><span>Notas fiscais</span><strong>{numero(notas)}</strong></div>
            <div class="detail-metric"><span>Volumes</span><strong>{numero(volumes)}</strong></div>
            <div class="detail-metric"><span>Transportadoras</span><strong>{numero(transportadoras)}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    por_transportadora = (
        df.groupby("Transportadora")
        .agg(Notas=("NF", "nunique"), Volumes=("Quantidade", "sum"))
        .reset_index()
        .sort_values(["Notas", "Volumes"], ascending=False)
    )
    st.markdown("**Resumo por transportadora**")
    render_tabela_html(por_transportadora, ["Transportadora", "Notas", "Volumes"])

    detalhes = df[["Embarque", "NF", "Transportadora", "Placa", "Codigo", "Descricao", "Quantidade"]].copy()
    st.markdown("**Itens do dia**")
    render_tabela_html(detalhes, ["Embarque", "NF", "Transportadora", "Placa", "Codigo", "Descricao", "Quantidade"])


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
    }

    #MainMenu, footer {visibility: hidden !important;}

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
    label {
        color: #000000 !important;
    }

    .block-container,
    [data-testid="stMainBlockContainer"] {
        max-width: 1900px;
        padding-top: .25rem;
        padding-left: .75rem;
        padding-right: .75rem;
        padding-bottom: 1rem;
    }

    .sidebar-logo {
        display: flex;
        justify-content: center;
        gap: 8px;
        padding: 10px 0 20px 0;
    }

    .sidebar-logo img {
        background: #ffffff;
        border: 0;
        padding: 0;
        max-height: 24px;
        width: auto;
    }

    .page-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 20px;
        margin: 0 0 1.35rem 0;
        padding: 0;
    }

    .page-title h1 {
        margin: 0;
        color: #000000;
        font-size: 32px;
        line-height: 1.05;
        font-weight: 900;
        letter-spacing: 0;
    }

    .page-title p {
        margin: 8px 0 0 0;
        color: #333333;
        font-size: 12px;
    }

    .page-logos {
        display: flex;
        align-items: center;
        gap: 14px;
        padding-top: 2px;
        color: #000000;
        font-size: 28px;
        font-weight: 900;
        letter-spacing: .5px;
    }

    .page-logos img {
        max-height: 36px;
        max-width: 158px;
        object-fit: contain;
    }

    .page-logos .goper-mark {
        max-height: 36px;
        max-width: 36px;
    }

    .logo-divider {
        width: 3px;
        height: 34px;
        background: #000000;
        display: inline-block;
    }

    .kpi-card,
    div[data-testid="stVerticalBlockBorderWrapper"],
    div[data-testid="stDataFrame"] {
        border: 3px solid #000000;
        border-radius: 8px;
        background: #ffffff;
        box-shadow: none;
    }

    .kpi-card {
        min-height: 100px;
        padding: 16px 22px;
        position: relative;
        overflow: hidden;
        display: grid;
        grid-template-columns: 66px 1fr;
        align-items: center;
        gap: 18px;
    }

    .kpi-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 62px;
        height: 62px;
        border: 2px solid #000000;
        border-radius: 8px;
        background: #ffffff;
        color: #000000;
    }

    .kpi-icon svg,
    .mini-event-icon svg {
        width: 34px;
        height: 34px;
        fill: none;
        stroke: currentColor;
        stroke-width: 2.25;
        stroke-linecap: round;
        stroke-linejoin: round;
    }

    .kpi-label {
        color: #000000;
        font-size: 15px;
        font-weight: 850;
        text-transform: none;
    }

    .kpi-value {
        margin-top: 6px;
        color: #000000;
        font-size: 30px;
        line-height: 1;
        font-weight: 900;
    }

    .kpi-note {
        margin-top: 9px;
        color: #475467;
        font-size: 12px;
    }

    .kpi-recebimento {border-left: 8px solid #22c55e;}
    .kpi-embarque {border-left: 8px solid #ef4444;}
    .kpi-mes {border-left: 8px solid #22c55e;}
    .kpi-alerta {border-left: 8px solid #ef4444;}

    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 10px 12px;
    }

    .calendar-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 12px;
    }

    .calendar-title {
        color: #000000;
        font-size: 28px;
        font-weight: 900;
        text-align: center;
        line-height: 46px;
    }

    .weekday {
        padding: 11px 4px;
        border: 2px solid #000000;
        border-radius: 7px;
        background: #000000;
        color: #ffffff;
        text-align: center;
        font-size: 13px;
        font-weight: 900;
    }

    .stButton > button {
        border: 3px solid #000000 !important;
        border-radius: 8px !important;
        background: #ffffff !important;
        color: #000000 !important;
        box-shadow: none !important;
        font-weight: 900 !important;
    }

    .calendar-day .stButton > button {
        min-height: 116px !important;
        padding: 10px !important;
        white-space: pre-line !important;
        line-height: 1.35 !important;
        font-size: 15px !important;
        text-align: left !important;
        align-items: flex-start !important;
        justify-content: flex-start !important;
    }

    .day-empty .stButton > button {
        background: #ffffff !important;
        color: #98a2b3 !important;
        border-color: #000000 !important;
    }

    .day-recebimento .stButton > button {
        background: #ffffff !important;
        border-color: #2f8f4f !important;
    }

    .day-embarque .stButton > button {
        background: #ffffff !important;
        border-color: #ef4444 !important;
    }

    .day-misto .stButton > button {
        background: #ffffff !important;
        border-color: #000000 !important;
    }

    .day-today .stButton > button {
        outline: 3px solid #2563eb !important;
        outline-offset: 1px !important;
    }

    .legend-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-top: 12px;
        color: #344054;
        font-size: 12px;
        font-weight: 750;
    }

    .legend-dot {
        display: inline-flex;
        align-items: center;
        gap: 6px;
    }

    .legend-dot::before {
        content: "";
        width: 12px;
        height: 12px;
        border: 2px solid #000000;
        border-radius: 999px;
        display: inline-block;
    }

    .legend-recebimento::before {background: #22c55e;}
    .legend-embarque::before {background: #ef4444;}
    .legend-misto::before {background: linear-gradient(135deg, #22c55e 0 49%, #ef4444 50% 100%);}

    .section-title {
        margin: 0 0 12px 0;
        color: #000000;
        font-size: 18px;
        font-weight: 900;
    }

    .events-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 10px;
    }

    .events-head button {
        border: 2px solid #000000;
        border-radius: 6px;
        background: #ffffff;
        color: #000000;
        min-height: 30px;
        padding: 0 12px;
        font-size: 11px;
        font-weight: 900;
    }

    .mini-event {
        display: grid;
        grid-template-columns: 52px minmax(0, 1fr) 54px;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;
        padding: 9px 10px;
        border: 3px solid #000000;
        border-radius: 7px;
        background: #ffffff;
    }

    .mini-event-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 50px;
        height: 50px;
        border: 2px solid #000000;
        border-radius: 7px;
        background: #ffffff;
        color: #000000;
    }

    .mini-event strong {
        color: #000000;
        font-size: 13px;
        font-weight: 900;
    }

    .mini-event span,
    .mini-event small {
        display: block;
        margin-top: 2px;
        color: #475467;
        font-size: 11px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .mini-event-total {
        text-align: right;
        color: #000000;
    }

    .mini-event-total b {
        display: block;
        color: #000000;
        font-size: 24px;
        line-height: 1;
        font-weight: 900;
    }

    .mini-event-total span {
        display: block;
        color: #344054;
        font-size: 10px;
        font-weight: 750;
        margin-top: 3px;
    }

    .event-recebimento {
        background: #ffffff;
        border-left: 8px solid #22c55e;
    }
    .event-embarque {
        background: #ffffff;
        border-left: 8px solid #ef4444;
    }

    .empty {
        min-height: 90px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 2px dashed #d0d5dd;
        border-radius: 10px;
        color: #667085;
        text-align: center;
    }

    .dialog-head h2 {
        margin: 0;
        color: #000000;
        font-size: 22px;
        font-weight: 900;
    }

    .dialog-head p {
        margin: 4px 0 12px 0;
        color: #475467;
        font-size: 13px;
        font-weight: 750;
    }

    div[data-testid="stDialog"] > div {
        border: 3px solid #000000 !important;
        border-radius: 8px !important;
        background: #ffffff !important;
    }

    .detail-metrics {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
        margin: 8px 0 12px 0;
    }

    .detail-metric {
        min-height: 60px;
        padding: 8px 10px;
        border: 2px solid #000000;
        border-radius: 7px;
        background: #ffffff;
    }

    .detail-metric span {
        display: block;
        color: #344054;
        font-size: 12px;
        font-weight: 850;
    }

    .detail-metric strong {
        display: block;
        margin-top: 4px;
        color: #000000;
        font-size: 18px;
        font-weight: 900;
    }

    .detail-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border: 2px solid #000000;
        border-radius: 7px;
        overflow: hidden;
        margin: 8px 0 16px 0;
        table-layout: fixed;
    }

    .detail-table th {
        background: #000000;
        color: #ffffff;
        padding: 7px 8px;
        font-size: 12px;
        font-weight: 900;
        text-align: left;
        border-right: 1px solid #333333;
    }

    .detail-table td {
        min-height: 30px;
        padding: 7px 8px;
        color: #000000;
        background: #ffffff;
        border-top: 1px solid #d0d5dd;
        border-right: 1px solid #d0d5dd;
        font-size: 12px;
        overflow-wrap: anywhere;
    }

    @media (max-width: 900px) {
        .page-head {
            flex-direction: column;
        }

        .calendar-day .stButton > button {
            min-height: 86px !important;
            font-size: 12px !important;
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
    st.page_link("app.py", label="Inicio")
    st.page_link("pages/Consulta_Pedidos.py", label="Consulta de Pedidos")
    st.page_link("pages/Confirmar_Recebimento.py", label="Confirmar Recebimento")
    st.page_link("pages/Cronograma.py", label="Agenda")

logo_branco = base64.b64encode(Path("Logo Branco.bmp").read_bytes()).decode("utf-8")
logo_goper = base64.b64encode(Path("logo preto goper.png").read_bytes()).decode("utf-8")

st.markdown(
    f"""
    <div class="page-head">
        <div class="page-title">
            <h1>Agenda Logistica</h1>
            <p>Calendario mensal com recebimentos e embarques programados.</p>
        </div>
        <div class="page-logos">
            <img src="data:image/bmp;base64,{logo_branco}" alt="Trendx">
            <span class="logo-divider"></span>
            <img class="goper-mark" src="data:image/png;base64,{logo_goper}" alt="Goper">
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

try:
    recebimentos = preparar_recebimentos(carregar_dados())
except Exception as exc:
    recebimentos = preparar_recebimentos(pd.DataFrame())
    st.warning("Nao foi possivel carregar a aba Pedidos.")
    st.caption(str(exc))

try:
    embarques = preparar_embarques(carregar_embarques())
except Exception as exc:
    embarques = preparar_embarques(pd.DataFrame())
    st.warning("Nao foi possivel carregar a aba Embarques.")
    st.caption(str(exc))

hoje = pd.Timestamp.today().normalize().date()
mes_atual = pd.Timestamp.today().to_period("M")

datas_disponiveis = []
if not recebimentos.empty:
    datas_disponiveis += pd.to_datetime(recebimentos["Data Agenda"]).dt.to_period("M").dropna().tolist()
if not embarques.empty:
    datas_disponiveis += pd.to_datetime(embarques["Data Agenda"]).dt.to_period("M").dropna().tolist()

if datas_disponiveis:
    meses = sorted(set(datas_disponiveis))
else:
    meses = [mes_atual]

idx_padrao = meses.index(mes_atual) if mes_atual in meses else len(meses) - 1

if "agenda_mes_idx" not in st.session_state:
    st.session_state.agenda_mes_idx = idx_padrao

st.session_state.agenda_mes_idx = max(0, min(st.session_state.agenda_mes_idx, len(meses) - 1))
mes_selecionado = meses[st.session_state.agenda_mes_idx]

recebimentos_mes, embarques_mes = resumo_mes(recebimentos, embarques, mes_selecionado)
recebimentos_hoje, embarques_hoje = resumo_data(recebimentos, embarques, hoje)

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_kpi("Recebimentos hoje", numero(recebimentos_hoje["Pedido"].nunique()), "Pedidos previstos", "kpi-recebimento", "recebimento")
with k2:
    render_kpi("Embarques hoje", numero(embarques_hoje["NF"].nunique()), "Notas fiscais previstas", "kpi-embarque", "embarque")
with k3:
    render_kpi("Recebimentos do mes", numero(recebimentos_mes["Pedido"].nunique()), "Pedidos no calendario", "kpi-mes", "caixa")
with k4:
    render_kpi("Embarques do mes", numero(embarques_mes["NF"].nunique()), "Notas fiscais no calendario", "kpi-alerta", "caminhao")

col_calendario, col_lateral = st.columns([3.35, 1], gap="medium")

with col_calendario:
    with st.container(border=True):
        h1, h2, h3 = st.columns([.38, 2.4, .38])

        with h1:
            if st.button("‹", use_container_width=True, disabled=st.session_state.agenda_mes_idx <= 0):
                st.session_state.agenda_mes_idx -= 1
                st.rerun()

        with h2:
            st.markdown(f'<div class="calendar-title">{escape(mes_formatado(mes_selecionado))}</div>', unsafe_allow_html=True)

        with h3:
            if st.button("›", use_container_width=True, disabled=st.session_state.agenda_mes_idx >= len(meses) - 1):
                st.session_state.agenda_mes_idx += 1
                st.rerun()

        semana_header = st.columns(7)
        for indice, dia in enumerate(DIAS_SEMANA):
            with semana_header[indice]:
                st.markdown(f'<div class="weekday">{dia}</div>', unsafe_allow_html=True)

        calendario = calendar.Calendar(firstweekday=0)
        for semana in calendario.monthdatescalendar(mes_selecionado.year, mes_selecionado.month):
            cols = st.columns(7)
            for indice, data in enumerate(semana):
                recebimentos_dia, embarques_dia = resumo_data(recebimentos, embarques, data)
                tem_recebimento = not recebimentos_dia.empty
                tem_embarque = not embarques_dia.empty
                fora_mes = data.month != mes_selecionado.month

                classes = ["calendar-day"]
                if fora_mes:
                    classes.append("day-empty")
                elif tem_recebimento and tem_embarque:
                    classes.append("day-misto")
                elif tem_recebimento:
                    classes.append("day-recebimento")
                elif tem_embarque:
                    classes.append("day-embarque")
                else:
                    classes.append("day-empty")

                if data == hoje:
                    classes.append("day-today")

                texto_botao = f"{data.day}"
                if not fora_mes:
                    indicadores = []
                    if tem_recebimento:
                        indicadores.append(f"● Receb. {recebimentos_dia['Pedido'].nunique()}")
                    if tem_embarque:
                        indicadores.append(f"■ Embarq. {embarques_dia['NF'].nunique()}")
                    if indicadores:
                        texto_botao += "\n" + "\n".join(indicadores)

                texto_botao = f"{data.day}"
                if not fora_mes:
                    marcadores_dia = []
                    if tem_recebimento:
                        marcadores_dia.append(f"R {recebimentos_dia['Pedido'].nunique()}")
                    if tem_embarque:
                        marcadores_dia.append(f"E {embarques_dia['NF'].nunique()}")
                    if marcadores_dia:
                        texto_botao += "\n\n" + "    ".join(marcadores_dia)

                with cols[indice]:
                    chave_dia = f"cal_{data.strftime('%Y_%m_%d')}"
                    if "day-misto" in classes:
                        estilo_botao = "background: #ffffff !important; border-color: #000000 !important; color: #000000 !important;"
                    elif "day-recebimento" in classes:
                        estilo_botao = "background: #ffffff !important; border-color: #2f8f4f !important; color: #000000 !important;"
                    elif "day-embarque" in classes:
                        estilo_botao = "background: #ffffff !important; border-color: #ef4444 !important; color: #000000 !important;"
                    else:
                        estilo_botao = "background: #ffffff !important; border-color: #000000 !important; color: #000000 !important;"

                    if data == hoje:
                        estilo_botao += " outline: 3px solid #2563eb !important; outline-offset: 1px !important;"

                    st.markdown(
                        f"""
                        <style>
                        .st-key-{chave_dia} button {{
                            min-height: 126px !important;
                            padding: 11px !important;
                            white-space: pre-line !important;
                            line-height: 1.35 !important;
                            font-size: 18px !important;
                            font-weight: 800 !important;
                            {estilo_botao}
                        }}
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )
                    clicou = st.button(
                        texto_botao,
                        key=chave_dia,
                        use_container_width=True,
                        disabled=fora_mes,
                    )

                    if clicou:
                        abrir_detalhe_dia(data, recebimentos, embarques)

        st.markdown(
            """
            <div class="legend-row">
                <span class="legend-dot legend-recebimento">Recebimento</span>
                <span class="legend-dot legend-embarque">Embarque</span>
                <span class="legend-dot legend-misto">Recebimento e embarque</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

with col_lateral:
    with st.container(border=True):
        render_proximos(recebimentos, embarques)
