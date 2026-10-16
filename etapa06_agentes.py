"""
ETAPA 6 -- Os especialistas, cada um com UMA responsabilidade e SÓ as tools de que precisa.

ESQUELETO:
  ETAPA 6.1 -- criar_normas(), criar_escala(), criar_financeiro(), criar_redator()
  ETAPA 6.2 -- criar_coordenador(): usa Normas, Escala e Financeiro como TOOLS (as_tool)

As tools abaixo (PRONTAS) só repassam a chamada ao MCP Server do RH (cliente_mcp.chamar_mcp_async). Dar a cada agente
só as tools dele é o PRIVILÉGIO MÍNIMO (Etapa 9.1); o hook do 🆕 B (etapa10_governanca.py) confere isso em tempo de execução.

REFERÊNCIAS NAS AULAS
  aula4/ex03_agente_as_tool.py                         Coordenador que chama especialistas como tools    <- o mais parecido
  aula2/agente_handoff2.py                             as_tool com tool_name e tool_description
  aula4/ex02_handoff_roteamento.py                     handoff: compare (quem responde no fim?)
  aula7/exemplos/02_agentes_especializados/main.py     uma responsabilidade por agente
  aula7/agentes.py                                     ModelSettings(temperature=0) para respostas mais estáveis
  aula8/exemplos/06_excessive_agency/1_codigo_pronto/main.py   o problema de dar tools DEMAIS a um agente
"""
import json

from agents import Agent, ModelSettings, RunHooks, function_tool

from etapa05_cliente_mcp import chamar_mcp_async
from etapa04_ferramentas import cotacao_usd_brl

CONFIG = ModelSettings(temperature=0)


# ------------------------------------------------------------------ tools (PRONTAS)
@function_tool
async def consultar_normas(tema: str) -> str:
    """Regras da norma interna sobre um tema: férias, prazos, escala, abono, diária, aprovação, saúde ou dados."""
    return json.dumps(await chamar_mcp_async("consultar_normas", {"tema": tema}), ensure_ascii=False)


@function_tool
async def consultar_escala(equipe: str, inicio: str, fim: str) -> str:
    """Afastamentos da equipe que se sobrepõem ao período (AAAA-MM-DD) e o limite de afastados da regra N5."""
    return json.dumps(await chamar_mcp_async("consultar_escala", {"equipe": equipe, "inicio": inicio, "fim": fim}),
                      ensure_ascii=False)


@function_tool
async def tabela_diarias(tipo_destino: str) -> str:
    """Moeda e valor da diária para o tipo de destino: capital, interior ou exterior."""
    return json.dumps(await chamar_mcp_async("tabela_diarias", {"tipo_destino": tipo_destino}), ensure_ascii=False)


@function_tool
async def consultar_remuneracao(matricula: str) -> str:
    """[RESTRITA] Salário-base de um servidor. Só para calcular a venda de férias (N2)."""
    print(f"[tool] consultar_remuneracao({matricula}) EXECUTOU")  # o 🆕 B prova que, barrada, ela NÃO executa
    return json.dumps(await chamar_mcp_async("consultar_remuneracao", {"matricula": matricula}), ensure_ascii=False)


@function_tool
def cotacao_dolar() -> str:
    """Cotação atual do dólar em reais (USD->BRL). Devolve 'indisponível' se a API falhar: nunca invente o câmbio."""
    cotacao = cotacao_usd_brl()
    return f"{cotacao:.4f}" if cotacao else "indisponível"


# ------------------------------------------------------------------ ETAPA 6.1: especialistas
def criar_normas() -> Agent:
    return Agent(
        name="Normas",
        instructions=(
            "Você é o especialista em NORMAS do RH. Sua única responsabilidade: dizer QUAIS regras da norma interna "
            "(N1 a N10) se aplicam ao pedido recebido e explicá-las em linguagem simples. Use a tool consultar_normas "
            "com o tema do pedido (férias, abono ou diária; e prazos/aprovação quando fizer sentido). "
            "Você recebe também as violações objetivas já calculadas pelo sistema: não refaça as contas nem discorde "
            "delas, apenas explique cada uma. Liste as regras CUMPRIDAS e as VIOLADAS. "
            "Não calcule valores, não consulte a escala e não cite CPF nem dados de saúde."
        ),
        tools=[consultar_normas],
        model_settings=CONFIG,
    )


def criar_escala() -> Agent:
    return Agent(
        name="Escala",
        instructions=(
            "Você é o especialista em ESCALA da equipe. Use a tool consultar_escala com a equipe e o período do pedido "
            "(datas AAAA-MM-DD) e confira a regra N5: no máximo o limite_afastados da equipe pode estar afastado no "
            "mesmo dia (sem contar o próprio servidor). Diga se há conflito e com quem (matrícula e datas). "
            "Se houver conflito, SUGIRA outro período com o MESMO número de dias, começando no primeiro dia depois do "
            "fim do afastamento que causa o conflito, numa segunda, terça ou quarta-feira que não seja véspera nem "
            "antevéspera de feriado (regra N3). Não calcule valores e não cite dados de saúde."
        ),
        tools=[consultar_escala],
        model_settings=CONFIG,
    )


def criar_financeiro() -> Agent:
    return Agent(
        name="Financeiro",
        instructions=(
            "Você é o especialista FINANCEIRO. Calcule SEMPRE mostrando a conta. "
            "Venda de férias (N2): use consultar_remuneracao para obter o salario_base e calcule "
            "dias_vendidos x salario_base / 30. "
            "Diárias (N7): use tabela_diarias com o tipo de destino. Conte uma diária por dia com pernoite e meia diária "
            "no dia do retorno (ex.: de 08 a 11 = 3 pernoites + 0,5 = 3,5 diárias). No exterior o valor é em USD: use "
            "cotacao_dolar para converter em reais; se a cotação estiver indisponível, diga que o valor em reais está "
            "'a calcular' e informe só o valor em USD. Nunca invente o câmbio. "
            "Se o pedido não envolver dinheiro (abono simples, férias sem venda), diga que não há valor a calcular e "
            "não consulte o salário. Você é o único agente que vê o salário: use-o só na conta e não o repita fora dela."
        ),
        tools=[tabela_diarias, consultar_remuneracao, cotacao_dolar],
        model_settings=CONFIG,
    )


def criar_redator() -> Agent:
    return Agent(
        name="Redator",
        instructions=(
            "Você redige o DESPACHO oficial (deferimento ou indeferimento) de um pedido de servidor, em português formal "
            "e objetivo, em um ou dois parágrafos. Use SOMENTE os fatos recebidos: matrícula, período, decisão, regras "
            "citadas, valores e, no indeferimento, a sugestão de novas datas. O despacho DEVE citar a matrícula, o "
            "período (datas) e a decisão, usando a palavra 'deferido' ou 'indeferido' (ex.: 'Pedido deferido'). "
            "Não invente fatos nem valores. "
            "NUNCA escreva CPF, CID ou qualquer informação de saúde (regra N10). "
            "Se receber um feedback (da validação ou da chefia), corrija o despacho conforme o feedback."
        ),
        model_settings=CONFIG,
    )


# ------------------------------------------------------------------ ETAPA 6.2: coordenador
def criar_coordenador(hooks: RunHooks | None = None, tools_extras: list | None = None) -> Agent:
    return Agent(
        name="Coordenador",
        instructions=(
            "Você coordena a análise de um pedido de servidor (férias, abono ou diária). Você tem três especialistas, "
            "como tools: parecer_normas (regras aplicáveis), parecer_escala (conflito de escala da equipe) e "
            "parecer_financeiro (valores de venda de férias ou diárias). Decida QUAIS consultar, só os necessários: "
            "abono simples não precisa do Financeiro; diária não precisa da Escala. "
            "Ao chamar cada especialista, repasse os fatos do pedido (matrícula, equipe, tipo, datas, dias vendidos, "
            "tipo e cidade de destino) e as violações objetivas. "
            "Depois, junte os pareceres num parecer único e curto, mantendo as contas e as sugestões de datas. "
            "Não decida a aprovação: isso é da norma e da chefia. Não cite CPF nem dados de saúde."
        ),
        tools=[
            criar_normas().as_tool(
                tool_name="parecer_normas",
                tool_description="Parecer sobre as regras da norma que se aplicam ao pedido e se foram cumpridas.",
                hooks=hooks, failure_error_function=None),
            criar_escala().as_tool(
                tool_name="parecer_escala",
                tool_description="Parecer sobre o conflito de escala (N5) da equipe e sugestão de outro período.",
                hooks=hooks, failure_error_function=None),
            criar_financeiro().as_tool(
                tool_name="parecer_financeiro",
                tool_description="Cálculo do valor da venda de férias (N2) ou das diárias (N7), com a conta.",
                hooks=hooks, failure_error_function=None),
            *(tools_extras or []),
        ],
        model_settings=CONFIG,
    )
