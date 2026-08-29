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

- [X] T001a [P] Create root project structure: `projects/PROJ-510-predicting-the-glass-forming-region-of-a/`, `data/`, `code/`, `tests/`, `docs/`. **Files to create**: `README.md` (empty), `.gitignore` (standard python). **Verify**: Run a Python script `python -c "import os, sys; paths=['projects/PROJ-510-predicting-the-glass-forming-region-of-a','data','code','tests','docs','README.md']; [sys.exit(1) if not os.path.exists(os.path.join('projects/PROJ-510-predicting-the-glass-forming-region-of-a', p)) if p != 'README.md' else sys.exit(1) if not os.path.exists(p) else 0 for p in paths]; print('All paths exist')"`.
- [X] T001b [P] Create source code structure: `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/__init__.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/utils.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/features.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/requirements.txt`. **Verify**: Run `ls -l projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/` and `test -f projects/PROJ-510-predicting-the-glass-forming-region-of-a/requirements.txt` to confirm all files exist and are non-empty.
- [X] T001c [P] Create test structure: `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/__init__.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_features.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_ingestion.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_train.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_analyze.py`. **Verify**: Run `ls -l projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/` to confirm all files exist.
- [X] T002 Initialize Python 3.11 project with dependencies: `pandas`, `scikit-learn`, `numpy`, `requests`, `pyyaml`, `datasets`, `mendeleev`, `scipy`, `pydantic`, `jsonschema` in `requirements.txt`. **Verify**: Run `pip install -r requirements.txt` and confirm no errors.
- [X] T003 [P] Configure linting (flake8/black) and formatting tools. **Files to create**: `.flake8` (max-line-length=120), `pyproject.toml` (black config). **Verify**: Run `flake8 --version` and `black --version` to confirm installation and config loading.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/raw/` and `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/` directory structure with `.gitignore` rules. **Content**: `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/.gitignore` must contain `*.csv`, `*.pkl`, `*.json`, `!README.md`. **Verify**: Run `mkdir -p projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/raw projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed` and `cat projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/.gitignore` to confirm content.
- [X] T005 [P] [US1] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/utils.py` with periodic table lookup helpers using `mendeleev` and logging infrastructure. **Verify**: Run `python -c "from code.utils import get_element_property; print(get_element_property('Fe', 'atomic_mass'))"` to confirm functionality.
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
 **Verify**: Run `python -c "import json, jsonschema; s=json.load(open('contracts/dataset.schema.yaml')); jsonschema.validate({'composition':'A_B_C', 'critical_cooling_rate':100.0, 'mixing_enthalpy':0.0, 'atomic_size_mismatch':0.0, 'electronegativity_variance':0.0, 'source_label':'test'}, s)"` to confirm validation.
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
 required: [fold_scores, mean_rmse, test_rmse, p_value_vs_null]
 SensitivityReport:
 type: object
 properties:
 threshold_values: {type: array, items: {type: number}}
 rmse_variance: {type: number}
 collinearity_flags: {type: array, items: {type: string}}
 required: [threshold_values, rmse_variance]
 ```
 **Verify**: Run `python -c "import json, jsonschema; s=json.load(open('contracts/model_output.schema.yaml')); jsonschema.validate({'fold_scores':[1.0], 'mean_rmse':1.0, 'test_rmse':1.0, 'p_value_vs_null':0.0, 'threshold_values':[50.0], 'rmse_variance':0.0}, s)"` to confirm validation.
- [X] T007b [P] [US2, US3] Update `plan.md` Technical Context to explicitly document the schema versioning strategy and the `jsonschema` enforcement mechanism required by Constitution Principle IV. **Action**: Add a subsection "Schema Versioning & Enforcement" listing `contracts/` as the source of truth and `jsonschema` as the validator. **Verify**: Run `grep -A 5 "Schema Versioning" plan.md` to confirm presence.
- [X] T008 [P] [US1] Configure error handling: Ensure data loading fails loudly (no synthetic fallback) if `matsci/glass-forming-ability` fetch fails. **Implementation**: Add `raise ValueError("Data fetch failed: matsci/glass-forming-ability unavailable")` in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py` line 45. **Verify**: Run `pytest` with a mock that simulates fetch failure to ensure the error is raised.
- [X] T009 Setup `pytest` configuration and seed management (`random_state=42`) in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/utils.py`. **Verify**: Run `pytest --version` and check `pytest.ini` or `pyproject.toml`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Thermodynamic Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Download experimental data, filter for valid ternary alloys, and compute thermodynamic descriptors.

**Independent Test**: The pipeline can be run in isolation to produce a CSV file containing at least 500 valid alloy records with all required thermodynamic columns and the `critical_cooling_rate` column computed, without training any model.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: T010 and T011 are written but currently FAIL until T012-T017 are implemented.

- [X] T010 [US1] Write unit test for thermodynamic formula calculation (mixing enthalpy, atomic size mismatch) in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_features.py`. **Status**: Written, currently fails. **Expected Failure**: Assert `AssertionError` with message "Expected mixing_enthalpy to be X but got Y" when formula is incorrect.
- [X] T011 [US1] Write integration test for data ingestion pipeline ensuring ≥500 rows and no NaN in target columns in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_ingestion.py`. **Status**: Written, currently fails. **Expected Failure**: Assert `ValueError` with message "Data availability error: <500 valid entries or zero variance in critical_cooling_rate".

### Implementation for User Story 1

- [X] T012 [US1] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py`: Download `matsci/glass-forming-ability` dataset using `datasets.load_dataset`. **Reconciliation**: This dataset is the verified source for CCR (Plan), while Mendeleev provides elemental properties (Constitution Principle VI). **Action**: Use `load_dataset("matsci/glass-forming-ability")` and verify `critical_cooling_rate` column exists and is of type `float64`. Raise `ValueError` if missing. **Verify**: Run `python -c "from code.ingestion import load_data; df = load_data(); print(len(df))"` to confirm data load.
- [X] T013 [US1] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py`: Filter dataset for ternary alloys (3 elements) and exclude rows with missing elemental data or unknown glass-forming labels. Log exclusion counts. **Verify**: Run pipeline and check logs for exclusion counts.
- [X] T014 [P] [US1] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/features.py`: Calculate `mixing_enthalpy` using `mendeleev` elemental properties and ternary composition weights. **Verify**: Run unit tests in `test_features.py`.
- [X] T015 [P] [US1] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/features.py`: Calculate `atomic_size_mismatch` and `electronegativity_variance` using standard periodic table definitions. **Verify**: Run unit tests in `test_features.py`.
- [X] T016a [US1] [Depends on T013] Save processed data to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/processed_alloys.csv`. **Verification**:
 1. Ensure file exists and is non-empty.
 2. Validate schema: Check for columns `composition`, `critical_cooling_rate`, `mixing_enthalpy`, `atomic_size_mismatch`, `electronegativity_variance`.
 3. Validate row count: Assert `len(df) >= 500`.
 4. Validate data integrity: Assert no NaN in `critical_cooling_rate` or `mixing_enthalpy`.
 **Action**: Write script to perform these checks and raise `ValueError` if any fail.
- [X] T017 [US1] Add validation to ensure `critical_cooling_rate` has non-zero variance and ≥500 entries. **Implementation**: In `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py`, after filtering, check `df['critical_cooling_rate'].var() > 0` and `len(df) >= 500`. **Error**: `raise ValueError("Data availability error: <500 valid entries or zero variance in critical_cooling_rate")`. **Verify**: Run pipeline with a truncated dataset to confirm error.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train a Random Forest regressor with k-fold cross-validation and evaluate performance.

**Independent Test**: The training script can be executed on the generated dataset to produce a trained model file and a metrics report containing the cross-validation score, without requiring any external GPU or internet access after the data is loaded.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for k-fold cross-validation split generation ensuring non-overlapping folds in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_train.py`.
- [X] T019 [P] [US2] Integration test for model training producing valid `ModelMetrics` schema in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_train.py`.

### Implementation for User Story 2

- [X] T020 [US2] [Depends on T016a] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py`: Load `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/processed_alloys.csv`, perform a standard train-test split with `random_state=42`. **Verification**: Assert `len(train) == 0.8 * len(df)` (approx) and `random_state=42` is used in logs.
- [X] T021 [US2] [Depends on T020] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py`: Train `RandomForestRegressor` and perform k-fold cross-validation. **Action**: Aggregate fold scores, calculate mean RMSE and fold variance. Save `fold_scores` and `mean_rmse` to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/cv_metrics.json`. **Schema**: `{"fold_scores": [0.0,...], "mean_rmse": 0.0}`. **Verification**: Run `python -c "import json; d=json.load(open('data/models/cv_metrics.json')); assert 'fold_scores' in d and 'mean_rmse' in d"`.
- [X] T022 [US2] [Depends on T021] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py`: Evaluate on held-out test set, calculate test RMSE, and save model to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/random_forest_model.pkl`. **Verification**: Run `python -c "import os; assert os.path.exists('data/models/random_forest_model.pkl')"`.
- [X] T022b [US2] [Depends on T022] Generate null model baseline and predictions. **Implementation**:
 1. Train a `DummyRegressor` (strategy='mean') on the training set with `random_state=42`.
 2. Calculate predictions on the test set.
 3. Save null model predictions to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/null_model_predictions.npy`.
 4. Save null model RMSE to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/null_model_rmse.json`.
 **Verification**: Check file existence and non-zero size for both files.
- [X] T024 [US2] [Depends on T022, T022b] Compare RF RMSE against the null model baseline using a **two-sided paired t-test** (SC-002). **Implementation**:
 1. Load RF model predictions and Null model predictions on the test set.
 2. Calculate absolute errors for both: `abs(y_test - y_pred_rf)` and `abs(y_test - y_pred_null)`.
 3. **Align** the error vectors by index to ensure pairing.
 4. Perform a two-sided **paired** t-test on these aligned error vectors using `scipy.stats.ttest_rel` (assume equal variance is not applicable for paired tests).
 5. Calculate p-value.
 6. If p-value < 0.05, log "Model is statistically distinguishable from null (p < 0.05)". Else, log warning.
 **Reporting**: Log the p-value and save to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/statistical_comparison.json`. **Schema**: `{"p_value": 0.0, "test_statistic": 0.0}`. **Verification**: Run pipeline and confirm p-value is printed and `statistical_comparison.json` exists with valid schema.
- [X] T025 [US2] [Depends on T021, T022] Add explicit documentation and framing in output artifacts. **Implementation**:
 1. Add `# FINDINGS ARE ASSOCIATIONAL: This study uses observational data; no causal claims are made.` at the top of `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py`.
 2. Inject the statement "FINDINGS ARE ASSOCIATIONAL" into the `ModelMetrics` JSON report generated in T021.
 3. Inject the statement into `projects/PROJ-510-predicting-the-glass-forming-region-of-a/README.md` under a "Caveats" section.
 4. Create `projects/PROJ-510-predicting-the-glass-forming-region-of-a/Research_Notes.md` with a "Framing" section stating: "All predictive findings are explicitly framed as ASSOCIATIONAL due to the observational nature of the dataset."
 5. Ensure the final `sensitivity_report.csv` or `model_metrics.json` includes a metadata field or header noting "ASSOCIATIONAL".
 **Verify**: Run `grep "ASSOCIATIONAL" projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py` and check JSON/README/Research Notes content.
- [X] T025c [US2] [Depends on T021, T024, T022b] Aggregate CV metrics, null model comparison, and test RMSE into a single `model_metrics_final.json` artifact. **Implementation**:
 1. Load `cv_metrics.json`, `statistical_comparison.json`, and `test_rmse` (calculated in T022).
 2. Merge into a single JSON object containing `mean_rmse`, `fold_scores`, `p_value_vs_null`, `test_rmse`, and `feature_importance_ranking` (from T028).
 3. Save to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/model_metrics_final.json`.
 **Verification**: Run `python -c "import json; d=json.load(open('data/models/model_metrics_final.json')); assert 'mean_rmse' in d and 'p_value_vs_null' in d"`.
- [X] T025b [US2] [Depends on T025c] Update `plan.md` to reference the unified `model_metrics_final.json` as the single source of truth for SC-002. **Action**: Update the "Key Entities" or "Success Criteria" section to point to this file. **Verify**: Run `grep "model_metrics_final.json" plan.md`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Feature Importance and Sensitivity Analysis (Priority: P3)

**Goal**: Perform permutation importance analysis and sensitivity analysis on classification thresholds.

**Independent Test**: The analysis script can be run on the trained model to output a ranked list of feature importances and a sensitivity report showing how performance metrics vary with threshold changes.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for permutation importance calculation (n=1000, random_state=42) in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_analyze.py`. **Implementation**: Assert that the output is a list of floats and matches expected values for a known model.
- [X] T027 [P] [US3] Integration test for sensitivity analysis across thresholds {50, 100, 150} K/s in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_analyze.py`. **Implementation**: Assert that the output JSON contains the correct keys and values.

### Implementation for User Story 3

- [X] T028 [US3] [Depends on T022] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py`: Load trained model (`random_forest_model.pkl`) and dataset. Perform permutation importance analysis (n_permutations=1000, random_state=42).
- [X] T029 [US3] [Depends on T028] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py`: Calculate p-values for feature importances against shuffled baseline. Rank features and flag top contributors (SC-004). **Method**: Use permutation test to calculate p-values. **Threshold**: Flag top contributors if `p < 0.05`. **Output**: JSON list of features with p-values. **File Path**: `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/feature_importance.json`. **Schema**: `[{"feature": "mixing_enthalpy", "p_value": 0.01},...]`. **Verification**: Validate JSON against schema and ensure at least one thermodynamic parameter is in the top-2 with p < 0.05.
- [X] T029a [US3] [Depends on T028, T029] Detect collinearity and flag results. **Implementation**:
 1. Check correlation matrix of predictors using `numpy.corrcoef`.
 2. **Threshold**: Flag any pair with correlation > 0.8.
 3. **Action**: If collinearity > 0.8 is detected, **re-train** the Random Forest model excluding the lower-importance feature of the pair to verify stability.
 4. **Crucial**: Save the re-trained model to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/random_forest_model.pkl` (overwriting the previous version) so downstream tasks use the stable model.
 5. Generate a report `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/collinearity_report.json` listing flagged pairs.
 6. **Stability Check**: Append a "stability_check" section to `feature_importance.json` (or create `stability_comparison.json`) showing the top features before and after exclusion of the collinear feature.
 **Verification**: Explicitly verify that `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/collinearity_report.json` exists, is non-empty, and matches the schema (list of flagged pairs). Verify that `feature_importance.json` (or `stability_comparison.json`) contains the stability comparison if collinearity was detected.
- [X] T031 [US3] [Depends on T022 (or T029a if re-trained)] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py`: Conduct sensitivity analysis sweeping the **specific thresholds {50, 100, 150} K/s** (hardcoded). **Logic**:
 1. Load `random_forest_model.pkl`.
 2. For each threshold in {50, 100, 150} K/s:
 a. Predict on the test set (continuous).
 b. Binarize true labels: `1 if y_true >= threshold else 0`.
 b. Binarize predictions: `1 if y_pred >= threshold else 0`.
 c. Calculate **RMSE** on the continuous predictions (primary metric).
 d. Calculate **F1-score** on the binarized labels and predictions (secondary metric).
 3. Report RMSE and F1-score values for each threshold.
 4. Calculate RMSE variance across thresholds.
 **Output**: Report RMSE and F1-score values. **Dependency Note**: This task requires `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/random_forest_model.pkl` (from T022 or T029a).
- [X] T030b [US3] [Depends on T031] Verify stability: Read **RMSE variance** from T031 output file (`sensitivity_report.csv`). **Action**: Assert that the **RMSE variance** is negligible (e.g., < 10% relative variance). **Verify**: Run pipeline and confirm stability check passes. **Verification**: Assert `variance < 0.1 * mean` for **RMSE** scores across thresholds. (Secondary: Assert F1-score variance < 10% if applicable).
- [X] T032 [US3] [Depends on T031] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py`: Generate `SensitivityReport` (CSV/JSON). **File Path**: `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/sensitivity_report.csv`. **Schema**: CSV with columns `threshold`, `rmse`, `f1_score`. **Validation**: Assert RMSE variance across thresholds is < 10% (or report the variance). **Verify**: Run pipeline and confirm report is generated and validation passes.
- [X] T033 [US3] **REMOVED**: Logic merged into T032 to avoid redundancy.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Documentation updates: Add `projects/PROJ-510-predicting-the-glass-forming-region-of-a/README.md` with execution instructions. **Content**: Sections: 'Prerequisites' (list packages), 'Data Ingestion Command' (`python projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py`), 'Training Command' (`python projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py`), 'Analysis Command' (`python projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py`). **Verify**: Run `cat projects/PROJ-510-predicting-the-glass-forming-region-of-a/README.md` to confirm sections.
- [X] T035 Code cleanup and refactoring to ensure `random_state=42` is consistent across all scripts. **Verify**: Run `grep -r "random_state=42" projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/` to confirm consistency.
- [X] T036 Performance optimization: Verify pipeline completes within 6 hours on CPU-only runner (2 cores, 7 GB RAM). **Verification**:
 1. Run pipeline locally as a sanity check.
 2. **Definitive Check**: Inspect the GitHub Actions runner logs for the CI job to confirm the total execution time is < 6 hours.
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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T016a output** (processed data). May integrate with US1 but should be independently testable.
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

## Phase O: Revision & Gap Resolution (Addressing Review Concerns)

**Purpose**: Resolve specific issues raised by the analysis phase regarding data sampling, collinearity handling, and statistical rigor.

- [ ] T039 [US1] Implement robust data sampling for large datasets: If `matsci/glass-forming-ability` exceeds ~10k rows, implement streaming or a fixed-seed sample (e.g., `itertools.islice` or `df.sample(n=1000, random_state=42)`) in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py`. **Constraint**: Do NOT use synthetic data. Log the exact sampling rule (N, seed, method) in `data/processed/sampling_log.txt`. **Verify**: Check logs for sampling parameters and confirm N >= 500.
- [ ] T040 [US3] Refine collinearity handling: In `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py`, if collinearity > 0.8 is detected, do NOT just flag. Instead, re-run the feature importance analysis (T028) excluding the lower-importance feature of the pair to verify stability. **Output**: Append a "stability_check" section to `feature_importance.json` showing the top features before and after exclusion. **Verify**: Confirm the report includes the stability comparison.
- [ ] T041 [US2] Enhance statistical rigor: In `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py`, ensure the t-test (T024) explicitly handles unequal variances (use `equal_var=False` in `scipy.stats.ttest_ind` unless proven otherwise) and logs the assumption. **Verify**: Check code for `equal_var=False` parameter and corresponding log message.
- [ ] T042 [US3] Address threshold sensitivity: In `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py`, if the RMSE variance across {50, 100, 150} K/s exceeds 10% (failing SC-003), generate an additional report `sensitivity_report_extended.csv` with a finer sweep (e.g., every 10 K/s from 0 to 200) to identify the stability region. **Verify**: Confirm the extended report exists and is referenced in the main sensitivity report.