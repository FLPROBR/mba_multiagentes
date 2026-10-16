"""
ETAPA 5 -- MCP Server do RH (30 min). Volta aqui na ETAPA 9 (token, regra N8 e auditoria).

Os dados saem de dentro do agente e passam a morar num PROCESSO SEPARADO, que fala MCP. O agente (Etapa 5.3) e os
nós do grafo (Etapa 7, via cliente_mcp.chamar_mcp) só enxergam as tools abaixo: nunca os CSVs.

ESQUELETO: implemente as etapas na ordem (troque cada raise NotImplementedError pelo código da etapa).
  ETAPA 5.1 -- as 5 tools de LEITURA: declare cada uma com @mcp.tool(), escreva a DOCSTRING (é o "schema" que o LLM
               lê) e devolva o resultado da consulta pronta de dados_rh.py. Toda tool devolve UM dict.
  ETAPA 5.2 -- a tool de ESCRITA registrar_decisao, IDEMPOTENTE (protocolo repetido não duplica)
  ETAPA 9.2 -- autorização NO SERVER: token + regra N8 (chefia certa, nunca o próprio servidor) + decisão num enum
  ETAPA 9.3 -- auditoria: toda tentativa de escrita (ALLOW ou DENY) vira uma linha em saidas/auditoria.jsonl

REFERÊNCIAS NAS AULAS
  aula6/desafio2/mcp_unidades.py               MCP Server que lê um CSV                          <- o mais parecido (5.1)
  aula5/exemplos/03_mcp_parametros/server.py   tool com parâmetros opcionais
  aula5/exemplos/05_multiplas_tools/server.py  várias tools no mesmo server, tool de "descoberta"
  aula3/agente_retry3.py                       idempotência (5.2)
  aula5/exemplos/10_seguranca/server_seguro.py token, enum fechado e auditoria NO SERVER        <- o mais parecido (9.2/9.3)

Testar sem agente (MCP Inspector, precisa de Node.js):
    npx @modelcontextprotocol/inspector python etapa05_mcp_rh.py

Pronto quando: o Inspector lista as 6 tools; registrar C1 duas vezes gera um único registro.
"""
import json
import os
from datetime import datetime

from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

from dados_rh import PASTA, SAIDAS, carregar_servidores, diaria, escala_da_equipe, normas, remuneracao, servidor_publico

# O server roda como SUBPROCESSO: ele não herda o ambiente de quem o chamou. Por isso carrega o .env sozinho
# (mesmo cuidado de aula5/exemplos/02_mcp_basico/database.py).
load_dotenv(PASTA / ".env")

mcp = MCPServer("rh-mcp")

ARQUIVO_REGISTROS = SAIDAS / "registros.json"
ARQUIVO_AUDITORIA = SAIDAS / "auditoria.jsonl"
TOKEN_REGISTRO = os.getenv("TOKEN_REGISTRO", "")
DECISOES_VALIDAS = {"deferido", "indeferido", "indeferido_pela_chefia"}
TIPOS_COM_CHEFIA = {"ferias", "diaria"}  # regra N8


def _ler_registros() -> dict:
    """(PRONTO) {protocolo: registro} gravados até agora."""
    if ARQUIVO_REGISTROS.exists():
        return json.loads(ARQUIVO_REGISTROS.read_text(encoding="utf-8"))
    return {}


def _gravar_registros(registros: dict) -> None:
    """(PRONTO)"""
    ARQUIVO_REGISTROS.write_text(json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8")


# ------------------------------------------------------------------ ETAPA 5.1: leitura
@mcp.tool()
def consultar_servidor(matricula: str) -> dict:
    """Consulta o cadastro de UM servidor pela matrícula. Devolve matrícula, nome, cargo, equipe,
    saldo_ferias_dias, abonos_restantes e a matrícula da chefia imediata. NÃO devolve o salário (dado restrito).
    Se a matrícula não existir, devolve um dict com o campo "erro".

    Args:
        matricula: matrícula do servidor, só dígitos (ex.: "1002").
    """
    return servidor_publico(matricula)


@mcp.tool()
def consultar_escala(equipe: str, inicio: str, fim: str) -> dict:
    """Consulta a escala de uma equipe num período e o limite da regra N5 (no máximo 30% da equipe afastada no mesmo
    dia, arredondado para baixo, mínimo 1). Devolve o tamanho da equipe, o limite de afastados e a lista de
    afastamentos (matrícula, início, fim, tipo) que se sobrepõem ao período.

    Args:
        equipe: nome da equipe, como no cadastro (ex.: "Cartório", "Plantão A").
        inicio: primeiro dia do período, no formato AAAA-MM-DD.
        fim: último dia do período, no formato AAAA-MM-DD.
    """
    return escala_da_equipe(equipe, inicio, fim)


@mcp.tool()
def consultar_normas(tema: str) -> dict:
    """Consulta as regras da Norma Interna (N1 a N10) de um tema. Temas existentes: férias, prazos, escala, abono,
    diária, aprovação, saúde e dados. Devolve {"tema": ..., "regras": [{"codigo", "tema", "regra"}, ...]}.

    Args:
        tema: tema das regras (ex.: "férias", "abono", "diária"). Acentos e maiúsculas são ignorados.
    """
    # Um dict (e não a lista direta): uma tool MCP que devolve lista manda cada item como um conteúdo separado,
    # e quem chama não distingue "lista com 1 regra" de "1 dict". Neste server, TODA tool devolve UM dict.
    return {"tema": tema, "regras": normas(tema)}


@mcp.tool()
def tabela_diarias(tipo_destino: str) -> dict:
    """Consulta o valor da diária (regra N7) de um tipo de destino. Devolve a moeda (BRL para capital e interior,
    USD para exterior) e o valor de uma diária completa.

    Args:
        tipo_destino: "capital", "interior" ou "exterior".
    """
    return diaria(tipo_destino)


@mcp.tool()
def consultar_remuneracao(matricula: str) -> dict:
    """[RESTRITA] Consulta o salário-base de um servidor. Dado sensível: só o especialista Financeiro deve usar,
    para calcular o valor da venda de férias (N2: salário-base / 30 por dia vendido). Nunca repita o salário
    em despachos nem em respostas ao servidor.

    Args:
        matricula: matrícula do servidor, só dígitos (ex.: "1002").
    """
    return remuneracao(matricula)


# ------------------------------------------------------------------ ETAPA 5.2 / 9.2 / 9.3: escrita
def _auditar(protocolo: str, decisao_acesso: str, motivo: str, parametros: dict) -> None:
    # ETAPA 9.3 -- acrescente UMA linha JSON em ARQUIVO_AUDITORIA com: quando (datetime.now().isoformat()),
    #   thread_id, quem pediu (aprovador), tool ("registrar_decisao"), protocolo, decisao_acesso ("ALLOW"/"DENY"),
    #   motivo e os parâmetros (SEM o token e SEM o despacho inteiro).
    #   Referência: aula5/exemplos/10_seguranca/server_seguro.py (_registrar_auditoria), aqui em JSON Lines.
    #   Até fazer a 9.3, este pass deixa a escrita funcionar sem auditoria.
    pass


@mcp.tool()
def registrar_decisao(protocolo: str, matricula: str, tipo: str, inicio: str, fim: str, decisao: str,
                      aprovador: str, despacho: str, token: str, thread_id: str = "") -> dict:
    """[ESCRITA -- requer autorização] Registra a decisão de um pedido. É idempotente: se o protocolo já existir,
    não grava de novo e devolve {"sucesso": True, "duplicado": True, "protocolo": ...}.

    Args:
        protocolo: protocolo idempotente do pedido (etapa04_ferramentas.gerar_protocolo).
        matricula: matrícula do servidor que fez o pedido.
        tipo: tipo do pedido: "ferias", "abono" ou "diaria".
        inicio: primeiro dia, AAAA-MM-DD.
        fim: último dia, AAAA-MM-DD.
        decisao: "deferido", "indeferido" ou "indeferido_pela_chefia".
        aprovador: matrícula de quem aprovou (a chefia) ou "sistema" quando a N8 não exige chefia.
        despacho: texto do despacho (sem CPF nem dado de saúde, N10).
        token: token de registro. Sem ele, a gravação é negada.
        thread_id: identificador da execução do grafo (para a auditoria).
    """
    parametros = {"matricula": matricula, "tipo": tipo, "inicio": inicio, "fim": fim, "decisao": decisao,
                  "aprovador": aprovador, "thread_id": thread_id}

    # ETAPA 9.2 -- ANTES de gravar, negue (e audite com DENY) quando:
    #   - token != TOKEN_REGISTRO (ou TOKEN_REGISTRO vazio);
    #   - decisao não está em DECISOES_VALIDAS;
    #   - aprovador == matricula (ninguém aprova o próprio pedido, N8);
    #   - decisao == "deferido" e tipo in TIPOS_COM_CHEFIA e aprovador != chefia do servidor no cadastro.
    #   Devolva {"sucesso": False, "erro": "..."} -- quem nega é o SERVER, não o agente.
    #   Referência: aula5/exemplos/10_seguranca/server_seguro.py (alterar_status_ocorrencia)

    # ETAPA 5.2 -- grave em ARQUIVO_REGISTROS (use _ler_registros/_gravar_registros).
    #   Protocolo já existe -> NÃO grave de novo; devolva {"sucesso": True, "duplicado": True, ...}.
    #   Senão grave {**parametros, "despacho": despacho, "registrado_em": ...} e devolva {"sucesso": True, ...}.
    #   Audite com ALLOW (9.3).
    registros = _ler_registros()
    if protocolo in registros:
        _auditar(protocolo, "ALLOW", "protocolo já registrado (duplicado)", parametros)
        return {"sucesso": True, "duplicado": True, "protocolo": protocolo}
    registros[protocolo] = {**parametros, "protocolo": protocolo, "despacho": despacho,
                            "registrado_em": datetime.now().isoformat(timespec="seconds")}
    _gravar_registros(registros)
    _auditar(protocolo, "ALLOW", "registro gravado", parametros)
    return {"sucesso": True, "protocolo": protocolo}


if __name__ == "__main__":
    mcp.run(transport="stdio")
