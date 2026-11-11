"""Atualiza a aba "Pedido de compra" da planilha da agenda com os dados do ERP Millennium.

Traz os pedidos de compra ainda nao recebidos (Efetuado = False, aprovados ou nao) com
entrega a partir de DIAS_ATRASO dias atras, uma linha por item, nas mesmas colunas do
relatorio que era exportado manualmente.

Conexao com o ERP (mesma regra da skill erp-millennium-conexao):
  - Gateway: se ERP_GATEWAY_URL existir, usa <url>/api com a chave ERP_GATEWAY_KEY.
    Nao depende do ERP aberto; e o modo para rodar agendado.
  - Direto: sem ERP_GATEWAY_URL, usa a sessao do ERP deste PC (token_atual.json em
    ERP_MILLENNIUM_RAIZ, padrao C:\\Projetos\\erp_millennium). Se a sessao expirar, tenta
    recapturar o token do ERP aberto em modo debug.

Credenciais do Google: .streamlit/secrets.toml (gcp_service_account e spreadsheet_id).

Uso:
  python atualizar_pedidos_compra.py            # atualiza a planilha
  python atualizar_pedidos_compra.py --simular  # so mostra o que gravaria
"""

import argparse
import json
import os
import subprocess
import sys
import tomllib
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import gspread
import requests
from google.oauth2.service_account import Credentials


PASTA = Path(__file__).resolve().parent
ABA = "Pedido de compra"
DIAS_ATRASO = 30

ERP_HOST = "http://179.124.192.37:6017"
ERP_RAIZ = Path(os.environ.get("ERP_MILLENNIUM_RAIZ") or r"C:\Projetos\erp_millennium")

CABECALHO = [
    "Empresa", "Numero do Pedido", "Data Emissao", "Fornecedor", "Forcededor",
    "Forma de Pagamento", "Observacao", "Data Entrega", "Codigo", "Descricao",
    "Cor", "Desc Cor", "UN", "Qtde", "Vlr. Unit", "Total",
]

SELECT = ",".join([
    "pedidocompra.filial.gerador.nome as empresa",
    "pedidocompra.pedido_compra.COD_PEDIDOC as pedido",
    "pedidocompra.data_emissao as emissao",
    "pedidocompra.fornecedor.gerador.cod_nome_fornecedor as fornecedor",
    "pedidocompra.condicao_pgto.descricao as pagamento",
    "pedidocompra.obs as obs",
    "pedidocompra.data_entrega as entrega",
    "produto.produto.cod_produto as codigo",
    "produto.produto.descricao1 as descricao",
    "cor.cod_cor as cor",
    "cor.descricao as desc_cor",
    "produto.produto.unidade_compra as un",
    "pedc.quantidade as qtde",
    "pedc.valor_unitario as vlr_unit",
    "pedc.valor as total",
])


class SessaoExpirada(RuntimeError):
    pass


# ==================================================
# ERP
# ==================================================

def _conexao_erp():
    gateway = (os.environ.get("ERP_GATEWAY_URL") or "").strip().rstrip("/")
    if gateway:
        chave = (os.environ.get("ERP_GATEWAY_KEY") or "").strip()
        return f"{gateway}/api", ({"x-api-key": chave} if chave else {}), "gateway"

    token = ERP_RAIZ / "token_atual.json"
    if not token.is_file():
        raise SessaoExpirada(f"Não achei {token}. Abra o ERP em modo debug e capture o token.")
    dados = json.loads(token.read_text(encoding="utf-8"))
    return f"{ERP_HOST}/api", {"WTS-Session": dados["WTS-Session"], "WTS-Token": dados["WTS-Token"]}, "direto"


def _consultar(select, filtro):
    base, credencial, _ = _conexao_erp()
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "X-DateFormat": "ISOTZ",
        "X-HTTP-Method": "GET",
        "X-IdentifierCase": "upper",
        **credencial,
    }
    corpo = {"with": "", "select": select, "filter": filtro, "ignoreUserRestriction": False}
    resposta = requests.post(
        f"{base}/millenium?$format=json;odata.metadata=full",
        data=json.dumps(corpo), headers=headers, timeout=600,
    )
    if resposta.status_code in (401, 403):
        raise SessaoExpirada(f"{resposta.status_code}: o ERP recusou a credencial.")
    if not resposta.ok:
        raise RuntimeError(f"ERP respondeu {resposta.status_code}: {resposta.text[:500]}")
    return resposta.json().get("value", [])


def _recapturar_token():
    script = ERP_RAIZ / "erp_conexao" / "_get_token.py"
    if not script.is_file():
        return False
    resultado = subprocess.run(
        [sys.executable, str(script)], cwd=ERP_RAIZ, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=180,
    )
    return "Salvo em" in (resultado.stdout + resultado.stderr)


def consultar_erp(select, filtro):
    try:
        return _consultar(select, filtro)
    except SessaoExpirada:
        if _conexao_erp()[2] != "direto" or not _recapturar_token():
            raise
        return _consultar(select, filtro)


# ==================================================
# FORMATACAO (igual ao relatorio exportado)
# ==================================================

def _data(valor):
    if not valor:
        return ""
    # A API devolve meia-noite de Brasilia em UTC (ex.: 2026-12-14T03:00:00.000Z).
    utc = datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
    return utc.astimezone(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y")


def _numero(valor, casas=4):
    if valor is None or valor == "":
        return ""
    numero = round(float(valor), casas)
    if numero.is_integer():
        return str(int(numero))
    return f"{numero:.{casas}f}".rstrip("0").rstrip(".").replace(".", ",")


def _sem_zeros(texto):
    texto = str(texto or "").strip()
    return texto.lstrip("0") or ("0" if texto else "")


def _texto(valor):
    return " ".join(str(valor or "").split())


def montar_linhas(registros):
    linhas = []
    for r in registros:
        cod_nome = str(r.get("FORNECEDOR") or "")
        cod_fornecedor, _, nome_fornecedor = cod_nome.partition(" - ")
        linhas.append([
            _texto(r.get("EMPRESA")),
            _texto(r.get("PEDIDO")),
            _data(r.get("EMISSAO")),
            _sem_zeros(cod_fornecedor),
            _texto(nome_fornecedor or cod_nome),
            _texto(r.get("PAGAMENTO")),
            _texto(r.get("OBS")),
            _data(r.get("ENTREGA")),
            _texto(r.get("CODIGO")),
            _texto(r.get("DESCRICAO")),
            _sem_zeros(r.get("COR")),
            _texto(r.get("DESC_COR")),
            _texto(r.get("UN")),
            _numero(r.get("QTDE")),
            _numero(r.get("VLR_UNIT")),
            _numero(r.get("TOTAL")),
        ])

    def chave(linha):
        entrega = datetime.strptime(linha[7], "%d/%m/%Y") if linha[7] else datetime.max
        return entrega, linha[1], linha[8]

    return sorted(linhas, key=chave)


# ==================================================
# GOOGLE SHEETS
# ==================================================

def abrir_aba():
    segredos = tomllib.loads((PASTA / ".streamlit" / "secrets.toml").read_text(encoding="utf-8"))
    credenciais = Credentials.from_service_account_info(
        segredos["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets"],
    )
    planilha = gspread.authorize(credenciais).open_by_key(segredos["spreadsheet_id"])
    try:
        return planilha.worksheet(ABA)
    except gspread.WorksheetNotFound:
        return planilha.add_worksheet(ABA, rows=1000, cols=len(CABECALHO))


def gravar(aba, linhas):
    valores = [CABECALHO] + linhas
    total_linhas = len(valores)
    if aba.row_count < total_linhas:
        aba.add_rows(total_linhas - aba.row_count)
    # Sobrescreve primeiro e so depois limpa o que sobrou, para a aba nunca ficar vazia.
    aba.update(valores, "A1", value_input_option="RAW")
    if aba.row_count > total_linhas:
        aba.batch_clear([f"A{total_linhas + 1}:{gspread.utils.rowcol_to_a1(aba.row_count, aba.col_count)}"])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--simular", action="store_true", help="não grava na planilha")
    args = parser.parse_args()

    inicio = (date.today() - timedelta(days=DIAS_ATRASO)).isoformat()
    filtro = f"pedidocompra.pedido_compra.Efetuado = False and pedidocompra.data_entrega >= '{inicio}'"

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    modo = _conexao_erp()[2] if (os.environ.get("ERP_GATEWAY_URL") or (ERP_RAIZ / "token_atual.json").is_file()) else "?"
    print(f"[{agora}] Consultando o ERP ({modo}) - entregas a partir de {inicio}...")
    linhas = montar_linhas(consultar_erp(SELECT, filtro))
    pedidos = len({linha[1] for linha in linhas})
    print(f"{len(linhas)} linha(s) de {pedidos} pedido(s).")

    if not linhas:
        # Resposta vazia quase sempre e falha de consulta: nao apaga a aba.
        raise SystemExit("Nenhuma linha retornada pelo ERP. A planilha não foi alterada.")

    if args.simular:
        for linha in linhas[:5]:
            print(" | ".join(linha))
        print("Simulação: nada gravado.")
        return

    gravar(abrir_aba(), linhas)
    print(f"Aba '{ABA}' atualizada.")


if __name__ == "__main__":
    try:
        main()
    except SessaoExpirada as exc:
        raise SystemExit(f"ERRO de acesso ao ERP: {exc}")
