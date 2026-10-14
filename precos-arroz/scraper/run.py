"""Recolhe os preços de arroz nas cadeias e grava os ficheiros de dados.

Uso:
    python -m scraper.run                    # todas as cadeias
    python -m scraper.run --cadeias continente auchan
    python -m scraper.run --intermarche-lojas 20   # teste rápido

Saídas (pasta data/):
    precos_arroz_AAAA-MM-DD.csv   todos os produtos do dia, já classificados
    historico_precos_arroz.csv    acumulado de todas as recolhas
    intermarche_lojas.csv         preço por loja do Intermarché (última recolha)
    latest.json                   produtos + estatísticas, lido pelo dashboard
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
import traceback
from pathlib import Path

from . import continente, pingodoce, auchan, intermarche, elcorteingles
from .common import Registo, classificar
from .stats import estatisticas

MODULOS = {
    "continente": continente, "pingodoce": pingodoce, "auchan": auchan,
    "intermarche": intermarche, "elcorteingles": elcorteingles,
}
CAMPOS = ["data", "cadeia", "tipo", "segmento", "marca", "nome", "peso_g", "preco", "eur_kg",
          "preco_ref", "promo", "n_lojas", "preco_min_lojas", "preco_max_lojas", "ean", "id", "url", "nota"]


def gravar(regs: list[Registo], pasta: Path, data: str, erros: dict) -> None:
    pasta.mkdir(parents=True, exist_ok=True)
    linhas = [{"data": data, **{k: v for k, v in r.dict().items() if k in CAMPOS}} for r in regs]
    carregadas = []
    # Cadeias que falharam hoje: mantém no dashboard a última recolha boa (assinalada)
    anterior = pasta / "latest.json"
    if erros and anterior.exists():
        velho = json.loads(anterior.read_text(encoding="utf-8"))
        nomes = {MODULOS[k].CADEIA for k in erros}
        for l in velho.get("produtos", []):
            if l["cadeia"] in nomes:
                l = dict(l)
                l["nota"] = (l.get("nota") or "") + f" Recolha de {data} falhou; preço de {l['data']}."
                carregadas.append(l)
    with open(pasta / f"precos_arroz_{data}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows(linhas)
    hist = pasta / "historico_precos_arroz.csv"
    novo = not hist.exists()
    if not novo:  # não duplicar a mesma data
        with open(hist, encoding="utf-8") as f:
            antigas = [l for l in csv.DictReader(f) if l["data"] != data]
    with open(hist, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        if not novo:
            w.writerows(antigas)
        w.writerows(linhas)
    linhas_dash = linhas + carregadas
    cadeias = sorted({l["cadeia"] for l in linhas_dash})
    (pasta / "latest.json").write_text(json.dumps({
        "data": data,
        "cadeias": cadeias,
        "erros": erros,
        "produtos": linhas_dash,
        "estatisticas": estatisticas(linhas_dash),
    }, ensure_ascii=False, indent=1), encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cadeias", nargs="*", default=list(MODULOS))
    ap.add_argument("--intermarche-lojas", type=int, default=None)
    ap.add_argument("--pasta", default="data")
    a = ap.parse_args(argv)
    pasta = Path(a.pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    data = dt.date.today().isoformat()
    regs, erros = [], {}
    for nome in a.cadeias:
        try:
            if nome == "intermarche":
                brutos = intermarche.recolher(a.intermarche_lojas, pasta)
            else:
                brutos = MODULOS[nome].recolher()
            ok = [r for r in (classificar(b) for b in brutos) if r]
            print(f"{nome}: {len(brutos)} produtos, {len(ok)} de arroz", file=sys.stderr)
            if not ok:
                raise RuntimeError("nenhum produto recolhido (o site pode ter mudado ou bloqueado o pedido)")
            regs.extend(ok)
        except Exception as e:  # uma cadeia a falhar não impede as outras
            erros[nome] = f"{type(e).__name__}: {e}"
            traceback.print_exc()
    if regs:
        gravar(regs, pasta, data, erros)
    return 1 if erros and not regs else 0


if __name__ == "__main__":
    raise SystemExit(main())
