# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Power is estimated with `statsmodels.stats.power.TTestIndPower`, which assumes a two‑sample t‑test. The primary association tests (Spearman correlation on CLR data and MaAsLin2 linear models) are not simple t‑tests, so the chosen power‑analysis method does not match the statistical model being evaluated.
