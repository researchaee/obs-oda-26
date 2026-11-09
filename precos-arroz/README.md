# Preços do arroz no retalho (Observatório do Arroz)

Recolha semanal dos preços de arroz nas lojas online de Continente, Pingo Doce,
Auchan, Intermarché e El Corte Inglés, com um dashboard por tipo de arroz
(mínimo, máximo, média e mediana do €/kg, por cadeia e por segmento de marca).

## Onde aparece

- **No observatório:** Painel 5 «Preços no retalho» (navegação, cartão na página inicial,
  respostas do Assistente IA e entradas no catálogo de fontes). Os dados vão para a chave
  `retail` de `observatorio-maizoryza/observatory-data.json`, e o histórico para `history.retail`.
- **Página à parte (opcional):** `precos-arroz/index.html`.

A recolha semanal (`.github/workflows/precos-arroz.yml`, na raiz do repositório) corre o
scraper, atualiza o `observatory-data.json` e faz commit sozinha às segundas-feiras.

## Se substituir o site por um build novo

O painel 5 foi injetado no site construído (o código-fonte da vaga 13 não estava disponível).
Se publicar um build novo do observatório, volte a aplicá-lo:

```bash
python precos-arroz/tools/observatorio/patch_bundle.py .
cd precos-arroz && python -m tools.merge_into_observatory
```

O script verifica cada alteração e pára sem estragar nada se o bundle for diferente.
O painel de retalho e o componente de cotações ISMEA (`tools/observatorio/mz_market_quotes.js`)
estão fora do código-fonte original; quando houver código-fonte, passar ambos para lá.

Para atualizar as cotações oficiais de mercado (ISMEA Mercati e Lonja de Sevilla), executar
na raiz do repositório:

```bash
python precos-arroz/tools/observatorio/update_market_quotes.py
```

Este importador atualiza a página «Cotações» e mantém o painel comparativo limitado às
culturas que já contém.

## Correr à mão (no teu computador)

```bash
cd precos-arroz
pip install -r requirements.txt
python -m scraper.run                      # todas as cadeias (Intermarché: ~150 lojas, 5–10 min)
python -m scraper.run --intermarche-lojas 10   # teste rápido
python -m tools.merge_into_observatory     # leva os dados para o observatório (painel 5)
python -m tools.build_dashboard            # atualiza a página à parte precos-arroz/index.html
```

Se os sites bloquearem os servidores do GitHub (aparece um aviso no dashboard e
o erro no log do Actions), corre os mesmos comandos no teu computador e faz push.

## Ficheiros de dados (`data/`)

| Ficheiro | Conteúdo |
|---|---|
| `precos_arroz_AAAA-MM-DD.csv` | Todos os produtos de arroz do dia, já classificados |
| `historico_precos_arroz.csv` | Acumulado de todas as recolhas (base para o índice de preços) |
| `intermarche_lojas.csv` | Preço de cada produto em cada loja Intermarché (com localidade, código postal e coordenadas, para médias por distrito) |
| `latest.json` | Produtos e estatísticas da última recolha (lido pelo dashboard) |

Colunas principais: `cadeia, tipo, segmento, marca, nome, peso_g, preco, eur_kg, preco_ref, promo, n_lojas, preco_min_lojas, preco_max_lojas`.

## Como funciona cada cadeia

| Cadeia | Fonte | Notas |
|---|---|---|
| Continente | `Search-UpdateGrid` (SFCC), categoria arroz | Preço riscado = PVPR |
| Pingo Doce | `Search-UpdateGrid` (SFCC), categoria arroz | Ignora produtos patrocinados; «Un» lido como kg |
| Auchan | `Search-UpdateGrid` (SFCC), categoria arroz | Mostra o PVP recomendado quando há desconto |
| Intermarché | API JSON da loja online, loja a loja | Preço = mediana entre lojas; ~120 lojas sem loja online são ignoradas |
| El Corte Inglés | Páginas HTML da categoria arroz | 20 produtos por página |

A classificação (tipo de arroz e segmento) está em `scraper/common.py`
(listas `TIPOS`, `PREPARADOS`, `MARCAS_PROPRIAS`, `MARCAS_PREMIUM`): para
corrigir um produto mal classificado, acrescentar a palavra-chave ou a marca.

## Limitações

- Lidl, Aldi e Mercadona não vendem mercearia online em Portugal.
- Preços online podem diferir da loja física.
- Se um site mudar o HTML, a recolha dessa cadeia devolve 0 produtos: o run
  regista o erro e o dashboard mantém os preços da recolha anterior, com aviso.
- Recolha 1 vez por semana, com pausas entre pedidos e User-Agent identificado.
