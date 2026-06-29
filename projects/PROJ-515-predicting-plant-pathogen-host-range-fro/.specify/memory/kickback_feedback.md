# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 2 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T017 'Create run_pipeline.sh CLI entry point' fails the 'Concrete deliverable' test. It does not specify the exact command-line arguments (e.g., `--data-dir`, `--mode`, `--seed`) or the exact output artifacts (e.g., `model.pkl`, `feature_importance.csv`) that must be generated to mark the task as done. The 'Independent Test' section describes a test, but the task itself lacks the specific artifact definitions.
- Task T030 ('Implement Sensitivity Mode... treating missing interactions as negative') addresses FR-016. However, FR-016 requires a 'sensitivity analysis' comparing the 'unknown' treatment against the 'negative' treatment. The task only describes implementing the 'negative' mode logic. It lacks a specific task to *perform the comparison* and *report the variance* as mandated by FR-016 ('the pipeline MUST report the variance... and flag'). While T032 mentions comparing AUPRC, T030's description is incomplete regarding the full FR-016 requirement to handle the 'unknown' baseline logic within the same task scope or ensure the comparison logic is explicitly tied to the sensitivity analysis output.
