"""Vaga 19 (19/11/2026): filtros de país e de variedade no Painel 1, gráfico 04 (área por variedade).

    python precos-arroz/tools/observatorio/patch_vaga19.py <raiz-do-repositório>

Aplicar depois de patch_vaga18.py. Por baixo do título do gráfico 04 ficam, lado a lado, duas listas:
«País» (Portugal, Itália, Espanha) e «Variedade» («Todas» ou uma variedade). A variedade escolhida
filtra a tabela e o Excel; ao mudar de país, a variedade volta a «Todas». O filtro de país deixa de
estar nos botões do canto superior direito.

Também reescreve a explicação do «i» do cartão «Importações de arroz» (Painel 1), com a fonte, o código NC,
a unidade e o âmbito (Estados-Membros com comércio total, UE só extra-UE), em vez de o corrigir por script
no index.html.

No Painel 3, o «i» do cartão «Importações líquidas» passa a ter uma definição mais simples para quem não
é do setor, mantendo o rigor técnico.
"""
import hashlib
import re
import sys
from pathlib import Path

PICK = "function MzVarietyPick({render:n}){let[r,i]=(0,l.useState)(null);return n(r,i)}\n"

SEGMENTED = (
    "(0,T.jsx)(`div`,{className:`segmented-control`,\"aria-label\":`País das variedades`,children:[`PT`,`IT`,`ES`]"
    ".filter(t=>e.crop_comparison.rice_varieties.countries[t]).map(t=>(0,T.jsx)(`button`,{className:x===t?`active`:``,"
    "onClick:()=>S(t),children:e.crop_comparison.rice_varieties.countries[t]},t))}),"
)

FILTERS = (
    ",(0,T.jsxs)(`div`,{className:`mz-variety-filters`,role:`group`,\"aria-label\":`Filtros do gráfico de variedades`,children:["
    "(0,T.jsxs)(`label`,{className:`inline-select`,children:[`País`,(0,T.jsx)(`select`,{value:x,"
    "onChange:ev=>{S(ev.target.value);MzSetV(null)},children:[`PT`,`IT`,`ES`].filter(t=>e.crop_comparison.rice_varieties.countries[t])"
    ".map(t=>(0,T.jsx)(`option`,{value:t,children:e.crop_comparison.rice_varieties.countries[t]},t))})]}),"
    "(0,T.jsxs)(`label`,{className:`inline-select`,children:[`Variedade`,(0,T.jsx)(`select`,{value:MzQ??``,"
    "onChange:ev=>MzSetV(ev.target.value||null),children:[(0,T.jsx)(`option`,{value:``,children:`Todas`},`__todas`),"
    "...k.map(t=>(0,T.jsx)(`option`,{value:t.name,children:t.name},t.name))]})]})]})"
)

PRELUDE = (
    "let MzQ=q!=null&&k.some(t=>t.name===q)?q:null,MzKs=MzQ==null?k:k.filter(t=>t.name===MzQ),"
    "MzAs=Array.from(new Set(MzKs.flatMap(t=>t.points.map(t=>t.x)))).sort((t,n)=>t-n);"
)

IMPORT_INFO_OLD = (
    "info:`Indicador de mercado, não de produção: o Eurostat não publica produção mensal. A linha mensal mostra "
    "as importações do Comext no mês escolhido, para acompanhar o mercado entre colheitas.`"
)
IMPORT_INFO_NEW = (
    "info:`Indicador de comércio externo, não de produção. As estatísticas de produção agrícola do Eurostat são "
    "anuais, por isso não existe produção mensal. O valor principal é o total anual das importações de arroz "
    "(código NC 1006, que inclui arroz em casca, descascado, branqueado e trincas), em euros correntes, com o peso "
    "líquido indicado por baixo. A linha mensal mostra o valor importado no mês escolhido em «Mês nos cartões» e a "
    "variação face ao mesmo mês do ano anterior. Para cada Estado-Membro conta o comércio total declarado, dentro e "
    "fora da UE. Para a União Europeia conta só o comércio extra-UE, para não somar duas vezes as trocas entre "
    "Estados-Membros. Os meses mais recentes são provisórios e podem ser revistos. Fonte: Eurostat Comext, quadro "
    "DS-045409.`"
)

NET_INFO_OLD = (
    "info:`É a parte do consumo aparente que vem do comércio externo. Valores negativos indicam que o país "
    "exporta mais arroz do que importa.`"
)
NET_INFO_NEW = (
    "info:`Quanto arroz o país compra ao estrangeiro a mais do que vende (importações menos exportações, em toneladas, todo o arroz NC 1006). Se for negativo, vende mais do que compra. Fonte: Eurostat Comext.`"
)

CSS = "\n.mz-variety-filters{display:flex;flex-wrap:wrap;gap:12px 28px;margin:4px 0 14px}\n"


def sub(s, antigo, novo, nome, n=1):
    c = s.count(antigo)
    if c != n:
        raise SystemExit(f"[{nome}] esperava {n} ocorrência(s), encontrei {c}.")
    return s.replace(antigo, novo)


def call_end(s: str, start: int) -> int:
    """Índice a seguir ao ')' que fecha a chamada que começa em s[start] == '('."""
    assert s[start] == "("
    depth, i, stack, mode = 0, start, [], "code"
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


def patch_js(s: str) -> str:
    s = sub(s, NET_INFO_OLD, NET_INFO_NEW, "explicação das importações líquidas")
    s = sub(s, IMPORT_INFO_OLD, IMPORT_INFO_NEW, "explicação das importações")
    s = sub(s, "function MzCropPick(", PICK + "function MzCropPick(", "componente do filtro")
    marker = "(0,T.jsxs)(`section`,{className:`visual-card`,id:`production-varieties`,children:["
    if s.count(marker) != 1:
        raise SystemExit("[production-varieties] secção não encontrada.")
    start = s.index(marker)
    end = call_end(s, start + len("(0,T.jsxs)"))
    section = s[start:end]
    section = sub(section, SEGMENTED, "", "filtro de país antigo")
    head_marker = "(0,T.jsxs)(`div`,{className:`visual-head`,"
    hs = section.index(head_marker)
    he = call_end(section, hs + len("(0,T.jsxs)"))
    section = section[:he] + FILTERS + section[he:]
    # colunas e campanhas passam a seguir a variedade escolhida; a lista de opções mantém todas
    section = section.replace("...k.map(t=>(0,T.jsx)(`option`", "...MZALL(t=>(0,T.jsx)(`option`")
    for nome, antigo, novo, n in (("colunas", "k.map(", "MzKs.map(", 4), ("campanhas", "A.map(", "MzAs.map(", 2)):
        padrao = r"(?<![\w$])(?<![\w$]\.)" + re.escape(antigo)
        c = len(re.findall(padrao, section))
        if c != n:
            raise SystemExit(f"[{nome}] esperava {n} ocorrência(s), encontrei {c}.")
        section = re.sub(padrao, novo, section)
    section = section.replace("...MZALL(t=>(0,T.jsx)(`option`", "...k.map(t=>(0,T.jsx)(`option`")
    wrapped = f"(0,T.jsx)(MzVarietyPick,{{render:(q,MzSetV)=>{{{PRELUDE}return {section}}}}},`mz-varieties`)"
    return s[:start] + wrapped + s[end:]


def nome_hash(conteudo, ext):
    return f"index-mz{hashlib.sha256(conteudo.encode()).hexdigest()[:8]}.{ext}"


def main():
    raiz = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    site = raiz / "observatorio-maizoryza"
    idx = (site / "index.html").read_text(encoding="utf-8")
    js_antigo = re.search(r"assets/(index-[\w-]+\.js)", idx).group(1)
    css_antigo = re.search(r"assets/(index-[\w-]+\.css)", idx).group(1)
    js = (site / "assets" / js_antigo).read_text(encoding="utf-8")
    if "`./crop-icon-${e}.svg`" not in js:
        raise SystemExit("Aplicar primeiro patch_vaga18.py.")
    if "function MzVarietyPick(" in js:
        raise SystemExit("O bundle já tem a vaga 19 aplicada.")
    js = patch_js(js)
    css = (site / "assets" / css_antigo).read_text(encoding="utf-8") + CSS
    js_novo, css_novo = nome_hash(js, "js"), nome_hash(css, "css")
    (site / "assets" / js_novo).write_text(js, encoding="utf-8", newline="\n")
    (site / "assets" / css_novo).write_text(css, encoding="utf-8", newline="\n")
    for f in (site / "index.html", raiz / "index.html"):
        html = f.read_text(encoding="utf-8")
        if js_antigo not in html or css_antigo not in html:
            raise SystemExit(f"{f} não aponta para o bundle esperado.")
        f.write_text(html.replace(js_antigo, js_novo).replace(css_antigo, css_novo), encoding="utf-8")
    print(f"JS {js_antigo} -> {js_novo}\nCSS {css_antigo} -> {css_novo}")


if __name__ == "__main__":
    main()
