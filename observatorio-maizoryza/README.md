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

## Alterações de 18/11/2026 (vaga 15)

- Gráficos de grãos (Painel 1, gráfico 02, e Painel 3, gráfico 02): cada grão vale uma quantidade
  redonda, indicada na legenda (por exemplo, 1 grão = 50 mil t); o último grão aparece cortado na
  fração certa.
- Painel 1, gráfico 04: acrescentada Espanha (província de Sevilha), em percentagem da área semeada
  por variedade, a partir dos boletins finais da RAIF (Junta de Andalucía) de 2022, 2024 e 2025.
- Painel 5 «Cotações»: cereais e girassol (semente, óleo bruto e bagaço) da DG AGRI para todos os
  Estados-Membros com cotação publicada; a lista de países passa a incluí-los.
- O bundle foi alterado por `precos-arroz/tools/observatorio/patch_vaga15.py`. Num build novo,
  correr `patch_bundle.py` e depois `patch_vaga15.py`.

## Alterações de 18/11/2026 (vaga 16)

- Painel 7 «Outras culturas»: o quadro de cotações saiu (continua na página Cotações) e a comparação
  entre culturas passa a incluir todas as culturas das cotações (arroz, milho, girassol, trigo mole,
  trigo duro, cevada, aveia, centeio e triticale), com as mesmas fontes dos gráficos: Eurostat
  apro_cpsh1 (produção, 2021 a 2025), Comext DS-045409 (comércio, 2015 a 2025) e apri_ap_crpouta
  (preço na produção, 2015 a 2024).
- Bundle alterado por `precos-arroz/tools/observatorio/patch_vaga16.py`, a correr depois de
  `patch_vaga15.py`.

## Alterações de 18/11/2026 (vaga 17)

- Painel 7: cada um dos três gráficos tem uma fila de botões «Culturas» para escolher as culturas
  mostradas. «Todas» repõe todas; com todas ativas, clicar numa cultura mostra só essa; depois,
  cada clique junta ou retira culturas. O Excel de cada gráfico segue a seleção.
- Bundle alterado por `precos-arroz/tools/observatorio/patch_vaga17.py`, a correr depois de
  `patch_vaga16.py`.

## Alterações de 18/11/2026 (vaga 18)

- Painel 7, gráfico 02: trigo mole, trigo duro, cevada, aveia, centeio e triticale passam a ter
  ilustrações próprias, ao estilo dos ícones de arroz, milho e girassol.
- Bundle alterado por `precos-arroz/tools/observatorio/patch_vaga18.py`, a correr depois de
  `patch_vaga17.py`.

## Alterações de 19/11/2026 (vaga 19)

- Painel 1, gráfico 04 (área por variedade): por baixo do título ficam, lado a lado, as listas «País» e
  «Variedade». A variedade escolhida filtra a tabela e o Excel; ao mudar de país volta a «Todas». Os
  botões de país do canto superior direito saíram. Pedido da Beatriz Cardoso nos comentários do artifact.
- Painel 1, cartão «Importações de arroz»: o «i» passa a explicar com rigor o indicador (Comext DS-045409,
  código NC 1006, euros correntes, total anual com peso líquido, linha mensal com variação homóloga,
  Estados-Membros com comércio total e UE só extra-UE). A correção por script no index.html da raiz saiu.
- Painel 3, cartão «Importações líquidas»: o «i» passa a ter uma definição curta e simples
  (importações menos exportações, em toneladas, todo o arroz NC 1006; fonte Eurostat Comext).
- Bundle alterado por `precos-arroz/tools/observatorio/patch_vaga19.py`, a correr depois de
  `patch_vaga18.py`.

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
Sevilla e a exportação do dashboard oficial Cereals prices da Comissão Europeia (DG AGRI)
para todos os Estados-Membros, incluindo as cotações de girassol do painel Oilseeds prices. Só são usados preços publicados, sem estimativas.
As cotações de cereais são adicionadas ao painel «Cotações», não ao painel comparativo.
