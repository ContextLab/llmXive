# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 5 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'requirement'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-001 requires downloading a public AM‑alloy dataset that contains the exact columns `laser_power`, `scan_speed`, `layer_thickness`, `alloy_composition`, `yield_strength`, and `ductility` (≥ 50 samples). The plan uses a proxy dataset (`doe.csv`) with columns `x1`, `x2`, `x3`, `response` and explicitly states that FR‑001 cannot be fully satisfied. No alternative task or mitigation is provided, leaving the functional requirement unimplemented.
- SC‑004 demands measuring the correlation between permutation‑importance rankings and an independent reference ranking from prior literature. The plan’s Task T005 computes permutation importance but notes that no external ranking exists for the proxy dataset and therefore does not perform any correlation measurement, leaving the success criterion unmet.
- SC‑006 requires that after preprocessing the CSV contains **all required columns** (`laser_power`, `scan_speed`, `layer_thickness`, `alloy_composition`, `yield_strength`, `ductility`) with no missing values. Because the plan operates on a proxy dataset lacking these columns, this criterion is not addressed anywhere in the plan.
- SC‑007 calls for reporting subgroup R² scores for each alloy type and comparing them to the overall R² to assess confounding. The plan’s Task T010 produces a `confounders.json` with correlation and VIF diagnostics but does not compute or report per‑alloy‑type R² metrics, so the criterion is missing.
- SC‑008 requires demonstrating the impact of controlling for alloy composition (and any microstructural covariates) by reporting model performance with and without those covariates and showing a minimum ΔR² ≥ 0.02 or ΔRMSE ≥ 5 %. The plan includes confounder detection (Task T010) but does not generate the required comparative performance results, leaving the success criterion unfulfilled.
