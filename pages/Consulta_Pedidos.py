import base64
from pathlib import Path

import streamlit as st
import pandas as pd
from utils.display_mode import ativar_modo_exibicao, render_menu_lateral
from utils.sheets import PlanilhaIndisponivel, carregar_dados, _encontrar_coluna as encontrar_coluna

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

try:
    df = carregar_dados()
except PlanilhaIndisponivel as exc:
    st.error(str(exc))
    st.stop()

if df.empty:
    st.info("A aba Pedidos ainda não tem registros.")
    st.stop()

# ==================================================
# COLUNAS (a base pode vir com nomes diferentes)
# ==================================================

FILTROS = [
    ("Pedido", ["Numero do Pedido", "Número do Pedido", "Pedido"]),
    ("Código", ["Codigo", "Código"]),
    ("Descrição", ["Descricao", "Descrição"]),
    ("Fornecedor", ["Forcededor", "Nome Fornecedor", "Razao Social Fornecedor"]),
    ("Empresa", ["Empresa"]),
    ("Referência", ["Referência", "Referencia"]),
    ("Marca", ["Marca"]),
    ("Subgrupo", ["Subgrupo"]),
    ("Categoria", ["Categoria"]),
    ("Grupo", ["Grupo"]),
    ("Tipo", ["Tipo"]),
]

filtros_disponiveis = []
for rotulo, nomes in FILTROS:
    nome_coluna = encontrar_coluna(df, nomes)
    if nome_coluna is not None:
        df[nome_coluna] = df[nome_coluna].fillna("").astype(str).str.strip()
        filtros_disponiveis.append((rotulo, nome_coluna))

colunas = dict(filtros_disponiveis)
coluna_pedido = colunas.get("Pedido")
if coluna_pedido is None:
    st.error("A aba de pedidos não tem a coluna \"Numero do Pedido\".")
    st.stop()

coluna_emissao = encontrar_coluna(df, ["Data Emissao", "Data de Emissão"])
coluna_entrega = encontrar_coluna(df, ["Data Entrega", "Data de Entrega"])
coluna_qtde = encontrar_coluna(df, ["Qtde", "Quantidade", "Qtd"])

for nome_coluna in [coluna_emissao, coluna_entrega]:
    if nome_coluna is not None:
        df[nome_coluna] = pd.to_datetime(df[nome_coluna], errors="coerce", dayfirst=True)


def limites_data(serie):
    hoje = pd.Timestamp.today().date()
    if serie.notna().any():
        return serie.min().date(), serie.max().date()
    return hoje, hoje


# ==================================================
# FILTROS
# ==================================================

campos = [("filtro", rotulo, nome_coluna) for rotulo, nome_coluna in filtros_disponiveis]
if coluna_emissao is not None:
    campos.append(("data", "Emissão", coluna_emissao))
if coluna_entrega is not None:
    campos.append(("data", "Entrega", coluna_entrega))
campos.append(("botao", None, None))

selecoes = {}
periodos = {}
pesquisar = False
for inicio in range(0, len(campos), 4):
    colunas_linha = st.columns(4)
    for coluna_layout, (tipo, rotulo, nome_coluna) in zip(colunas_linha, campos[inicio:inicio + 4]):
        with coluna_layout:
            if tipo == "filtro":
                opcoes = sorted(valor for valor in df[nome_coluna].unique() if valor)
                selecoes[nome_coluna] = st.multiselect(rotulo, opcoes, placeholder="Selecionar...")
            elif tipo == "data":
                limites = limites_data(df[nome_coluna])
                periodos[nome_coluna] = (limites, st.date_input(rotulo, value=limites))
            else:
                st.write("")
                st.write("")
                pesquisar = st.button("🔍 Pesquisar", use_container_width=True)

# ==================================================
# RESULTADOS
# ==================================================

if pesquisar:
    resultado = df.copy()

    for nome_coluna, valores in selecoes.items():
        if valores:
            resultado = resultado[resultado[nome_coluna].isin(valores)]

    for nome_coluna, (limites, periodo) in periodos.items():
        # Sem alterar o periodo padrao, mantem tambem os pedidos sem data.
        if len(periodo) == 2 and tuple(periodo) != tuple(limites):
            resultado = resultado[
                (resultado[nome_coluna] >= pd.to_datetime(periodo[0]))
                & (resultado[nome_coluna] <= pd.to_datetime(periodo[1]))
            ]

    exibir = [
        ("Número do Pedido", coluna_pedido),
        ("Data Entrega", coluna_entrega),
        ("Fornecedor", colunas.get("Fornecedor")),
        ("Código", colunas.get("Código")),
        ("Descrição", colunas.get("Descrição")),
        ("Quantidade", coluna_qtde),
    ]
    exibir = [(rotulo, nome_coluna) for rotulo, nome_coluna in exibir if nome_coluna is not None]

    resultado = resultado[[nome_coluna for _, nome_coluna in exibir]].copy()
    resultado.columns = [rotulo for rotulo, _ in exibir]
    if "Data Entrega" in resultado.columns:
        resultado["Data Entrega"] = resultado["Data Entrega"].dt.strftime("%d/%m/%Y").fillna("")
    for rotulo in ["Número do Pedido", "Código"]:
        if rotulo in resultado.columns:
            resultado[rotulo] = resultado[rotulo].astype("string")

    st.session_state["consulta_resultado"] = resultado

if "consulta_resultado" in st.session_state:
    resultado = st.session_state["consulta_resultado"]

    st.divider()
    st.caption(f"{len(resultado)} registro(s) encontrado(s)")

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
