# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'science'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan states that a verified SORCE/TIM TSI dataset is not available and substitutes CMIP6 solar forcing as a proxy, yet the contract `contracts/dataset.schema.yaml` mandates a **tsi** dataset with fields `date`, `tsi_value`, `instrument`, `uncertainty`. No step in the plan ingests or validates such a TSI dataset, leaving the contract unexercised.
- The plan validates the reconstructed TSI by comparing it to the CMIP6 solar‑forcing series, which is also the target variable used during model training (see Phase 2 – Model Training & Validation). This makes the validation target not independent of the predictor (GSN), resulting in a circular evaluation that cannot substantiate the claim of accurate TSI reconstruction.
- Success Criterion SC‑001 requires a ≥15 % reduction in RMSE versus the 2007 baseline reconstruction, yet the 2007 baseline dataset is explicitly unavailable (see Research.md). The plan states the reduction will be omitted, but the output schema still mandates fields like `rmse_reduction_percentage`, `baseline_rmse`, and `baseline_r2`. Consequently the metric cannot be measured, rendering the claimed improvement non‑empirical.
