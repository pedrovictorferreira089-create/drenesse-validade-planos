"""Gera o favorito (bookmarklet) do botão de auditoria a partir de botao/botao_auditoria.js.

Uso: python3 scripts/gerar_botao.py  ->  botao/favorito.txt (uma linha "javascript:..." para colar na URL do favorito)
Usa apps_script_url e chave de dados/monitor/config.json. O arquivo gerado leva a chave: não publique.
"""
import json
import os
import urllib.parse

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cfg = json.load(open(os.path.join(RAIZ, "dados", "monitor", "config.json")))
if not cfg.get("apps_script_url"):
    raise SystemExit("Falta apps_script_url em dados/monitor/config.json.")
fonte = open(os.path.join(RAIZ, "botao", "botao_auditoria.js"), encoding="utf-8").read()
codigo = "\n".join(l for l in fonte.splitlines() if not l.strip().startswith("//"))
codigo = codigo.replace("__URL__", cfg["apps_script_url"]).replace("__CHAVE__", cfg["chave"])
saida = os.path.join(RAIZ, "botao", "favorito.txt")
open(saida, "w", encoding="utf-8").write("javascript:" + urllib.parse.quote(codigo, safe="(){}[]=>;:,.'`$!*/?&+-_~@"))
print(f"Favorito gerado em {saida} ({os.path.getsize(saida)} caracteres).")
