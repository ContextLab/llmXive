# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'planned'; worst unresolved severity = 'methodology'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Handling Missing Data: The plan states entries missing thermodynamic data are 'excluded from the thermodynamic model but retained for the composition-only baseline.' This creates a selection bias where the Thermo model is trained only on alloys for which MP data exists (potentially a specific subset of alloys), while the Baseline is trained on the full set. This violates the assumption of a fair comparison. The Baseline should ideally be trained on the same subset of data as the Thermo model to isolate the feature effect, or the missing data mechanism must be explicitly modeled.
