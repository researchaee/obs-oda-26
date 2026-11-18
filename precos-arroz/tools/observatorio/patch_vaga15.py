"""Vaga 15 (18/11/2026): alterações aplicadas ao bundle já construído do observatório.

    python precos-arroz/tools/observatorio/patch_vaga15.py <raiz-do-repositório>

1. Gráficos de grãos (Painel 1 gráfico 02 e Painel 3 gráfico 02): cada grão passa a valer uma
   quantidade redonda (1, 2, 2,5 ou 5 × 10^n), o último grão aparece cortado na fração certa e
   a legenda mostra o grão e o que equivale.
2. Painel 1 gráfico 04: acrescenta Espanha (Sevilha), em percentagem da área semeada (RAIF).
3. Painel 5 «Cotações»: a lista de países inclui todos os Estados-Membros com cotações da DG AGRI
   e o quadro de cereais e girassol usa a versão nova de mz_market_quotes.js.

Cada substituição é verificada; se o texto esperado não existir, o script pára sem escrever nada.
Os ficheiros novos ganham um nome com hash e os dois index.html passam a apontar para eles.
"""
import hashlib
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def sub1(s: str, antigo: str, novo: str, nome: str) -> str:
    n = s.count(antigo)
    if n != 1:
        raise SystemExit(f"[{nome}] esperava 1 ocorrência, encontrei {n}. Bundle diferente do esperado?")
    return s.replace(antigo, novo)


GRAIN_UNIT = (
    "function MzGrainUnit(v){let m=Math.max(0,...v.map(e=>Math.abs(e??0)));if(!(m>0))return 1;"
    "let r=m/30,p=Math.pow(10,Math.floor(Math.log10(r))),f=r/p;return[1,2,2.5,5,10].find(e=>f<=e+1e-9)*p}"
    "function MzGrainKey(){return(0,T.jsx)(`i`,{className:`mz-grain-key`,\"aria-hidden\":!0})}\n"
)

OLD_GRAIN = (
    "function _e({rows:e,valueLabel:t,onPick:n}){let r=Math.max(...e.map(e=>Math.abs(e.value)),1);"
    "return e.length?(0,T.jsx)(`div`,{className:`grain-list`,children:e.map((e,i)=>{let a=Math.max(1,Math.round(Math.abs(e.value)/r*30));"
)
NEW_GRAIN = (
    "function _e({rows:e,valueLabel:t,onPick:n}){let r=MzGrainUnit(e.map(e=>e.value));"
    "return e.length?(0,T.jsx)(`div`,{className:`grain-list`,children:e.map((e,i)=>{let q=Math.abs(e.value)/r,a=Math.floor(q+1e-9),pf=q-a;"
)
OLD_TRACK = (
    "(0,T.jsx)(`span`,{className:`grain-track`,\"aria-label\":`${a} grãos numa escala máxima de 30`,"
    "children:Array.from({length:a},(e,t)=>(0,T.jsx)(`i`,{},t))})"
)
NEW_TRACK = (
    "(0,T.jsx)(`span`,{className:`grain-track`,\"aria-label\":`${t(e.value)}: cada grão equivale a ${t(r)}`,"
    "children:[...Array.from({length:a},(e,t)=>(0,T.jsx)(`i`,{},t)),...(pf>.02||a===0&&q>0?[(0,T.jsx)(`i`,"
    "{className:`mz-grain-part`,style:{clipPath:`inset(0 ${Math.round((1-Math.max(pf,.2))*100)}% 0 0)`}},`p`)]:[])]})"
)

# legenda do Painel 1, gráfico 02
OLD_LEG1 = (
    "(0,T.jsx)(z,{note:`Clique num país para o acrescentar ao gráfico de evolução.`,children:(0,T.jsxs)(`span`,"
    "{children:[(0,T.jsx)(`i`,{style:{background:D.greenDark}}),j[_].short,` em `,o,` (`,j[_].unit,`)`]})})"
)
NEW_LEG1 = (
    "(0,T.jsx)(z,{note:`${j[_].short} em ${o} (${j[_].unit}). O último grão de cada país aparece cortado na fração que lhe "
    "corresponde. Clique num país para o acrescentar ao gráfico de evolução.`,children:(0,T.jsxs)(`span`,{className:`mz-grain-legend`,"
    "children:[MzGrainKey(),`1 grão = ${F(MzGrainUnit(C.map(e=>e[_]??0)),_)}`]})})"
)
# legenda do Painel 3, gráfico 02
OLD_LEG3 = (
    "(0,T.jsx)(z,{children:(0,T.jsxs)(`span`,{children:[(0,T.jsx)(`i`,{style:{background:p===`M`?te:ne}}),"
    "e.trade.flows[p],` de `,e.trade.rice_codes[d].toLowerCase(),` em `,xt,`, em milhões de euros`]})})"
)
NEW_LEG3 = (
    "(0,T.jsx)(z,{note:`${e.trade.flows[p]} de ${e.trade.rice_codes[d].toLowerCase()} em ${xt}, em milhões de euros. "
    "O último grão de cada país aparece cortado na fração que lhe corresponde.`,children:(0,T.jsxs)(`span`,"
    "{className:`mz-grain-legend`,children:[MzGrainKey(),`1 grão = ${Ze(MzGrainUnit(wt(p).map(e=>e.value)))}`]})})"
)


def patch_grains(s: str) -> str:
    s = sub1(s, "function _e({rows:e,valueLabel:t,onPick:n}){", GRAIN_UNIT + "function _e({rows:e,valueLabel:t,onPick:n}){", "funções dos grãos")
    s = sub1(s, OLD_GRAIN, NEW_GRAIN, "escala dos grãos")
    s = sub1(s, OLD_TRACK, NEW_TRACK, "desenho dos grãos")
    s = sub1(s, OLD_LEG1, NEW_LEG1, "legenda Painel 1 gráfico 02")
    s = sub1(s, OLD_LEG3, NEW_LEG3, "legenda Painel 3 gráfico 02")
    return s


def patch_varieties(s: str) -> str:
    s = sub1(
        s,
        "ne=E.filter(e=>e.year===te).sort((e,t)=>t.area_ha-e.area_ha).slice(0,6),",
        "ne=E.filter(e=>e.year===te).sort((e,t)=>(t.area_ha??t.share_pct)-(e.area_ha??e.share_pct)).slice(0,6),MzPct=x===`ES`,",
        "ordem das variedades",
    )
    s = sub1(
        s,
        "points:E.filter(t=>t.variety===e.variety&&t.group===e.group).sort((e,t)=>e.year-t.year).map(e=>({x:e.year,y:e.area_ha,note:e.group}))",
        "points:E.filter(t=>t.variety===e.variety&&t.group===e.group).sort((e,t)=>e.year-t.year).map(e=>({x:e.year,y:e.area_ha??e.share_pct,note:e.group}))",
        "pontos das variedades",
    )
    s = sub1(
        s,
        "children:`Área de arroz por variedade em ${e.crop_comparison.rice_varieties.countries[x]}`",
        "children:MzPct?`Área semeada de arroz por variedade (%) em ${e.crop_comparison.rice_varieties.countries[x]}`:`Área de arroz por variedade em ${e.crop_comparison.rice_varieties.countries[x]}`",
        "título das variedades",
    )
    s = sub1(
        s,
        "children:[`PT`,`IT`].map(t=>(0,T.jsx)(`button`,{className:x===t?`active`:``,onClick:()=>S(t),children:e.crop_comparison.rice_varieties.countries[t]},t))",
        "children:[`PT`,`IT`,`ES`].filter(t=>e.crop_comparison.rice_varieties.countries[t]).map(t=>(0,T.jsx)(`button`,{className:x===t?`active`:``,onClick:()=>S(t),children:e.crop_comparison.rice_varieties.countries[t]},t))",
        "botões das variedades",
    )
    s = sub1(
        s,
        "headers:[`Campanha`,...k.map(e=>`${e.name} (ha)`)]",
        "headers:[`Campanha`,...k.map(e=>`${e.name} (${MzPct?`% da área semeada`:`ha`})`)]",
        "Excel das variedades",
    )
    s = sub1(
        s,
        "(0,T.jsx)(me,{series:k,valueLabel:e=>`${N(e,0)} ha`,height:470,endLabels:!0,xTitle:`Campanha`,yTitle:`Área declarada (ha)`})",
        "(0,T.jsx)(me,{series:k,valueLabel:e=>MzPct?`${N(e,1)}%`:`${N(e,0)} ha`,height:470,endLabels:!0,xTitle:`Campanha`,yTitle:MzPct?`Área semeada (%)`:`Área declarada (ha)`})",
        "eixo das variedades",
    )
    # Assistente IA
    s = sub1(
        s,
        "let t=d===`IT`?`IT`:d===`PT`?`PT`:null;if(!t)return{text:`As áreas por variedade só existem para Portugal (IFAP) e Itália (CREA). Para os outros países não há série oficial comparável, e o observatório não estima variedades.`",
        "let t=d===`IT`?`IT`:d===`PT`?`PT`:d===`ES`?`ES`:null;if(!t)return{text:`As áreas por variedade existem para Portugal (IFAP) e Itália (Ente Nazionale Risi), e para a província de Sevilha em percentagem da área semeada (RAIF). Para os outros países não há série oficial comparável, e o observatório não estima variedades.`",
        "assistente: países das variedades",
    )
    s = sub1(
        s,
        "i=n.filter(e=>e.year===r).sort((e,t)=>t.area_ha-e.area_ha).slice(0,3);return S(t),{text:`Em ${r},",
        "i=n.filter(e=>e.year===r).sort((e,t)=>(t.area_ha??t.share_pct)-(e.area_ha??e.share_pct)).slice(0,3);return S(t),t===`ES`?{text:`Em ${r}, as variedades mais semeadas na província de Sevilha foram ${i.map(e=>`${e.variety} (${N(e.share_pct,1)}% da área)`).join(`, `)}.`,note:`${i[0].source}. Percentagem da área semeada publicada no boletim final da campanha; não há área em hectares nem produção por variedade.`,page:`production`,chartId:`production-varieties`,chartLabel:`Ver a evolução das variedades`,filters:O(`Espanha (Sevilha)`,`Área por variedade`)}:{text:`Em ${r},",
        "assistente: resposta das variedades",
    )
    return s


def patch_quotes(s: str) -> str:
    # componente novo
    start = s.index("var MzQuoteCropLabels = {")
    end = s.index("function pe({page:e,children:t}){", start)
    componente = (AQUI / "mz_market_quotes.js").read_text(encoding="utf-8").strip()
    s = s[:start] + componente + "\n" + s[end:]
    # países com cotações da DG AGRI na lista do Painel 5
    s = sub1(
        s,
        "ge=[`PT`,`ES`,`IT`,`EL`,`FR`,`BG`,`RO`].filter(e=>L?.rows.some(t=>t[0]===e)||e===`ES`&&(s.length||ce||w||A)||e===`IT`&&f.length)",
        "ge=Array.from(new Set([`PT`,`ES`,`IT`,`EL`,`FR`,`BG`,`RO`,...Object.keys(MzCountryPT)])).filter(e=>L?.rows.some(t=>t[0]===e)||e===`ES`&&(s.length||ce||w||A)||e===`IT`&&f.length||MzHasEuQuotes(t,e))",
        "lista de países das cotações",
    )
    s = sub1(
        s,
        "_e&&C?.cme?`cme`:``,_e?`fred`:``].filter(Boolean)",
        "_e&&C?.cme?`cme`:``,_e?`fred`:``,!_e&&MzHasEuQuotes(t,Ee)?`dgagri`:``].filter(Boolean)",
        "contagem de fontes das cotações",
    )
    s = sub1(
        s,
        "Re=t=>t===`WORLD`?`Mercados mundiais`:e.production.countries[t]??t,",
        "Re=t=>t===`WORLD`?`Mercados mundiais`:e.production.countries[t]??MzCountryPT[t]??t,",
        "nome do país nas cotações",
    )
    s = sub1(
        s,
        "Ct=(t,n=t=>e?.production.countries[t]??t)=>",
        "Ct=(t,n=t=>e?.production.countries[t]??MzCountryPT[t]??t)=>",
        "nomes dos países nas listas",
    )
    return s


CSS = """
.grain-track i.mz-grain-part{flex:none}
.mz-grain-legend{display:inline-flex;align-items:center;gap:8px;font-weight:700}
.chart-legend .mz-grain-legend i.mz-grain-key,.mz-grain-legend i.mz-grain-key{background:linear-gradient(135deg,#fff9db,#dfca8d)!important;border:1px solid #b89c5a;border-radius:80% 20%;width:14px!important;height:7px!important;display:inline-block;transform:rotate(-17deg);box-shadow:inset -2px -1px 2px #664c1826}
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
    if "function MzGrainUnit(" in js:
        raise SystemExit("O bundle já tem a vaga 15 aplicada.")
    js = patch_quotes(patch_varieties(patch_grains(js)))
    css = (site / "assets" / css_antigo).read_text(encoding="utf-8")
    old = css.find(".dashboard-main{grid-template-columns:minmax(0,1fr)}")
    if old >= 0:
        css = css[:old].rstrip() + "\n" + (AQUI / "mz_market_quotes.css").read_text(encoding="utf-8").strip()
    css += CSS
    js_novo, css_novo = nome_hash("index", js, "js"), nome_hash("index", css, "css")
    (site / "assets" / js_novo).write_text(js, encoding="utf-8")
    (site / "assets" / css_novo).write_text(css, encoding="utf-8")
    for f in (site / "index.html", raiz / "index.html"):
        f.write_text(f.read_text(encoding="utf-8").replace(js_antigo, js_novo).replace(css_antigo, css_novo), encoding="utf-8")
    print(f"JS {js_antigo} -> {js_novo}\nCSS {css_antigo} -> {css_novo}")


if __name__ == "__main__":
    main()
