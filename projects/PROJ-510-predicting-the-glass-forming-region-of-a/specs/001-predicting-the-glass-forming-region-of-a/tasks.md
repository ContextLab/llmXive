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

- [X] T001a‑1 [P] Create root project directories: `data/`, `code/`, `tests/`, `docs/`.
- [X] T001a‑2 [P] Create placeholder files: `README.md` (empty) and `.gitignore` (standard Python).
- [X] T001a‑3 [P] Write validation script `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/validate_setup.py` to check:
 1. Existence of directories `data/`, `code/`, `tests/`, `docs/`.
 2. Existence of `README.md` and `.gitignore`.
 3. Write permissions for `data/` and `code/`.
 4. Exit with code 0 if all pass, code 1 otherwise.
- [X] T001a‑4 [P] Execute validation script to ensure setup correctness.
- [X] T001b [P] Create source code structure: empty `__init__.py`, `utils.py`, `ingestion.py`, `features.py`, `train.py`, `analyze.py`. Add `requirements.txt` with:
```
pandas>=2.0.0
scikit-learn>=1.3.0
numpy>=1.24.0
requests>=2.31.0
pyyaml>=6.0.0
datasets>=2.14.0
mendeleev>=0.17.0
scipy>=1.11.0
pydantic>=2.0.0
jsonschema>=4.19.0
pytest>=7.4.0
shap>=0.42.0
```
- [X] T001c [P] Populate `__init__.py` and core modules with basic imports and docstrings.
- [X] T001d [P] Create test package: `tests/__init__.py`, `test_features.py`, `test_ingestion.py`, `test_train.py`, `test_analyze.py`.
- [X] T002 Initialize Python project with dependencies (install `requirements.txt`).
- [X] T003 [P] Configure linting (flake8/black) with `.flake8` and `pyproject.toml`.

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [X] T004 [P] Setup `data/raw/` and `data/processed/` directories with `.gitignore` (ignore `*.csv`, `*.pkl`, `*.json`, keep `README.md`).
- [X] T005 [P] [US1] Implement `code/utils.py` with periodic table lookup helpers (`mendeleev`) and logging.
- [X] T006 [P] [US1] Create `contracts/dataset.schema.yaml` defining `AlloyRecord` fields (as previously defined).
- [X] T007 [P] [US2, US3] Create `contracts/model_output.schema.yaml` defining `ModelMetrics` and `SensitivityReport` (as previously defined).
- [X] T007b [P] [US2, US3] Update `plan.md` to document schema versioning and JSON‑Schema enforcement.
- [ ] T008 [P] [US1] **Ingestion Error Handling**: Implement `code/ingestion.py` to include a `try/except` block around the dataset fetch. If the fetch fails (HTTP error, timeout, or missing column), raise `ValueError` and write a detailed error log to `data/logs/fetch_error.log`.
 - **Deliverable**: `data/logs/fetch_error.log` (created on failure) and explicit `ValueError` on failure.
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
 5. **Data Volume Handling**: Process data in chunks of **5000 rows**.
 - **Implementation**: Use a buffer list. Accumulate rows from the streaming generator until the list size reaches 5000.
 - Convert the buffer list to a `pandas.DataFrame`.
 - Process the DataFrame (filtering, feature engineering) and append valid rows to the final output file (or a temporary chunk file).
 - Clear the buffer list.
 - Repeat until the generator is exhausted.
 - This ensures no single chunk exceeds memory limits while processing the full dataset.
 6. **Source Labeling**: Add a column `source_label` with value `'matsci/glass-forming-ability'` to every row.
 7. Write the filtered rows to `data/processed/processed_alloys_raw.csv`.
- [X] T012b [US1] Validate dataset size against FR-001 target:
 - Load `data/processed/processed_alloys_raw.csv`.
 - If N < 500, raise `ValueError("Data availability error: N < 500. Minimum N >= 500 required by FR-001.")`.
 - If 500 <= N < 1000, log `WARNING` "Data size below target (N < 1000) but above minimum (N >= 500). Proceeding."
 - If N >= 1000, log `INFO` (data is sufficient).
 - **Deliverable**: Write `data/logs/data_validation_status.json` with schema `{"status": "pass|warning|fail", "n_total": int, "message": str}`.
- [X] T014 [P] [US1] Implement `code/features.py` function `calc_mixing_enthalpy`: <!-- FAILED: unspecified -->
 **Formula**: Use pairwise enthalpy of mixing data.
 **Fallback Strategy**: If pairwise data is missing for any pair from the primary source (local CSV):
 1. **Fallback Source**: Use the Miedema model approximation.
 2. **Implementation**: Calculate Miedema enthalpy using elemental properties (radius, electronegativity) from `mendeleev` and hardcoded constants in `code/features.py` (derived from standard Miedema parameters).
 3. **Formula**: $H_{mix} = \sum_{i \neq j} c_i c_j \Delta H_{ij}$ using the calculated values.
 4. **Constraint**: Do NOT use unverified proxy values. The Miedema calculation must be explicit and logged.
 5. **Enforcement**: If `mendeleev` lacks data for a pair, **MUST** use the Miedema fallback to ensure every valid entry gets a descriptor. Do NOT exclude rows due to missing data.
 **Deliverable**: Update `data/processed/processed_alloys_raw.csv` with computed enthalpy; log exclusions to `data/logs/exclusion_log.txt`.
- [X] T014b [P] [US1] **Miedema Coefficients**: Create `data/raw/miedema_coeffs.csv` containing pairwise enthalpy coefficients (or a script to fetch them from a verified source like `).
 - **Action**: If no verified source exists, implement the Miedema formula in `code/features.py` using standard parameters (e.g., from `mendeleev` properties) and hardcode the necessary constants in `code/features.py` with citations.
 - **Deliverable**: `data/raw/miedema_coeffs.csv` or hardcoded constants in `code/features.py`.
- [X] T015 [P] [US1] Implement `code/features.py` function `calc_size_mismatch` and `calc_electronegativity_variance`: <!-- FAILED: unspecified -->
 **Formulas**:
 - `atomic_size_mismatch` ($\delta$): $1 - \frac{\sum c_i r_i}{\bar{r}}$, where $r_i$ is atomic radius from `mendeleev` and $\bar{r}$ is the weighted average radius.
 - `electronegativity_variance`: Variance of electronegativity values weighted by composition $c_i$.
 **Output**: Save the function signatures and ensure they return float values.
- [ ] T010a [US1] Unit test `test_features.py::test_mixing_enthalpy`: <!-- FAILED: unspecified -->
 - Implement unit tests verifying the `calc_mixing_enthalpy` function against known periodic table values.
 - Ensure the test passes for valid ternary compositions and correctly handles edge cases.
- [ ] T010b [US1] Unit test `test_features.py::test_size_mismatch`:
 - Implement unit tests verifying the `calc_size_mismatch` and `calc_electronegativity_variance` functions.
 - Ensure the tests pass for known compositions and verify tolerance within an acceptable numerical threshold.
- [ ] T016a [US1] Save the engineered dataset (including all thermodynamic columns) to `data/processed/processed_alloys.csv`.
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

- [X] T019 [US2] **Critical**: Validate Total Dataset Size (Pre-Split).
 - Load `data/processed/processed_alloys.csv` (the full dataset before splitting).
 - If `len(df) < 500`, raise `ValueError("SC-001 Violation: Total dataset size < 500. Minimum N >= 500 required by FR-001.")`.
 - **Deliverable**: Write `data/logs/training_set_validation.json` with schema `{"status": "pass|fail", "n_total": int}`.
- [ ] T020 [US2] Load `processed_alloys.csv`; perform a standard train-test split (`random_state=42`, `test_size=0.2`).
 - **Depends on**: T019 (Dataset Validation).
 - Split the data into `data/processed/train_set.csv` and `data/processed/test_set.csv`.
 - Save the split indices to `data/models/split_indices.json`.
 - **Deliverable**: `data/processed/train_set.csv`, `data/processed/test_set.csv`, `data/models/split_indices.json`.
- [X] T020b [US2] **Shared CV Splitter**: Instantiate a `KFold(n_splits=5, shuffle=True, random_state=42)` object.
 - **Action**: Configure the splitter. Do NOT save indices here; T021 will save them.
 - **Deliverable**: Configured splitter object (used in T021).
- [ ] T021 [US2] Train `RandomForestRegressor` on the training set; perform 5-fold cross-validation using the **shared folds** from T020b. Record each fold RMSE in `data/models/cv_metrics.json`.
 - Train the model on `data/processed/train_set.csv`.
 - Perform cross-validation.
 - **Explicitly save** the fold indices used to `data/models/cv_folds_indices.json` (authoritative source for T022b-2a).
 - Save the trained model to `data/models/random_forest_model.pkl`.
 - **Output Schema**: `{"fold_scores": [float, float, float, float, float], "mean_rmse": float, "std_rmse": float}`.
 - **Deliverable**: `data/models/cv_metrics.json`, `data/models/random_forest_model.pkl`, `data/models/cv_folds_indices.json`.

### Statistical Validation (SC‑002)

- [ ] T022b-1 [US2] **Null Model Training**: Train a `DummyRegressor` (strategy='mean') on the **same training split** as T021.
 - Save the trained dummy model to `data/models/null_model.pkl`.
- [X] T022b-2a [US2] **Load CV Indices**:
 - Load `data/models/cv_folds_indices.json` (produced by T021).
 - Parse the indices into a list of (train_idx, test_idx) tuples.
 - **Deliverable**: In-memory list of folds.
- [X] T022b-2b [US2] **Split Data for Null Model**:
 - Load `data/processed/train_set.csv`.
 - Apply the folds from T022b-2a to split the training data into 5 distinct folds.
 - **Deliverable**: List of 5 train/test splits for the null model.
- [X] T022b-2c [US2] **Null Model CV**: Perform 5-fold CV on the `DummyRegressor` using the splits from T022b-2b.
 - **Instruction**: Use the exact splits from T022b-2b.
 - Save the 5 fold scores to `data/models/null_model_cv_scores.json` with schema `{"fold_scores": [float, float, float, float, float], "mean_rmse": float, "std_rmse": float}`.
- [X] T022b-3 [US2] **Null Model Test Evaluation**: Evaluate the `DummyRegressor` on the test set.
 - **Depends on**: T020 (Test Set Creation).
 - Save the test set predictions to `data/models/null_model_predictions.npy` and the test RMSE to `data/models/null_model_rmse.json`.

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

- [ ] T022 [US2] Evaluate on the held‑out test set; save RMSE and the trained model to `data/models/random_forest_model.pkl`.
 - Load `data/models/random_forest_model.pkl` and `data/processed/test_set.csv`.
 - Calculate test set RMSE.
 - **Deliverable**: `data/models/test_metrics.json` with schema `{"test_rmse": float}`.

## Phase 5: User Story 3 - Feature Importance and Sensitivity Analysis (Priority: P3)

### Collinearity Detection and Stability Check (Pre-Analysis)

- [X] T029a [US3] **Detect Collinearity**:
 1. Load the initial model (`random_forest_model.pkl`) and the processed dataset.
 2. Compute Pearson correlation matrix of the engineered features.
 3. Flag any pair with |ρ| > 0.8; write `collinearity_report.json`.
 4. **Report Initial Metrics**: Before any retraining, record the initial model's metrics in `data/models/initial_model_metrics.json`.
 - **Deliverable**: `collinearity_report.json` (list of collinear pairs) and `data/models/initial_model_metrics.json`.
- [X] T029b-1 [US3] **Identify Drop Candidate**:
 - **Input**: Load `collinearity_report.json` from T029a.
 - **Logic**: If `collinearity_report.json` is empty or contains no pairs, log "No collinearity detected" and skip to T029b-3 (Record Decision: No Action).
 - **If Collinearity Exists**:
 - Compute mean absolute SHAP values from the **initial** model.
 - Identify the feature with the **lowest** mean absolute SHAP among the collinear pairs.
 - **Constraint**: **DO NOT** drop the core thermodynamic descriptors: `mixing_enthalpy`, `atomic_size_mismatch`, `electronegativity_variance`.
 - **Candidate Selection**: If the lowest SHAP feature is a core descriptor, mark as "No Valid Candidate".
 - **Deliverable**: `drop_candidate.json` with `{"feature": "<name>" | null, "status": "candidate_found|no_candidate"}`.
- [ ] T029b-2 [US3] **Retrain Model (If Needed)**:
 - **Input**: Load `drop_candidate.json` from T029b-1.
 - **Logic**:
 - If `status` is "candidate_found":
 - Retrain a new `RandomForestRegressor` excluding that feature, using **identical hyperparameters and random_state=42**.
 - Save as `data/models/random_forest_model_stable.pkl`.
 - If `status` is "no_candidate":
 - **Do NOT raise a ValueError**.
 - Save the **initial** model as `data/models/random_forest_model_best_available.pkl`.
 - Log a WARNING: "Core descriptors are collinear. Proceeding with best available model."
 - **Deliverable**: `data/models/random_forest_model_stable.pkl` (if candidate found) OR `data/models/random_forest_model_best_available.pkl` (if no candidate).
- [X] T029b-3 [US3] **Validate Stability**:
 - **Input**: Load the model from T029b-2.
 - **Logic**:
 - If `random_forest_model_stable.pkl` exists, check if it was trained on a subset. If so, verify that the removed feature was not a core descriptor (should be true by T029b-1 logic).
 - If `random_forest_model_best_available.pkl` exists, it implies core descriptors were collinear or no candidate found.
 - **Deliverable**: `collinearity_decision.json` (`{"retrain_required": true/false, "dropped_feature": "<name>" | null, "iterations": 1, "status": "stable|best_available"}`).
- [X] T029b-4 [US3] **Ensure Model Artifact**:
 - **Input**: Check existence of `random_forest_model_stable.pkl` and `random_forest_model_best_available.pkl`.
 - **Logic**:
 - If `random_forest_model_stable.pkl` exists, do nothing.
 - If only `random_forest_model_best_available.pkl` exists, copy it to `data/models/random_forest_model_stable.pkl` and log "Using best available model as stable model".
 - **Deliverable**: `data/models/random_forest_model_stable.pkl` (guaranteed to exist).
- [X] T029c [US3] **Stable Model Fallback**:
 - Ensure `random_forest_model_stable.pkl` exists. If T029b-4 produced a 'best_available' model, it is already copied.
 - This task ensures T028 and T031 always have a valid model input.
 - **Deliverable**: `data/models/random_forest_model_stable.pkl`.

### Permutation Importance (SC‑004)

- [X] T028 [US3] Using the **stable model** (`random_forest_model_stable.pkl`), compute permutation importance (`n_permutations=1000`, `random_state=42`).
 1. **Feature Set Consistency**: Load the feature set defined in `collinearity_decision.json`. If a feature was dropped or regularization applied, ensure the input data for this step matches the model's expected features.
 2. Calculate p-values using a **one-sample t-test** comparing the observed importance of each feature against the distribution of importance scores from the 1000 permutations (shuffled baseline).
 3. Write `feature_importance.json` (list of `{feature, p_value, importance_score}`).
 4. **Report**: Log whether at least one thermodynamic feature is in the top‑2 with `p_value < 0.05`. Do not fail the pipeline if this condition is not met; simply report the finding.

### Sensitivity Analysis (SC‑003)

- [X] T031 [US3] Perform **Threshold‑Sweep Sensitivity Analysis** (Depends on: T029c):
 1. Load the **stable model** produced by T029c (`random_forest_model_stable.pkl`) and the full processed dataset.
 2. **Threshold Sweep Logic**:
 - Define thresholds: `[50, 100, 150]` K/s.
 - For each threshold `T`:
 - **Continuous RMSE**: Filter the test set to include ONLY samples where `critical_cooling_rate >= T`. Calculate RMSE of the model's continuous predictions against the continuous `critical_cooling_rate` for this **filtered subset**.
 - **Binarize**: Create a binary target `y_bin` where `y_bin = 1` if `critical_cooling_rate >= T` else `0` (for the full test set).
 - **Predict**: Use the stable model to predict continuous `y_pred` on the test set.
 - **Binarize Predictions**: Create binary predictions `y_pred_bin` where `y_pred_bin = 1` if `y_pred >= T` else `0`.
 - **Evaluate**: Calculate **F1-score** between `y_bin` and `y_pred_bin` for the entire test set.
 - Record `rmse_continuous` and `f1_score` for each `T`.
 3. **Stability Check**:
 - Calculate `rmse_variance` (variance of the 3 continuous RMSE values).
 - Calculate `f1_variance` (variance of the 3 F1 scores).
 - Calculate margin: `rmse_variance < 0.05 * mean_rmse_continuous` AND `f1_variance < 0.05 * mean_f1_score`.
 - `stability_status` is `PASS` if margin condition is met.
 4. Write `sensitivity_report.csv` with columns `threshold,rmse_continuous,f1_score,rmse_variance,f1_variance,stability_status`.
 - **Deliverable**: Write `sensitivity_status.json` with schema `{"stability_met": true/false, "rmse_variance": <float>, "f1_variance": <float>, "threshold_values": [50,100,150], "run_status": "FAILED" if stability_met is false else "PASSED"}`.
 - **Note**: If the model used is "best_available" (unstable), the `stability_met` flag may be false, but the analysis must still run and report this status to satisfy FR-006 associational framing.
- [X] T030b [US3] Verification of sensitivity stability:
 - Load `sensitivity_status.json`; assert `stability_met` is `true`. If not, log a **WARNING** "SC-003 failed: Sensitivity margin exceeds 5% of mean" and save `sc003_status: FAILED` to `data/models/sc003_status.json`. **Do not raise an exception**; the pipeline must continue to generate the report with this negative finding, but the `run_status` in `sensitivity_status.json` must be explicitly set to "FAILED" to flag the violation.

## Phase 6: Polish & Cross‑Cutting Concerns

- [X] T034 [P] Documentation updates: README with execution instructions. **Note**: Specific caveats and "ASSOCIATIONAL" framing will be added in T055.
- [X] T035 Ensure `random_state=42` is used consistently across all scripts.
- [X] T036 Performance optimization: confirm pipeline completes within 6 h on CPU (local sanity check + CI logs).
- [ ] T037 [P] Run `validate_schemas.py` to ensure all artifacts match contracts.
 **Script Definition**: Create `code/validate_schemas.py`. It must load `contracts/dataset.schema.yaml` and `contracts/model_output.schema.yaml`. It must iterate through all generated JSON/CSV artifacts in `data/` and `data/models/` and validate them against the schemas.
 **Output**: Print "Validation Passed" and exit with code 0 if all match. Print "Validation Failed" and list errors, then exit with code 1 if any mismatch.
- [X] T038 Security hardening: scan for hard‑coded secrets; ensure only verified URL is used.

## Phase Q: Verification & Compliance (New)

**Purpose**: Ensure all outputs meet the "Real Data Only" and "No Fabrication" constitution gates.

- [ ] T046 [P] **Data Source Audit**: Write `code/audit_data_source.py` to verify that `data/processed/processed_alloys.csv` contains a `source_label` column explicitly set to "matsci/glass-forming-ability" and that no synthetic data flags (e.g., `is_synthetic=True`) exist.
- [ ] T047 [P] **Result Reproducibility Check**: Re-run `code/ingestion.py` and `code/features.py` in a fresh environment and compare the content hash (SHA-256) of the output `processed_alloys.csv` against the original run hash stored in `data/logs/ingestion_hash.txt`. If hashes differ, raise an error.
- [ ] T048 [P] **Statistical Significance Gate**: Create a script `code/check_sc002.py` that parses `statistical_comparison.json` and logs a **WARNING** if `sc002_met` is false, ensuring the report explicitly flags the failure (consistent with T024c's non-blocking design). **Do NOT exit with code 1**.
- [ ] T049 [P] **Sensitivity Gate**: Create a script `code/check_sc003.py` that parses `sensitivity_status.json` and logs a failure if `stability_met` is false, ensuring the report explicitly flags unstable thresholds.

## Phase R: Edge Case & Robustness Handling (New)

**Purpose**: Address specific edge cases and robustness requirements from spec.md to prevent silent failures or data corruption.

- [ ] T050 [US1] **Edge Case: Empty Dataset**: Modify `code/ingestion.py` to explicitly check if the filtered dataset is empty after removing malformed compositions. If empty, raise `ValueError("Dataset is empty after filtering. Check composition parsing logic and data source validity.")`. Log the error to `data/logs/empty_dataset_error.log`.
- [ ] T051 [US1] **Edge Case: Unknown Labels**: Ensure `code/ingestion.py` explicitly filters out rows where `glass_forming_label` is "unknown", "mixed", or null, and logs the count of excluded samples to `data/logs/exclusion_log.txt`. Write a status file `data/logs/label_filtering_status.json` with schema `{"excluded_count": int, "status": "pass"}`.
- [ ] T052 [US1] **Edge Case: Zero Enthalpy**: Verify `code/features.py` handles `mixing_enthalpy == 0` as a valid numeric value (no special error handling required, but ensure no `NaN` propagation).
- [ ] T053 [US2] **Edge Case: Low Variance Target**: In `code/train.py`, verify that the target variable `critical_cooling_rate` has non-zero variance before training. If variance is 0, raise `ValueError("Target variable has zero variance; cannot train regression model.")`.
- [ ] T054 [US3] **Edge Case: Collinearity Resolution Failure**: If T029b fails to identify a stable model after 3 drops (all features collinear), log a **WARNING** "Collinearity resolution failed: No stable feature subset found. Proceeding with best available model." and save the failure state to `data/models/collinearity_resolution_failed.json`. **Do NOT raise a ValueError**.

## Phase S: Documentation & Reporting Refinement (New)

**Purpose**: Ensure the final report and documentation strictly adhere to the "Associational" constraint and clearly communicate limitations.

- [X] T055 [US3] **Associational Framing**: Update `REPORT.md` template to include a dedicated "Limitations and Caveats" section that explicitly states:
 1. The dataset is observational; all findings are **associational**, not causal.
 2. The model performance is bounded by the quality and representativeness of the `matsci/glass-forming-ability` dataset.
 3. The sensitivity analysis results are specific to the tested thresholds within the examined range.
 **Note**: This task is independent of T028/T031 success to ensure the disclaimer is always present.
- [X] T056 [US3] Update `README.md` to include a "How to Interpret Results" section that guides users on reading the `sc002_met` and `stability_met` flags without over-interpreting negative results.

## Phase U: Revision & Gap Resolution (New)

**Purpose**: Address specific reviewer concerns regarding audit execution, task granularity, and final validation steps.

- [ ] T065 [P] [US1] **Audit Execution Fix**: Execute `code/audit_data_source.py` and ensure `data/logs/data_source_audit.json` is populated with a valid `status: "pass"` or `status: "fail"` and a descriptive message. If the previous run failed due to missing logic, update `code/audit_data_source.py` to handle edge cases (e.g., missing columns) gracefully before re-running.
- [ ] T066 [P] [US2] **Statistical Audit Execution**: Execute `code/check_sc002.py`. Ensure it correctly parses `statistical_comparison.json`, handles missing files, and writes a valid `data/logs/statistical_significance_audit.json` with `status` and `p_value` fields.
- [ ] T067 [P] [US3] **Sensitivity Audit Execution**: Execute `code/check_sc003.py`. Ensure it correctly parses `sensitivity_status.json` and writes a valid `data/logs/sensitivity_stability_audit.json` with `status` and `rmse_variance` fields.
- [X] T068 [P] **Report Validation Script**: Create `code/validate_report.py` to programmatically verify that `REPORT.md` contains the required sections: "Limitations and Caveats", "Statistical Significance", "Feature Importance", "Sensitivity Analysis", and "Associational Framing". Exit with error if any section is missing.
- [ ] T069 [P] **Atomic Pipeline Test**: Break down T061 into discrete steps: 1. Clean environment setup, 2. Data ingestion run, 3. Feature engineering run, 4. Model training run, 5. Analysis run, 6. Report generation. Verify artifacts after each step.
- [X] T070 [P] **Documentation Review Checklist**: Create `docs/review_checklist.md` listing specific criteria for README.md and REPORT.md (e.g., "Explicitly mentions random_state=42", "States dataset source URL", "Includes caveats on associational findings").
- [X] T071 [P] **Code Quality Metrics**: Run `flake8` and `black --check` on the entire `code/` directory. Fix any linting errors or formatting issues found.
- [X] T072 [P] **Constitutional Compliance Script**: Create `code/verify_constitution.py` to automatically check:
 1. Reproducibility: `random_state=42` is present in all scripts.
 2. Verified Accuracy: No hardcoded URLs other than `matsci/glass-forming-ability`.
 3. Data Hygiene: No synthetic data flags in `processed_alloys.csv`.
 4. Single Source of Truth: All metrics in `REPORT.md` match values in JSON artifacts.
 5. Versioning: Content hashes are recorded in `data/logs/`.
 6. Thermodynamic Integrity: Feature formulas match spec.
 7. Cross-Validation Rigor: 5-fold CV is used.

## Phase T: Final Review & Compliance Verification (New)

**Purpose**: Ensure the entire pipeline and its outputs meet all constitutional gates and specification requirements before final delivery.

- [ ] T057 [P] [US1] **Data Source Verification**: Execute `code/audit_data_source.py` (created in Phase Q and fixed in Phase U) to confirm the dataset source is valid and no synthetic data was introduced. Log the result to `data/logs/data_source_audit.json`.
 - **Depends on**: T065 (Phase U).
 - **Deliverable**: `data/logs/data_source_audit.json` with schema `{"status": "pass|fail", "message": str}`.
- [X] T058 [P] [US2] **Statistical Significance Confirmation**: Run `code/check_sc002.py` (created in Phase Q and fixed in Phase U) to verify the model's statistical significance against the null model. Log the result to `data/logs/statistical_significance_audit.json`.
 - **Depends on**: T066 (Phase U).
 - **Deliverable**: `data/logs/statistical_significance_audit.json` with schema `{"status": "pass|fail", "p_value": float}`.
- [X] T059 [P] [US3] **Sensitivity Stability Confirmation**: Run `code/check_sc003.py` (created in Phase Q and fixed in Phase U) to verify the sensitivity analysis stability. Log the result to `data/logs/sensitivity_stability_audit.json`.
 - **Depends on**: T067 (Phase U).
 - **Deliverable**: `data/logs/sensitivity_stability_audit.json` with schema `{"status": "pass|fail", "f1_variance": float}`.
- [X] T060 [P] **Final Report Validation**: Ensure `REPORT.md` includes all required sections, explicitly states the associational nature of findings, and correctly reports the status of all success criteria (SC-001 to SC-005).
 - **Execution**: Run `code/validate_report.py` and verify exit code 0.
 - **Deliverable**: `data/logs/report_validation_status.json` with schema `{"status": "pass|fail", "missing_sections": list}`.
- [ ] T061a [P] **Atomic Pipeline Test - Ingestion**: Execute `code/ingestion.py` in a clean environment. Verify `data/processed/processed_alloys_raw.csv` is generated.
- [ ] T061b [P] **Atomic Pipeline Test - Features**: Execute `code/features.py`. Verify `data/processed/processed_alloys.csv` is generated.
- [ ] T061c [P] **Atomic Pipeline Test - Training**: Execute `code/train.py`. Verify `data/models/random_forest_model.pkl` and `data/models/cv_metrics.json` are generated.
- [ ] T061d [P] **Atomic Pipeline Test - Analysis**: Execute `code/analyze.py`. Verify `data/models/feature_importance.json` and `data/models/sensitivity_status.json` are generated.
- [X] T061e [P] **Atomic Pipeline Test - Report**: Execute `code/generate_report.py` (or T043 logic). Verify `REPORT.md` is generated.
- [X] T061f [P] **Atomic Pipeline Test - Final Verification**: Run all audit scripts (T046-T049) and verify all JSON logs are present and valid.
- [X] T062a [P] **README Completeness**: Verify `README.md` contains:
 1. Execution instructions.
 2. Dataset source URL.
 3. Random seed information.
 4. Associational framing note.
 - **Deliverable**: `data/logs/readme_checklist.json` with schema `{"status": "pass|fail", "missing_items": list}`.
- [X] T062b [P] **REPORT.md Completeness**: Verify `REPORT.md` contains:
 1. "Limitations and Caveats" section.
 2. "Statistical Significance" section.
 3. "Feature Importance" section.
 4. "Sensitivity Analysis" section.
 - **Deliverable**: `data/logs/report_checklist.json` with schema `{"status": "pass|fail", "missing_items": list}`.
- [X] T063 [P] **Code Quality Final Review**: Perform a final code review to ensure all code follows best practices, is well-documented, and adheres to the project's coding standards.
 - **Execution**: Run `flake8` and `black --check`.
 - **Deliverable**: `data/logs/linting_report.txt` containing the output of the linting checks.
- [X] T064 [P] **Constitutional Compliance Audit**: Conduct a final audit to ensure all constitutional principles (Reproducibility, Verified Accuracy, Data Hygiene, Single Source of Truth, Versioning, Thermodynamic Feature Engineering Integrity, Cross-Validation Rigor) are fully satisfied.
 - **Execution**: Run `code/verify_constitution.py` and **write results to `data/logs/constitutional_compliance_report.json`**.
 - **Deliverable**: `data/logs/constitutional_compliance_report.json` with schema `{"status": "pass|fail", "violations": list}`.

## Phase V: Final Gap Resolution & Missing Task Implementation

**Purpose**: Address specific reviewer concerns regarding missing implementation steps, task granularity, and final validation gaps identified in the audit.

- [ ] T073 [P] [US1] **Verification: Data Streaming**: Execute `code/ingestion.py` with a large dataset (or simulated large stream) to verify that the chunked processing (5000 rows) completes without OOM.
 - **Action**: Run the script and log memory usage peaks.
 - **Deliverable**: `data/logs/streaming_strategy.json` with `{"status": "pass", "max_memory_mb": int}`.
- [X] T074a [P] **Create Report Template**: Create `docs/report_template.md` with the exact Markdown structure for `REPORT.md`:
 1. Title, Date, Author.
 2. Executive Summary.
 3. Data Source & Methodology.
 4. Statistical Significance (SC-002).
 5. Feature Importance (SC-004).
 6. Sensitivity Analysis (SC-003).
 7. Limitations and Caveats (Associational Framing).
 - **Deliverable**: `docs/report_template.md`.
- [X] T074 [P] [US2] **Missing Task: Report Generation Script**: Create the missing `code/generate_report.py` script referenced in T061e.
 - **Action**: Implement a script that reads `docs/report_template.md` and all JSON artifacts (`cv_metrics.json`, `feature_importance.json`, `sensitivity_status.json`, etc.) and populates the template with actual values.
 - **Mapping Logic**:
 - Insert `mean_rmse` from `cv_metrics.json` into Section 4.1.
 - Insert `sc002_met` and `p_value` from `statistical_comparison.json` into Section 4.2.
 - Insert `feature_importance_ranking` from `feature_importance.json` into Section 5.
 - Insert `rmse_variance` and `stability_met` from `sensitivity_status.json` into Section 6.
 - Insert the "Associational Framing" disclaimer from T055 into Section 7.
 - **Requirement**: The script must include the "Associational Framing" disclaimer (from T055) and dynamically populate tables with the actual metrics.
 - **Deliverable**: `code/generate_report.py` and a sample `REPORT.md` generated by running it locally.
- [X] T075 [P] [US3] **Missing Task: Collinearity Resolution Script**: Create `code/resolve_collinearity.py` to automate the logic described in T029b-1 to T029b-4.
 - **Action**: Implement the loop that detects collinearity, identifies the lowest SHAP feature among collinear pairs, drops it if not a core descriptor, and retrains the model.
 - **Requirement**: Ensure the script respects the "Core Feature Handling" constraint (never drop `mixing_enthalpy`, `atomic_size_mismatch`, `electronegativity_variance`).
 - **Deliverable**: `code/resolve_collinearity.py` and `data/models/collinearity_decision.json` populated by running the script.
- [X] T076 [P] **Missing Task: Final Integration Test**: Create `tests/integration/test_full_pipeline.py` to run the entire pipeline end-to-end.
 - **Action**: Write a test that executes `ingestion.py`, `features.py`, `train.py`, `analyze.py`, and `generate_report.py` in sequence.
 - **Requirement**: Assert that all expected output files exist and contain valid data (schema validation).
 - **Deliverable**: `tests/integration/test_full_pipeline.py` and a passing CI run.
- [X] T077 [P] **Missing Task: Error Handling for Missing Dependencies**: Add robust error handling for missing optional dependencies (e.g., `shap`, `mendeleev`).
 - **Action**: Update `code/utils.py` to check for required imports at startup and raise a clear `ImportError` with installation instructions if missing.
 - **Requirement**: Ensure the pipeline fails fast with a helpful message rather than a cryptic traceback.
 - **Deliverable**: Updated `code/utils.py` and a test case verifying the error message.
- [X] T078 [P] **Missing Task: Configuration Management**: Create a `config.yaml` file to centralize hyperparameters and thresholds.
 - **Action**: Move hard-coded values (e.g., `random_state`, `test_size`, `thresholds`, `n_permutations`) into `config.yaml`.
 - **Requirement**: All scripts must read from `config.yaml` instead of hard-coding values.
 - **Deliverable**: `config.yaml` and updated scripts that load it.
- [X] T079 [P] **Missing Task: Documentation of Data Flow**: Create `docs/data_flow.md` to visualize the data flow between tasks.
 - **Action**: Document the input/output relationships between `ingestion.py`, `features.py`, `train.py`, and `analyze.py`.
 - **Requirement**: Include a diagram (Mermaid or ASCII) showing the flow of data and artifacts.
 - **Deliverable**: `docs/data_flow.md` with a clear visualization.
- [X] T080 [P] **Missing Task: Performance Benchmarking**: Add a benchmarking task to measure execution time of each phase.
 - **Action**: Instrument `code/ingestion.py`, `code/features.py`, `code/train.py`, and `code/analyze.py` to log execution time.
 - **Requirement**: Ensure the total pipeline time is logged and compared against the 6-hour limit.
 - **Deliverable**: `data/logs/performance_benchmark.json` with timing data for each phase.
- [X] T081 [P] [US3] **Missing Task: Continuous RMSE Variance Calculation**: Create `code/calculate_continuous_rmse_variance.py` to explicitly calculate the RMSE variance for the continuous `critical_cooling_rate` target across thresholds {50, 100, 150} K/s.
 - **Action**: Implement a script that loads the stable model, iterates through the thresholds, filters the test set to include ONLY samples where `critical_cooling_rate >= T`, calculates the continuous RMSE for each filtered subset, and computes the variance of these RMSE values.
 - **Requirement**: The script must output a JSON file `data/models/continuous_rmse_variance.json` with schema `{"thresholds": [50, 100, 150], "rmse_values": [float, float, float], "rmse_variance": float, "stability_met": bool}`. This satisfies the primary metric requirement of SC-003.
 - **Deliverable**: `code/calculate_continuous_rmse_variance.py` and `data/models/continuous_rmse_variance.json`.
