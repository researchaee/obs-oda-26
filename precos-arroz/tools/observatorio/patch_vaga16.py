"""Vaga 16 (18/11/2026): Painel 7 «Outras culturas».

    python precos-arroz/tools/observatorio/patch_vaga16.py <raiz-do-repositório>

Aplicar depois de patch_vaga15.py.
1. Retira do Painel 7 o quadro de cotações (fica só na página Cotações).
2. A comparação entre culturas passa a usar todas as culturas de crop_comparison.crops
   (arroz, milho, girassol, trigo mole, trigo duro, cevada, aveia, centeio e triticale):
   cores, ícone de substituição para as culturas sem imagem, anos do preço na produção e textos.
3. A página Cotações continua a desenhar as referências FRED/FMI só para as culturas que as têm.

Cada substituição é verificada; se o texto esperado não existir, o script pára sem escrever nada.
"""
import hashlib
import re
import sys
from pathlib import Path


def sub(s: str, antigo: str, novo: str, nome: str, n: int = 1) -> str:
    c = s.count(antigo)
    if c != n:
        raise SystemExit(f"[{nome}] esperava {n} ocorrência(s), encontrei {c}.")
    return s.replace(antigo, novo)


def patch_js(s: str) -> str:
    s = sub(s, "k={rice:D.greenDark,maize:D.amber,sunflower:D.plum}",
            "k={rice:D.greenDark,maize:D.amber,sunflower:D.plum,soft_wheat:D.blue,durum_wheat:D.deficit,"
            "barley:`#6F7470`,oats:`#8C6D1F`,rye:`#5B4B8A`,triticale:`#2E8B85`}", "cores das culturas")
    s = sub(
        s,
        "function L({crop:e,compact:t=!1}){return(0,T.jsx)(`span`,{className:`crop-tech-icon ${t?`compact`:``}`,role:`img`,"
        "\"aria-label\":`Cultura: ${e===`rice`?`arroz`:e===`maize`?`milho`:`girassol`}`,children:(0,T.jsx)(`img`,{src:E(`crop-icon-${e}.png`),alt:``})})}",
        "function L({crop:e,compact:t=!1}){let n={rice:`arroz`,maize:`milho`,sunflower:`girassol`,soft_wheat:`trigo mole`,durum_wheat:`trigo duro`,"
        "barley:`cevada`,oats:`aveia`,rye:`centeio`,triticale:`triticale`}[e]??e;return(0,T.jsx)(`span`,{className:`crop-tech-icon ${t?`compact`:``}`,role:`img`,"
        "\"aria-label\":`Cultura: ${n}`,children:[`rice`,`maize`,`sunflower`].includes(e)?(0,T.jsx)(`img`,{src:E(`crop-icon-${e}.png`),alt:``})"
        ":(0,T.jsx)(`i`,{className:`mz-crop-dot`,style:{background:k[e]??D.grey},children:n.slice(0,1).toUpperCase()})})}",
        "ícone das culturas",
    )
    # Painel 7
    s = sub(s, "(0,T.jsx)(MzMarketQuotes,{records:e.quotes?.market_prices?.records??e.crop_comparison.market_prices.records,country:c}),",
            "", "cotações no Painel 7")
    s = sub(s, "a=Array.from(new Set([`rice`,`maize`,`sunflower`].flatMap(e=>ct(e)))).sort((e,t)=>e-t)",
            "a=Array.from(new Set(t.flatMap(e=>ct(e)))).sort((e,t)=>e-t)", "anos do preço na produção")
    s = sub(s, "text:`É o último ano simultaneamente disponível nas séries harmonizadas de produção e comércio das três culturas.`",
            "text:`É o último ano simultaneamente disponível nas séries harmonizadas de produção e comércio das culturas comparadas.`",
            "ano comum")
    s = sub(s, "As três culturas partilham a mesma escala.", "Todas as culturas partilham a mesma escala.", "escala do comércio")
    s = sub(s, "title:`Arroz, milho e girassol: comparação entre culturas`", "title:`Comparação entre culturas`", "título do Painel 7")
    s = sub(s, "panel:`06 — Arroz, milho e girassol`", "panel:`07 — Outras culturas`", "Excel do Painel 7", 3)
    s = sub(s, "caption:`Milho colhido na União Europeia em ${r}, a maior das três culturas`",
            "caption:`Milho colhido na União Europeia em ${r}`", "cartão da página inicial")
    s = sub(s, "chartLabel:`Comparar as três culturas`", "chartLabel:`Comparar as culturas`", "assistente: comparar", 2)
    s = sub(s, "chartLabel:`Ver o comércio das três culturas`", "chartLabel:`Ver o comércio por cultura`", "assistente: comércio")
    # Cotações: referências FRED/FMI só para culturas com série
    s = sub(s, "b=Object.keys(e.crop_comparison.crops),x=e=>e.split(`-`).reverse().join(`/`)",
            "b=Object.keys(e.crop_comparison.crops).filter(t=>e.crop_comparison.trading.series[t]),x=e=>e.split(`-`).reverse().join(`/`)",
            "séries FRED nas cotações")
    return s


CSS = """
.crop-tech-icon .mz-crop-dot{display:grid;place-items:center;width:100%;height:100%;min-width:28px;min-height:28px;border-radius:50%;color:#fff;font-style:normal;font-weight:700;font-size:13px}
"""


def nome_hash(prefixo: str, conteudo: str, ext: str) -> str:
    return f"{prefixo}-mz{hashlib.sha256(conteudo.encode()).hexdigest()[:8]}.{ext}"


def main():
    raiz = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    site = raiz / "observatorio-maizoryza"
    idx = (site / "index.html").read_text(encoding="utf-8")
    js_antigo = re.search(r"assets/(index-[\w-]+\.js)", idx).group(1)
    css_antigo = re.search(r"assets/(index-[\w-]+\.css)", idx).group(1)
    js = (site / "assets" / js_antigo).read_text(encoding="utf-8")
    if "function MzGrainUnit(" not in js:
        raise SystemExit("Aplicar primeiro patch_vaga15.py.")
    if "mz-crop-dot" in js:
        raise SystemExit("O bundle já tem a vaga 16 aplicada.")
    js = patch_js(js)
    css = (site / "assets" / css_antigo).read_text(encoding="utf-8") + CSS
    js_novo, css_novo = nome_hash("index", js, "js"), nome_hash("index", css, "css")
    (site / "assets" / js_novo).write_text(js, encoding="utf-8")
    (site / "assets" / css_novo).write_text(css, encoding="utf-8")
    for f in (site / "index.html", raiz / "index.html"):
        f.write_text(f.read_text(encoding="utf-8").replace(js_antigo, js_novo).replace(css_antigo, css_novo), encoding="utf-8")
    print(f"JS {js_antigo} -> {js_novo}\nCSS {css_antigo} -> {css_novo}")


if __name__ == "__main__":
    main()
