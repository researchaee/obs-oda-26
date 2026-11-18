"""Vaga 18: ilustrações para as seis culturas sem ícone no Painel 7.

    python precos-arroz/tools/observatorio/patch_vaga18.py <raiz-do-repositório>

Aplicar depois de patch_vaga17.py. Os SVGs crop-icon-*.svg ficam junto ao index do
observatório; os três ícones PNG já existentes mantêm os seus URLs atuais.
"""
import hashlib
import re
import sys
from pathlib import Path


OLD = (
    "children:[`rice`,`maize`,`sunflower`].includes(e)?(0,T.jsx)(`img`,"
    "{src:E(`crop-icon-${e}.png`),alt:``}):(0,T.jsx)(`i`,"
    "{className:`mz-crop-dot`,style:{background:k[e]??D.grey},children:n.slice(0,1).toUpperCase()})"
)
NEW = (
    "children:[`rice`,`maize`,`sunflower`,`soft_wheat`,`durum_wheat`,`barley`,`oats`,`rye`,`triticale`].includes(e)"
    "?(0,T.jsx)(`img`,{src:[`rice`,`maize`,`sunflower`].includes(e)?E(`crop-icon-${e}.png`):`./crop-icon-${e}.svg`,alt:``})"
    ":(0,T.jsx)(`i`,{className:`mz-crop-dot`,style:{background:k[e]??D.grey},children:n.slice(0,1).toUpperCase()})"
)
ICON_NAMES = ("soft_wheat", "durum_wheat", "barley", "oats", "rye", "triticale")


def patch_js(content: str) -> str:
    if "function MzCropPick(" not in content:
        raise SystemExit("Aplicar primeiro patch_vaga17.py.")
    if content.count(OLD) != 1:
        raise SystemExit("O renderer de ícones não corresponde ao bundle esperado.")
    return content.replace(OLD, NEW)


def nome_hash(content: str) -> str:
    return f"index-mz{hashlib.sha256(content.encode()).hexdigest()[:8]}.js"


def main() -> None:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    site = root / "observatorio-maizoryza"
    for name in ICON_NAMES:
        if not (site / f"crop-icon-{name}.svg").is_file():
            raise SystemExit(f"Ícone em falta: crop-icon-{name}.svg")

    site_index = site / "index.html"
    root_index = root / "index.html"
    site_html = site_index.read_text(encoding="utf-8")
    js_match = re.search(r"assets/(index-[\w-]+\.js)", site_html)
    if js_match is None:
        raise SystemExit("Bundle JavaScript não encontrado em observatorio-maizoryza/index.html.")
    old_js_name = js_match.group(1)
    old_js_path = site / "assets" / old_js_name
    content = patch_js(old_js_path.read_text(encoding="utf-8"))
    new_js_name = nome_hash(content)
    root_html = root_index.read_text(encoding="utf-8")
    if old_js_name not in root_html:
        raise SystemExit("O index.html da raiz não aponta para o bundle esperado.")

    (site / "assets" / new_js_name).write_text(content, encoding="utf-8")
    site_index.write_text(site_html.replace(old_js_name, new_js_name), encoding="utf-8")
    root_index.write_text(root_html.replace(old_js_name, new_js_name), encoding="utf-8")
    print(f"JS {old_js_name} -> {new_js_name}")


if __name__ == "__main__":
    main()
