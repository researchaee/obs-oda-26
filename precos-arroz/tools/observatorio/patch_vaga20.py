"""Vaga 20 (20/11/2026): pedidos da revisão no artifact (comentários de 20/11), passados para o bundle.

    python precos-arroz/tools/observatorio/patch_vaga20.py <raiz-do-repositório>

Aplicar depois de patch_vaga19.py. Faz no código o que até aqui estava remendado por script ou CSS no
index.html, e acrescenta o que faltava:

1. Tabelas ordenáveis por clique no cabeçalho (▲ ascendente, ▼ descendente): produtos do retalho
   (Painel 4, gráfico 03) e variedades de Portugal, Itália e Espanha (Painel 1, gráfico 04). Números,
   preços e percentagens ordenam como números; texto por ordem alfabética. Sai o botão «Ordenar por».
2. Painel 7: «Ano comum» passa a «Último ano disponível».
3. Cabeçalho de todos os gráficos: título numa linha, com o «i» e o botão do Excel logo a seguir;
   os filtros passam para a linha de baixo (componente MzHead).
4. (vem com o 3) os filtros ficam por baixo do título, que ganha a largura toda.
5. Painel 5 (Cotações): filtro «Cultura» junto ao «País», ambos no painel lateral «Filtros». Esconde os quadros sem essa cultura e filtra
   as linhas e séries dos quadros com várias culturas (MAPA, Lonja de Sevilla, FRED/FMI, DG AGRI).
6. «EUR» passa a «€» em todo o painel, incluindo os textos que vêm do observatory-data.json e os
   ficheiros Excel (exceto códigos de moeda e endereços).
7. Painel 4, gráfico 02: a nota sai do topo do gráfico e fica por baixo da legenda:
   «Cada ponto é um produto (€/kg). O traço laranja corresponde à mediana.»
8. Painel 4: os filtros «Tipo de arroz» e «Segmento» passam para o painel lateral «Filtros», como nos outros
   painéis, e ficam visíveis ao longo da página.
9. Painel 3, cartões de importações e exportações: «… t — +x% homólogo» passa a «… t: +x% homólogo».
10. «·» passa a «-» em todo o painel (bundle e textos do observatory-data.json).
11. Painel 4: o carimbo «Recolha de» passa a «Última atualização:».
12. Painel 2, gráfico de evolução: sai a nota «Valores em mil t» (o eixo já diz «Mil toneladas»).
13. Painel 4: carregar num valor da tabela do gráfico 02 abre o produto correspondente na tabela 03
    (filtra o supermercado, desce até à linha e destaca os produtos com esse preço por kg). Média e mediana
    levam ao produto com o preço por kg mais próximo.
"""
import hashlib
import re
import sys
from pathlib import Path

HELPERS = r"""function MzFlat(c){let o=[];(function w(x){if(x==null||x===!1||x===!0)return;if(Array.isArray(x)){x.forEach(w);return}if(x&&x.type===T.Fragment&&x.props){w(x.props.children);return}o.push(x)})(c);return o}
function MzHead({children:c}){let k=MzFlat(c),a=k.filter(e=>e&&e.props&&typeof e.props.className==`string`&&/(^| )chart-actions( |$)/.test(e.props.className));if(!a.length)return(0,T.jsx)(`div`,{className:"visual-head",children:c});let r=k.filter(e=>!a.includes(e)),it=a.flatMap(e=>MzFlat(e.props.children)),tl=it.filter(e=>e&&(e.type===I||e.type===V)),fl=it.filter(e=>!tl.includes(e)),t=r[0],tw=tl.length?(0,T.jsx)(`div`,{className:`mz-head-tools`,children:tl}):null,tt=t&&t.props&&typeof t.type==`string`?(0,l.cloneElement)(t,{className:`${t.props.className??``} mz-head-title`.trim()},...MzFlat(t.props.children),tw):t;return(0,T.jsxs)(`div`,{className:`visual-head mz-head`,children:[tt,...r.slice(1),tt===t&&tw,fl.length?(0,T.jsx)(`div`,{className:`chart-actions mz-head-filters`,children:fl}):null]})}
function MzTxt(n){return n==null||typeof n==`boolean`?``:typeof n==`string`||typeof n==`number`?String(n):Array.isArray(n)?n.map(MzTxt).join(` `):n.props?MzTxt(n.props.children):``}
function MzNum(t){if(typeof t==`number`)return t;let m=String(t).replace(/[  ]/g,` `).trim().match(/^([+\-−]?)(\d[\d .]*)(?:,(\d+))?\s*(kg|g)?(?![a-z])/i);if(!m)return null;let v=Number(m[2].replace(/[ .]/g,``)+(m[3]?`.`+m[3]:``));if(m[1]&&m[1]!==`+`)v=-v;return m[4]&&m[4].toLowerCase()===`g`?v/1e3:v}
function MzSortTable({className:cn,children:c,init:ini}){let[st,setSt]=(0,l.useState)(ini??null),ps=MzFlat(c),hd=ps.find(e=>e&&e.type===`thead`);if(!hd)return(0,T.jsx)(`table`,{className:cn,children:c});let bs=ps.filter(e=>e&&e.type===`tbody`),ot=ps.filter(e=>e!==hd&&!bs.includes(e)),hr=MzFlat(hd.props.children)[0],ths=MzFlat(hr.props.children),go=i=>setSt(st&&st.c===i?{c:i,d:-st.d}:{c:i,d:1}),nt=ths.map((h,i)=>{let on=st&&st.c===i;return(0,l.cloneElement)(h,{key:h.key??`c${i}`,className:`${h.props.className??``} mz-sort${on?` mz-sorted`:``}`.trim(),"aria-sort":on?st.d>0?`ascending`:`descending`:`none`,tabIndex:0,title:`Ordenar por esta coluna`,onClick:()=>go(i),onKeyDown:e=>{(e.key===`Enter`||e.key===` `)&&(e.preventDefault(),go(i))}},...MzFlat(h.props.children),(0,T.jsx)(`span`,{className:`mz-sort-ico`,"aria-hidden":`true`,children:on?st.d>0?`▲`:`▼`:`▲▼`}))}),so=rs=>{if(!st)return rs;let vs=rs.map(r=>{let x=MzFlat(r.props.children)[st.c],d=x&&x.props?x.props[`data-sort`]:void 0;return d??MzTxt(x).trim()}),em=v=>v==null||v===``||v===`—`||v===`S/O`,nu=vs.every(v=>em(v)||MzNum(v)!=null),ky=vs.map(v=>em(v)?null:nu?MzNum(v):String(v));return rs.map((r,i)=>[r,ky[i],i]).sort((a,b)=>a[1]==null&&b[1]==null?a[2]-b[2]:a[1]==null?1:b[1]==null?-1:(nu?a[1]-b[1]:a[1].localeCompare(b[1],`pt`,{sensitivity:`base`,numeric:!0}))*st.d||a[2]-b[2]).map(e=>e[0])};return(0,T.jsxs)(`table`,{className:cn,children:[...ot,(0,l.cloneElement)(hd,{key:`h`},(0,l.cloneElement)(hr,{},...nt)),...bs.map((b,i)=>(0,l.cloneElement)(b,{key:b.key??`b${i}`},...so(MzFlat(b.props.children))))]})}
function MzEurRev(k,v){return typeof v==`string`&&v!==`EUR`&&!/^https?:/.test(v)?v.replace(/(?<![A-Za-z])EUR(?![A-Za-z])/g,`€`).replace(/·/g,`-`):v}
function MzQuoteCropPick({country:c,render:r}){let[s,setS]=(0,l.useState)({c,v:`all`}),v=s.c===c?s.v:`all`;return r(v,x=>setS({c,v:x}))}
var MzRS={v:null,l:new Set,set(v){this.v=v;this.l.forEach(f=>f())}};
function MzRetailPub(p){(0,l.useEffect)(()=>{MzRS.set(p)});(0,l.useEffect)(()=>()=>MzRS.set(null),[]);return null}
function MzRetailAside(){let[,f]=(0,l.useState)(0);(0,l.useEffect)(()=>{let g=()=>f(x=>x+1);MzRS.l.add(g);g();return()=>{MzRS.l.delete(g)}},[]);let v=MzRS.v;if(!v)return null;return(0,T.jsxs)(`section`,{className:`filter-panel`,children:[(0,T.jsxs)(`div`,{className:`aside-title`,children:[(0,T.jsx)(`span`,{children:`Filtros`}),(0,T.jsx)(`small`,{children:`Atualizam cartões e gráficos`})]}),(0,T.jsxs)(`label`,{children:[`Tipo de arroz`,(0,T.jsx)(`select`,{value:v.tipo,onChange:e=>v.setTipo(e.target.value),children:v.types.map(t=>(0,T.jsx)(`option`,{value:t,children:t},t))})]}),(0,T.jsxs)(`label`,{children:[`Segmento`,(0,T.jsx)(`select`,{value:v.seg,onChange:e=>v.setSeg(e.target.value),children:MzSegs.map(t=>(0,T.jsx)(`option`,{value:t,children:t},t))})]}),(0,T.jsx)(`p`,{className:`filter-note`,children:`Preços ao consumidor nas lojas online, em euros por kg. Marca própria inclui as linhas biológicas e premium das cadeias. Lidl, Aldi e Mercadona não vendem mercearia online em Portugal.`})]})}
var MzQS={v:null,l:new Set,set(v){this.v=v;this.l.forEach(f=>f())}};
function MzQuotePub({v}){(0,l.useEffect)(()=>{MzQS.set(v)});(0,l.useEffect)(()=>()=>MzQS.set(null),[]);return null}
function MzQuoteAside(){let[,f]=(0,l.useState)(0);(0,l.useEffect)(()=>{let g=()=>f(x=>x+1);MzQS.l.add(g);g();return()=>{MzQS.l.delete(g)}},[]);let v=MzQS.v;if(!v)return null;return(0,T.jsxs)(`section`,{className:`filter-panel mz-quote-filters`,children:[(0,T.jsxs)(`div`,{className:`aside-title`,children:[(0,T.jsx)(`span`,{children:`Filtros`}),(0,T.jsx)(`small`,{children:`Atualizam cartões e gráficos`})]}),v[0],v[1],(0,T.jsx)(`div`,{className:`filter-note`,children:v[2]})]})}
function MzPid(p){return`${p.c}|${p.nome}|${p.peso}|${p.preco}`}
function MzQuoteCrops(rs,c){return Array.from(new Set(rs.filter(r=>r.country_code===c&&(r.source===`Comissão Europeia`&&r.crop!==`rice`||r.crop===`sunflower`)).map(r=>r.crop)))}
"""

QUOTES_PRE = (
    "let MzQ2=c=>MzQC===`all`||c===MzQC,MzCm=c=>c===`wheat`?`soft_wheat`:c,"
    "MzCS={ec:[`rice`],ismea:[`rice`],mapa:Array.from(new Set(s.map(t=>t.crop))),"
    "sevilla:ce?Array.from(new Set(ce.rows.map(t=>t.crop))):[],salamanca:[`maize`,`sunflower`],binefar:[`maize`],"
    "cme:H?[MzCm(H.crop)]:[],fred:b.map(MzCm),dgagri:MzQuoteCrops(t,Ee)},"
    "MzAll=Array.from(new Set(ve.flatMap(k=>MzCS[k]??[]))).sort((x,y)=>(x===`rice`?-1:y===`rice`?1:0)||String(MzQuoteCropLabels[x]??x).localeCompare(MzQuoteCropLabels[y]??y,`pt`)),"
    "MzOK=k=>MzQC===`all`||(MzCS[k]??[]).includes(MzQC),"
    "MzP=P.filter((x,i)=>MzQ2(MzCm(b[i]))),MzVe=ve.filter(MzOK),"
    "ye=k=>{let n=String(MzVe.indexOf(k)+1).padStart(2,`0`);return(0,T.jsx)(`span`,{className:`chart-number`,\"aria-label\":`Gráfico ${n}`,children:n})};"
)

QUOTE_CROP_SELECT = (
    ",MzAll.length>1&&(0,T.jsxs)(`label`,{children:[`Cultura`,(0,T.jsxs)(`select`,{value:MzQC,"
    "\"aria-label\":`Filtrar as cotações por cultura`,onChange:ev=>MzSetQC(ev.target.value),children:["
    "(0,T.jsx)(`option`,{value:`all`,children:`Todas as culturas`}),"
    "...MzAll.map(c=>(0,T.jsx)(`option`,{value:c,children:MzQuoteCropLabels[c]??e.crop_comparison.crops[c]?.label??c},c))]})]})"
)

MEDIAN_OLD = "j(`text`,{x:left,y:14,fontSize:12,fill:`#62625f`,children:`Cada ponto é um produto (€/kg); o traço marca a mediana`}),"
LEGEND_END = "js(`span`,{children:[j(`i`,{style:{background:`#D99A00`}}),`Mediana do supermercado`]},`m`)]})"
MEDIAN_NOTE = ",j(`p`,{className:`mz-chart-note`,children:`Cada ponto é um produto (€/kg). O traço laranja corresponde à mediana.`})"

CSS = """
.visual-head.mz-head{display:flex;flex-direction:column;align-items:stretch;justify-content:flex-start;gap:12px}
.visual-head.mz-head>.mz-head-title{display:flex;align-items:center;gap:16px;min-width:0}
.visual-head.mz-head>.mz-head-title>h2.chart-title{flex:0 1 auto;min-width:0}
.visual-head.mz-head .mz-head-tools{display:inline-flex;flex:none;align-items:center;gap:8px}
.visual-head.mz-head>.chart-actions.mz-head-filters{display:flex;flex-flow:row wrap;justify-content:flex-start;align-items:center;gap:10px}
@media (width<=700px){.visual-head.mz-head>.mz-head-title{flex-wrap:wrap;gap:10px}}
th.mz-sort{cursor:pointer;user-select:none;white-space:nowrap}
th.mz-sort:hover,th.mz-sort:focus-visible{color:#007A3D}
.mz-sort-ico{margin-left:6px;font-size:.7em;letter-spacing:-.15em;opacity:.3}
th.mz-sorted .mz-sort-ico{opacity:1;letter-spacing:0;color:#007A3D}
#retail-stats td.mz-go{cursor:pointer}
#retail-stats td.mz-go:hover b,#retail-stats td.mz-go:hover{text-decoration:underline;text-underline-offset:3px}
#retail-products{scroll-margin-top:130px}
#retail-products tr.mz-hl td{background:#fff1bf;transition:background .4s}
.mz-quote-filters .filter-note small{display:block;font-size:inherit;line-height:inherit}
.mz-chart-note{margin:8px 0 0;text-align:center;color:#46534a;font-size:13px;line-height:1.45}
"""


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


def patch_heads(s):
    # 3 e 4: todos os cabeçalhos dos gráficos passam pelo MzHead
    padrao = re.compile(r"(\(0,\s*T\.jsxs?\)|(?<![\w$])js|(?<![\w$])j)\(`div`,\s*\{\s*className:\s*`visual-head`,")
    s, n = padrao.subn(lambda m: m.group(1) + "(MzHead,{", s)
    if n < 25:
        raise SystemExit(f"[cabeçalhos] só encontrei {n} cabeçalhos.")
    return s, n


def patch_quotes(s):
    # 5: filtro de cultura nas Cotações
    ret = "return(0,T.jsxs)(T.Fragment,{children:[(0,T.jsx)(pe,{page:`prices`}),"
    if s.count(ret) != 1:
        raise SystemExit("[cotações] início do painel não encontrado.")
    a = s.index(ret) + len("return")
    b = call_end(s, a + len("(0,T.jsxs)"))
    body = s[a:b]
    guards = (
        ("L&&R.length>0&&(0,T.jsxs)(`section`,{className:`visual-card`,id:`quotes-ce`",
         "MzOK(`ec`)&&L&&R.length>0&&(0,T.jsxs)(`section`,{className:`visual-card`,id:`quotes-ce`"),
        ("Ee===`ES`&&(0,T.jsx)(T.Fragment,{children:(0,T.jsxs)(`section`,{className:`visual-card`,id:`quotes-mapa`",
         "Ee===`ES`&&MzOK(`mapa`)&&(0,T.jsx)(T.Fragment,{children:(0,T.jsxs)(`section`,{className:`visual-card`,id:`quotes-mapa`"),
        ("Ee===`IT`&&(0,T.jsx)(T.Fragment,{children:(0,T.jsxs)(`section`,{className:`visual-card`,id:`quotes-ismea`",
         "Ee===`IT`&&MzOK(`ismea`)&&(0,T.jsx)(T.Fragment,{children:(0,T.jsxs)(`section`,{className:`visual-card`,id:`quotes-ismea`"),
        ("Ee===`ES`&&(0,T.jsx)(T.Fragment,{children:ce&&(0,T.jsxs)(`section`,{className:`visual-card`,id:`quotes-sevilla`",
         "Ee===`ES`&&MzOK(`sevilla`)&&(0,T.jsx)(T.Fragment,{children:ce&&(0,T.jsxs)(`section`,{className:`visual-card`,id:`quotes-sevilla`"),
        ("Ee===`ES`&&(0,T.jsx)(T.Fragment,{children:w&&(0,T.jsxs)(`section`,{className:`visual-card`,id:`quotes-salamanca`",
         "Ee===`ES`&&MzOK(`salamanca`)&&(0,T.jsx)(T.Fragment,{children:w&&(0,T.jsxs)(`section`,{className:`visual-card`,id:`quotes-salamanca`"),
        ("Ee===`ES`&&(0,T.jsx)(T.Fragment,{children:A&&(0,T.jsxs)(`section`,{className:`visual-card`,id:`quotes-binefar`",
         "Ee===`ES`&&MzOK(`binefar`)&&(0,T.jsx)(T.Fragment,{children:A&&(0,T.jsxs)(`section`,{className:`visual-card`,id:`quotes-binefar`"),
        ("_e&&ze&&H&&(0,T.jsxs)(`section`,{className:`visual-card`,id:`quotes-cme`",
         "MzOK(`cme`)&&_e&&ze&&H&&(0,T.jsxs)(`section`,{className:`visual-card`,id:`quotes-cme`"),
        ("_e&&(0,T.jsx)(T.Fragment,{children:(0,T.jsxs)(`section`,{className:`visual-card trading-card`,id:`crop-trading`",
         "_e&&MzOK(`fred`)&&(0,T.jsx)(T.Fragment,{children:(0,T.jsxs)(`section`,{className:`visual-card trading-card`,id:`crop-trading`"),
        ("(0,T.jsx)(MzMarketQuotes,{records:t,country:Ee})",
         "MzOK(`dgagri`)&&(0,T.jsx)(MzMarketQuotes,{records:t,country:Ee,crop:MzQC})"),
        # linhas dos quadros com várias culturas
        ("u.filter(e=>s.some(t=>t.crop===e))", "u.filter(e=>MzQ2(e)&&s.some(t=>t.crop===e))"),
        ("Array.from(new Set(ce.rows.map(e=>e.crop))).map(t=>(0,T.jsxs)(`tbody`",
         "Array.from(new Set(ce.rows.map(e=>e.crop))).filter(MzQ2).map(t=>(0,T.jsxs)(`tbody`"),
    )
    for antigo, novo in guards:
        body = sub(body, antigo, novo, f"cotações: {antigo[:40]}")
    # séries FRED/FMI filtradas pela cultura
    fa = body.index("id:`crop-trading`")
    fb = body.index("MzOK(`dgagri`)")
    fred = body[fa:fb]
    fred = sub(fred, "series:P,", "series:MzP,", "FRED séries")
    fred = sub(fred, "children:P.map(", "children:MzP.map(", "FRED legenda")
    body = body[:fa] + fred + body[fb:]
    # lista «Cultura» ao lado do «País»
    lab = "(0,T.jsxs)(`label`,{children:[`País`,(0,T.jsxs)(`select`,{value:Ee,"
    if body.count(lab) != 1:
        raise SystemExit("[cotações] filtro de país não encontrado.")
    la = body.index(lab)
    le = call_end(body, la + len("(0,T.jsxs)"))
    body = body[:le] + QUOTE_CROP_SELECT + body[le:]
    # filtros «País» e «Cultura» no painel lateral «Filtros», como nos outros painéis
    body = sub(body, "(0,T.jsxs)(`div`,{className:`month-filter quote-country-filter`,children:",
               "(0,T.jsx)(MzQuotePub,{v:", "filtros das cotações para o painel lateral")
    novo = f"(0,T.jsx)(MzQuoteCropPick,{{country:Ee,render:(MzQC,MzSetQC)=>{{{QUOTES_PRE}return {body}}}}})"
    return s[:a] + novo + s[b:]


def patch_market_quotes(s):
    # o quadro DG AGRI passa a seguir o filtro de cultura do painel; sai a lista própria
    s = sub(s, "function MzMarketQuotes({ records, country })",
            "function MzMarketQuotes({ records, country, crop: extCrop })", "DG AGRI assinatura")
    s = sub(s, "let activeCrop = allRows.some((row) => row.crop === crop) ? crop : `all`;",
            "let activeCrop = extCrop && extCrop !== `all` && allRows.some((row) => row.crop === extCrop) ? extCrop : `all`;",
            "DG AGRI cultura ativa")
    i = s.index("id: `quotes-eu-cereals`")
    k = s.index("`Cultura`,", i)
    a = s.rfind("(0, T.jsxs)(`label`", i, k)
    b = call_end(s, a + len("(0, T.jsxs)"))
    if b < k:
        raise SystemExit("[DG AGRI] lista de cultura não encontrada.")
    return s[:a] + "null" + s[b:]


def patch_js(s: str) -> str:
    s = sub(s, "function MzCropPick(", HELPERS + "function MzCropPick(", "componentes")
    # 6: EUR -> € (texto do bundle e dados)
    s = sub(s, "return e.json()}).then(e=>{t(e),s(e.metadata.trade_latest_year)})",
            "return e.text()}).then(e=>JSON.parse(e,MzEurRev)).then(e=>{t(e),s(e.metadata.trade_latest_year)})",
            "leitura dos dados")
    s, n = re.subn(r"(?<![A-Za-z])EUR(?=/| )", "€", s)
    if n < 8:
        raise SystemExit(f"[EUR] esperava pelo menos 8, encontrei {n}.")
    # 10: «·» passa a «-» (texto do bundle; os dados são convertidos ao ler)
    n = s.count("·")
    if n < 10:
        raise SystemExit(f"[pontos] esperava pelo menos 10, encontrei {n}.")
    s = s.replace("·", "-")
    # 11: «Recolha de» passa a «Última atualização:» no carimbo do retalho
    s = sub(s, "children:[`Recolha de `,j(`b`,{children:dt})]", "children:[`Última atualização: `,j(`b`,{children:dt})]", "carimbo do retalho")
    # 12: Painel 2, gráfico de evolução: sai a nota «Valores em mil t» (o eixo já diz Mil toneladas)
    s = sub(s, "(0,T.jsx)(z,{note:`Valores em ${f}.`,children:w.map(", "(0,T.jsx)(z,{note:f===`mil t`?void 0:`Valores em ${f}.`,children:w.map(", "nota do consumo")
    # 2: Ano comum
    s = sub(s, "children:[`Ano comum `,", "children:[`Último ano disponível `,", "ano comum")
    s = sub(s, "`Explicação do ano comum`", "`Explicação do último ano disponível`", "ano comum (i)")
    # 9: dois pontos a seguir às toneladas
    s = sub(s, "` — ${fe(f.change)} homólogo`", "`: ${fe(f.change)} homólogo`", "homólogo importações")
    s = sub(s, "` — ${fe(h.change)} homólogo`", "`: ${fe(h.change)} homólogo`", "homólogo exportações")
    # 7: nota da mediana por baixo da legenda
    s = sub(s, MEDIAN_OLD, "", "nota da mediana (topo)")
    s = sub(s, LEGEND_END, LEGEND_END + MEDIAN_NOTE, "nota da mediana (legenda)")
    # 8: filtros do retalho no painel lateral «Filtros», como nos outros painéis (fica visível ao longo da página)
    m = "js(`div`,{className:`month-filter quote-country-filter mz-filter`,children:[js(`label`,{children:[`Tipo de arroz`"
    if s.count(m) != 1:
        raise SystemExit("[filtros do retalho] não encontrados.")
    a = s.index(m)
    b = call_end(s, a + len("js"))
    s = s[:a] + "j(MzRetailPub,{tipo,seg,setTipo,setSeg,types:d.types})" + s[b:]
    s = sub(s, "function Ut(){if(!e||i===`home`||i===`prices`||i===`retail`)return null;",
            "function Ut(){if(e&&i===`retail`)return(0,T.jsx)(MzRetailAside,{});if(e&&i===`prices`)return(0,T.jsx)(MzQuoteAside,{});if(!e||i===`home`)return null;",
            "painel lateral do retalho")
    # 13: Painel 4, gráfico 02: cada valor da tabela leva ao produto correspondente na tabela 03
    s = sub(s, "[ord,setOrd]=(0,l.useState)(`kg`)",
            "[ord,setOrd]=(0,l.useState)(`kg`),[MzHl,setMzHl]=(0,l.useState)(null),MzEf=(0,l.useEffect)(()=>{if(!MzHl)return;"
            "let r=requestAnimationFrame(()=>{let el=MzHl.id===`__t`?document.getElementById(`retail-products`):"
            "document.querySelector(`#retail-products tr.mz-hl`);"
            "el&&el.scrollIntoView({behavior:`smooth`,block:MzHl.id===`__t`?`start`:`center`})}),t=setTimeout(()=>setMzHl(null),6e3);"
            "return()=>{cancelAnimationFrame(r);clearTimeout(t)}},[MzHl])", "estado do destaque")
    s = sub(s, "return j(`td`,{className:`num${c?``:` mz-all`}`,children:x==null?`—`:j(`b`,{className:c&&v.length>1&&x===lo?`mz-lo`:c&&v.length>1&&x===hi?`mz-hi`:``,children:MzF(x)})},c??`all`)",
            "return j(`td`,{className:`num${c?``:` mz-all`}${x==null?``:` mz-go`}`,title:x==null?void 0:`Ver o produto na tabela 03`,"
            "onClick:x==null?void 0:()=>{let L=TL.filter(p=>!c||p.c===c),b=L.reduce((a,p)=>!a||Math.abs(p.kg-x)<Math.abs(a.kg-x)?p:a,null);"
            "setCad(c??`Todas`);b&&setMzHl({id:MzPid(b),ids:L.filter(p=>p.kg===b.kg).map(MzPid),n:Date.now()})},"
            "children:x==null?`—`:j(`b`,{className:c&&v.length>1&&x===lo?`mz-lo`:c&&v.length>1&&x===hi?`mz-hi`:``,children:MzF(x)})},c??`all`)",
            "valores da tabela 02")
    s = sub(s, "...cols.map(c=>j(`td`,{className:`num${c?``:` mz-all`}`,children:st(tipo,c)?.n??0},c??`all`))",
            "...cols.map(c=>j(`td`,{className:`num${c?``:` mz-all`} mz-go`,title:`Ver os produtos na tabela 03`,onClick:()=>{setCad(c??`Todas`);setMzHl({id:`__t`,n:Date.now()})},children:st(tipo,c)?.n??0},c??`all`))",
            "contagem da tabela 02")
    s = sub(s, "SL.map((p,i)=>js(`tr`,{children:[", "SL.map((p,i)=>js(`tr`,{\"data-mzp\":MzPid(p),className:MzHl&&MzHl.ids&&MzHl.ids.includes(MzPid(p))?`mz-hl`:void 0,children:[", "linhas da tabela 03")
    # 1: tabelas ordenáveis
    i = s.index(',j(`div`,{className:`segmented-control`,"aria-label":`Ordenar por`')
    e = call_end(s, i + len(",j"))
    s = s[:i] + s[e:]
    s = sub(s, "js(`table`,{className:`quote-table mz-products`,", "js(MzSortTable,{init:{c:5,d:1},className:`quote-table mz-products`,", "tabela de produtos")
    s = sub(s, "j(`td`,{className:`num`,children:MzPeso(p.peso)})", "j(`td`,{className:`num`,\"data-sort\":p.peso,children:MzPeso(p.peso)})", "ordem embalagem")
    s = sub(s, "js(`td`,{className:`num`,children:[`${MzF(p.preco)} €`", "js(`td`,{className:`num`,\"data-sort\":p.preco,children:[`${MzF(p.preco)} €`", "ordem preço")
    s = sub(s, "js(`td`,{className:`num`,children:[j(`b`,{children:MzF(p.kg)})", "js(`td`,{className:`num`,\"data-sort\":p.kg,children:[j(`b`,{children:MzF(p.kg)})", "ordem €/kg")
    s = sub(s, "(0,T.jsx)(`table`,{className:`mz-variety-table`,", "(0,T.jsx)(MzSortTable,{className:`mz-variety-table`,", "tabela de variedades")
    # 5
    s = patch_quotes(s)
    s = patch_market_quotes(s)
    # 3 e 4 (no fim, para as âncoras acima continuarem a bater certo)
    s, n = patch_heads(s)
    print(f"Cabeçalhos com MzHead: {n}")
    return s


def nome_hash(conteudo, ext):
    return f"index-mz{hashlib.sha256(conteudo.encode()).hexdigest()[:8]}.{ext}"


def main():
    raiz = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    site = raiz / "observatorio-maizoryza"
    idx = (site / "index.html").read_text(encoding="utf-8")
    js_antigo = re.search(r"assets/(index-[\w-]+\.js)", idx).group(1)
    css_antigo = re.search(r"assets/(index-[\w-]+\.css)", idx).group(1)
    js = (site / "assets" / js_antigo).read_text(encoding="utf-8")
    if "function MzVarietyPick(" not in js:
        raise SystemExit("Aplicar primeiro patch_vaga19.py.")
    if "function MzHead(" in js:
        raise SystemExit("O bundle já tem a vaga 20 aplicada.")
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
