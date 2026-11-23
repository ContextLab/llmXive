# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 5 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- T045a (Implement outer CV split) depends on 'Paired samples (T006)'. T006 is in Phase 0.1. This is correct. T045b (Inner CV alpha tuning) depends on 'Fold indices (T045a)'. This is correct. T045c (Train final model) depends on 'Fold indices, alpha values'. This is correct. T045d (Serialize model) depends on 'Trained models (T045c)'. This is correct. T047 (Permutation test) depends on 'T045c'. This is correct. T055 (Cross-species model) depends on 'Data after T036/T037 (z-score + ComBat)'. T036/T037 are in Phase 4. This is correct. The ordering within Phase 5 is correct.
- Task T001a (Download gene expression) and T001b (Parse) are grouped by dataset but T001a covers two datasets (GSE21857, GSE167633). Split T001a into 'Download GSE21857' and 'Download GSE167633' to allow parallel execution and independent failure handling.
- Task T032a, T032b, T032c (KEGG mapping) are split but T032a (Fetch) and T032b (Map) are tightly coupled. Consider merging T032a/b into a single 'Implement KEGG fetch and mapping pipeline' task, or ensure T032b explicitly handles the case where T032a fails (abort logic).
- Task T045a, T045b, T045c, T045d (Modeling pipeline) are split by step but T045a (Outer CV) and T045b (Inner CV) are logically one 'Nested CV' operation. Split T045a/b into 'Implement nested CV split logic' and 'Implement alpha tuning loop' for better granularity.
- Task T021-INIT (Setup CI resource monitoring) is too coarse. It mixes timer initialization, abort logic, and file creation. Split into: 1) Create `runtime_monitor.json` schema, 2) Implement timer initialization logic, 3) Implement abort check function.
