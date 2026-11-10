"""Aplica os painéis de cotações e retalho ao site construído do observatório (vaga 13).

    python tools/observatorio/patch_bundle.py <raiz-do-repositório>
    python tools/observatorio/patch_bundle.py --quotes-only <raiz-do-repositório>

O repositório só tem o site construído, por isso o painel é injetado no bundle
JavaScript já minificado, reutilizando os componentes do próprio site (cabeçalho
do painel, cartões KPI, quadros, botão «Dados em Excel», fontes). Cada substituição
é verificada: se o texto esperado não existir (bundle diferente), o script pára
sem estragar nada. Os ficheiros novos ganham um nome com hash próprio e os dois
index.html passam a apontar para eles.
"""
import hashlib
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent


def sub1(s: str, antigo: str, novo: str, nome: str) -> str:
    n = s.count(antigo)
    if n != 1:
        raise SystemExit(f"[{nome}] esperava 1 ocorrência, encontrei {n}. Bundle diferente do da vaga 13?")
    return s.replace(antigo, novo)


def patch_italy_quote_table(s: str) -> str:
    old_title = "Cotações de mercado do arroz por variedade, Itália — praças de ${p.join(` e `)} (EUR/t), última data publicada ${_}"
    new_title = "Cotações de arroz por variedade — Itália"
    if old_title in s:
        s = sub1(s, old_title, new_title, "título do gráfico 02")
    elif s.count(new_title) != 1:
        raise SystemExit("[título do gráfico 02] texto esperado não encontrado.")

    price_prefix = "(0,T.jsxs)(`td`,{className:`num`,children:[(0,T.jsx)(`b`,{children:n?o(n.price_eur_t):`—`}),n&&a(n.price_eur_t,"
    if price_prefix in s:
        if s.count(price_prefix) != 1:
            raise SystemExit("[preços do gráfico 02] esperava 1 ocorrência.")
        start = s.index(price_prefix)
        end = s.index(")]})", start) + len(")]})")
        price_cell = s[start:end]
        price_cell = price_cell.replace(
            "className:`num`,",
            "className:`num`,\"data-label\":`${t} · €/t`,",
            1,
        )
        s = s[:start] + price_cell + s[end:]
    elif s.count('"data-label":`${t} · €/t`') != 1:
        raise SystemExit("[preços do gráfico 02] célula esperada não encontrada.")

    old_change_cell = "(0,T.jsx)(`td`,{className:`num quote-change ${(n?.weekly_change_pct??0)<0?`down`:(n?.weekly_change_pct??0)>0?`up`:``}`,children:y(n?.weekly_change_pct)})"
    new_change_cell = "(0,T.jsx)(`td`,{className:`num quote-change ${(n?.weekly_change_pct??0)<0?`down`:(n?.weekly_change_pct??0)>0?`up`:``}`,\"data-label\":`${t} · variação`,children:y(n?.weekly_change_pct)})"
    if old_change_cell in s:
        s = sub1(s, old_change_cell, new_change_cell, "variações do gráfico 02")
    elif s.count('"data-label":`${t} · variação`') != 1:
        raise SystemExit("[variações do gráfico 02] célula esperada não encontrada.")

    obsolete_table = "(0,T.jsx)(MzMarketQuotes,{records:t,country:Ee,countryLabel:Re(Ee)}),"
    if obsolete_table in s:
        s = sub1(s, obsolete_table, "", "tabela sem número")
    cereal_chart = "(0,T.jsx)(MzMarketQuotes,{records:t,country:Ee})"
    if s.count(cereal_chart) > 1:
        raise SystemExit("[gráfico de cereais] encontrei chamadas duplicadas.")
    if cereal_chart not in s:
        s = sub1(
            s,
            "(0,T.jsx)(B,{links:ue})]})})]})},Bt=()=>",
            "(0,T.jsx)(B,{links:ue})]})}),(0,T.jsx)(MzMarketQuotes,{records:t,country:Ee})]})},Bt=()=>",
            "gráfico de cereais no fim do painel",
        )
    return s


def patch_crops_quotes(s: str) -> str:
    call = "(0,T.jsx)(MzMarketQuotes,{records:e.quotes?.market_prices?.records??e.crop_comparison.market_prices.records,country:c}),"
    if call in s:
        return s
    return sub1(
        s,
        "(0,T.jsxs)(`section`,{className:`visual-card`,id:`crop-evolution`,",
        call + "(0,T.jsxs)(`section`,{className:`visual-card`,id:`crop-evolution`,",
        "cotações no painel comparativo",
    )


def patch_current_navigation(s: str) -> str:
    panel_numbers = (
        ("consumption", "03", "02"),
        ("trade", "06", "03"),
        ("retail", "05", "04"),
        ("prices", "04", "05"),
        ("inputs", "02", "06"),
    )
    for page, old_number, new_number in panel_numbers:
        old = f"{page}:{{number:`{old_number}`"
        new = f"{page}:{{number:`{new_number}`"
        if old in s:
            s = sub1(s, old, new, f"número do painel {page}")
        elif s.count(new) != 1:
            raise SystemExit(f"[número do painel {page}] número atual inesperado.")

    old_order = "Kt=[`home`,`production`,`inputs`,`consumption`,`prices`,`retail`,`trade`,`crops`]"
    new_order = "Kt=[`home`,`production`,`consumption`,`trade`,`retail`,`prices`,`inputs`,`crops`]"
    if old_order in s:
        s = sub1(s, old_order, new_order, "ordem dos painéis")
    elif s.count(new_order) != 1:
        raise SystemExit("[ordem dos painéis] sequência atual inesperada.")

    old_button = "className:i===e?`active`:``,onClick:()=>Ve(e),children:"
    new_button = 'className:i===e?`active`:``, "data-panel-spacer":e===`prices`?`true`:void 0,onClick:()=>Ve(e),children:'
    if '"data-panel-spacer":e===`prices`' not in s:
        s = sub1(s, old_button, new_button, "espaçamento antes das cotações")
    return s


def patch_home_cards(s: str) -> str:
    start_marker = "x=[{page:`"
    end_marker = "];return(0,T.jsxs)(T.Fragment,{children:[(0,T.jsxs)(`section`,{className:`intro-hero`"
    if s.count(start_marker) != 1 or s.count(end_marker) != 1:
        raise SystemExit("[cartões iniciais] não foi possível localizar a lista de painéis.")
    start = s.index(start_marker)
    end = s.index(end_marker, start)
    body = s[start + len("x=["):end]
    retail_marker = ",...(e.retail?[MzRetailCard(e.retail)]:[])"
    has_retail = body.count(retail_marker) == 1
    if has_retail:
        body = body.replace(retail_marker, "", 1)

    if body.count(",{page:`") > body.count("},{page:`"):
        segments = body.split(",{page:`")
        cards = [segments[0]] + ["{page:`" + segment for segment in segments[1:]]
        cards = [card if card.endswith("}") else card + "}" for card in cards]
    else:
        segments = body.split("},{page:`")
        cards = [segments[0] + "}"] + [
            card if card.endswith("}") else card + "}"
            for card in ("{page:`" + segment for segment in segments[1:])
        ]
    by_page: dict[str, str] = {}
    for card in cards:
        match = re.match(r"\{page:`([^`]+)`", card)
        if not match or match.group(1) in by_page:
            raise SystemExit("[cartões iniciais] formato ou painel duplicado na lista.")
        by_page[match.group(1)] = card
    order = ("production", "consumption", "trade", "retail", "prices", "inputs", "crops")
    if set(by_page) != set(order) - {"retail"}:
        if set(by_page) == set(order) and not has_retail:
            pass
        else:
            raise SystemExit("[cartões iniciais] a lista de painéis não corresponde ao esperado.")
    units = [
        by_page[page] if page != "retail" else "...(e.retail?[MzRetailCard(e.retail)]:[])"
        for page in order
    ]
    return s[:start] + "x=[" + ",".join(units) + s[end:]


def patch_js(s: str) -> str:
    if "function MzRetail(" in s:
        raise SystemExit("O bundle já tem o painel de retalho.")
    # 1. Definição do painel de retalho
    s = sub1(s, "inputs:{number:`06`,title:`Inputs agrícolas`,navTitle:`Inputs agrícolas`,kicker:`Custos de produção agrícola`,color:D.amberText}}",
             "inputs:{number:`06`,title:`Inputs agrícolas`,navTitle:`Inputs agrícolas`,kicker:`Custos de produção agrícola`,color:D.amberText},"
             "retail:{number:`07`,title:`Preços do arroz no retalho`,navTitle:`Preços no retalho`,kicker:`Preço ao consumidor em Portugal`,color:D.greenDark}}",
             "páginas")
    # 2. Componentes (antes do primeiro componente do site)
    s = sub1(s, "function pe({page:e,children:t}){", (AQUI / "mz_retail.js").read_text(encoding="utf-8").strip() + "\nfunction pe({page:e,children:t}){", "componente")
    # 3. Encaminhamento e navegação
    s = sub1(s, "i===`inputs`?Bt():null,Kt=[`home`,`production`,`trade`,`consumption`,`crops`,`prices`,`inputs`]",
             "i===`inputs`?Bt():i===`retail`?(e.retail?(0,T.jsx)(MzRetail,{data:e.retail,history:e.history?.retail}):(0,T.jsxs)(T.Fragment,{children:[(0,T.jsx)(pe,{page:`retail`}),(0,T.jsx)(`div`,{className:`empty-state`,children:`Os preços no retalho não estão disponíveis.`})]})):null,"
             "Kt=[`home`,`production`,`trade`,`consumption`,`crops`,`prices`,`inputs`,`retail`]",
             "navegação")
    # 4. Sem painel de filtros lateral (os filtros estão no próprio painel)
    s = sub1(s, "if(!e||i===`home`||i===`prices`)return null;", "if(!e||i===`home`||i===`prices`||i===`retail`)return null;", "filtros")
    # 5. Cartão na página inicial
    m = re.search(r"\{page:`inputs`,anchor:`inputs-index`,value:.*?extra:b\?.*?:`Eurostat e DG AGRI`\}\]", s)
    if not m:
        raise SystemExit("[página inicial] cartão de inputs não encontrado.")
    s = s[:m.end() - 1] + ",...(e.retail?[MzRetailCard(e.retail)]:[])]" + s[m.end():]
    # 6. Assistente: perguntas sobre retalho
    s = sub1(s, "if(e.inputs&&r(`adubo`",
             "if(e.retail&&r(`retalho`,`supermercado`,`consumidor`,`continente`,`pingo doce`,`auchan`,`intermarch`,`corte ingl`,`minipreco`,`marca propria`,`marca branca`,`prateleira`,`por kg`,`€/kg`,`euros o quilo`,`euros por quilo`,`quanto custa o arroz`,`mais barato`,`mais caro`,`custa o arroz`,`custa o quilo`,`custa um quilo`,`preco do arroz agulha`,`preco do arroz carolino`,`preco do arroz basmati`))return MzRetailAnswer(e.retail,n);"
             "if(e.inputs&&r(`adubo`", "assistente")
    s = sub1(s, "i===`inputs`?[`Quanto subiram os adubos em Portugal?`",
             "i===`retail`?[`Quanto custa o arroz agulha nos supermercados?`,`Onde está mais barato o arroz carolino?`,`Qual o preço do arroz basmati no Continente?`]:"
             "i===`inputs`?[`Quanto subiram os adubos em Portugal?`", "sugestões")
    return patch_market_quotes(s)


def patch_market_quotes(s: str) -> str:
    if "function MzMarketQuotes(" in s:
        if s.count("function MzMarketQuotes(") != 1:
            raise SystemExit("Esperava um único componente de cotações ISMEA no bundle.")
        inicio = s.index("function MzMarketQuotes(")
        inicio_rotulos = s.find("var MzQuoteCropLabels =")
        if 0 <= inicio_rotulos < inicio:
            inicio = inicio_rotulos
        fim = s.find("\nfunction pe(", inicio)
        if fim < 0:
            raise SystemExit("Não foi possível localizar o fim do componente de cotações ISMEA.")
        componente = (AQUI / "mz_market_quotes.js").read_text(encoding="utf-8").strip()
        s = s[:inicio] + componente + s[fim:]
        return patch_current_navigation(
            patch_home_cards(patch_crops_quotes(patch_italy_quote_table(s)))
        )

    s = sub1(
        s,
        "crops:{number:`04`,title:`Arroz, milho e girassol: comparação entre culturas`,navTitle:`Três culturas`,kicker:`Comparação de três culturas`,color:D.amberText},"
        "prices:{number:`05`,title:`Cotações`,navTitle:`Cotações`,kicker:`Preços de mercado do arroz`,color:D.greenDark},"
        "inputs:{number:`06`,title:`Inputs agrícolas`,navTitle:`Inputs agrícolas`,kicker:`Custos de produção agrícola`,color:D.amberText},"
        "retail:{number:`07`,title:`Preços do arroz no retalho`,navTitle:`Preços no retalho`,kicker:`Preço ao consumidor em Portugal`,color:D.greenDark}}",
        "crops:{number:`07`,title:`Arroz, milho e girassol: comparação entre culturas`,navTitle:`Outras culturas`,kicker:`Painel comparativo`,color:D.amberText},"
        "prices:{number:`05`,title:`Cotações`,navTitle:`Cotações`,kicker:`Cotações de mercado do arroz e de outras culturas`,color:D.greenDark},"
        "inputs:{number:`06`,title:`Inputs agrícolas`,navTitle:`Inputs agrícolas`,kicker:`Custos de produção agrícola`,color:D.amberText},"
        "retail:{number:`04`,title:`Preços do arroz no retalho`,navTitle:`Preços no retalho`,kicker:`Preço ao consumidor em Portugal`,color:D.greenDark}}",
        "números e títulos dos painéis",
    )
    s = sub1(s, "trade:{number:`02`,title:`Comércio internacional de arroz`",
             "trade:{number:`03`,title:`Comércio internacional de arroz`", "número do comércio internacional")
    s = sub1(s, "consumption:{number:`03`,title:`Consumo e autoaprovisionamento`",
             "consumption:{number:`02`,title:`Consumo e autoaprovisionamento`", "número do consumo")
    s = sub1(
        s,
        "function pe({page:e,children:t}){",
        (AQUI / "mz_market_quotes.js").read_text(encoding="utf-8").strip() + "\nfunction pe({page:e,children:t}){",
        "componente de cotações",
    )
    s = sub1(
        s,
        "t=e.crop_comparison.market_prices.records,n=e=>t.filter(t=>t.source===e)",
        "t=e.quotes?.market_prices?.records??e.crop_comparison.market_prices.records,n=e=>t.filter(t=>t.source===e)",
        "dados do painel",
    )
    s = sub1(s, "f=n(`ISMEA`),p=Array.from", "f=n(`ISMEA`).filter(e=>e.crop===`rice`),p=Array.from", "cotações de arroz")
    s = sub1(
        s,
        "m=Array.from(new Set(f.map(e=>e.product))).sort((e,t)=>e.localeCompare(t,`pt`))",
        "m=Array.from(new Set([...f.map(e=>e.product),...(Ee===`IT`?[`Ribe`]:[])])).sort((e,t)=>e.localeCompare(t,`pt`))",
        "variedade Ribe",
    )
    s = sub1(
        s,
        "Cotações semanais do ISMEA nas praças de ${p.join(` e `)}, para arroz em casca (risone) por variedade. ${p.map(e=>`${e}: ${g(e).toLowerCase()}`).join(`; `)}. A variação é face à semana anterior.",
        "Cotações semanais do ISMEA nas praças de ${p.join(` e `)}, para arroz em casca (risone) por variedade. ${p.map(e=>`${e}: ${g(e).toLowerCase()}`).join(`; `)}. ${f.some(e=>e.product===`Ribe`)?`Ribe: com cotação publicada.`:`Ribe: sem cotação na última publicação consultada.`} A variação é face à semana anterior.",
        "nota sobre a variedade Ribe",
    )
    s = sub1(
        s,
        "return(0,T.jsxs)(T.Fragment,{children:[(0,T.jsx)(pe,{page:`prices`}),(0,T.jsxs)(`div`,{className:`month-filter quote-country-filter`",
        "return(0,T.jsxs)(T.Fragment,{children:[(0,T.jsx)(pe,{page:`prices`}),(0,T.jsxs)(`div`,{className:`month-filter quote-country-filter`",
        "tabela de cereais ISMEA",
    )
    s = sub1(
        s,
        "b.filter(e=>ce.rows.some(t=>t.crop===e)).map(t=>(0,T.jsxs)(`tbody`,{children:[(0,T.jsx)(`tr`,{className:`quote-group`,children:(0,T.jsx)(`th`,{colSpan:5,children:e.crop_comparison.crops[t].label})})",
        "Array.from(new Set(ce.rows.map(e=>e.crop))).map(t=>(0,T.jsxs)(`tbody`,{children:[(0,T.jsx)(`tr`,{className:`quote-group`,children:(0,T.jsx)(`th`,{colSpan:6,children:e.crop_comparison.crops[t]?.label??MzQuoteCropLabels[t]??t})})",
        "culturas da Lonja",
    )
    inicio = s.index("id:`quotes-sevilla`")
    fim = s.index("id:`quotes-salamanca`", inicio)
    sevilha = s[inicio:fim]
    sevilha = sub1(
        sevilha,
        "(0,T.jsx)(`th`,{children:`Produto`}),(0,T.jsx)(`th`,{className:`num`,children:`€/t`})",
        "(0,T.jsx)(`th`,{children:`Produto`}),(0,T.jsx)(`th`,{children:`Data`}),(0,T.jsx)(`th`,{className:`num`,children:`€/t`})",
        "data das cotações Sevilla",
    )
    sevilha = sub1(
        sevilha,
        "(0,T.jsx)(`td`,{children:e.product}),(0,T.jsx)(`td`,{className:`num`,children:(0,T.jsx)(`b`,{children:e.price==null?`S/O`:o(e.price)})})",
        "(0,T.jsx)(`td`,{children:e.product}),(0,T.jsx)(`td`,{children:x(e.quote_date??ce.session_date)}),(0,T.jsx)(`td`,{className:`num`,children:(0,T.jsx)(`b`,{children:e.price==null?`S/O`:o(e.price)})})",
        "data das cotações Sevilla",
    )
    s = s[:inicio] + sevilha + s[fim:]
    s = sub1(s, "title:`Lonja de Sevilla — milho e girassol`", "title:`Lonja de Sevilla — milho, girassol e cereais`", "título Sevilla")
    s = sub1(
        s,
        "A coluna anterior é a sessão de ${x(ce.previous_session)}; próxima sessão a ${x(ce.next_session)}. O histórico consulta-se no consultor de preços da Lonja.",
        "A coluna anterior é a sessão de ${x(ce.previous_session)}. O histórico consulta-se no consultor de preços da Lonja.",
        "nota da Lonja",
    )
    s = sub1(
        s,
        "rows:ce.rows.map(e=>[e.product,x(ce.session_date),e.price,e.previous,e.volume])",
        "rows:ce.rows.map(e=>[e.product,x(e.quote_date??ce.session_date),e.price,e.previous,e.volume])",
        "exportação Sevilla",
    )
    nome_antigo = "Observatório de arroz, milho e girassol"
    if s.count(nome_antigo) != 2:
        raise SystemExit(
            "[identidade do observatório] esperava 2 ocorrências, "
            f"encontrei {s.count(nome_antigo)}. Bundle diferente do da vaga 13?"
        )
    s = s.replace(nome_antigo, "Observatório de Preços do Arroz")
    s = s.replace("Maizoryza — Observatório do arroz", "Observatório de Preços do Arroz")
    s = s.replace("`04 — Arroz, milho e girassol`", "`07 — Arroz, milho e girassol`")
    s = s.replace("`07 — Preços no retalho`", "`04 — Preços no retalho`")
    s = sub1(
        s,
        "Kt=[`home`,`production`,`trade`,`consumption`,`crops`,`prices`,`inputs`,`retail`]",
        "Kt=[`home`,`production`,`consumption`,`trade`,`retail`,`prices`,`inputs`,`crops`]",
        "ordem de navegação",
    )
    return patch_current_navigation(
        patch_home_cards(patch_crops_quotes(patch_italy_quote_table(s)))
    )


def nome_hash(prefixo: str, conteudo: str, ext: str) -> str:
    h = hashlib.sha256(conteudo.encode()).hexdigest()[:8]
    return f"{prefixo}-mz{h}.{ext}"


def main():
    args = sys.argv[1:]
    quotes_only = bool(args and args[0] == "--quotes-only")
    if quotes_only:
        args = args[1:]
    raiz = Path(args[0]) if args else Path(".")
    site = raiz / "observatorio-maizoryza"
    idx = (site / "index.html").read_text(encoding="utf-8")
    js_antigo = re.search(r"assets/(index-[\w-]+\.js)", idx).group(1)
    css_antigo = re.search(r"assets/(index-[\w-]+\.css)", idx).group(1)
    js_original = (site / "assets" / js_antigo).read_text(encoding="utf-8")
    js = patch_market_quotes(js_original) if quotes_only else patch_js(js_original)
    css = (site / "assets" / css_antigo).read_text(encoding="utf-8")
    if not quotes_only:
        css += "\n" + (AQUI / "mz_retail.css").read_text(encoding="utf-8")
    market_quotes_css = (AQUI / "mz_market_quotes.css").read_text(encoding="utf-8").strip()
    old_quotes_css = css.find(".dashboard-main{grid-template-columns:minmax(0,1fr)}")
    if old_quotes_css >= 0:
        css = css[:old_quotes_css].rstrip()
    css += "\n" + market_quotes_css
    js_novo, css_novo = nome_hash("index", js, "js"), nome_hash("index", css, "css")
    (site / "assets" / js_novo).write_text(js, encoding="utf-8")
    (site / "assets" / css_novo).write_text(css, encoding="utf-8")
    for f in (site / "index.html", raiz / "index.html"):
        t = f.read_text(encoding="utf-8").replace(js_antigo, js_novo).replace(css_antigo, css_novo)
        t = t.replace("<title>Observatório Maizoryza</title>", "<title>Observatório de Preços do Arroz</title>")
        t = t.replace(
            "Produção, comércio, consumo e preços de arroz, milho e girassol na Europa, a partir de fontes estatísticas oficiais.",
            "Produção, comércio, consumo e cotações do arroz; painel comparativo de outras culturas.",
        )
        f.write_text(t, encoding="utf-8")
    if js_antigo != js_novo:
        (site / "assets" / js_antigo).unlink()
    if css_antigo != css_novo:
        (site / "assets" / css_antigo).unlink()
    print(f"JS {js_antigo} -> {js_novo}\nCSS {css_antigo} -> {css_novo}")


if __name__ == "__main__":
    main()
