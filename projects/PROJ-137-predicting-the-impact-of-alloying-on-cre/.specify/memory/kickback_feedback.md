# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'clarified'; worst unresolved severity = 'requirement'. Routing to 'specified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Unresolved Methodology Concern: The spec retains the selection bias identified in the kickback. FR-002 states entries missing thermodynamic data are 'excluded from the thermodynamic model but retained for the composition-only baseline.' FR-004 and FR-005 define the comparison between these two models. This creates a non-comparable dataset split (Thermo model on subset A, Baseline on set A+B), violating the fair comparison requirement. The spec must mandate that the Baseline model is trained on the SAME subset of data as the Thermo model (i.e., only entries with valid thermodynamic data) to isolate the feature effect, or explicitly define an imputation strategy for missing thermodynamic data.
