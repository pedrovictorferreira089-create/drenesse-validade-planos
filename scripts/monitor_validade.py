"""Monitor diário da validade dos planos (API de integração do Belle).

Uso: python3 scripts/monitor_validade.py [--hoje AAAA-MM-DD]

1. Tira a foto do dia: idPlano, unidade, venda, validade e sessões restantes de todos os planos com sessões
   a fazer nas 4 unidades (relatório Sessões de Planos, janelas de 3 meses desde 2018).
2. Compara com a foto anterior (dados/monitor/foto_validade.csv) e registra cada validade que mudou em
   dados/monitor/alteracoes_detectadas.csv.
3. Completa o cadastro de vendedora dos planos que aparecem no dashboard (dados/monitor/vendedores.csv).

O token vem do proxy da sessão (ou da variável BELLE_TOKEN); nunca fica no código.
"""
import argparse
import csv
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://app.bellesoftware.com.br/api/release/controller/IntegracaoExterna/v1.0/"
UNIDADES = {1: "Petrópolis", 2: "Lagoa Nova", 3: "Capim Macio", 6: "Norte Shopping"}
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MON = os.path.join(RAIZ, "dados", "monitor")
FOTO = os.path.join(MON, "foto_validade.csv")
ALTER = os.path.join(MON, "alteracoes_detectadas.csv")
VEND = os.path.join(MON, "vendedores.csv")
ESTADO = os.path.join(MON, "estado.json")

CAMPOS_FOTO = ["id", "estab", "venda", "validade", "vendidas", "restantes", "valor"]
CAMPOS_ALTER = ["id", "estab", "unidade", "venda", "validade_antes", "validade_depois", "meses_antes", "meses_depois",
                "foto_anterior", "detectado_em", "restantes", "valor"]
CAMPOS_VEND = ["id", "estab", "venda", "vendedor", "plano", "cliente"]


def api(path, **q):
    url = BASE + path + "?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers={"Authorization": os.environ.get("BELLE_TOKEN", "x")})
    for tentativa in range(5):
        try:
            data = json.loads(urllib.request.urlopen(req, timeout=300).read())
            break
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if tentativa == 4 or (isinstance(e, urllib.error.HTTPError) and 400 <= e.code < 500 and e.code != 429):
                raise
            time.sleep(10 * (tentativa + 1))
    if isinstance(data, dict) and (data.get("erro") or data.get("error")):
        raise RuntimeError(f"{path} {q}: {data}")
    time.sleep(0.5)
    return data


def br_data(s):
    return dt.datetime.strptime(s, "%d/%m/%Y").date() if s else None


def num(v):
    if v in (None, ""):
        return 0.0
    s = str(v)
    return float(s.replace(".", "").replace(",", ".")) if "," in s else float(s)


def meses(venda, validade):
    """Meses entre a venda e a validade (o Belle soma meses inteiros à data da venda)."""
    if not venda or not validade:
        return None
    return round((validade - venda).days / 30.4375)


def trimestres(ate, desde=dt.date(2018, 1, 1)):
    fim = ate
    while fim >= desde:
        ini = dt.date(fim.year, 3 * ((fim.month - 1) // 3) + 1, 1)
        yield max(ini, desde), fim
        fim = ini - dt.timedelta(days=1)


def tirar_foto(hoje):
    """Planos com sessões a fazer: {id: {...}}. Validade = maior data entre os serviços do plano."""
    planos = {}
    for estab in UNIDADES:
        vazios = 0
        for ini, fim in trimestres(hoje):
            linhas = api("relatorios/sessoes_planos", codEstab=estab, dtVndIni=ini.strftime("%d/%m/%Y"),
                         dtVndFim=fim.strftime("%d/%m/%Y"))
            vazios = 0 if linhas else vazios + 1
            for x in linhas:
                pid = str(x["idPlano"])
                p = planos.setdefault(pid, {"id": pid, "estab": estab, "venda": br_data(x["dtVenda"]), "validade": None,
                                            "vendidas": 0, "restantes": 0, "valor": num(x.get("vlrFinalPlano"))})
                v = br_data(x.get("dtValidade"))
                if v and (p["validade"] is None or v > p["validade"]):
                    p["validade"] = v
                p["vendidas"] += int(num(x.get("sessoesVendidas")))
                p["restantes"] += int(num(x.get("sessoesRestante")))
            if vazios >= 4:  # início do histórico da unidade
                break
    return {k: p for k, p in planos.items() if p["restantes"] > 0 and p["validade"]}


def ler_csv(caminho):
    if not os.path.exists(caminho):
        return []
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def gravar_csv(caminho, campos, linhas, modo="w"):
    novo = modo == "w" or not os.path.exists(caminho)
    with open(caminho, modo, newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        if novo:
            w.writeheader()
        w.writerows(linhas)


def iso(d):
    return d.isoformat() if d else ""


def completar_vendedores(ids_por_estab_venda):
    """Busca em venda_planos a vendedora e a cliente dos planos que ainda não estão no cadastro (por unidade e trimestre)."""
    cad = {r["id"]: r for r in ler_csv(VEND)}
    faltam = {(e, v) for pid, (e, v) in ids_por_estab_venda.items() if pid not in cad or cad[pid].get("cliente") is None}
    janelas = {}
    for e, v in faltam:
        ini = dt.date(v.year, 3 * ((v.month - 1) // 3) + 1, 1)
        fim = (dt.date(ini.year + (ini.month + 2) // 12, (ini.month + 2) % 12 + 1, 1) - dt.timedelta(days=1))
        janelas.setdefault((e, ini, fim), set())
    for (e, ini, fim) in sorted(janelas):
        for p in api("venda_planos", codEstab=e, dtInicio=ini.strftime("%d/%m/%Y"), dtFim=fim.strftime("%d/%m/%Y")):
            pid = str(p["codOrcamento"])
            cad[pid] = {"id": pid, "estab": e, "venda": iso(br_data(p.get("dataVenda"))),
                        "vendedor": " ".join((p.get("vendedor") or "").split()), "plano": (p.get("nomePlano") or "").strip(),
                        "cliente": " ".join((p.get("cliente") or "").split())}
    for pid, (e, v) in ids_por_estab_venda.items():  # não achados: registra vazio para não buscar de novo
        if cad.get(pid, {}).get("cliente") is None:
            cad[pid] = {"id": pid, "estab": e, "venda": iso(v), "vendedor": cad.get(pid, {}).get("vendedor", ""),
                        "plano": cad.get(pid, {}).get("plano", ""), "cliente": ""}
    gravar_csv(VEND, CAMPOS_VEND, sorted(cad.values(), key=lambda r: r["id"]))
    return cad


def atualizar_cadastro():
    """Vendedora e cliente dos planos que aparecem no painel: alterados (foto ou Auditoria) e vendidos desde 2026 com mais de 6 meses."""
    foto = {r["id"]: r for r in ler_csv(FOTO)}
    cad = {r["id"]: r for r in ler_csv(VEND)}
    interesse = {r["id"]: (int(r["estab"]), dt.date.fromisoformat(r["venda"])) for r in ler_csv(ALTER)}
    for pid, f in foto.items():
        venda, validade = dt.date.fromisoformat(f["venda"]), dt.date.fromisoformat(f["validade"])
        if venda >= dt.date(2026, 1, 1) and (meses(venda, validade) or 0) > 6:
            interesse[pid] = (int(f["estab"]), venda)
    for a in ler_csv(os.path.join(MON, "auditoria_belle.csv")):
        f = foto.get(a["id"]) or cad.get(a["id"])
        if f and f.get("venda"):
            interesse[a["id"]] = (int(f.get("estab") or a["estab"]), dt.date.fromisoformat(f["venda"]))
    completar_vendedores(interesse)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hoje", help="data da foto (AAAA-MM-DD); padrão: hoje em Natal")
    ap.add_argument("--cadastro", action="store_true", help="só completa vendedora e cliente, sem tirar foto")
    a = ap.parse_args()
    if a.cadastro:
        atualizar_cadastro()
        return
    agora = dt.datetime.now(dt.timezone(dt.timedelta(hours=-3)))
    hoje = dt.date.fromisoformat(a.hoje) if a.hoje else agora.date()
    os.makedirs(MON, exist_ok=True)

    anterior = {r["id"]: r for r in ler_csv(FOTO)}
    estado = json.load(open(ESTADO)) if os.path.exists(ESTADO) else {}
    data_anterior = estado.get("ultima_foto", "")
    if data_anterior == hoje.isoformat():
        print(f"Foto de {hoje} já tirada; só completando vendedora e cliente.")
        atualizar_cadastro()
        return

    t0 = time.time()
    foto = tirar_foto(hoje)
    print(f"Foto de {hoje}: {len(foto)} planos com sessões a fazer ({time.time() - t0:.0f}s).")
    if len(foto) < 0.5 * max(len(anterior), 1):
        sys.exit(f"Foto suspeita: {len(foto)} planos contra {len(anterior)} na anterior. Nada gravado.")

    novas = []
    for pid, p in foto.items():
        a_ = anterior.get(pid)
        if not a_ or a_["validade"] == iso(p["validade"]):
            continue
        antes = dt.date.fromisoformat(a_["validade"])
        novas.append({"id": pid, "estab": p["estab"], "unidade": UNIDADES[p["estab"]], "venda": iso(p["venda"]),
                      "validade_antes": a_["validade"], "validade_depois": iso(p["validade"]),
                      "meses_antes": meses(p["venda"], antes), "meses_depois": meses(p["venda"], p["validade"]),
                      "foto_anterior": data_anterior, "detectado_em": hoje.isoformat(),
                      "restantes": p["restantes"], "valor": f'{p["valor"]:.2f}'})
    if novas:
        gravar_csv(ALTER, CAMPOS_ALTER, novas, modo="a")
    elif not os.path.exists(ALTER):
        gravar_csv(ALTER, CAMPOS_ALTER, [])
    print(f"Validades alteradas desde {data_anterior or '(primeira foto)'}: {len(novas)}")

    gravar_csv(FOTO, CAMPOS_FOTO, [{**p, "venda": iso(p["venda"]), "validade": iso(p["validade"]), "valor": f'{p["valor"]:.2f}'}
                                   for p in sorted(foto.values(), key=lambda p: p["id"])])
    estado.update({"ultima_foto": hoje.isoformat(), "foto_anterior": data_anterior, "planos_na_foto": len(foto),
                   "alteracoes_na_ultima_foto": len(novas), "gerado_em": agora.isoformat(timespec="minutes")})
    json.dump(estado, open(ESTADO, "w"), ensure_ascii=False, indent=1)

    atualizar_cadastro()


if __name__ == "__main__":
    main()
