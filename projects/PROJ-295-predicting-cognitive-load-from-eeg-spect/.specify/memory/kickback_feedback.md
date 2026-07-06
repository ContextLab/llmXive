# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 6 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- Task T003 [P] Configure linting. This is parallel-safe. However, T002 (Initialize Python project) must complete before T003 can configure tools within that project. The [P] tag is correct for parallel execution *after* T002, but the list order T001, T002, T003 is correct. No violation here, just noting the dependency.
- Task T015 (alignment logic) depends on T012 (download) and T013 (preprocess). The list order is T012, T014, T013, T015. This is correct. T016 (error handling) depends on T015. Correct. T017 (validation) depends on T013/T015. Correct.
- Task T023 (label generation) depends on T021 (feature extraction) for the 'clean epochs' input? No, T023 depends on 'aligned behavioral logs' (from US1) and 'clean epochs' (from US1). T021 depends on 'clean epochs' (from US1). T021 and T023 are parallel in terms of US1 dependency, but T023 (label generation) might be needed for T021? No, T021 is features, T023 is labels. They are parallel. T026 validates both. Correct.
- Task T031 (train_model) depends on T021 (features) and T023 (labels). T032 (evaluate) depends on T031. T033 (correction) depends on T032. T034 (reporting) depends on T033. T035 (visualization) depends on T034. T036 (validation) depends on T032/T034. The list order T031-T036 is correct.
- Task T007 (manifest.json structure) depends on T001 (project structure). T008 (env config) is parallel. T004 (pipeline_config) is parallel. T006 (schemas) is parallel. T005 (validate) depends on T006. The list order T006, T005, T004, T007, T008 is correct.
- Task T042 (retention check) depends on T013 (ICA) and T017 (validation). T042 is listed after T017. Correct.
