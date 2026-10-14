"""Estatísticas (mín., máx., média, mediana de €/kg) por tipo de arroz, cadeia e segmento."""
from __future__ import annotations

import statistics
from collections import defaultdict

TODAS = "Todas as cadeias"
TODOS = "Todos"


def _resumo(vals: list[float]) -> dict:
    return {
        "n": len(vals),
        "min": round(min(vals), 2),
        "max": round(max(vals), 2),
        "media": round(statistics.fmean(vals), 2),
        "mediana": round(statistics.median(vals), 2),
    }


def estatisticas(linhas: list[dict]) -> list[dict]:
    """linhas: dicionários com tipo, cadeia, segmento e eur_kg."""
    grupos = defaultdict(list)
    for r in linhas:
        v = r.get("eur_kg")
        if v in (None, ""):
            continue
        for cad in (r["cadeia"], TODAS):
            for seg in (r["segmento"], TODOS):
                grupos[(r["tipo"], cad, seg)].append(float(v))
    return [{"tipo": t, "cadeia": c, "segmento": s, **_resumo(v)}
            for (t, c, s), v in sorted(grupos.items())]
