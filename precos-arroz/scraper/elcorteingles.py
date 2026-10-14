"""El Corte Inglés (elcorteingles.pt/supermercado) — Mercearia > Massas, arroz… > Arroz.

Páginas HTML renderizadas no servidor: /arroz/1/, /arroz/2/, … (20 produtos por
página). O nome vem como «Produto  Marca» (dois espaços antes da marca).
"""
import re

from bs4 import BeautifulSoup

from .common import Registo, sessao, get, peso_em_gramas, eur_kg_de_texto, euros

CADEIA = "El Corte Inglés"
BASE = "https://www.elcorteingles.pt"
PAG = BASE + "/supermercado/mercearia/massas-arroz-farinhas-e-legumes-secos/arroz/{p}/"


def parse(html: str) -> list[Registo]:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for li in soup.select('li[data-type="item"]'):
        a = li.select_one(".food-product-preview-responsive__description")
        if not a:
            continue
        href = a.get("href", "")
        texto = a.get_text()
        if "  " in texto:
            nome, marca = [x.strip() for x in texto.rsplit("  ", 1)]
        else:
            nome, marca = texto.strip(), ""
        offer = li.select_one(".food-prices__offer")
        price = offer or li.select_one(".food-prices__price")
        orig = li.select_one(".food-prices__price--original")
        preco = euros(price.get_text()) if price else None
        if preco is None:
            continue
        venda = li.select_one(".food-product-preview-responsive__sale_type")
        peso = peso_em_gramas(venda.get_text(" ", strip=True) if venda else "") \
            or peso_em_gramas(href.replace("-", " "))
        unit = li.select_one(".food-prices__measurement-unit")
        m = re.search(r"B(\d+)", href)
        out.append(Registo(
            cadeia=CADEIA, id=m.group(1) if m else href, nome=nome, marca=marca,
            preco=preco, peso_g=peso,
            eur_kg=eur_kg_de_texto(unit.get_text(" ", strip=True) if unit else ""),
            preco_ref=euros(orig.get_text()) if orig else None, promo=bool(offer),
            url=BASE + href,
        ))
    return out


def recolher() -> list[Registo]:
    s = sessao()
    vistos, out = set(), []
    for p in range(1, 15):
        regs = [r for r in parse(get(s, PAG.format(p=p)).text) if r.id not in vistos]
        if not regs:
            break
        vistos.update(r.id for r in regs)
        out.extend(regs)
    return out
