import base64
from html import escape
from io import BytesIO

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from utils.display_mode import ativar_modo_exibicao, render_menu_lateral
from utils.sheets import carregar_volumetria, localizar_pedido, recebimento_ja_registrado, registrar_recebimento


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
    st.page_link("app.py", label="Inicio")
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
    if isinstance(valor, (int, float)):
        numero = pd.to_numeric(valor, errors="coerce")
    else:
        texto_numero = str(valor or "").strip()
        if "," in texto_numero and "." in texto_numero:
            texto_numero = texto_numero.replace(".", "").replace(",", ".")
        elif "," in texto_numero:
            texto_numero = texto_numero.replace(",", ".")
        numero = pd.to_numeric(texto_numero, errors="coerce")
    if pd.isna(numero):
        return texto(valor)
    if float(numero).is_integer():
        return str(int(numero))
    return str(round(float(numero), 2)).replace(".", ",")


def somar_coluna(df, coluna):
    if coluna not in df.columns:
        return None

    valores = df[coluna].fillna("").astype(str).str.strip()
    valores = valores.mask(
        valores.str.contains(",", regex=False) & valores.str.contains(".", regex=False),
        valores.str.replace(".", "", regex=False).str.replace(",", ".", regex=False),
    )
    valores = valores.mask(
        valores.str.contains(",", regex=False) & ~valores.str.contains(".", regex=False),
        valores.str.replace(",", ".", regex=False),
    )
    numeros = pd.to_numeric(valores, errors="coerce")
    return numeros.sum() if numeros.notna().any() else None


def normalizar_coluna(nome):
    texto_coluna = str(nome or "").strip().lower()
    trocas = {
        "Ã³": "o",
        "ó": "o",
        "Ã§": "c",
        "ç": "c",
        "Ã£": "a",
        "ã": "a",
        "Ãª": "e",
        "ê": "e",
        "Ãº": "u",
        "ú": "u",
        "Ã­": "i",
        "í": "i",
    }
    for origem, destino in trocas.items():
        texto_coluna = texto_coluna.replace(origem, destino)
    return " ".join(texto_coluna.split())


def encontrar_coluna(df, opcoes):
    mapa = {normalizar_coluna(coluna): coluna for coluna in df.columns}
    for opcao in opcoes:
        coluna = mapa.get(normalizar_coluna(opcao))
        if coluna is not None:
            return coluna
    return None


def chave_codigo(valor):
    return "".join(char for char in str(valor or "").upper().strip() if char.isalnum())


def montar_mapa_volumetria():
    try:
        volumetria = carregar_volumetria()
    except Exception:
        return {}

    if volumetria.empty:
        return {}

    coluna_codigo = encontrar_coluna(volumetria, ["Codigo", "Código", "Produto", "Referencia", "Referência"])
    coluna_caixas = encontrar_coluna(
        volumetria,
        ["Volumetria", "Caixas por produto", "Caixas", "Qtd caixas", "Quantidade de caixas"],
    )

    if coluna_codigo is None or coluna_caixas is None:
        return {}

    mapa = {}
    for _, linha in volumetria.iterrows():
        codigo = chave_codigo(linha.get(coluna_codigo, ""))
        if codigo and codigo not in mapa:
            mapa[codigo] = str(linha.get(coluna_caixas, "")).strip() or "Nao cadastrado"
    return mapa


def preparar_linhas_pdf(numero_pedido, itens):
    mapa_volumetria = montar_mapa_volumetria()
    col_codigo = encontrar_coluna(itens, ["Codigo", "Código"])
    col_descricao = encontrar_coluna(itens, ["Descricao", "Descrição"])
    col_qtde = encontrar_coluna(itens, ["Qtde", "Quantidade", "Qtd"])
    col_grupo = encontrar_coluna(itens, ["Grupo"])

    linhas = []
    for _, item in itens.iterrows():
        codigo = str(item.get(col_codigo, "")).strip() if col_codigo else ""
        volumetria = mapa_volumetria.get(chave_codigo(codigo), "Nao cadastrado")
        linhas.append(
            [
                numero_pedido,
                codigo,
                str(item.get(col_descricao, "")).strip() if col_descricao else "",
                formatar_numero(item.get(col_qtde, "")) if col_qtde else "",
                str(item.get(col_grupo, "")).strip() if col_grupo else "",
                volumetria,
                "",
            ]
        )
    return linhas


def gerar_pdf_carregamento(numero_pedido, itens):
    buffer = BytesIO()
    documento = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=.8 * cm,
        leftMargin=.8 * cm,
        topMargin=.8 * cm,
        bottomMargin=.8 * cm,
    )
    estilos = getSampleStyleSheet()
    normal = estilos["BodyText"]
    normal.fontSize = 7
    normal.leading = 8

    linhas = preparar_linhas_pdf(numero_pedido, itens)
    cabecalho = ["Numero do pedido", "Codigo", "Descricao", "Qtde", "Grupo", "Volumetria", "Conferencia"]
    dados = [cabecalho]
    for linha in linhas:
        dados.append([Paragraph(escape(str(valor)), normal) for valor in linha])

    tabela = Table(
        dados,
        repeatRows=1,
        colWidths=[3.1 * cm, 2.5 * cm, 8.5 * cm, 1.7 * cm, 3.5 * cm, 2.6 * cm, 3.2 * cm],
    )
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), .4, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (3, 1), (3, -1), "CENTER"),
                ("ALIGN", (5, 1), (6, -1), "CENTER"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F7FB")]),
                ("MINROWHEIGHT", (0, 1), (-1, -1), .8 * cm),
            ]
        )
    )

    titulo = Paragraph(f"Carregamento do pedido {escape(str(numero_pedido))}", estilos["Title"])
    documento.build([titulo, Spacer(1, .25 * cm), tabela])
    buffer.seek(0)
    return buffer.getvalue()


def render_botao_imprimir_pdf(pdf_bytes, nome_arquivo):
    pdf_base64 = base64.b64encode(pdf_bytes).decode("ascii")
    nome_seguro = escape(nome_arquivo, quote=True)

    components.html(
        f"""
        <button id="print-pdf-button" type="button">
            Imprimir carregamento
        </button>
        <script>
        const button = document.getElementById("print-pdf-button");
        button.addEventListener("click", () => {{
            const pdfBase64 = "{pdf_base64}";
            const byteCharacters = atob(pdfBase64);
            const byteNumbers = new Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {{
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }}
            const byteArray = new Uint8Array(byteNumbers);
            const blob = new Blob([byteArray], {{ type: "application/pdf" }});
            const url = URL.createObjectURL(blob);
            const printWindow = window.open("", "_blank");

            if (!printWindow) {{
                window.open(url, "_blank");
                return;
            }}

            printWindow.document.write(`
                <!doctype html>
                <html>
                    <head>
                        <title>{nome_seguro}</title>
                        <style>
                            html, body {{
                                margin: 0;
                                width: 100%;
                                height: 100%;
                                overflow: hidden;
                            }}
                            iframe {{
                                border: 0;
                                width: 100%;
                                height: 100%;
                            }}
                        </style>
                    </head>
                    <body>
                        <iframe id="pdf-frame" src="${{url}}"></iframe>
                        <script>
                            const frame = document.getElementById("pdf-frame");
                            frame.onload = () => {{
                                setTimeout(() => {{
                                    frame.contentWindow.focus();
                                    frame.contentWindow.print();
                                }}, 500);
                            }};
                        <\\/script>
                    </body>
                </html>
            `);
            printWindow.document.close();
        }});
        </script>
        <style>
            #print-pdf-button {{
                width: 100%;
                min-height: 42px;
                border: 2px solid #000000;
                border-radius: 7px;
                background: #000000;
                color: #ffffff;
                font: 850 16px Arial, sans-serif;
                cursor: pointer;
            }}
        </style>
        """,
        height=52,
    )


def render_pedido(itens):
    primeiro = itens.iloc[0]
    numero = str(primeiro.get("Numero do Pedido", "")).strip()
    recebido = recebimento_ja_registrado(numero)
    quantidade_total = somar_coluna(itens, "Qtde")
    total_pedido = somar_coluna(itens, "Total")
    colunas_visiveis = [
        coluna
        for coluna in ["Codigo", "Descricao", "Qtde", "Total", "Referencia", "Marca", "Categoria", "Grupo", "Tipo"]
        if coluna in itens.columns
    ]
    altura_tabela = min(340, 70 + (len(itens) * 36))

    st.markdown(
        f"""
        <div class="panel">
            <strong>Informacoes do pedido</strong>
            <div class="detail-grid">
                <div class="detail-box">
                    <div class="detail-label">Pedido</div>
                    <div class="detail-value">{texto(numero)}</div>
                </div>
                <div class="detail-box">
                    <div class="detail-label">Fornecedor</div>
                    <div class="detail-value">{texto(primeiro.get("Fornecedor", ""))}</div>
                </div>
                <div class="detail-box">
                    <div class="detail-label">Data entrega</div>
                    <div class="detail-value">{escape(formatar_data(primeiro.get("Data Entrega", "")))}</div>
                </div>
                <div class="detail-box">
                    <div class="detail-label">Itens</div>
                    <div class="detail-value">{len(itens)}</div>
                </div>
                <div class="detail-box">
                    <div class="detail-label">Quantidade total</div>
                    <div class="detail-value">{escape(formatar_numero(quantidade_total)) if quantidade_total is not None else "-"}</div>
                </div>
                <div class="detail-box">
                    <div class="detail-label">Total</div>
                    <div class="detail-value">{escape(formatar_numero(total_pedido)) if total_pedido is not None else "-"}</div>
                </div>
                <div class="detail-box">
                    <div class="detail-label">Marca</div>
                    <div class="detail-value">{texto(primeiro.get("Marca", ""))}</div>
                </div>
                <div class="detail-box">
                    <div class="detail-label">Tipo</div>
                    <div class="detail-value">{texto(primeiro.get("Tipo", ""))}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if colunas_visiveis:
        st.dataframe(
            itens[colunas_visiveis],
            use_container_width=True,
            hide_index=True,
            height=altura_tabela,
        )

    try:
        pdf_carregamento = gerar_pdf_carregamento(numero, itens)
    except Exception as exc:
        st.error("Nao foi possivel gerar o PDF do carregamento.")
        st.caption(str(exc))
    else:
        nome_pdf = f"carregamento_pedido_{numero or 'sem_numero'}.pdf"
        render_botao_imprimir_pdf(pdf_carregamento, nome_pdf)
        st.download_button(
            "Baixar PDF",
            data=pdf_carregamento,
            file_name=nome_pdf,
            mime="application/pdf",
            use_container_width=True,
        )

    if recebido:
        st.markdown(
            '<div class="status-box">Recebimento ja registrado para este pedido.</div>',
            unsafe_allow_html=True,
        )
        return

    if st.button("Confirmar recebimento", key="confirmar_recebimento", use_container_width=True):
        try:
            registrar_recebimento(numero, itens)
        except Exception as exc:
            st.error(str(exc))
        else:
            st.success("Recebimento registrado no Historico.")
            st.rerun()


st.markdown(
    """
    <div class="page-head">
        <div class="page-title">
            <h1>Confirmar Recebimento</h1>
            <p>Digite o numero do pedido para consultar os dados e registrar o recebimento.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("form_busca_recebimento"):
    pedido_digitado = st.text_input(
        "Numero do pedido",
        value=st.session_state.get("pedido_recebimento", ""),
    )
    consultar = st.form_submit_button("Consultar", use_container_width=True)

if consultar:
    st.session_state.pedido_recebimento = pedido_digitado.strip()

numero_pedido = st.session_state.get("pedido_recebimento", "").strip()

if not numero_pedido:
    st.markdown(
        '<div class="status-box">Informe um numero de pedido para consultar.</div>',
        unsafe_allow_html=True,
    )
    st.stop()

try:
    encontrados = localizar_pedido(numero_pedido)
except Exception as exc:
    st.error("Nao foi possivel consultar a planilha.")
    st.caption(str(exc))
    st.stop()

if encontrados.empty:
    st.markdown(
        '<div class="status-box">Nenhum pedido encontrado com este numero.</div>',
        unsafe_allow_html=True,
    )
    st.stop()

render_pedido(encontrados)
