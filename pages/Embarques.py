from html import escape

import pandas as pd
import base64
import plotly.express as px
import streamlit as st
from pathlib import Path

from utils.display_mode import ativar_modo_exibicao
from utils.sheets import carregar_embarques


st.set_page_config(page_title="Embarques", layout="wide", initial_sidebar_state="expanded")
ativar_modo_exibicao("embarques")


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

CORES_GRUPO = ["#2563eb", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444", "#06b6d4"]
PALETA_PLOTLY = ["#2563eb", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444", "#06b6d4", "#64748b"]


st.markdown(
    """
    <style>
    header,
    header[data-testid="stHeader"] {
        visibility: visible !important;
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
        background: #f7f9fc;
        color: #101828;
    }

    .block-container,
    [data-testid="stMainBlockContainer"] {
        max-width: 1540px;
        padding-top: 0.75rem;
        padding-bottom: 1.4rem;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 1.1rem;
    }

    div[data-testid="column"] {
        min-width: 0;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #dfe6ef;
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 8px 24px rgba(16, 24, 40, .055);
        padding: 14px 16px 16px 16px;
    }

    div[data-testid="stRadio"] {
        margin-top: -4px;
        margin-bottom: 6px;
    }

    .page-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 18px;
        margin-bottom: .2rem;
    }

    .page-title h1 {
        margin: 0;
        color: #0f172a;
        font-size: 29px;
        line-height: 1.05;
        letter-spacing: 0;
        font-weight: 850;
    }

    .page-title p {
        margin: 6px 0 0 0;
        color: #667085;
        font-size: 14px;
    }

    .month-title {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 46px;
        width: 100%;
        border-radius: 8px;
        color: #2563eb;
        font-size: 29px;
        line-height: 1;
        font-weight: 850;
        letter-spacing: 0;
    }

    .nav-button .stButton > button,
    .refresh-button .stButton > button {
        height: 44px;
        border-radius: 8px;
        border: 1px solid #dce3ee;
        background: #ffffff;
        color: #2563eb;
        font-weight: 800;
        box-shadow: 0 6px 18px rgba(16, 24, 40, .05);
    }

    .nav-button .stButton > button:hover,
    .refresh-button .stButton > button:hover {
        border-color: #2563eb;
        background: #f8fbff;
    }

    .kpi-card {
        display: grid;
        grid-template-columns: 58px 1fr;
        gap: 16px;
        align-items: center;
        min-height: 108px;
        padding: 18px;
        border: 1px solid #dfe6ef;
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 8px 24px rgba(16, 24, 40, .055);
    }

    .kpi-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 58px;
        height: 58px;
        border-radius: 999px;
        font-size: 25px;
        font-weight: 850;
    }

    .icon-blue {background: #eaf1ff; color: #2563eb;}
    .icon-green {background: #e8f8ef; color: #10a66a;}
    .icon-orange {background: #fff1df; color: #f97316;}
    .icon-purple {background: #f1e8ff; color: #8b5cf6;}

    .kpi-label {
        color: #475467;
        font-size: 14px;
        font-weight: 650;
    }

    .kpi-value {
        margin-top: 4px;
        color: #0f172a;
        font-size: 27px;
        line-height: 1;
        font-weight: 850;
    }

    .kpi-value.blue {color: #2563eb;}
    .kpi-value.green {color: #10a66a;}
    .kpi-value.orange {color: #f97316;}
    .kpi-value.purple {color: #8b5cf6;}

    .kpi-note {
        margin-top: 7px;
        color: #667085;
        font-size: 12px;
    }

    .panel {
        border: 1px solid #dfe6ef;
        border-radius: 8px;
        background: #ffffff;
        box-shadow: 0 8px 24px rgba(16, 24, 40, .055);
        padding: 16px;
    }

    .soft-panel {
        border: 1px solid #dfe6ef;
        border-radius: 8px;
        background:
            linear-gradient(135deg, rgba(37, 99, 235, .06), rgba(16, 185, 129, .05)),
            #ffffff;
        box-shadow: 0 8px 24px rgba(16, 24, 40, .055);
        padding: 16px;
    }

    .panel-title {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 0 0 12px 0;
        color: #101828;
        font-size: 16px;
        font-weight: 850;
    }

    .next-card {
        display: grid;
        grid-template-columns: 42px minmax(0, 1fr) 58px 58px;
        align-items: center;
        gap: 10px;
        padding: 9px 11px;
        margin-bottom: 8px;
        border-radius: 8px;
        border: 1px solid #dfe6ef;
        background: #f8fbff;
    }

    .next-card.today {background: #ecfdf5; border-color: #bbf7d0;}
    .next-card.soon {background: #eff6ff; border-color: #bfdbfe;}
    .next-card.attention {background: #fff7ed; border-color: #fed7aa;}
    .next-card.selected {outline: 2px solid #2563eb; background: #eff6ff;}

    .next-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 34px;
        height: 34px;
        border-radius: 999px;
        background: #2563eb;
        color: white;
        font-size: 17px;
        font-weight: 850;
    }

    .next-card.today .next-icon {background: #16a34a;}
    .next-card.attention .next-icon {background: #f97316;}

    .next-when {
        color: #101828;
        font-size: 14px;
        line-height: 1.25;
        font-weight: 800;
    }

    .next-date {
        display: block;
        margin-top: 3px;
        color: #667085;
        font-size: 12px;
        font-weight: 600;
    }

    .next-extra {
        display: block;
        margin-top: 5px;
        color: #2563eb;
        font-size: 11px;
        font-weight: 800;
        max-width: 170px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .next-metric {
        text-align: right;
        min-width: 0;
    }

    .next-number {
        color: #2563eb;
        font-size: 16px;
        line-height: 1;
        font-weight: 850;
    }

    .next-label {
        margin-top: 4px;
        color: #667085;
        font-size: 11px;
    }

    .analysis-select {
        margin-bottom: 10px;
    }

    .analysis-select div[data-baseweb="select"] {
        font-size: 13px;
    }

    .next-action .stButton > button {
        min-height: 30px;
        margin-top: -4px;
        margin-bottom: 6px;
        border-radius: 8px;
        border: 1px solid #dbe7ff;
        background: #ffffff;
        color: #2563eb;
        font-size: 12px;
        font-weight: 800;
    }

    .next-action .stButton > button:hover {
        border-color: #2563eb;
        background: #eff6ff;
    }

    .mini-table {
        width: 100%;
        border-collapse: collapse;
        overflow: hidden;
        border-radius: 8px;
        font-size: 13px;
    }

    .mini-table th {
        padding: 10px 12px;
        border: 1px solid #e5eaf2;
        background: #f8fafc;
        color: #475467;
        text-align: left;
        font-weight: 800;
    }

    .mini-table td {
        padding: 10px 12px;
        border: 1px solid #e5eaf2;
        color: #344054;
        background: #ffffff;
    }

    .mini-table td.num,
    .mini-table th.num {
        text-align: center;
    }

    .tag {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 72px;
        max-width: 160px;
        padding: 4px 9px;
        border-radius: 6px;
        background: #eaf1ff;
        color: #2563eb;
        font-size: 11px;
        font-weight: 850;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .tag.green {background: #e8f8ef; color: #047857;}
    .tag.orange {background: #fff1df; color: #c2410c;}
    .tag.slate {background: #f1f5f9; color: #334155;}

    .insight-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 10px;
    }

    .analysis-kpis {
        grid-template-columns: repeat(4, minmax(0, 1fr));
        margin-bottom: 14px;
    }

    .insight {
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #dfe6ef;
        background: rgba(255, 255, 255, .74);
    }

    .insight-label {
        color: #667085;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
    }

    .insight-value {
        margin-top: 5px;
        color: #0f172a;
        font-size: 14px;
        font-weight: 850;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .progress-row {
        display: grid;
        grid-template-columns: minmax(96px, 1fr) 2.5fr 76px;
        align-items: center;
        gap: 12px;
        margin: 15px 0;
    }

    .progress-name {
        color: #101828;
        font-size: 13px;
        font-weight: 800;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .progress-track {
        height: 12px;
        border-radius: 999px;
        background: #eef2f7;
        overflow: hidden;
    }

    .progress-fill {
        height: 100%;
        border-radius: 999px;
    }

    .progress-value {
        color: #475467;
        font-size: 12px;
        text-align: right;
        white-space: nowrap;
    }

    .empty {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 110px;
        border: 1px dashed #d0d5dd;
        border-radius: 8px;
        color: #667085;
        background: #ffffff;
        text-align: center;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #dfe6ef;
        border-radius: 8px;
        overflow: hidden;
    }

    .analysis-chart-title {
        margin: 0 0 8px 0;
        color: #101828;
        font-size: 15px;
        line-height: 1.25;
        font-weight: 850;
    }

    .sidebar-logo {
        display: flex;
        justify-content: center;
        padding: 8px 0 18px 0;
    }

    div[data-testid="stExpander"] {
        margin-top: .35rem;
    }

    @media (max-width: 1000px) {
        .page-head {
            flex-direction: column;
        }

        .next-card {
            grid-template-columns: 38px 1fr;
        }

        .next-metric {
            text-align: left;
        }
    }

    .stApp,
    [data-testid="stAppViewContainer"] {
        background: #000000;
        color: #ffffff;
    }

    [data-testid="stSidebar"] {
        background: #000000 !important;
        border-right: 1px solid #ffffff;
    }

    [data-testid="stSidebar"] a,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: #ffffff !important;
    }

    .sidebar-logo img,
    .page-logo {
        background: #ffffff;
        border: 2px solid #ffffff;
        border-radius: 8px;
        padding: 6px;
    }

    .page-title h1,
    .page-title p {
        color: #ffffff;
    }

    .page-logo {
        width: 126px;
        flex: 0 0 auto;
    }

    .month-title {
        color: #ffffff;
        border: 1px solid #ffffff;
    }

    .nav-button .stButton > button,
    .refresh-button .stButton > button,
    .next-action .stButton > button {
        border: 1px solid #000000;
        background: #ffffff;
        color: #000000;
        box-shadow: none;
    }

    .kpi-card,
    .panel,
    .soft-panel,
    div[data-testid="stVerticalBlockBorderWrapper"],
    .insight,
    .next-card,
    .mini-table th,
    .mini-table td,
    .empty {
        background: #ffffff;
        border-color: #000000;
        box-shadow: none;
    }

    .kpi-icon {
        background: #ffffff !important;
        border: 2px solid #000000;
        color: #000000 !important;
    }

    .next-card.today,
    .next-card.soon,
    .next-card.attention,
    .next-card.selected {
        background: #ffffff;
        border-color: #000000;
        outline-color: #000000;
    }

    .next-icon,
    .next-card.today .next-icon,
    .next-card.attention .next-icon {
        background: #ffffff;
        border: 2px solid #000000;
        color: #000000;
    }

    .kpi-value,
    .kpi-value.blue,
    .kpi-value.green,
    .kpi-value.orange,
    .kpi-value.purple,
    .next-number,
    .next-extra {
        color: #000000;
    }

    .tag,
    .tag.green,
    .tag.orange,
    .tag.slate {
        background: #ffffff;
        border: 1px solid #000000;
        color: #000000;
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
    label {
        color: #000000 !important;
    }

    .block-container,
    [data-testid="stMainBlockContainer"] {
        max-width: 1540px;
        padding-top: 1.25rem;
        padding-bottom: 1.25rem;
    }

    div[data-testid="stVerticalBlock"] {
        gap: 1rem;
    }

    .page-head {
        align-items: flex-start;
        gap: 20px;
        margin-bottom: 1.25rem;
    }

    .page-title h1,
    .page-title p,
    .month-title {
        color: #000000;
    }

    .page-logos {
        display: flex;
        align-items: center;
        gap: 12px;
        flex: 0 0 auto;
    }

    .page-logos img {
        max-height: 30px;
        max-width: 104px;
        object-fit: contain;
    }

    .sidebar-logo img {
        border: 0;
        padding: 0;
        max-height: 24px;
        width: auto;
    }

    .month-title,
    .kpi-card,
    .panel,
    .soft-panel,
    div[data-testid="stVerticalBlockBorderWrapper"],
    .insight,
    .mini-table th,
    .mini-table td,
    div[data-testid="stDataFrame"] {
        border: 2px solid #000000;
        border-radius: 12px;
        box-shadow: none;
    }

    .kpi-card,
    .panel,
    .soft-panel,
    .insight,
    .mini-table th,
    .mini-table td,
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff;
    }

    .kpi-icon {
        background: #ffffff !important;
        border: 2px solid #000000;
        color: #000000 !important;
    }

    .nav-button .stButton > button,
    .refresh-button .stButton > button {
        border: 2px solid #000000;
        background: #ffffff;
        color: #000000;
        border-radius: 7px;
        box-shadow: none;
    }

    .next-card {
        border-radius: 12px;
    }

    .next-card.today {background: #ecfdf5; border-color: #22c55e;}
    .next-card.soon {background: #eff6ff; border-color: #60a5fa;}
    .next-card.attention {background: #fff7ed; border-color: #fb923c;}
    .next-card.selected {outline: 2px solid #000000;}
    .next-icon {background: #2563eb; border: 0; color: #ffffff;}
    .next-card.today .next-icon {background: #16a34a;}
    .next-card.attention .next-icon {background: #f97316;}

    .next-panel {
        border: 2px solid #000000;
        border-radius: 12px;
        background: #ffffff;
        padding: 14px;
        min-height: 100%;
    }

    .next-panel .panel-title {
        margin-bottom: 12px;
    }

    .analysis-select {
        margin: 0 0 12px 0;
    }

    .analysis-select div[data-baseweb="select"] > div {
        min-height: 42px;
        border: 2px solid #000000;
        border-radius: 7px;
        background: #ffffff;
    }

    .next-card {
        grid-template-columns: 38px minmax(0, 1fr) 50px 50px;
        gap: 10px;
        min-height: 76px;
        padding: 10px;
        margin-bottom: 10px;
        border-width: 2px;
        box-shadow: none;
    }

    .next-card.danger {
        background: #fff1f2;
        border-color: #ef4444;
    }

    .next-card.warning {
        background: #fffbeb;
        border-color: #f59e0b;
    }

    .next-card.soon {
        background: #eff6ff;
        border-color: #3b82f6;
    }

    .next-card.safe {
        background: #ecfdf5;
        border-color: #22c55e;
    }

    .next-card.selected {
        outline: 2px solid #000000;
        outline-offset: 1px;
    }

    .next-card.danger .next-icon {background: #ef4444;}
    .next-card.warning .next-icon {background: #f59e0b;}
    .next-card.soon .next-icon {background: #3b82f6;}
    .next-card.safe .next-icon {background: #22c55e;}

    .next-icon {
        width: 32px;
        height: 32px;
        border: 0;
        color: #ffffff;
        font-size: 15px;
    }

    .next-when {
        font-size: 13px;
    }

    .next-date {
        margin-top: 2px;
    }

    .next-extra {
        margin-top: 4px;
        max-width: 150px;
    }

    .next-number {
        font-size: 15px;
    }

    .next-label {
        font-size: 10px;
    }

    .kpi-card,
    .panel,
    .soft-panel,
    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 14px;
    }

    .kpi-card {
        min-height: 96px;
    }

    .insight-grid {
        gap: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
    st.image("Logo Branco.bmp", width=72)
    st.image("logo preto goper.png", width=32)
    st.markdown("</div>", unsafe_allow_html=True)
    st.page_link("app.py", label="Inicio")
    st.page_link("pages/Consulta_Pedidos.py", label="Consulta de Pedidos")
    st.page_link("pages/Cronograma.py", label="Recebimentos")
    st.page_link("pages/Embarques.py", label="Embarques")


def texto(serie):
    return serie.fillna("").astype(str).str.strip()


def preparar_dados(df_original):
    df = df_original.copy()
    obrigatorias = ["Data", "Numero do embarque", "Numero", "Quantidade", "Nome do transportadora"]
    faltantes = [col for col in obrigatorias if col not in df.columns]

    if faltantes:
        st.error("A aba Embarques precisa conter estas colunas: " + ", ".join(faltantes))
        st.stop()

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
    df = df[df["Data"].notna()].copy()

    if df.empty:
        return df

    df["Numero do embarque"] = texto(df["Numero do embarque"]).replace("", "Nao informado")
    df["Numero"] = texto(df["Numero"]).replace("", "Nao informado")
    df["Nome do transportadora"] = texto(df["Nome do transportadora"]).replace("", "Nao informado")
    df["Data Embarque"] = df["Data"].dt.date

    df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce").fillna(0)

    for coluna in ["Num box", "Placa", "Codigo", "Descrição", "Endereço nota", "Status"]:
        if coluna in df.columns:
            df[coluna] = texto(df[coluna])

    return df


def mes_formatado(periodo):
    return f"{MESES_PT[periodo.month]} {periodo.year}"


def numero(valor):
    return f"{int(valor):,}".replace(",", ".")


def render_kpi(titulo, valor, nota, icone, cor):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon icon-{cor}">{icone}</div>
            <div>
                <div class="kpi-label">{escape(titulo)}</div>
                <div class="kpi-value {cor}">{numero(valor)}</div>
                <div class="kpi-note">{escape(nota)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def resumo_por_data(df):
    return (
        df.groupby("Data Embarque")
        .agg(
            Notas=("Numero", "nunique"),
            Volumes=("Quantidade", "sum"),
            Linhas=("Numero", "size"),
            Embarques=("Numero do embarque", "nunique"),
            Transportadoras=("Nome do transportadora", "nunique"),
            Transportadora_Principal=(
                "Nome do transportadora",
                lambda s: s.value_counts().index[0] if not s.empty else "",
            ),
            Embarque_Principal=(
                "Numero do embarque",
                lambda s: s.value_counts().index[0] if not s.empty else "",
            ),
        )
        .reset_index()
        .sort_values("Data Embarque")
    )


def label_prazo(data_recebimento):
    hoje = pd.Timestamp.today().normalize().date()
    dias = (data_recebimento - hoje).days

    if dias == 0:
        return "Hoje", "danger"
    if dias == 1:
        return "Amanha", "danger"
    if dias < 5:
        return f"Em {dias} dias", "danger"
    if dias <= 10:
        return f"Em {dias} dias", "warning"
    if dias < 15:
        return f"Em {dias} dias", "soon"
    return f"Em {dias} dias", "safe"


def proximas_datas(df, limite=5):
    hoje = pd.Timestamp.today().normalize().date()
    return resumo_por_data(df[df["Data Embarque"] >= hoje]).head(limite)


def render_proximos_embarques(proximas):
    if "embarque_data_alerta" not in st.session_state and not proximas.empty:
        st.session_state.embarque_data_alerta = proximas.iloc[0]["Data Embarque"].strftime("%Y-%m-%d")

    st.markdown('<div class="panel-title next-panel-title">Proximos embarques</div>', unsafe_allow_html=True)

    if proximas.empty:
        st.markdown('<div class="empty">Nenhum embarque futuro cadastrado.</div>', unsafe_allow_html=True)
        return

    opcoes = {
        f"{label_prazo(linha['Data Embarque'])[0]} - {linha['Data Embarque'].strftime('%d/%m/%Y')}": linha["Data Embarque"].strftime("%Y-%m-%d")
        for _, linha in proximas.iterrows()
    }
    valores = list(opcoes.values())
    valor_atual = st.session_state.get("embarque_data_alerta", valores[0])
    indice_atual = valores.index(valor_atual) if valor_atual in valores else 0

    st.markdown('<div class="analysis-select">', unsafe_allow_html=True)
    escolha = st.selectbox(
        "Embarque analisado",
        list(opcoes.keys()),
        index=indice_atual,
        label_visibility="collapsed",
    )
    st.session_state.embarque_data_alerta = opcoes[escolha]
    st.markdown("</div>", unsafe_allow_html=True)

    for _, linha in proximas.iterrows():
        data_recebimento = linha["Data Embarque"]
        quando, classe = label_prazo(data_recebimento)
        selecionado = "selected" if data_recebimento.strftime("%Y-%m-%d") == st.session_state.embarque_data_alerta else ""

        st.markdown(
            f"""
            <div class="next-card {classe} {selecionado}">
                <div class="next-icon">•</div>
                <div>
                    <div class="next-when">{escape(quando)}</div>
                    <span class="next-date">{data_recebimento.strftime("%d/%m/%Y")}</span>
                    <span class="next-extra">{escape(str(linha["Transportadora_Principal"]))} | {escape(str(linha["Embarque_Principal"]))}</span>
                </div>
                <div class="next-metric">
                    <div class="next-number">{numero(linha["Notas"])}</div>
                    <div class="next-label">Notas</div>
                </div>
                <div class="next-metric">
                    <div class="next-number">{numero(linha["Volumes"])}</div>
                    <div class="next-label">Volumes</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_tabela_mes(resumo):
    linhas = []
    for _, linha in resumo.head(8).iterrows():
        linhas.append(
            "<tr>"
            f"<td>{linha['Data Embarque'].strftime('%d/%m/%Y')}</td>"
            f"<td class='num'>{numero(linha['Notas'])}</td>"
            f"<td class='num'>{numero(linha['Volumes'])}</td>"
            f"<td class='num'>{numero(linha['Embarques'])}</td>"
            f"<td class='num'>{numero(linha['Transportadoras'])}</td>"
            "</tr>"
        )

    if not linhas:
        return '<div class="empty">Sem embarques neste mes.</div>'

    return (
        "<table class='mini-table'>"
        "<thead>"
        "<tr>"
        "<th>Data</th>"
        "<th class='num'>Notas</th>"
        "<th class='num'>Volumes</th>"
        "<th class='num'>Embarques</th>"
        "<th class='num'>Transportadoras</th>"
        "</tr>"
        "</thead>"
        "<tbody>"
        + "".join(linhas)
        + "</tbody></table>"
    )


def render_ranking(titulo, df_ranking, coluna_nome, coluna_valor, sufixo):
    st.markdown(f'<div class="panel"><div class="panel-title">{escape(titulo)}</div>', unsafe_allow_html=True)

    if df_ranking.empty:
        st.markdown('<div class="empty">Sem dados para exibir.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        return

    maximo = max(float(df_ranking[coluna_valor].max()), 1)

    for indice, (_, linha) in enumerate(df_ranking.iterrows()):
        largura = int((float(linha[coluna_valor]) / maximo) * 100)
        cor = CORES_GRUPO[indice % len(CORES_GRUPO)]
        nome = escape(str(linha[coluna_nome]))

        st.markdown(
            f"""
            <div class="progress-row">
                <div class="progress-name" title="{nome}">{nome}</div>
                <div class="progress-track">
                    <div class="progress-fill" style="width:{largura}%; background:{cor};"></div>
                </div>
                <div class="progress-value">{numero(linha[coluna_valor])} {sufixo}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def valor_top(df, coluna, coluna_valor="Numero", agregacao="nunique"):
    if df.empty or coluna not in df.columns:
        return "Sem dados", 0

    ranking = df.groupby(coluna).agg(Valor=(coluna_valor, agregacao)).reset_index()
    if ranking.empty:
        return "Sem dados", 0

    linha = ranking.sort_values("Valor", ascending=False).iloc[0]
    return str(linha[coluna]), int(linha["Valor"])


def render_leitura_operacional(df_mes):
    transportadora, notas_transportadora = valor_top(df_mes, "Nome do transportadora")
    dia_ranking = (
        df_mes.groupby("Data Embarque")
        .agg(Valor=("Quantidade", "sum"))
        .reset_index()
        .sort_values("Valor", ascending=False)
    )
    if dia_ranking.empty:
        dia_volume, volumes_dia = "Sem dados", 0
    else:
        dia_volume = dia_ranking.iloc[0]["Data Embarque"].strftime("%d/%m/%Y")
        volumes_dia = int(dia_ranking.iloc[0]["Valor"])
    embarque, notas_embarque = valor_top(df_mes, "Numero do embarque")

    st.markdown(
        f"""
        <div class="soft-panel">
            <div class="panel-title">Leitura operacional do mes</div>
            <div class="insight-grid">
                <div class="insight">
                    <div class="insight-label">Transportadora dominante</div>
                    <div class="insight-value" title="{escape(transportadora)}">{escape(transportadora)}</div>
                    <div class="kpi-note">{numero(notas_transportadora)} notas</div>
                </div>
                <div class="insight">
                    <div class="insight-label">Dia com maior volume</div>
                    <div class="insight-value" title="{escape(str(dia_volume))}">{escape(str(dia_volume))}</div>
                    <div class="kpi-note">{numero(volumes_dia)} volumes</div>
                </div>
                <div class="insight">
                    <div class="insight-label">Embarque com mais notas</div>
                    <div class="insight-value" title="{escape(embarque)}">{escape(embarque)}</div>
                    <div class="kpi-note">{numero(notas_embarque)} notas fiscais</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_analise_entrega(df, data_alerta):
    if data_alerta is None:
        st.markdown('<div class="empty">Selecione um proximo embarque para analisar.</div>', unsafe_allow_html=True)
        return

    df_alerta = df[df["Data Embarque"] == data_alerta].copy()

    if df_alerta.empty:
        st.markdown('<div class="empty">Nao ha itens para o embarque selecionado.</div>', unsafe_allow_html=True)
        return

    notas = df_alerta["Numero"].nunique()
    volumes = df_alerta["Quantidade"].sum()
    embarques = df_alerta["Numero do embarque"].nunique()
    transportadoras = df_alerta["Nome do transportadora"].nunique()
    lista_transportadoras = sorted(df_alerta["Nome do transportadora"].dropna().astype(str).unique())
    transportadoras_resumo = ", ".join(lista_transportadoras[:3])
    if len(lista_transportadoras) > 3:
        transportadoras_resumo += f" +{len(lista_transportadoras) - 3}"

    st.markdown(
        f"""
        <div class="panel-title">Analise do embarque de {data_alerta.strftime("%d/%m/%Y")}</div>
        <div class="insight-grid analysis-kpis">
            <div class="insight">
                <div class="insight-label">Notas fiscais</div>
                <div class="insight-value">{numero(notas)}</div>
            </div>
            <div class="insight">
                <div class="insight-label">Volumes</div>
                <div class="insight-value">{numero(volumes)}</div>
            </div>
            <div class="insight">
                <div class="insight-label">Embarques</div>
                <div class="insight-value">{numero(embarques)}</div>
            </div>
            <div class="insight">
                <div class="insight-label">Transportadoras</div>
                <div class="insight-value" title="{escape(', '.join(lista_transportadoras))}">{escape(transportadoras_resumo)}</div>
                <div class="kpi-note">{numero(transportadoras)} transportadoras</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    transportadora, volumes_col = st.columns(2)

    with transportadora:
        with st.container(border=True):
            st.markdown('<div class="analysis-chart-title">Notas Fiscais por Transportadora</div>', unsafe_allow_html=True)
            por_transportadora = (
                df_alerta.groupby("Nome do transportadora")
                .agg(Notas=("Numero", "nunique"))
                .reset_index()
                .sort_values("Notas", ascending=False)
            )
            fig_transportadora = px.pie(
                por_transportadora,
                names="Nome do transportadora",
                values="Notas",
                hole=.55,
                color_discrete_sequence=PALETA_PLOTLY,
            )
            fig_transportadora = ajustar_pizza(fig_transportadora)
            fig_transportadora.update_traces(hovertemplate="<b>%{label}</b><br>Notas fiscais: %{value}<extra></extra>")
            st.plotly_chart(
                estilizar_grafico(fig_transportadora, altura=390, legenda=True),
                use_container_width=True,
                config={"displayModeBar": False},
            )

    with volumes_col:
        with st.container(border=True):
            st.markdown('<div class="analysis-chart-title">Volumes por Transportadora</div>', unsafe_allow_html=True)
            por_volume = (
                df_alerta.groupby("Nome do transportadora")
                .agg(Volumes=("Quantidade", "sum"))
                .reset_index()
                .sort_values("Volumes", ascending=False)
            )
            fig_volume = px.pie(
                por_volume,
                names="Nome do transportadora",
                values="Volumes",
                hole=.55,
                color_discrete_sequence=["#f97316", "#2563eb", "#10b981", "#8b5cf6", "#64748b"],
            )
            fig_volume = ajustar_pizza(fig_volume)
            fig_volume.update_traces(hovertemplate="<b>%{label}</b><br>Volumes: %{value}<extra></extra>")
            st.plotly_chart(
                estilizar_grafico(fig_volume, altura=390, legenda=True),
                use_container_width=True,
                config={"displayModeBar": False},
            )


def ajustar_pizza(fig):
    fig.update_traces(
        textinfo="value",
        texttemplate="%{value}",
        textposition="inside",
        marker=dict(line=dict(color="#ffffff", width=2)),
        domain=dict(x=[0.03, 0.97], y=[0.28, 1.0]),
    )
    return fig


def estilizar_grafico(fig, altura=282, legenda=False):
    fig.update_layout(
        height=altura,
        margin=dict(l=6, r=6, t=4, b=84),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(family="Arial", size=12, color="#475467"),
        showlegend=legenda,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.02,
            xanchor="center",
            x=0.5,
            font=dict(size=12, color="#101828"),
            itemwidth=30,
        ),
    )
    fig.update_xaxes(showgrid=False, linecolor="#e5eaf2", tickfont=dict(color="#667085"))
    fig.update_yaxes(gridcolor="#e9eef5", linecolor="#e5eaf2", tickfont=dict(color="#667085"))
    return fig


df = preparar_dados(carregar_embarques())
logo_branco = base64.b64encode(Path("Logo Branco.bmp").read_bytes()).decode("utf-8")
logo_preto = base64.b64encode(Path("logo preto goper.png").read_bytes()).decode("utf-8")

st.markdown(
    f"""
    <div class="page-head">
        <div class="page-title">
            <h1>Embarques Programados</h1>
            <p>Acompanhe as saidas previstas por data, transportadora e volume operacional.</p>
        </div>
        <div class="page-logos">
            <img src="data:image/bmp;base64,{logo_branco}" alt="Trendx">
            <img src="data:image/png;base64,{logo_preto}" alt="Goper">
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if df.empty:
    st.markdown('<div class="empty">Nao ha datas validas na coluna Data da aba Embarques.</div>', unsafe_allow_html=True)
    st.stop()

meses = sorted(df["Data"].dt.to_period("M").unique())
mes_atual = pd.Timestamp.today().to_period("M")
idx_padrao = meses.index(mes_atual) if mes_atual in meses else len(meses) - 1

if "embarque_mes_idx" not in st.session_state:
    st.session_state.embarque_mes_idx = idx_padrao

mes_selecionado = meses[st.session_state.embarque_mes_idx]

nav_1, nav_2, nav_3, nav_4 = st.columns([.55, 3.1, .55, .8])

with nav_1:
    st.markdown('<div class="nav-button">', unsafe_allow_html=True)
    if st.button("‹", use_container_width=True, disabled=st.session_state.embarque_mes_idx <= 0):
        st.session_state.embarque_mes_idx -= 1
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with nav_2:
    st.markdown(f'<div class="month-title">{escape(mes_formatado(mes_selecionado))}</div>', unsafe_allow_html=True)

with nav_3:
    st.markdown('<div class="nav-button">', unsafe_allow_html=True)
    if st.button("›", use_container_width=True, disabled=st.session_state.embarque_mes_idx >= len(meses) - 1):
        st.session_state.embarque_mes_idx += 1
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with nav_4:
    st.markdown('<div class="refresh-button">', unsafe_allow_html=True)
    if st.button("Atualizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

df_mes = df[df["Data"].dt.to_period("M") == mes_selecionado].copy()
resumo_mes = resumo_por_data(df_mes)

k1, k2, k3, k4 = st.columns(4)

with k1:
    render_kpi("Notas Fiscais", df_mes["Numero"].nunique(), "Notas fiscais diferentes", "NF", "blue")
with k2:
    render_kpi("Volumes", df_mes["Quantidade"].sum(), "Soma das quantidades", "V", "green")
with k3:
    render_kpi("Embarques", df_mes["Numero do embarque"].nunique(), "Embarques diferentes", "E", "orange")
with k4:
    render_kpi("Transportadoras", df_mes["Nome do transportadora"].nunique(), "Transportadoras diferentes", "T", "purple")

render_leitura_operacional(df_mes)

proximas = proximas_datas(df)

col_proximas, col_grafico = st.columns([1.05, 2.55], gap="medium")

with col_proximas:
    with st.container(border=True):
        render_proximos_embarques(proximas)

with col_grafico:
    with st.container(border=True):
        data_alerta = None
        if "embarque_data_alerta" in st.session_state:
            data_alerta = pd.to_datetime(st.session_state.embarque_data_alerta).date()
        render_analise_entrega(df, data_alerta)

col_tabela, col_rank = st.columns([1.65, 1], gap="medium")

with col_tabela:
    st.markdown('<div class="panel"><div class="panel-title">Embarques do mes</div></div>', unsafe_allow_html=True)
    st.markdown(render_tabela_mes(resumo_mes), unsafe_allow_html=True)

    datas_disponiveis = ["Visao do mes"] + [
        data.strftime("%d/%m/%Y") for data in resumo_mes["Data Embarque"].tolist()
    ]
    data_label = st.selectbox("Detalhar embarque", datas_disponiveis)

with col_rank:
    aba_transportadora, aba_embarque, aba_volume = st.tabs(["Transportadoras", "Embarques", "Volumes"])

    with aba_transportadora:
        ranking_transportadora = (
            df_mes.groupby("Nome do transportadora")
            .agg(Notas=("Numero", "nunique"), Volumes=("Quantidade", "sum"))
            .reset_index()
            .sort_values("Notas", ascending=False)
            .head(6)
        )
        render_ranking("Top transportadoras do mes", ranking_transportadora, "Nome do transportadora", "Notas", "notas")

    with aba_embarque:
        ranking_embarque = (
            df_mes.groupby("Numero do embarque")
            .agg(Notas=("Numero", "nunique"), Volumes=("Quantidade", "sum"))
            .reset_index()
            .sort_values("Notas", ascending=False)
            .head(6)
        )
        render_ranking("Embarques por notas fiscais", ranking_embarque, "Numero do embarque", "Notas", "notas")

    with aba_volume:
        ranking_volume = (
            df_mes.groupby("Nome do transportadora")
            .agg(Volumes=("Quantidade", "sum"), Notas=("Numero", "nunique"))
            .reset_index()
            .sort_values("Volumes", ascending=False)
            .head(6)
        )
        render_ranking("Volumes por transportadora", ranking_volume, "Nome do transportadora", "Volumes", "vol.")

if data_label != "Visao do mes":
    data_detalhe = pd.to_datetime(data_label, dayfirst=True).date()
    df_detalhe = df_mes[df_mes["Data Embarque"] == data_detalhe].copy()
    titulo = f"Embarques detalhados de {data_label}"
else:
    df_detalhe = df_mes.copy()
    titulo = "Embarques detalhados do mes"

colunas = [
    "Data",
    "Numero do embarque",
    "Numero",
    "Codigo",
    "Descrição",
    "Quantidade",
    "Nome do transportadora",
]
colunas = [col for col in colunas if col in df_detalhe.columns]
df_detalhe = df_detalhe[colunas].copy()

for coluna_texto in ["Numero do embarque", "Numero", "Codigo"]:
    if coluna_texto in df_detalhe.columns:
        df_detalhe[coluna_texto] = df_detalhe[coluna_texto].fillna("").astype(str).str.strip()

if "Data" in df_detalhe.columns:
    df_detalhe["Data"] = df_detalhe["Data"].dt.strftime("%d/%m/%Y")

df_detalhe = df_detalhe.rename(
    columns={
        "Numero": "NF",
    }
)

with st.expander(titulo, expanded=False):
    st.dataframe(
        df_detalhe,
        use_container_width=True,
        hide_index=True,
        height=360,
        column_config={
            "NF": st.column_config.TextColumn("NF"),
            "Codigo": st.column_config.TextColumn("Codigo"),
        },
    )

