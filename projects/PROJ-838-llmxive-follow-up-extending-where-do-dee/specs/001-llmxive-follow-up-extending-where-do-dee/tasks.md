# Tasks: llmXive follow-up: extending "Where Do Deep-Research Agents Go Wrong? Span-Level Error Localization"

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
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
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (pandas, networkx, scikit-learn, spacy, tqdm, pyyaml, requests, scipy, spacy-experimental)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/config.py` to define hyperparameters (`cutoff_depth`, `seed`, `dataset_url`)
- [ ] T005 [P] Implement `code/hasher.py` for SHA-256 artifact hashing and state file updates
- [ ] T006 [P] Implement data validation logic in `code/downloader.py` to handle malformed JSON and missing fields gracefully
- [ ] T007 [P] Implement `code/downloader.py` to fetch TELBench dataset from HuggingFace using validation logic from T006 with checksum verification
- [ ] T008 Setup `data/raw` and `data/processed` directories with `.gitkeep`
- [ ] T009 Configure `pytest` environment and create `tests/conftest.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Extract Topological Metrics from Early Trajectory Spans (Priority: P1) 🎯 MVP

**Goal**: Parse TELBench JSON, filter early spans (first int(len(spans) * config.cutoff_depth)), and construct a DAG based on co-reference/citation logic without using error labels.

**Independent Test**: Run on a single trajectory file; verify node count matches the first int(len(spans) * config.cutoff_depth) of spans and edges match manual inspection of co-references.

### Tests for User Story 1

- [ ] T010 [P] [US1] Unit test for span filtering logic in `tests/unit/test_graph_builder.py`
- [ ] T011 [P] [US1] Unit test for edge detection (co-reference/citation) in `tests/unit/test_graph_builder.py`
- [ ] T012 [P] [US1] Integration test for DAG construction on a sample trajectory in `tests/integration/test_graph_builder.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement `code/graph_builder.py` with `parse_trajectory` function to extract first int(len(spans) * config.cutoff_depth) spans
- [ ] T014 [US1] Implement co-reference resolution and citation detection using `spaCy` (`en_core_web_sm`) and `spacy-experimental`/`neuralcoref` in `code/graph_builder.py`
- [ ] T015 [US1] Implement `build_dag` function in `code/graph_builder.py` to construct `networkx.DiGraph` excluding ground-truth labels
- [ ] T016 [US1] Add error handling for trajectories shorter than int(len(spans) * config.cutoff_depth) (use all spans) and zero-edge cases (return empty graph)
- [ ] T017 [US1] Implement `save_graph` function to output intermediate DAGs to `data/processed/graphs/` as JSON

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Calculate Connectivity and Branching Metrics (Priority: P2)

**Goal**: Compute normalized Global Connectivity and Average Branching Factor for each trajectory's early-stage graph.

**Independent Test**: Feed a known small graph (3 nodes, 2 edges); verify output matches mathematically derived values exactly.

### Tests for User Story 2

- [ ] T018 [P] [US2] Unit test for Global Connectivity calculation in `tests/unit/test_metrics.py`
- [ ] T019 [P] [US2] Unit test for Average Branching Factor calculation in `tests/unit/test_metrics.py`
- [ ] T020 [P] [US2] Integration test for batch metric calculation in `tests/integration/test_metrics.py`

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/metrics.py` with `calculate_global_connectivity` (Input: `data/processed/graphs/`, Output: `metrics.csv`). Formula: edges / (N * (N - 1)), normalized by node count.
- [ ] T022 [US2] Implement `code/metrics.py` with `calculate_avg_branching_factor` (Input: `data/processed/graphs/`, Output: `metrics.csv`). Formula: sum of out-degrees / node count.
- [ ] T023a [US2] Implement `process_batch_iterate` in `code/metrics.py` to iterate over `data/processed/graphs/` JSON files.
- [ ] T023b [US2] Implement `process_batch_aggregate` in `code/metrics.py` to aggregate metrics and write `data/processed/metrics.csv`.
- [ ] T024 [US2] Ensure metrics handle zero-node or zero-edge cases by returning 0.0 instead of NaN
- [ ] T025 [US2] Add logging for batch processing progress using `tqdm`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Predict Collapse and Validate Against Ground Truth (Priority: P3)

**Goal**: Apply a data-driven threshold to metrics, predict collapse, and validate against ground-truth labels to generate Precision/Recall/F1.

**Independent Test**: Provide a synthetic dataset with known labels; verify confusion matrix matches expected values.

### Tests for User Story 3

- [ ] T026 [P] [US3] Unit test for threshold calculation (F1 max) in `tests/unit/test_evaluator.py`
- [ ] T027 [P] [US3] Unit test for confusion matrix and metric calculation in `tests/unit/test_evaluator.py`
- [ ] T028 [P] [US3] Integration test for full prediction pipeline on Train/Test split in `tests/integration/test_evaluator.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/evaluator.py` with `stratified_split` function (Input: `data/processed/metrics.csv`, Output: `data/processed/train_metrics.csv`, `data/processed/test_metrics.csv`) to divide data into Train/Test sets preserving label balance
- [ ] T030 [US3] Implement `calculate_optimal_threshold` in `code/evaluator.py` (Input: `data/processed/train_metrics.csv`) to maximize F1-score by sweeping thresholds on the Train set.
- [ ] T031 [US3] Implement `calculate_percentile_threshold` in `code/evaluator.py` (Input: `data/processed/train_metrics.csv`) to calculate the 20th percentile of connectivity for the success class as a baseline.
- [ ] T032 [US3] Implement `predict_collapse` in `code/evaluator.py` applying the threshold to the Test set
- [ ] T033 [US3] Implement `evaluate_performance` in `code/evaluator.py` to generate Precision, Recall, F1, and Confusion Matrix
- [ ] T034 [US3] Implement `calculate_baseline` in `code/evaluator.py` to calculate and report mean connectivity of the "success" class (FR-007). Verify output matches mean of success subset.
- [ ] T035 [US3] Implement `calculate_correlation` in `code/evaluator.py` to calculate and report Pearson/Spearman correlation coefficient (r) between connectivity and collapse (SC-002).
- [ ] T036 [US3] Implement `run_sensitivity_analysis` in `code/evaluator.py` to sweep thresholds (0.01, 0.05, 0.1) and percentiles (10, 20, 30).
- [ ] T037a [US3] Implement `calculate_null_distribution` in `code/evaluator.py` to perform permutation test (1000 permutations, shuffle labels, p < 0.05) to establish null distribution.
- [ ] T037b [US3] Implement `generate_results_report` in `code/evaluator.py` to write `data/processed/results_report.json` with all metrics, thresholds, and sensitivity data.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Run `code/hasher.py` to record hashes of all processed artifacts and update state file
- [ ] T039 Update `README.md` with execution instructions and environment setup
- [ ] T040 [P] Run full integration test suite on CPU-only environment (GitHub Actions runner simulation)
- [ ] T041 Document construct validity limitations (heuristic proxy vs ground truth) in `research.md` if edge detection accuracy < 60%
- [ ] T042 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (needs graphs to calculate metrics)
- **User Story 3 (P3)**: Depends on US2 completion (needs metrics to predict collapse)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Core logic before batch processing
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Tests for a specific user story marked [P] can run in parallel
- Once Foundational phase completes, US1 can start immediately; US2 and US3 must wait for their predecessors

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
   - Developer C: User Story 3 (Evaluation) - *Wait for US2 data*
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
- **Critical Constraint**: All graph algorithms and NLP must run on CPU only (no CUDA/GPU); use `spaCy` in CPU mode.
- **Data Integrity**: Never fabricate data; use real TELBench dataset fetched via `downloader.py`.