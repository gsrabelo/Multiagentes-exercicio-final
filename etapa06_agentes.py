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
    # ETAPA 6.1 -- Agent(name="Normas", instructions=..., tools=[consultar_normas], model_settings=CONFIG)
    #   Responsabilidade: dizer QUAIS regras se aplicam ao pedido e explicá-las em linguagem simples.
    #   NÃO calcula valores, NÃO consulta a escala. Recebe também as violações objetivas (etapa06_regras.py) para explicá-las.
    return Agent(
        name="Normas",
        instructions=(
            "Você é o especialista em Normas de gestão de pessoas. Recebe um pedido (férias, abono ou diária) e as "
            "violações objetivas já calculadas pelo sistema. Consulte a ferramenta consultar_normas para os temas que "
            "se aplicam ao pedido e diga QUAIS regras se aplicam, citando o código (N1..N10), em linguagem simples. "
            "Se receber violações objetivas, explique cada uma com base no texto da regra. Se NÃO receber a lista de "
            "violações, não conclua se o pedido viola ou não alguma regra: quem decide isso é o sistema. Não calcule "
            "valores e não confira a escala: isso é de outros especialistas. Responda em português, em poucas linhas."
        ),
        tools=[consultar_normas],
        model_settings=CONFIG,
    )


def criar_escala() -> Agent:
    # ETAPA 6.1 -- tools=[consultar_escala]. Confere a N5 e, se houver conflito, SUGERE outro período
    #   (com o mesmo número de dias, começando num dia permitido).
    return Agent(
        name="Escala",
        instructions=(
            "Você é o especialista em Escala. Use consultar_escala com a equipe e o período do pedido (AAAA-MM-DD) e "
            "confira a regra N5: no mesmo dia, no máximo `limite_afastados` servidores da equipe afastados. Ignore "
            "afastamentos do próprio servidor do pedido. Se houver conflito, diga com quem e em que dias, e SUGIRA "
            "outro período com o mesmo número de dias corridos, começando depois do fim do afastamento que conflita, "
            "numa segunda, terça ou quarta-feira que não seja véspera nem antevéspera de feriado (N3). Se receber um "
            "PERÍODO SUGERIDO já calculado pelo sistema, use exatamente esse (não calcule outro). "
            "Responda em português, em poucas linhas."
        ),
        tools=[consultar_escala],
        model_settings=CONFIG,
    )


def criar_financeiro() -> Agent:
    # ETAPA 6.1 -- tools=[tabela_diarias, consultar_remuneracao, cotacao_dolar].
    #   Venda de férias (N2): dias_vendidos x salario_base / 30. Diárias (N7): uma por pernoite + meia no retorno;
    #   no exterior, em USD convertido pela cotação. Mostre a conta. Câmbio indisponível -> "a calcular".
    #   É o ÚNICO agente que vê o salário.
    return Agent(
        name="Financeiro",
        instructions=(
            "Você é o especialista Financeiro e o ÚNICO que pode ver o salário. Calcule só o que o pedido envolve e "
            "mostre a conta:\n"
            "- Venda de férias (N2), quando dias_vendidos > 0: consulte consultar_remuneracao e calcule "
            "dias_vendidos x salario_base / 30, em reais com duas casas.\n"
            "- Diária (N7): uma diária por dia com pernoite e meia diária no dia do retorno (ex.: de 08 a 11 são 3 "
            "pernoites + meia = 3,5 diárias). Consulte tabela_diarias com o tipo de destino. No exterior o valor é "
            "em USD: converta com cotacao_dolar; se ela devolver 'indisponível', escreva o total em USD e 'valor em "
            "reais: a calcular'. Nunca invente câmbio.\n"
            "Não informe o salário-base no parecer, só o valor calculado. Responda em português, em poucas linhas."
        ),
        tools=[tabela_diarias, consultar_remuneracao, cotacao_dolar],
        model_settings=CONFIG,
    )


def criar_redator() -> Agent:
    # ETAPA 6.1 -- sem tools. Escreve o DESPACHO (deferimento ou indeferimento) usando SÓ os fatos recebidos:
    #   matrícula, período, decisão, regras citadas, valores e, no indeferimento, a sugestão de datas.
    #   Nunca escreve CPF nem dado de saúde (N10). Se receber um feedback (da validação ou da chefia), corrige.
    return Agent(
        name="Redator",
        instructions=(
            "Você redige o DESPACHO do RH sobre um pedido, usando SÓ os fatos recebidos: matrícula, tipo, período, "
            "decisão, regras citadas, valores e, no indeferimento, o motivo e a sugestão de datas. Comece por "
            "'Defiro' ou 'Indefiro', conforme a decisão recebida (não a mude), e escreva também a palavra 'deferido' ou "
            "'indeferido' (ex.: 'Pedido deferido.'). Cite a matrícula e a data de início. Texto formal, em um ou dois "
            "parágrafos curtos, datas SEMPRE no formato DD/MM/AAAA (nunca por extenso). No indeferimento, use só a "
            "sugestão de datas recebida, sem inventar outra. Nunca escreva CPF, CID nem informação de saúde (N10), "
            "nem o salário-base. Se receber um feedback (da validação ou da chefia), reescreva corrigindo o que foi "
            "apontado. Devolva só o texto do despacho."
        ),
        model_settings=CONFIG,
    )


# ------------------------------------------------------------------ ETAPA 6.2: coordenador
def criar_coordenador(hooks: RunHooks | None = None, tools_extras: list | None = None) -> Agent:
    # ETAPA 6.2 -- Agent(name="Coordenador", instructions=..., tools=[
    #       criar_normas().as_tool(tool_name="parecer_normas", tool_description=..., hooks=hooks,
    #                              failure_error_function=None),
    #       criar_escala().as_tool(tool_name="parecer_escala", ..., hooks=hooks, failure_error_function=None),
    #       criar_financeiro().as_tool(tool_name="parecer_financeiro", ..., hooks=hooks, failure_error_function=None),
    #       *(tools_extras or [])])
    #   O Coordenador decide QUAIS especialistas consultar (abono não precisa do Financeiro) e junta os pareceres.
    #   hooks=hooks nas as_tool faz o hook do 🆕 B enxergar também as tools DENTRO de cada especialista.
    #   failure_error_function=None: sem isso, um erro dentro do especialista (inclusive o bloqueio do 🆕 B) vira só
    #   um texto de erro para o Coordenador, que segue em frente. Com None, o erro interrompe a execução.
    #   tools_extras serve só para o teste do 🆕 B (dar de propósito consultar_remuneracao ao Coordenador).
    #   Referência: aula4/ex03_agente_as_tool.py
    return Agent(
        name="Coordenador",
        instructions=(
            "Você coordena a análise de um pedido ao RH e consulta especialistas por meio das suas ferramentas. "
            "Escolha QUAIS consultar pelo campo `tipo` do pedido, exatamente assim:\n"
            "- tipo 'abono': parecer_normas e parecer_escala;\n"
            "- tipo 'ferias' com dias_vendidos = 0: parecer_normas e parecer_escala;\n"
            "- tipo 'ferias' com dias_vendidos > 0: parecer_normas, parecer_escala e parecer_financeiro;\n"
            "- tipo 'diaria': parecer_normas e parecer_financeiro (OBRIGATÓRIO: é ele que calcula as diárias); "
            "a viagem a serviço não usa a escala.\n"
            "Mande a cada especialista os dados de que ele precisa (matrícula, equipe, tipo, datas AAAA-MM-DD, dias "
            "vendidos, tipo de destino, violações). Depois junte os pareceres num parecer final curto, com uma linha "
            "por especialista consultado. A decisão segue as violações objetivas: com violação, indeferimento "
            "(inclua a sugestão de datas da Escala, se houver); sem violação, o pedido é deferível. Não decida "
            "contra as violações objetivas."
        ),
        tools=[
            criar_normas().as_tool(
                tool_name="parecer_normas",
                tool_description="Parecer do especialista em Normas: quais regras se aplicam ao pedido e explicação "
                                 "das violações objetivas.",
                hooks=hooks, failure_error_function=None),
            criar_escala().as_tool(
                tool_name="parecer_escala",
                tool_description="Parecer do especialista em Escala: confere a regra N5 na equipe e, se houver "
                                 "conflito, sugere outro período.",
                hooks=hooks, failure_error_function=None),
            criar_financeiro().as_tool(
                tool_name="parecer_financeiro",
                tool_description="Parecer do especialista Financeiro: valor da venda de férias (N2) ou das diárias "
                                 "(N7), com a conta.",
                hooks=hooks, failure_error_function=None),
            *(tools_extras or []),
        ],
        model_settings=CONFIG,
    )
