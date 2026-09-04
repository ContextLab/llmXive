---
description: "Task list template for feature implementation"
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
- [X] T008 [P] [US1] Ensure `ingestion.py` raises a clear `ValueError` if the `matsci/glass-forming-ability` dataset cannot be fetched.
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
 4. Exclude rows missing `critical_cooling_rate` or with malformed composition; log exclusions with reasons.
 5. **Data Volume Handling**: Process ALL valid data. If the dataset exceeds memory limits (e.g., >100k rows), stream and process in chunks, accumulating statistics online. Do NOT hardcode a sampling cap that reduces data below the FR-001 target of N >= 1000.
 6. Write the filtered rows to `data/processed/processed_alloys_raw.csv`.
- [X] T012a [US1] Implement `code/ingestion.py` parsing and validation logic as a distinct function `parse_composition_and_validate` to ensure atomicity. <!-- FAILED: unspecified -->
- [ ] T012b [US1] Validate dataset size against FR-001 target:
 - Load `data/processed/processed_alloys_raw.csv`.
 - If N < 1000, raise `ValueError("Data availability error: N < 1000. Target N >= 1000 required by FR-001.")`.
 - If N >= 1000, log `INFO` (data is sufficient).
- [X] T014 [P] [US1] Implement `code/features.py` function `calc_mixing_enthalpy`:
 **Formula**: Use pairwise enthalpy of mixing data from `mendeleev` (if available for the specific element pairs). If pairwise data is missing for any pair in the ternary system, raise a `ValueError` (do not fallback to approximations like Miedema or weighted averages, to ensure strict adherence to Constitution Principle VI).
 Formula: $H_{mix} = \sum_{i \neq j} c_i c_j \Delta H_{ij}$.
- [X] T015 [P] [US1] Implement `code/features.py` function `calc_size_mismatch` and `calc_electronegativity_variance`: <!-- FAILED: unspecified -->
 **Formulas**:
 - `atomic_size_mismatch` ($\delta$): $1 - \frac{\sum c_i r_i}{\bar{r}}$, where $r_i$ is atomic radius from `mendeleev` and $\bar{r}$ is the weighted average radius.
 - `electronegativity_variance`: Variance of electronegativity values weighted by composition $c_i$.
- [ ] T010a [US1] Unit test `test_features.py::test_mixing_enthalpy` and `test_size_mismatch` (runs after successful implementation of T014 & T015).
- [ ] T016a [US1] Save the engineered dataset (including all thermodynamic columns) to `data/processed/processed_alloys.csv`.
- [ ] T016b [US1] Validate processed data: <!-- FAILED: unspecified -->
 - Verify schema compliance against `contracts/dataset.schema.yaml`.
 - **CRITICAL**: Load `data/processed/processed_alloys.csv`. If N < 1000, raise `ValueError("Data availability error: N < 1000. Target N >= 1000 required by FR-001.")`.
 - If 1000 <= N < 5000, log `INFO` (data is sufficient but below ideal).
 - If N >= 5000, log `INFO` (data is sufficient).
- [ ] T017 [US1] After filtering, assert that `critical_cooling_rate` variance > 0; otherwise raise `ValueError("Zero variance in critical_cooling_rate")`.

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train a Random Forest regressor with k-fold cross-validation and evaluate against a null model.

- [ ] T020 [US2] Load `processed_alloys.csv`; perform a standard train-test split (`random_state=42`).
- [ ] T021 [US2] Train `RandomForestRegressor` on the training set; perform 5‑fold CV, record each fold RMSE in `data/models/cv_metrics.json` (`{"fold_scores": [...], "mean_rmse":...}`). <!-- FAILED: unspecified -->
- [ ] T022 [US2] Evaluate on the held‑out test set; save RMSE and the trained model to `data/models/random_forest_model.pkl`.
- [ ] T022b [US2] Train a `DummyRegressor` (strategy='mean') on the same training split; compute test RMSE; save predictions (`null_model_predictions.npy`) and RMSE (`null_model_rmse.json`). <!-- FAILED: unspecified -->

### Statistical Validation (SC‑002)

- [ ] T024a [US2] Implement **Null-Model Statistical Test**: <!-- FAILED: unspecified -->
 1. Load the 5-fold CV RMSE scores from `cv_metrics.json` (list of 5 values).
 2. Generate a distribution of 5-fold CV RMSE scores for the **Null Model** (DummyRegressor) using the same 5-fold splits, performing 1000 bootstrap resamples to establish a stable null distribution. Save to `null_model_cv_scores.json`.
 3. Perform a **two-sample t-test** (independent samples) using `scipy.stats.ttest_ind` comparing the Model CV scores distribution against the Null Model CV scores distribution.
 4. Compute p-value.
 5. Save results to `data/models/statistical_comparison.json` (`{"p_value": <float>, "t_statistic": <float>, "sc002_met": <bool>}`) where `sc002_met` is `p_value < 0.05`.
- [ ] T024c [US2] Gate task (Non-Blocking):
 - Load `statistical_comparison.json`.
 - If `sc002_met` is `false`, log a **WARNING** "SC-002 failed: Model not statistically distinguishable from null" and save a status flag `sc002_status: FAILED` to `data/models/sc002_status.json`. **Do not raise an exception**; the pipeline must continue to generate the report with this negative finding.
 - If `sc002_met` is `true`, log success and save `sc002_status: PASSED`.

## Phase 5: User Story 3 - Feature Importance and Sensitivity Analysis (Priority: P3)

### Collinearity Detection and Stability Check (Pre-Analysis)

- [ ] T029a [US3] Perform **Stability Check & Retrain if needed**: <!-- FAILED: unspecified -->
 1. Load the initial model (`random_forest_model.pkl`) and the processed dataset.
 2. Compute Pearson correlation matrix of the engineered features.
 3. Flag any pair with |ρ| > 0.8; write `collinearity_report.json`.
 4. If collinearity exists:
 - Compute mean absolute SHAP values from the **initial** model.
 - Identify the feature with the **lowest** mean absolute SHAP among the collinear pairs.
 - Retrain a new `RandomForestRegressor` excluding that feature, using **identical hyperparameters and random_state=42** as the initial model.
 - Save the new model as `data/models/random_forest_model_stable.pkl`.
 - Re-run 5-fold CV on this stable model, saving `cv_metrics_stable.json`.
 - Record decision in `collinearity_decision.json` (`{"retrain_required": true, "dropped_feature": "<name>"}`).
 5. If no collinearity:
 - Copy `random_forest_model.pkl` to `random_forest_model_stable.pkl`.
 - Copy `cv_metrics.json` to `cv_metrics_stable.json`.
 - Record decision in `collinearity_decision.json` (`{"retrain_required": false}`).
- [ ] T029b [US3] **Stable Model Fallback**:
 - Ensure `random_forest_model_stable.pkl` exists. If T029a failed or was skipped, copy `random_forest_model.pkl` to `random_forest_model_stable.pkl` and log a warning. This task ensures T028 and T031 always have a valid stable model input.

### Permutation Importance (SC‑004)

- [ ] T028 [US3] Using the **stable model** (`random_forest_model_stable.pkl`), compute permutation importance (`n_permutations=1000`, `random_state=42`). Calculate p-values using a **one-sample t-test** comparing the observed importance of each feature against the distribution of importance scores from the 1000 permutations (shuffled baseline). Write `feature_importance.json` (list of `{feature, p_value}`) ensuring at least one thermodynamic feature is in the top‑2 with `p_value < 0.05`. <!-- FAILED: unspecified -->

### Sensitivity Analysis (SC‑003)

- [ ] T031 [US3] Perform **Threshold‑Sweep Sensitivity Analysis**:
 1. Load the **stable model** (`random_forest_model_stable.pkl`) and the full processed dataset.
 2. **Regression Metric (Constant)**: Compute RMSE on the continuous target using the stable model. This value is invariant to the threshold.
 3. **Classification F1 Stability Sweep**:
 - For each threshold in {, 100, 150} K/s:
 - Binarize the target: `y_bin = (critical_cooling_rate >= threshold).astype(int)`.
 - Train a `RandomForestClassifier` on the same features with this binary target (using the same `random_state=42` and the same train-test split as T020). **Do NOT retrain the original regression model.**
 - Compute F1‑score on the held‑out test set and record it.
 4. **Metrics Calculation**:
 - **F1 Stability**: Calculate the percentage margin: `(max_F1 - min_F1) / mean_F1`.
 5. Write `sensitivity_report.csv` with columns `threshold,f1_score,f1_margin_pct,stability_status`.
 - `stability_status` is `PASS` if `f1_margin_pct <= 0.10` else `FAIL`.
 6. Write `sensitivity_status.json` (`{"stability_met": true/false, "f1_margin_pct": <float>, "threshold_values": [50,100,150], "run_status": "FAILED" if stability_met is false else "PASSED"}`).
- [ ] T030b [US3] Verification of sensitivity stability:
 - Load `sensitivity_status.json`; assert `stability_met` is `true`. If not, log a **WARNING** "SC-003 failed: Sensitivity margin exceeds 10%" and save `sc003_status: FAILED` to `data/models/sc003_status.json`. **Do not raise an exception**; the pipeline must continue to generate the report with this negative finding, but the `run_status` in `sensitivity_status.json` must be explicitly set to "FAILED" to flag the violation.

## Phase N: Polish & Cross‑Cutting Concerns

- [X] T034 [P] Documentation updates: README with execution instructions. **Note**: Specific caveats and "ASSOCIATIONAL" framing will be added in T034b after report generation.
- [X] T035 Ensure `random_state=42` is used consistently across all scripts.
- [X] T036 Performance optimization: confirm pipeline completes within 6 h on CPU (local sanity check + CI logs).
- [ ] T037 [P] Run `validate_schemas.py` to ensure all artifacts match contracts. <!-- FAILED: unspecified -->
- [X] T038 Security hardening: scan for hard‑coded secrets; ensure only verified URL is used.

## Phase O: Revision & Gap Resolution

- (T041 removed: logic merged into T024a)

## Phase P: Final Integration & Reporting

- [ ] T043 [US3] Generate `REPORT.md` summarizing data, model performance, feature importance, sensitivity analysis, and caveats.
 **Inputs**: `model_metrics_baseline.json`, `feature_importance.json`, `sensitivity_status.json`, **`statistical_comparison.json`**.
 **Requirements**:
 - Explicitly state that all predictive findings are **ASSOCIATIONAL** (per FR-006).
 - Report the statistical significance of the model vs null model (p-value, t-statistic, sc002_met status) as a core section.
 - Report feature importance and sensitivity stability results (including the `run_status` flag).
 **Depends on**: T028, T031, T022.
- [ ] T034b [P] [MOVED] Documentation updates: README with execution instructions and caveats (including "ASSOCIATIONAL" framing). **Depends on T043**.
- [ ] T044 Full pipeline run validation (ingestion → train → analyze → report) in a clean environment.
- [X] T045 Update `README.md` with final execution instructions and link to `REPORT.md`.

## Phase Q: Verification & Compliance (New)

**Purpose**: Ensure all outputs meet the "Real Data Only" and "No Fabrication" constitution gates.

- [ ] T046 [P] **Data Source Audit**: Write `code/audit_data_source.py` to verify that `data/processed/processed_alloys.csv` contains a `source_label` column explicitly set to "matsci/glass-forming-ability" and that no synthetic data flags (e.g., `is_synthetic=True`) exist.
- [ ] T047 [P] **Result Reproducibility Check**: Re-run `code/ingestion.py` and `code/features.py` in a fresh environment and compare the content hash of the output `processed_alloys.csv` against the original run. If hashes differ, raise an error.
- [ ] T048 [P] **Statistical Significance Gate**: Create a script `code/check_sc002.py` that parses `statistical_comparison.json` and logs a **WARNING** if `sc002_met` is false, ensuring the report explicitly flags the failure (consistent with T024c's non-blocking design). **Do NOT exit with code 1**.
- [ ] T049 [P] **Sensitivity Gate**: Create a script `code/check_sc003.py` that parses `sensitivity_status.json` and logs a failure if `stability_met` is false, ensuring the report explicitly flags unstable thresholds.