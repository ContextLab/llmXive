# Tasks: Predicting the Glass Forming Region of Alloy Systems with Machine Learning

**Input**: Design documents from `/specs/001-predict-glass-forming-region/`
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

- [ ] T001a [P] Create root project structure: `projects/PROJ-510-predicting-the-glass-forming-region-of-a/`, `data/`, `code/`, `tests/`, `docs/`
- [X] T001b [P] Create source code structure: `code/__init__.py`, `code/utils.py`, `code/ingestion.py`, `code/features.py`, `code/train.py`, `code/analyze.py`, `requirements.txt`
- [X] T001c [P] Create test structure: `tests/__init__.py`, `tests/test_features.py`, `tests/test_ingestion.py`, `tests/test_train.py`, `tests/test_analyze.py`
- [X] T002 Initialize Python 3.11 project with dependencies: `pandas`, `scikit-learn`, `numpy`, `requests`, `pyyaml`, `datasets`, `mendeleev` in `requirements.txt`
- [ ] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your plan):

- [ ] T004 Setup `data/raw/` and `data/processed/` directory structure with `.gitignore` rules for large files
- [X] T005 [P] Implement `code/utils.py` with periodic table lookup helpers using `mendeleev` and logging infrastructure
- [ ] T006 [P] Create `contracts/dataset.schema.yaml` defining `AlloyRecord` fields (composition, critical_cooling_rate, mixing_enthalpy, atomic_size_mismatch, electronegativity_variance, source_label derived from dataset metadata)
- [ ] T007 Create `contracts/model_output.schema.yaml` defining `ModelMetrics` and `SensitivityReport` structures
- [ ] T008 Configure error handling: Ensure data loading fails loudly (no synthetic fallback) if `matsci/glass-forming-ability` fetch fails
- [X] T009 Setup `pytest` configuration and seed management (`random_state=42`) in `code/utils.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Thermodynamic Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Download experimental data, filter for valid ternary alloys, and compute thermodynamic descriptors.

**Independent Test**: The pipeline can be run in isolation to produce a CSV file containing at least 500 valid alloy records with all required thermodynamic columns and the `critical_cooling_rate` column computed, without training any model.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. Note: These tests depend on T012-T017 for execution.**

- [X] T010 [US1] Unit test for thermodynamic formula calculation (mixing enthalpy, atomic size mismatch) in `tests/test_features.py`
- [X] T011 [US1] Integration test for data ingestion pipeline ensuring ≥500 rows and no NaN in target columns in `tests/test_ingestion.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/ingestion.py`: Download `matsci/glass-forming-ability` dataset using `datasets.load_dataset` (streaming=False for <7GB check, then filter). Ensure strict error on missing `critical_cooling_rate` column. Explicitly reconcile: Use MatsSci-Glass for CCR values and Mendeleev for elemental properties (Constitution Principle VI).
- [X] T013 [US1] Implement `code/ingestion.py`: Filter dataset for ternary alloys (3 elements) and exclude rows with missing elemental data or unknown glass-forming labels. Log exclusion counts.
- [X] T014 [P] [US1] Implement `code/features.py`: Calculate `mixing_enthalpy` using `mendeleev` elemental properties and ternary composition weights.
- [X] T015 [P] [US1] Implement `code/features.py`: Calculate `atomic_size_mismatch` and `electronegativity_variance` using standard periodic table definitions.
- [ ] T016 [US1] Implement `code/features.py`: Validate computed features (tolerance 1e-6) and save processed data to `data/processed/processed_alloys.csv`.
- [ ] T017 [US1] Add validation to ensure `critical_cooling_rate` has non-zero variance and ≥500 entries; fail gracefully with specific error if not.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train a Random Forest regressor with 5-fold cross-validation and evaluate performance.

**Independent Test**: The training script can be executed on the generated dataset to produce a trained model file and a metrics report containing the cross-validation score, without requiring any external GPU or internet access after the data is loaded.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for 5-fold cross-validation split generation ensuring non-overlapping folds in `tests/test_train.py`
- [X] T019 [P] [US2] Integration test for model training producing valid `ModelMetrics` schema in `tests/test_train.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/train.py`: Load `data/processed/processed_alloys.csv`, perform 80/20 train-test split with `random_state=42`.
- [X] T021 [US2] Implement `code/train.py`: Train `RandomForestRegressor` and perform 5-fold cross-validation. Calculate mean RMSE and fold variance.
- [X] T022 [US2] Implement `code/train.py`: Evaluate on held-out test set, calculate test RMSE, and save model to `data/models/random_forest_model.pkl`.
- [X] T023 [US2] Implement `code/train.py`: Generate `ModelMetrics` report (CSV/JSON) containing `fold_scores`, `mean_rmse`, `test_rmse`.
- [ ] T024a [P] [US2] Generate null model distribution: Train a `DummyRegressor` (mean strategy) on the training set. Perform 1000 bootstrap samples, train a `DummyRegressor` on each, and record the RMSE distribution. Save distribution to `data/models/null_model_distribution.json`.
- [ ] T024 [US2] [Depends on T024a] Compare RF RMSE against the null model distribution generated in T024a (`data/models/null_model_distribution.json`). Perform a two-sided t-test (p < 0.05) to assert statistical significance (SC-002). **MUST raise AssertionError if p >= 0.05.**
- [ ] T025 [US2] Add explicit documentation/comment in code framing findings as ASSOCIATIONAL (FR-006).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Sensitivity Analysis (Priority: P3)

**Goal**: Perform permutation importance analysis and sensitivity analysis on classification thresholds.

**Independent Test**: The analysis script can be run on the trained model to output a ranked list of feature importances and a sensitivity report showing how performance metrics vary with threshold changes.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for permutation importance calculation (n=1000, random_state=42) in `tests/test_analyze.py`
- [ ] T027 [P] [US3] Integration test for sensitivity analysis across thresholds {50, 100, 150} K/s in `tests/test_analyze.py`

### Implementation for User Story 3

- [ ] T028 [US3] Implement `code/analyze.py`: Load trained model and dataset. Perform permutation importance analysis (n_permutations=1000, random_state=42).
- [ ] T029 [US3] Implement `code/analyze.py`: Calculate p-values for feature importances against shuffled baseline. Rank features and flag top contributors (SC-004).
- [ ] T030a [US3] [Depends on T022] Detect collinearity: Check correlation matrix of predictors. Flag any pair with correlation > 0.8. IF flagged, re-train the Random Forest model excluding one of the collinear features and save as `data/models/stability_test_model.pkl`. **ELSE (if no collinearity flagged), copy `data/models/random_forest_model.pkl` to `data/models/stability_test_model.pkl` to ensure a model artifact exists for the next step.**
- [ ] T030b [US3] [Depends on T030a] Verify stability: Compare the RMSE of the model from T030a (`data/models/stability_test_model.pkl`) against the original model (T022). Assert that the RMSE difference is < 5% to verify stability (US-3 Acceptance Scenario 3).
- [ ] T031 [US3] [Depends on T022, T023] Implement `code/analyze.py`: Load trained model and dataset. Conduct sensitivity analysis sweeping the **specific thresholds {50, 100, 150} K/s**. For each threshold: IF threshold < 100 K/s THEN binarize target (CCR < threshold) and calculate F1; ELSE calculate RMSE. Use the binarization cutoff as defined in the method.
- [ ] T032 [US3] Implement `code/analyze.py`: Generate `SensitivityReport` (CSV/JSON). Include validation logic: IF binarized (threshold < 100 K/s) THEN assert F1 variance < 10% (Raise error if >= 10%); ELSE assert RMSE variance < 10% (Raise error if >= 10%).
- [ ] T033 [US3] Add validation to ensure RMSE variance across thresholds is negligible (<10% if binarized) as per SC-003.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates: Add `README.md` with execution instructions. Sections required: 'Prerequisites' (list packages), 'Data Ingestion Command' (`python code/ingestion.py`), 'Training Command' (`python code/train.py`), 'Analysis Command' (`python code/analyze.py`).
- [ ] T035 Code cleanup and refactoring to ensure `random_state=42` is consistent across all scripts
- [ ] T036 Performance optimization: Verify pipeline completes within 6 hours on CPU-only runner (2 cores, 7 GB RAM)
- [ ] T037 [P] Run `quickstart.md` validation to ensure all artifacts match schemas in `contracts/`
- [ ] T038 Security hardening: Ensure no hardcoded secrets or external URLs other than verified `matsci/glass-forming-ability`

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Must produce `data/processed/processed_alloys.csv`**.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T016 output** (processed data). May integrate with US1 but should be independently testable.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on T023 output** (trained model). May integrate with US1/US2 but should be independently testable.

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
Task: "Unit test for thermodynamic formula calculation in tests/test_features.py"
Task: "Integration test for data ingestion pipeline in tests/test_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement code/ingestion.py: Download dataset"
Task: "Implement code/features.py: Calculate mixing_enthalpy"
Task: "Implement code/features.py: Calculate atomic_size_mismatch"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Data Ingestion & Feature Engineering)
4. **STOP and VALIDATE**: Test User Story 1 independently (verify ≥500 rows, correct features)
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
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Model Training) - *Wait for US1 data*
 - Developer C: User Story 3 (Analysis) - *Wait for US2 model*
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
- **Data Integrity**: Never use synthetic fallbacks. If `matsci/glass-forming-ability` fails, the pipeline must crash with a clear error.
- **Compute**: All tasks are designed to run on CPU (2 cores, 7GB RAM) within 6 hours. No GPU required for Random Forest on a moderate-sized dataset

The research question remains: How does Random Forest perform on tabular data?
The method remains: Random Forest classifier.
References: [Citation preserved as in original context].