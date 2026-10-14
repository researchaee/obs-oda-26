"""Continente (continente.pt) — categoria Mercearia > Arroz, Massa e Farinha > Arroz.

O site é Salesforce Commerce Cloud: a grelha de produtos vem do endpoint
Search-UpdateGrid, em blocos de 35, com os dados do produto no atributo
data-product-tile-impression (JSON).
"""
import json

from bs4 import BeautifulSoup

from .common import Registo, sessao, get, peso_em_gramas, eur_kg_de_texto, euros

CADEIA = "Continente"
GRID = ("https://www.continente.pt/on/demandware.store/Sites-continente-Site/default/"
        "Search-UpdateGrid?cgid=mercearias-arroz-massa-arroz&pmin=0.01&start={start}&sz=35")


def parse(html: str) -> list[Registo]:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for t in soup.select("div.product-tile[data-product-tile-impression]"):
        imp = json.loads(t["data-product-tile-impression"])
        qty = t.select_one(".pwc-tile--quantity")
        qty = qty.get_text(" ", strip=True) if qty else ""
        lista = t.select_one(".prices-wrapper .list")
        ref = None
        if lista and "d-none" not in (lista.get("class") or []):
            ref = euros(lista.get_text(" ", strip=True).replace("PVPR", ""))
        sec = t.select_one(".pwc-tile--price-secondary")
        link = t.select_one("a[href]")
        out.append(Registo(
            cadeia=CADEIA, id=str(imp["id"]), nome=imp["name"], marca=imp.get("brand") or "",
            preco=float(imp["price"]), peso_g=peso_em_gramas(qty),
            eur_kg=eur_kg_de_texto(sec.get_text(" ", strip=True) if sec else ""),
            preco_ref=ref,
            promo=bool(t.select_one(".ct-product-tile-badge--promotional")) or bool(ref and ref > float(imp["price"])),
            url=link["href"] if link else "",
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
        start += 35
    return out
