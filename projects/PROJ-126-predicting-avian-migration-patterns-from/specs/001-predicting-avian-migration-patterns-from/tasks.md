# Tasks: Predicting Avian Migration Patterns from Publicly Available eBird Data

**Input**: Design documents from `/specs/001-predicting-avian-migration/`
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

- [ ] T001 Create project structure by executing `mkdir -p code tests data/raw data/processed data/outputs` and creating `code/__init__.py` and `tests/__init__.py`.
- [ ] T002 Create `code/requirements.txt` containing pinned versions for: pandas, xgboost, scikit-learn, scipy, shap, requests, huggingface_hub, numpy, pytest.
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup `config.py` for paths, random seed (42), and hyperparameters
- [ ] T005 [P] Implement robust data directory structure (`data/raw`, `data/processed`, `data/outputs`) with checksum verification logic
- [ ] T006 [P] Add a `get_logger` function to `code/__init__.py` that returns a configured logger instance, and configure logging in `code/config.py`.
- [ ] T007 Create base data models/entities (`GridCellObservation`, `EnvironmentalPredictor`) in `code/data_models.py`
- [ ] T008 Implement strict error handling for data loading (FAIL LOUDLY on fetch failure, no synthetic fallback) in `code/data_loader.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline Construction and First-Arrival Derivation (Priority: P1) 🎯 MVP

**Goal**: Ingest raw eBird and MODIS data, align to 0.5° grid, and derive "first arrival" dates for *Setophaga ruticilla* (2015–2023) across North America.

**Independent Test**: The pipeline can be executed on a subset (single year/region) to produce a CSV with grid-cell ID, week, first-arrival date, and environmental values, verifiable against manual spot-checks.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for data schema in `tests/contract/test_dataset_schema.py`
- [ ] T010 [P] [US1] Integration test for end-to-end pipeline on sample data in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement EBD data loader in `code/data_loader.py`: Download specific *Setophaga ruticilla* records (2015-2023) via `datasets.load_dataset` or verified URL, filter for complete checklists (duration ≥ 1m, observers ≥ 1, distance ≤ 10km), stream to `data/raw/ebd_subset.csv`, and verify checksum. **Constraint**: Must raise `ConnectionError` if fetch fails (NO synthetic fallback).
- [ ] T012 [P] [US1] Implement MODIS data loader in `code/data_loader.py`: Retrieve and resample MOD11A2 (Temp) and MOD13Q1 (NDVI) to 0.5° grid/weekly frequency for North America. Handle cloud gaps via temporal interpolation.
- [ ] T013 [US1] Implement grid aggregation logic in `code/preprocessing.py`: Aggregate eBird counts to regular spatial grid cells and join with MODIS environmental data. Flag missing environmental data.
- [ ] T014 [US1] Implement "first arrival" derivation in `code/preprocessing.py`: Calculate the week where the cumulative count reaches a specified threshold observation. Exclude grid cells with total annual counts < 10. Write output to `data/processed/first_arrival.csv` with columns: `grid_id`, `week`, `arrival_date`, `status`.
- [ ] T015 [US1] Implement sensitivity sweep logic in `code/preprocessing.py`: Pre-filter input data to exclude cells with total annual counts < 10. Then generate "first arrival" dates for thresholds of varying observation counts (3, 5, 10) and store in `data/processed/first_arrival_sweep.csv`.
- [ ] T016 [US1] Add validation to ensure no "false positive" arrival dates are generated for cells with insufficient data (mark as "undetermined").

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Gradient Boosting Model Training and Variable Importance Extraction (Priority: P2)

**Goal**: Train an XGBoost model using a **Spatial Split** (Train: Eastern US, Test: Western US) to predict first arrival dates and extract SHAP values.

**Independent Test**: The model achieves lower RMSE than a naive baseline on the test set (Western US 2022) and produces consistent SHAP/Permutation importance rankings.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Contract test for model output schema in `tests/contract/test_output_schema.py`
- [ ] T018 [P] [US2] Integration test for model training and evaluation in `tests/integration/test_model_training.py`

### Implementation for User Story 2

- [ ] T019 [P] [US2] Implement feature engineering in `code/preprocessing.py`: Create lagged features (1–4 weeks prior) for temperature and NDVI. Ensure strict separation of target (current week) and predictors.
- [ ] T020 [P] [US2] Implement spatial data splitting logic in `code/model_training.py`: Split data into Train (Eastern US: longitude < -100), Validate (Eastern US, recent historical period), and Test (Western US: longitude >= -100, 2022) strictly by geography and year.
- [ ] T021 [US2] Implement XGBoost training in `code/model_training.py`: Train Gradient Boosting Regressor with `tree_method='hist'` (CPU-optimized) on training set. Optimize hyperparameters using grid search over `max_depth=[5,7]`, `eta=[0.01, 0.1]` minimizing RMSE on the validation set.
- [ ] T022 [US2] Implement model evaluation in `code/model_training.py`: Calculate RMSE and Pearson correlation on the held-out Western US test set. Compare against naive baseline (mean arrival date).
- [ ] T023 [US2] Implement SHAP analysis in `code/model_training.py`: Compute SHAP values and generate beeswarm summary plots to quantify temperature vs. NDVI contribution. Save plot to `data/outputs/shap_summary.png`.
- [ ] T024 [US2] Implement permutation importance test in `code/model_training.py`: Verify feature rankings are robust and not artifacts of collinearity.
- [ ] T025 [US2] Implement continental-scale map generation in `code/visualization.py`: Visualize predicted arrival dates and spatial gradient of the strongest predictor for the entire North American domain.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation and Sensitivity Analysis (Priority: P3)

**Goal**: Perform Linear Mixed-Effects Modeling (LMM) to statistically compare model performance across predictor sets and validate the robustness of the "first arrival" threshold.

**Independent Test**: The analysis produces p-values for predictor set comparisons and a table showing arrival date stability across thresholds {3, 5, 10}.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Contract test for metrics output in `tests/contract/test_metrics_schema.py`
- [ ] T027 [P] [US3] Integration test for statistical validation in `tests/integration/test_statistical_validation.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement Linear Mixed-Effects Model (LMM) in `code/model_training.py`: Fit LMM with Grid Cell as a random effect to compare RMSE/Correlation across predictor sets (Temperature-only, NDVI-only, Combined).
- [ ] T029 [US3] Implement statistical comparison in `code/model_training.py`: Calculate p-values for the comparison of predictor sets using the LMM results. Append results to `data/processed/metrics.json` with keys: `p_temp_vs_ndvi`, `p_combined_vs_temp`.
- [ ] T030 [US3] Implement threshold sensitivity analysis in `code/model_training.py`: Analyze variation in first-arrival dates across the {3, 5, 10} sweep. Flag findings if variation exceeds tolerance.
- [ ] T031 [US3] Implement final metrics aggregation in `code/model_training.py`: Write all RMSE, Correlation, p-values (from T029), and stability flags to `data/processed/metrics.json`. Ensure T031 reads from outputs generated by T028/T029.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates: Update `README.md` with installation steps and add docstrings to all functions in `code/`.
- [ ] T033 Code cleanup: Remove unused imports and ensure PEP8 compliance via ruff.
- [ ] T034 Performance optimization: Run cProfile on `data_loader.py`, identify top bottlenecks, and implement chunked reading strategy if RAM usage > 5GB or runtime > 4 hours.
- [ ] T035 [P] Additional unit tests in `tests/unit/`
- [ ] T036 Run `quickstart.md` validation to ensure reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (aggregated grid)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output and US1 sensitivity data

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data loading before feature engineering
- Feature engineering before model training
- Model training before evaluation/visualization
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
Task: "Contract test for data schema in tests/contract/test_dataset_schema.py"
Task: "Integration test for end-to-end pipeline on sample data in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement EBD data loader in code/data_loader.py"
Task: "Implement MODIS data loader in code/data_loader.py"
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
   - Developer A: User Story 1 (Data Pipeline)
   - Developer B: User Story 2 (Modeling) - *Requires US1 data output, so must wait or use mock schema*
   - Developer C: User Story 3 (Validation) - *Requires US2 output*
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
- **Plan Discrepancy Note**: The `plan.md` currently describes a temporal split and Lake Powell scope. The tasks above (T020, T025) explicitly override this to match the `spec.md` requirements (Spatial Split, Continental Scale). The plan.md must be updated to reflect this alignment.
