# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 26 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- SC-005 (computational feasibility measured by runtime) requires a task to measure and report the total pipeline runtime. T034b-PilotRuntime measures pilot runtime. T052-Exec executes the pipeline and logs to `pipeline_execution.log`. T052-Report generates `runtime_verification.md`. This covers SC-005. However, T034b-PilotRuntime and T052-Exec/T052-Report seem to duplicate the runtime measurement. T034b is for pilot size determination. T052 is for final verification. This is acceptable. No missing task here.
- T008b is tagged [US1] but the description says 'This utility MUST be invoked by the data pipeline task (T015)'. T015 is in Phase 3. T008b is in Phase 2. The tag [US1] is correct as it supports US1. However, the task T008b is described as 'Implement conformer_params.json generator utility'. The Plan.md T014 says 'Log parameters to conformer_params.json'. The task T015 says 'Invoke the utility from T008b'. This is consistent. No missing task.
- T024 is listed as 'Removed: Merged into T025'. However, the Plan.md Phase 3 lists T024 as 'Geometry Oracle Evaluation'. The Spec FR-004 requires a 'Geometry-Based Baseline'. T021b implements a 'Geometry-Based Baseline' using Linear Regression. T024 (removed) was 'Geometry Oracle Evaluation'. The Plan.md has both T024 (Oracle) and T029 (Primary Metric Calculation). The tasks.md has T021b (Baseline) and T025 (Comparison). The 'Geometry Oracle' (direct calculation) from Plan.md T024 is not explicitly implemented as a separate task in tasks.md. T021b trains a model. Is the 'Geometry Oracle' the same as the 'Geometry-Based Baseline'? The Plan.md says 'The baseline is defined as the direct computation of SASA via RDKit on the test set (the "Geometry Oracle")'. This implies the baseline is NOT a trained model, but a direct calculation. T021b trains a Linear Regression model. This is a contradiction. T021b implements a trained model, but the Plan says the baseline is a direct calculation. T024 (direct calculation) is removed. Therefore, the 'Geometry Oracle' baseline required by the Plan is missing from the tasks. T021b implements a different baseline (trained model). This is a coverage gap for the Plan's specific baseline definition.
- T034b-PilotRuntime and T052-Exec/T052-Report both measure runtime. T034b is for pilot size. T052 is for final verification. This is acceptable. However, T034b outputs `pilot_timing.json` and `runtime_verification.md`. T052-Report also outputs `runtime_verification.md`. This is a duplicate output file. T034b should output `pilot_timing.md` or similar. T052-Report should output `final_runtime_verification.md`. The duplicate file name `runtime_verification.md` is a writing issue, not a coverage gap.
- T017 'Add validation and error handling for invalid SMILES and failed conformer generation' is a generic task. T048 (Ingestion) and T015 (Conformer) already have specific error handling logic (T048: 'Strict Fallback Logic', 'Max Atoms Filter'; T015: 'halt with critical error if >10%'). T017 seems redundant. It might be a stale task or a catch-all that is already covered. If it's redundant, it's a writing issue. If it's meant to cover edge cases not in T048/T015, it's vague. No missing task, but potential redundancy.
- T018 'Add logging for excluded molecules and dataset statistics' is a generic task. T048 logs excluded molecules. T015 logs failure count. T016 logs split report. T018 seems redundant. Writing issue.
- T050 'Implement gradient accumulation logic' is tagged [US2]. It is a prerequisite for T022. T022 depends on T050. This is correct. No missing task.
- T026 and T027 are contract/unit tests for US3. They are present. No missing task.
- T032a, T032b, T033, T034a, T035, T036 are polish tasks. They are present. No missing task.
- T045, T046, T053, T055 are robustness tasks. They are present. No missing task.
- T001a-d, T002, T003, T004, T005, T006, T049 are setup tasks. They are present. No missing task.
- T007, T008a, T008b, T009, T010, T011 are foundational tasks. They are present. No missing task.
- T012, T013 are tests for US1. They are present. No missing task.
- T019, T020 are tests for US2. They are present. No missing task.
- T026, T027 are tests for US3. They are present. No missing task.
- T032a, T032b, T033, T034a, T035, T036 are polish tasks. They are present. No missing task.
- T045, T046, T053, T055 are robustness tasks. They are present. No missing task.
- T001a-d, T002, T003, T004, T005, T006, T049 are setup tasks. They are present. No missing task.
- T007, T008a, T008b, T009, T010, T011 are foundational tasks. They are present. No missing task.
- T012, T013 are tests for US1. They are present. No missing task.
- T019, T020 are tests for US2. They are present. No missing task.
- T026, T027 are tests for US3. They are present. No missing task.
- T032a, T032b, T033, T034a, T035, T036 are polish tasks. They are present. No missing task.
- T045, T046, T053, T055 are robustness tasks. They are present. No missing task.
- T022 (Training Loop) is marked [P] but depends on T050 (Gradient Accumulation logic) and implicitly on T021a (Model Definition). The description states 'incorporating gradient accumulation logic from T050'. If T050 is a prerequisite logic block, T022 cannot be parallel-safe relative to it. Furthermore, training requires the dataset from Phase 3, making it sequential to the entire data pipeline.
- T028 description states 'Must run after... T028 (Absolute)'. This is a self-reference error. It should likely reference T021b/T022 or T040. This is a writing nit but obscures the true dependency chain.
