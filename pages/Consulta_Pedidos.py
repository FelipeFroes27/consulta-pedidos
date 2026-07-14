import base64
from pathlib import Path

import streamlit as st
import pandas as pd
from utils.display_mode import ativar_modo_exibicao, render_menu_lateral
from utils.sheets import carregar_dados

# ==================================================
# CONFIGURAÇÃO DA PÁGINA
# ==================================================

st.set_page_config(
    page_title="Consulta de Pedidos",
    layout="wide",
    initial_sidebar_state="expanded"
)

ativar_modo_exibicao("consulta")

# ==================================================
# CSS
# ==================================================

st.markdown("""
<style>

/* Mantem a seta lateral sem mostrar a barra superior */
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

[data-testid="stStatusWidget"] {
    display: none !important;
}

[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapseButton"] {
    visibility: hidden !important;
    display: none !important;
}

[data-testid="stHeaderActionElements"],
[data-testid="stStatusWidget"],
[data-testid="stToolbar"],
[data-testid="stDecoration"] {
    display: none !important;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

/* Reduz espaço superior */
.block-container,
[data-testid="stMainBlockContainer"] {
    max-width: 1540px;
    padding-top: .25rem;
    padding-bottom: 1.25rem;
}

/* Compacta componentes */
div[data-baseweb="select"] {
    font-size: 14px;
}

.sidebar-logo {
    display: flex;
    justify-content: center;
    padding: 8px 0 18px 0;
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

.sidebar-logo img {
    background: #ffffff;
    border: 0;
    border-radius: 0;
    padding: 0;
}

.page-logos {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 0 0 auto;
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

.page-head {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 1.25rem;
}

.page-title h1 {
    margin: 0;
    color: #000000;
    font-size: 29px;
    line-height: 1.05;
    font-weight: 850;
    letter-spacing: 0;
}

.stButton > button,
div[data-baseweb="select"] > div,
[data-testid="stDateInput"] input {
    border: 2px solid #000000 !important;
    background: #ffffff !important;
    color: #000000 !important;
    border-radius: 7px !important;
    box-shadow: none !important;
}

div[data-testid="stDataFrame"] {
    border: 2px solid #000000;
    border-radius: 12px;
    overflow: hidden;
}

</style>
""", unsafe_allow_html=True)

render_menu_lateral()

with st.sidebar:
    st.markdown('<div class="sidebar-logo">', unsafe_allow_html=True)
    st.image("Logo Branco.bmp", width=72)
    st.image("logo preto goper.png", width=32)
    st.markdown("</div>", unsafe_allow_html=True)
    st.page_link("app.py", label="Início")
    st.page_link("pages/Consulta_Pedidos.py", label="Consulta de Pedidos")
    st.page_link("pages/Cronograma.py", label="Agenda")

# ==================================================
# TÍTULO
# ==================================================

logo_branco = base64.b64encode(Path("Logo Branco.bmp").read_bytes()).decode("utf-8")
logo_goper = base64.b64encode(Path("logo preto goper.png").read_bytes()).decode("utf-8")

st.markdown(
    f"""
    <div class="page-head">
        <div class="page-title">
            <h1>Consulta de Pedidos</h1>
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

# ==================================================
# CARREGAR DADOS
# ==================================================

df = carregar_dados()

# ==================================================
# PRESERVAR ZEROS À ESQUERDA
# ==================================================

df["Numero do Pedido"] = (
    df["Numero do Pedido"]
    .fillna("")
    .astype(str)
    .str.strip()
)

df["Codigo"] = (
    df["Codigo"]
    .fillna("")
    .astype(str)
    .str.strip()
)

# ==================================================
# CAMPOS TEXTO
# ==================================================

colunas_texto = [
    "Descricao",
    "Referência",
    "Subgrupo",
    "Marca",
    "Categoria",
    "Grupo",
    "Tipo"
]

for col in colunas_texto:
    df[col] = (
        df[col]
        .fillna("")
        .astype(str)
        .str.strip()
    )

# ==================================================
# DATAS
# ==================================================

df["Data Emissao"] = pd.to_datetime(
    df["Data Emissao"],
    errors="coerce",
    dayfirst=True
)

df["Data Entrega"] = pd.to_datetime(
    df["Data Entrega"],
    errors="coerce",
    dayfirst=True
)

# ==================================================
# LIMITES DE DATA
# ==================================================

data_min_emissao = df["Data Emissao"].min().date()
data_max_emissao = df["Data Emissao"].max().date()

data_min_entrega = df["Data Entrega"].min().date()
data_max_entrega = df["Data Entrega"].max().date()

# ==================================================
# FILTROS
# ==================================================

col1, col2, col3, col4 = st.columns(4)

with col1:

    pedido = st.multiselect(
        "Pedido",
        sorted(df["Numero do Pedido"].unique()),
        placeholder="Selecionar..."
    )

with col2:

    codigo = st.multiselect(
        "Código",
        sorted(df["Codigo"].unique()),
        placeholder="Selecionar..."
    )

with col3:

    referencia = st.multiselect(
        "Referência",
        sorted(df["Referência"].unique()),
        placeholder="Selecionar..."
    )

with col4:

    marca = st.multiselect(
        "Marca",
        sorted(df["Marca"].unique()),
        placeholder="Selecionar..."
    )

# ==================================================

col5, col6, col7, col8 = st.columns(4)

with col5:

    descricao = st.multiselect(
        "Descrição",
        sorted(df["Descricao"].unique()),
        placeholder="Selecionar..."
    )

with col6:

    subgrupo = st.multiselect(
        "Subgrupo",
        sorted(df["Subgrupo"].unique()),
        placeholder="Selecionar..."
    )

with col7:

    categoria = st.multiselect(
        "Categoria",
        sorted(df["Categoria"].unique()),
        placeholder="Selecionar..."
    )

with col8:

    grupo = st.multiselect(
        "Grupo",
        sorted(df["Grupo"].unique()),
        placeholder="Selecionar..."
    )

# ==================================================

col9, col10, col11, col12 = st.columns(4)

with col9:

    tipo = st.multiselect(
        "Tipo",
        sorted(df["Tipo"].unique()),
        placeholder="Selecionar..."
    )

with col10:

    periodo_emissao = st.date_input(
        "Emissão",
        value=(
            data_min_emissao,
            data_max_emissao
        )
    )

with col11:

    periodo_entrega = st.date_input(
        "Entrega",
        value=(
            data_min_entrega,
            data_max_entrega
        )
    )

with col12:

    st.write("")
    st.write("")

    pesquisar = st.button(
        "🔍 Pesquisar",
        use_container_width=True
    )

# ==================================================
# RESULTADOS
# ==================================================

if pesquisar:

    resultado = df.copy()

    if pedido:
        resultado = resultado[
            resultado["Numero do Pedido"].isin(pedido)
        ]

    if codigo:
        resultado = resultado[
            resultado["Codigo"].isin(codigo)
        ]

    if descricao:
        resultado = resultado[
            resultado["Descricao"].isin(descricao)
        ]

    if referencia:
        resultado = resultado[
            resultado["Referência"].isin(referencia)
        ]

    if subgrupo:
        resultado = resultado[
            resultado["Subgrupo"].isin(subgrupo)
        ]

    if marca:
        resultado = resultado[
            resultado["Marca"].isin(marca)
        ]

    if categoria:
        resultado = resultado[
            resultado["Categoria"].isin(categoria)
        ]

    if grupo:
        resultado = resultado[
            resultado["Grupo"].isin(grupo)
        ]

    if tipo:
        resultado = resultado[
            resultado["Tipo"].isin(tipo)
        ]

    # ==========================================
    # FILTRO DATA EMISSÃO
    # ==========================================

    if len(periodo_emissao) == 2:

        resultado = resultado[
            (
                resultado["Data Emissao"]
                >= pd.to_datetime(periodo_emissao[0])
            )
            &
            (
                resultado["Data Emissao"]
                <= pd.to_datetime(periodo_emissao[1])
            )
        ]

    # ==========================================
    # FILTRO DATA ENTREGA
    # ==========================================

    if len(periodo_entrega) == 2:

        resultado = resultado[
            (
                resultado["Data Entrega"]
                >= pd.to_datetime(periodo_entrega[0])
            )
            &
            (
                resultado["Data Entrega"]
                <= pd.to_datetime(periodo_entrega[1])
            )
        ]

    # ==========================================
    # FORMATAÇÃO
    # ==========================================

    resultado["Data Entrega"] = resultado[
        "Data Entrega"
    ].dt.strftime("%d/%m/%Y")

    resultado = resultado[
        [
            "Numero do Pedido",
            "Data Entrega",
            "Codigo",
            "Descricao",
            "Qtde"
        ]
    ]

    for coluna_texto in ["Numero do Pedido", "Codigo"]:
        resultado[coluna_texto] = resultado[coluna_texto].fillna("").astype("string")

    resultado = resultado.rename(
        columns={
            "Numero do Pedido": "Número do Pedido",
            "Codigo": "Código",
            "Descricao": "Descrição",
            "Qtde": "Quantidade",
        }
    )

    st.session_state["consulta_resultado"] = resultado
    st.session_state["consulta_total_resultados"] = len(resultado)

if "consulta_resultado" in st.session_state:
    resultado = st.session_state["consulta_resultado"]

    st.divider()

    st.caption(
        f"{st.session_state.get('consulta_total_resultados', len(resultado))} registro(s) encontrado(s)"
    )

    st.dataframe(
        resultado,
        use_container_width=True,
        hide_index=True,
        height=800,
        column_config={
            "Número do Pedido": st.column_config.TextColumn("Número do Pedido"),
            "Código": st.column_config.TextColumn("Código"),
        },
    )
