# Tasks: llmXive follow-up: extending "Where Do Deep-Research Agents Go Wrong? Span-Level Error Localization "

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan: `mkdir -p code data tests data/raw data/processed graphs data/processed/graphs`. Create `code/__init__.py`, `data/raw/.gitkeep`, `data/processed/.gitkeep`, `tests/__init__.py`.
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, networkx, scikit-learn, spaCy, tqdm, pyyaml, requests, scipy)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `pyproject.toml` with explicit `[tool.black]` (line-length=88, target-version=['py311']) and `[tool.ruff]` (select=['E','W','F'], ignore=['E501']) sections.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` to define hyperparameters (`cutoff_depth`, `seed`, `dataset_url`, `sensitivity_thresholds=[low, 0.05, 0.1]`, `sensitivity_percentiles=[, 20, 30]`)
- [X] T005 [P] Setup hashing utility in `code/hasher.py` (utility setup only, does not run on artifacts yet)
- [X] T006 [P] Implement data validation logic in `code/downloader.py` to handle malformed JSON and missing fields gracefully (Implementation of validation logic only, not execution)
- [X] T007 [P] Implement `code/downloader.py` to fetch TELBench dataset from HuggingFace (Primary ID: `HuggingFaceH4/tebench`, Fallback: `HuggingFaceH4/tebench-v1`) using `datasets.load_dataset(..., streaming=True)`. **MUST FAIL LOUDLY** if dataset source is missing; skip individual malformed trajectories with log. **Include verification**: Add unit test `tests/unit/test_downloader.py::test_verify_dataset_exists_fails_on_missing_id` to confirm existence check logic. **Depends on T007a logic merged here**.
- [ ] T008 Setup `data/raw` and `data/processed` directories with `.gitkeep`
- [X] T009 Configure `pytest` environment and create `tests/conftest.py`
- [X] T047 [P] Implement `stream_dataset` utility in `code/downloader.py` using `datasets.load_dataset(..., streaming=True)` to handle large TELBench splits without exceeding RAM, ensuring the full dataset contributes to statistics if possible. **Integrated into T007**.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract Topological Metrics from Early Trajectory Spans (Priority: P1) 🎯 MVP

**Goal**: Parse TELBench JSON, filter early spans (first int(len(spans) * config.cutoff_depth)), and construct a DAG based on co-reference/citation logic without using error labels.

**Independent Test**: Run on a single trajectory file; verify node count matches the first int(len(spans) * config.cutoff_depth) of spans and edges match manual inspection of co-references.

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/graph_builder.py` with `parse_trajectory` function to extract first int(len(spans) * config.cutoff_depth) spans
- [X] T014 [US1] Implement co-reference resolution and citation detection using `spaCy` (`en_core_web_sm`) and `Matcher` in `code/graph_builder.py` (CPU-tractable, no neuralcoref, no spacy-experimental)
- [X] T015 [US1] Implement `build_dag` function in `code/graph_builder.py` to construct `networkx.DiGraph` excluding ground-truth labels
- [ ] T016a [US1] Add error handling for trajectories shorter than int(len(spans) * config.cutoff_depth) (use all spans) and log the specific trajectory ID. **Verification**: Add unit test `tests/unit/test_graph_builder.py::test_short_trajectory_handling` to verify graph contains all spans.
- [ ] T016b [US1] Add error handling for zero-edge cases (return empty graph with nodes, connectivity=0.0). **Verification**: Add unit test `tests/unit/test_graph_builder.py::test_zero_edge_graph` to verify graph has nodes but 0 edges and connectivity=0.0.
- [ ] T017 [US1] Implement `save_graph` function to output intermediate DAGs to `data/processed/graphs/` as JSON

### Tests for User Story 1

- [X] T010 [P] [US1] Unit test for span filtering logic in `tests/unit/test_graph_builder.py`
- [X] T011 [P] [US1] Unit test for edge detection (co-reference/citation) in `tests/unit/test_graph_builder.py`
- [X] T012 [P] [US1] Integration test for DAG construction on a sample trajectory in `tests/integration/test_graph_builder.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Calculate Connectivity and Branching Metrics (Priority: P2)

**Goal**: Compute normalized Global Connectivity AND Average Branching Factor for each trajectory's early-stage graph. (Both metrics required per FR-003).

**Independent Test**: Feed a known small graph (3 nodes, 2 edges); verify output matches mathematically derived values exactly.

**CRITICAL CHECKPOINT: Phase 3 Completion**
> **STOP**: Do not begin Phase 4 until **T017** (save_graph) is marked COMPLETE.
> T021 and T022 explicitly depend on the artifacts produced by T017. Execution of T021/T022 before T017 completion will result in missing input files and failure.

### Implementation for User Story 2

- [X] T021 [US2] Implement `code/metrics.py` with `calculate_global_connectivity` AND `calculate_average_branching_factor`. Input: `data/processed/graphs/`. Output: `metrics.csv`. Formulas: Connectivity is defined as the ratio of edges to the total number of possible connections among N nodes.; Branching = sum(out-degrees) / N. **Note**: Both metrics are calculated per FR-003. **Depends on T017**.
- [ ] T023 [US2] Implement `process_batch` in `code/metrics.py` to iterate over `data/processed/graphs/` JSON files, aggregate metrics (Connectivity and Branching), and write `data/processed/metrics.csv`. **Depends on T021** (function implementation must exist before batch script calls it).
- [X] T024 [US2] Ensure metrics handle zero-node or zero-edge cases by returning 0.0 instead of NaN (Implemented in `process_batch` function in `code/metrics.py`).
- [X] T025 [US2] Add logging for batch processing progress using `tqdm` (Implemented in `process_batch` function in `code/metrics.py`).

### Tests for User Story 2

- [X] T018 [P] [US2] Unit test for Global Connectivity calculation in `tests/unit/test_metrics.py`
- [X] T019 [P] [US2] Unit test for Average Branching Factor calculation in `tests/unit/test_metrics.py`
- [X] T020 [P] [US2] Integration test for batch metric calculation in `tests/integration/test_metrics.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predict Collapse and Validate Against Ground Truth (Priority: P3)

**Goal**: Apply the SPEC-MANDATED lower percentile threshold to metrics, predict collapse, and validate against ground-truth labels to generate Precision/Recall/F1.

**Independent Test**: Provide a synthetic dataset with known labels; verify confusion matrix matches expected values.

**⚠️ SPEC OVERRIDE NOTE**: The Plan (Phase 3, Step 2) suggests using an "optimal F1-score" threshold. However, **FR-004 (Spec)** mandates the "20th percentile of the success class" as the primary decision boundary. **This task list enforces FR-004 as the primary logic.** T031 (F1-max) is for comparative analysis only and MUST NOT override the primary threshold.

**CRITICAL CHECKPOINT: Phase 3 & 4 Completion**
> **STOP**: Do not begin Phase 5 until **T017** (save_graph) and **T023** (process_batch) are COMPLETE.
> Task T038 (calculate_linear_reasoning_index) requires graph artifacts from T017.
> Task T030 (calculate_20th_percentile_threshold) requires metrics from T023/T029.
> **CRITICAL ORDERING**: US3 (Phase 5) CANNOT start until US1 (Phase 3) is COMPLETE. The 'Parallel Opportunities' section below is updated to reflect that US3 must wait for US1 completion due to T038's dependency on T017 artifacts.
> **DEPENDENCY NOTE**: T038 depends on T017. Do not start T038 until T017 is COMPLETE.

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/evaluator.py` with `stratified_split` function (Input: `data/processed/metrics.csv`, Output: `data/processed/train_metrics.csv`, `data/processed/test_metrics.csv`) to divide data into Train/Test sets preserving label balance. **Verification**: Add unit test `tests/unit/test_evaluator.py::test_stratified_split_preserves_label_ratio`. **Depends on T023**.
- [ ] T034 [US3] Implement `calculate_baseline` in `code/evaluator.py` (Input: `data/processed/train_metrics.csv`, Success Class) to calculate and report mean connectivity of the "success" class (FR-007). **Verification**: Add unit test `tests/unit/test_evaluator.py::test_baseline_mean_connectivity`. Assert mean matches pandas `.mean()` on success-class subset. **Output**: Write `baseline_mean_connectivity` as a distinct field to `data/processed/baseline_report.json`. **Depends on T029**.
- [ ] T030 [US3] Implement `calculate_20th_percentile_threshold` in `code/evaluator.py` (Input: `data/processed/train_metrics.csv`, Success Class). **PRIMARY THRESHOLD per FR-004**. Calculate the 20th percentile of the **joint distribution** of connectivity and branching (or the specific metric defined in FR-004) for the success class subset of the training split. **Do NOT optimize**; calculate the deterministic percentile. **Verification**: Add unit test `tests/unit/test_evaluator.py::test_20th_percentile_threshold`. **Output**: Write threshold value to `data/processed/threshold_config.json`. **Depends on T029**.
- [ ] T031 [US3] Implement `calculate_f1_max_threshold` in `code/evaluator.py` (Input: `data/processed/train_metrics.csv`). **COMPARATIVE ANALYSIS ONLY**. Calculate the optimal F1-score threshold for comparison against the primary baseline. **Verification**: Add unit test `tests/unit/test_evaluator.py::test_f1_max_threshold_calculation`. **Output**: Write threshold value to `data/processed/f1_max_threshold.json`. **Depends on T029**.
- [ ] T036 [US3] Implement `run_sensitivity_analysis` in `code/evaluator.py` (Input: `data/processed/test_metrics.csv`) to sweep thresholds over a specific set of small values and percentiles {10, 20, 30} as mandated by SC-004. Report the full matrix and write results to `data/processed/sensitivity_matrix.json`. **Verification**: Add unit test `tests/unit/test_evaluator.py::test_sensitivity_analysis_matrix`. **Depends on T029**.
- [ ] T046 [US3] Implement `report_comparative_thresholds` in `code/evaluator.py` (Input: `data/processed/threshold_config.json` from T030, `data/processed/f1_max_threshold.json` from T031, `data/processed/sensitivity_matrix.json` from T036). **REPORT ONLY**. Compare the mandatory 20th percentile (T030) with the F1-max value (T031) and sensitivity data. **Verification**: Add unit test `tests/unit/test_evaluator.py::test_comparative_thresholds_report`. **Output**: Write comparative report to `data/processed/comparative_report.json`. **Depends on T030, T031, T036**.
- [ ] T032 [US3] Implement `predict_collapse` in `code/evaluator.py` (Input: `data/processed/test_metrics.csv`, **20th Percentile Threshold from T030**) applying the 20th percentile threshold to the Test set. **Verification**: Add unit test `tests/unit/test_evaluator.py::test_predict_collapse_threshold_application`. **Depends on T030**.
- [ ] T033 [US3] Implement `evaluate_performance` in `code/evaluator.py` (Input: `data/processed/test_metrics.csv`, Predictions from T032) to generate Precision, Recall, F1, and Confusion Matrix. **Verification**: Add unit test `tests/unit/test_evaluator.py::test_evaluate_performance_metrics`. **Depends on T032**.
- [ ] T035 [US3] Implement `calculate_correlation` in `code/evaluator.py` (Input: `data/processed/test_metrics.csv`) to calculate and report Pearson/Spearman correlation coefficient (r) between connectivity and collapse (SC-002). **Verification**: Add unit test `tests/unit/test_evaluator.py::test_correlation_coefficient_calculation`. **Depends on T029**.
- [ ] T037a [US3] Implement `calculate_null_distribution` in `code/evaluator.py` (Input: `data/processed/test_metrics.csv`) to perform permutation test (a sufficient number of permutations), **read seed from `code/config.py`**, shuffle labels column) to establish null distribution, calculate correlation coefficient (r) and p-value, compare r against significance threshold p < 0.05, report significance conclusion as boolean `sc_002_passed`, and write results to `data/processed/sc_002_result.json`. **Verification**: Add unit test `tests/unit/test_evaluator.py::test_null_distribution_permutation`. **Note**: Do NOT mark as [P]; ensure RNG isolation. **Depends on T035**.
- [ ] T038 [US3] Implement `calculate_linear_reasoning_index` in `code/evaluator.py` (Input: `data/processed/test_metrics.csv`, Graphs from T017) to calculate a chain-like topology metric (ratio of nodes with in-degree=1 AND out-degree=1 AND total edges = total nodes - 1) AND check for low branching (avg out-degree < 1.5, using `avg_branching_factor` column) and low connectivity (global connectivity < 0.1) for the success class to rule out misclassification (FR-008). **Verification**: Add unit test `tests/unit/test_evaluator.py::test_linear_reasoning_index_calculation`. **Output**: Write `linear_reasoning_confirmed` boolean to `data/processed/linear_reasoning_report.json`. **Depends on T017, T023**.
- [ ] T037b [US3] Implement `generate_results_report` in `code/evaluator.py` (Input: Outputs from T030, T031, T032, T033, T034, T035, T036, T037a, T038, T046) to write `data/processed/results_report.json` with all metrics, thresholds (including mandatory baseline), sensitivity data, SC-002 pass/fail conclusion, and FR-008 rule-out conclusion. **Verification**: Add integration test `tests/integration/test_evaluator.py::test_generate_results_report`. **Depends on T030, T031, T032, T033, T034, T035, T036, T037a, T038, T046**.
- [ ] T045 [US3] Implement `calculate_power_analysis` in `code/evaluator.py` (Input: `data/processed/train_metrics.csv`) to calculate effect size (Cohen's d) and perform post-hoc power analysis. If power < 0.8, flag the limitation in the final report (`data/processed/results_report.json`). Write results to `data/processed/power_analysis.json`. **Verification**: Add unit test `tests/unit/test_evaluator.py::test_power_analysis_cohen_d`. **Depends on T029**.

### Tests for User Story 3

- [ ] T026 [P] [US3] Unit test for threshold calculation (20th percentile) in `tests/unit/test_evaluator.py::test_20th_percentile_threshold_calculation`
- [ ] T027 [P] [US3] Unit test for confusion matrix and metric calculation in `tests/unit/test_evaluator.py::test_confusion_matrix_metrics`
- [ ] T028 [P] [US3] Integration test for full prediction pipeline on Train/Test split in `tests/integration/test_evaluator.py::test_full_prediction_pipeline` (Input: `data/processed/train_metrics.csv`, Output: `data/processed/results_report.json`)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Run `code/hasher.py` to record hashes of all processed artifacts and update `state/projects/PROJ-838-llmxive-follow-up-extending-where-do-dee.yaml`
- [ ] T040 Update `README.md` with execution instructions and environment setup
- [ ] T041 [P] Run full integration test suite on CPU-only environment (GitHub Actions runner simulation)
- [ ] T042a [P] Implement `code/validator.py::spot_check_graphs` to generate `data/processed/validity_check.json` (Automated spot-check of a representative subset of graphs).
- [ ] T042 [P] Document construct validity limitations in `research.md` (Append section based on `data/processed/validity_check.json` from T042a). **Depends on T042a**.
- [ ] T043 Run quickstart.md validation: Run `scripts/validate_quickstart.sh` and verify exit code 0.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
 - **CRITICAL**: Phase 5 (US3) CANNOT start until Phase 3 (US1) is COMPLETE due to T038 dependency on T017 artifacts.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (needs graphs to calculate metrics)
- **User Story 3 (P3)**: Depends on US2 completion (needs metrics to predict collapse) AND US1 completion (needs graphs for linear reasoning). **US3 cannot start until US1 is COMPLETE.**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Core logic before batch processing
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Tests for a specific user story marked [P] can run in parallel
- Once Foundational phase completes, US1 can start immediately; US2 must wait for US1; **US3 cannot start until US1 is COMPLETE** (due to T038 dependency on T017 artifacts).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test US1 independently (graph construction accuracy)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Graph Construction)
 - Developer B: User Story 2 (Metric Calculation) - *Wait for US1 data*
 - Developer C: User Story 3 (Evaluation) - *Wait for US1 AND US2 data*
3. Stories complete and integrate sequentially due to data flow dependencies

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All graph algorithms and NLP must run on CPU only (no CUDA/GPU); use `spaCy` in CPU mode (`en_core_web_sm`).
- **Data Integrity**: Never fabricate data; use real TELBench dataset fetched via `downloader.py` (HuggingFaceH4/tebench). **NO SYNTHETIC FALLBACKS**.
- **Threshold Logic**: T030 (20th Percentile) is the PRIMARY THRESHOLD per FR-004 (Spec Mandate). T031 (F1-Max) is for comparative analysis ONLY. T032 uses T030 for prediction. T046 reports the comparison.
- **Input Dependencies**: All US3 tasks (T030-T038) explicitly depend on T029's output (`train_metrics.csv` / `test_metrics.csv`). T032 depends on T030. T037b depends on T038 and T046.
- **Linear Reasoning**: T038 explicitly addresses FR-008 by calculating a dedicated chain-like topology metric (in-degree=1, out-degree=1, edges=nodes-1) AND checking for low branching/connectivity to rule out misclassification. **Now possible because T021 calculates Branching Factor.**
- **Power Analysis**: T045 explicitly addresses Plan Phase 3 Step 3 by calculating effect size and power, and flagging limitations in the final report.
- **Sensitivity Matrix**: T036 explicitly writes the sensitivity matrix to `data/processed/sensitivity_matrix.json` for T046 to consume, using the **exact values** {0.01, 0.05, 0.1} and {10, 20, 30}.
- **Streaming**: T047 ensures the pipeline can handle large datasets via streaming to respect RAM constraints without resorting to synthetic data. Integrated into T007.
- **Fail Loudly**: T007 ensures that dataset source missing causes an immediate, descriptive failure, while individual malformed trajectories are skipped with logs.
- **Ordering**: T034 (baseline) precedes T030/T031. T030 precedes T032. T036 precedes T046. T038 precedes T037b. T042a precedes T042. T023 depends on T021.
- **Metric Restoration**: T021 now calculates **both** Global Connectivity and Average Branching Factor as required by FR-003, removing the previous "simplification" that caused violations.
- **Reproducibility**: All seeds (e.g., in T037a) must be read from `code/config.py`, not hardcoded in task descriptions.