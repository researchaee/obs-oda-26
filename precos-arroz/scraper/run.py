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


DIAS_SEM_RECOLHA = 8  # acima disto, uma cadeia sem recolha nova aparece no aviso do painel
_FALHOU = " Recolha de "


def _sem_avisos(nota: str) -> str:
    """Tira avisos de falhas anteriores para não se acumularem semana após semana."""
    return nota.split(_FALHOU)[0].strip() if nota else ""


def gravar(regs: list[Registo], pasta: Path, data: str, erros: dict, corridas: list[str] | None = None) -> None:
    """Grava a recolha de hoje sem apagar as cadeias que não correram nesta execução.

    A recolha está dividida em duas: o GitHub Actions recolhe Continente, Pingo Doce e
    Auchan; o PC recolhe Intermarché e El Corte Inglés (bloqueiam os servidores do GitHub).
    Cada execução só substitui as cadeias que tentou recolher (`corridas`).
    """
    corridas = list(MODULOS) if corridas is None else corridas
    pasta.mkdir(parents=True, exist_ok=True)
    linhas = [{"data": data, **{k: v for k, v in r.dict().items() if k in CAMPOS}} for r in regs]
    nomes_corridos = {MODULOS[k].CADEIA for k in corridas}
    nomes_com_erro = {MODULOS[k].CADEIA for k in erros}
    nomes_ok = {l["cadeia"] for l in linhas}

    # 1. Dashboard: cadeias que não correram ou falharam ficam com a última recolha boa
    anterior = pasta / "latest.json"
    velho = json.loads(anterior.read_text(encoding="utf-8")) if anterior.exists() else {}
    carregadas = []
    for l in velho.get("produtos", []):
        if l["cadeia"] in nomes_ok:
            continue
        l = dict(l)
        l["nota"] = _sem_avisos(l.get("nota") or "")
        if l["cadeia"] in nomes_com_erro:
            l["nota"] = (l["nota"] + f"{_FALHOU}{data} falhou; preço de {l['data']}.").strip()
        carregadas.append(l)
    # Erros: os de hoje + os das cadeias que não correram agora (para não os apagar)
    todos_erros = {k: v for k, v in (velho.get("erros") or {}).items() if k not in corridas}
    todos_erros.update(erros)
    hoje = dt.date.fromisoformat(data)
    for k, mod in MODULOS.items():
        datas = [l["data"] for l in carregadas if l["cadeia"] == mod.CADEIA]
        if k in todos_erros or not datas:
            continue
        ultima = max(datas)
        if (hoje - dt.date.fromisoformat(ultima)).days > DIAS_SEM_RECOLHA:
            todos_erros[k] = f"Sem recolha nova desde {ultima}"

    # 2. Ficheiro do dia: junta as cadeias de hoje às que outra execução já gravou na mesma data
    if linhas:
        dia = pasta / f"precos_arroz_{data}.csv"
        outras = []
        if dia.exists():
            with open(dia, encoding="utf-8") as f:
                outras = [l for l in csv.DictReader(f) if l["cadeia"] not in nomes_corridos]
        with open(dia, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CAMPOS)
            w.writeheader()
            w.writerows(outras)
            w.writerows(linhas)

        # 3. Histórico: só substitui as linhas de hoje das cadeias que correram agora
        hist = pasta / "historico_precos_arroz.csv"
        antigas = []
        if hist.exists():
            with open(hist, encoding="utf-8") as f:
                antigas = [l for l in csv.DictReader(f)
                           if not (l["data"] == data and l["cadeia"] in nomes_corridos)]
        with open(hist, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CAMPOS)
            w.writeheader()
            w.writerows(antigas)
            w.writerows(linhas)

    linhas_dash = linhas + carregadas
    cadeias = sorted({l["cadeia"] for l in linhas_dash})
    (pasta / "latest.json").write_text(json.dumps({
        "data": data,
        "cadeias": cadeias,
        "erros": todos_erros,
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
    if regs or erros:  # mesmo sem produtos, regista os erros para o aviso do painel
        gravar(regs, pasta, data, erros, a.cadeias)
    return 1 if erros and not regs else 0


if __name__ == "__main__":
    raise SystemExit(main())
