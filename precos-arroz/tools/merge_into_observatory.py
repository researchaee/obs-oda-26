"""Junta a recolha de preços no retalho ao observatory-data.json do observatório.

    python -m tools.merge_into_observatory [caminho/observatory-data.json]

Escreve três coisas no ficheiro de dados (sem mexer no resto):
  retail            produtos da última recolha (formato compacto) — lido pelo painel 7
  history.retail    todas as recolhas acumuladas (folha «Histórico das recolhas» do Excel)
  sources           uma entrada por supermercado no catálogo de fontes
"""
import csv
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ.parent / "observatorio-maizoryza" / "observatory-data.json"

CADEIAS = ["Continente", "Pingo Doce", "Auchan", "Intermarché", "El Corte Inglés"]
TIPOS = ["Agulha", "Carolino", "Basmati", "Thai / Jasmim / Aromático", "Vaporizado / Estufado", "Integral",
         "Risotto (arbório, carnaroli)", "Paelha / Bomba", "Sushi / Poke",
         "Especialidades (selvagem, negro, vermelho)", "Pronto a comer / preparados", "Outros"]
SEGMENTOS = ["Marca própria", "Marca de fabricante", "Premium / Bio"]
SITES = {
    "Continente": "https://www.continente.pt/supermercado/mercearia/arroz-massa-e-farinha/arroz/",
    "Pingo Doce": "https://www.pingodoce.pt/home/produtos/mercearia/arroz-massa-e-leguminosas/arroz",
    "Auchan": "https://www.auchan.pt/pt/alimentacao/mercearia/arroz-e-massa/arroz/",
    "Intermarché": "https://www.intermarche.pt/",
    "El Corte Inglés": "https://www.elcorteingles.pt/supermercado/mercearia/massas-arroz-farinhas-e-legumes-secos/arroz/",
}
AUTORIDADE = {
    "Continente": "Modelo Continente (Sonae MC)", "Pingo Doce": "Pingo Doce (Jerónimo Martins)",
    "Auchan": "Auchan Retail Portugal", "Intermarché": "Os Mosqueteiros (lojas Intermarché)",
    "El Corte Inglés": "El Corte Inglés Portugal",
}


def _num(v):
    if v in (None, ""):
        return None
    f = float(v)
    return int(f) if f.is_integer() and abs(f) >= 10 else round(f, 3)


def compacto(latest: dict) -> dict:
    tipos = [t for t in TIPOS if any(p["tipo"] == t for p in latest["produtos"])]
    cadeias = [c for c in CADEIAS if c in latest["cadeias"]]
    prods = []
    for p in latest["produtos"]:
        if p["cadeia"] not in cadeias or p["tipo"] not in tipos or not p.get("eur_kg"):
            continue
        prods.append([cadeias.index(p["cadeia"]), tipos.index(p["tipo"]), SEGMENTOS.index(p["segmento"]),
                      p["nome"], p["marca"], _num(p["peso_g"]), _num(p["preco"]), _num(p["eur_kg"]),
                      _num(p.get("preco_ref")), 1 if p.get("promo") in (True, "True", 1) else 0,
                      _num(p.get("n_lojas")), _num(p.get("preco_min_lojas")), _num(p.get("preco_max_lojas")),
                      p.get("url") or ""])
    datas = {p["cadeia"]: p["data"] for p in latest["produtos"]}
    return {
        "retrieved": latest["data"],
        "chains": cadeias,
        "chain_dates": [datas.get(c, latest["data"]) for c in cadeias],
        "chain_urls": [SITES[c] for c in cadeias],
        "types": tipos,
        "segments": SEGMENTOS,
        "errors": latest.get("erros") or {},
        "fields": ["cadeia", "tipo", "segmento", "nome", "marca", "peso_g", "preco", "eur_kg", "preco_ref",
                   "promo", "n_lojas", "preco_min_lojas", "preco_max_lojas", "url"],
        "products": prods,
    }


def historico(csv_path: Path) -> list[dict]:
    if not csv_path.exists():
        return []
    with open(csv_path, encoding="utf-8") as f:
        return [{"captured": r["data"], "chain": r["cadeia"], "type": r["tipo"], "segment": r["segmento"],
                 "brand": r["marca"], "product": r["nome"], "weight_g": _num(r["peso_g"]),
                 "price_eur": _num(r["preco"]), "eur_kg": _num(r["eur_kg"]),
                 "promo": "sim" if r["promo"] in ("True", "1", "true") else ""}
                for r in csv.DictReader(f)]


def fontes(d: dict, retail: dict) -> None:
    lista = [s for s in d.get("sources", []) if not s.get("retail")]
    for c, url in zip(retail["chains"], retail["chain_urls"]):
        intermarche = c == "Intermarché"
        lista.append({
            "source": f"{c} — loja online",
            "authority": AUTORIDADE[c],
            "api": ("API JSON da loja online (pdvs/zone e products/byKeywordAndCategory), loja a loja"
                    if intermarche else "Página pública da categoria de arroz da loja online (recolha automática)"),
            "url": url,
            "api_url": url,
            "used_for": "Preços de venda ao consumidor do arroz, por tipo, marca e embalagem (Painel 7)",
            "coverage": "Portugal, recolha semanal desde 13/10/2026",
            "status": "Integrada no Painel 7",
            "notes": ("Cada loja Intermarché define os seus preços: o painel usa a mediana entre as lojas com loja online."
                      if intermarche else "Preço online do dia da recolha; pode diferir da loja física."),
            "retail": True,
        })
    d["sources"] = lista


def main():
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else DESTINO
    latest = json.loads((RAIZ / "data" / "latest.json").read_text(encoding="utf-8"))
    d = json.loads(destino.read_text(encoding="utf-8"))
    d["retail"] = compacto(latest)
    d.setdefault("history", {})["retail"] = historico(RAIZ / "data" / "historico_precos_arroz.csv")
    fontes(d, d["retail"])
    destino.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{destino}: {len(d['retail']['products'])} produtos de retalho, "
          f"{len(d['history']['retail'])} linhas de histórico, {len(d['sources'])} fontes")


if __name__ == "__main__":
    main()
