# Observatório de Preços do Arroz

O observatório acompanha produção, comércio, consumo e preços do arroz. O painel
comparativo de outras culturas mantém-se separado e limitado a arroz, milho e girassol.
Desenvolvido pela Consulai.

Este repositório contém o site já construído, pronto para o GitHub Pages. A navegação
apresenta Produção e preços, Consumo, Comércio internacional, Preços no retalho,
Cotações, Inputs agrícolas e Outras culturas. As cotações incluem girassol; o painel
comparativo também apresenta as cotações de cereais. O painel de retalho foi
acrescentado a 13/10/2026 (ver `../precos-arroz/README.md`).

Na página «Cotações», os preços de arroz e de outras culturas são apresentados por
país, produto e praça. As cotações ISMEA incluem todas as praças publicadas; a página
não estima preços para variedades sem cotação, como Ribe quando ausente da fonte.

## Publicar
1. Settings › Pages › Build and deployment › Source: **Deploy from a branch**.
2. Branch: **main**, pasta **/ (root)** › Save.
3. O site fica em `https://<utilizador>.github.io/<repositório>/` ao fim de 1–2 minutos.

## Atualizar
Substituir os ficheiros por uma versão nova do site construído e enviar (commit + push).
Os dados estão em `observatory-data.json`.

Para atualizar as cotações oficiais, executar na raiz do repositório:

```bash
python precos-arroz/tools/observatorio/update_market_quotes.py
```

O importador lê a tabela pública completa do ISMEA, o consultor oficial da Lonja de
Sevilla e a exportação do dashboard oficial Cereals prices da Comissão Europeia para
Portugal, Grécia, Bulgária e França. Só são usados preços publicados, sem estimativas.
As cotações de cereais são adicionadas ao painel «Cotações», não ao painel comparativo.
