# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 6 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The primary constructs (cognitive load) are measured only by `time‑to‑success` and `iteration_count`. These proxies may not fully capture cognitive load, which is typically also assessed via subjective (NASA‑TLX) or physiological measures. Relying solely on latency/iterations threatens construct validity.
- Power analysis uses α = 0.05, but the final tests apply a Bonferroni‑corrected α = 0.025. The required N≈28 therefore underestimates the sample size needed for the corrected significance level, risking insufficient power.
- Success is defined as both an exact vector match **and** a semantic similarity ≥ 0.95. This dual‑threshold is very strict and may discard many otherwise correct edits, reducing usable data and further lowering statistical power. The rationale for the 0.95 cutoff is not justified.
- Only counterbalancing of interface order is mentioned; no wash‑out period or task‑level randomization to mitigate carry‑over learning effects. Without a separation interval, performance on the second interface may be inflated by practice.
- Aborted tasks are excluded from `time‑to‑success` but retained in `iteration_count` analysis. This asymmetric treatment can bias the iteration metric, as longer‑running (failed) tasks inflate iteration counts while not contributing to latency statistics.
- The plan assumes participant expertise is homogeneous, yet no stratification or covariate control is described. Differences in prior experience with figure editing could confound the observed latency/iteration differences.
