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

- [X] T001a [P] Create root project structure: `projects/PROJ-510-predicting-the-glass-forming-region-of-a/`, `data/`, `code/`, `tests/`, `docs/`. **Files to create**: `README.md` (empty), `.gitignore` (standard python). **Verify**: Run `ls -R projects/PROJ-510-predicting-the-glass-forming-region-of-a/` to confirm all directories and files exist relative to the repository root.
- [ ] T001b [P] Create source code structure: `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/__init__.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/utils.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/features.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/requirements.txt`
- [X] T001c [P] Create test structure: `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/__init__.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_features.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_ingestion.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_train.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_analyze.py`
- [X] T002 Initialize Python 3.11 project with dependencies: `pandas`, `scikit-learn`, `numpy`, `requests`, `pyyaml`, `datasets`, `mendeleev`, `scipy`, `pydantic` in `requirements.txt`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools. **Files to create**: `.flake8` (max-line-length=120), `pyproject.toml` (black config). **Verify**: Run `flake8 --version` and `black --version` to confirm installation and config loading.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/raw/` and `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/` directory structure with `.gitignore` rules. **Content**: `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/.gitignore` must contain `*.csv`, `*.pkl`, `*.json`, `!README.md`. **Verify**: Run `mkdir -p projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/raw projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed` and `cat projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/.gitignore` to confirm content.
- [X] T005 [P] [US1] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/utils.py` with periodic table lookup helpers using `mendeleev` and logging infrastructure.
- [X] T006 [P] [US1] Create `projects/PROJ-510-predicting-the-glass-forming-region-of-a/contracts/dataset.schema.yaml` defining `AlloyRecord` fields. **Content**:
 ```yaml
 AlloyRecord:
 type: object
 properties:
 composition: {type: string}
 critical_cooling_rate: {type: number}
 mixing_enthalpy: {type: number}
 atomic_size_mismatch: {type: number}
 electronegativity_variance: {type: number}
 source_label: {type: string}
 required: [composition, critical_cooling_rate, mixing_enthalpy, atomic_size_mismatch, electronegativity_variance]
 ```
 **Verify**: Run `pydantic` validation on a sample row against this schema.
- [X] T007 [P] [US2, US3] Create `projects/PROJ-510-predicting-the-glass-forming-region-of-a/contracts/model_output.schema.yaml` defining `ModelMetrics` and `SensitivityReport` structures. **Content**:
 ```yaml
 ModelMetrics:
 type: object
 properties:
 fold_scores: {type: array, items: {type: number}}
 mean_rmse: {type: number}
 test_rmse: {type: number}
 feature_importance_ranking: {type: array, items: {type: string}}
 p_value_vs_null: {type: number}
 required: [fold_scores, mean_rmse, test_rmse]
 SensitivityReport:
 type: object
 properties:
 threshold_values: {type: array, items: {type: number}}
 rmse_variance: {type: number}
 collinearity_flags: {type: array, items: {type: string}}
 required: [threshold_values, rmse_variance]
 ```
 **Verify**: Run `pydantic` validation on sample outputs.
- [X] T008 [P] [US1] Configure error handling: Ensure data loading fails loudly (no synthetic fallback) if `matsci/glass-forming-ability` fetch fails. **Implementation**: Add `raise ValueError("Data fetch failed: matsci/glass-forming-ability unavailable")` in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py` line 45. **Verify**: Run `pytest` with a mock that simulates fetch failure to ensure the error is raised.
- [X] T009 Setup `pytest` configuration and seed management (`random_state=42`) in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/utils.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Thermodynamic Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Download experimental data, filter for valid ternary alloys, and compute thermodynamic descriptors.

**Independent Test**: The pipeline can be run in isolation to produce a CSV file containing at least 500 valid alloy records with all required thermodynamic columns and the `critical_cooling_rate` column computed, without training any model.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: T010 and T011 are written but currently FAIL until T012-T017 are implemented.

- [X] T010 [US1] Write unit test for thermodynamic formula calculation (mixing enthalpy, atomic size mismatch) in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_features.py`. **Status**: Written, currently fails.
- [X] T011 [US1] Write integration test for data ingestion pipeline ensuring ≥500 rows and no NaN in target columns in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_ingestion.py`. **Status**: Written, currently fails.

### Implementation for User Story 1

- [X] T012 [US1] Implement `projects/PROJ-Predicting-the-glass-forming-region-of-a/code/ingestion.py`: Download `matsci/glass-forming-ability` dataset using `datasets.load_dataset`. **Reconciliation**: This dataset is the verified source for CCR (Plan), while Mendeleev provides elemental properties (Constitution Principle VI). **Action**: Use `load_dataset("matsci/glass-forming-ability")` and verify `critical_cooling_rate` column exists and is of type `float64`. Raise `ValueError` if missing.
- [X] T013 [US1] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py`: Filter dataset for ternary alloys (3 elements) and exclude rows with missing elemental data or unknown glass-forming labels. Log exclusion counts.
- [X] T014 [P] [US1] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/features.py`: Calculate `mixing_enthalpy` using `mendeleev` elemental properties and ternary composition weights.
- [X] T015 [P] [US1] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/features.py`: Calculate `atomic_size_mismatch` and `electronegativity_variance` using standard periodic table definitions.
- [ ] T016a [US1] [Depends on T015] Save processed data to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/processed_alloys.csv`. **Verification**: Ensure file exists and is non-empty.
- [ ] T016b [US1] [Depends on T016a] Run `tests/test_features.py` to assert tolerance (1e-6) on computed features. **Verification**: Ensure all tests pass.
- [X] T017 [US1] Add validation to ensure `critical_cooling_rate` has non-zero variance and ≥500 entries. **Implementation**: In `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py`, after filtering, check `df['critical_cooling_rate'].var() > 0` and `len(df) >= 500`. **Error**: `raise ValueError("Data availability error: <500 valid entries or zero variance in critical_cooling_rate")`. **Verify**: Run pipeline with a truncated dataset to confirm error.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train a Random Forest regressor with k-fold cross-validation and evaluate performance.

**Independent Test**: The training script can be executed on the generated dataset to produce a trained model file and a metrics report containing the cross-validation score, without requiring any external GPU or internet access after the data is loaded.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for 5-fold cross-validation split generation ensuring non-overlapping folds in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_train.py`
- [ ] T019 [P] [US2] Integration test for model training producing valid `ModelMetrics` schema in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_train.py`

### Implementation for User Story 2

- [ ] T020 [US2] [Depends on T016] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py`: Load `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/processed_alloys.csv`, perform 80/20 train-test split with `random_state=42`.
- [ ] T021 [US2] [Depends on T020] Implement `projects/PROJ-predicting-the-glass-forming-region-of-a/code/train.py`: Train `RandomForestRegressor` and perform 5-fold cross-validation. **Action**: Aggregate fold scores, calculate mean RMSE and fold variance. Save `fold_scores` and `mean_rmse` to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/cv_metrics.json`.
- [ ] T022 [US2] [Depends on T021] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py`: Evaluate on held-out test set, calculate test RMSE, and save model to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/random_forest_model.pkl`.
- [ ] T023 [US2] [Depends on T022] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py`: Generate `ModelMetrics` report (CSV/JSON) containing `fold_scores`, `mean_rmse`, `test_rmse`.
- [X] T024a [US2] [Depends on T020] Generate null model baseline for statistical comparison. **Implementation**: Train a `DummyRegressor` (strategy='mean') on the training set with `random_state=42`. Calculate its RMSE on the test set. Save this single RMSE value to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/null_model_rmse.json`. **Note**: This provides the baseline RMSE for comparison.
- [ ] T024 [US2] [Depends on T022, T024a] Compare RF RMSE against the null model baseline using a **two-sided paired t-test** (SC-002). **Implementation**:
 1. Load RF model predictions and Null model predictions on the test set.
 2. Calculate absolute errors for both: `abs(y_test - y_pred_rf)` and `abs(y_test - y_pred_null)`.
 3. Perform a paired two-sided t-test on these absolute error vectors using `scipy.stats.ttest_rel`.
 4. Calculate p-value.
 5. If p-value < 0.05, log "Model is statistically distinguishable from null (p < 0.05)". Else, log warning.
 **Reporting**: Log the p-value. **Verify**: Run pipeline and confirm p-value is printed and pipeline completes.
- [ ] T025 [US2] [Depends on T023] Add explicit documentation and framing in output artifacts. **Implementation**:
 1. Add `# FINDINGS ARE ASSOCIATIONAL: This study uses observational data; no causal claims are made.` at the top of `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py`.
 2. Inject the statement "FINDINGS ARE ASSOCIATIONAL" into the `ModelMetrics` JSON report generated in T023.
 3. Inject the statement into `projects/PROJ-510-predicting-the-glass-forming-region-of-a/README.md` under a "Caveats" section.
 **Verify**: Run `grep "ASSOCIATIONAL" projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py` and check JSON/README content.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Sensitivity Analysis (Priority: P3)

**Goal**: Perform permutation importance analysis and sensitivity analysis on classification thresholds.

**Independent Test**: The analysis script can be run on the trained model to output a ranked list of feature importances and a sensitivity report showing how performance metrics vary with threshold changes.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for permutation importance calculation (n=1000, random_state=42) in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_analyze.py`. **Implementation**: Assert that the output is a list of floats and matches expected values for a known model.
- [ ] T027 [P] [US3] Integration test for sensitivity analysis across thresholds {50, 100, 150} K/s in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_analyze.py`. **Implementation**: Assert that the output JSON contains the correct keys and values.

### Implementation for User Story 3

- [ ] T028 [US3] [Depends on T022] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py`: Load trained model and dataset. Perform permutation importance analysis (n_permutations=1000, random_state=42).
- [ ] T029 [US3] [Depends on T028] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py`: Calculate p-values for feature importances against shuffled baseline. Rank features and flag top contributors (SC-004). **Method**: Use permutation test to calculate p-values. **Threshold**: Flag top contributors if `p < 0.05`. **Output**: JSON list of features with p-values.
- [ ] T029a [US3] [Depends on T028] Detect collinearity and re-train if necessary. **Implementation**:
 1. Check correlation matrix of predictors using `numpy.corrcoef`.
 2. **Threshold**: Flag any pair with correlation > 0.8.
 3. **Action**: IF flagged, re-train the Random Forest model excluding the feature with the lower absolute correlation with the target variable; if tied, remove alphabetically first. Save as `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/stability_test_model.pkl`.
 4. **ELSE**, copy `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/random_forest_model.pkl` to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/stability_test_model.pkl`.
 **Verification**: Explicitly verify that `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/stability_test_model.pkl` exists and is non-empty before marking task complete.
- [ ] T030b [US3] [Depends on T029a] Verify stability: Calculate RMSE variance across the swept threshold range using the `stability_test_model.pkl`. **Action**: Assert that the RMSE variance is negligible (e.g., < 5% relative variance). **Verify**: Run pipeline and confirm stability check passes.
- [ ] T031 [US3] [Depends on T029a] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py`: Conduct sensitivity analysis sweeping the **specific thresholds across a representative range of heating rates**. **Logic**:
 1. Load `stability_test_model.pkl`.
 2. For each threshold:
    a. Predict on the test set (continuous).
    b. Calculate RMSE on the continuous target (no binarization).
 3. Report RMSE values for each threshold.
 4. (Optional) Calculate RMSE variance across thresholds.
 **Output**: Report RMSE values. **Dependency Note**: This task requires `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/stability_test_model.pkl` (from T029a) to ensure the model used for sensitivity analysis has passed collinearity checks.
- [ ] T032 [US3] [Depends on T031] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py`: Generate `SensitivityReport` (CSV/JSON). **Schema**: Include `threshold_values`, `rmse_values`. **Validation**: Assert RMSE variance across thresholds is < 10% (or report the variance). **Verify**: Run pipeline and confirm report is generated and validation passes.
- [X] T033 [US3] **REMOVED**: Logic merged into T032 to avoid redundancy.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates: Add `projects/PROJ-510-predicting-the-glass-forming-region-of-a/README.md` with execution instructions. **Content**: Sections: 'Prerequisites' (list packages), 'Data Ingestion Command' (`python projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py`), 'Training Command' (`python projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py`), 'Analysis Command' (`python projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py`). **Verify**: Run `mkdocs build` or `cat projects/PROJ-510-predicting-the-glass-forming-region-of-a/README.md` to confirm sections.
- [X] T035 Code cleanup and refactoring to ensure `random_state=42` is consistent across all scripts. **Verify**: Run `grep -r "random_state=42" projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/` to confirm consistency.
- [X] T036 Performance optimization: Verify pipeline completes within 6 hours on CPU-only runner (2 cores, 7 GB RAM). **Verify**: Run `time python projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/pipeline.py` and check duration < 6h.
- [X] T037 [P] Run `quickstart.md` validation to ensure all artifacts match schemas in `contracts/`. **Command**: Run `python projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/validate_schemas.py`.
- [X] T038 Security hardening: Ensure no hardcoded secrets or external URLs other than verified `matsci/glass-forming-ability`. **Verify**: Run `bandit -r projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/` to scan for issues.

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Must produce `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/processed_alloys.csv`**.
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
Task: "Write unit test for thermodynamic formula calculation in tests/test_features.py"
Task: "Write integration test for data ingestion pipeline in tests/test_ingestion.py"

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