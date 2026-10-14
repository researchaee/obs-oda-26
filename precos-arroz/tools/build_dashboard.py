"""Gera o dashboard com os dados embutidos.

    python -m tools.build_dashboard
Escreve index.html (página completa, para o GitHub Pages) e dist/artifact.html
(só o conteúdo, para publicar como artifact no Claude).
"""
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def main():
    tpl = (RAIZ / "dashboard" / "template.html").read_text(encoding="utf-8")
    dados = json.loads((RAIZ / "data" / "latest.json").read_text(encoding="utf-8"))
    js = json.dumps(dados, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    corpo = tpl.replace("/*__DADOS__*/null", js)
    (RAIZ / "dist").mkdir(exist_ok=True)
    (RAIZ / "dist" / "artifact.html").write_text(corpo, encoding="utf-8")
    pagina = ('<!doctype html>\n<html lang="pt-PT">\n<head>\n<meta charset="utf-8">\n'
              '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
              '<style>[hidden]{display:none!important}body{margin:0}img{max-width:100%}</style>\n'
              '</head>\n<body>\n' + corpo + '\n</body>\n</html>\n')
    (RAIZ / "index.html").write_text(pagina, encoding="utf-8")
    print("index.html e dist/artifact.html gerados")


if __name__ == "__main__":
    main()
