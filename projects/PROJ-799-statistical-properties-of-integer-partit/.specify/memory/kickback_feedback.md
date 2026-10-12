# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'science'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The `regression_output.schema.yaml` expects fields `mse` and `cv_mse`, but the plan's output (`model_results.json`) provides only `mse_cv`. This discrepancy will cause the contract tests to fail.
- The validation target R(n)=log(p_P(n))−log(Q_as(n)) is defined using the asymptotic baseline Q_as(n), which itself is a function of the prime‑density quantities (π(n), 1/ln n, ∑_{p≤n}1/p) that are later used as predictors in the regression. This creates a circular/tautological validation: any correlation between R and those predictors is at least partially forced by the way Q_as was constructed, so the analysis cannot cleanly separate a genuine systematic correction from artefacts of the baseline definition.
