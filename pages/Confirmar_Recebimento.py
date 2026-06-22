import base64
from html import escape
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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
        rightMargin=.35 * cm,
        leftMargin=.35 * cm,
        topMargin=.35 * cm,
        bottomMargin=.35 * cm,
    )
    estilos = getSampleStyleSheet()
    normal = estilos["BodyText"]
    normal.fontName = "Helvetica"
    normal.fontSize = 6.4
    normal.leading = 7.2

    titulo_style = estilos["Title"]
    titulo_style.fontName = "Helvetica-Bold"
    titulo_style.fontSize = 18
    titulo_style.leading = 22

    linhas = preparar_linhas_pdf(numero_pedido, itens)
    cabecalho = ["Numero do pedido", "Codigo", "Descricao", "Qtde", "Grupo", "Volumetria", "Conferencia"]
    dados = [cabecalho]
    for linha in linhas:
        dados.append([Paragraph(escape(str(valor)), normal) for valor in linha])

    base_dir = Path(__file__).resolve().parents[1]
    logo_principal = base_dir / "icones" / "romaneio-logo-trendx.png"
    logo_simbolo = base_dir / "icones" / "romaneio-logo-simbolo.png"
    header = Table(
        [
            [
                Image(str(logo_principal), width=4.2 * cm, height=1.02 * cm),
                Paragraph(f"Romaneio de conferencia - Pedido: {escape(str(numero_pedido))}", titulo_style),
                Image(str(logo_simbolo), width=1.05 * cm, height=1.05 * cm),
            ]
        ],
        colWidths=[5.2 * cm, 18.3 * cm, 5.2 * cm],
    )
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (0, 0), "LEFT"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    tabela = Table(
        dados,
        repeatRows=1,
        colWidths=[3.0 * cm, 2.2 * cm, 10.0 * cm, 1.4 * cm, 4.7 * cm, 2.5 * cm, 4.8 * cm],
    )
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.black),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, 0), 6.8),
                ("FONTSIZE", (0, 1), (-1, -1), 6.4),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                ("GRID", (0, 0), (-1, -1), .55, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (3, 1), (3, -1), "CENTER"),
                ("ALIGN", (5, 1), (6, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ("MINROWHEIGHT", (0, 0), (-1, 0), .55 * cm),
                ("MINROWHEIGHT", (0, 1), (-1, -1), .62 * cm),
            ]
        )
    )

    documento.build([header, Spacer(1, .15 * cm), tabela])
    buffer.seek(0)
    return buffer.getvalue()


def imagem_base64(caminho):
    return base64.b64encode(Path(caminho).read_bytes()).decode("ascii")


def render_botao_imprimir_romaneio(numero_pedido, itens):
    linhas = preparar_linhas_pdf(numero_pedido, itens)
    base_dir = Path(__file__).resolve().parents[1]
    logo_trendx = imagem_base64(base_dir / "icones" / "romaneio-logo-trendx.png")
    logo_simbolo = imagem_base64(base_dir / "icones" / "romaneio-logo-simbolo.png")

    linhas_html = []
    for linha in linhas:
        linhas_html.append(
            "<tr>"
            + "".join(f"<td>{escape(str(valor))}</td>" for valor in linha)
            + "</tr>"
        )

    tabela_html = "\n".join(linhas_html)
    titulo = f"Romaneio de conferencia - Pedido: {escape(str(numero_pedido))}"

    components.html(
        f"""
        <button id="botao-imprimir-romaneio" type="button">Imprimir carregamento</button>
        <script>
        const botao = document.getElementById("botao-imprimir-romaneio");
        botao.addEventListener("click", () => {{
            const janela = window.open("", "_blank", "width=1200,height=800");
            if (!janela) {{
                alert("O navegador bloqueou a janela de impressao. Libere pop-ups para imprimir.");
                return;
            }}
            janela.document.open();
            janela.document.write(`
                <!doctype html>
                <html>
                    <head>
                        <title>{titulo}</title>
                        <style>
                            @page {{
                                size: A4 landscape;
                                margin: 5mm;
                            }}
                            * {{
                                box-sizing: border-box;
                            }}
                            body {{
                                margin: 0;
                                background: #ffffff;
                                color: #000000;
                                font-family: Arial, Helvetica, sans-serif;
                            }}
                            .topo {{
                                display: grid;
                                grid-template-columns: 190px 1fr 80px;
                                align-items: center;
                                gap: 12px;
                                margin: 6px 0 8px 0;
                            }}
                            .logo-trendx {{
                                width: 150px;
                                height: auto;
                            }}
                            .logo-simbolo {{
                                width: 44px;
                                height: auto;
                                justify-self: end;
                            }}
                            h1 {{
                                margin: 0;
                                text-align: center;
                                font-size: 24px;
                                line-height: 1.1;
                                font-weight: 800;
                            }}
                            table {{
                                width: 100%;
                                border-collapse: collapse;
                                table-layout: fixed;
                                background: #ffffff;
                            }}
                            th {{
                                background: #000000;
                                color: #ffffff;
                                border: 1px solid #000000;
                                padding: 5px 4px;
                                font-size: 10px;
                                text-align: left;
                                font-weight: 700;
                            }}
                            td {{
                                height: 20px;
                                border: 1px solid #000000;
                                padding: 3px 4px;
                                font-size: 9px;
                                vertical-align: middle;
                                background: #ffffff;
                                overflow-wrap: anywhere;
                            }}
                            th:nth-child(1), td:nth-child(1) {{ width: 11%; }}
                            th:nth-child(2), td:nth-child(2) {{ width: 10%; }}
                            th:nth-child(3), td:nth-child(3) {{ width: 35%; }}
                            th:nth-child(4), td:nth-child(4) {{ width: 6%; text-align: center; }}
                            th:nth-child(5), td:nth-child(5) {{ width: 17%; }}
                            th:nth-child(6), td:nth-child(6) {{ width: 10%; text-align: center; }}
                            th:nth-child(7), td:nth-child(7) {{ width: 11%; }}
                            @media print {{
                                body {{
                                    -webkit-print-color-adjust: exact;
                                    print-color-adjust: exact;
                                }}
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="topo">
                            <img class="logo-trendx" src="data:image/png;base64,{logo_trendx}">
                            <h1>{titulo}</h1>
                            <img class="logo-simbolo" src="data:image/png;base64,{logo_simbolo}">
                        </div>
                        <table>
                            <thead>
                                <tr>
                                    <th>Numero do pedido</th>
                                    <th>Codigo</th>
                                    <th>Descricao</th>
                                    <th>Qtde</th>
                                    <th>Grupo</th>
                                    <th>Volumetria</th>
                                    <th>Conferencia</th>
                                </tr>
                            </thead>
                            <tbody>
                                {tabela_html}
                            </tbody>
                        </table>
                        <script>
                            window.onload = () => {{
                                setTimeout(() => {{
                                    window.focus();
                                    window.print();
                                }}, 250);
                            }};
                        <\\/script>
                    </body>
                </html>
            `);
            janela.document.close();
        }});
        </script>
        <style>
            #botao-imprimir-romaneio {{
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

    render_botao_imprimir_romaneio(numero, itens)

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
