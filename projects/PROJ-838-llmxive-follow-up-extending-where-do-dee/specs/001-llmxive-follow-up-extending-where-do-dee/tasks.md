# Tasks: llmXive follow-up: extending "Where Do Deep-Research Agents Go Wrong? Span-Level Error Localization"

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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, networkx, scikit-learn, spaCy, tqdm, pyyaml, requests, scipy)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` to define hyperparameters (`cutoff_depth`, `seed`, `dataset_url`)
- [X] T005 [P] Setup hashing utility in `code/hasher.py` (utility setup only, does not run on artifacts yet)
- [X] T006 [P] Implement data validation logic in `code/downloader.py` to handle malformed JSON and missing fields gracefully
- [ ] T007 [P] Implement `code/downloader.py` to fetch TELBench dataset from HuggingFace (ID: `NJU-LINK/TELBench`, file path: `train.json` at root). **Action**: First verify file existence via `datasets` library or `list_files` before download; handle path `train.json` (not `data/train.json`). Use checksum verification.
- [ ] T008 Setup `data/raw` and `data/processed` directories with `.gitkeep`
- [X] T009 Configure `pytest` environment and create `tests/conftest.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract Topological Metrics from Early Trajectory Spans (Priority: P1) 🎯 MVP

**Goal**: Parse TELBench JSON, filter early spans (first int(len(spans) * config.cutoff_depth)), and construct a DAG based on co-reference/citation logic without using error labels.

**Independent Test**: Run on a single trajectory file; verify node count matches the first int(len(spans) * config.cutoff_depth) of spans and edges match manual inspection of co-references.

### Implementation for User Story 1

- [X] T013 [US1] Implement `code/graph_builder.py` with `parse_trajectory` function to extract first int(len(spans) * config.cutoff_depth) spans. **Import**: `import code.config` to access `cutoff_depth`.
- [X] T014 [US1] Implement co-reference resolution and citation detection using `spaCy` (`en_core_web_sm`) and `Matcher` in `code/graph_builder.py` (CPU-tractable, no neuralcoref, no spacy-experimental). **Input**: `span_text` field from trajectory. **Output**: `list of (source_node_id, target_node_id)`. **Constraint**: STRIP success/failure label from input trajectory before processing.
- [X] T015 [US1] Implement `build_dag` function in `code/graph_builder.py` to construct `networkx.DiGraph` excluding ground-truth labels. **Constraint**: STRIP success/failure label from input trajectory before processing.
- [ ] T016 [US1] Add error handling for trajectories shorter than int(len(spans) * config.cutoff_depth) (use all spans) and zero-edge cases (return empty graph)
- [ ] T017 [US1] Implement `save_graph` function to output intermediate DAGs to `data/processed/graphs/` as JSON with naming convention `{trajectory_id}.json`. **Dependency**: Must be completed before T038.

### Tests for User Story 1

- [X] T010 [P] [US1] Unit test for span filtering logic in `tests/unit/test_graph_builder.py`
- [X] T011 [P] [US1] Unit test for edge detection (co-reference/citation) in `tests/unit/test_graph_builder.py`
- [X] T012 [P] [US1] Integration test for DAG construction on a sample trajectory in `tests/integration/test_graph_builder.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Calculate Connectivity and Branching Metrics (Priority: P2)

**Goal**: Compute normalized Global Connectivity and Average Branching Factor for each trajectory's early-stage graph.

**Independent Test**: Feed a known small graph (3 nodes, 2 edges); verify output matches mathematically derived values exactly.

**CRITICAL CHECKPOINT: Phase 3 Completion**
> **STOP**: Do not begin Phase 4 until **T017** (save_graph) is marked COMPLETE.
> T021 and T022 explicitly depend on the artifacts produced by T017. Execution of T021/T022 before T017 completion will result in missing input files and failure.

### Implementation for User Story 2

- [X] T021 [US2] Implement `code/metrics.py` with `calculate_global_connectivity` (Input: `data/processed/graphs/`, Output: `metrics.csv`). Formula: edges / (N * (N)), normalized by node count. **Depends on T017 completion**.
- [X] T022 [US2] Implement `code/metrics.py` with `calculate_avg_branching_factor` (Input: `data/processed/graphs/`, Output: `metrics.csv`). Formula: sum of out-degrees / node count. **Depends on T017 completion**.
- [X] T023 [US2] Implement `process_batch` in `code/metrics.py` to iterate over `data/processed/graphs/` JSON files, aggregate metrics (including BOTH `global_connectivity` AND `avg_branching_factor`), and write `data/processed/metrics.csv`. **Depends on T017**.
- [ ] T024 [US2] Ensure metrics handle zero-node or zero-edge cases by returning 0.0 instead of NaN
- [ ] T025 [US2] Add logging for batch processing progress using `tqdm`

### Tests for User Story 2

- [X] T018 [P] [US2] Unit test for Global Connectivity calculation in `tests/unit/test_metrics.py`
- [X] T019 [P] [US2] Unit test for Average Branching Factor calculation in `tests/unit/test_metrics.py`
- [X] T020 [P] [US2] Integration test for batch metric calculation in `tests/integration/test_metrics.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predict Collapse and Validate Against Ground Truth (Priority: P3)

**Goal**: Apply a data-driven threshold to metrics, predict collapse, and validate against ground-truth labels to generate Precision/Recall/F1.

**Independent Test**: Provide a synthetic dataset with known labels; verify confusion matrix matches expected values.

**⚠️ SPEC OVERRIDE NOTE**: The Plan (Phase 3, Step 2) suggests using an "optimal F1-score" threshold. However, **FR-004 (Spec)** mandates the "20th percentile of the success class" as the primary decision boundary. **This task list enforces FR-004 as the primary logic.** T031 (F1-max) is for comparative analysis only and MUST NOT override the primary threshold.

**CRITICAL CHECKPOINT: Phase 3 & 4 Completion**
> **STOP**: Do not begin Phase 5 until **T017** (save_graph) and **T023** (process_batch) are COMPLETE.
> Task T038 (calculate_linear_reasoning_index) requires graph artifacts from T017.
> Task T030 (calculate_20th_percentile_threshold) requires metrics from T023/T029.
> **CRITICAL ORDERING**: US3 (Phase 5) CANNOT start until US1 (Phase 3) is COMPLETE. The 'Parallel Opportunities' section below is updated to reflect that US3 must wait for US1 completion due to T038's dependency on T017 artifacts.
> **DEPENDENCY NOTE**: T038 depends on T017. Do not start T038 until T017 is COMPLETE.

### Implementation for User Story 3

- [X] T029 [US3] Implement `code/evaluator.py` with `stratified_split` function (Input: `data/processed/metrics.csv`, Output: `data/processed/train_metrics.csv`, `data/processed/test_metrics.csv`) to divide data into Train/Test sets preserving label balance. **Depends on T023**.
- [ ] T030 [US3] Implement `calculate_20th_percentile_threshold` in `code/evaluator.py` (Input: `data/processed/train_metrics.csv`, Success Class). **PRIMARY THRESHOLD per FR-004**. Search space: sweep all unique metric values in the success class subset of the training split. Output: `data/processed/threshold_config.json` containing the threshold value. **Depends on T029**.
- [ ] T031 [US3] Implement `calculate_f1_max_threshold` in `code/evaluator.py` (Input: `data/processed/train_metrics.csv`). **COMPARATIVE ANALYSIS ONLY**. Calculate the optimal F1-score threshold for comparison against the primary baseline. **Constraint**: This value is for reporting only and MUST NOT influence the threshold selection logic. **MUST NOT** be used for prediction logic. **Depends on T029**.
- [ ] T032a [US3] **ENFORCEMENT TASK**: Implement `enforce_primary_threshold` in `code/evaluator.py` to explicitly select the threshold from T030 (20th percentile) as the mandatory input for T032. **Logic**: Select `threshold = T030.value`; IGNORE `T031.value` for prediction logic. Output: `threshold_used` value for T032. **Depends on T030**.
- [ ] T032 [US3] Implement `predict_collapse` in `code/evaluator.py` (Input: `data/processed/test_metrics.csv`, Threshold from T032a) applying the PRIMARY threshold (T030) to the Test set. **Depends on T032a**.
- [ ] T033 [US3] Implement `evaluate_performance` in `code/evaluator.py` (Input: `data/processed/test_metrics.csv`, Predictions from T032) to generate Precision, Recall, F1, and Confusion Matrix
- [ ] T034 [US3] Implement `calculate_baseline` in `code/evaluator.py` (Input: `data/processed/train_metrics.csv`, Success Class) to calculate and report mean connectivity of the "success" class (FR-007). Verify output matches mean of success subset.
- [ ] T035 [US3] Implement `calculate_correlation` in `code/evaluator.py` (Input: `data/processed/test_metrics.csv`) to calculate and report Pearson/Spearman correlation coefficient (r) between connectivity and collapse (SC-002).
- [ ] T036 [US3] Implement `run_sensitivity_analysis` in `code/evaluator.py` (Input: `data/processed/train_metrics.csv`). **Sweep**: Thresholds over the SPECIFIED set of absolute values {0.01, 0.05, 0.1} AND percentiles {10, 20, 30}. **Output**: Explicitly report the stability of F1-score across the SPECIFIED set as the primary verification artifact for SC-004. **Constraint**: Use training data to prevent leakage. **Explicitly calculate stability metric on `train_metrics.csv`**. **Depends on T029**.
- [ ] T037a [US3] Implement `calculate_null_distribution` in `code/evaluator.py` (Input: `data/processed/train_metrics.csv`). **Method**: Permutation test (1000 permutations minimum, seed=42, **shuffle labels in a copy** to preserve original dataset) to establish null distribution, compare observed correlation against null to generate p-value. **Explicit Step**: Compare the calculated p-value against the 0.05 threshold and output a binary pass/fail result to `data/processed/correlation_test_result.json`. **Constraint**: Use training data to prevent leakage. **Depends on T029**.
- [ ] T038 [US3] Implement `calculate_linear_reasoning_index` in `code/evaluator.py` (Input: `data/processed/test_metrics.csv`, Graphs from T017). **Dependency**: T017 must be completed before this task starts (see Critical Checkpoint). **Logic**: Use `trajectory_id` as join key; load graph files named `{trajectory_id}.json` from `data/processed/graphs/`. Calculate the `linear_reasoning_index` as the ratio of nodes with in-degree=1 and out-degree=1 divided by total node count for the success class and output `data/processed/linear_reasoning_report.json` to satisfy FR-008.
- [ ] T037b [US3] Implement `generate_results_report` in `code/evaluator.py` (Input: Outputs from T030, T031, T032, T033, T034, T035, T036, T037a, T038) to write `data/processed/results_report.json`. **Requirement**: Must explicitly include mean connectivity baseline from T034 and linear reasoning index from T038 in this report. **Schema**: JSON object with keys: `precision`, `recall`, `f1`, `threshold_used`, `linear_reasoning_index`, `p_value`, `pass_fail`, `sensitivity_analysis`. **Dependency**: Consumes `data/processed/correlation_test_result.json` from T037a.

### Tests for User Story 3

- [ ] T026 [P] [US3] Unit test for threshold calculation (20th percentile) in `tests/unit/test_evaluator.py`
- [ ] T027 [P] [US3] Unit test for confusion matrix and metric calculation in `tests/unit/test_evaluator.py`
- [ ] T028 [P] [US3] Integration test for full prediction pipeline on Train/Test split in `tests/integration/test_evaluator.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Run `code/hasher.py` to record hashes of all processed artifacts and update state file
- [ ] T040 Update `README.md` with execution instructions and environment setup
- [ ] T041 [P] Run full integration test suite on CPU-only environment (GitHub Actions runner simulation)
- [ ] T042 Document construct validity limitations (heuristic proxy vs ground truth) in `research.md` if edge detection accuracy < 60% (Input: manual spot-check of a sample of graphs stored in `data/processed/validity_check.json`)
- [ ] T043 Run quickstart.md validation

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
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All graph algorithms and NLP must run on CPU only (no CUDA/GPU); use `spaCy` in CPU mode (`en_core_web_sm`).
- **Data Integrity**: Never fabricate data; use real TELBench dataset fetched via `downloader.py` (NJU-LINK/TELBench).
- **Threshold Logic**: T030 (20th Percentile) is the PRIMARY threshold per FR-004 (Spec Mandate). T031 (F1-max) is for comparative analysis ONLY. T032a enforces this order by explicitly ignoring T031.
- **Input Dependencies**: All US3 tasks (T030-T038) explicitly depend on T029's output (`train_metrics.csv` / `test_metrics.csv`).
- **Linear Reasoning**: T038 explicitly addresses FR-008 by calculating a dedicated chain-like topology metric (ratio of nodes with in-degree=1 and out-degree=1) and including it in the final report (T037b).
- **Metric Usage**: Both `avg_branching_factor` (T022) and `global_connectivity` (T021) are calculated and included in the final metrics CSV (T023) and results report (T037b) to satisfy FR-003.
- **Data Leakage Prevention**: T036 and T037a operate on `train_metrics.csv` to ensure threshold sweeping and null distribution testing do not leak test set information.