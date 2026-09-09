---
description: "Task list for feature implementation"
---

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a‑1 [P] Create root project directories:
 - `projects/PROJ-510-predicting-the-glass-forming-region-of-a/`
 - `data/`, `code/`, `tests/`, `docs/`
- [X] T001a‑2 [P] Create placeholder files: `README.md` (empty) and `.gitignore` (standard Python).
- [X] T001a‑3 [P] Write validation script `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/validate_setup.py` (as previously defined) to check directories and files.
- [X] T001a‑4 [P] Execute validation script to ensure setup correctness.
- [X] T001b [P] Create source code structure: empty `__init__.py`, `utils.py`, `ingestion.py`, `features.py`, `train.py`, `analyze.py`. Add `requirements.txt` with:
```
pandas
scikit-learn
numpy
requests
pyyaml
datasets
mendeleev
scipy
pydantic
jsonschema
pytest
shap
```
- [X] T001c [P] Populate `__init__.py` and core modules with basic imports and docstrings.
- [X] T001d [P] Create test package: `tests/__init__.py`, `test_features.py`, `test_ingestion.py`, `test_train.py`, `test_analyze.py`.
- [X] T002 Initialize Python 3.11 project with dependencies (install `requirements.txt`).
- [X] T003 [P] Configure linting (flake8/black) with `.flake8` and `pyproject.toml`.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T004 [P] Setup `data/raw/` and `data/processed/` directories with `.gitignore` (ignore `*.csv`, `*.pkl`, `*.json`, keep `README.md`).
- [X] T005 [P] [US1] Implement `code/utils.py` with periodic table lookup helpers (`mendeleev`) and logging.
- [X] T006 [P] [US1] Create `contracts/dataset.schema.yaml` defining `AlloyRecord` fields (as previously defined).
- [X] T007 [P] [US2, US3] Create `contracts/model_output.schema.yaml` defining `ModelMetrics` and `SensitivityReport` (as previously defined).
- [X] T007b [P] [US2, US3] Update `plan.md` to document schema versioning and JSON‑Schema enforcement.
- [X] T008 [P] [US1] **Ingestion Error Handling**: Ensure `code/ingestion.py` raises a clear `ValueError` if the `matsci/glass-forming-ability` dataset cannot be fetched. This is integrated into T012 logic.
- [X] T009 [P] Configure `pytest` and enforce `random_state=42` in `utils.py`.

## Phase 3: User Story 1 - Data Ingestion and Thermodynamic Feature Engineering (Priority: P1)

**Goal**: Download experimental data, filter for valid ternary alloys, and compute thermodynamic descriptors.

- [X] T012 [US1] Implement `code/ingestion.py`:
 1. Load the verified dataset via `datasets.load_dataset("matsci/glass-forming-ability", streaming=True)`.
 2. **Schema Validation**: Immediately check that the dataset schema contains the `critical_cooling_rate` column. If missing, raise `ValueError("Verified Data Source Mismatch: Dataset lacks critical_cooling_rate column.")`.
 3. Filter for ternary alloys: parse the `composition` string using a **robust parser** that:
 - Splits the string into element‑symbol/amount tokens using regex `r'([A-Z][a-z]?)(\d*\.?\d*)'`.
 - Builds a dict `{element: float(amount)}`.
 - Validates that exactly three distinct elements are present and that each element exists in `mendeleev`.
 4. Exclude rows missing `critical_cooling_rate` or with malformed composition; log exclusions with reasons to `data/logs/exclusion_log.txt`.
 5. **Data Volume Handling**: Process ALL valid data. If the dataset exceeds memory limits (e.g., >100k rows), stream and process in chunks, accumulating statistics online. Do NOT hardcode a sampling cap that reduces data below the FR-001 target of N >= 1000.
 6. Write the filtered rows to `data/processed/processed_alloys_raw.csv`.
- [X] T012b [US1] Validate dataset size against FR-001 target:
 - Load `data/processed/processed_alloys_raw.csv`.
 - If N < 500, raise `ValueError("Data availability error: N < 500. Minimum N >= 500 required by FR-001.")`.
 - If 500 <= N < 1000, log `WARNING` "Data size below target (N < 1000) but above minimum (N >= 500). Proceeding."
 - If N >= 1000, log `INFO` (data is sufficient).
 - **Deliverable**: Write `data/logs/data_validation_status.json` with schema `{"status": "pass|warning|fail", "n_total": int, "message": str}`.
- [X] T014 [P] [US1] Implement `code/features.py` function `calc_mixing_enthalpy`:
 **Formula**: Use pairwise enthalpy of mixing data from `mendeleev` (if available for the specific element pairs).
 **Edge Case Handling**: If pairwise data is missing for any pair in the ternary system, **exclude the row** from the dataset, log the exclusion with the specific missing pair to `data/logs/exclusion_log.txt`, and continue processing. **CRITICAL**: If the resulting dataset size drops below N=500 due to these exclusions, raise a `ValueError("Dataset size dropped below N=500 due to missing enthalpy data. Cannot proceed.")` to satisfy FR-002.
 Formula: $H_{mix} = \sum_{i \neq j} c_i c_j \Delta H_{ij}$.
 **Deliverable**: Update `data/processed/processed_alloys_raw.csv` with computed enthalpy; log exclusions to `data/logs/exclusion_log.txt`.
- [X] T015 [P] [US1] Implement `code/features.py` function `calc_size_mismatch` and `calc_electronegativity_variance`:
 **Formulas**:
 - `atomic_size_mismatch` ($\delta$): $1 - \frac{\sum c_i r_i}{\bar{r}}$, where $r_i$ is atomic radius from `mendeleev` and $\bar{r}$ is the weighted average radius.
 - `electronegativity_variance`: Variance of electronegativity values weighted by composition $c_i$.
 **Output**: Save the function signatures and ensure they return float values.
- [X] T010a [US1] Unit test `test_features.py::test_mixing_enthalpy`:
 - Implement unit tests verifying the `calc_mixing_enthalpy` function against known periodic table values.
 - Ensure the test passes for valid ternary compositions and correctly handles edge cases.
- [X] T010b [US1] Unit test `test_features.py::test_size_mismatch`:
 - Implement unit tests verifying the `calc_size_mismatch` and `calc_electronegativity_variance` functions.
 - Ensure the tests pass for known compositions and verify tolerance of 1e-6.
- [X] T016a [US1] Save the engineered dataset (including all thermodynamic columns) to `data/processed/processed_alloys.csv`.
 - Load `data/processed/processed_alloys_raw.csv` and append computed features.
 - Ensure the file contains exactly the columns defined in `contracts/dataset.schema.yaml`.
 - **Deliverable**: `data/processed/processed_alloys.csv`.
- [X] T016b [US1] Validate processed data:
 - Load `data/processed/processed_alloys.csv`.
 - **Schema Check**: Use `jsonschema` to validate the data against `contracts/dataset.schema.yaml`. Log errors if validation fails.
 - **Data Volume Check**: If N < 500, raise `ValueError("Data availability error: N < 500. Minimum N >= 500 required by FR-001.")`.
 - If 500 <= N < 1000, log `WARNING` "Data size below target (N < 1000) but above minimum (N >= 500). Proceeding."
 - If N >= 1000, log `INFO` (data is sufficient).
 - **Deliverable**: Write `data/logs/schema_validation_status.json` with schema `{"status": "pass|fail", "n_valid": int, "errors": list}`.
- [X] T016c [US1] **Data Availability Audit**:
 - Load `data/processed/processed_alloys.csv`.
 - Count the total number of valid ternary alloys after all filtering steps (composition parsing, missing data, label exclusion).
 - Write a persistent audit log `data/logs/data_availability_audit.json` with schema `{"total_valid": int, "target_met": bool, "minimum_met": bool}`.
 - **Deliverable**: `data/logs/data_availability_audit.json`.
- [X] T017 [US1] After filtering, assert that `critical_cooling_rate` variance > 0; otherwise raise `ValueError("Zero variance in critical_cooling_rate")`.

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train a Random Forest regressor with k-fold cross-validation and evaluate against a null model.

- [X] T020 [US2] Load `processed_alloys.csv`; perform a standard train-test split (`random_state=42`, `test_size=0.2`).
 - Split the data into `data/processed/train_set.csv` and `data/processed/test_set.csv`.
 - Save the split indices to `data/models/split_indices.json`.
 - **Deliverable**: `data/processed/train_set.csv`, `data/processed/test_set.csv`, `data/models/split_indices.json`.
- [X] T019 [US2] **Critical**: Validate Training Set Size.
 - Load the training set created in T020 (`data/processed/train_set.csv`).
 - If `len(X_train) < 500`, raise `ValueError("SC-001 Violation: Training set size < 500 after 80/20 split. Increase raw data or adjust split ratio.")`.
 - **Deliverable**: Write `data/logs/training_set_validation.json` with schema `{"status": "pass|fail", "n_train": int}`.
- [X] T020b [US2] **Shared CV Splitter**: Instantiate a `KFold(n_splits=5, shuffle=True, random_state=42)` object. Save the fold indices to `data/models/cv_folds_indices.json` to ensure T021 and T022b use the exact same folds.
- [X] T021 [US2] Train `RandomForestRegressor` on the training set; perform 5-fold cross-validation using the **shared folds** from T020b. Record each fold RMSE in `data/models/cv_metrics.json`.
 - Train the model on `data/processed/train_set.csv`.
 - Perform 5-fold CV; save fold scores to `data/models/cv_metrics.json`.
 - Save the trained model to `data/models/random_forest_model.pkl`.
 - **Output Schema**: `{"fold_scores": [float, float, float, float, float], "mean_rmse": float, "std_rmse": float}`.
 - **Deliverable**: `data/models/cv_metrics.json`, `data/models/random_forest_model.pkl`.
- [X] T022 [US2] Evaluate on the held‑out test set; save RMSE and the trained model to `data/models/random_forest_model.pkl`.
 - Load `data/models/random_forest_model.pkl` and `data/processed/test_set.csv`.
 - Calculate test set RMSE.
 - **Deliverable**: `data/models/test_metrics.json` with schema `{"test_rmse": float}`.
- [X] T022b-1 [US2] **Null Model Training**: Train a `DummyRegressor` (strategy='mean') on the **same training split** as T021.
 - Save the trained dummy model to `data/models/null_model.pkl`.
- [X] T022b-2 [US2] **Null Model CV**: Perform **5-fold CV** on the `DummyRegressor` using the **exact same folds** from T020b.
 - Save the 5 fold scores to `data/models/null_model_cv_scores.json` with schema `{"fold_scores": [float, float, float, float, float], "mean_rmse": float, "std_rmse": float}`.
- [X] T022b-3 [US2] **Null Model Test Evaluation**: Evaluate the `DummyRegressor` on the test set.
 - Save the test set predictions to `data/models/null_model_predictions.npy` and the test RMSE to `data/models/null_model_rmse.json`.

### Statistical Validation (SC‑002)

- [X] T024a [US2] Implement **Null-Model Statistical Test**:
 1. Load the 5-fold CV RMSE scores from `cv_metrics.json` (list of 5 values).
 2. Load the 5-fold CV RMSE scores from `null_model_cv_scores.json` (list of 5 values).
 3. Perform a **paired t-test** (using `scipy.stats.ttest_rel`) comparing the Model CV scores against the Null Model CV scores.
 4. Compute p-value and t-statistic.
 5. **Deliverable**: Save results to `data/models/statistical_comparison.json` with schema `{"p_value": <float>, "t_statistic": <float>, "sc002_met": <bool>}` where `sc002_met` is `p_value < 0.05`.
- [X] T024c [US2] Gate task (Non-Blocking):
 - Load `statistical_comparison.json`.
 - If `sc002_met` is `false`, log a **WARNING** "SC-002 failed: Model not statistically distinguishable from null" and save a status flag `sc002_status: FAILED` to `data/models/sc002_status.json`. **Do not raise an exception**; the pipeline must continue to generate the report with this negative finding.
 - If `sc002_met` is `true`, log success and save `sc002_status: PASSED`.

## Phase 5: User Story 3 - Feature Importance and Sensitivity Analysis (Priority: P3)

### Collinearity Detection and Stability Check (Pre-Analysis)

- [X] T029a [US3] **Detect Collinearity**:
 1. Load the initial model (`random_forest_model.pkl`) and the processed dataset.
 2. Compute Pearson correlation matrix of the engineered features.
 3. Flag any pair with |ρ| > 0.8; write `collinearity_report.json`.
 4. **Report Initial Metrics**: Before any retraining, record the initial model's metrics in `data/models/initial_model_metrics.json`.
- [X] T029b [US3] **Retrain if Needed (with Fallback)**:
 1. If collinearity exists:
 - Compute mean absolute SHAP values from the **initial** model.
 - Identify the feature with the **lowest** mean absolute SHAP among the collinear pairs.
 - **Loop**: Retrain a new `RandomForestRegressor` excluding that feature, using **identical hyperparameters and random_state=42**.
 - **Max Iterations**: Limit the number of iterations to a finite, manageable set. If collinearity persists after 3 drops, stop and mark as "best_available".
 - Save the new model as `data/models/random_forest_model_stable.pkl` (if stable) or `data/models/random_forest_model_best_available.pkl` (if max iterations reached).
 - Record decision in `collinearity_decision.json` (`{"retrain_required": true, "dropped_feature": "<name>", "iterations": int, "status": "stable|best_available"}`).
 2. If no collinearity:
 - Copy `random_forest_model.pkl` to `random_forest_model_stable.pkl`.
 - Record decision in `collinearity_decision.json` (`{"retrain_required": false}`).
 - **Deliverable**: `data/models/random_forest_model_stable.pkl` or `data/models/random_forest_model_best_available.pkl`, `collinearity_decision.json`.
- [X] T029c [US3] **Stable Model Fallback**:
 - Ensure `random_forest_model_stable.pkl` exists. If T029b produced a `best_available` model, copy `random_forest_model_best_available.pkl` to `random_forest_model_stable.pkl` and log a warning "Stability not fully achieved; using best available model".
 - This task ensures T028 and T031 always have a valid model input.
 - **Deliverable**: `data/models/random_forest_model_stable.pkl`.

### Permutation Importance (SC‑004)

- [X] T028 [US3] Using the **stable model** (`random_forest_model_stable.pkl`), compute permutation importance (`n_permutations=1000`, `random_state=42`).
 1. Calculate p-values using a **one-sample t-test** comparing the observed importance of each feature against the distribution of importance scores from the 1000 permutations (shuffled baseline).
 2. Write `feature_importance.json` (list of `{feature, p_value, importance_score}`).
 3. **Report**: Log whether at least one thermodynamic feature is in the top‑2 with `p_value < 0.05`. Do not fail the pipeline if this condition is not met; simply report the finding.

### Sensitivity Analysis (SC‑003)

- [X] T031 [US3] Perform **Threshold‑Sweep Sensitivity Analysis** (Depends on: T029c):
 1. Load the **stable model** (`random_forest_model_stable.pkl`) and the full processed dataset.
 2. **Regression Metric Sweep**:
 - For each threshold in a range of high cooling rates:
 - **Binarize Predictions**: Use the *regressor's* predictions and binarize them at the current threshold (prediction >= threshold ? 1: 0). Do NOT retrain a new model.
 - Compute F1-score on the test set using these binarized predictions.
 - **Step C (Report)**: Calculate the F1 margin: `(max_F1 - min_F1) / max(mean_f1, 0.1)`. (Use 0.1 as floor to prevent masking instability).
 - **Step D (RMSE Variance Reporting)**: Calculate the variance of the *regression* RMSE across thresholds (should be near zero).
 3. Write `sensitivity_report.csv` with columns `threshold,f1_score,f1_margin_pct,rmse_variance,stability_status`.
 - `stability_status` is `PASS` if `f1_margin_pct <= 0.10` else `FAIL`.
 4. **Deliverable**: Write `sensitivity_status.json` with schema `{"stability_met": true/false, "f1_margin_pct": <float>, "threshold_values": [50,100,150], "run_status": "FAILED" if stability_met is false else "PASSED"}`.
 - **Note**: If the model used is "best_available" (unstable), the `stability_met` flag may be false, but the analysis must still run and report this status to satisfy FR-006 associational framing.
- [X] T030b [US3] Verification of sensitivity stability:
 - Load `sensitivity_status.json`; assert `stability_met` is `true`. If not, log a **WARNING** "SC-003 failed: Sensitivity margin exceeds 10%" and save `sc003_status: FAILED` to `data/models/sc003_status.json`. **Do not raise an exception**; the pipeline must continue to generate the report with this negative finding, but the `run_status` in `sensitivity_status.json` must be explicitly set to "FAILED" to flag the violation.

## Phase N: Polish & Cross‑Cutting Concerns

- [X] T034 [P] Documentation updates: README with execution instructions. **Note**: Specific caveats and "ASSOCIATIONAL" framing will be added in T055.
- [X] T035 Ensure `random_state=42` is used consistently across all scripts.
- [X] T036 Performance optimization: confirm pipeline completes within 6 h on CPU (local sanity check + CI logs).
- [X] T037 [P] Run `validate_schemas.py` to ensure all artifacts match contracts.
 **Script Definition**: Create `code/validate_schemas.py`. It must load `contracts/dataset.schema.yaml` and `contracts/model_output.schema.yaml`. It must iterate through all generated JSON/CSV artifacts in `data/` and `data/models/` and validate them against the schemas.
 **Output**: Print "Validation Passed" and exit with code 0 if all match. Print "Validation Failed" and list errors, then exit with code 1 if any mismatch.
- [X] T038 Security hardening: scan for hard‑coded secrets; ensure only verified URL is used.

## Phase O: Revision & Gap Resolution

- (T041 removed: logic merged into T024a)

## Phase P: Final Integration & Reporting

- [X] T043 [US3] Generate `REPORT.md` summarizing data, model performance, feature importance, sensitivity analysis, and caveats.
 **Inputs**: `model_metrics_baseline.json`, `feature_importance.json`, `sensitivity_status.json`, **`statistical_comparison.json`**, **`data/logs/training_set_validation.json`**.
 **Requirements**:
 - Explicitly state that all predictive findings are **ASSOCIATIONAL** (per FR-006).
 - Report the statistical significance of the model vs null model (p-value, t-statistic, sc002_met status) as a core section.
 - Report feature importance and sensitivity stability results (including the `run_status` flag).
 - **Headline Metric**: Explicitly report the **5-fold CV mean RMSE** as the primary performance metric (Constitution Principle VII).
 **Depends on**: T028, T031, T022, T055.
- [X] T034b [P] [MOVED] Documentation updates: README with execution instructions and caveats (including "ASSOCIATIONAL" framing). **Depends on T043**.
- [X] T044 [P] Full pipeline run validation (ingestion → train → analyze → report) in a clean environment.
 - Execute the full pipeline in a fresh virtualenv.
 - Verify all artifacts are generated and match schemas.
 - **Deliverable**: `data/logs/pipeline_run_validation.log`.

## Phase Q: Verification & Compliance (New)

**Purpose**: Ensure all outputs meet the "Real Data Only" and "No Fabrication" constitution gates.

- [X] T046 [P] **Data Source Audit**: Write `code/audit_data_source.py` to verify that `data/processed/processed_alloys.csv` contains a `source_label` column explicitly set to "matsci/glass-forming-ability" and that no synthetic data flags (e.g., `is_synthetic=True`) exist.
- [X] T047 [P] **Result Reproducibility Check**: Re-run `code/ingestion.py` and `code/features.py` in a fresh environment and compare the content hash (SHA-256) of the output `processed_alloys.csv` against the original run hash stored in `data/logs/ingestion_hash.txt`. If hashes differ, raise an error.
- [X] T048 [P] **Statistical Significance Gate**: Create a script `code/check_sc002.py` that parses `statistical_comparison.json` and logs a **WARNING** if `sc002_met` is false, ensuring the report explicitly flags the failure (consistent with T024c's non-blocking design). **Do NOT exit with code 1**.
- [X] T049 [P] **Sensitivity Gate**: Create a script `code/check_sc003.py` that parses `sensitivity_status.json` and logs a failure if `stability_met` is false, ensuring the report explicitly flags unstable thresholds.

## Phase R: Edge Case & Robustness Handling (New)

**Purpose**: Address specific edge cases and robustness requirements from spec.md to prevent silent failures or data corruption.

- [X] T050 [US1] **Edge Case: Empty Dataset**: Modify `code/ingestion.py` to explicitly check if the filtered dataset is empty after removing malformed compositions. If empty, raise `ValueError("Dataset is empty after filtering. Check composition parsing logic and data source validity.")`. Log the error to `data/logs/empty_dataset_error.log`.
- [X] T051 [US1] **Edge Case: Unknown Labels**: Ensure `code/ingestion.py` explicitly filters out rows where `glass_forming_label` is "unknown", "mixed", or null, and logs the count of excluded samples to `data/logs/exclusion_log.txt`. Write a status file `data/logs/label_filtering_status.json` with schema `{"excluded_count": int, "status": "pass"}`.
- [X] T052 [US1] **Edge Case: Zero Enthalpy**: Verify `code/features.py` handles `mixing_enthalpy == 0` as a valid numeric value (no special error handling required, but ensure no `NaN` propagation).
- [X] T053 [US2] **Edge Case: Low Variance Target**: In `code/train.py`, verify that the target variable `critical_cooling_rate` has non-zero variance before training. If variance is 0, raise `ValueError("Target variable has zero variance; cannot train regression model.")`.
- [X] T054 [US3] **Edge Case: Collinearity Resolution Failure**: If T029b fails to identify a stable model after 3 drops (all features collinear), raise a clear `ValueError("Collinearity resolution failed: No stable feature subset found.")` rather than proceeding with an unstable model. Log the failure state to `data/models/collinearity_resolution_failed.json`.

## Phase S: Documentation & Reporting Refinement (New)

**Purpose**: Ensure the final report and documentation strictly adhere to the "Associational" constraint and clearly communicate limitations.

- [X] T055 [US3] **Associational Framing**: Update `REPORT.md` template to include a dedicated "Limitations and Caveats" section that explicitly states:
 1. The dataset is observational; all findings are **associational**, not causal.
 2. The model performance is bounded by the quality and representativeness of the `matsci/glass-forming-ability` dataset.
 3. The sensitivity analysis results are specific to the tested thresholds within the examined range.
 **Note**: This task is independent of T028/T031 success to ensure the disclaimer is always present.
- [X] T056 [US3] Update `README.md` to include a "How to Interpret Results" section that guides users on reading the `sc002_met` and `stability_met` flags without over-interpreting negative results.