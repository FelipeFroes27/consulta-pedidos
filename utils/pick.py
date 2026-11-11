"""Gera o pick de conferencia de recebimento em PDF."""

from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


_estilos = getSampleStyleSheet()
TITULO = ParagraphStyle("titulo", parent=_estilos["Title"], fontSize=15, leading=18, spaceAfter=2)
SUBTITULO = ParagraphStyle("subtitulo", parent=_estilos["Normal"], fontSize=9, alignment=TA_CENTER, textColor=colors.HexColor("#475467"))
CELULA = ParagraphStyle("celula", parent=_estilos["Normal"], fontSize=8, leading=10)
CELULA_NEGRITO = ParagraphStyle("celula_negrito", parent=CELULA, fontName="Helvetica-Bold")
CELULA_DIREITA = ParagraphStyle("celula_direita", parent=CELULA, alignment=TA_RIGHT)
CABECALHO = ParagraphStyle("cabecalho", parent=CELULA, fontName="Helvetica-Bold", textColor=colors.white)
TEXTO = ParagraphStyle("texto", parent=_estilos["Normal"], fontSize=9, leading=12)

LARGURA_UTIL = A4[0] - 24 * mm


class _MarcaPedido(Flowable):
    """Informa ao rodape qual pedido esta sendo impresso."""

    def __init__(self, pedido):
        super().__init__()
        self.pedido = pedido

    def wrap(self, *_):
        return 0, 0

    def draw(self):
        self.canv._pedido_atual = self.pedido


def _tem_cor(itens):
    if "Cor" not in itens.columns:
        return False
    valores = {str(valor).strip().upper() for valor in itens["Cor"].fillna("")}
    return bool(valores - {"", "UNICA", "ÚNICA", "0"})


def _p(texto, estilo=CELULA):
    return Paragraph(escape(str(texto or "")), estilo)


def _formatar_data(valor):
    if valor is None or (not isinstance(valor, str) and pd.isna(valor)):
        return ""
    if hasattr(valor, "strftime"):
        return valor.strftime("%d/%m/%Y")
    convertida = pd.to_datetime(str(valor), errors="coerce", dayfirst=True)
    return str(valor) if pd.isna(convertida) else convertida.strftime("%d/%m/%Y")


def _formatar_qtde(valor):
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return str(valor or "")
    if numero.is_integer():
        return f"{int(numero):,}".replace(",", ".")
    return f"{numero:.3f}".rstrip("0").rstrip(".").replace(".", ",")


def _primeiro(df, coluna):
    if coluna not in df.columns:
        return ""
    valores = [str(valor).strip() for valor in df[coluna].dropna() if str(valor).strip()]
    return valores[0] if valores else ""


def _bloco_pedido(pedido, itens, data_agendada, gerado_em):
    elementos = [
        _MarcaPedido(pedido),
        Paragraph("PICK DE CONFERÊNCIA — RECEBIMENTO", TITULO),
        Paragraph(f"Gerado em {gerado_em}", SUBTITULO),
        Spacer(1, 5 * mm),
    ]

    info = [
        [_p("Pedido", CELULA_NEGRITO), _p(pedido), _p("Entrega prevista", CELULA_NEGRITO), _p(_formatar_data(data_agendada))],
        [_p("Fornecedor", CELULA_NEGRITO), _p(_primeiro(itens, "Fornecedor")), _p("Emissão", CELULA_NEGRITO), _p(_formatar_data(_primeiro(itens, "Emissao")))],
        [_p("Empresa", CELULA_NEGRITO), _p(_primeiro(itens, "Empresa")), _p("Nota fiscal", CELULA_NEGRITO), _p("")],
    ]
    tabela_info = Table(info, colWidths=[24 * mm, 82 * mm, 30 * mm, LARGURA_UTIL - 136 * mm])
    tabela_info.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#98a2b3")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f2f4f7")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f2f4f7")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elementos += [tabela_info, Spacer(1, 3 * mm)]

    observacao = _primeiro(itens, "Observacao")
    if observacao:
        elementos += [Paragraph(f"<b>Observação do pedido:</b> {escape(observacao)}", TEXTO), Spacer(1, 3 * mm)]

    com_cor = _tem_cor(itens)
    cabecalho = ["#", "Código", "Descrição"] + (["Cor"] if com_cor else []) + [
        "UN", "Qtd prevista", "Qtd conferida", "OK", "Observação",
    ]
    linhas = [[_p(titulo, CABECALHO) for titulo in cabecalho]]
    itens_ordenados = itens.sort_values(["Codigo", "Descricao"], kind="stable") if "Codigo" in itens.columns else itens
    for indice, (_, item) in enumerate(itens_ordenados.iterrows(), start=1):
        linhas.append([
            _p(indice, CELULA_DIREITA),
            _p(item.get("Codigo", "")),
            _p(item.get("Descricao", "")),
            *([_p(item.get("Cor", ""))] if com_cor else []),
            _p(item.get("UN", "")),
            _p(_formatar_qtde(item.get("Quantidade", "")), CELULA_DIREITA),
            "",
            "",
            "",
        ])

    larguras = [8 * mm, 18 * mm, 66 * mm if com_cor else 82 * mm] + ([16 * mm] if com_cor else []) + [10 * mm, 17 * mm, 19 * mm, 9 * mm]
    larguras.append(LARGURA_UTIL - sum(larguras))
    tabela_itens = Table(linhas, colWidths=larguras, repeatRows=1)
    tabela_itens.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#98a2b3")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
    ]))
    elementos += [tabela_itens, Spacer(1, 3 * mm)]

    total_qtde = pd.to_numeric(itens.get("Quantidade", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
    elementos.append(Paragraph(
        f"<b>Total:</b> {len(itens)} linha(s) &nbsp;&nbsp;|&nbsp;&nbsp; <b>Quantidade prevista:</b> {_formatar_qtde(total_qtde)}",
        TEXTO,
    ))
    elementos.append(Spacer(1, 6 * mm))

    rodape = Table(
        [
            [_p("Divergências / avarias:", CELULA_NEGRITO), ""],
            ["", ""],
            ["", ""],
            [_p("Conferente:", CELULA_NEGRITO), _p("Data: ____/____/________     Assinatura: ______________________________")],
        ],
        colWidths=[38 * mm, LARGURA_UTIL - 38 * mm],
        rowHeights=[7 * mm, 7 * mm, 7 * mm, 10 * mm],
    )
    rodape.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.black),
        ("LINEBELOW", (0, 0), (-1, 2), 0.4, colors.HexColor("#98a2b3")),
        ("SPAN", (0, 1), (-1, 1)),
        ("SPAN", (0, 2), (-1, 2)),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
    ]))
    elementos.append(KeepTogether(rodape))
    return elementos


class _DocumentoPick(SimpleDocTemplate):
    def afterPage(self):
        # Chamado no fim de cada pagina, depois que o pedido da pagina ja foi marcado.
        _numerar_pagina(self.canv, self)


def _numerar_pagina(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#475467"))
    pedido = getattr(canvas, "_pedido_atual", "")
    canvas.drawString(12 * mm, 8 * mm, f"Pick de conferência · Pedido {pedido}" if pedido else "Pick de conferência")
    canvas.drawRightString(A4[0] - 12 * mm, 8 * mm, f"Página {doc.page}")
    canvas.restoreState()


def gerar_pick_pdf(itens, data_agendada):
    """Recebe os itens (um ou varios pedidos) de uma data e devolve o PDF em bytes.

    Cada pedido comeca em uma pagina nova.
    """
    buffer = BytesIO()
    doc = _DocumentoPick(
        buffer,
        pagesize=A4,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=14 * mm,
        title=f"Pick de conferência {_formatar_data(data_agendada)}",
    )
    gerado_em = datetime.now().strftime("%d/%m/%Y %H:%M")

    elementos = []
    pedidos = list(dict.fromkeys(itens["Pedido"].astype(str).str.strip()))
    for posicao, pedido in enumerate(pedidos):
        if posicao:
            elementos.append(PageBreak())
        itens_pedido = itens[itens["Pedido"].astype(str).str.strip() == pedido]
        elementos += _bloco_pedido(pedido, itens_pedido, data_agendada, gerado_em)

    doc.build(elementos)
    return buffer.getvalue()
