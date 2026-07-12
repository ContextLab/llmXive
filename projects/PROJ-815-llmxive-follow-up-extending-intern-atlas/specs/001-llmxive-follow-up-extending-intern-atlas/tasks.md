# Tasks: llmXive follow-up: extending Intern-Atlas

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-intern-atlas/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
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

- [ ] T001 Create project structure: `mkdir -p projects/PROJ-815-llmxive-follow-up-extending-intern-atlas/{code/data,code/models,code/analysis,code/utils,data/raw,data/processed,tests/unit,tests/integration}`
- [ ] T002 Initialize Python 3.11 project: Create `projects/PROJ-815-llmxive-follow-up-extending-intern-atlas/requirements.txt` with pinned versions (e.g., `pandas==2.0.3`, `numpy==1.24.3`, `scikit-learn==1.3.0`, `networkx==3.1`, `requests==2.31.0`, `pyyaml==6.0.1`, `seaborn==0.13.0`, `matplotlib==3.7.2`, `python-Levenshtein==0.21.1`)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Create `code/utils/constants.py` defining constants for date ranges (2010-2018), edge types (`improves`, `replaces`, `extends`), and retraction label mappings (0=Robust, 1=Fragile, 2=Retraction-Only)
- [ ] T005 [P] Create `code/utils/graph_utils.py` with helper functions for graph loading, edge filtering, and metadata validation
- [ ] T006 [P] Document the "Synthetic Fallback Protocol" in `docs/fallback_protocol.md` as a contingency for missing real data, ensuring it is an authorized part of the workflow (not silent drift)
- [ ] T007 [P] Configure environment configuration (`.env.example`) and logging infrastructure (`code/utils/logging_config.py`) with keys for `DATA_PATH`, `LOG_LEVEL`, `SEED`
- [ ] T008 [P] Create `data-model.md` in `specs/001-llmxive-follow-up-extending-intern-atlas/` defining the schema for `MethodNode`, `RetractionLabel`, and `TopologicalFeatures`
- [ ] T009 [P] Create `contracts/` directory and files: `dataset.schema.yaml` and `model.schema.yaml` in `specs/001-llmxive-follow-up-extending-intern-atlas/contracts/`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Extraction and Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Ingest Intern-Atlas graph and retraction databases to compute topological features and labels for nodes from a historical period..

**Independent Test**: The pipeline can be tested by running the extraction script on a small subset and verifying the output CSV contains computed features and correct binary labels.

### Tests for User Story 1 (Scaffolding - Parallel)

> **NOTE**: Create these test files first (empty or with placeholders) to define the interface. Execution happens after implementation.

- [ ] T010 [P] [US1] Scaffold unit test file `tests/unit/test_feature_extraction.py` for edge type filtering logic
- [ ] T011 [P] [US1] Scaffold unit test file `tests/unit/test_graph_utils.py` for Levenshtein fuzzy matching logic
- [ ] T012 [P] [US1] Scaffold integration test file `tests/integration/test_pipeline.py` for full extraction pipeline on synthetic data

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `code/data/extract_intern_atlas.py`: Load graph, filter nodes by year (2010-2018), validate edge types (exclude LLM-inferred and retraction-outcome types), handle missing edge types.
- [ ] T014 [P] [US1] Implement `code/data/compute_features.py`: Calculate `bottleneck_resolution_ratio` (improves/replaces edges / total outgoing) and `branching_entropy` (Shannon entropy of downstream method types); handle nodes with 0 outgoing edges gracefully
- [ ] T015 [P] [US1] Implement `code/data/merge_retractions.py`: Map nodes to retraction databases using exact DOI match first, then Levenshtein fuzzy match (ratio >= 0.85) for title/author; implement duplicate resolution (earliest date, then alphabetical journal)
- [ ] T016 [US1] Implement label mapping logic in `code/data/merge_retractions.py` to assign label `1` (Fragile), `2` (Retraction-Only), or `0` (Robust) based on retraction reason (FR-004)
- [ ] T017 [US1] Implement main pipeline orchestrator in `code/data/run_extraction.py` to chain extraction, feature computation, and merging. **CRITICAL**: This function MUST check for the existence of ground truth labels; if missing, it MUST ABORT with the exact message: "No ground truth labels found for the specified time window; analysis cannot proceed." Output `data/processed/features_2010_2018.csv`.

### Execution for User Story 1 (Sequential - After Implementation)

- [ ] T018 [US1] Execute unit tests in `tests/unit/test_feature_extraction.py`
- [ ] T019 [US1] Execute unit tests in `tests/unit/test_graph_utils.py`
- [ ] T020 [US1] Execute integration tests in `tests/integration/test_pipeline.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train and compare topological vs. citation-only models to predict retraction status.

**Independent Test**: The training script can be run with a fixed seed; output must show AUC-ROC and Precision-Recall for both models.

### Tests for User Story 2 (Scaffolding - Parallel)

- [ ] T021 [P] [US2] Scaffold unit test file `tests/unit/test_model_training.py` for data split logic (stratified time-based)
- [ ] T022 [P] [US2] Scaffold integration test file `tests/integration/test_pipeline.py` for model training and evaluation

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement `code/models/train_baseline.py`: Train Logistic Regression using only `citation_count` and `publication_year`; ensure stratified time-based split (early period train, later period val) with minimum positive case check
- [ ] T024 [US2] Implement `code/models/train_topological.py`: Train **binary** Logistic Regression using only `bottleneck_resolution_ratio` and `branching_entropy` to predict binary `retraction_status` (Fragile vs Robust); output coefficients. **Do NOT implement multi-class classification.**
- [ ] T025 [US2] Implement `code/models/evaluate.py`: Calculate AUC-ROC, Precision, Recall, F1 for both binary models; generate PR curves; compute delta metrics between topological and baseline models; save results to `data/processed/model_results.json`
- [ ] T026 [US2] Implement comparison logic to report if topological model provides independent predictive power over citation baseline

### Execution for User Story 2 (Sequential - After Implementation)

- [ ] T027 [US2] Execute unit tests in `tests/unit/test_model_training.py`
- [ ] T028 [US2] Execute integration tests in `tests/integration/test_pipeline.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness and Sensitivity Analysis (Priority: P3)

**Goal**: Perform permutation tests and threshold sweeps to ensure findings are not spurious.

**Independent Test**: The robustness script generates a distribution of AUC scores from permuted labels; result must show observed AUC significantly exceeds the mean of permuted distributions.

### Tests for User Story 3 (Scaffolding - Parallel)

- [ ] T029 [P] [US3] Scaffold unit test file `tests/unit/test_robustness.py` for permutation test logic
- [ ] T030 [P] [US3] Scaffold unit test file `tests/unit/test_robustness.py` for collinearity diagnostics (VIF/MI)

### Implementation for User Story 3

- [ ] T031 [P] [US3] Implement `code/analysis/robustness_tests.py`: Perform stratified permutation test with **exactly n=100 iterations** (as per FR-007) shuffling labels while controlling for `field_of_study` and `publication_venue`; compare observed AUC to permuted distribution.
- [ ] T032 [US3] Implement `code/analysis/sensitivity_analysis.py`: Run threshold sweep over the **specific set {0.3, 0.5, 0.7}** (as per FR-008 and SC-002); calculate and report FPR/FNR for each; calculate VIF and MI for predictors; flag instability if VIF > 5 or MI > 0.1.
- [ ] T033 [US3] Implement structural coupling diagnostic: If VIF > 5, re-run model with single predictor or composite metric and report as sensitivity analysis
- [ ] T034 [US3] Implement covariate adjustment: **MUST perform** logistic regression with `field_of_study` and `publication_venue` as covariates to control for confounding variables (as per FR-012); this is a **required, unconditional** step.

### Execution for User Story 3 (Sequential - After Implementation)

- [ ] T035 [US3] Execute unit tests in `tests/unit/test_robustness.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Artifact Generation (Polish)

**Purpose**: Generate final results and update `research.md`.

- [ ] T036 [P] Aggregate metrics from `model_results.json` and sensitivity analysis outputs into `data/processed/final_metrics_summary.csv`
- [ ] T037 [P] Generate plots: Save PR curve to `data/processed/plots/pr_curve.png`, Permutation distribution to `data/processed/plots/permutation_dist.png`, and Threshold sensitivity to `data/processed/plots/threshold_sweep.png`
- [ ] T038 [US3] Write final report to `specs/001-llmxive-follow-up-extending-intern-atlas/research.md` including methodology, results, limitations (synthetic fallback status), and conclusions
- [ ] T039 [P] Review and update `data-model.md` and `contracts/` in `specs/001-llmxive-follow-up-extending-intern-atlas/` if implementation diverged from initial schema

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
- **User Story 2 (P2)**: Depends on US1 completion (needs processed features)
- **User Story 3 (P3)**: Depends on US2 completion (needs trained models)

### Within Each User Story

- Tests (Scaffolding) MUST be created FIRST (parallel)
- Implementation follows
- Test Execution follows Implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Test Scaffolding tasks within a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (only after US1 data is ready for US2/US3)

---

## Parallel Example: User Story 1

```bash
# Launch all test scaffolding for User Story 1 together:
Task: "Scaffold unit test file tests/unit/test_feature_extraction.py"
Task: "Scaffold unit test file tests/unit/test_graph_utils.py"

# Launch core implementation tasks in parallel (different files):
Task: "Implement code/data/extract_intern_atlas.py"
Task: "Implement code/data/compute_features.py"
Task: "Implement code/data/merge_retractions.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Pipeline)
4. **STOP and VALIDATE**: Test extraction on synthetic data; verify CSV output matches schema
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! Data Pipeline)
3. Add User Story 2 → Test independently → Deploy/Demo (Modeling)
4. Add User Story 3 → Test independently → Deploy/Demo (Robustness)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data Extraction)
   - Developer B: User Story 2 (Modeling) - *Note: Can start once US1 data schema is defined, but needs actual data output to run fully*
   - Developer C: User Story 3 (Robustness) - *Note: Needs US2 models to run*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical**: Ensure Synthetic Fallback Protocol is triggered correctly if real data is missing; scientific analysis must abort in that case.
- **Critical**: Ensure edge types are strictly human-annotated; exclude any LLM-inferred edges to prevent semantic leakage.
- **Critical**: Ensure permutation tests are stratified by field/venue to control confounding.
- **Critical**: Ensure the retraction-only label is mapped correctly for data integrity but models predict binary Fragile vs Robust.
- **Critical**: Ensure FR-012 "MUST perform" covariate adjustment is executed unconditionally.