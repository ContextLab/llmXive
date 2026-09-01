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
- [X] T006 [US1] Create `contracts/dataset.schema.yaml` defining `AlloyRecord` fields (as previously defined).
- [X] T007 [P] [US2, US3] Create `contracts/model_output.schema.yaml` defining `ModelMetrics` and `SensitivityReport` (as previously defined).
- [X] T007b [P] [US2, US3] Update `plan.md` to document schema versioning and JSON‑Schema enforcement.
- [X] T008 [P] [US1] Ensure `ingestion.py` raises a clear `ValueError` if the `matsci/glass-forming-ability` dataset cannot be fetched.
- [X] T009 [P] Configure `pytest` and enforce `random_state=42` in `utils.py`.

## Phase 3: User Story 1 - Data Ingestion and Thermodynamic Feature Engineering (Priority: P1)

**Goal**: Download experimental data, filter for valid ternary alloys, and compute thermodynamic descriptors.

- [X] T012 [US1] Implement `code/ingestion.py`:
 1. Load the verified dataset via `datasets.load_dataset("matsci/glass-forming-ability", streaming=True)`.
 2. Filter for ternary alloys: parse the `composition` string using a **robust parser** that:
 - Splits the string into element‑symbol/amount tokens using regex `r'([A-Z][a-z]?)(\d*\.?\d*)'`.
 - Builds a dict `{element: float(amount)}`.
 - Validates that exactly three distinct elements are present and that each element exists in `mendeleev`.
 3. Exclude rows missing `critical_cooling_rate` or with malformed composition; log exclusions with reasons.
 4. If the filtered dataset exceeds 10 000 rows, sample down to 10 000 using `itertools.islice` with a fixed `random_state=42`.
 5. Write the filtered rows to `data/processed/processed_alloys_raw.csv`.
- [ ] T014 [P] [US1] Implement `features.py` to compute `mixing_enthalpy` using `mendeleev` elemental properties and composition weights.
- [ ] T015 [P] [US1] Implement `features.py` to compute `atomic_size_mismatch` and `electronegativity_variance`.
- [ ] T010a [US1] Unit test `test_features.py::test_mixing_enthalpy` (runs after successful implementation of T014 & T015).
- [ ] T016a [US1] Save the engineered dataset (including all thermodynamic columns) to `data/processed/processed_alloys.csv`.
- [ ] T016b [US1] Validate processed data:
 - Verify schema compliance against `contracts/dataset.schema.yaml`.
 - Ensure row count ≥ 500. If 500 ≤ N < 1000, log an **INFO** message (no warning or error).
 - If N < 500, raise `ValueError("Data availability error: <500 valid entries")`.
- [ ] T017 [US1] After filtering, assert that `critical_cooling_rate` variance > 0; otherwise raise `ValueError("Zero variance in critical_cooling_rate")`.

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train a Random Forest regressor with k-fold cross-validation and evaluate against a null model.

- [ ] T020 [US2] Load `processed_alloys.csv`; perform an 80/20 train‑test split (`random_state=42`).
- [X] T021 [US2] Train `RandomForestRegressor` on the training set; perform 5‑fold CV, record each fold RMSE in `data/models/cv_metrics.json` (`{"fold_scores": [...], "mean_rmse":...}`).
- [ ] T022 [US2] Evaluate on the held‑out test set; save RMSE and the trained model to `data/models/random_forest_model.pkl`.
- [X] T022b [US2] Train a `DummyRegressor` (strategy='mean') on the same training split; compute test RMSE; save predictions (`null_model_predictions.npy`) and RMSE (`null_model_rmse.json`).

### Statistical Validation (SC‑002)

- [ ] T024a [US2] Implement **null‑model statistical test**:
 1. Load the 5‑fold CV RMSE scores from `cv_metrics.json` (list of 5 values).
 2. Load the null-model test RMSE from `null_model_rmse.json` (single scalar value).
 3. Perform a **one-sample t-test** (two-sided) using `scipy.stats.ttest_1samp` comparing the 5-fold RMSEs against the null RMSE value.
 4. Compute p-value from the t-distribution.
 5. Save results to `data/models/statistical_comparison.json` (`{"p_value": <float>, "t_statistic": <float>, "sc002_met": <bool>}`) where `sc002_met` is `p_value < 0.05`.
- [ ] T024c [US2] Gate task:
 - Load `statistical_comparison.json`; if `sc002_met` is `false`, raise `ValueError("SC‑002 failed: model not statistically distinguishable from null")`; otherwise log success.

## Phase 5: User Story 3 - Feature Importance and Sensitivity Analysis (Priority: P3)

### Collinearity Detection and Stability Check (Pre-Analysis)

- [ ] T029a [US3] Perform **Stability Check & Retrain if needed**:
 1. Load the initial model (`random_forest_model.pkl`) and the processed dataset.
 2. Compute Pearson correlation matrix of the engineered features.
 3. Flag any pair with |ρ| > 0.8; write `collinearity_report.json`.
 4. If collinearity exists:
 - Compute mean absolute SHAP values from the **initial** model.
 - Identify the feature with the lowest mean absolute SHAP among the collinear pairs.
 - Retrain a new `RandomForestRegressor` excluding that feature.
 - Save the new model as `data/models/random_forest_model_stable.pkl`.
 - Re-run 5-fold CV on this stable model, saving `cv_metrics_stable.json`.
 - Record decision in `collinearity_decision.json` (`{"retrain_required": true, "dropped_feature": "<name>"}`).
 5. If no collinearity:
 - Copy `random_forest_model.pkl` to `random_forest_model_stable.pkl`.
 - Copy `cv_metrics.json` to `cv_metrics_stable.json`.
 - Record decision in `collinearity_decision.json` (`{"retrain_required": false}`).

### Permutation Importance (SC‑004)

- [ ] T028 [US3] Using the **stable model** (`random_forest_model_stable.pkl`), compute permutation importance (`n_permutations=1000`, `random_state=42`), calculate p‑values against a shuffled baseline, and write `feature_importance.json` (list of `{feature, p_value}`) ensuring at least one thermodynamic feature is in the top‑2 with `p_value < 0.05`.

### Sensitivity Analysis (SC‑003)

- [ ] T031 [US3] Perform **Threshold‑Sweep Sensitivity Analysis**:
 1. Load the **stable model** (`random_forest_model_stable.pkl`) and the full processed dataset.
 2. For each threshold in {50, 100, 150} K/s:
 - Binarize the target: `y_bin = (critical_cooling_rate >= threshold).astype(int)`.
 - Train a `RandomForestClassifier` on the same features with this binary target (using the same `random_state=42` and the same train-test split as T020).
 - Compute F1‑score on the held‑out test set and record it.
 3. Compute the Coefficient of Variation (CV) of the three F1‑scores using sample standard deviation (`ddof=1`): `CV = std(F1_scores, ddof=1) / mean(F1_scores)`. If the mean is zero, set CV to `inf` and log an error.
 4. Write `sensitivity_report.csv` with columns `threshold,f1_score,cv,stability_status` where `stability_status` is `PASS` if `cv <= 0.10` else `FAIL`.
 5. Also write `sensitivity_status.json` (`{"stability_met": true/false, "cv": <float>, "threshold_values": [50,100,150]}`).

- [ ] T030b [US3] Verification of sensitivity stability:
 - Load `sensitivity_status.json`; assert `stability_met` is `true`. If not, raise `ValueError("SC‑003 failed: sensitivity variance exceeds allowed margin")`.

## Phase N: Polish & Cross‑Cutting Concerns

- [X] T034 [P] Documentation updates: README with execution instructions and caveats.
- [X] T035 Ensure `random_state=42` is used consistently across all scripts.
- [X] T036 Performance optimization: confirm pipeline completes within 6 h on CPU (local sanity check + CI logs).
- [ ] T037 [P] Run `validate_schemas.py` to ensure all artifacts match contracts.
- [X] T038 Security hardening: scan for hard‑coded secrets; ensure only verified URL is used.

## Phase O: Revision & Gap Resolution

- [ ] T041 [US2] Verify that the null‑model statistical test (T024a) correctly implements the one-sample t-test against the dummy regressor baseline; add explicit log confirming the method used.

## Phase P: Final Integration & Reporting

- [X] T043 [US3] Generate `REPORT.md` summarizing data, model performance, feature importance, sensitivity analysis, and caveats (including “ASSOCIATIONAL” framing). Pull values from `model_metrics_baseline.json`, `feature_importance.json`, and `sensitivity_status.json`.
- [~] T044 Full pipeline run validation (ingestion → train → analyze → report) in a clean environment.
- [X] T045 Update `README.md` with final execution instructions and link to `REPORT.md`.
