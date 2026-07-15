# Tasks: Predicting Plant Stress Resilience from Publicly Available Metabolomic Data

**Input**: Design documents from `/specs/001-predict-plant-stress-resilience/`
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

- [ ] T001 Create project structure per implementation plan in `projects/PROJ-455-predicting-plant-stress-resilience/` by executing `mkdir -p code/data code/models code/analysis tests/unit tests/integration tests/contract tests/benchmark contracts data/raw data/processed data/results`.
- [ ] T002 Initialize Python 3.11 project with dependencies (`pandas==2.0.3`, `scikit-learn==1.3.0`, `numpy==1.24.0`, `requests==2.31.0`, `biopython==1.81`, `pyyaml==6.0.1`, `pytest==7.4.0`) in `requirements.txt`.
- [ ] T003 [P] Configure linting (flake8/black) by creating `.flake8` and `pyproject.toml` with black settings.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Define data schemas in `contracts/`:
 - T004.1 Create `contracts/dataset.schema.yaml` defining JSON/YAML schema for `MetabolomicProfile`.
 - T004.2 Create `contracts/model_result.schema.yaml` defining JSON/YAML schema for `ModelResult`.
 - T004.3 Create `contracts/recovery.schema.yaml` defining JSON/YAML schema for `RecoveryMetric`.
- [ ] T005 [P] Implement base data models (`MetabolomicProfile`, `RecoveryMetric`, `RecoveryIndex`) with validation rules in `code/data/models.py` using Pydantic.
- [X] T006 [P] Setup logging and error handling infrastructure in `code/utils/logging.py` by implementing a `get_logger` function that configures a standard JSON formatter and file/console handlers.
- [ ] T007 Create the Mechanism-Guided Synthetic Generator in `code/data/generator.py` by implementing `generate_synthetic_data(n_samples, stress_type)` that outputs a Parquet file to `data/raw/synthetic_*.parquet` with embedded ground-truth pathways. <!-- FAILED: unspecified -->
- [~] T008 [P] Implement the Mock Adapter in `code/data/ingest.py` by creating `MockAdapter` class that calls the synthetic generator and returns a Pandas DataFrame matching `dataset.schema.yaml`.
- [X] T009 [P] Implement the Real Adapter stub in `code/data/ingest.py` by creating `RealAdapter` class with a `fetch(accession_id)` method that validates URL format and returns a stub DataFrame or raises a NotImplementedError.
- [ ] T009.1 [P] Implement ExternalDatasetManager in `code/data/ingest.py` by creating `ExternalDatasetManager` class that ingests, checksums, and validates multiple independent external datasets (NCBI GEO/Zenodo) for LODO.
- [ ] T009.2 [P] Implement LODO Data Prep in `code/data/ingest.py` by creating `prepare_lodo_datasets()` function that organizes external datasets into train/test splits for Leave-One-Dataset-Out validation.
- [ ] T009.3 [P] Implement Synthetic Multi-Dataset Generator in `code/data/generator.py` by creating `generate_lodo_synthetic_datasets(n_datasets, stress_types)` that produces multiple distinct Parquet files with varying noise profiles and stress vectors to simulate external datasets for LODO validation.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw plant metabolomic datasets (synthetic or real), filter for relevant stress conditions, and normalize data for analysis.

**Independent Test**: Run the data pipeline script against the synthetic generator output and verify the output is a normalized CSV/Parquet file with no missing critical columns, correct row counts, and applied transformations (ln, half-min, TIC).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for data ingestion schema in `tests/contract/test_ingest_schema.py`.
- [X] T011 [P] [US1] Integration test for preprocessing pipeline in `tests/integration/test_preprocess_pipeline.py`.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/data/ingest.py::RealAdapter::fetch` to parse NCBI GEO/Zenodo XML/JSON responses into a `MetabolomicProfile` DataFrame. <!-- FAILED: unspecified -->
- [X] T013 [US1] Implement `code/data/ingest.py::filter_by_recovery_time(df, min_days=7)` function that returns a filtered DataFrame.
- [X] T014 [US1] Implement `code/data/preprocess.py::normalize_recovery(df)` function that maps biomass/survival columns to a `RecoveryIndex` (normalized scale) column.
- [X] T015 [US1] Implement `code/data/preprocess.py::check_missing_threshold(df, threshold=0.1)` that raises a `DataRejectionError` if missing >10%.
- [X] T016 [US1] Implement `code/data/preprocess.py::impute_half_min(df)` function that replaces NaN with half the column minimum.
- [X] T017 [US1] Implement `code/data/preprocess.py::normalize_tic_and_log(df)` function that applies TIC normalization and **natural log (ln)** transformation (using `np.log` with zero-handling logic) as required by FR-003.
- [X] T018 [US1] Implement `code/data/preprocess.py::aggregate_population(df)` function that computes mean pre-stress and mean recovery per group if individual pairing is missing.
- [X] T019 [US1] Add validation and error handling for dataset rejection scenarios in `code/data/ingest.py` to catch `DataRejectionError` and log specific rejection reasons (e.g., 'Missing >10%') to `code/utils/logging.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Model Training and Feature Importance (Priority: P2)

**Goal**: Train Random Forest and SVM models to predict recovery rates from pre-stress metabolomic profiles and identify the most predictive metabolites.

**Independent Test**: Train models on a split dataset, evaluate performance metrics (R² or Pearson correlation), and verify that feature importance rankings are generated for the top 20 metabolites.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for model output schema in `tests/contract/test_model_result_schema.py`.
- [~] T021 [P] [US2] Unit test for feature importance extraction in `tests/unit/test_feature_importance.py`. <!-- SKIPPED: YAML+regex parse failed (while scanning an alias
  in "<unicode string>", line 2, column 1:
    **Implementation Details:**
    ^
expected alphabetic or numeric character, but found '*'
  in "<unicode string>", line 2, column 2:
    **Implementation Details:**
     ^) -->

### Implementation for User Story 2

- [ ] T022 [US2] Implement `code/models/train.py::train_random_forest(X, y, cv=5)` returning a fitted model and `model_result.schema.yaml` compliant metrics.
- [ ] T023 [US2] Implement `code/models/train.py::train_svm(X, y, cv=5)` returning a fitted model and metrics.
- [ ] T024.1 [US2] Implement `code/models/train.py::calculate_metric(y_true, y_pred, mode)` that returns R² for individual mode and Pearson r for population mode.
- [ ] T025 [US2] Implement `code/models/train.py::get_top_features(model, n=20)` returning a list of (feature_name, importance) tuples.
- [ ] T026 [US2] Consume persisted KEGG mapping from processed data in `code/models/train.py` for downstream validation.
- [ ] T027 [US2] Add logging for model training metrics in `code/models/train.py` to record R²/r, top 5 features, and training time to the configured logger.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cross-Stress Generalizability and Statistical Validation (Priority: P3)

**Goal**: Evaluate model generalizability across stress types, perform permutation testing, and validate biological plausibility against known pathways.

**Independent Test**: Run cross-stress evaluation and permutation test (n=1000), verify p-values are calculated, generalizability scores reported, and pathway enrichment checks pass.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US3] Contract test for validation results schema in `tests/contract/test_validation_schema.py`.
- [ ] T029 [P] [US3] Integration test for cross-stress evaluation in `tests/integration/test_cross_stress_eval.py`.

### Implementation for User Story 3

- [ ] T019.2 [US3] Implement `code/analysis/pathway.py::map_to_kegg(df)` function that maps raw metabolite names to KEGG Compound IDs using a local mapping table and persists the IDs as a new column in the processed DataFrame (Moved from T019.1 to align with project structure).
- [ ] T030 [US3] Implement `code/models/validate.py::lodo_cv(models, datasets)` that executes the Leave-One-Dataset-Out loop (train on N-1, test on held-out) using the synthetic or external datasets, returning a list of scores.
- [ ] T031 [US3] Implement `code/models/validate.py::cross_stress_eval(model, train_stress, test_stress)` calculating R²_drop or r_drop.
- [ ] T032 [US3] Implement `code/models/validate.py::permutation_test(model, X, y, n=1000)` returning a p-value.
- [ ] T033 [US3] Implement `code/analysis/pathway.py::enrichment_analysis(kegg_ids, pathways)` calculating Jaccard similarity and Enrichment p-value.
- [ ] T034 [US3] Implement `code/analysis/pathway.py::validate_alignment(jaccard, p_value)` returning a boolean flag if Jaccard ≥ 0.3 or p < 0.05.
- [ ] T035 [US3] Implement `code/models/validate.py` check: if `len(samples) < 50`, skip evaluation and log a warning.
- [ ] T036 [US3] Implement `code/models/validate.py::baseline_null_model(y)` predicting mean and calculating its R²/r for comparison.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Implement `tests/benchmark/test_pipeline_timing.py` that runs the full pipeline and asserts `execution_time <= 6 hours`.
- [ ] T038 [P] Implement `code/analysis/sensitivity.py::sensitivity_rejection_threshold(thresholds=[0.08, 0.10, 0.12])` to analyze model robustness by varying the *rejection* threshold for missing values, satisfying the Assumptions section without violating the hard >10% constraint.
- [ ] T039 Refactor `code/data/ingest.py` to use a factory pattern for adapters (MockAdapter, RealAdapter, ExternalDatasetManager).
- [ ] T040 [P] Implement `tests/unit/test_edge_cases.py` with tests for: >10% missing, <50 samples, and missing individual pairing.
- [ ] T041 Update `README.md` with sections: Installation, Data Generation (Synthetic), Execution Command, and Expected Output.
- [ ] T042 Execute `quickstart.md` instructions in a fresh environment and verify success, logging any errors.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on clean data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on trained models from US2

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
Task: "Contract test for data ingestion schema in tests/contract/test_ingest_schema.py"
Task: "Integration test for preprocessing pipeline in tests/integration/test_preprocess_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement logic to filter datasets for samples with pre-stress profiles and post-stress recovery metrics ≥7 days in code/data/ingest.py"
Task: "Implement normalization of heterogeneous recovery metrics (biomass, survival) to a unified Recovery Index (0-1 scale) in code/data/preprocess.py"
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