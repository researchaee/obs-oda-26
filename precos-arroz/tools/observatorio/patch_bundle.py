"""Acrescenta o Painel 7 «Preços no retalho» ao site construído do observatório (vaga 13).

    python tools/observatorio/patch_bundle.py <raiz-do-repositório>

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


def patch_js(s: str) -> str:
    if "function MzRetail(" in s:
        raise SystemExit("O bundle já tem o painel de retalho.")
    # 1. Definição do painel 7
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
    return s


def nome_hash(prefixo: str, conteudo: str, ext: str) -> str:
    h = hashlib.sha256(conteudo.encode()).hexdigest()[:8]
    return f"{prefixo}-mz{h}.{ext}"


def main():
    raiz = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    site = raiz / "observatorio-maizoryza"
    idx = (site / "index.html").read_text(encoding="utf-8")
    js_antigo = re.search(r"assets/(index-[\w-]+\.js)", idx).group(1)
    css_antigo = re.search(r"assets/(index-[\w-]+\.css)", idx).group(1)
    js = patch_js((site / "assets" / js_antigo).read_text(encoding="utf-8"))
    css = (site / "assets" / css_antigo).read_text(encoding="utf-8") + "\n" + (AQUI / "mz_retail.css").read_text(encoding="utf-8")
    js_novo, css_novo = nome_hash("index", js, "js"), nome_hash("index", css, "css")
    (site / "assets" / js_novo).write_text(js, encoding="utf-8")
    (site / "assets" / css_novo).write_text(css, encoding="utf-8")
    for f in (site / "index.html", raiz / "index.html"):
        t = f.read_text(encoding="utf-8").replace(js_antigo, js_novo).replace(css_antigo, css_novo)
        f.write_text(t, encoding="utf-8")
    (site / "assets" / js_antigo).unlink()
    (site / "assets" / css_antigo).unlink()
    print(f"JS {js_antigo} -> {js_novo}\nCSS {css_antigo} -> {css_novo}")


if __name__ == "__main__":
    main()
