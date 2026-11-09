var MzQuoteCropLabels = {
  maize: `Milho`,
  sunflower: `Girassol`,
  soft_wheat: `Trigo mole`,
  durum_wheat: `Trigo duro`,
  barley: `Cevada`,
  oats: `Aveia`,
  triticale: `Triticale`
};

function MzMarketQuotes({ records, country, countryLabel }) {
  let rows = records
    .filter((row) => row.country_code === country && row.source === `ISMEA` && row.crop !== `rice`)
    .sort(
      (a, b) =>
        a.crop.localeCompare(b.crop, `pt`) ||
        a.product.localeCompare(b.product, `pt`) ||
        a.market.localeCompare(b.market, `pt`)
    );
  if (!rows.length) return null;

  return (0, T.jsxs)(`section`, {
    className: `visual-card`,
    id: `quotes-ismea-cereals`,
    children: [
      (0, T.jsxs)(`div`, {
        className: `visual-head`,
        children: [
          (0, T.jsxs)(`div`, {
            children: [
              (0, T.jsx)(`h2`, {
                className: `chart-title`,
                children: `Cotações de cereais — ${countryLabel}`
              }),
              (0, T.jsx)(`p`, {
                className: `chart-note`,
                children: `ISMEA Mercati · valores por produto, praça e condição, em €/t.`
              })
            ]
          }),
          (0, T.jsx)(B, {
            href: rows[0].source_url,
            children: `ISMEA Mercati`
          })
        ]
      }),
      (0, T.jsxs)(`table`, {
        className: `quote-table`,
        children: [
          (0, T.jsx)(`thead`, {
            children: (0, T.jsxs)(`tr`, {
              children: [
                (0, T.jsx)(`th`, { children: `Cultura` }),
                (0, T.jsx)(`th`, { children: `Produto` }),
                (0, T.jsx)(`th`, { children: `Praça` }),
                (0, T.jsx)(`th`, { children: `Condição` }),
                (0, T.jsx)(`th`, { children: `Data` }),
                (0, T.jsx)(`th`, { className: `num`, children: `Cotação (€/t)` }),
                (0, T.jsx)(`th`, { className: `num`, children: `Variação semanal` })
              ]
            })
          }),
          (0, T.jsx)(`tbody`, {
            children: rows.map((row) =>
              (0, T.jsxs)(
                `tr`,
                {
                  children: [
                    (0, T.jsx)(`td`, { children: MzQuoteCropLabels[row.crop] ?? row.crop }),
                    (0, T.jsx)(`td`, { children: row.product }),
                    (0, T.jsx)(`td`, { children: row.market }),
                    (0, T.jsx)(`td`, { children: row.stage }),
                    (0, T.jsx)(`td`, { children: row.date }),
                    (0, T.jsx)(`td`, {
                      className: `num`,
                      children: row.price_eur_t == null ? `—` : `${N(row.price_eur_t, 1)}`
                    }),
                    (0, T.jsx)(`td`, {
                      className: `num`,
                      children:
                        row.weekly_change_pct == null
                          ? `—`
                          : `${N(row.weekly_change_pct, 1)}%`
                    })
                  ]
                },
                `${row.crop}-${row.product}-${row.market}-${row.stage}-${row.date}`
              )
            )
          })
        ]
      })
    ]
  });
}
