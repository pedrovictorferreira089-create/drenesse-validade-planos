# Histórico — validade e renovação dos planos

## Linha do tempo

| Data | O que aconteceu |
|---|---|
| 30/09–01/10/2026 | Auditoria de preços e descontos com dados do Belle. Criada a aba "Validade dos planos" (validade acima de 12 meses, 2021–2026) no relatório "Auditoria de Descontos Drenesse". Planilha `Descontos_e_Validade_Drenesse.xlsx` com os 86 planos de 2026 acima de 12 meses (script `belle_desc_validade.py`). |
| 02/10 | Relatório "Desconto e Validade dos Planos": 86 planos de 2026 acima de 1 ano (2,8% das vendas) contra 1.454 (39%) no mesmo período de 2025; estoque de 3.438 planos ativos acima de 1 ano. |
| 06/10 | Atualização dos dados até 06/10: 91 planos de 2026 acima de 1 ano. Comparando consultas de 30/09 e 06/10, foi identificado que a data de validade estava sendo **renovada depois do vencimento** (caso real: venda em 30/01/2026, venceu em 30/07 com 2 sessões, renovada em outubro para 30/06/2028 — de 6 para 29 meses). |
| 08/10 | Plano de ação "Descontos e Validade" com aba de validade (91 planos, 17 prorrogados na semana) e listas semanais de vencimento por unidade. |
| 08/10 | Pedido do chefe: material de conscientização para as esteticistas, com foco na **data de renovação**. Criada a apresentação "Validade do plano". |
| 08/10 | Análise do modelo de contrato (cláusula 1, parágrafo único: plano vencido = contrato encerrado, salvo prorrogação autorizada pela Drenesse; cláusula 4: horários dentro da validade; cláusula 5: falta sem aviso). Criado o documento "Alterações no Contrato" com os pontos para a gerência; exportado em Word. |
| 08–09/10 | Alterações pedidas na apresentação e no documento (ver abaixo). |
| 09/10 | Descoberto no Belle onde ver quem alterou a validade (Venda de Planos → clicar no plano → Auditoria). Auditoria dos 91 planos concluída e planilha do Google preenchida. |

## Alterações pedidas pelo usuário

Na apresentação "Validade do plano":
1. Acrescentar que, quando a cliente terminar o prazo com sessões em aberto, ela passa por **reavaliação** antes de renovar.
2. Plano vencido com sessões em aberto: para renovar, **multa de 30% sobre o valor das sessões restantes** (exemplo R$ 1.000 / 10 sessões, fez 2, restam R$ 800 → R$ 240). "Nossa ideia anterior seria que ele deveria realizar outro plano, mas meu chefe pediu para aplicarmos essa multa para renovação."
3. Acrescentar um slide de **conscientização** ("No slide mostra muitos dados mas pouca conscientização para as meninas") → slide "Cuidar do prazo é cuidar da cliente".
4. Dizer que haverá **auditoria recorrente** e que, se ainda forem encontrados esses problemas, será **passível de advertência**.
5. Regra 2: tirar "com senha" (o Belle não tem senha para isso), mantendo que **só a gerência altera**.
6. Último slide: tirar a frase "Os 86 planos que já passaram de 1 ano serão ajustados pela gerência até 31/10, e cada cliente será avisada."

No documento "Alterações no Contrato": atualizar com a multa de 30% e a reavaliação, as regras internas (sem senha no Belle, permissão de usuário, auditoria e advertência, regra por escrito) e a observação sobre os 86 planos. Depois, exportar em Word.

## Método da auditoria de quem alterou a validade

- No Belle: **Venda de Planos → clicar no plano → Auditoria**. A operação procurada é "Alterou Validade" (mostra quem, quando e de quantos para quantos meses).
- Em massa: o Belle tem o endpoint interno `Plano/v1.0/listar_auditoria_venda_plano` (parâmetros `codOrcamento`, `dataIni`, `dataFim`, `estabGeral`). Ele só responde dentro do navegador logado (a partir da nuvem retorna "Token inválido ou bloqueado"). A auditoria dos 91 planos foi feita com um script colado no **console do navegador** (F12) com o Belle aberto, que percorreu os planos e copiou o resultado para a planilha.
- Critério usado: **operação "alterou validade"**; registrar **quem alterou a validade**, não quem fez a venda.
- Códigos das unidades no Belle: Petrópolis 1, Lagoa Nova 2, Capim Macio 3, Norte Shopping 6.

## Resultado da auditoria (91 planos)

- Por unidade: Lagoa Nova 33, Petrópolis 26, Capim Macio 21, Norte Shopping 11.
- Por mês da alteração: jul 18, ago 34, set 34, out 5.
- 85 de 91 alterados depois do vencimento (mediana de 20 dias).
- Acima de 24 meses (12 planos): Thayane 60 e 30; Bruna 50, 40, 40, 40, 30, 30; Andreza 33 e 25; Roberta Paiva 29; Vitória 25.
- Por função: recepção 50 (55%), central (primeiro contato, closer, treinamento, vendas) 19 (21%), coordenação 17 (19%), esteticistas sêniores 3 (3%), fora do RH 2.
- Só 1 alteração feita pela mesma pessoa que vendeu o plano.
- Ponto de atenção levantado: a coordenadora (Andreza) pode contar como "gerência"; mesmo assim, duas alterações dela passaram de 24 meses, fora da regra de no máximo 12 meses da venda.
