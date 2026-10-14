"""Funções comuns: sessão HTTP, leitura de pesos, classificação e segmentos."""
from __future__ import annotations

import re
import time
import unicodedata
from dataclasses import dataclass, asdict, field
from typing import Optional

import requests

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36 "
    "ObservatorioArroz/1.0 (+https://lsmc-isa.github.io/Observat-rio-do-Arroz/)"
)
PAUSA = 1.0  # segundos entre pedidos ao mesmo site


def sessao() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "pt-PT,pt;q=0.9"})
    return s


def get(s: requests.Session, url: str, **kw) -> requests.Response:
    for tentativa in range(3):
        r = s.get(url, timeout=30, **kw)
        if r.status_code < 500 and r.status_code != 429:
            r.raise_for_status()
            time.sleep(PAUSA)
            return r
        time.sleep(5 * (tentativa + 1))
    r.raise_for_status()
    return r


@dataclass
class Registo:
    """Uma observação de preço (um produto numa cadeia, num dia)."""
    cadeia: str
    id: str
    nome: str
    marca: str
    preco: float                      # preço de venda (€) da embalagem
    peso_g: Optional[float] = None    # peso líquido da embalagem (g)
    eur_kg: Optional[float] = None    # €/kg (do site, ou calculado)
    preco_ref: Optional[float] = None # preço riscado / PVPR, se houver
    promo: bool = False
    ean: str = ""
    url: str = ""
    # Só Intermarché: dispersão entre lojas
    n_lojas: Optional[int] = None
    preco_min_lojas: Optional[float] = None
    preco_max_lojas: Optional[float] = None
    # Preenchidos por classificar()
    tipo: str = ""
    segmento: str = ""
    nota: str = ""
    preparado: bool = False  # pista da própria loja (ex.: secção take-away)

    def dict(self):
        return asdict(self)


# ---------------------------------------------------------------- pesos
_NUM = r"(\d+(?:[.,]\d+)?)"


def _f(x: str) -> float:
    return float(x.replace(",", "."))


def peso_em_gramas(texto: str) -> Optional[float]:
    """Lê o peso total de textos como 'emb. 2 x 125 gr', '1kg+25%', '0.5 Kg', '500g(4x125g)'."""
    if not texto:
        return None
    t = texto.lower().replace("\xa0", " ")
    m = re.search(_NUM + r"\s*kg\s*\+\s*(\d+)\s*%", t)  # 1kg+25%
    if m:
        return _f(m.group(1)) * 1000 * (1 + int(m.group(2)) / 100)
    m = re.search(r"(\d+)\s*x\s*" + _NUM + r"\s*(kg|gr|g)\b", t)  # 2 x 125 gr
    if m and not re.search(_NUM + r"\s*(kg|gr|g)\s*\(", t):
        mult = 1000 if m.group(3) == "kg" else 1
        return int(m.group(1)) * _f(m.group(2)) * mult
    m = re.search(_NUM + r"\s*(kg|kgs|quilos?)\b", t)
    if m:
        return _f(m.group(1)) * 1000
    m = re.search(_NUM + r"\s*(gr|g|grs|gramas)\b", t)
    if m:
        return _f(m.group(1))
    return None


def eur_kg_de_texto(texto: str) -> Optional[float]:
    """'2,36€/kg' ou '1.27 €/Kg' -> 2.36. Devolve None se 0 ou ausente."""
    if not texto:
        return None
    m = re.search(_NUM + r"\s*€\s*/\s*kg", texto.lower())
    if not m:
        return None
    v = _f(m.group(1))
    return v or None


def euros(texto: str) -> Optional[float]:
    if not texto:
        return None
    m = re.search(r"(\d+(?:[.,]\d+)?)", texto.replace("\xa0", " "))
    return _f(m.group(1)) if m else None


# ---------------------------------------------------------------- classificação
def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))


NAO_ARROZ = ["konjac", "flocos", "bulgur", "quinoa", "tortit", "bebida", "farinha",
             "vinagre", "racao", "trinca", "noodles", "crispies", "bolacha", "shampoo"]
PREPARADOS = ["pronto", "minuto", "de pato", "com feijao", "de feijao", "preparado",
              "primavera", "de legumes", "de coentros", "de tomate", "3 delicias",
              "cantones", "risotto de", "risoto de", "risotto com", "risotto pronto",
              "risoto queijo", "risoto 4", "risotto marinheiro", "risotto mediterraneo",
              "4 queijos", "trufa", "cogumelos", "chilli", "marisco"]

# (tipo, palavras-chave) — a ordem conta: o primeiro que bater ganha.
TIPOS = [
    ("Especialidades (selvagem, negro, vermelho)", ["selvagem", "negro", "preto", "vermelho", "pink"]),
    ("Sushi / Poke", ["sushi", "poke"]),
    ("Paelha / Bomba", ["paella", "paelha", "bomba", "calasparra", "valencia"]),
    ("Risotto (arbório, carnaroli)", ["risott", "risoto", "arbori", "arbore", "carnaroli"]),
    ("Integral", ["integral", "complet"]),
    ("Vaporizado / Estufado", ["vaporizado", "estufado", "parboil"]),
    ("Basmati", ["basmati", "brajma"]),
    ("Thai / Jasmim / Aromático", ["thai", "jasmi", "perfumado", "aromatico"]),
    ("Carolino", ["carolino", "calorino", "malandrin", "caldoso", "arroz doce", "para arroz doce"]),
    ("Agulha", ["agulha", "agulhita", "longo", "branqueado", "arroz branco", "europa", "america do sul"]),
]

TIPO_PREPARADO = "Pronto a comer / preparados"

MARCAS_PROPRIAS = {
    "continente", "continente bio", "continente equilibrio", "continente selecao",
    "pingo doce", "pingo doce biologico",
    "auchan", "auchan bio", "auchan cob", "vida auchan cob", "auchan amp",
    "porsi", "porsi bio", "porsi viva bem", "porsi select", "saint eloi",
    "itineraire des saveurs", "intermarche",
    "el corte ingles", "el corte ingles selection",
}
MARCAS_PREMIUM = {
    "riso gallo", "gallo", "scotti", "tilda", "nomen", "esperanza", "la fallera",
    "origens bio", "provida", "uncle ben?s", "uncle ben's", "lal qilla", "seara",
    "terrazza mediterranean", "chef tellini", "keto chef",
}


def classificar(r: Registo) -> Optional[Registo]:
    """Atribui tipo e segmento. Devolve None se o produto não for arroz (ou for sobremesa)."""
    n = _norm(r.nome)
    if any(k in n for k in NAO_ARROZ):
        return None
    if "arroz" not in n and "risot" not in n:
        return None
    if n.startswith("arroz doce") and "especial" not in n and (r.peso_g or 0) < 500:
        return None  # arroz doce já feito (sobremesa), não é arroz cru
    if r.preparado or any(k in n + " " + _norm(r.marca) for k in PREPARADOS):
        r.tipo = TIPO_PREPARADO
    else:
        r.tipo = "Outros"
        for tipo, chaves in TIPOS:
            if any(k in n for k in chaves):
                r.tipo = tipo
                break
    m = _norm(r.marca)
    if m in MARCAS_PROPRIAS:
        r.segmento = "Marca própria"
    elif m in MARCAS_PREMIUM or "bio" in n.split() or "biologic" in n:
        r.segmento = "Premium / Bio"
    else:
        r.segmento = "Marca de fabricante"
    # €/kg final
    if not r.eur_kg and r.peso_g:
        r.eur_kg = round(r.preco / (r.peso_g / 1000), 2)
    if r.eur_kg and (not r.peso_g or abs(r.preco / (r.peso_g / 1000) - r.eur_kg) > 0.05 * r.eur_kg):
        r.peso_g = round(r.preco / r.eur_kg * 1000)  # o €/kg do site manda (ex.: packs 2 x 125 g)
    return r
