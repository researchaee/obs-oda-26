"""Vaga 17 (18/11/2026): filtro de culturas nos três gráficos do Painel 7.

    python precos-arroz/tools/observatorio/patch_vaga17.py <raiz-do-repositório>

Aplicar depois de patch_vaga16.py. Cada gráfico (produção, comércio e preço na produção) ganha
uma fila de botões «Culturas»: «Todas» repõe todas; com todas ativas, clicar numa cultura mostra
só essa; depois, cada clique junta ou retira culturas (fica sempre pelo menos uma). O Excel de
cada gráfico segue a seleção.
"""
import hashlib
import re
import sys
from pathlib import Path

PICK = (
    "function MzCropPick({crops:e,labels:t,render:n}){let[r,i]=(0,l.useState)(null),a=(r??e).filter(t=>e.includes(t));"
    "a.length||(a=e);let o=a.length===e.length,s=(0,T.jsxs)(`div`,{className:`country-chips mz-crop-chips`,role:`group`,"
    "\"aria-label\":`Culturas no gráfico`,children:[(0,T.jsx)(`span`,{children:`Culturas`}),(0,T.jsx)(`button`,{type:`button`,"
    "\"aria-pressed\":o,className:o?`active`:``,onClick:()=>i(null),children:`Todas`}),...e.map(e=>{let n=a.includes(e);"
    "return(0,T.jsx)(`button`,{type:`button`,\"aria-pressed\":n&&!o,className:n&&!o?`active`:``,style:{\"--chip-color\":k[e]??D.grey},"
    "onClick:()=>i(o?[e]:n?a.length>1?a.filter(t=>t!==e):a:[...a,e]),children:t[e]??e},e)})]});return n(a,s)}\n"
)


def sub(s, antigo, novo, nome, n=1):
    c = s.count(antigo)
    if c != n:
        raise SystemExit(f"[{nome}] esperava {n} ocorrência(s), encontrei {c}.")
    return s.replace(antigo, novo)


def call_end(s: str, start: int) -> int:
    """Índice a seguir ao ')' que fecha a chamada que começa em s[start] == '('.
    Percorre parênteses ignorando strings e literais de template (com ${...} encaixados)."""
    assert s[start] == "("
    depth = 0
    i = start
    stack = []  # contexto: 'code' ou 'tpl'
    mode = "code"
    while i < len(s):
        ch = s[i]
        if mode == "tpl":
            if ch == "\\":
                i += 2
                continue
            if ch == "`":
                mode = stack.pop()
            elif ch == "$" and s[i + 1] == "{":
                stack.append("tpl")
                stack.append("brace")
                mode = "code"
                i += 2
                continue
            i += 1
            continue
        if ch in "\"'":
            j = i + 1
            while s[j] != ch:
                j += 2 if s[j] == "\\" else 1
            i = j + 1
            continue
        if ch == "`":
            stack.append("code")
            mode = "tpl"
        elif ch == "{":
            stack.append("{")
        elif ch == "}":
            top = stack.pop()
            if top == "brace":
                mode = stack.pop()
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise SystemExit("Fim da chamada não encontrado.")


def wrap_section(s, sec_id, prelude, crops_expr, key):
    marker = f"(0,T.jsxs)(`section`,{{className:`visual-card`,id:`{sec_id}`,children:["
    if s.count(marker) != 1:
        raise SystemExit(f"[{sec_id}] secção não encontrada.")
    start = s.index(marker)
    end = call_end(s, start + len("(0,T.jsxs)"))
    section = s[start:end]
    head_marker = "(0,T.jsxs)(`div`,{className:`visual-head`,"
    hs = section.index(head_marker)
    he = call_end(section, hs + len("(0,T.jsxs)"))
    section = section[:he] + ",MzChips" + section[he:]
    wrapped = (
        f"(0,T.jsx)(MzCropPick,{{crops:{crops_expr},labels:MzCL,render:(q,MzChips)=>{{{prelude}return {section}}}}},`{key}`)"
    )
    return s[:start] + wrapped + s[end:]


def patch_js(s: str) -> str:
    s = sub(s, "function _e({rows:e,valueLabel:t,onPick:n}){", PICK + "function _e({rows:e,valueLabel:t,onPick:n}){", "componente do filtro")
    # séries com a chave da cultura
    s = sub(s, "let n=t.map(t=>({name:e.crop_comparison.crops[t].label,color:k[t],points:e.crop_comparison.production.filter(",
            "let n=t.map(t=>({crop:t,name:e.crop_comparison.crops[t].label,color:k[t],points:e.crop_comparison.production.filter(",
            "séries de produção")
    s = sub(s, "s=t.map(t=>({name:e.crop_comparison.crops[t].label,color:k[t],points:a.map(e=>({x:e,y:st(c,e,t)}))})).filter(e=>e.points.some(e=>e.y!=null));return(0,T.jsxs)(T.Fragment,{children:[(0,T.jsx)(pe,{page:`crops`,",
            "s=t.map(t=>({crop:t,name:e.crop_comparison.crops[t].label,color:k[t],points:a.map(e=>({x:e,y:st(c,e,t)}))})).filter(e=>e.points.some(e=>e.y!=null));"
            "let MzA1=n,MzA2=r,MzA3=s,MzCL=Object.fromEntries(t.map(t=>[t,e.crop_comparison.crops[t].label]));"
            "return(0,T.jsxs)(T.Fragment,{children:[(0,T.jsx)(pe,{page:`crops`,",
            "séries de preço")
    s = wrap_section(s, "crop-evolution", "let n=MzA1.filter(e=>q.includes(e.crop));", "t", "mz-crop-evolution")
    s = wrap_section(s, "crop-trade",
                     "let r=MzA2.filter(e=>q.includes(e.crop)),i=Math.max(...r.flatMap(e=>[e.imports??0,e.exports??0]),1);",
                     "t", "mz-crop-trade")
    s = wrap_section(s, "crop-producer-prices", "let s=MzA3.filter(e=>q.includes(e.crop));",
                     "MzA3.map(e=>e.crop)", "mz-crop-prices")
    s = sub(s, "Todas as culturas partilham a mesma escala.", "As culturas escolhidas partilham a mesma escala.", "nota da escala")
    return s


CSS = "\n.mz-crop-chips{margin:4px 0 16px}\n"


def nome_hash(prefixo, conteudo, ext):
    return f"{prefixo}-mz{hashlib.sha256(conteudo.encode()).hexdigest()[:8]}.{ext}"


def main():
    raiz = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    site = raiz / "observatorio-maizoryza"
    idx = (site / "index.html").read_text(encoding="utf-8")
    js_antigo = re.search(r"assets/(index-[\w-]+\.js)", idx).group(1)
    css_antigo = re.search(r"assets/(index-[\w-]+\.css)", idx).group(1)
    js = (site / "assets" / js_antigo).read_text(encoding="utf-8")
    if "mz-crop-dot" not in js:
        raise SystemExit("Aplicar primeiro patch_vaga16.py.")
    if "function MzCropPick(" in js:
        raise SystemExit("O bundle já tem a vaga 17 aplicada.")
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
