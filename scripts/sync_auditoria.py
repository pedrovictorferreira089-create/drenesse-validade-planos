"""Troca de dados com a planilha-ponte (Apps Script) do botão de auditoria.

Uso:
  python3 scripts/sync_auditoria.py respostas   # lê as respostas novas do botão e grava em dados/monitor/
  python3 scripts/sync_auditoria.py fila        # envia a fila de planos a consultar (painel/fila.json)

A URL do App da Web e a chave ficam em dados/monitor/config.json (apps_script_url, chave).
"""
import csv
import json
import os
import re
import sys
import urllib.parse
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MON = os.path.join(RAIZ, "dados", "monitor")
CFG = json.load(open(os.path.join(MON, "config.json")))
ESTADO = os.path.join(MON, "estado.json")
CAMPOS_AUD = ["id", "estab", "dt", "hora", "usuario", "acao", "detalhes", "de", "para", "fonte", "consultado_em"]
CAMPOS_CONS = ["id", "consultado_em", "alteracoes", "fonte"]
DE_PARA = re.compile(r"de\s*(\d+)\s*(?:mes(?:es)?\s*)?para\s*(\d+)", re.I)


def chamar(params=None, corpo=None):
    url = CFG["apps_script_url"]
    if params:
        url += "?" + urllib.parse.urlencode(params)
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(url, data=dados, headers={"Content-Type": "text/plain;charset=utf-8"} if dados else {})
    resp = json.loads(urllib.request.urlopen(req, timeout=300).read())
    if isinstance(resp, dict) and resp.get("erro"):
        raise RuntimeError(f"Apps Script: {resp['erro']}")
    return resp


def ler(nome):
    caminho = os.path.join(MON, nome)
    if not os.path.exists(caminho):
        return []
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def anexar(nome, campos, linhas):
    caminho = os.path.join(MON, nome)
    novo = not os.path.exists(caminho)
    with open(caminho, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        if novo:
            w.writeheader()
        w.writerows(linhas)


def data_iso(s):
    s = (s or "").strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s) or None
    if m:
        return f"{m[1]}-{m[2]}-{m[3]}"
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", s)
    return f"{m[3]}-{m[2]}-{m[1]}" if m else s


def respostas():
    estado = json.load(open(ESTADO)) if os.path.exists(ESTADO) else {}
    desde = int(estado.get("respostas_lidas", 0))
    r = chamar({"acao": "respostas", "k": CFG["chave"], "desde": desde})
    linhas = r.get("linhas", [])
    ja = {(a["id"], a["dt"], a["hora"], a["usuario"], a["detalhes"]) for a in ler("auditoria_belle.csv")}
    ja_cons = {(c["id"], c["consultado_em"]) for c in ler("consultas.csv")}
    novas_aud, novas_cons, por_consulta = [], [], {}
    for x in linhas:
        chave_cons = (str(x["plano"]), x["consultado_em"])
        por_consulta.setdefault(chave_cons, 0)
        if x["acao"].startswith("SEM ALTERA"):
            continue
        por_consulta[chave_cons] += 1
        m = DE_PARA.search(x.get("detalhes", ""))
        a = {"id": str(x["plano"]), "estab": x["estab"], "dt": data_iso(x["data"]), "hora": x["hora"],
             "usuario": " ".join(x["usuario"].split()), "acao": x["acao"], "detalhes": x["detalhes"],
             "de": m[1] if m else "", "para": m[2] if m else "", "fonte": "Auditoria do Belle (botão)",
             "consultado_em": x["consultado_em"]}
        k = (a["id"], a["dt"], a["hora"], a["usuario"], a["detalhes"])
        if k not in ja:
            ja.add(k)
            novas_aud.append(a)
    for (pid, quando), n in por_consulta.items():
        if (pid, quando) not in ja_cons:
            novas_cons.append({"id": pid, "consultado_em": quando, "alteracoes": n, "fonte": "Auditoria do Belle (botão)"})
    if novas_aud:
        anexar("auditoria_belle.csv", CAMPOS_AUD, novas_aud)
    if novas_cons:
        anexar("consultas.csv", CAMPOS_CONS, novas_cons)
    estado["respostas_lidas"] = int(r.get("total", desde))
    if linhas:
        estado["ultima_resposta_botao"] = max(x["recebido_em"] for x in linhas)
    json.dump(estado, open(ESTADO, "w"), ensure_ascii=False, indent=1)
    print(f"Respostas do botão: {len(linhas)} linhas novas, {len(novas_aud)} alterações de validade, "
          f"{len(novas_cons)} planos consultados.")


def fila():
    rows = json.load(open(os.path.join(RAIZ, "painel", "fila.json")))["rows"]
    r = chamar(corpo={"k": CFG["chave"], "acao": "fila", "linhas": rows})
    print(f"Fila enviada à planilha-ponte: {r.get('n')} planos.")


if __name__ == "__main__":
    if not CFG.get("apps_script_url"):
        print("Planilha-ponte ainda não configurada (apps_script_url vazio em config.json); nada a fazer.")
        sys.exit(0)
    {"respostas": respostas, "fila": fila}[sys.argv[1]]()
