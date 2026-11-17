#!/usr/bin/env bash
# Rotina diária do painel "Auditoria de validade dos planos".
# 1. lê as respostas novas do botão da Auditoria (planilha-ponte);
# 2. tira a foto do dia pela API de integração do Belle e registra as validades que mudaram;
# 3. gera os dados do painel (painel/alteracoes.json, painel/monitor.json, painel/fila.json);
# 4. manda a fila nova para a planilha-ponte.
# Depois disso, o Claude sobe painel/alteracoes.json e painel/monitor.json para o painel e faz commit/push de dados/monitor.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/sync_auditoria.py respostas
python3 scripts/monitor_validade.py
python3 scripts/gerar_painel.py
python3 scripts/sync_auditoria.py fila
