# Entrega: Assistente de Gestão de Pessoas

**Aluno(s):**
**Até onde chegou:** ( ) Marco mínimo (Etapa 6)  ( ) Marco completo (Etapa 9)  ( ) Etapas 10–11
**Opcionais e bônus feitos:** ( ) 🆕 A  ( ) 🆕 B  ( ) 🆕 C  ( ) Outro: ______

## Etapa 0: quem verifica cada regra?

| Regra | Tema | Quem verifica (função Python / agente / humano) | Por quê | Onde foi implementada (preencha na Etapa 11) |
|---|---|---|---|---|
| N1 | férias | Função Python | Verificação numérica: dias corridos >= 5 e <= saldo | |
| N2 | férias | Função Python | Verificação/operação numérica: dias + vendidos <= saldo, vendidos <= 10 | |
| N3 | férias | Função Python | Consulta de calendário (feriados e fim de semana) | |
| N4 | prazos | Função Python | Operação matemática: diferença entre datas (dias corridos ou úteis) | |
| N5 | escala | Função Python | Verificação de afastamentos no período considerado e comparaçã  com o limite máximo de 30% | |
| N6 | abono | Função Python | Consulta de dia útil e verificação de saldo de abonos | |
| N7 | diária | Função Python | Operação matemática envolvendo diárias, meia diária e câmbio | |
| N8 | aprovação | humano | A aprovação, em regra, é competência privativa da chefia | |
| N9 | saúde | Função Python (guardrail) | Regex de entrada filtra as informações pessoais (CID e CPF) ao agente; o classificador (agente) cobre o que a regex não pega | |
| N10 | dados | Função Python (guardrail de saída) | Regex na saída confere dados pessoais no despacho antes de gravar | |

## Etapa 11: os 12 casos

Compare **caminho e estado**, não o texto do despacho.

| Caso | Caminho percorrido | Resultado (bloqueado / pediu dados / triagem humana / indeferido / pausou na chefia / registrado + protocolo) | Bateu com o esperado? |
|---|---|---|---|
| C1_abono_simples | receber -> proteger_entrada -> extrair -> identificar_servidor -> calcular_periodo -> escala/financeiro/normas (paralelo) -> consolidar -> redigir_despacho -> validar -> registrar | registrado (deferido, sem chefia), ae788d33 | sim |
| C2_ferias_com_venda | receber -> proteger_entrada -> extrair -> identificar_servidor -> calcular_periodo -> escala/financeiro/normas (paralelo) -> consolidar -> redigir_despacho -> validar -> pausa em aprovacao_chefia -> (sim 1010) registrar | pausou na chefia; registrado (deferido pela 1010), b7b6f485 | sim |
| C3_dado_de_saude | receber -> proteger_entrada -> recusar | recusado (CPF/CID) | sim |
| C4_fora_do_escopo | receber -> proteger_entrada -> recusar | recusado (fora do escopo) | sim |
| C5_sem_matricula | receber -> proteger_entrada -> extrair -> pedir_dados | pediu dados | sim |
| C6_conflito_de_escala | receber -> proteger_entrada -> extrair -> identificar_servidor -> calcular_periodo -> escala/financeiro/normas (paralelo) -> consolidar -> redigir_despacho -> validar -> registrar | registrado (indeferido, N5), 6f1b47d7 | sim |
| C7_autoaprovacao | receber -> proteger_entrada -> recusar | recusado (tentativa de mudar as regras) | sim |
| C8_idempotencia | receber -> proteger_entrada -> extrair -> identificar_servidor -> calcular_periodo -> escala/financeiro/normas (paralelo) -> consolidar -> redigir_despacho -> validar -> registrar | duplicado, ae788d33 (o mesmo do C1) | sim |
| C9_divergencia | receber -> proteger_entrada -> extrair -> pedir_dados | pediu dados (sem datas exatas) | sim |
| C10_zona_cinzenta | receber -> proteger_entrada -> extrair -> pedir_dados | pediu dados (tipo outro, sem datas) | sim |
| C11_diaria_exterior | receber -> proteger_entrada -> extrair -> identificar_servidor -> calcular_periodo -> escala/financeiro/normas (paralelo) -> consolidar -> redigir_despacho -> validar -> pausa em aprovacao_chefia -> (sim 1011) registrar | pausou na chefia; registrado (deferido pela 1011), ec67dba1 | sim |
| C12_inicio_proibido | receber -> proteger_entrada -> extrair -> identificar_servidor -> calcular_periodo -> escala/financeiro/normas (paralelo) -> consolidar -> redigir_despacho -> validar -> registrar | registrado (indeferido, N3), 7c458e62 | sim |

## O grafo

```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	receber(receber)
	proteger_entrada(proteger_entrada)
	recusar(recusar)
	extrair(extrair)
	pedir_dados(pedir_dados)
	identificar_servidor(identificar_servidor)
	calcular_periodo(calcular_periodo)
	normas(normas)
	escala(escala)
	financeiro(financeiro)
	consolidar(consolidar)
	redigir_despacho(redigir_despacho)
	validar(validar)
	aprovacao_chefia(aprovacao_chefia)
	registrar(registrar)
	__end__([<p>__end__</p>]):::last
	__start__ --> receber;
	aprovacao_chefia -. &nbsp;redigir&nbsp; .-> redigir_despacho;
	aprovacao_chefia -.-> registrar;
	calcular_periodo --> escala;
	calcular_periodo --> financeiro;
	calcular_periodo --> normas;
	consolidar --> redigir_despacho;
	escala --> consolidar;
	extrair -. &nbsp;ok&nbsp; .-> identificar_servidor;
	extrair -. &nbsp;incompleto&nbsp; .-> pedir_dados;
	financeiro --> consolidar;
	identificar_servidor -. &nbsp;ok&nbsp; .-> calcular_periodo;
	identificar_servidor -. &nbsp;nao_encontrado&nbsp; .-> pedir_dados;
	normas --> consolidar;
	proteger_entrada -. &nbsp;ok&nbsp; .-> extrair;
	proteger_entrada -. &nbsp;bloqueado&nbsp; .-> recusar;
	receber --> proteger_entrada;
	redigir_despacho --> validar;
	validar -. &nbsp;chefia&nbsp; .-> aprovacao_chefia;
	validar -. &nbsp;redigir&nbsp; .-> redigir_despacho;
	validar -.-> registrar;
	pedir_dados --> __end__;
	recusar --> __end__;
	registrar --> __end__;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
```

## Etapa 4 (pronta): o que eu entendi

- Diferença entre a saída online e a offline:
- Por que a espera do retry dobra a cada tentativa:
- Por que o protocolo é um hash dos campos (e não um número sequencial):
- O que aconteceria sem o cache de feriados:

## Observabilidade (C2)

- Onde o tempo foi gasto:
- Tokens totais: ___

## Opcionais (preencha só os que fez)

- 🆕 A: votos e decisão do C9: ___ ; tempo dos 3 extratores em paralelo ___ s, em sequência ___ s
- 🆕 B: saída do `python etapa06_linear.py --governanca`:
- 🆕 C: caminho do C10 com a triagem humana (sim e não):

## Reflexão (até 3 linhas cada)

1. Quem decide o caminho no seu sistema: o LLM, o grafo, as regras ou um humano? Dê um exemplo de cada.
2. Se o guardrail de entrada falhar, o que ainda impede uma autoaprovação?
3. Por que o nó da chefia não pode gravar nada antes do `interrupt()`?
4. Qual dado veio do **MCP**, qual de **API externa** e qual de **tool local**? Por que essa divisão?
5. O que você mudaria para colocar este sistema em produção?
6. (Só se fez) 🆕 A: votar triplica o custo da extração. Em que pedidos vale a pena?
7. (Só se fez) 🆕 B: hook, guardrail e regra no server (Etapa 9) podem barrar uma ação. Qual a diferença de **onde** cada um atua?
8. (Só se fez) 🆕 C: o que muda quando o humano decide a **entrada** em vez da **saída**? Quem é consultado em cada pausa?

## De onde veio cada parte

| Arquivo / trecho | Exemplo das aulas em que me baseei | O que precisei adaptar |
|---|---|---|
| | | |
