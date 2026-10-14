"""Converte a primeira recolha (feita no browser em 13/10/2026) para o formato do scraper.

Uso: python -m tools.importar_recolha_browser <pasta_raw> <data>
"""
import json
import sys
from pathlib import Path

from scraper.common import Registo, classificar, peso_em_gramas, eur_kg_de_texto
from scraper.pingodoce import _peso
from scraper.run import gravar


def carregar(raw: Path) -> list[Registo]:
    regs = []
    for i, n, m, p, q, old, promo in json.loads((raw / "continente.json").read_text()):
        regs.append(Registo("Continente", i, n, m, p, peso_em_gramas(q), None, old,
                            bool(promo) or bool(old and old > p)))
    for i, n, m, p, u, old, _ in json.loads((raw / "pingodoce.json").read_text()):
        peso, nota = _peso(u)
        regs.append(Registo("Pingo Doce", i, n, m, p, peso,
                            eur_kg_de_texto(u) if "€/kg" in u.lower() else None, old,
                            bool(old and old > p), nota=nota))
    for i, n, m, p, u, old, strike in json.loads((raw / "auchan.json").read_text()):
        regs.append(Registo("Auchan", i, n, m, p, peso_em_gramas(n), eur_kg_de_texto(u), old,
                            bool(strike) or bool(old and old > p)))
    for i, txt, slug, p, venda, old, promo, u in json.loads((raw / "elcorteingles.json").read_text()):
        nome, marca = [x.strip() for x in txt.rsplit("  ", 1)] if "  " in txt else (txt, "")
        regs.append(Registo("El Corte Inglés", i, nome, marca, p,
                            peso_em_gramas(venda or "") or peso_em_gramas(slug.replace("-", " ")),
                            eur_kg_de_texto(u), old, bool(promo),
                            url=f"https://www.elcorteingles.pt/supermercado/B{i}-{slug}/"))
    im = json.loads((raw / "intermarche.json").read_text())
    for ean, nome, marca, peso, fam, n, med, mn, mx, _ in im["rows"]:
        if fam.split("/")[0] in {"10103", "10104", "10071"} or ean.startswith("2"):
            continue
        regs.append(Registo("Intermarché", ean, nome, marca, round(med, 2), peso, ean=ean,
                            n_lojas=n, preco_min_lojas=mn, preco_max_lojas=mx,
                            nota=f"Preço = mediana entre {n} lojas",
                            preparado=fam.split("/")[0] in {"10115", "11641", "11574"}))
    return regs


if __name__ == "__main__":
    raw, data = Path(sys.argv[1]), sys.argv[2]
    brutos = carregar(raw)
    ok = [r for r in (classificar(b) for b in brutos) if r]
    print(f"{len(brutos)} brutos, {len(ok)} de arroz")
    gravar(ok, Path("data"), data, {})
