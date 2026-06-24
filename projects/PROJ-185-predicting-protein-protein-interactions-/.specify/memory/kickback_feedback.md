# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 3 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'science'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan does not reference the `predicted_edges.schema.yaml` contract; no task or test is defined to validate the `results/edges/<species>_raw_edges.tsv` file against this schema (original concern plan_consistency-c6dd014f).
- The validation target (STRING high‑confidence interaction set) is not independent of the predictor because STRING’s combined scores incorporate co‑expression evidence, which is the same signal used to generate the predicted edges. Using this benchmark creates a circular validation: the model is being evaluated against a ground‑truth that partially derives from the very data (gene expression) it predicts from, inflating performance metrics and undermining the scientific claim that co‑expression alone recovers true PPIs.
- The validation target (STRING high‑confidence interaction set) is not independent of the predictor because STRING’s combined scores incorporate co‑expression evidence, which is the same signal used to generate the predicted edges. This creates a circular validation that inflates performance metrics and undermines the claim that co‑expression alone recovers true PPIs.
