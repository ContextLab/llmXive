# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 1 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- T030 (Binary Logistic Regression) lists dependencies: `T018c, T015, T026`. T015 is the 'Ingest Pipeline Orchestrator' for US1. T018c is the 'Feature Pipeline' for US2. T026 is the 'Static Analysis Pipeline' for US4. This is correct. However, T030a (McFadden's Pseudo R²) depends on T030. T030b (Report Generator Update) depends on T030a. T033 (Report Generator) depends on T030b. This chain is correct. But T031 (McNemar's test) depends on T015 and T026. T031 is listed as 'parallel consumers of T015/T026'. This is correct. The issue is T030's dependency on T015. T015 produces `predictions.csv`. T030 needs `predictions.csv` (from T015) and `features.csv` (from T018c). This is correct. The ordering seems valid here, but the previous errors in Phase 2 are critical.
