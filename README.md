# Drenesse — Validade e renovação dos planos

Repositório de continuidade do trabalho sobre **planos com validade acima de 1 ano** e as **regras de vencimento e renovação** da Drenesse (Natal/RN), feito entre 30/09 e 09/10/2026. **Para retomar em outro chat, leia este README, depois [docs/HISTORICO.md](docs/HISTORICO.md) e [docs/RELATORIOS.md](docs/RELATORIOS.md).**

## Situação atual (em 03/11/2026)

**O problema:** quase todos os planos saem da venda com 6 meses de validade (91%). Quando vencem com sessões em aberto, a data de validade é renovada no Belle, muitas vezes semanas depois de vencer e para prazos muito longos (há planos de 2026 com até 5 anos). O problema nasce na **data de renovação**, não na venda.

**Números de referência (planos vendidos de 01/01 a 06/10/2026):**
- 91 planos com validade acima de 1 ano, entre 3.152 vendidos; 86 deles ainda com 1.150 sessões a fazer (R$ 79 mil já pagos).
- 88 dos 91 foram vendidos entre janeiro e março, venceram entre julho e setembro e tiveram a data renovada depois de vencidos.
- De 30/09 a 08/10, 40 planos tiveram a data renovada em uma semana; todos já estavam vencidos.
- Próximos 30 dias (até 07/11): 407 planos vencem com sessões sobrando (Lagoa Nova 153, Capim Macio 103, Norte 96, Petrópolis 55).
- Estoque antigo: 3.438 planos ativos com validade acima de 1 ano (61% dos planos ativos), vencendo até 2034.

**Auditoria de quem alterou a validade (91 planos, concluída em 09/10):** todas as alterações foram de 6 meses para mais. 85 das 91 foram feitas **depois** do vencimento (mediana de 20 dias depois). Quem mais alterou:

| Pessoa | Função | Planos |
|---|---|---|
| Andreza Rayane | Coordenadora (Lagoa Nova) | 17 |
| Vitória Borges | Recepção Petrópolis | 17 |
| Bruna Letícia | Primeiro contato (central) | 11 (validades de 30 a 50 meses) |
| Yannye Thaynnara / Haline Samara | Recepção | 6 cada |
| Outras 16 pessoas | maioria recepção | 1 a 5 cada |

Por função: recepção 50 planos (55%), central 19 (21%), coordenação 17 (19%), esteticistas sêniores 3 (3%). **Quase ninguém que alterou é esteticista** — a conscientização e a regra de advertência precisam chegar também à recepção, à coordenação e à central. 12 planos ficaram acima de 24 meses (maior: 60 meses). Só 1 dos 91 foi alterado pela mesma pessoa que vendeu.

### Regras definidas (apresentadas às esteticistas)
1. Na venda, a validade segue o tamanho do pacote: até 24 sessões, 6 meses; 25 sessões ou mais, 12 meses.
2. Só a gerência altera a data no Belle: uma única vez, com o motivo registrado, e no máximo até 12 meses da venda. (O Belle não tem "senha de gerente" para isso; o bloqueio é pela permissão de usuário.)
3. Venceu com sessões em aberto: para renovar, reavaliação e **multa de 30%** sobre o valor das sessões restantes, pelo preço pago por sessão. Exemplo: plano de R$ 1.000 com 10 sessões, fez 2, restam 8 = R$ 800 → multa de R$ 240. (Decisão do chefe: substitui a ideia anterior de exigir um plano novo.)
4. Auditoria recorrente: data alterada fora da regra é passível de advertência.

### Painel de auditoria (desde 17/11/2026)

Painel **Auditoria de validade dos planos**: https://claude.ai/artifact/8cbaXTrQ3daPqc8TJdESqr (fica privado até ser compartilhado pelo menu Compartilhar).
- **Todo dia (automático):** uma rotina tira a foto da validade de todos os planos com sessões a fazer (API de integração, Sessões de Planos), compara com o dia anterior e registra cada validade que mudou (`scripts/rotina_diaria.sh`). Os dados ficam em `dados/monitor/`.
- **Quem alterou:** só a Auditoria do Belle mostra, e ela só responde a quem está logado no navegador (testado da nuvem em 16/11: 401 "Token inválido ou bloqueado"). A gerência clica num **botão de favoritos** no Belle, que consulta a Auditoria dos planos da fila e grava o resultado numa planilha-ponte (Google Apps Script) lida pela rotina. Instalação em [botao/COMO_INSTALAR.md](botao/COMO_INSTALAR.md).
- **Regra aplicada:** fora da regra = nova validade acima de 12 meses da venda, ou segunda alteração que aumenta a validade (decisão de 17/11: a função de quem alterou não entra na regra; o painel mostra quem alterou e a função, de `dados/monitor/funcoes.csv`, montado das planilhas do RH). "Plano já vencido" é um alerta à parte (renovar exige reavaliação e multa de 30%, que o Belle não mostra).
- **Na primeira foto (17/11):** 15.570 planos com sessões a fazer; 105 planos vendidos em 2026 com validade acima de 12 meses, dos quais **24 passaram de 12 meses depois de 06/10** (não estavam nos 91). Fila inicial da Auditoria: 1.572 planos (24 de 2026 acima de 12 meses, 261 de 2026 com 7 a 12 meses, 1.287 de 2025 acima de 12 meses).

### Pendências em aberto
1. Fazer uma versão da apresentação (ou um reforço) para **recepção, coordenação e central**, que foram quem mais alterou datas.
2. Bloquear a alteração de validade no Belle pela **permissão de usuário** (só gerência).
3. Gerência decidir as alterações no contrato (ver documento "Alterações no Contrato") e passar pelo advogado; qualquer redução de validade dos planos já alterados depende do advogado.
4. Lista semanal (toda segunda) por unidade dos planos que vencem nas próximas 4 semanas, com as sessões que faltam.
5. Auditoria recorrente: automatizada no painel (acima). Falta instalar a planilha-ponte e o botão (botao/COMO_INSTALAR.md), confirmar a função de 4 pessoas fora das planilhas do RH (Maria Leanne Lopes Alves, Roberta Viana de Oliveira, Vanessa Maria de Oliveira Pereira, Marina Batista Costa Pontes da Silva), se a coordenação (Andreza) conta como gerência e a data em que a regra passou a valer (no painel: 09/10/2026).
6. Decidir o que fazer com o estoque antigo de planos longos (3.438 ativos acima de 1 ano).

## Materiais

| Material | Link / arquivo | Situação |
|---|---|---|
| Painel "Auditoria de validade dos planos" (atualizado todo dia) | https://claude.ai/artifact/8cbaXTrQ3daPqc8TJdESqr | **Vigente** |
| Apresentação "Validade do plano" (reunião com as esteticistas, 15 slides) | https://claude.ai/artifact/N6WVpPMexBvXTiEeitmrzn · PDF em `apresentacao/` | **Vigente** |
| Alterações no Contrato (documento para a gerência) | https://claude.ai/artifact/L9v2wWCPJ7dhQ82sXT49wB | **Vigente**, aguarda decisão da gerência |
| Planilha "Quem alterou a validade" (91 planos) | https://docs.google.com/spreadsheets/d/1xnAqRj10vH_LsChbJBa4KbcUz3YRAouUCUHCOichDKk/edit?usp=sharing · cópia sem nomes de clientes em `dados/auditoria_91_planos.csv` | **Concluída** em 09/10 |
| Plano de ação "Descontos e Validade" (08/10) | https://claude.ai/artifact/25kUiYGYieKcm7m5PJmKqq | Base do plano de ação; o item "corrigir os 86 planos até 31/10" foi retirado depois |
| Relatório "Desconto e Validade dos Planos" (02/10) | https://claude.ai/artifact/HqvU4sbFwRYD1D8WLxHRUH | Diagnóstico inicial (86 planos) |
| Auditoria de Descontos — aba Validade (01/10) | https://claude.ai/artifact/TZiv3LFtGRrUFKtC8QoKiQ | Histórico 2021–2026 |

Os links abrem só para a conta dona dos relatórios. O conteúdo de cada um está resumido em [docs/RELATORIOS.md](docs/RELATORIOS.md).

## Estrutura do repositório

| Pasta | Conteúdo |
|---|---|
| `docs/HISTORICO.md` | Linha do tempo, alterações pedidas, decisões e método da auditoria |
| `docs/RELATORIOS.md` | Conteúdo detalhado dos relatórios publicados e do documento do contrato |
| `apresentacao/` | PDF da apresentação "Validade do plano" |
| `dados/auditoria_91_planos.csv` | Os 91 planos auditados: unidade, datas, vendedora, quem alterou, de/para (sem nomes de clientes) |
| `dados/monitor/` | Foto diária da validade, alterações detectadas, respostas da Auditoria do Belle, funções do RH e configuração do painel |
| `scripts/monitor_validade.py`, `gerar_painel.py`, `sync_auditoria.py`, `rotina_diaria.sh` | Rotina diária do painel (foto pela API, dados do painel, troca com a planilha-ponte) |
| `botao/` | Botão de favoritos da Auditoria (fonte), código do Apps Script da planilha-ponte e instruções |
| `painel/` | Página e dados do painel, como publicados |
| `scripts/belle_desc_validade.py` | Gerador da planilha de descontos e validade a partir da API do Belle (token na variável `BELLE_TOKEN`, nunca no código) |
