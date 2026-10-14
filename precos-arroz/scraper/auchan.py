"""Auchan (auchan.pt) — categoria Mercearia > Arroz e Massa > Arroz.

Salesforce Commerce Cloud: Search-UpdateGrid em blocos de 24. O preço de venda
está em .sales .value[content]; o PVP recomendado (quando o site o mostra) em
.pvp-recommended; o €/kg em .auc-measures--price-per-unit.
"""
import json

from bs4 import BeautifulSoup

from .common import Registo, sessao, get, peso_em_gramas, eur_kg_de_texto, euros

CADEIA = "Auchan"
BASE = "https://www.auchan.pt"
GRID = (BASE + "/on/demandware.store/Sites-AuchanPT-Site/pt_PT/Search-UpdateGrid?"
        "cgid=arroz_agulha_carolinho-1-1&prefn1=soldInStores&prefv1=000&start={start}&sz=24")


def parse(html: str) -> list[Registo]:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for t in soup.select("div.product-tile[data-gtm-new]"):
        g = json.loads(t["data-gtm-new"])
        venda = t.select_one(".sales .value[content]")
        if not venda:
            continue
        preco = float(venda["content"])
        strike = t.select_one(".strike-through .value[content], del .value[content]")
        pvpr = t.select_one(".pvp-recommended")
        ref = float(strike["content"]) if strike else (euros(pvpr.get_text()) if pvpr else None)
        nome_el = t.select_one(".auc-product-tile__name a")
        nome = nome_el.get_text(" ", strip=True) if nome_el else g["item_name"]
        unit = t.select_one(".auc-measures--price-per-unit")
        out.append(Registo(
            cadeia=CADEIA, id=str(g["item_id"]), nome=nome, marca=g.get("item_brand", ""),
            preco=preco, peso_g=peso_em_gramas(nome),
            eur_kg=eur_kg_de_texto(unit.get_text(" ", strip=True) if unit else ""),
            preco_ref=ref, promo=bool(strike) or bool(ref and ref > preco),
            url=BASE + nome_el["href"] if nome_el else "",
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
        start += 24
    return out
