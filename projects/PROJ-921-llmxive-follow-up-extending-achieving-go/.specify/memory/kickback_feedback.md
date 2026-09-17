# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- The plan.md Summary and Complexity Tracking explicitly state the analysis uses a Linear Mixed Effects (LME) model. The spec.md FR-005 mandates Point-Biserial and t-test. The tasks only cover the spec's Point-Biserial/t-test (T028, T029) but lack any task to implement the LME model proposed in the plan. This is a missing task for the plan's architectural element (LME model).
- Task T028/T029 implement Point-Biserial and t-test, but the plan.md (Summary & Complexity Tracking) explicitly mandates a Linear Mixed Effects (LME) model to handle nested data and interaction effects. The task order implements the spec's outdated requirement (FR-005) rather than the plan's corrected methodology, creating a semantic dependency violation where the analysis tasks do not produce the artifact required by the approved plan.
