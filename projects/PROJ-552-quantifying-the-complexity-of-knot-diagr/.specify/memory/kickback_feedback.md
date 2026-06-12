# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 6 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- FR-003 mandates 'Reference implementations and mathematical definitions documented in docs/reproducibility/invariant_algorithms.md'. T054 lists 'algorithm_validation.md' (FR-003) but omits 'invariant_algorithms.md' from its required documents list. No other task creates this document.
- T008 creates base directory structure (data/raw, data/processed, data/plots, docs/reproducibility) but T001c and T001d already create these exact subdirectories in Phase 1. This is duplicate work violating efficient ordering. T008 should be removed or merged with T001-T003.
- T046 'Generate derivation notes' doesn't specify required content sections (formula citations, transformation logic, etc.) per FR-007.
- Constitution infrastructure tasks (T065 citation validation, T066 content hashing) lack explicit linkage to Constitution principles (II and V respectively) in task descriptions for audit traceability.
- T054 documentation list includes 'logs.md' but FR-007 doesn't specify a filename, and T049 creates 'operation_logs.md'. This creates ambiguity about which file to reference. Align T054's list with actual filenames (e.g., operation_logs.md).
- T065-T066 implement Constitution Principles II and V but lack explicit linkage to Constitution principles in task descriptions for audit traceability. Add explicit principle citations (e.g., 'per Constitution Principle II') to task descriptions.
