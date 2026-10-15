# Rascunho das respostas da ficha (Aula 10)

Arquivo de trabalho: reúne as saídas e respostas de cada etapa para copiar à ficha .docx no fim.

## Etapa 0
Saída de `python dados_rh.py` (primeira linha):
```
9 servidores; 3 afastamentos; 13 feriados locais; 10 regras
```
Tabela N1–N10: ver `ENTREGA.md`.
Ambiente: Python 3.13.15, provedor OpenRouter (`openrouter:openai/gpt-6-luna`); `verificar_ambiente.py` -> "tudo certo".

## Etapa 1
Saída de `python etapa01_agente.py`:
```
[modelo] openrouter:openai/gpt-6-luna
[tool] consultar_servidor 1002
A matrícula 1002 ainda tem **30 dias de férias**.
Abono pecuniário é a conversão de parte das férias em dinheiro. Em geral, o servidor recebe o valor correspondente aos dias convertidos, além da remuneração das férias. As regras e a quantidade permitida dependem da legislação aplicável ao órgão.
```
- Quantas vezes `[tool] consultar_servidor` apareceu? Por quê?
  **1 vez.** Só a primeira pergunta cita uma matrícula e depende do cadastro; a segunda é conceitual e o agente respondeu direto.
- O que mudei até o agente usar a tool só quando precisava?
  Nada precisou ser ajustado após a primeira versão: a docstring diz "somente quando a pergunta for sobre uma matrícula específica; não use para perguntas gerais", e as instruções do agente repetem isso e proíbem inventar saldo.
