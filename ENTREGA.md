# Entrega: Assistente de Gestão de Pessoas

**Aluno(s):**
**Até onde chegou:** ( ) Marco mínimo (Etapa 6)  ( ) Marco completo (Etapa 9)  ( ) Etapas 10–11
**Opcionais e bônus feitos:** ( ) 🆕 A  ( ) 🆕 B  ( ) 🆕 C  ( ) Outro: ______

## Etapa 0: quem verifica cada regra?

| Regra | Tema | Quem verifica (função Python / agente / humano) | Por quê | Onde foi implementada (preencha na Etapa 11) |
|---|---|---|---|---|
| N1 | férias | Função Python | Conta de saldo, nº de períodos (até 3) e mínimo de 5 dias: regra objetiva, sem interpretação. | |
| N2 | férias | Função Python (limite e soma); agente Financeiro (valor) | Limite de 10 dias e dias gozados + vendidos ≤ saldo são aritmética. O valor (salário/30) o Financeiro calcula com as tools. | |
| N3 | férias | Função Python | Depende só de calendário e feriados (`inicio_permitido`). | |
| N4 | prazos | Função Python | Antecedência é contagem de dias corridos e úteis a partir da data do pedido. | |
| N5 | escala | Função Python (decide); agente Escala (explica e sugere outro período) | O limite de 30% (mín. 1) é conta; sugerir novas datas exige raciocínio. | |
| N6 | abono | Função Python | 1 dia útil, `abonos_restantes`, fim de semana e feriado: tudo objetivo. | |
| N7 | diária | Agente Financeiro | Combina tabela de diárias, pernoite/meia diária e câmbio do dia, interpretando o período do pedido. | |
| N8 | aprovação | Função Python (se precisa de chefia); humano (aprovar) | Exigir chefia é regra por tipo de pedido; aprovar é decisão da chefia imediata, e ninguém aprova o próprio pedido. | |
| N9 | saúde | Função Python (regex CPF/CID) + agente classificador | Dado sensível é padrão fixo (regex, sem LLM); reconhecer um pedido de licença médica exige interpretar o texto. | |
| N10 | dados | Função Python | Despacho sem CPF/CID é filtro objetivo (guardrail de saída); o Redator só escreve com os fatos recebidos. | |

## Etapa 11: os 12 casos

Compare **caminho e estado**, não o texto do despacho.

| Caso | Caminho percorrido | Resultado (bloqueado / pediu dados / triagem humana / indeferido / pausou na chefia / registrado + protocolo) | Bateu com o esperado? |
|---|---|---|---|
| C1_abono_simples | | | |
| C2_ferias_com_venda | | | |
| C3_dado_de_saude | | | |
| C4_fora_do_escopo | | | |
| C5_sem_matricula | | | |
| C6_conflito_de_escala | | | |
| C7_autoaprovacao | | | |
| C8_idempotencia | | | |
| C9_divergencia | | | |
| C10_zona_cinzenta | | | |
| C11_diaria_exterior | | | |
| C12_inicio_proibido | | | |

## O grafo

```mermaid
%% cole aqui a saída de: python etapa07_grafo.py --mermaid
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

