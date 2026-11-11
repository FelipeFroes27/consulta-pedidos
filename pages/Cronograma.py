import base64
import calendar
import unicodedata
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from utils.display_mode import ativar_modo_exibicao, render_menu_lateral
from utils.pick import gerar_pick_pdf
from utils.sheets import (
    PlanilhaIndisponivel,
    carregar_dados,
    carregar_historico_recebimentos,
    recebimentos_registrados,
    registrar_recebimentos,
)


st.set_page_config(page_title="Agenda de Recebimentos", layout="wide", initial_sidebar_state="expanded")
ativar_modo_exibicao("agenda")


MESES_PT = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
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

DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

COLUNAS_RECEBIMENTO = [
    "Data Agenda",
    "Pedido",
    "Fornecedor",
    "Empresa",
    "Emissao",
    "Observacao",
    "Codigo",
    "Descricao",
    "Cor",
    "UN",
    "Quantidade",
]


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


def texto_serie(serie, padrao="Não informado"):
    return serie.fillna("").astype(str).str.strip().replace("", padrao)


def numero(valor):
    return f"{int(valor):,}".replace(",", ".")


def converter_numero(serie):
    texto = serie.fillna("").astype(str).str.strip()
    tem_virgula = texto.str.contains(",", regex=False)
    texto = texto.where(~tem_virgula, texto.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    return pd.to_numeric(texto, errors="coerce").fillna(0)


def total_itens(df):
    if df.empty or "Quantidade" not in df.columns:
        return 0
    return int(pd.to_numeric(df["Quantidade"], errors="coerce").fillna(0).sum())


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

    if df.empty or coluna_data is None or coluna_pedido is None:
        return pd.DataFrame(columns=COLUNAS_RECEBIMENTO)

    df["Data Agenda"] = pd.to_datetime(df[coluna_data], errors="coerce", dayfirst=True).dt.date
    df = df[df["Data Agenda"].notna()].copy()
    if df.empty:
        return pd.DataFrame(columns=COLUNAS_RECEBIMENTO)

    def texto(opcoes, padrao=""):
        coluna = encontrar_coluna(df, opcoes)
        return texto_serie(df[coluna], padrao) if coluna else padrao

    df["Pedido"] = texto_serie(df[coluna_pedido], "")
    df["Fornecedor"] = texto(["Forcededor", "Nome Fornecedor", "Razao Social Fornecedor", "Subgrupo", "Fornecedor"], "Não informado")
    df["Empresa"] = texto(["Empresa"])
    df["Emissao"] = texto(["Data Emissao", "Data de Emissão"])
    df["Observacao"] = texto(["Observacao", "Observação"])
    df["Codigo"] = texto(["Codigo", "Codigo Produto", "Cod"])
    df["Descricao"] = texto(["Descricao", "Descricao Produto", "Produto"])
    df["Cor"] = texto(["Desc Cor", "Cor"])
    df["UN"] = texto(["UN", "Unidade"])
    coluna_qtde = encontrar_coluna(df, ["Qtde", "Quantidade", "Qtd"])
    df["Quantidade"] = converter_numero(df[coluna_qtde]) if coluna_qtde else 1

    return df[COLUNAS_RECEBIMENTO].copy()


def label_prazo(data):
    hoje = pd.Timestamp.today().normalize().date()
    dias = (data - hoje).days

    if dias < 0:
        return f"Atrasado {abs(dias)}d"
    if dias == 0:
        return "Hoje"
    if dias == 1:
        return "Amanhã"
    return f"Em {dias} dias"


def icone_svg(tipo):
    imagens = {
        "recebimento": "receber.png",
        "compromisso": "compromisso.png",
    }
    caminho = Path(imagens.get(tipo, "receber.png"))
    if caminho.exists():
        imagem = base64.b64encode(caminho.read_bytes()).decode("utf-8")
        return f'<img class="agenda-icon-img" src="data:image/png;base64,{imagem}" alt="{escape(tipo)}">'
    return """
        <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M3 7h18v14H3z"></path>
            <path d="M3 7l3-4h12l3 4"></path>
            <path d="M12 3v18"></path>
        </svg>
    """


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


def recebimentos_do_dia(recebimentos, data):
    return recebimentos[recebimentos["Data Agenda"] == data].copy()


def recebimentos_do_mes(recebimentos, periodo):
    if recebimentos.empty:
        return recebimentos
    return recebimentos[pd.to_datetime(recebimentos["Data Agenda"]).dt.to_period("M") == periodo]


def proximos_recebimentos(df, limite=8):
    hoje = pd.Timestamp.today().normalize().date()
    df_futuro = df[df["Data Agenda"] >= hoje].copy()
    if df_futuro.empty:
        return pd.DataFrame(columns=["Data Agenda", "Titulo", "Qtd"])

    resumo = (
        df_futuro.groupby("Data Agenda")
        .agg(Titulo=("Fornecedor", lambda s: s.value_counts().index[0]), Qtd=("Quantidade", "sum"))
        .reset_index()
    )
    return resumo.sort_values("Data Agenda").head(limite)


def render_proximos(recebimentos):
    eventos = proximos_recebimentos(recebimentos)

    st.markdown('<div class="events-head"><div class="section-title">Próximos recebimentos</div></div>', unsafe_allow_html=True)

    if eventos.empty:
        st.markdown('<div class="empty">Nenhum recebimento futuro encontrado.</div>', unsafe_allow_html=True)
        return

    for _, linha in eventos.iterrows():
        unidade = "item" if int(linha["Qtd"]) == 1 else "itens"
        st.markdown(
            f"""
            <div class="mini-event event-recebimento">
                <div class="mini-event-icon">{icone_svg("recebimento")}</div>
                <div>
                    <strong>Recebimento</strong>
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
        <div class="detail-table-wrap">
            <table class="detail-table">
                <thead><tr>{cabecalho}</tr></thead>
                <tbody>{"".join(linhas)}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.dialog("Detalhes do dia", width="large")
def abrir_detalhe_dia(data, recebimentos):
    recebimentos_dia = recebimentos_do_dia(recebimentos, data)

    st.markdown(
        f"""
        <div class="dialog-head">
            <h2>{formatar_data(data)}</h2>
            <p>{escape(label_prazo(data))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if recebimentos_dia.empty:
        st.info("Não há recebimentos programados para este dia.")
        return

    render_detalhe_recebimentos(recebimentos_dia, data)


def render_confirmacao(df, data, pedidos_dia):
    try:
        registrados = recebimentos_registrados()
    except Exception as exc:
        st.warning(f"Não foi possível ler a aba Histórico: {exc}")
        return

    pedidos_pendentes = [pedido for pedido in pedidos_dia if not registrados.contem(pedido, data)]

    st.markdown("**Confirmação de recebimento**")
    if not pedidos_dia:
        st.info("Nenhum pedido encontrado para confirmar.")
        return
    if not pedidos_pendentes:
        st.markdown(
            '<div class="status-box">Todos os recebimentos deste dia já foram registrados.</div>',
            unsafe_allow_html=True,
        )
        return

    texto_botao = "Confirmar recebimento do dia" if len(pedidos_pendentes) == 1 else "Confirmar recebimentos do dia"
    st.caption("Pendentes: " + ", ".join(pedidos_pendentes))
    if st.button(texto_botao, key=f"confirmar_recebimentos_{data.strftime('%Y%m%d')}", use_container_width=True):
        try:
            confirmados = registrar_recebimentos([(pedido, data) for pedido in pedidos_pendentes])
        except Exception as exc:
            st.error(f"Não foi possível registrar no Histórico: {exc}")
        else:
            st.success(f"{confirmados} recebimento(s) registrado(s) no Histórico.")
            st.rerun()


def render_picks(df, data, pedidos_dia):
    st.markdown("**Pick para conferência**")
    chave_data = data.strftime("%Y%m%d")

    if len(pedidos_dia) > 1:
        st.download_button(
            f"Baixar pick de todos os pedidos do dia ({len(pedidos_dia)})",
            data=gerar_pick_pdf(df, data),
            file_name=f"pick_{chave_data}.pdf",
            mime="application/pdf",
            key=f"pick_dia_{chave_data}",
            use_container_width=True,
        )

    for pedido in pedidos_dia:
        itens_pedido = df[df["Pedido"] == pedido]
        fornecedor = itens_pedido["Fornecedor"].iloc[0]
        coluna_texto, coluna_botao = st.columns([3, 1], vertical_alignment="center")
        with coluna_texto:
            st.markdown(
                f"**Pedido {escape(pedido)}** · {escape(fornecedor)} · "
                f"{len(itens_pedido)} linha(s), {numero(total_itens(itens_pedido))} un."
            )
        with coluna_botao:
            st.download_button(
                "Baixar pick",
                data=gerar_pick_pdf(itens_pedido, data),
                file_name=f"pick_pedido_{pedido}_{chave_data}.pdf",
                mime="application/pdf",
                key=f"pick_{pedido}_{chave_data}",
                use_container_width=True,
            )


def render_detalhe_recebimentos(df, data):
    pedidos = df["Pedido"].nunique()
    itens = total_itens(df)
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

    pedidos_dia = [pedido for pedido in dict.fromkeys(df["Pedido"].astype(str).str.strip()) if pedido]

    render_confirmacao(df, data, pedidos_dia)
    render_picks(df, data, pedidos_dia)

    por_fornecedor = (
        df.groupby("Fornecedor")
        .agg(Pedidos=("Pedido", "nunique"), Itens=("Quantidade", "sum"))
        .reset_index()
        .sort_values(["Pedidos", "Itens"], ascending=False)
    )
    por_fornecedor["Itens"] = por_fornecedor["Itens"].map(numero)
    st.markdown("**Resumo por fornecedor**")
    render_tabela_html(por_fornecedor, ["Fornecedor", "Pedidos", "Itens"])

    detalhes = df[["Pedido", "Fornecedor", "Codigo", "Descricao", "UN", "Quantidade"]].copy()
    detalhes = detalhes.rename(columns={"Codigo": "Código", "Descricao": "Descrição"})
    st.markdown("**Itens do dia**")
    render_tabela_html(detalhes, ["Pedido", "Fornecedor", "Código", "Descrição", "UN", "Quantidade"])


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

    .agenda-icon-img {
        width: 36px;
        height: 36px;
        object-fit: contain;
        display: block;
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

    .kpi-recebimento {border-left: 8px solid #86efac;}
    .kpi-mes {border-left: 8px solid #86efac;}

    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 8px 10px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stHorizontalBlock"] {
        gap: 0 !important;
        margin-bottom: 0 !important;
    }

    .calendar-head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 8px;
    }

    .calendar-title {
        color: #000000;
        font-size: 28px;
        font-weight: 900;
        text-align: center;
        line-height: 40px;
    }

    .weekday {
        box-sizing: border-box;
        padding: 9px 4px;
        border: 2px solid #000000;
        border-radius: 0;
        background: #000000;
        color: #ffffff;
        text-align: center;
        font-size: 13px;
        font-weight: 900;
    }

    .stButton > button {
        border: 3px solid #000000 !important;
        border-radius: 0 !important;
        background: #ffffff !important;
        color: #000000 !important;
        box-shadow: none !important;
        font-weight: 900 !important;
    }

    .calendar-day .stButton > button {
        width: calc(100% - 0.3cm) !important;
        box-sizing: border-box !important;
        margin: 0 0.3cm 0.3cm 0 !important;
        min-height: 116px !important;
        padding: 8px !important;
        white-space: pre-line !important;
        line-height: 1.25 !important;
        font-size: 14px !important;
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
        background: #86efac !important;
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

    .legend-recebimento::before {background: #86efac;}

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
        grid-template-columns: 52px minmax(0, 1fr) 72px;
        align-items: center;
        gap: 12px;
        margin-bottom: 8px;
        padding: 9px 10px;
        border: 3px solid #000000;
        border-radius: 4px;
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
        border-left: 8px solid #86efac;
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

    div[data-testid="stDialog"] {
        position: fixed !important;
        inset: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 2rem !important;
    }

    div[data-testid="stDialog"] > div {
        width: min(1120px, calc(100vw - 5rem)) !important;
        max-width: min(1120px, calc(100vw - 5rem)) !important;
        min-height: auto !important;
        max-height: 86vh !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        margin: 0 auto !important;
        border: 3px solid #000000 !important;
        border-radius: 8px !important;
        background: #ffffff !important;
    }

    div[data-testid="stDialog"] > div::-webkit-scrollbar,
    .detail-table-wrap::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }

    div[data-testid="stDialog"] > div::-webkit-scrollbar-thumb,
    .detail-table-wrap::-webkit-scrollbar-thumb {
        background: #000000;
        border-radius: 0;
    }

    div[data-testid="stDialog"] > div::-webkit-scrollbar-track,
    .detail-table-wrap::-webkit-scrollbar-track {
        background: #ffffff;
    }

    div[data-testid="stDialog"] [data-testid="stVerticalBlock"] {
        gap: .55rem !important;
    }

    .detail-metrics {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 8px;
        margin: 6px 0 10px 0;
    }

    .detail-metric {
        min-height: 54px;
        padding: 7px 9px;
        border: 2px solid #000000;
        border-radius: 4px;
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

    .status-box {
        margin: 8px 0 12px 0;
        padding: 10px 12px;
        border: 2px solid #000000;
        border-radius: 4px;
        background: #f3f4f6;
        color: #000000;
        font-size: 13px;
        font-weight: 850;
    }

    .detail-table-wrap {
        width: 100%;
        max-height: 260px;
        overflow: auto;
        border: 2px solid #000000;
        border-radius: 4px;
        margin: 6px 0 12px 0;
        background: #ffffff;
    }

    .detail-table-wrap thead th {
        position: sticky;
        top: 0;
        z-index: 1;
    }

    .detail-table {
        width: 100%;
        border-collapse: collapse;
        border-spacing: 0;
        border: 0;
        margin: 0;
        table-layout: fixed;
    }

    .detail-table th {
        background: #000000;
        color: #ffffff;
        padding: 7px 8px;
        font-size: 12px;
        font-weight: 900;
        text-align: left;
        border: 1px solid #000000;
    }

    .detail-table td {
        min-height: 30px;
        padding: 6px 8px;
        color: #000000;
        background: #ffffff;
        border: 1px solid #98a2b3;
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
    st.page_link("pages/Cronograma.py", label="Agenda")

logo_branco = base64.b64encode(Path("Logo Branco.bmp").read_bytes()).decode("utf-8")
logo_goper = base64.b64encode(Path("logo preto goper.png").read_bytes()).decode("utf-8")

st.markdown(
    f"""
    <div class="page-head">
        <div class="page-title">
            <h1>Agenda de Recebimentos</h1>
            <p>Calendário mensal com os recebimentos programados.</p>
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

_, coluna_atualizar = st.columns([6, 1])
with coluna_atualizar:
    if st.button("Atualizar dados", use_container_width=True):
        carregar_dados.clear()
        carregar_historico_recebimentos.clear()
        st.rerun()

try:
    dados_pedidos = carregar_dados()
except PlanilhaIndisponivel as exc:
    st.error(str(exc))
    st.stop()

try:
    recebimentos = preparar_recebimentos(dados_pedidos)
except Exception as exc:
    recebimentos = preparar_recebimentos(pd.DataFrame())
    st.warning("Não foi possível carregar a aba de pedidos.")
    st.caption(str(exc))

hoje = pd.Timestamp.today().normalize().date()
mes_atual = pd.Timestamp.today().to_period("M")

if recebimentos.empty:
    meses = [mes_atual]
else:
    meses = sorted(set(pd.to_datetime(recebimentos["Data Agenda"]).dt.to_period("M").dropna().tolist()))

idx_padrao = meses.index(mes_atual) if mes_atual in meses else len(meses) - 1

if "agenda_mes_idx" not in st.session_state:
    st.session_state.agenda_mes_idx = idx_padrao

st.session_state.agenda_mes_idx = max(0, min(st.session_state.agenda_mes_idx, len(meses) - 1))
mes_selecionado = meses[st.session_state.agenda_mes_idx]

recebimentos_mes = recebimentos_do_mes(recebimentos, mes_selecionado)
recebimentos_hoje = recebimentos_do_dia(recebimentos, hoje)

k1, k2, k3, k4 = st.columns(4)
with k1:
    render_kpi("Recebimentos hoje", numero(total_itens(recebimentos_hoje)), "Itens previstos", "kpi-recebimento", "recebimento")
with k2:
    render_kpi("Pedidos hoje", numero(recebimentos_hoje["Pedido"].nunique()), "Pedidos a receber", "kpi-recebimento", "compromisso")
with k3:
    render_kpi("Recebimentos do mês", numero(total_itens(recebimentos_mes)), "Itens no calendário", "kpi-mes", "recebimento")
with k4:
    render_kpi("Pedidos do mês", numero(recebimentos_mes["Pedido"].nunique()), "Pedidos no calendário", "kpi-mes", "compromisso")

col_calendario, col_lateral = st.columns([3.35, 1], gap="medium")

with col_calendario:
    with st.container(border=True):
        h1, h2, h3 = st.columns([.38, 2.4, .38])

        with h1:
            if st.button("<", use_container_width=True, disabled=st.session_state.agenda_mes_idx <= 0):
                st.session_state.agenda_mes_idx -= 1
                st.rerun()

        with h2:
            st.markdown(f'<div class="calendar-title">{escape(mes_formatado(mes_selecionado))}</div>', unsafe_allow_html=True)

        with h3:
            if st.button(">", use_container_width=True, disabled=st.session_state.agenda_mes_idx >= len(meses) - 1):
                st.session_state.agenda_mes_idx += 1
                st.rerun()

        semana_header = st.columns(7, gap=None)
        for indice, dia in enumerate(DIAS_SEMANA):
            with semana_header[indice]:
                st.markdown(f'<div class="weekday">{dia}</div>', unsafe_allow_html=True)

        estilo_base = "border-color: #000000 !important; color: #000000 !important;"
        calendario = calendar.Calendar(firstweekday=0)
        for semana in calendario.monthdatescalendar(mes_selecionado.year, mes_selecionado.month):
            cols = st.columns(7, gap=None)
            for indice, data in enumerate(semana):
                fora_mes = data.month != mes_selecionado.month
                recebimentos_dia = recebimentos_do_dia(recebimentos, data)
                tem_recebimento = not fora_mes and not recebimentos_dia.empty

                texto_botao = f"{data.day}"
                if tem_recebimento:
                    texto_botao += f"\n\nR {numero(total_itens(recebimentos_dia))}"

                fundo = "#86efac" if tem_recebimento else "#ffffff"
                estilo_botao = f"background: {fundo} !important; {estilo_base}"
                if data == hoje:
                    estilo_botao += " outline: 3px solid #2563eb !important; outline-offset: 1px !important;"

                with cols[indice]:
                    chave_dia = f"cal_{data.strftime('%Y_%m_%d')}"
                    st.markdown(
                        f"""
                        <style>
                        .st-key-{chave_dia} button {{
                            min-height: 126px !important;
                            padding: 8px !important;
                            white-space: pre-line !important;
                            line-height: 1.25 !important;
                            font-size: 15px !important;
                            font-weight: 800 !important;
                            border-radius: 0 !important;
                            width: calc(100% - 0.3cm) !important;
                            box-sizing: border-box !important;
                            margin: 0 0.3cm 0.3cm 0 !important;
                            {estilo_botao}
                        }}
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )
                    if st.button(texto_botao, key=chave_dia, use_container_width=True, disabled=fora_mes):
                        abrir_detalhe_dia(data, recebimentos)

        st.markdown(
            """
            <div class="legend-row">
                <span class="legend-dot legend-recebimento">Recebimento programado</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

with col_lateral:
    with st.container(border=True):
        render_proximos(recebimentos)
