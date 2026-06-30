# Tasks: Predicting Cognitive Decline from Resting-State fMRI Network Topology

**Input**: Design documents from `/specs/001-predict-cognitive-decline/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

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

- [ ] T001 Create directories `code/`, `tests/`, and `docs/` at repository root
- [ ] T002 Create directories `data/raw/` and `data/processed/` at repository root
- [ ] T003 Create directories `tests/unit/`, `tests/integration/`, and `tests/contract/` at repository root
- [ ] T004 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt` (nibabel, networkx, scikit-learn, pandas, numpy, bids, requests, tqdm, pytest, fsl, nilearn). Define `EXIT_CODE_NO_LABELS = 2` in `code/utils/constants.py` and configure `code/00_data_gate.py` to verify OpenNeuro `ds000246` availability, exiting with code `2` if metadata is missing.
- [ ] T005 [P] Implement utility modules: `code/utils/io.py` (BIDS loading), `code/utils/graph.py` (AAL atlas loading), `code/utils/stats.py` (collinearity checks)
- [ ] T006 [P] Setup logging infrastructure in `code/utils/logger.py` to capture excluded subjects and feature filtering logs
- [ ] T007 Create base schema contracts in `specs/001-predict-cognitive-decline/contracts/` for dataset, graph metrics, and model output
- [ ] T008 Configure environment configuration management for random seeds (`random_seed=42`) and runtime limits

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T009 [P] Setup data versioning gate: Implement `code/00_data_gate.py` to verify OpenNeuro `ds000246` availability and exit with `EXIT_CODE_NO_LABELS` (2) if metadata is missing
- [ ] T010 [P] Implement utility modules: `code/utils/io.py` (BIDS loading), `code/utils/graph.py` (AAL atlas loading), `code/utils/stats.py` (collinearity checks)
- [ ] T011 [P] Setup logging infrastructure in `code/utils/logger.py` to capture excluded subjects and feature filtering logs
- [ ] T012 Create base schema contracts in `specs/001-predict-cognitive-decline/contracts/` for dataset, graph metrics, and model output
- [ ] T013 Configure environment configuration management for random seeds (`random_seed=42`) and runtime limits

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Download raw BIDS rs-fMRI data, filter for longitudinal scores, and generate graph metrics.

**Independent Test**: The pipeline can be run on a single batch of data to produce `data/processed/graph_metrics.csv` containing subject IDs and calculated graph metrics without any machine learning training.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T014 [P] [US1] Unit test for AAL atlas parcellation in `tests/unit/test_parcellation.py`
- [ ] T015 [P] [US1] Unit test for graph metric calculation (degree, efficiency) in `tests/unit/test_graph_metrics.py`
- [ ] T016 [P] [US1] Integration test for data filtering logic (MMSE/MOCA non-null check) in `tests/integration/test_filtering.py`

### Implementation for User Story 1

- [ ] T017 [P] [US1] Implement `code/01_download_and_filter.py`: Download `ds000246`, parse BIDS metadata, filter for subjects with non-null MMSE/MOCA at both timepoints, limit to N=min(a predefined threshold, available_eligible), fail if zero eligible subjects, log excluded subjects
- [ ] T018 [P] [US1] Implement `code/02_preprocess_and_parcellate.py`: Load raw BIDS data, perform motion correction using `fsl` (mcflirt), normalization using `nilearn`, apply 90-region AAL atlas, generate 90x90 connectivity matrices for each subject
- [ ] T019 [US1] Implement `code/03_compute_graph_metrics.py`: Calculate node degree, global efficiency, clustering coefficient, and path length for every subject; output to `data/processed/graph_metrics.csv`
- [ ] T020 [US1] Add validation: Verify memory usage during graph metric calculation stays within 7GB RAM limit on 2-core runner

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Modeling and Validation (Priority: P2)

**Goal**: Train a Random Forest classifier with nested cross-validation to predict cognitive decline.

**Independent Test**: The pipeline can be executed to output `data/processed/model.pkl` and `data/processed/performance_report.json` containing ROC-AUC and F1-score for nested CV, without running the permutation test.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T021 [P] [US2] Unit test for nested CV grid search logic in `tests/unit/test_nested_cv.py`
- [ ] T022 [P] [US2] Integration test for model training and evaluation flow in `tests/integration/test_model_training.py`

### Implementation for User Story 2

- [ ] T023 [P] [US2] Implement `code/04_train_model.py`: Define decline label (drop ≥ 3 points), implement Nested CV (5-fold outer, grid search inner for n_estimators ∈ {a range of values}, max_depth ∈ {5, 10, None}). Inside the inner loop: perform collinearity check (exclude features with correlation > 0.95, keep higher variance), apply Variance Thresholding (variance > 0.01) and RFE (select a subset of top features), then fit Random Forest (n_estimators=100, max_depth=None, random_seed=42).
- [ ] T024 [US2] Implement `code/05_evaluate_model.py`: Calculate ROC-AUC, accuracy, and F1-score per fold and mean; output to `data/processed/performance_report.json`
- [ ] T025 [US2] Implement `code/11_external_outcome_check.py`: Check for MCI conversion data in dataset; if unavailable, document this limitation in the final report (write to `data/artifacts/limitations.txt`)
- [ ] T026 [US2] Verify runtime: Ensure nested CV training completes within 30 minutes on CPU-only runner

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance and Sensitivity Analysis (Priority: P3)

**Goal**: Validate model significance via permutation test and assess robustness via threshold sensitivity.

**Independent Test**: The pipeline can take an existing model and performance metric, run the permutation test, and output `data/processed/permutation_results.json` and `data/processed/sensitivity_report.json`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T027 [P] [US3] Unit test for p-value calculation logic in `tests/unit/test_permutation.py`
- [ ] T028 [P] [US3] Unit test for threshold sweep logic in `tests/unit/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `code/06_permutation_test.py`: Import training logic from `code/04_train_model.py`. Shuffle labels 500 times (seed=42), re-train/re-evaluate model. Monitor runtime; if > 2 hours, stop immediately, log the number of completed permutations, and calculate a partial p-value based on completed runs. Output to `data/processed/permutation_results.json`.
- [ ] T030 [US3] Implement `code/07_sensitivity_analysis.py`: Sweep decision thresholds {, 0.50, 0.55}. Additionally, re-calculate 'decline' labels using the ±1 point variation on raw MMSE/MOCA scores, re-run classification for each variation, and report FPR/FNR variation for all thresholds and label definitions. Output to `data/processed/sensitivity_report.json`.
- [ ] T031 [US3] Implement `code/09_generate_report.py`: Aggregate all results, explicitly label findings as "associational" (FR-007), document limitations (read from `data/artifacts/limitations.txt`), output `data/artifacts/final_report.md`.
- [ ] T032 [US3] Implement `code/10_verify_success_criteria.py`: Check ROC-AUC > 0.50, p < 0.05, and runtime < 6h; output `VERIFICATION_STATUS` and `runtime_report.json`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T033 [P] Documentation updates: Update `README.md` with execution order and data requirements
- [ ] T034 Code cleanup: Remove debug prints, ensure all random seeds are pinned to 42
- [ ] T035 Performance optimization: Refactor `code/03_compute_graph_metrics.py` to use `joblib.Parallel(n_jobs=2)` and verify runtime reduction
- [ ] T036 [P] Run `tests/` suite and ensure [deferred] pass rate
- [ ] T037 Security hardening: Scan `data/raw/` for PII using `bids-validator` (via `pybids`) to check JSON sidecars and filenames for patterns (names, IDs) and ensure redaction
- [ ] T038 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for AAL atlas parcellation in tests/unit/test_parcellation.py"
Task: "Unit test for graph metric calculation in tests/unit/test_graph_metrics.py"

# Launch all models for User Story 1 together:
Task: "Implement download_and_filter.py"
Task: "Implement preprocess_and_parcellate.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
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
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: Ensure `code/01_download_and_filter.py` handles OpenNeuro download failures with retries and clear exit codes.
- **Critical**: Ensure `code/03_compute_graph_metrics.py` does not load full raw NIfTI files into memory simultaneously if N=100 exceeds RAM; process subject-by-subject.
- **Critical**: Ensure `code/04_train_model.py` uses `joblib` or similar for parallelization within the 2-core limit without oversubscription.