"""Gera os dados do painel "Auditoria de Validade Drenesse" a partir de dados/monitor/.

Uso: python3 scripts/gerar_painel.py [pasta_de_saida]   (padrão: painel/)

Entradas (dados/monitor/): foto_validade.csv (foto diária da API), alteracoes_detectadas.csv (validades que mudaram
entre duas fotos), auditoria_belle.csv (operações "Alterou Validade" lidas na Auditoria do Belle), consultas.csv
(planos já consultados na Auditoria), vendedores.csv, funcoes.csv e config.json.

Saídas: alteracoes.json (uma linha por alteração de validade, com a regra aplicada), fila.json (planos que ainda
precisam ser consultados na Auditoria do Belle, por prioridade) e monitor.json (situação da alimentação).

Regra vigente: só a gerência altera, uma única vez, e no máximo até 12 meses da venda.
- acima_12: a nova validade passa de 12 meses contados da venda;
- repetida: segunda alteração ou mais no mesmo plano que aumenta a validade (reduzir para voltar à regra não conta);
- fora_regra: qualquer uma das duas (quem alterou é mostrado, mas não entra na regra). depois_vencido (alterou com o plano já vencido) é um alerta à parte:
  renovar plano vencido exige reavaliação e multa de 30%, que o Belle não mostra aqui.
"""
import calendar
import csv
import datetime as dt
import json
import os
import re
import sys
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MON = os.path.join(RAIZ, "dados", "monitor")
UNIDADES = {1: "Petrópolis", 2: "Lagoa Nova", 3: "Capim Macio", 6: "Norte Shopping"}


def ler(nome):
    caminho = os.path.join(MON, nome)
    if not os.path.exists(caminho):
        return []
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def d(s):
    """Data ISO (AAAA-MM-DD) ou dd/mm/aaaa, lida pelo texto, sem fuso."""
    if not s:
        return None
    s = str(s).strip()
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return dt.date(int(m[1]), int(m[2]), int(m[3]))
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", s)
    return dt.date(int(m[3]), int(m[2]), int(m[1])) if m else None


def mais_meses(data, n):
    mes = data.month - 1 + n
    ano, mes = data.year + mes // 12, mes % 12 + 1
    return dt.date(ano, mes, min(data.day, calendar.monthrange(ano, mes)[1]))


def meses(venda, validade):
    return round((validade - venda).days / 30.4375) if venda and validade else None


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return " ".join(w for w in re.split(r"[^a-z]+", s) if w)


def casar_pessoas(funcoes):
    """Acha a função pelo nome completo; senão pelo primeiro e último nome; senão pelos dois primeiros."""
    exato = {norm(r["nome"]): r for r in funcoes}
    def chaves(n):
        p = n.split()
        return [(p[0], p[-1]), tuple(p[:2])] if len(p) > 1 else []
    por_chave = {}
    for r in funcoes:
        for k in chaves(norm(r["nome"])):
            por_chave.setdefault(k, []).append(r)

    def achar(nome):
        n = norm(nome)
        if not n:
            return None
        if n in exato:
            return exato[n]
        for k in chaves(n):
            if len(por_chave.get(k, [])) == 1:
                return por_chave[k][0]
        return None
    return achar


DE_PARA = re.compile(r"de\s*(\d+)\s*(?:mes(?:es)?\s*)?para\s*(\d+)", re.I)


def main():
    saida = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "painel")
    os.makedirs(saida, exist_ok=True)
    cfg = json.load(open(os.path.join(MON, "config.json")))
    estado = json.load(open(os.path.join(MON, "estado.json"))) if os.path.exists(os.path.join(MON, "estado.json")) else {}
    vigencia = d(cfg["vigencia_regra"])
    limite = int(cfg.get("limite_meses", 12))
    hoje = d(estado.get("ultima_foto")) or dt.date.today()

    foto = {r["id"]: r for r in ler("foto_validade.csv")}
    vend = {r["id"]: r for r in ler("vendedores.csv")}
    achar = casar_pessoas(ler("funcoes.csv"))
    consultas = {}
    for r in ler("consultas.csv"):
        c = d(r["consultado_em"])
        if c and (r["id"] not in consultas or c > consultas[r["id"]]):
            consultas[r["id"]] = c

    def plano(pid, estab=None, venda=None):
        f, v = foto.get(pid, {}), vend.get(pid, {})
        estab = int(estab or f.get("estab") or v.get("estab") or 0)
        return {"id": pid, "unidade": UNIDADES.get(estab, ""), "estab": estab,
                "venda": d(venda) or d(f.get("venda")) or d(v.get("venda")),
                "vendedora": v.get("vendedor", ""), "restantes": int(f["restantes"]) if f.get("restantes") else None,
                "validade_hoje": d(f.get("validade"))}

    eventos = []
    # 1) Operações "Alterou Validade" lidas na Auditoria do Belle (botão ou auditoria manual).
    for a in ler("auditoria_belle.csv"):
        if not re.search(r"validade", a.get("acao", "") + " " + a.get("detalhes", ""), re.I):
            continue
        de, para = a.get("de"), a.get("para")
        if not (de and para):
            m = DE_PARA.search(a.get("detalhes", ""))
            de, para = (m[1], m[2]) if m else (de, para)
        eventos.append({**plano(a["id"], a.get("estab")), "data": d(a["dt"]), "hora": a.get("hora", ""),
                        "quem": " ".join(a["usuario"].split()), "de": int(de) if de else None, "para": int(para) if para else None,
                        "origem": a.get("fonte") or "Auditoria do Belle", "status": "Identificado"})
    por_plano = {}
    for e in eventos:
        por_plano.setdefault(e["id"], []).append(e)

    # 2) Validades que mudaram entre duas fotos e que a Auditoria ainda não explicou.
    for c in ler("alteracoes_detectadas.csv"):
        ini, fim = d(c["foto_anterior"]), d(c["detectado_em"])
        explicada = any(e["data"] and ini and ini - dt.timedelta(days=1) <= e["data"] <= fim + dt.timedelta(days=1)
                        for e in por_plano.get(c["id"], []))
        if explicada:
            continue
        consultado = consultas.get(c["id"])
        eventos.append({**plano(c["id"], c["estab"], c["venda"]), "data": fim, "hora": "", "data_aprox": True,
                        "quem": "", "de": int(c["meses_antes"]), "para": int(c["meses_depois"]),
                        "origem": f"Foto diária: validade mudou entre {ini:%d/%m} e {fim:%d/%m/%Y}",
                        "status": "Sem registro na Auditoria" if consultado and consultado >= fim else "Aguardando consulta"})

    # 3) Planos vendidos em 2026 com validade acima de 12 meses que ainda não foram consultados.
    for pid, f in foto.items():
        venda, validade = d(f["venda"]), d(f["validade"])
        if venda < dt.date(2026, 1, 1) or meses(venda, validade) <= limite or pid in por_plano or pid in consultas:
            continue
        if any(e["id"] == pid for e in eventos):
            continue
        eventos.append({**plano(pid), "data": None, "hora": "", "quem": "", "de": None, "para": meses(venda, validade),
                        "origem": "Validade acima de 12 meses, alteração anterior ao monitoramento", "status": "Aguardando consulta"})

    # Regra.
    eventos.sort(key=lambda e: (e["id"], e["data"] or dt.date.max, e["hora"] or ""))
    ordem = {}
    linhas = []
    for e in eventos:
        ordem[e["id"]] = ordem.get(e["id"], 0) + 1
        p = achar(e["quem"]) if e["quem"] else None
        venda = e["venda"]
        venc_ant = mais_meses(venda, e["de"]) if venda and e["de"] else None
        nova = mais_meses(venda, e["para"]) if venda and e["para"] else e.get("validade_hoje")
        dias = (e["data"] - venc_ant).days if e["data"] and venc_ant and not e.get("data_aprox") else None
        if e.get("data_aprox") and e["data"] and venc_ant:
            dias = (e["data"] - venc_ant).days
        acima = bool(nova and venda and nova > mais_meses(venda, limite))
        # Segunda alteração que aumenta a validade (uma redução para voltar à regra não conta como repetição).
        repetida = ordem[e["id"]] > 1 and not (e["de"] and e["para"] and e["para"] < e["de"])
        linhas.append({
            "plano": e["id"], "unidade": e["unidade"], "vendedora": e["vendedora"] or "Não informada",
            "venda": venda.isoformat() if venda else "",
            "data": e["data"].isoformat() if e["data"] else "", "mes": e["data"].strftime("%Y-%m") if e["data"] else "",
            "data_aproximada": bool(e.get("data_aprox")), "hora": e["hora"],
            "quem": e["quem"] or "Aguardando consulta",
            "funcao": (p["funcao"] if p else ("Não identificada" if e["quem"] else "")),
            "grupo": (p["grupo"] if p else ("Não identificado" if e["quem"] else "Aguardando consulta")),
            "gerencia": "sim" if p and p["gerencia"] == "sim" else ("não" if e["quem"] else ""),
            "de_meses": e["de"], "para_meses": e["para"],
            "vencimento_anterior": venc_ant.isoformat() if venc_ant else "",
            "nova_validade": nova.isoformat() if nova else "",
            "dias_apos_vencimento": dias,
            "sessoes_restantes": e["restantes"],
            "alteracao_no_plano": ordem[e["id"]],
            "acima_12_meses": acima, "alteracao_repetida": repetida,
            "depois_do_vencimento": bool(dias is not None and dias > 0),
            "fora_da_regra": acima or repetida,
            "depois_da_vigencia": bool(e["data"] and e["data"] >= vigencia),
            "situacao": e["status"], "origem": e["origem"],
        })
    linhas.sort(key=lambda r: (r["data"] or "9999", r["plano"]), reverse=True)

    # Fila de consulta na Auditoria do Belle (o botão lê esta lista).
    fila, vistos = [], set()
    def entra(pid, prioridade, motivo, estab=None, venda=None):
        if pid in vistos:
            return
        vistos.add(pid)
        p = plano(pid, estab, venda)
        if p["venda"] and p["estab"] in UNIDADES:
            fila.append({"plano": pid, "estab": p["estab"], "unidade": p["unidade"], "venda": p["venda"].isoformat(),
                         "prioridade": prioridade, "motivo": motivo})
    for c in ler("alteracoes_detectadas.csv"):
        cons = consultas.get(c["id"])
        if not cons or cons < d(c["detectado_em"]):
            entra(c["id"], 1, "Validade alterada (foto diária)", c["estab"], c["venda"])
    for alvo, prioridade, motivo in ((lambda m, v: v >= dt.date(2026, 1, 1) and m > limite, 2, "Vendido em 2026, validade acima de 12 meses"),
                                     (lambda m, v: v >= dt.date(2026, 1, 1) and 6 < m <= limite, 3, "Vendido em 2026, validade de 7 a 12 meses"),
                                     (lambda m, v: dt.date(2025, 1, 1) <= v < dt.date(2026, 1, 1) and m > limite, 4, "Vendido em 2025, validade acima de 12 meses")):
        for pid, f in sorted(foto.items(), key=lambda kv: kv[1]["venda"], reverse=True):
            v = d(f["venda"])
            if pid not in consultas and alvo(meses(v, d(f["validade"])), v):
                entra(pid, prioridade, motivo)
    fila.sort(key=lambda r: (r["prioridade"], r["venda"]))

    codigo = open(os.path.abspath(__file__), encoding="utf-8").read()
    meta = [{"label": "gerar_painel.py", "value": codigo, "type": "code", "lang": "python"},
            {"label": "Entradas", "value": "API de integração do Belle (Sessões de Planos e Venda de Planos), Auditoria do Belle (Venda de Planos > plano > Auditoria) e planilhas do RH"}]
    json.dump({"rows": linhas, "meta": meta}, open(os.path.join(saida, "alteracoes.json"), "w"), ensure_ascii=False)
    json.dump({"rows": fila, "meta": meta}, open(os.path.join(saida, "fila.json"), "w"), ensure_ascii=False)

    identificadas = [r for r in linhas if r["situacao"] == "Identificado"]
    ult_consulta = max(consultas.values()) if consultas else None
    monitor = [{
        "atualizado_em": estado.get("gerado_em", ""), "ultima_foto": estado.get("ultima_foto", ""),
        "planos_na_foto": estado.get("planos_na_foto", 0), "alteracoes_ultima_foto": estado.get("alteracoes_na_ultima_foto", 0),
        "ultima_consulta_auditoria": ult_consulta.isoformat() if ult_consulta else "",
        "planos_consultados": len(consultas), "na_fila": len(fila),
        "na_fila_prioridade_1": sum(1 for r in fila if r["prioridade"] == 1),
        "na_fila_prioridade_2": sum(1 for r in fila if r["prioridade"] == 2),
        "alteracoes_identificadas": len(identificadas), "vigencia_regra": vigencia.isoformat(), "limite_meses": limite,
    }]
    json.dump({"rows": monitor, "meta": meta}, open(os.path.join(saida, "monitor.json"), "w"), ensure_ascii=False)
    print(f"{len(linhas)} alterações ({len(identificadas)} com quem alterou), fila de {len(fila)} planos -> {saida}")


if __name__ == "__main__":
    main()
