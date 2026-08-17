# Unresolved panel concerns (address in this revision)

The convergence panel for this stage could not resolve the concerns below within its round cap and kicked the project back for an IN-PLACE revision of the existing artifact. Revise the document to RESOLVE each concern — do NOT regenerate the document from scratch, and do NOT drop content that is not implicated by a concern.

**Why it was kicked back**: 71 concern(s) remained unresolved after 3 round(s) at stage 'tasked'; worst unresolved severity = 'requirement'. Routing to 'clarified' with full provenance so the next worker can address the root cause.

## Unresolved concerns

- T017 (Train Randomized Control Model) depends on T015b (Control Indices) and T024 (Model Implementation). T024 is in Phase 4 (US2). T015b is in Phase 3 (US1). This creates a valid cross-phase dependency. However, T017 is listed under 'Implementation for User Story 2' but logically belongs to the data preparation phase for the control experiment. The ordering is acceptable, but the task description in T017 says 'Use the same training script as T024/T025'. T025 (Training Loop) depends on T024b (Verify Model Size). T017 depends on T024 (Implementation). This is a valid producer-consumer flow: T024 produces the script, T017 uses it. No violation here, but the grouping is slightly confusing.
- T038a (Compute Correlation) and T038b (Verify Orthogonality Gate) are placed in Phase 3 (US1) and depend on T015 (PyBullet scores) and T018 (MuJoCo scores). T018 is also in Phase 3. This is correct. However, T038b is described as a 'HARD GATE before Phase 4'. The task list places T038a/b in Phase 3, which is correct. But T024 (Phase 4) depends on T038b. This is a valid cross-phase dependency. The ordering is correct: T015 -> T018 -> T038a -> T038b -> T024. No violation.
- T016c (Execute Augmentation) depends on T016 (Filtering Logic). T016 produces 'data/curated/curated_metadata.jsonl' with 'needs_augmentation'. T016c reads this flag. This is a valid producer-consumer flow. However, T016c is marked as 'Unconditional' in the description but the logic says 'If true... If false... exit'. This is a conditional execution, not unconditional. The dependency is correct, but the task description 'Unconditional' is misleading. The ordering is fine.
- T015b (Generate Randomized Control Indices) depends on T016c. T016c is the execution of augmentation. If T016c is a no-op (because needs_augmentation is false), T016c still runs and exits. T015b then runs. This is valid. However, T015b's logic says 'Read N_curated from data/curated/curated_metadata.jsonl (output of T016c)'. T016c updates this file. T016 also writes this file. If T016c is a no-op, T016's output is the source. If T016c runs, it updates the file. The dependency on T016c ensures the file is in its final state (post-augmentation or not). This is a valid ordering.
- T024 (Implement UNet-based diffusion model) depends on T038b (Orthogonality Gate). T038b is in Phase 3. T024 is in Phase 4. This is a valid cross-phase dependency. The gate must pass before training begins. Correct.
- T013 (Implement Wan2.1 video generation) depends on T012 (Load Verified Prompts). T012 is in Phase 2. T013 is in Phase 3. This is a valid producer-consumer flow. T012 produces 'data/prompts.jsonl', T013 consumes it. Correct.
- T015 (Implement physics scoring) depends on T015a (Create Physics Simulation Schema). T015a is in Phase 3. T015 is in Phase 3. T015a produces 'src/filtering/schema.py', T015 consumes it. Correct.
- T016 (Implement filtering logic) depends on T015 (Physics scoring) and T007b (Config). T015 produces 'data/curated/scores.parquet', T016 consumes it. T007b produces 'config.yaml', T016 consumes it. Correct.
- T018 (Run MuJoCo Validation) depends on T016 (Filtering Logic) for 'data/curated/' videos. T016 produces the curated videos. T018 consumes them. Correct.
- T038a (Compute Correlation) depends on T015 (PyBullet scores) and T018 (MuJoCo scores). T015 produces 'data/curated/scores.parquet', T018 produces 'data/validation/mujoco_scores.parquet'. T038a consumes both. Correct.
- T025 (Implement training loop) depends on T024b (Verify Model Size). T024b produces 'logs/model_size_verification.log'. T025 consumes the verified model. Correct.
- T026 (Implement data loader) depends on T024 (Model Implementation) and T025 (Training Loop) implicitly? No, T026 is part of T024/T025 implementation. The dependency list says 'Dependency: T024b'. This is slightly ambiguous. T026 is a sub-task of the training implementation. It should depend on T024 (Model) and T025 (Loop) or be part of them. The current dependency on T024b is weak. However, T026 is listed as a separate task. It depends on T024b (Model verified). This is acceptable.
- T029 (Instrument Training Metrics) depends on T025 (Training Loop). T025 produces the training loop. T029 instruments it. Correct.
- T017 (Train Randomized Control Model) depends on T015b (Control Indices) and T024 (Model Implementation). T015b produces 'data/control/indices.json'. T024 produces the model script. T017 consumes both. Correct.
- T031 (R-Bench scorer) and T032 (PAI-Bench scorer) are in Phase 5 (US3). They depend on T024 (Model) and T025 (Training) implicitly? No, they depend on the trained model. The dependency list is empty. They should depend on T024/T025 (Model trained). This is a missing dependency. The tasks assume the model is trained, but the ordering does not enforce it. This is a semantic violation: consumer (T031) before producer (T024/T025) is not enforced by the dependency list, though the phase structure implies it. The phase structure (Phase 5 after Phase 4) is correct, but the explicit dependency is missing.
- T034 (Stratified sampling) depends on T016c (Augmentation) implicitly? It says 'Sample from the *augmented* curated dataset (if T016c augmented)'. T016c is in Phase 3. T034 is in Phase 5. The dependency is valid. No explicit dependency listed, but phase ordering handles it.
- T035a (Statistical testing) and T036 (Performance gap) depend on T034 (Sampling) and T031/T032 (Scorers). No explicit dependencies listed. Phase ordering (Phase 5) handles it. Acceptable.
- T039 (Generate final JSON report) depends on T031, T032, T035a, T036. No explicit dependencies. Phase ordering handles it. Acceptable.
- T022 (Integration test for full evaluation) depends on T030 (Integration test for full evaluation pipeline). This is circular or redundant. T030 is the integration test. T022 is also an integration test. T022 depends on T030? No, T022 is the test. T030 is the test. This is a naming conflict. T022 in US2 is 'Integration test for training'. T022 in US3 is 'Secondary Benchmark'. The ID T022 is reused. This is a critical error. T022 in US3 should be a new ID. The dependency 'Dependency: T030' is also wrong. T030 is the test. T022 is the test. They are the same. This is a severe ordering/ID conflict.
- T022 (US2) depends on T024, T025. Correct. But T022 (US3) reuses the ID. This is a fatal ordering/ID violation. The engine cannot distinguish between the two T022 tasks. The dependency for T022 (US3) is 'T030', which is also a test. This is a mess. T022 (US3) should be T049 or similar. The dependency on T030 is also wrong. T030 is the test. T022 is the test. They are the same. This is a critical violation.
- T030 (Integration test for full evaluation pipeline) depends on T030b (Integration test for orthogonality check). T030b depends on T038c. T030 depends on T030b. This is valid. But T030 is the main test. T030b is a sub-test. The dependency is correct. However, T030 depends on 'Trained model, baseline model, n=30 eval set'. The trained model is from T024/T025. The baseline is from T033a. The eval set is from T034. No explicit dependencies. Phase ordering handles it.
- T030b (Integration test for orthogonality check) depends on T038c (Final Orthogonality Gate). T038c is in Phase 5. T030b is in Phase 5. T038c produces 'data/validation/final_orthogonality.json'. T030b consumes it. Correct.
- T033a (Load PhysisForcing Baseline) depends on nothing. It produces 'data/eval/physisforcing_baseline.json'. T033b depends on T033a. Correct. T039 depends on T033a (implicitly). Correct.
- T033b (Verify PhysisForcing Baseline) depends on T033a. Correct.
- T038c (Final Orthogonality Gate) depends on T015, T018. T015 produces PyBullet scores. T018 produces MuJoCo scores. T038c consumes both. Correct.
- T048 (Fail Loud data loader) depends on nothing. It is a sub-task of T026. No explicit dependency. Acceptable.
- CRITICAL: Task ID T022 is used twice. Once in US2 (Integration test for training) and once in US3 (Secondary Benchmark). This is a fatal ordering/ID violation. The engine cannot track dependencies for duplicate IDs. T022 (US3) must be renamed (e.g., T049). The dependency 'Dependency: T030' for T022 (US3) is also incorrect. T030 is the integration test. T022 is the benchmark. They are different. This is a severe violation.
- T011a, T011b, T011c are tests for US1. They depend on T012, T016, T015. No explicit dependencies. Phase ordering (Tests after Implementation) handles it. Acceptable.
- The duplicate ID T022 is the most severe ordering violation. It breaks the dependency graph. T022 (US3) must be renamed. The dependency 'T030' for T022 (US3) is also wrong. T030 is the integration test. T022 is the benchmark. They are different. This is a fatal violation.
- T015b depends on T016c. T016c is the augmentation execution. If T016c is a no-op, T016c still runs. T015b then runs. This is valid. However, T015b's logic says 'Read N_curated from data/curated/curated_metadata.jsonl (output of T016c)'. T016c updates this file. T016 also writes this file. If T016c is a no-op, T016's output is the source. If T016c runs, it updates the file. The dependency on T016c ensures the file is in its final state. This is a valid ordering.
- T017 depends on T015b and T024. T015b is in Phase 3. T024 is in Phase 4. T017 is in Phase 4. This is valid. T017 uses the control indices from T015b and the model from T024. Correct.
- T024 depends on T038b. T038b is in Phase 3. T024 is in Phase 4. This is valid. The gate must pass before training. Correct.
- T025 depends on T024b. T024b depends on T024. T025 is the training loop. T024 is the model. T024b verifies the model. T025 uses the verified model. Correct.
- T026 depends on T024b. T026 is the data loader. T024b verifies the model. The data loader is part of the training. This is acceptable.
- T027 (Checkpointing) depends on nothing. It is part of T025. Acceptable.
- T028 (Resource monitoring) depends on nothing. It is part of T025. Acceptable.
- T029 depends on T025. T029 instruments T025. Correct.
- T031, T032 depend on nothing. They are in Phase 5. They should depend on T024/T025 (Model trained). The phase ordering handles it, but explicit dependencies are missing. This is a minor violation.
- T034 depends on nothing. It is in Phase 5. It should depend on T016c (Augmentation). The phase ordering handles it. Acceptable.
- T035a, T036 depend on nothing. They are in Phase 5. They should depend on T034, T031, T032. The phase ordering handles it. Acceptable.
- T039 depends on nothing. It is in Phase 5. It should depend on T031, T032, T035a, T036. The phase ordering handles it. Acceptable.
- T030 depends on T030b. T030b depends on T038c. T030 is the integration test. T030b is the orthogonality test. T038c is the gate. This is valid.
- T030b depends on T038c. Correct.
- T033a depends on nothing. Correct.
- T033b depends on T033a. Correct.
- T038c depends on T015, T018. Correct.
- T048 depends on nothing. Correct.
- The duplicate ID T022 is the most severe violation. It breaks the dependency graph. T022 (US3) must be renamed. The dependency 'T030' for T022 (US3) is also wrong. T030 is the integration test. T022 is the benchmark. They are different. This is a fatal violation.
- T011a, T011b, T011c are tests for US1. They depend on T012, T016, T015. No explicit dependencies. Phase ordering handles it. Acceptable.
- The duplicate ID T022 is the most severe violation. It breaks the dependency graph. T022 (US3) must be renamed. The dependency 'T030' for T022 (US3) is also wrong. T030 is the integration test. T022 is the benchmark. They are different. This is a fatal violation.
- T015b depends on T016c. T016c is the augmentation execution. If T016c is a no-op, T016c still runs. T015b then runs. This is valid. However, T015b's logic says 'Read N_curated from data/curated/curated_metadata.jsonl (output of T016c)'. T016c updates this file. T016 also writes this file. If T016c is a no-op, T016's output is the source. If T016c runs, it updates the file. The dependency on T016c ensures the file is in its final state. This is a valid ordering.
- T017 depends on T015b and T024. T015b is in Phase 3. T024 is in Phase 4. T017 is in Phase 4. This is valid. T017 uses the control indices from T015b and the model from T024. Correct.
- T024 depends on T038b. T038b is in Phase 3. T024 is in Phase 4. This is valid. The gate must pass before training. Correct.
- T025 depends on T024b. T024b depends on T024. T025 is the training loop. T024 is the model. T024b verifies the model. T025 uses the verified model. Correct.
- T026 depends on T024b. T026 is the data loader. T024b verifies the model. The data loader is part of the training. This is acceptable.
- T027 (Checkpointing) depends on nothing. It is part of T025. Acceptable.
- T028 (Resource monitoring) depends on nothing. It is part of T025. Acceptable.
- T029 depends on T025. T029 instruments T025. Correct.
- T031, T032 depend on nothing. They are in Phase 5. They should depend on T024/T025 (Model trained). The phase ordering handles it, but explicit dependencies are missing. This is a minor violation.
- T034 depends on nothing. It is in Phase 5. It should depend on T016c (Augmentation). The phase ordering handles it. Acceptable.
- T035a, T036 depend on nothing. They are in Phase 5. They should depend on T034, T031, T032. The phase ordering handles it. Acceptable.
- T039 depends on nothing. It is in Phase 5. It should depend on T031, T032, T035a, T036. The phase ordering handles it. Acceptable.
- T030 depends on T030b. T030b depends on T038c. T030 is the integration test. T030b is the orthogonality test. T038c is the gate. This is valid.
- T030b depends on T038c. Correct.
- T033a depends on nothing. Correct.
- T033b depends on T033a. Correct.
- T038c depends on T015, T018. Correct.
- T048 depends on nothing. Correct.
- The duplicate ID T022 is the most severe violation. It breaks the dependency graph. T022 (US3) must be renamed. The dependency 'T030' for T022 (US3) is also wrong. T030 is the integration test. T022 is the benchmark. They are different. This is a fatal violation.
- T011a, T011b, T011c are tests for US1. They depend on T012, T016, T015. No explicit dependencies. Phase ordering handles it. Acceptable.
- The duplicate ID T022 is the most severe violation. It breaks the dependency graph. T022 (US3) must be renamed. The dependency 'T030' for T022 (US3) is also wrong. T030 is the integration test. T022 is the benchmark. They are different. This is a fatal violation.
