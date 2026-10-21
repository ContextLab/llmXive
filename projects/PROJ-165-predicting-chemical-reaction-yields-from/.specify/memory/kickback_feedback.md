# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan states that IR spectra are resampled to 400‑4000 cm⁻¹ at 1 cm⁻¹ steps and NMR to 0‑10 ppm at 0.01 ppm steps, which yields 1000 points per spectrum. However, the `dataset.schema.yaml` contract defines `ir_spectrum` and `nmr_spectrum` with `minItems: 200` and `maxItems: 200`. This length mismatch means data produced by the pipeline would not validate against the contract.
- The core hypothesis (spectra add predictive signal beyond fingerprints) cannot be empirically tested because no verified open dataset provides paired IR + ¹H‑NMR spectra **and** reaction yields for the same reaction. The plan merely aborts with a `DATA_INSUFFICIENT` error and logs the failure, without proposing any alternative data acquisition strategy (e.g., experimental measurement, simulation, or curated proprietary dataset). Consequently, the primary research question remains untestable in the current project scope, violating scientific soundness.
