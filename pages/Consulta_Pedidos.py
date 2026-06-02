import streamlit as st
import pandas as pd
from utils.sheets import carregar_dados

# ==================================================
# CONFIGURAÇÃO DA PÁGINA
# ==================================================

st.set_page_config(
    page_title="Consulta de Pedidos",
    layout="wide"
)

# ==================================================
# CSS
# ==================================================

st.markdown("""
<style>

/* Mantem a seta lateral sem mostrar a barra superior */
header,
header[data-testid="stHeader"] {
    visibility: visible !important;
    height: 0rem !important;
    min-height: 0rem !important;
    background: transparent !important;
    box-shadow: none !important;
    border: 0 !important;
}

[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapseButton"] {
    visibility: visible !important;
    display: flex !important;
    opacity: 1 !important;
    pointer-events: auto !important;
    position: fixed !important;
    top: 0.55rem !important;
    left: 0.55rem !important;
    z-index: 999999 !important;
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
st.markdown("## Consulta de Pedidos")

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

    st.divider()

    st.caption(
        f"{len(resultado)} registro(s) encontrado(s)"
    )

    st.dataframe(
        resultado,
        use_container_width=True,
        hide_index=True,
        height=800
    )
