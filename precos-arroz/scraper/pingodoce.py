"""Pingo Doce (pingodoce.pt) — categoria Mercearia > Arroz, Massa e Leguminosas > Arroz.

Também Salesforce Commerce Cloud: Search-UpdateGrid em blocos de 14. Os dados
do produto estão em data-gtm-info (JSON). Produtos patrocinados («PUB», classe
retail-media) são ignorados.
"""
import json
import re

from bs4 import BeautifulSoup

from .common import Registo, sessao, get, eur_kg_de_texto

CADEIA = "Pingo Doce"
BASE = "https://www.pingodoce.pt"
GRID = (BASE + "/on/demandware.store/Sites-pingo-doce-Site/default/"
        "Search-UpdateGrid?cgid=ec_arroz_1300_100_100&pmin=0.04&start={start}&sz=14")


def _peso(unidade: str):
    """'1 Kg | 1,89 €/Kg' -> 1000 ; '0.25 Kg | …' -> 250 ; '1.5 Un | 1,49 €/Un' -> 1500 (assume kg)."""
    m = re.match(r"\s*([\d.,]+)\s*(kg|un|g)\b", unidade.lower())
    if not m:
        return None, ""
    q = float(m.group(1).replace(",", "."))
    if m.group(2) == "g":
        return q, ""
    if m.group(2) == "un":
        return q * 1000, "Peso inferido (o site indica «Un»)"
    return q * 1000, ""


def parse(html: str) -> list[Registo]:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for t in soup.select("div.product-tile-pd[data-gtm-info]"):
        if "retail-media" in (t.get("class") or []):
            continue
        g = json.loads(t["data-gtm-info"])["items"][0]
        unidade = t.select_one(".product-unit")
        unidade = unidade.get_text(" ", strip=True) if unidade else ""
        peso, nota = _peso(unidade)
        old = t.select_one(".product-price .strike-through .value, .product-price .list .value, .product-price del .value")
        ref = float(old["content"]) if old and old.get("content") else None
        nome = t.select_one(".product-name-link")
        link = t.select_one(".product-name-link a[href]")
        eur = eur_kg_de_texto(unidade) if "€/kg" in unidade.lower() else None
        out.append(Registo(
            cadeia=CADEIA, id=str(g["item_id"]),
            nome=nome.get_text(" ", strip=True) if nome else g["item_name"],
            marca=(t.select_one(".product-brand-name").get_text(strip=True)
                   if t.select_one(".product-brand-name") else g.get("item_brand", "")),
            preco=float(g["price"]), peso_g=peso, eur_kg=eur, preco_ref=ref,
            promo=bool(ref and ref > float(g["price"])),
            url=BASE + link["href"] if link else "", nota=nota,
        ))
    return out


def recolher() -> list[Registo]:
    s = sessao()
    out, start = [], 0
    while start < 1000:
        regs = parse(get(s, GRID.format(start=start)).text)
        if not regs:
            break
        out.extend(regs)
        start += 14
    return out
