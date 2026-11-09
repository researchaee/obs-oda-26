var MzQuoteCropLabels = {
  rice: `Arroz`,
  maize: `Milho`,
  sunflower: `Girassol`,
  soft_wheat: `Trigo mole`,
  durum_wheat: `Trigo duro`,
  barley: `Cevada`,
  oats: `Aveia`,
  triticale: `Triticale`
};

function MzMarketQuotes({ records, country }) {
  let allRows = records
    .filter((row) => row.country_code === country && row.source === `ISMEA`)
    .sort(
      (a, b) =>
        (a.crop === `rice` ? -1 : b.crop === `rice` ? 1 : 0) ||
      (MzQuoteCropLabels[a.crop] ?? a.crop).localeCompare(
        MzQuoteCropLabels[b.crop] ?? b.crop,
        `pt`
      ) ||
        a.product.localeCompare(b.product, `pt`) ||
        a.market.localeCompare(b.market, `pt`)
    );
  let [crop, setCrop] = (0, l.useState)(`all`);
  let rows = allRows.filter((row) => crop === `all` || row.crop === crop);
  if (!allRows.length) return null;

  return (0, T.jsxs)(`section`, {
    className: `visual-card`,
    id: `quotes-ismea-cereals`,
    children: [
      (0, T.jsxs)(`div`, {
        className: `visual-head`,
        children: [
          (0, T.jsxs)(`div`, {
            children: [
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
      (0, T.jsxs)(`div`, {
        className: `month-filter quote-country-filter mz-filter`,
        children: [
          (0, T.jsxs)(`label`, {
            children: [
              `Cultura`,
              (0, T.jsxs)(`select`, {
                "aria-label": `Filtrar por cultura`,
                value: crop,
                onChange: (event) => setCrop(event.target.value),
                children: [
                  (0, T.jsx)(`option`, { value: `all`, children: `Todas as culturas` }),
                  ...Array.from(new Set(allRows.map((row) => row.crop))).map((value) =>
                    (0, T.jsx)(
                      `option`,
                      { value, children: MzQuoteCropLabels[value] ?? value },
                      value
                    )
                  )
                ]
              })
            ]
          }),
          (0, T.jsx)(`small`, { children: `${rows.length} cotações` })
        ]
      }),
      (0, T.jsx)(`div`, {
        className: `mz-scroll`,
        children: (0, T.jsxs)(`table`, {
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
                      (0, T.jsx)(`td`, {
                        "data-label": `Cultura`,
                        children: MzQuoteCropLabels[row.crop] ?? row.crop
                      }),
                      (0, T.jsx)(`td`, { "data-label": `Produto`, children: row.product }),
                      (0, T.jsx)(`td`, { "data-label": `Praça`, children: row.market }),
                      (0, T.jsx)(`td`, { "data-label": `Condição`, children: row.stage }),
                      (0, T.jsx)(`td`, { "data-label": `Data`, children: row.date }),
                      (0, T.jsx)(`td`, {
                        className: `num`,
                        "data-label": `Cotação (€/t)`,
                        children: row.price_eur_t == null ? `—` : `${N(row.price_eur_t, 1)}`
                      }),
                      (0, T.jsx)(`td`, {
                        className: `num`,
                        "data-label": `Variação semanal`,
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
      })
    ]
  });
}
