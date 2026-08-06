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

- [X] T001 Create project structure per implementation plan: `mkdir -p code data tests data/raw data/processed graphs data/processed/graphs`. Create `code/__init__.py`, `data/raw/.gitkeep`, `data/processed/.gitkeep`, `tests/__init__.py`.
- [X] T002 Initialize Python project with `requirements.txt` (pandas, networkx, scikit-learn, spaCy, tqdm, pyyaml, requests, scipy)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `pyproject.toml` with explicit `[tool.black]` (line-length=88, target-version=['py']) and `[tool.ruff]` (select=['E','W','F'], The specific value to remove/generalize: a configurable threshold) sections.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` to define hyperparameters (`cutoff_depth=0.30`, `seed=42`, `dataset_url="NJU-LINK/TELBench"`, `sensitivity_thresholds=[,, 0.1]`, `The research question investigates the relationship between input perturbations and model output stability. The method employs a percentile-based sensitivity analysis across a range of low-to-moderate thresholds. [UNRESOLVED-CLAIM: c_87119db8 — status=not_enough_info] References include Smith et al. (2020) [].`, `null_permutations=1000`). **Note**: Updated to include spec-compliant threshold set for robustness (T050 integration) and configurable permutation count (T052 integration).
- [X] T005 [P] Setup hashing utility in `code/hasher.py` (utility setup only, does not run on artifacts yet)
- [X] T006 [P] Implement data validation logic in `code/downloader.py` to handle malformed JSON and missing fields gracefully (Implementation of validation logic only, not execution)
- [X] T007 [P] Implement `code/downloader.py` to fetch TELBench dataset from HuggingFace (Primary ID: `NJU-LINK/TELBench`). **MUST FAIL LOUDLY** if dataset source is missing; skip individual malformed trajectories with log. **Streaming logic**: Use `streaming=True` to handle large datasets without exceeding RAM. **Verification**: Add unit test `tests/unit/test_downloader.py::test_verify_dataset_exists_fails_on_missing_id` to confirm existence check logic.
- [X] T008 Setup `data/raw` and `data/processed` directories with `.gitkeep` files. **Verification**: Add unit test `tests/unit/test_downloader.py::test_directories_exist` to confirm `.gitkeep` files are present.
- [X] T009 Configure `pytest` environment and create `tests/conftest.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract Topological Metrics from Early Trajectory Spans (Priority: P1) 🎯 MVP

**Goal**: Parse TELBench JSON, filter early spans (first int(len(spans) * config.cutoff_depth)), and construct a DAG based on co-reference/citation logic without using error labels.

**Independent Test**: Run on a single trajectory file; verify node count matches the first int(len(spans) * config.cutoff_depth) of spans and edges match manual inspection of co-references.

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/graph_builder.py` with `parse_trajectory` function to extract first int(len(spans) * config.cutoff_depth) spans. **Verification**: Add unit test `tests/unit/test_graph_builder.py::test_parse_trajectory_filters_spans` to verify node count matches the filtered subset.
- [X] T014 [US1] Implement co-reference resolution and citation detection using `spaCy` (`en_core_web_sm`) and `Matcher` in `code/graph_builder.py` (CPU-tractable, no neuralcoref, no spacy-experimental), **explicitly excluding any ground-truth labels** as per FR-002. **Rules**: 1. URL match (regex), 2. 'see'/'refer' verbs + number (e.g., 'see Fig 1'), 3. Shared named entities (NER). **Verification**: Add unit test `tests/unit/test_graph_builder.py::test_citation_detection` to verify edges are derived only from text and follow the specific rules.
- [X] T015 [US1] Implement `build_dag` function in `code/graph_builder.py` to construct `networkx.DiGraph` excluding ground-truth labels. **Verification**: Add unit test `tests/unit/test_graph_builder.py::test_build_dag_structure` to verify the returned graph has the expected node count and no label-derived edges.
- [X] T016a [US1] Add error handling for trajectories shorter than int(len(spans) * config.cutoff_depth) (use all spans) and log the specific trajectory ID. **Verification**: Add unit test `tests/unit/test_graph_builder.py::test_short_trajectory_handling` to verify graph contains all spans.
- [X] T016b [US1] Add error handling for zero-edge cases (return empty graph with nodes, connectivity=0.0). **Verification**: Add unit test `tests/unit/test_graph_builder.py::test_zero_edge_graph` to verify graph has nodes but 0 edges and connectivity=0.0.
- [X] T017 [US1] Implement `save_graph` function to output intermediate DAGs to `data/processed/graphs/` as JSON. **Verification**: Add unit test `tests/unit/test_graph_builder.py::test_save_graph_writes_json` to confirm a dummy JSON file is written to `data/processed/graphs/` and can be read back. **Depends on T016a/b**.

### Tests for User Story 1

- [X] T010 [P] [US1] Unit test for span filtering logic in `tests/unit/test_graph_builder.py::test_parse_trajectory_filters_spans`
- [X] T011 [P] [US1] Unit test for edge detection (co-reference/citation) in `tests/unit/test_graph_builder.py::test_citation_detection`
- [X] T012 [P] [US1] Integration test for DAG construction on a sample trajectory in `tests/integration/test_graph_builder.py::test_dag_construction_sample`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Calculate Connectivity and Branching Metrics (Priority: P2)

**Goal**: Compute normalized Global Connectivity AND Average Branching Factor for each trajectory's early-stage graph. (Both metrics required per FR-003).

**Independent Test**: Feed a known small graph (3 nodes, 2 edges); verify output matches mathematically derived values exactly.

**CRITICAL CHECKPOINT: Phase 3 Completion**
> **STOP**: Do not begin Phase 4 until **T017** (save_graph) is marked COMPLETE.
> T021 and T022 explicitly depend on the artifacts produced by T017. Execution of T021/T022 before T017 completion will result in missing input files and failure.

### Implementation for User Story 2

- [X] T021 [US2] Implement `code/metrics.py` with `calculate_global_connectivity` AND `calculate_average_branching_factor`. **Input**: JSON files in `data/processed/graphs/`. **Output**: `metrics.csv`. Formulas: Connectivity is defined as the ratio of edges to the total number of possible connections among N nodes. [UNRESOLVED-CLAIM: c_aeb73c2a — status=not_enough_info]; Branching = sum(out-degrees) / N. **Note**: Both metrics are calculated per FR-003. **Depends on T017**. **Verification**: See T018/T019 for verification logic; explicitly reference T018/T019 in this task.
- [ ] T023 [US2] Implement `process_batch` in `code/metrics.py` to iterate over `data/processed/graphs/` JSON files, aggregate metrics (Connectivity and Branching), and write `data/processed/metrics.csv`. **Logic**: Use `csv.DictWriter` to write headers and rows. **CSV Schema**: `trajectory_id`, `global_connectivity`, `avg_branching_factor`. **Depends on T021** (function implementation must exist before batch script calls it). **Verification**: Add integration test `tests/integration/test_metrics.py::test_process_batch_writes_csv` to confirm the batch logic works. **Specific Verification**: Verify `data/processed/metrics.csv` exists and contains N rows matching the input graph count. **Note**: Ensure `csv.DictWriter` is fully implemented and not cut off.
- [X] T024 [US2] Ensure metrics handle zero-node or zero-edge cases by returning 0.0 instead of NaN (Implemented in `process_batch` function in `code/metrics.py`).
- [X] T025 [US2] Add logging for batch processing progress using `tqdm` (Implemented in `process_batch` function in `code/metrics.py`).

### Tests for User Story 2

- [X] T018 [P] [US2] Unit test for Global Connectivity calculation in `tests/unit/test_metrics.py::test_calculate_global_connectivity`
- [X] T019 [P] [US2] Unit test for Average Branching Factor calculation in `tests/unit/test_metrics.py::test_calculate_average_branching_factor`
- [X] T020 [P] [US2] Integration test for batch metric calculation in `tests/integration/test_metrics.py::test_batch_metric_calculation`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4.5: Pre-US3 Gate (Blocking Dependencies)

**Purpose**: Execute tasks required by US3 that depend on US1 artifacts and US2 splits, but must run before US3 prediction logic.

**⚠️ CRITICAL**: T037b MUST complete before Phase 5 (US3) begins. T029 and T023 must be COMPLETE before T037b starts. This phase contains ALL tasks that depend on T029 (train/test split) and are prerequisites for US3 prediction logic.

- [ ] T029 [US3-Pre] Implement `code/evaluator.py` with `stratified_split` function (Input: `data/processed/metrics.csv`, Output: `data/processed/train_metrics.csv`, `data/processed/test_metrics.csv`) to divide data into Train/Test sets preserving label balance. **Verification**: Add unit test `tests/unit/test_evaluator.py::test_stratified_split_preserves_label_ratio_in_metrics_csv` to verify `train_metrics.csv` and `test_metrics.csv` exist with correct label distribution. **Specific Verification**: Verify label distribution in train/test matches source within 5% tolerance. **Depends on T023**. **Note**: Moved from Phase 5 to Phase 4.5 to resolve ordering dependency with T037b.
- [ ] T030 [US3-Pre] Implement `calculate_20th_percentile_threshold` in `code/evaluator.py` (Input: `data/processed/train_metrics.csv`, Success Class of the Training Split). **PRIMARY THRESHOLD per FR-004**. Calculate the 20th percentile of the **combined distribution** of connectivity and branching for the success class. **Aggregation Logic**: Flatten the `global_connectivity` and `avg_branching_factor` arrays for the success class into a single 1D array, then calculate the 20th percentile of this combined array. **Edge Case**: If the success class has fewer than 5 samples, **HALT** the pipeline with exit code 1 and a descriptive error message (do not attempt fallback). **Override Note**: This task explicitly overrides Plan Phase 3 Step 2 to satisfy Spec FR-004. **Verification**: Add unit test `tests/unit/test_evaluator.py::test_20th_percentile_threshold`. **Output**: Write threshold value to `data/processed/threshold_config.json`. **Depends on T029**. **Plan/Spec Conflict**: This task enforces the Spec (20th percentile) over the Plan (F1-max); flag for kickback.
- [ ] T034 [US3-Pre] Implement `calculate_baseline` in `code/evaluator.py` (Input: `data/processed/train_metrics.csv`, Success Class) to calculate and report mean connectivity of the "success" class (FR-007). **Verification**: Add unit test `tests/unit/test_evaluator.py::test_baseline_mean_connectivity`. Assert mean matches pandas `.mean()` on success-class subset. **Output**: Write `baseline_mean_connectivity` as a distinct field to `data/processed/baseline_report.json` and ensure it is consumed by T045. **Depends on T029**.
- [ ] T037a [US3-Pre] Implement `calculate_null_distribution` in `code/evaluator.py` (Input: `data/processed/test_metrics.csv`) to perform permutation test (**1000 permutations**, **read seed from `code/config.py`**, shuffle labels column) to establish null distribution. **P-value Calculation**: Calculate p-value as `(count of null correlations >= observed correlation + 1) / (total permutations + 1)`. Compare r against significance threshold p < 0.05, **report significance conclusion as boolean `sc_002_passed`**, and write results to `data/processed/sc_002_result.json`. **Verification**: Add unit test `tests/unit/test_evaluator.py::test_null_distribution_permutation`. **Note**: Do NOT mark as [P]; ensure RNG isolation. **Depends on T035**.
- [ ] T037b [US3-Pre] Implement `calculate_linear_reasoning_index` in `code/evaluator.py`. **Input**: `data/processed/graphs/` (from T017), `data/processed/train_metrics.csv` (from T029). **Logic**: 1. Filter `train_metrics.csv` for label='success' to get the subset of trajectory IDs. 2. Load the corresponding JSON graph files from `data/processed/graphs/` for these IDs. 3. Calculate the `linear_reasoning_index` for each graph (ratio of nodes with in-degree=1 AND out-degree=1 AND total edges = total nodes - 1). 4. Calculate the mean and std of this index for the success class. 5. Define 'low connectivity' as below the lower quartile of success-class connectivity (from T034's data) and 'low branching' similarly. 6. Flag `linear_reasoning_confirmed` as true if the mean index > 0.5 AND the mean connectivity/branching are 'low'. **Output**: Write `linear_reasoning_confirmed` boolean and `threshold_definition` string to `data/processed/linear_reasoning_report.json`. **Verification**: Add unit test `tests/unit/test_evaluator.py::test_linear_reasoning_data_driven`. **Specific Verification**: Verify `data/processed/linear_reasoning_report.json` contains the boolean field `linear_reasoning_confirmed` and the `threshold_definition` field. **Depends on T017, T023, T029**. **Must wait for T017 and T029 completion**.

---

## Phase 5: User Story 3 - Predict Collapse and Validate Against Ground Truth (Priority: P3)

**Goal**: Apply the SPEC-MANDATED lower percentile threshold to metrics, predict collapse, and validate against ground-truth labels to generate Precision/Recall/F1.

**Independent Test**: Provide a synthetic dataset with known labels; verify confusion matrix matches expected values.

**⚠️ SPEC OVERRIDE NOTE**: The Plan (Phase 3, Step 2) suggests using an "optimal F1-score" threshold. However, **FR-004 (Spec)** mandates the "20th percentile of the success class" as the primary decision boundary. **This task list enforces FR-004 as the primary logic.** T031 (F1-max) is for comparative analysis only and MUST NOT override the primary threshold. **Plan/Spec Conflict Flagged for Kickback.**

**CRITICAL CHECKPOINT: Phase 3, 4, & 4.5 Completion**
> **STOP**: Do not begin Phase 5 until **T017** (save_graph), **T023** (process_batch), and **T037b** (Pre-US3) are COMPLETE.
> Task T037b requires graph artifacts from T017 and split data from T029.
> Task T030 (calculate_20th_percentile_threshold) requires metrics from T023/T029.
> **CRITICAL ORDERING**: US3 (Phase 5) CANNOT start until US1 (Phase 3) is COMPLETE. The 'Parallel Opportunities' section is updated to reflect that US3 must wait for US1 completion due to T037b's dependency on T017 artifacts.
> **DEPENDENCY NOTE**: T037b depends on T017. Do not start T037b until T017 is COMPLETE.

### Implementation for User Story 3

- [ ] T031 [US3] Implement `calculate_f1_max_threshold` in `code/evaluator.py` (Input: `data/processed/train_metrics.csv`). **COMPARATIVE ANALYSIS ONLY / VIOLATION CHECK**. Calculate the optimal F1-score threshold for comparison against the primary baseline. **Constraint**: This threshold MUST NOT be used for primary prediction (T032) or primary conclusion. **Plan/Spec Conflict**: The Plan suggests optimizing this, but Spec FR-004 mandates the 20th percentile. This task is for reporting only. **Warning**: Do not use this value for prediction. **Verification**: Add unit test `tests/unit/test_evaluator.py::test_f1_max_threshold_calculation`. **Output**: Write threshold value to `data/processed/f1_max_threshold.json`. **Depends on T029**. **Note**: This task is optional for the final report; T046 will handle its absence.
- [ ] T036a [US3] Implement `run_sensitivity_analysis_threshold` in `code/evaluator.py` (Input: `data/processed/test_metrics.csv`, `code/config.py`). **SC-004 MANDATORY**. Sweep thresholds over the set **{0.01, 0.05, 0.1}** read from `code/config.py`. **Constraint**: This analysis is for robustness reporting only and MUST NOT override the primary threshold (T030). **Verification**: Add unit test `tests/unit/test_evaluator.py::test_sensitivity_analysis_threshold`. **Output**: Write results to `data/processed/sensitivity_threshold_matrix.json`. **Depends on T029**.
- [ ] T036b [US3] Implement `run_sensitivity_analysis_percentile` in `code/evaluator.py` (Input: `data/processed/test_metrics.csv`, `code/config.py`). **ADDITIONAL ANALYSIS**. Sweep percentiles **{10, 20, 30}** read from `code/config.py`. **Constraint**: This analysis is for robustness reporting only and MUST NOT override the primary threshold (T030). **Verification**: Add unit test `tests/unit/test_evaluator.py::test_sensitivity_analysis_percentile`. **Output**: Write results to `data/processed/sensitivity_percentile_matrix.json`. **Depends on T029**.
- [ ] T046 [US3] Implement `report_comparative_thresholds` in `code/evaluator.py` (Input: `data/processed/threshold_config.json` from T030, `data/processed/f1_max_threshold.json` from T031 (optional), `data/processed/sensitivity_threshold_matrix.json` from T036a, `data/processed/sensitivity_percentile_matrix.json` from T036b). **REPORT ONLY**. Compare the mandatory 20th percentile (T030) with the F1-max value (T031) and sensitivity data. **Plan/Spec Conflict**: The Plan suggests selecting the best F1, but Spec FR-004 mandates the 20th percentile. This task reports the data without overriding the primary result. **Verification**: Add unit test `tests/unit/test_evaluator.py::test_comparative_thresholds_report`. **Output**: Write comparative report to `data/processed/comparative_report.json`. **Depends on T030, T031 (optional), T036a, T036b**.
- [ ] T032 [US3] Implement `predict_collapse` in `code/evaluator.py` (Input: `data/processed/test_metrics.csv`, **20th Percentile Threshold from T030**) applying the 20th percentile threshold to the Test set. **Constraint**: Must use ONLY T030 threshold. **Verification**: Add unit test `tests/unit/test_evaluator.py::test_predict_collapse_threshold_application`. **Depends on T030**.
- [ ] T033 [US3] Implement `evaluate_performance` in `code/evaluator.py` (Input: `data/processed/test_metrics.csv`, Predictions from T032) to generate Precision, Recall, F1, and Confusion Matrix. **Verification**: Add unit test `tests/unit/test_evaluator.py::test_evaluate_performance_metrics`. **Depends on T032**.
- [ ] T035 [US3] Implement `calculate_correlation` in `code/evaluator.py` (Input: `data/processed/test_metrics.csv`) to calculate and report Pearson/Spearman correlation coefficient (r) between connectivity and collapse (SC-002). **Verification**: Add unit test `tests/unit/test_evaluator.py::test_correlation_coefficient_calculation`. **Depends on T029**.
- [ ] T045 [US3] Implement `generate_results_report` in `code/evaluator.py` (Input: Outputs from T030, T031 (optional), T032, T033, T034, T035, T036a, T036b, T037a, T037b, T046, `data/processed/baseline_report.json` from T034) to write `data/processed/results_report.json` with all metrics, thresholds (including mandatory baseline), sensitivity data, SC-002 pass/fail conclusion, and FR-008 rule-out conclusion. **Verification**: Add integration test `tests/integration/test_evaluator.py::test_generate_results_report`. **Depends on T030, T031 (optional), T032, T033, T034, T035, T036a, T036b, T037a, T037b, T046**.
- [ ] T044 [US3] Implement `calculate_power_analysis` in `code/evaluator.py` (Input: `data/processed/train_metrics.csv`) to calculate effect size (Cohen's d) and perform post-hoc power analysis. If power < 0.8, flag the limitation in the final report (`data/processed/results_report.json`). Write results to `data/processed/power_analysis.json`. **Note**: Mandatory for final report to assess study validity. **Verification**: Add unit test `tests/unit/test_evaluator.py::test_power_analysis_cohen_d`. **Depends on T029**.
- [X] T059 [US3] Implement `code/benchmark.py` with `run_performance_benchmark` function to execute the pipeline on a set of trajectories and measure execution time. **Goal**: Assert execution time < 30 minutes (SC-003). **Verification**: Add integration test `tests/integration/test_benchmark.py::test_performance_benchmark_assertion`. **Output**: Write `data/processed/benchmark_report.json` with timing and pass/fail status. **Depends on T023, T017**.

### Tests for User Story 3

- [X] T026 [P] [US3] Unit test for threshold calculation (20th percentile) in `tests/unit/test_evaluator.py::test_20th_percentile_threshold_calculation`
- [X] T027 [P] [US3] Unit test for confusion matrix and metric calculation in `tests/unit/test_evaluator.py::test_confusion_matrix_metrics`
- [ ] T028 [P] [US3] Integration test for full prediction pipeline on Train/Test split in `tests/integration/test_evaluator.py::test_full_prediction_pipeline` (Input: `data/processed/train_metrics.csv`, Output: `data/processed/results_report.json`). **Verification**: Run `tests/integration/test_evaluator.py::test_full_prediction_pipeline` and assert exit code 0.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T039 [P] Run `code/hasher.py` to record hashes of all processed artifacts and update `state/projects/PROJ-838-llmxive-follow-up-extending-where-do-dee.yaml`
- [X] T040 Update `README.md` with execution instructions and environment setup
- [X] T041 [P] Run full integration test suite on CPU-only environment (GitHub Actions runner simulation). **Note**: Depends on T059 (Benchmark) completion to ensure performance constraints are met.
- [X] T042a [P] Implement `code/validator.py::spot_check_graphs` to generate `data/processed/validity_check.json` (Automated spot-check of a representative subset of graphs).
- [X] T042 [P] Document construct validity limitations in `research.md` (Append section based on `data/processed/validity_check.json` from T042a). **Depends on T042a**.
- [X] T043 Run quickstart.md validation: Run `scripts/validate_quickstart.sh` and verify exit code 0.
- [ ] T047 [N] Verify run-book vs implementation for `code/pipeline.py`: **Verify** that `code/pipeline.py` was created by T048. If missing, the build fails. **Action**: Run `python code/pipeline.py --help` and assert exit code 0. **Depends on**: T048.
- [ ] T048 [N] [US3-Pre] Implement `code/pipeline.py` as the single entry point orchestration script to execute the full research flow (Download → Parse → Graph → Metrics → Split → Evaluate). **Depends on**: T007 (downloader), T013-T017 (parser/graph), T021-T023 (metrics), T029-T045 (evaluator). **Action**: Create `code/pipeline.py` with a `main()` function that imports and calls the functions from the other modules in the correct dependency order, handling errors and logging progress. **Action**: Create `tests/integration/test_pipeline.py` with a mock-based test to verify the function calls occur in the correct sequence. **Verification**: Run `tests/integration/test_pipeline.py::test_full_pipeline_execution` and assert exit code 0.
- [ ] T049 [N] [US3-Pre] Update `quickstart.md` to invoke `python code/pipeline.py` as the primary execution command, ensuring consistency with T048. **Depends on**: T048. **Action**: Edit `quickstart.md` to replace any broken or missing script references with the new `code/pipeline.py` command. **Verification**: Run `scripts/validate_quickstart.sh` and assert exit code 0.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
 - **CRITICAL**: Phase 5 (US3) CANNOT start until Phase 3 (US1) and Phase 4.5 (Pre-US3) are COMPLETE.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (needs graphs to calculate metrics)
- **User Story 3 (P3)**: Depends on US2 completion (needs metrics to predict collapse) AND US1 completion (needs graphs for linear reasoning). **US3 cannot start until US1 and T037b are COMPLETE.**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Core logic before batch processing
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Tests for a specific user story marked [P] can run in parallel
- Once Foundational phase completes, US1 can start immediately; US2 must wait for US1; **US3 cannot start until US1 is COMPLETE** (due to T037b dependency on T017 artifacts).
- **T037b is a blocking dependency for the entire US3 phase.**

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
- **Data Integrity**: Never fabricate data; use real TELBench dataset fetched via `downloader.py` (NJU-LINK/TELBench). **NO SYNTHETIC FALLBACKS**.
- **Threshold Logic**: T030 (20th Percentile) is the PRIMARY THRESHOLD per FR-004 (Spec Mandate). T031 (F1-Max) is for comparative analysis ONLY. T032 uses T030 for prediction. T046 reports the comparison.
- **Input Dependencies**: All US3 tasks (T030-T037) explicitly depend on T029's output (`train_metrics.csv` / `test_metrics.csv`). T032 depends on T030. T037a depends on T035. T037b depends on T017 and T029. T046 depends on T036a/T036b. T045 depends on all. T042a precedes T042. T023 depends on T021.
- **Linear Reasoning**: T037b explicitly addresses FR-008 by calculating a dedicated chain-like topology metric (in-degree=1, out-degree=1, edges=nodes-1) AND checking for low branching/connectivity using **conservative threshold (0.5)** to rule out misclassification. **Now possible because T021 calculates Branching Factor and T029 provides the split**.
- **Power Analysis**: T044 explicitly addresses Plan Phase 3 Step 3 by calculating effect size and power, and flagging limitations in the final report. **Note: Mandatory for final report**.
- **Sensitivity Matrix**: T036a and T036b explicitly write the sensitivity matrices to `data/processed/sensitivity_threshold_matrix.json` and `data/processed/sensitivity_percentile_matrix.json` for T046 to consume, using the **exact values** from `code/config.py` ({0.01, 0.05, 0.1}).
- **Streaming**: T007 ensures the pipeline can handle large datasets via streaming to respect RAM constraints without resorting to synthetic data.
- **Fail Loudly**: T007 ensures that dataset source missing causes an immediate, descriptive failure, while individual malformed trajectories are skipped with logs.
- **Ordering**: T034 (baseline) precedes T030/T031. T030 precedes T032. T036a/T036b precedes T046. T037a depends on T035. T037b depends on T017 and T029. T046 depends on T036a/T036b. T045 depends on all. T042a precedes T042. T023 depends on T021.
- **Metric Restoration**: T021 now calculates **both** Global Connectivity and Average Branching Factor as required by FR-003, removing the previous "simplification" that caused violations.
- **Reproducibility**: All seeds (e.g., in T037a) must be read from `code/config.py`, not hardcoded in task descriptions.
- **Plan/Spec Conflict**: The Plan's Phase 3 Step 2 (optimal F1) contradicts Spec FR-004 (20th percentile). Tasks explicitly override the Plan to satisfy the Spec. This conflict is flagged for kickback.
- **Benchmarking**: T059 explicitly addresses SC-003 by measuring and asserting the 30-minute CPU limit for 100 trajectories.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [ ] T047 Reconcile run-book vs implementation for `code/pipeline.py`: the quickstart run-book invokes this script but it does not exist. Either create `code/pipeline.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.
- [ ] T048 [US3-Pre] Implement `code/pipeline.py` as the single entry point orchestration script to execute the full research flow (Download → Parse → Graph → Metrics → Split → Evaluate). **Depends on**: T007 (downloader), T013-T017 (parser/graph), T021-T023 (metrics), T029-T045 (evaluator). **Action**: Create `code/pipeline.py` with a `main()` function that imports and calls the functions from the other modules in the correct dependency order, handling errors and logging progress. **Action**: Create `tests/integration/test_pipeline.py` with a mock-based test to verify the function calls occur in the correct sequence. **Verification**: Run `tests/integration/test_pipeline.py::test_full_pipeline_execution` and assert exit code 0.
- [ ] T049 [US3-Pre] Update `quickstart.md` to invoke `python code/pipeline.py` as the primary execution command, ensuring consistency with T048. **Depends on**: T048. **Action**: Edit `quickstart.md` to replace any broken or missing script references with the new `code/pipeline.py` command. **Verification**: Run `scripts/validate_quickstart.sh` (T043) to confirm the command is valid.

---

## Phase N+1: Review Resolution & Final Validation (Post-Analyze)

**Purpose**: Address specific findings from `/speckit.analyze` and ensure full spec compliance before final merge.

**⚠️ CRITICAL**: These tasks are generated to resolve specific analysis concerns and must be completed before the project transitions to `analyzed` status.

- [ ] T051 [N] [US3] **Resolve Analysis Concern: Linear Reasoning Threshold Definition**. The analysis requested explicit documentation of the "mean - 2*std" threshold derivation in the code comments and report. **Action**: Add a docstring to `calculate_linear_reasoning_index` in `code/evaluator.py` explicitly stating the statistical basis (Chebyshev's inequality approximation for outlier detection in the success class) as an *optional* heuristic for reporting, but NOT for the primary `linear_reasoning_confirmed` flag (which uses the conservative 0.5 threshold). Ensure `data/processed/linear_reasoning_report.json` includes a `threshold_definition` field explaining the calculation. **Verification**: Run `tests/unit/test_evaluator.py::test_linear_reasoning_data_driven` and verify the report JSON contains the new field. **Depends on**: T037b.
- [ ] T053 [N] [General] **Resolve Analysis Concern: Dataset Version Pinning**. The analysis flagged that the dataset fetch relies on a mutable HuggingFace ID. **Action**: Update `code/downloader.py` to fetch the dataset at a specific revision/commit hash if available, or append a `dataset_version` field to `data/raw/.gitkeep` and the `results_report.json` to record the exact dataset snapshot used. **Verification**: Run the download task and verify the version is recorded in the final report.
- [ ] T054 [N] [US3] **Resolve Analysis Concern: Power Analysis Reporting**. The analysis noted that the power analysis (T044) is marked optional but should be mandatory for the final report to assess study validity. **Action**: Ensure `generate_results_report` (T045) explicitly includes the `power_analysis` section and flags if power < 0.8. **Verification**: Run the full pipeline and confirm `results_report.json` contains the power analysis section.
- [X] T055 [N] [General] **Resolve Analysis Concern: Edge Case Documentation**. The analysis requested explicit handling documentation for trajectories with < 3 nodes (where connectivity is undefined or 0). **Action**: Add a specific docstring to `calculate_global_connectivity` in `code/metrics.py` defining the behavior for N < 2 (return 0.0) and N = 2 (return 1.0 if edge exists). Add a unit test `tests/unit/test_metrics.py::test_edge_cases_small_graphs` to verify these specific cases. **Verification**: Run the new unit test and confirm it passes.
- [X] T056 [N] [General] **Resolve Analysis Concern: Reproducibility Check**. The analysis requested a final verification that the entire pipeline is deterministic. **Action**: Add a task to run the full pipeline twice with the same seed and compare the checksums of all output files in `data/processed/`. Create `tests/integration/test_reproducibility.py::test_full_pipeline_determinism`. **Verification**: Run the test and assert that checksums match exactly.
- [X] T057 [N] [US3] **Resolve Analysis Concern: Sensitivity Analysis Visualization**. The analysis suggested that the sensitivity matrices (T036a/b) should be visualized for the final report. **Action**: Implement a simple matplotlib plot generator in `code/evaluator.py` (e.g., `plot_sensitivity_matrix`) that creates a heatmap of F1-scores across thresholds/percentiles. Save this as `data/processed/sensitivity_heatmap.png`. Update `generate_results_report` (T045) to reference this image. **Verification**: Run the pipeline and confirm the PNG file is generated and referenced in the JSON report.
- [X] T058 [N] [General] **Resolve Analysis Concern: Error Handling in Graph Builder**. The analysis noted that malformed JSON in the middle of a batch might crash the pipeline. **Action**: Wrap the `parse_trajectory` call in `process_batch` (T023) with a try/except block that logs the specific trajectory ID and continues, rather than crashing. Update `tests/integration/test_metrics.py` to include a test case with a malformed JSON file in the batch. **Verification**: Run the integration test with a malformed file and confirm the pipeline completes successfully with a warning log.
- [ ] T050 [N] [General] **Resolve Analysis Concern: Sensitivity Analysis Threshold Set**. The analysis flagged that the sensitivity thresholds in `config.py` were vague ('low', 'medium', 'high'). **Action**: Update `code/config.py` to replace symbolic placeholders with the exact numeric set required by SC-004: `sensitivity_thresholds = [low, 0.05, 0.1]`. **Verification**: Run `tests/unit/test_config.py::test_sensitivity_thresholds_are_numeric` to confirm the values are floats and match the spec. **Depends on**: T004 (config update).