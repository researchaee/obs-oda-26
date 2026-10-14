"""Intermarché (intermarche.pt) — API JSON da loja online, loja a loja.

Cada Intermarché é de um empresário independente e o preço pode variar entre
lojas. O script:
  1. lista as lojas (API pdvs/zone, raio de 400 km a partir do centro do país);
  2. em cada loja com loja online, pesquisa «arroz» (até 100 produtos por página);
  3. guarda o preço por loja (ficheiro intermarche_lojas.csv) e, por produto,
     a mediana, o mínimo e o máximo entre lojas — a mediana é o preço usado
     na tabela principal.
Lojas sem catálogo online devolvem 404 e são ignoradas.
"""
from __future__ import annotations

import csv
import json
import statistics
import time
from pathlib import Path

from .common import Registo, sessao

CADEIA = "Intermarché"
BASE = "https://www.intermarche.pt/api/service"
CAB = {"Content-Type": "application/json", "x-red-device": "red_fo_desktop", "x-red-version": "3"}
EXCLUIR_RAYON = {"10103", "10104", "10071"}  # animais, cabelo
RAYON_PREPARADOS = {"10115", "11641", "11574"}  # take-away, refeições refrigeradas/congeladas


def lojas(s) -> list[dict]:
    r = s.get(f"{BASE}/pdvs/v4/pdvs/zone?r=400000&lat=39.6&lon=-8.0&min=400",
              headers={**CAB, "x-service-name": "pdvs"}, timeout=30)
    r.raise_for_status()
    return [x for x in r.json()["resultats"] if x.get("ecommerce")]


def pesquisa(s, code: str, termo: str = "arroz") -> list[dict] | None:
    prods = []
    for page in range(1, 6):
        r = s.post(f"{BASE}/produits/v2/pdvs/{code}/products/byKeywordAndCategory",
                   headers={**CAB, "x-service-name": "produits",
                            "x-pdv": json.dumps({"ref": code, "isEcommerce": True})},
                   data=json.dumps({"keyword": termo, "page": page, "size": 100, "filtres": [],
                                    "tri": "pertinence", "ordreTri": "decroissant", "catalog": ["PDV"]}),
                   timeout=30)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        ps = r.json().get("produits") or []
        prods.extend(ps)
        if len(ps) < 100:
            break
        time.sleep(0.5)
    return prods


def recolher(max_lojas: int | None = None, pasta: Path | None = None) -> list[Registo]:
    s = sessao()
    todas = lojas(s)
    if max_lojas:
        todas = todas[:max_lojas]
    meta, precos, linhas_lojas = {}, {}, []
    for loja in todas:
        code = loja["storeCode"]
        prods = pesquisa(s, code)
        time.sleep(0.6)
        if not prods:
            continue
        end = loja["addresses"][0]
        for p in prods:
            if str(p.get("idRayon")) in EXCLUIR_RAYON:
                continue
            if str(p.get("produitEan13", "")).startswith("2"):  # vendidos ao peso (take-away)
                continue
            ean = p["produitEan13"]
            meta.setdefault(ean, p)
            precos.setdefault(ean, []).append(p["prix"])
            linhas_lojas.append([code, end.get("townLabel"), end.get("postCode"),
                                 end.get("latitude"), end.get("longitude"),
                                 ean, p["libelle"], p["prix"], p.get("prixBarre") or ""])
    if pasta:
        with open(pasta / "intermarche_lojas.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["loja", "localidade", "codigo_postal", "lat", "lon", "ean", "produto", "preco", "preco_riscado"])
            w.writerows(linhas_lojas)
    out = []
    for ean, ps in precos.items():
        p = meta[ean]
        nome = p["libelle"] + (f" | {p['conditionnement']}" if p.get("conditionnement") else "")
        out.append(Registo(
            cadeia=CADEIA, id=str(p["itemId"]), ean=ean, nome=nome, marca=p.get("marque") or "",
            preco=round(statistics.median(ps), 2), peso_g=p.get("poidsNet") or None,
            n_lojas=len(ps), preco_min_lojas=min(ps), preco_max_lojas=max(ps),
            nota=f"Preço = mediana entre {len(ps)} lojas",
            preparado=str(p.get("idRayon")) in RAYON_PREPARADOS,
        ))
    return out
