# Tasks: Predicting Avian Migration Patterns from Publicly Available eBird Data

**Input**: Design documents from `/specs/001-predicting-avian-migration/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions
- **[Depends on: T#]**: Explicit dependency marker for parallel runners

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

- [X] T001 Create project structure by executing `mkdir -p code tests data/raw data/processed data/outputs` and creating `code/__init__.py` and `tests/__init__.py`.
- [X] T002 Create `code/requirements.txt` containing pinned versions for: pandas, xgboost, scikit-learn, scipy, shap, requests, huggingface_hub, numpy, pytest, statsmodels, psutil.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools by creating `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections, and verifying setup by running `ruff check.` and `black --check.` with exit code 0.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Setup `config.py` with explicit variables: `SEED=42`, `LAKE_POWELL_BOUNDS` (dict: lat/lon min/max for the Lake Powell region: lat 36.8-37.2, lon -111.8 to -111.4), `MODIS_SOURCES` (dict: product IDs), `THRESHOLDS=[3, 5, 10]`, `MAX_GAP_DAYS=7`, `RAM_LIMIT_GB=7`, `TIME_LIMIT_HOURS=6`. Ensure no hardcoded values in downstream code.
- [X] T005 [P] Implement robust data directory structure (`data/raw`, `data/processed`, `data/outputs`) with checksum verification logic. Write SHA-256 checksums of all raw data files to `data/raw/checksums.json` upon successful download.
- [X] T006 [P] Add a `get_logger` function to `code/__init__.py` that returns a configured logger instance, and configure logging in `code/config.py`.
- [X] T007 Create base data models/entities (`GridCellObservation`, `EnvironmentalPredictor`) in `code/data_models.py`
- [X] T008 Implement strict error handling for data loading (FAIL LOUDLY on fetch failure, no synthetic fallback) in `code/data_loader.py`. Ensure `ConnectionError` is raised if eBird or MODIS fetch fails.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline Construction and First-Arrival Derivation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw eBird and MODIS data for the **Lake Powell region**, align to a fine-resolution grid, and derive "first arrival" dates for *Setophaga ruticilla* (2015–2023) using a sensitivity sweep.

**Independent Test**: The pipeline can be executed on a subset of data to produce a CSV with grid-cell ID, week, first-arrival date, and environmental values, verifiable against manual spot-checks.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for data schema in `tests/contract/test_dataset_schema.py`: Implement `test_ebd_schema_has_required_columns()` checking for `checklist_id`, `species_code`, `latitude`, `longitude`, `date`, `duration`, `observer_count`, `distance`.
- [X] T010 [P] [US1] Integration test for end-to-end pipeline on sample data in `tests/integration/test_data_pipeline.py`: Implement `test_pipeline_produces_valid_first_arrival()` verifying output CSV schema and non-null arrival dates for valid cells.

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement EBD data loader in `code/data_loader.py`: Download specific *Setophaga ruticilla* records (2015-2023) via `datasets.load_dataset(..., streaming=True)`, filter for complete checklists (duration ≥ 1m, observers ≥ 1, distance ≤ 10km), stream to `data/raw/ebd_subset.csv` in chunks (chunksize=50000), and verify checksum. **Constraint**: Must raise `ConnectionError` if fetch fails (NO synthetic fallback).
- [ ] T012 [P] [US1] Implement MODIS data loader in `code/data_loader.py`: Retrieve MOD11A2 (Temp) and MOD13Q1 (NDVI) data for the **Lake Powell region** (using `LAKE_POWELL_BOUNDS`), resample to a high-resolution grid/weekly frequency. **Constraint**: Handle cloud gaps via **linear interpolation** with `max_gap_days=7`. If gap > 7 days, mark as missing. Crop/resample to the `LAKE_POWELL_BOUNDS` bounding box.
- [ ] T013 [US1] [Depends on: T011, T012] Implement grid aggregation logic in `code/preprocessing.py`: Aggregate eBird counts to regular spatial grid cells within the Lake Powell region and join with MODIS environmental data. Flag missing environmental data.
- [ ] T014 [US1] [Depends on: T013] Derive "first arrival" dates with sensitivity sweep in `code/preprocessing.py`: Calculate the week where the **year-to-date cumulative count** reaches thresholds {3, 5, 10}. Algorithm: `first_index = df[df['cum_count'] >= threshold].index[0]`. Exclude grid cells with total annual counts < 10. Explicitly handle grid cells with **zero observations** for a specific year by marking them as `status='undetermined'`. Write unified output to `data/processed/first_arrival_sweep.csv` with columns: `grid_id`, `week`, `arrival_date_3`, `arrival_date_5`, `arrival_date_10`, `status`. **Constraint**: Must mark cells with insufficient data as `status='undetermined'`.
- [ ] T015 [US1] [Depends on: T014] Validate the unified sensitivity sweep output in `code/preprocessing.py`: Ensure the output file `data/processed/first_arrival_sweep.csv` contains valid dates for all thresholds {3, 5, 10} and correctly marks cells with insufficient data as `status='undetermined'`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Gradient Boosting Model Training and Variable Importance Extraction (Priority: P2)

**Goal**: Train an XGBoost model using a **Temporal Split** (Train: 2015–2020, Validate: 2021, Test: 2022) on the **Lake Powell region** to predict first arrival dates and extract SHAP values.

**Independent Test**: The model achieves lower RMSE than a naive baseline on the test set (2022 data) and produces consistent SHAP/Permutation importance rankings.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Contract test for model output schema in `tests/contract/test_output_schema.py`: Implement `test_model_metrics_schema()` checking for `rmse`, `pearson_r`, `shap_values`, `feature_names`.
- [X] T018 [P] [US2] Integration test for model training and evaluation in `tests/integration/test_model_training.py`: Implement `test_temporal_split_training()` verifying that 2015-2020 data is used for training and 2022 data for testing.

### Implementation for User Story 2

- [ ] T019 [US2] [Depends on: T015] Implement feature engineering in `code/preprocessing.py`: Create lagged features (multiple weeks prior) for temperature and NDVI. Ensure strict separation of target (current week) and predictors.
- [ ] T020 [US2] [Depends on: T015] Implement **Temporal Split** logic in `code/model_training.py`: Split data into Train (–2020), Validate (2021), and Test (2022) strictly by year. **Constraint**: Use `SEED=42` for reproducibility. Do NOT use spatial splits.
- [ ] T021 [US2] Implement XGBoost training in `code/model_training.py`: Train Gradient Boosting Regressor with `tree_method='hist'` (CPU-optimized) on training set. Optimize hyperparameters using grid search over `max_depth=[3,7]`, `eta=[0.01, 0.1]` minimizing RMSE on the validation set.
- [ ] T022 [US2] Implement model evaluation in `code/model_training.py`: Calculate RMSE and Pearson correlation on the held-out **2022** test set. Compare against naive baseline (mean arrival date of the training set).
- [ ] T023 [US2] Implement SHAP analysis in `code/model_training.py`: Compute SHAP values and generate beeswarm summary plots to quantify temperature vs. NDVI contribution. Save plot to `data/outputs/shap_summary.png`.
- [ ] [ ] T024 [US2] Implement permutation importance test in `code/model_training.py`: Verify feature rankings are robust and not artifacts of collinearity. Save results to `data/outputs/permutation_importance.csv`.
- [ ] T025 [US2] Implement regional mapping logic in `code/visualization.py`: Prepare data for regional visualization of predicted arrival dates within the **Lake Powell region**.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Perform **Diebold-Mariano test** to statistically compare model performance across predictor sets and validate the robustness of the "first arrival" threshold.

**Independent Test**: The analysis produces p-values for the DM test and a table showing arrival date stability across thresholds {3, 5, 10}.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test for metrics output in `tests/contract/test_metrics_schema.py`: Implement `test_dm_metrics_schema()` checking for `p_value`, `dm_statistic`, `model_type`.
- [X] T027 [P] [US3] Integration test for statistical validation in `tests/integration/test_statistical_validation.py`: Implement `test_dm_significance()` verifying that DM test returns valid p-values for predictor set comparisons.

### Implementation for User Story 3

- [ ] T028 [US3] [Depends on: T022] Implement **Diebold-Mariano test** logic in `code/model_training.py`: Calculate prediction errors for Temperature-only, NDVI-only, and Combined models on the test set. Use `statsmodels` or custom implementation to perform the Diebold-Mariano test comparing the error series.
- [ ] T029 [US3] [Depends on: T028] Implement statistical comparison in `code/model_training.py`: Calculate **p-values** (using Diebold-Mariano test) for the difference in forecast accuracy between predictor sets at **alpha=0.05**. Append results to `data/processed/metrics.json` with keys: `dm_p_value_combined_vs_temp`, `dm_p_value_combined_vs_ndvi`. **Constraint**: Must satisfy US-3 acceptance criteria for statistical significance.
- [ ] T030 [US3] [Depends on: T015] Implement threshold sensitivity analysis in `code/model_training.py`: Read from `data/processed/first_arrival_sweep.csv`. Analyze variation in first-arrival dates across {3, 5, 10}. Flag findings if **mean absolute difference > 7 days**. Output `status` column in CSV: 'stable' or 'sensitive'.
- [ ] T031 [US3] [Depends on: T029, T030] Implement final metrics aggregation in `code/model_training.py`: Write all RMSE, Correlation, DM p-values (from T029), and stability flags (from T030) to `data/processed/metrics.json`. **Constraint**: Must run strictly after T029 and T030 complete.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Visualization & Validation (Priority: P4)

**Goal**: Generate continental-scale maps and validate performance constraints.

- [ ] T032 [US3] [Depends on: T022, T025] Implement **continental-scale map generation** in `code/visualization.py`: Visualize predicted arrival dates and spatial gradient of the strongest predictor for the **full North American extent**. **Constraint**: Must cover the continental US/North America as per Spec FR-007. If data is only available for Lake Powell, the map must explicitly show the region of data availability within the continental context (e.g., using a base map of North America with data overlaid only for Lake Powell), but the artifact must be a continental-scale visualization.
- [ ] T033 [P] Documentation updates: Update `README.md` with installation steps and add docstrings to all functions in `code/`.
- [ ] T034 Code cleanup: Remove unused imports and ensure PEP8 compliance via ruff.
- [ ] T035 [P] Performance profiling: Run `time ./run_pipeline.sh` and capture RAM usage. **Explicitly use `psutil` (or parse `free -m` output)** to detect peak RAM usage. Write top 3 bottlenecks to `data/outputs/profile_report.txt`. Parse `free -m` output to extract peak RSS.
- [ ] T036 [P] Performance refactoring: If T035 reports peak RAM > **7 GB**, refactor `code/data_loader.py` to use `pandas.read_csv(chunksize=10000)` or `streaming=True` logic.
- [ ] T037 [P] Additional unit tests in `tests/unit/`: Create `tests/unit/test_dm.py` (testing T028 logic) and `tests/unit/test_regional_map.py` (testing T032 logic).
- [ ] T038 [P] Runtime validation: Execute the full pipeline (`python code/main.py --validate`) wrapped in a `time` command. Parse the output to extract total seconds, write `data/outputs/runtime_validation.json` with keys `total_seconds` and `passed` (true if < **21600s** (6 hours)).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Visualization & Validation (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on US1 data output** (aggregated grid). T019/T020 cannot run until T013/T014/T015 complete.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output and US1 sensitivity data (T015)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data loading before feature engineering
- Feature engineering before model training
- Model training before evaluation/visualization
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately.
- US2 (T019-T025) **cannot** start until US1 data is generated (T013/T014/T015 complete).
- US3 (T028-T031) **cannot** start until US2 is complete.
- All tests for a user story marked [P] can run in parallel.
- T032, T033, T034, T036, T037, T038 can run in parallel after all US tasks complete.
- T031 **cannot** run in parallel with T029/T030; it must follow them sequentially.

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
 - Developer A: User Story 1 (Data Pipeline)
 - Developer B: User Story 2 (Modeling) - *Must wait for US1 data output*
 - Developer C: User Story 3 (Validation) - *Must wait for US2 output*
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
- **Data Integrity**: All data loaders MUST fail loudly on fetch errors. NO synthetic data fallbacks allowed.
- **Compute Constraints**: All models must run on CPU (XGBoost `tree_method='hist'`). Full dataset must be streamed or sampled to fit < 7GB RAM.
- **Scope Constraint**: All tasks must target the **Lake Powell region** as per Plan.md and verified data constraints, EXCEPT T032 which must generate continental-scale maps per Spec FR-007.
- **Methodology Constraint**: Statistical validation MUST use **Diebold-Mariano test** (T028-T029), not LMM, as mandated by the Spec.
- **Temporal Split**: Model training MUST use a **Temporal Split** (2015-2020/21/22) as per FR-004 and Constitution Principle VII.
- **Sensitivity Sweep**: The sensitivity sweep MUST be integrated into the first-arrival derivation logic (T014) to produce a unified output for all thresholds {3, 5, 10} as required by FR-003.
- **Statistical Significance**: DM test MUST calculate p-values for the difference in forecast accuracy between predictor sets to satisfy US-3 acceptance criteria.
- **Memory Profiling**: T035 MUST include a specific mechanism for detecting peak RAM usage (`psutil` or `free -m`) before deciding on chunked reading implementation.
- **Explicit Dependencies**: T030 MUST explicitly reference the input file path `data/processed/first_arrival_sweep.csv` generated by T015.
- **Thresholds**: T030 must use **7 days** threshold; T036 must use **7 GB** threshold; T038 must use **6 hours** limit.