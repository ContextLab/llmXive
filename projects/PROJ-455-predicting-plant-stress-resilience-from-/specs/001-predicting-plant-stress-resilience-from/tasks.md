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

- [X] T001 Create project structure per implementation plan in `projects/PROJ-455-predicting-plant-stress-resilience-from-/` by executing `mkdir -p projects/PROJ-455-predicting-plant-stress-resilience-from-/code/data projects/PROJ-455-predicting-plant-stress-resilience-from-/code/models projects/PROJ-455-predicting-plant-stress-resilience-from-/code/analysis projects/PROJ-455-predicting-plant-stress-resilience-from-/tests/unit projects/PROJ-455-predicting-plant-stress-resilience-from-/tests/integration projects/PROJ-455-predicting-plant-stress-resilience-from-/tests/contract projects/PROJ-455-predicting-plant-stress-resilience-from-/tests/benchmark projects/PROJ-455-predicting-plant-stress-resilience-from-/contracts projects/PROJ-455-predicting-plant-stress-resilience-from-/data/raw projects/PROJ-455-predicting-plant-stress-resilience-from-/data/processed projects/PROJ-455-predicting-plant-stress-resilience-from-/data/results projects/PROJ-455-predicting-plant-stress-resilience-from-/state/projects`.
- [X] T002 Initialize Python 3.11 project with dependencies (`pandas==2.0.3`, `scikit-learn==1.3.0`, `numpy==1.24.0`, `requests==2.31.0`, `biopython==1.81`, `pyyaml==6.0.1`, `pytest==7.4.0`) in `requirements.txt`.
- [X] T003 [P] Configure linting (flake8/black) by creating `.flake8` and `pyproject.toml` with black settings.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004.1 [P] Create `contracts/dataset.schema.yaml` defining JSON/YAML schema for `MetabolomicProfile`.
- [X] T004.2 [P] Create `contracts/model_result.schema.yaml` defining the FULL JSON/YAML schema for `ModelResult` including fields: `model_type`, `metric_name`, `metric_value`, `feature_importance` (list), `p_value` (nullable), `validation_method`, and `seed_used`. **This task must contain the complete schema definition to unblock T022.**
- [ ] T004.3 [P] Create `contracts/recovery.schema.yaml` defining JSON/YAML schema for `RecoveryMetric`.
- [X] T005 [P] Implement base data models (`MetabolomicProfile`, `RecoveryMetric`, `RecoveryIndex`) with validation rules in `code/data/models.py` using Pydantic.
- [X] T006 [P] Setup logging and error handling infrastructure in `code/utils/logging.py` by implementing a `get_logger` function that configures a standard JSON formatter and file/console handlers.
- [X] T007 [P] Implement the Mechanism-Guided Synthetic Generator in `code/data/generator.py` by implementing `generate_synthetic_data(n_samples, stress_type, missing_rate=0.05, seed=42)` that outputs a Parquet file to `data/raw/synthetic_[stress_type]_[seed].parquet`. **CRITICAL**: The `missing_rate` parameter MUST be exposed and used to allow generation of datasets with >10% missing values (e.g., `missing_rate=0.15`) specifically to trigger the rejection logic in T015. The generator MUST embed ground-truth pathways (proline, ABA, glutathione) and explicit columns: `sample_id`, `stress_type`, `metabolite_name`, `concentration`, `recovery_metric`, `recovery_index`, `stress_vector_seed`. **Test Case**: Include a specific test case in the task description to verify that `missing_rate=0.15` results in a file that T015 rejects.
- [X] T007.1 [P] Implement checksum verification in `code/data/generator.py` by creating `verify_checksum(file_path)` that computes SHA256 and records it in `state/projects/PROJ-455-predicting-plant-stress-resilience-from-.yaml` under the `artifact_hashes` map per Constitution Principle III. **The YAML key path MUST be `state.projects['PROJ-455-predicting-plant-stress-resilience-from-'].artifact_hashes[file_path]`.**
- [X] T009.1 [P] Implement ExternalDatasetManager in `code/data/ingest.py` by creating `ExternalDatasetManager` class that handles fetching, parsing, and validation of external datasets.
 - [X] T009.1.1 [P] Implement `fetch(accession_id, source)` AND `search_keywords(keywords, source)` in `code/data/ingest.py` to download raw files from NCBI GEO/Zenodo using E-utilities or Zenodo API, with retry logic and checksumming. **For the current project state, this MUST implement the MockAdapter logic to fetch synthetic data from `data/raw/` as the verified source, raising `DataRejectionError` if the data is not found or invalid.**
 - [X] T009.1.2 [P] Implement `parse(raw_file, source)` in `code/data/ingest.py` to parse NCBI GEO XML/JSON or Zenodo CSV, mapping specific fields (e.g., `GSM`, `GPL`, `metabolite_concentration`) to DataFrame columns, and raising `DataRejectionError` for malformed data. **For the current project state, this MUST parse the synthetic Parquet format generated by T007, mapping columns to the `MetabolomicProfile` schema.**
 - [X] T009.1.3 [P] Implement `ingest_multiple(dataset_ids)` in `code/data/ingest.py` to fetch and validate multiple distinct datasets for LODO validation (FR-010). **Note**: This task handles *fetching* only; splitting logic is in T009.2.
- [X] T009.2 [P] Implement LODO Data Prep in `code/data/ingest.py` by creating `prepare_lodo_datasets()` function that organizes external datasets into train/test splits for Leave-One-Dataset-Out validation. **For the current project state, this MUST organize the synthetic datasets generated by T009.3 into N-1 train sets and 1 held-out test set, ensuring distinct `stress_vector_seed` values.**
- [X] T009.3 [P] Implement Synthetic Multi-Dataset Generator in `code/data/generator.py` by creating `generate_lodo_synthetic_datasets(n_datasets, stress_types)` that produces multiple distinct Parquet files with varying **biological stress vectors** (e.g., distinct metabolite response patterns for drought vs. salinity) and species to simulate independent external datasets for LODO validation (FR-010). Each dataset MUST have a unique `stress_vector_seed` to ensure independence.
- [X] T009.3.1 [P] Implement validation logic in `code/data/generator.py` or `code/data/ingest.py` to verify that synthetic datasets generated by T009.3 have **distinct `stress_vector_seed` values** before they are consumed by T030. This task explicitly enforces the independence requirement for LODO. **The function must return a boolean and raise an error if duplicates are found.**
- [X] T009.4 [P] Implement CLI entry point in `code/main.py` (or `code/cli.py`) that accepts user-provided accession IDs or keywords as arguments, parses them, and invokes `T009.1.1` and `T009.1.2` methods. This task satisfies FR-001's requirement for a user-facing interface.
- [X] T019.0 [P] Generate `data/raw/kegg_mapping.tsv` by implementing `code/analysis/pathway.py::generate_kegg_mapping()` which fetches mapping data from the exact KEGG API endpoint `https://rest.kegg.jp/link/compound/ko00001` OR falls back to a bundled static CSV at `data/raw/kegg_mapping_fallback.csv` if the API fails. The fallback file path MUST be deterministic and hardcoded.
- [X] T019.2 [P] Implement `code/analysis/pathway.py::map_to_kegg(df)` function that maps raw metabolite names to KEGG Compound IDs using the generated file `data/raw/kegg_mapping.tsv` (produced by T019.0) and persists the IDs as a new column in the processed DataFrame. This task MUST be completed before any model training tasks.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw plant metabolomic datasets (synthetic or real), filter for relevant stress conditions, and normalize data for analysis.

**Independent Test**: Run the data pipeline script against the synthetic generator output and verify the output is a normalized CSV/Parquet file with no missing critical columns, correct row counts, and applied transformations (ln, half-min, TIC).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Contract test for data ingestion schema in `tests/contract/test_ingest_schema.py`.
- [X] T011 [P] [US1] Integration test for preprocessing pipeline in `tests/integration/test_preprocess_pipeline.py`.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/data/ingest.py::RealAdapter::fetch` to parse NCBI GEO/Zenodo XML/JSON responses into a `MetabolomicProfile` DataFrame, ensuring it uses the infrastructure from T009.1.1. **Depends on T009.1.1 completion**.
- [X] T013 [US1] Implement `code/data/ingest.py::filter_by_recovery_time(df, min_days=7)` function that returns a filtered DataFrame.
- [X] T014 [US1] Implement `code/data/preprocess.py::normalize_recovery(df)` function that maps biomass/survival columns to a `RecoveryIndex` (normalized scale) column.
- [X] T015 [US1] Implement `code/data/preprocess.py::check_missing_threshold(df, threshold=0.1)` that raises a `DataRejectionError` if missing >10%.
- [X] T015.1 [US1] Implement orchestration in `code/data/preprocess.py` or `code/main.py` to explicitly call `generate_synthetic_data` with `missing_rate=0.15` and assert that `check_missing_threshold` raises `DataRejectionError`. This task ensures the rejection path is exercised in the main flow.
- [X] T016 [US1] Implement `code/data/preprocess.py::impute_half_min(df)` function that replaces NaN with half the column minimum.
- [X] T017 [US1] Implement `code/data/preprocess.py::normalize_tic_and_log(df)` function that applies TIC normalization and **natural log (ln)** transformation (using `np.log` with zero-handling logic) as required by FR-003. **Depends on T007** (data availability).
- [X] T018 [US1] Implement `code/data/preprocess.py::aggregate_population(df)` function that computes mean pre-stress and mean recovery per group if individual pairing is missing.
- [X] T019 [US1] Add validation and error handling for dataset rejection scenarios in `code/data/ingest.py` to catch `DataRejectionError` and log specific rejection reasons (e.g., 'Missing >10%') to `code/utils/logging.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Predictive Model Training and Feature Importance (Priority: P2)

**Goal**: Train Random Forest and SVM models to predict recovery rates from pre-stress metabolomic profiles and identify the most predictive metabolites.

**Independent Test**: Train models on a split dataset, evaluate performance metrics (R² or Pearson correlation), and verify that feature importance rankings are generated for the top 20 metabolites.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for model output schema in `tests/contract/test_model_result_schema.py`.
- [X] T021 [P] [US2] Unit test for feature importance extraction in `tests/unit/test_feature_importance.py`.

### Implementation for User Story 2

- [X] T022 [US2] Implement `code/models/train.py::train_random_forest(X, y, cv=5, seed=42)` returning a fitted model and `model_result.schema.yaml` compliant metrics. **Depends on T004.2 (schema definition)**. **The `seed` parameter MUST be used to set `numpy.random.seed(seed)` and `random_state=seed` in the model.**
- [X] T023 [US2] Implement `code/models/train.py::train_svm(X, y, cv=5, seed=42)` returning a fitted model and metrics. **The `seed` parameter MUST be used for reproducibility.**
- [X] T024.1 [US2] Implement `code/models/train.py::calculate_metric(y_true, y_pred, mode)` that returns R² for individual mode and Pearson r for population mode, satisfying FR-011. **The `mode` parameter must be 'individual' or 'population' to switch metrics.**
- [X] T025 [US2] Implement `code/models/train.py::get_top_features(model, n=20)` returning a list of (feature_name, importance) tuples.
- [X] T027 [US2] Add logging for model training metrics in `code/models/train.py` to record R²/r, top 5 features, and training time to the configured logger.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Cross-Stress Generalizability and Statistical Validation (Priority: P3)

**Goal**: Evaluate model generalizability across stress types, perform permutation testing, and validate biological plausibility against known pathways.

**Independent Test**: Run cross-stress evaluation and permutation test (n=1000), verify p-values are calculated, generalizability scores reported, and pathway enrichment checks pass.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Contract test for validation results schema in `tests/contract/test_validation_schema.py`.
- [X] T029 [P] [US3] Integration test for cross-stress evaluation in `tests/integration/test_cross_stress_eval.py`.

### Implementation for User Story 3

- [X] T030 [US3] Implement `code/models/validate.py::lodo_cv(models, datasets)` that executes the Leave-One-Dataset-Out loop (train on N-1, test on held-out) using the synthetic or external datasets. **Verification**: This task MUST explicitly verify that the input datasets have distinct `stress_vector_seed` metadata (ensured by T009.3.1) to satisfy FR-010.
- [X] T031 [US3] Implement `code/models/validate.py::cross_stress_eval(model, train_stress, test_stress)` calculating R²_drop or r_drop.
- [X] T032 [US3] Implement `code/models/validate.py::permutation_test(model, X, y, n=1000)` returning a p-value.
- [X] T033 [US3] Implement `code/analysis/pathway.py::enrichment_analysis(kegg_ids, pathways)` calculating Jaccard similarity and Enrichment p-value.
- [X] T034 [US3] Implement `code/analysis/pathway.py::validate_alignment(jaccard, p_value)` returning a boolean flag if Jaccard ≥ 0.3 or p < 0.05.
- [X] T035 [US3] Implement `code/models/validate.py` check: if `len(samples) < 50`, skip evaluation and log a warning.
- [X] T036 [US3] Implement `code/models/validate.py::baseline_null_model(y)` predicting mean and calculating its R²/r for comparison.
- [X] T026 [US3] Consume persisted KEGG mapping from `data/processed/mapped_data.parquet` (generated by T019.2) in `code/analysis/pathway.py` for downstream validation. **Depends on T019.2**. **This task must load the mapped data and pass it to T033 for enrichment analysis.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Implement `tests/benchmark/test_pipeline_timing.py` that runs the full pipeline and asserts `execution_time <= 6 hours`.
- [X] T038 [P] Implement `code/analysis/sensitivity.py::sensitivity_rejection_threshold(thresholds=[0.05, 0.08])` to analyze model robustness by varying the input to the rejection logic (strictly <10%), ensuring all tested thresholds are valid processing parameters. **Success Condition**: Record R² variance across thresholds and assert stability (variance < 0.05).
- [X] T039 Refactor `code/data/ingest.py` to use a factory pattern for adapters (MockAdapter, RealAdapter, ExternalDatasetManager).
- [X] T040 [P] Implement `tests/unit/test_edge_cases.py` with tests for: >10% missing, <50 samples, and missing individual pairing.
- [X] T040.1 [P] Generate `quickstart.md` in the project root by documenting the installation, data generation (synthetic), execution command, and expected output sections, ensuring it matches the requirements of T042. **Depends on T046** (Orchestration). **Must include sections: Installation, Data Generation (Synthetic), Execution Command, Expected Output.**
- [X] T041 Update `README.md` with sections: Installation, Data Generation (Synthetic), Execution Command, and Expected Output. **Must include explicit instructions for installing dependencies, generating synthetic data, running the pipeline, and interpreting the output.**
- [X] T042 Execute `quickstart.md` (generated by T040.1) instructions in a fresh environment and verify success by checking: (1) exit code 0, (2) existence of `data/results/model_metrics.json`, and (3) log containing "Pipeline completed successfully". **Depends on T046**.
- [X] T046 [Polish] Implement `code/main.py` as the orchestration entry point that: (1) calls the synthetic generator, (2) runs preprocessing, (3) trains models, (4) runs validation, (5) writes `data/results/model_metrics.json`, ensuring the pipeline can be invoked via `python code/main.py` for T042.
- [X] T047 [Polish] Add a `--seed` argument to `code/main.py` and `code/data/generator.py` to ensure reproducibility of the synthetic data generation and subsequent model training, satisfying Constitution Principle I. **Moved to Phase N.**
- [X] T047.1 [Polish] Implement verification logic in `code/main.py` or `code/utils/reproducibility.py` to explicitly audit that the `--seed` argument is correctly propagated to `generate_synthetic_data`, `train_random_forest`, and `train_svm` functions, ensuring all random states are pinned. This task explicitly verifies the mechanism required by Constitution Principle I.

---

## Revision Tasks: Addressing Unspecified/Failed Concerns

**Purpose**: Resolve gaps identified in the previous analysis (T007, T009.1, T019.2, T042) to ensure full pipeline execution.

- [X] T043 [US1] Implement `code/data/ingest.py::MockAdapter` class that wraps the synthetic generator (T007) to provide a consistent `fetch` interface, ensuring it raises `DataRejectionError` if the generated data violates the <10% missing threshold (simulating a real data failure).
- [X] T044 [US1] Implement `code/data/ingest.py::RealAdapter` stub that raises `NotImplementedError` with a clear message directing users to the synthetic generator for current testing, preventing accidental execution of unverified real-data fetch logic.
- [X] T045 [US3] Implement `code/analysis/pathway.py::load_kegg_mapping()` to robustly read `data/raw/kegg_mapping.tsv`, handling missing files by raising a clear error instead of silently failing, ensuring T019.0 is a hard dependency.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision Tasks**: Must be completed before T042 (Quickstart Execution) can succeed.

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
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
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

### Revision Strategy

1. **Priority 1**: Complete T043, T044, T045, T046, T047, T047.1 to resolve the "unspecified" failures in T042.
2. **Priority 2**: Re-run T042 (Quickstart Execution) to verify the full pipeline end-to-end.
3. **Priority 3**: Verify T007.1 (Checksums) and T009.3 (LODO Synthetic Data) are correctly integrated.
4. **Priority 4**: Re-run T037 (Benchmark) to ensure no performance regressions from the new orchestration logic.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: T007 (Valid Data), T015.1 (Rejection Orchestration), T019.0 (KEGG Mapping with fallback), and T040.1 (Quickstart) ensure compliance with FR-003, FR-012, and Constitution Principle III.
- **Revision Note**: Tasks T043-T047.1 are mandatory to unblock T042 and ensure the pipeline runs as a cohesive unit. T040.1 has been moved to Phase N to resolve phase ordering. T026 has been moved to Phase 5. T007.2 has been merged into T007.