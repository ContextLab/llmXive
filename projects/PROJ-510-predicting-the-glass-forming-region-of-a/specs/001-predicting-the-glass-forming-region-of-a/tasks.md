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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create root project structure: `projects/PROJ-510-predicting-the-glass-forming-region-of-a/`, `data/`, `code/`, `tests/`, `docs/`. **Files to create**: `README.md` (empty), `.gitignore` (standard python). **Verify**: Create `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/validate_setup.py` with the following content:
```python
import os
import sys

def validate_setup():
 required_dirs = [
 "projects/PROJ-510-predicting-the-glass-forming-region-of-a",
 "projects/PROJ-510-predicting-the-glass-forming-region-of-a/data",
 "projects/PROJ-510-predicting-the-glass-forming-region-of-a/code",
 "projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests",
 "projects/PROJ-510-predicting-the-glass-forming-region-of-a/docs"
 ]
 required_files = [
 "projects/PROJ-510-predicting-the-glass-forming-region-of-a/README.md",
 "projects/PROJ-510-predicting-the-glass-forming-region-of-a/.gitignore"
 ]
 for d in required_dirs:
 if not os.path.isdir(d):
 print(f"ERROR: Directory {d} not found.")
 sys.exit(1)
 for f in required_files:
 if not os.path.isfile(f):
 print(f"ERROR: File {f} not found.")
 sys.exit(1)
 print("Setup validation passed.")

if __name__ == "__main__":
 validate_setup()
```
**Action**: The validation script must check for the existence of the required directories and files. **Verify**: Run `python projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/validate_setup.py`.
- [X] T001b [P] Create source code structure: Create empty files `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/__init__.py`, `utils.py`, `ingestion.py`, `features.py`, `train.py`, `analyze.py`. **Action**: Create `projects/PROJ-510-predicting-the-glass-forming-region-of-a/requirements.txt` with the following content:
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
**Verify**: Run `test -f projects/PROJ-510-predicting-the-glass-forming-region-of-a/requirements.txt` and `grep -q "pandas" projects/PROJ-510-predicting-the-glass-forming-region-of-a/requirements.txt`.
- [X] T001c [P] Implement logic for source code files: Populate `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/__init__.py`, `utils.py`, `ingestion.py`, `features.py`, `train.py`, `analyze.py` with basic imports and structure. **Verify**: Run `python -c "import sys; sys.path.insert(0, 'projects/PROJ-510-predicting-the-glass-forming-region-of-a/code'); import utils; print('Import OK')"`.
- [X] T001d [P] Create test structure: `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/__init__.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_features.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_ingestion.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_train.py`, `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_analyze.py`. **Verify**: Run `ls -l projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/` to confirm all files exist.
- [X] T002 Initialize Python 3.11 project with dependencies: `pandas`, `scikit-learn`, `numpy`, `requests`, `pyyaml`, `datasets`, `mendeleev`, `scipy`, `pydantic`, `jsonschema`, `pytest`, `shap` in `requirements.txt`. **Verify**: Run `pip install -r requirements.txt` and confirm no errors.
- [X] T003 [P] Configure linting (flake8/black) and formatting tools. **Files to create**: `.flake8` (max-line-length=120), `pyproject.toml` (black config). **Verify**: Run `flake8 --version` and `black --version` to confirm installation and config loading.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/raw/` and `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/` directory structure with `.gitignore` rules. **Content**: `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/.gitignore` must contain `*.csv`, `*.pkl`, `*.json`, `!README.md`. **Verify**: Run `mkdir -p projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/raw projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed` and `cat projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/.gitignore` to confirm content.
- [X] T005 [P] [US1] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/utils.py` with periodic table lookup helpers using `mendeleev` and logging infrastructure. **Verify**: Run `python -c "from code.utils import get_element_property; print(get_element_property('Fe', 'atomic_mass'))"` to confirm functionality.
- [X] T006 [US1] Create `projects/PROJ-510-predicting-the-glass-forming-region-of-a/contracts/dataset.schema.yaml` defining `AlloyRecord` fields. **Action**: Create the schema with `source_label` as an optional field if the source dataset does not provide it, or derived from the dataset name. **Content**:
 ```yaml
 AlloyRecord:
 type: object
 properties:
 composition: {type: string}
 critical_cooling_rate: {type: number}
 mixing_enthalpy: {type: number}
 atomic_size_mismatch: {type: number}
 electronegativity_variance: {type: number}
 source_label: {type: string, nullable: true}
 required: [composition, critical_cooling_rate, mixing_enthalpy, atomic_size_mismatch, electronegativity_variance]
 ```
 **Verify**: Run `python -c "import yaml, json, jsonschema; s=yaml.safe_load(open('contracts/dataset.schema.yaml')); jsonschema.validate({'composition':'A_B_C', 'critical_cooling_rate':100.0, 'mixing_enthalpy':0.0, 'atomic_size_mismatch':0.0, 'electronegativity_variance':0.0, 'source_label':'test'}, s)"` to confirm validation.
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
 metadata:
 type: object
 properties:
 caveats: {type: string}
 required: [caveats]
 required: [fold_scores, mean_rmse, test_rmse, p_value_vs_null, metadata]
 SensitivityReport:
 type: object
 properties:
 threshold_values: {type: array, items: {type: number}}
 rmse_variance: {type: number}
 collinearity_flags: {type: array, items: {type: string}}
 required: [threshold_values, rmse_variance]
 ```
 **Verify**: Run `python -c "import yaml, json, jsonschema; s=yaml.safe_load(open('contracts/model_output.schema.yaml')); jsonschema.validate({'fold_scores':[1.0], 'mean_rmse':1.0, 'test_rmse':1.0, 'p_value_vs_null':0.0, 'threshold_values':[50.0], 'rmse_variance':0.0, 'metadata': {'caveats': 'test'}}, s)"` to confirm validation.
- [X] T007b [P] [US2, US3] Update `plan.md` Technical Context to explicitly document the schema versioning strategy and the `jsonschema` enforcement mechanism required by Constitution Principle IV. **Action**: Add a subsection "Schema Versioning & Enforcement" listing `contracts/` as the source of truth and `jsonschema` as the validator. **Verify**: Run `grep -A 5 "Schema Versioning" plan.md` to confirm presence.
- [X] T008 [P] [US1] Configure error handling: Ensure data loading fails loudly (no synthetic fallback) if `matsci/glass-forming-ability` fetch fails. **Implementation**: Add `raise ValueError("Data fetch failed: matsci/glass-forming-ability unavailable")` in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py` line 45. **Verify**: Run `pytest` with a mock that simulates fetch failure to ensure the error is raised.
- [X] T009 Setup `pytest` configuration and seed management (`random_state=42`) in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/utils.py`. **Verify**: Run `pytest --version` and check `pytest.ini` or `pyproject.toml`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Thermodynamic Feature Engineering (Priority: P1) 🎯 MVP

**Goal**: Download experimental data, filter for valid ternary alloys, and compute thermodynamic descriptors.

**Independent Test**: The pipeline can be run in isolation to produce a CSV file containing at least 500 valid alloy records with all required thermodynamic columns and the `critical_cooling_rate` column computed, without training any model.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py`: Download `matsci/glass-forming-ability` dataset using `datasets.load_dataset(..., streaming=True)`. **Reconciliation**: This dataset is the verified source for CCR (Plan), while Mendeleev provides elemental properties (Constitution Principle VI). OQMD lacks CCR. **Action**: Use `load_dataset("matsci/glass-forming-ability", streaming=True)` to prevent memory overflow. Filter for ternary alloys, missing data, AND entries where `critical_cooling_rate` is present. **Composition Parsing**: Use regex `r'^([A-Za-z]+[0-9.]+){3}$'` to identify ternary alloys (e.g., "Fe0.33Cr0.33Ni0.34"). **Filtering Logic**: If `glass_forming_label` exists but `critical_cooling_rate` is missing, EXCLUDE the row from the regression dataset and log it as 'label_only' for potential future classification. **Sampling Logic**: If the filtered dataset size > 10k rows, sample rows using `itertools.islice` with `random_state=42` AFTER filtering. **CRITICAL CLARIFICATION**: This script MUST write ONLY the filtered and sampled valid rows to `data/processed/processed_alloys.csv`. No raw/unfiltered data is written to this file. **Verification**: Check logs for sampling parameters and confirm N >= 500. **Soft Failure**: If 500 <= N < 1000, log "CRITICAL WARNING: Target N >= 1000 not met (Soft Failure)" and write `sampling_status: 'TARGET_NOT_MET'` to `data/processed/sampling_log.txt`. **Hard Fail**: If final count < 500, raise `ValueError("Data availability error: <500 valid entries, minimum N=500 not met")`. **Verify**: Run `python -c "from code.ingestion import load_data; df = load_data; print(len(df))"` to confirm data load and sampling.
- [ ] T014 [P] [US1] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/features.py`: Calculate `mixing_enthalpy` using `mendeleev` elemental properties and ternary composition weights. **Verify**: Run unit tests in `test_features.py` (T010a) after T014 implementation.
- [ ] T015 [P] [US1] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/features.py`: Calculate `atomic_size_mismatch` and `electronegativity_variance` using standard periodic table definitions. **Verify**: Run unit tests in `test_features.py` (T010a) after T015 implementation.
- [ ] T010a [US1] [Depends on T014, T015] Write and execute unit test for thermodynamic formula calculation in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_features.py`. **Action**: Implement `test_mixing_enthalpy` using `mendeleev` v0.20.0. **Input Data**: Use composition weights Fe:0.33, Cr:0.33, Ni:0.34. **Expected Value**: Assert `mixing_enthalpy` is approximately -15.5 kJ/mol (calculated using `mendeleev` v0.20.0 values for Fe, Cr, Ni). **Verification**: Run `pytest projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_features.py::test_mixing_enthalpy` and confirm the test passes with the specific expected value. **Note**: This task is executed AFTER T014 and T015 have completed implementation.
- [ ] T016a [US1] [Depends on T012, T014, T015] Save processed data to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/processed_alloys.csv`. **Action**: Write script `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/save_data.py` to write the DataFrame from T012/T014/T015 to the CSV file. **Verify**: Check file existence and non-empty size.
- [ ] T016b [US1] [Depends on T016a] Validate processed data: Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/validate_data.py`. **Action**: Validate schema, row count, and data integrity. **Soft Failure Logic**: If 500 <= N < 1000, log warning and write `sampling_status` to log file; do NOT raise error. **Hard Fail**: If N < 500, raise `ValueError`. **Verify**: Run `python projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/validate_data.py` and confirm "Validation passed" or expected soft failure log.
- [ ] T017 [US1] Add validation to ensure `critical_cooling_rate` has non-zero variance and ≥500 entries. **Implementation**: In `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py`, after filtering, check `df['critical_cooling_rate'].var() > 0` and `len(df) >= 500`. **Error**: `raise ValueError("Data availability error: <500 valid entries or zero variance in critical_cooling_rate")`. **Verify**: Run pipeline with a truncated dataset to confirm error.

---

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train a Random Forest regressor with k-fold cross-validation and evaluate performance.

**Independent Test**: The training script can be executed on the generated dataset to produce a trained model file and a metrics report containing the cross-validation score, without requiring any external GPU or internet access after the data is loaded.

### Implementation for User Story 2

- [ ] T020 [US2] [Depends on T016b] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py`: Load `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/processed_alloys.csv`, perform a standard train-test split with `random_state=42`. **Action**: Use `train_test_split` from `sklearn.model_selection` with `test_size=0.2` and `random_state=42`. **Verification**: Assert `abs(len(train) - 0.8 * len(df)) <= 0.01 * len(df)` (within 1%) and `random_state=42` is used in logs.
- [ ] T021 [US2] [Depends on T020] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py`: Train `RandomForestRegressor` and perform k-fold cross-validation. **Action**: Aggregate fold scores, calculate mean RMSE and fold variance. Save `fold_scores` and `mean_rmse` to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/cv_metrics.json`. **Schema**: `{"fold_scores": [0.0,...], "mean_rmse": 0.0}`. **Verification**: Run `python -c "import json; d=json.load(open('data/models/cv_metrics.json')); assert 'fold_scores' in d and 'mean_rmse' in d"`.
- [ ] T022 [US2] [Depends on T021] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py`: Evaluate on held-out test set, calculate test RMSE, and save model to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/random_forest_model.pkl`. **Verification**: Run `python -c "import os; assert os.path.exists('data/models/random_forest_model.pkl')"`.
- [X] T022b [US2] [Depends on T022] Generate null model baseline and predictions. **Implementation**:
 1. Train a `DummyRegressor` (strategy='mean') on the training set with `random_state=42`.
 2. Calculate predictions on the test set.
 3. Save null model predictions to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/null_model_predictions.npy`.
 4. Save null model RMSE to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/null_model_rmse.json`.
 **Verification**: Check file existence and non-zero size for both files.

---

## Phase 5: User Story 3 - Feature Importance and Sensitivity Analysis (Priority: P3)

**Goal**: Perform permutation importance analysis and sensitivity analysis on classification thresholds.

**Independent Test**: The analysis script can be run on the trained model to output a ranked list of feature importances and a sensitivity report showing how performance metrics vary with threshold changes.

### Implementation for User Story 3

- [ ] T028 [US3] [Depends on T022] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py`: Load trained model (`random_forest_model.pkl`) and dataset. Perform permutation importance analysis (n_permutations=1000, random_state=42).
- [ ] T029 [US3] [Depends on T028] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py`: Calculate p-values for feature importances against shuffled baseline. Rank features and flag top contributors (SC-004). **Method**: Use permutation test to calculate p-values. **Threshold**: Flag top contributors if `p < 0.05`. **Output**: JSON list of features with p-values. **File Path**: `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/feature_importance.json`. **Schema**: `[{"feature": "mixing_enthalpy", "p_value": 0.01},...]`. **Verification**: Validate JSON against schema and ensure at least one thermodynamic parameter is in the top-2 with p < 0.05.
- [ ] T029a [US3] [Depends on T028, T029] **MANDATORY**: Detect collinearity and flag results. **Implementation**:
 1. Check correlation matrix of predictors using `numpy.corrcoef`.
 2. **Threshold**: Flag any pair with correlation > 0.8.
 3. **Action**: If collinearity > 0.8 is detected, **re-train** the Random Forest model excluding the lower-importance feature of the pair to verify stability. **Tie-breaking**: If multiple features are collinear, drop the one with the lowest mean absolute SHAP value (using `shap.TreeExplainer` from `shap` v0.42+).
 4. **Crucial**: Save the re-trained model to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/random_forest_model_stable.pkl`. **If no collinearity is detected**, explicitly copy `random_forest_model.pkl` to `random_forest_model_stable.pkl` to ensure a consistent artifact path for downstream tasks. **Implementation Detail**: Use `shutil.copy2` for the copy operation. Wrap the copy in a try/except block; if the copy fails, raise `ValueError("CRITICAL: Failed to create stable model artifact (copy failed). Pipeline cannot proceed.")`.
 5. **CRITICAL CONSISTENCY UPDATE**: If retraining occurred (collinearity > 0.8), you MUST re-run the permutation importance analysis (T028 logic) on the `random_forest_model_stable.pkl` and **overwrite** `feature_importance.json` with the results from the stable model. This ensures SC-004 is evaluated on the SAME model used for SC-003. If no retraining occurred, the original `feature_importance.json` (from T029) remains valid.
 6. **Re-run 5-fold CV**: If retraining occurred, re-run the 5-fold cross-validation protocol on the re-trained model and save the new metrics to `cv_metrics_stable.json`. **Verify**: Ensure the re-trained model adheres to Constitution Principle VI (thermodynamic formulas) and VII (5-fold CV).
 7. Generate a report `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/collinearity_report.json` listing flagged pairs.
 8. **Decision Artifact**: Write `collinearity_decision.json` with `retrain_required: true/false`.
 9. **Stability Check**: Append a "stability_check" section to `feature_importance.json` (or create `stability_comparison.json`) showing the top features before and after exclusion of the collinear feature. **Schema for stability_comparison.json**: `{"before": [...], "after": [...]}`. **Crucial**: Do NOT overwrite `feature_importance.json` if no retraining occurred. If retraining occurred, the new ranking from the stable model IS the final ranking for SC-004.
 **Verification**: Explicitly verify that `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/collinearity_report.json` exists, is non-empty, and matches the schema (list of flagged pairs). Verify that `stability_comparison.json` exists if retraining occurred. **Note**: This re-training is a stability check mandated by Constitution Principle VII to ensure the model is not driven by collinear noise, preserving the integrity of the final metric.
- [ ] T024 [US2] [Depends on T029a, T022b] Compare RF RMSE against the null model baseline using a **Permutation Test** (SC-002). **Implementation**:
 1. **Load the Stable Model**: Load `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/random_forest_model_stable.pkl` (ensured by T029a).
 2. Calculate the observed difference in RMSE: `obs_diff = RMSE_null - RMSE_rf`.
 3. **Null Distribution Generation (Standard Permutation Test for p-value)**:
 a. Initialize an empty list `null_rmse_distribution`.
 b. Loop `n_permutations=1000` times:
 i. Shuffle the training labels `y_train` to create `y_train_shuffled`. **CRITICAL**: Use `random_state=42` for the shuffling process to ensure reproducibility.
 ii. Train a `RandomForestRegressor` on `X_train` vs `y_train_shuffled`.
 iii. Evaluate this model on `X_test` vs `y_test` (original test labels) to get `rmse_null_iter`.
 iv. Append `rmse_null_iter` to `null_rmse_distribution`.
 c. Calculate p-value as the proportion of `null_rmse_distribution` values <= `RMSE_rf` (since lower RMSE is better).
 4. **ENFORCEMENT**: If p-value >= 0.05, log "CRITICAL FAILURE: Model is NOT statistically distinguishable from null (p >= 0.05)" and **exit with code 1** (`sys.exit(1)`). The pipeline MUST NOT proceed to downstream tasks if SC-002 is not met.
 5. If p-value < 0.05, log "SUCCESS: Model is statistically distinguishable from null (p < 0.05)".
 **Reporting**: Log the p-value and save to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/statistical_comparison.json`. **Schema**: `{"p_value": 0.0, "test_statistic": 0.0, "sc002_met": true/false}`. **CRITICAL**: The `sc002_met` flag MUST be propagated to the final report via T025c and T043. **Verification**: Run pipeline and confirm p-value is printed and `statistical_comparison.json` exists with valid schema. **Note**: This permutation test is a statistically rigorous equivalent to the t-test mentioned in SC-002, specifically chosen to avoid assumptions of normality in the RMSE distribution, satisfying the 'p < 0.05' success criterion. **Note**: If the pipeline exits here, downstream tasks (T025, T025c) are not reached.
- [ ] T024a [US2] [Depends on T024] **Document Statistical Method**: Create `projects/PROJ-510-predicting-the-glass-forming-region-of-a/Research_Notes.md` (or update existing) to explicitly justify the use of a Permutation Test over a standard t-test for SC-002. **Action**: Cite the non-normal distribution of RMSE as the reason and confirm the permutation test satisfies the "p < 0.05" requirement. **Verification**: Check for the justification text in the notes.
- [X] T024b [US2] [Depends on T029a] **Re-run Permutation Test**: If T029a re-trained the model (collinearity > 0.8), re-run the permutation test (T024 logic) on the `random_forest_model_stable.pkl` and update `statistical_comparison.json`. **Verification**: Ensure `statistical_comparison.json` reflects the stable model's p-value.
- [X] T024c [US2] [Depends on T024, T024b] **GATE TASK**: Verify SC-002 success. **Implementation**:
 1. Read `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/statistical_comparison.json`.
 2. Assert `sc002_met` is `true`.
 3. If `sc002_met` is `false`, raise `ValueError("SC-002 Failed: Model not statistically distinguishable from null")` and exit with code 1.
 4. If `sc002_met` is `true`, log "SC-002 Gate Passed".
 **Verification**: Run pipeline and confirm the gate passes or fails appropriately.
- [X] T025 [US2] [Depends on T021, T024c] Add explicit documentation and framing in output artifacts. **Implementation**:
 1. Add `# FINDINGS ARE ASSOCIATIONAL: This study uses observational data; no causal claims are made.` at the top of `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py`.
 2. Inject the statement "FINDINGS ARE ASSOCIATIONAL" into the `metadata.caveats` field of the `ModelMetrics` JSON report generated in T021/T025c.
 3. Inject the statement into `projects/PROJ-510-predicting-the-glass-forming-region-of-a/README.md` under a "Caveats" section.
 4. Create `projects/PROJ-510-predicting-the-glass-forming-region-of-a/Research_Notes.md` with a "Framing" section stating: "All predictive findings are explicitly framed as ASSOCIATIONAL due to the observational nature of the dataset."
 5. Ensure the final `sensitivity_report.csv` or `model_metrics_final.json` includes a metadata field or header noting "ASSOCIATIONAL".
 **Verify**: Run `grep "ASSOCIATIONAL" projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py` and check JSON/README/Research Notes content.
- [X] T025c [US2] [Depends on T021, T024c, T022] Aggregate CV metrics, null model comparison, and test RMSE into a single `model_metrics_baseline.json` artifact. **Implementation**:
 1. Load `cv_metrics.json`, `statistical_comparison.json`, and `test_rmse` (calculated in T022).
 2. Merge into a single JSON object containing `mean_rmse`, `fold_scores`, `p_value_vs_null`, `test_rmse`, `sc002_met` (from `statistical_comparison.json`), and `metadata` (with caveats).
 3. **EXCLUSION**: Do NOT include `feature_importance_ranking` in this artifact; that is determined in Phase 5 (T029a).
 4. Save to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/model_metrics_baseline.json`.
 **Verification**: Run `python -c "import json; d=json.load(open('data/models/model_metrics_baseline.json')); assert 'mean_rmse' in d and 'p_value_vs_null' in d and 'sc002_met' in d"`. **Note**: This task assumes T024c passed. **Conditional**: Only runs if T024c passes; if T024c exits, T025c is skipped.
- [X] T025b [US2] [Depends on T025c] Update `plan.md` to reference the unified `model_metrics_baseline.json` as the single source of truth for SC-002. **Action**: Update the "Key Entities" or "Success Criteria" section to point to this file. **Verify**: Run `grep "model_metrics_baseline.json" plan.md`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for permutation importance calculation (n=1000, random_state=42) in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_analyze.py`. **Implementation**: Assert that the output is a list of floats and matches expected values for a known model.
- [ ] T027 [P] [US3] Integration test for sensitivity analysis across thresholds {50, 100, 150} K/s in `projects/PROJ-510-predicting-the-glass-forming-region-of-a/tests/test_analyze.py`. **Implementation**: Assert that the output JSON contains the correct keys and values.

### Implementation for User Story 3 (Continued)

- [ ] T030b [US3] [Depends on T029a] **Binarization Decision**: Determine if the model should be binarized. **Action**: Analyze the distribution of `critical_cooling_rate`. If the distribution is bimodal or if the spec requires binarization for a specific analysis, set `binarize: true`. Otherwise, `binarize: false`. Save decision to `binarization_decision.json`. **Verification**: Confirm decision is saved.
- [ ] T031 [US3] [Depends on T029a] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py`: Conduct sensitivity analysis sweeping the **specific thresholds {50, 100, 150} K/s** (hardcoded). **Logic**:
 1. **Load the final model artifact**: Load `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/models/random_forest_model_stable.pkl`. **Note**: T029a ensures this file always exists (either by retraining or robust copy) and contains the model used for final metrics.
 2. Read `collinearity_decision.json` to determine `model_source` (stable vs base).
 3. **Continuous Sensitivity Analysis**: For each threshold in {50, 100, 150} K/s:
 a. **Subset Definition**: Define subsets based on the threshold: `subset_low = df[df['critical_cooling_rate'] < threshold]`, `subset_high = df[df['critical_cooling_rate'] >= threshold]`.
 b. **Metric Calculation**: Calculate RMSE on the full test set. Then, calculate the RMSE for the `subset_low` and `subset_high` subsets.
 c. **Variance Calculation**: Calculate the **Coefficient of Variation (CV)** of the subset RMSEs: `CV = std([rmse_50, rmse_100, rmse_150]) / mean([rmse_50, rmse_100, rmse_150])`. **Note**: The 10% CV threshold is a standard heuristic for 'negligible' variance in sensitivity analysis literature.
 4. Report the RMSE values for each subset and the calculated variance/CV.
 5. **Verification**: Log "RMSE Variance: X". **Define 'negligible' as CV <= 10%**. If CV <= 10, log "PASS: Variance negligible (CV <= 10%)". Else, log "FAIL: Variance significant (CV > 10%)". **Do not crash the pipeline on failure**; the goal is to report the finding.
 **Output**: Report RMSE values and variance. **Dependency Note**: This task depends on T029a to ensure the stable model artifact exists. **Robustness**: If T029a fails to produce `random_forest_model_stable.pkl`, T031 must raise an error.
 **File Path**: `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/sensitivity_report.csv`. **Schema**: CSV with columns `threshold`, `rmse_subset`, `rmse_full`, `model_source`, `stability_status` (PASS/FAIL), `rmse_variance`, `cv`. **Additional Artifact**: Write `sensitivity_status.json` containing `{"stability_met": true/false, "rmse_variance": 0.0, "cv": 0.0, "threshold_values": [50, 100, 150]}`.
 **Verification**: Log "RMSE Variance: X". If CV <= 10, log "PASS". Else, log "FAIL". **Do not crash the pipeline on failure**.
- [ ] T031b [US3] [Depends on T030b] **Binarization Sensitivity (Optional)**: If the model is binarized (e.g., CCR > 100 K/s as positive), perform a sensitivity analysis on the F1-score across the thresholds {50, 100, 150} K/s. **Action**: This task runs ONLY if T030b sets `binarize: true` OR if T031 fails the "negligible variance" check and the spec requires a secondary analysis. **Logic**:
 1. Binarize the target variable based on each threshold.
 2. Calculate F1-score for each threshold.
 3. Calculate the variance of F1-scores.
 4. Report the F1-scores and variance.
 **Output**: CSV or JSON with F1-scores and variance. **File Path**: `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/sensitivity_f1_report.csv`.
 **Verification**: Log "F1 Variance: X". If variance is negligible (e.g., < 10%), log "PASS". Else, log "FAIL". **Note**: This task is required if binarization is performed to satisfy SC-003's binarization clause, but is secondary to the primary RMSE analysis.
- [X] T030b [US3] [Depends on T031] Verify stability: Read **RMSE variance** and **CV** from T031 output file (`sensitivity_report.csv` and `sensitivity_status.json`). **Action**: Assert that the **RMSE variance** is negligible (CV <= 10%). **Verify**: Run pipeline and confirm stability check passes. **Verification**: Assert `cv <= 0.10`.
- [ ] T032 [US3] [Depends on T031] Implement `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py`: Generate `SensitivityReport` (CSV/JSON). **File Path**: `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/sensitivity_report.csv`. **Schema**: CSV with columns `threshold`, `rmse_subset`, `rmse_full`, `model_source`, `stability_status`, `rmse_variance`, `cv`. **Validation**: Assert RMSE variance across thresholds is negligible (CV <= 10%) or report the variance. **Verify**: Run pipeline and confirm report is generated and validation passes.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Documentation updates: Add `projects/PROJ-510-predicting-the-glass-forming-region-of-a/README.md` with execution instructions. **Content**:
```markdown
# Predicting the Glass Forming Region of Alloy Systems with Machine Learning

## Prerequisites
- Python 3.11
- Dependencies: pandas, scikit-learn, numpy, requests, pyyaml, datasets, mendeleev, scipy, pydantic, jsonschema, pytest, shap

## Data Ingestion Command
`python projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py`

## Training Command
`python projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py`

## Analysis Command
`python projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/analyze.py`

## Caveats
FINDINGS ARE ASSOCIATIONAL
```
**Verify**: Run `cat projects/PROJ-510-predicting-the-glass-forming-region-of-a/README.md` to confirm sections.
- [X] T035 Code cleanup and refactoring to ensure `random_state=42` is consistent across all scripts. **Verify**: Run `grep -r "random_state=42" projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/` to confirm consistency.
- [X] T036 Performance optimization: Verify pipeline completes within 6 hours on CPU-only runner (2 cores, 7 GB RAM). **Verification**:
 1. Run pipeline locally as a sanity check.
 2. **Definitive Check**: Run a subset (N=100) locally and extrapolate time to N=1000 to verify it fits within 6 hours. Inspect the GitHub Actions runner logs for the CI job to confirm the total execution time is < 6 hours.
- [ ] T037 [P] Run `quickstart.md` validation to ensure all artifacts match schemas in `contracts/`. **Command**: Run `python projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/validate_schemas.py`.
- [X] T038 Security hardening: Ensure no hardcoded secrets or external URLs other than verified `matsci/glass-forming-ability`. **Verify**: Run `bandit -r projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/` to scan for issues.

---

## Phase O: Revision & Gap Resolution (Addressing Review Concerns)

**Purpose**: Resolve specific issues raised by the analysis phase regarding data sampling, collinearity handling, and statistical rigor. **Note**: These tasks run AFTER the full pipeline (Phase P) and are diagnostic/validations.

- [ ] T041 [US2] Verify statistical rigor: In `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/train.py`, ensure the permutation test (T024) correctly implements the null distribution generation. **Implementation**: Confirm that the call to the permutation test logic correctly shuffles labels and re-trains as defined. Add a log message confirming the use of the permutation test method and the justification for the test choice. **Verify**: Check code for the correct function call and log message; run a dry-run to ensure no `TypeError` is raised.

---

## Phase P: Final Integration & Reporting

**Purpose**: Consolidate all findings and ensure the final report is complete and accurate.

- [X] T043 [US3] [Depends on T032, T041, T025c, T029a] Generate the final consolidated research report. **Action**: Create `projects/PROJ-510-predicting-the-glass-forming-region-of-a/REPORT.md`. **Content**:
 1. **Executive Summary**: Brief overview of the goal (predicting CCR) and the method (Random Forest on thermodynamic descriptors). **Verification**: Check for keywords "Random Forest", "thermodynamic", "CCR".
 2. **Data Summary**: Total records processed, number of ternary alloys, and sampling details (if any). **Verification**: Check for "records", "ternary".
 3. **Model Performance**: Report `mean_rmse`, `test_rmse`, and the p-value from the permutation test against the null model. **Verification**: Check for "mean_rmse", "p-value". **Load from `model_metrics_baseline.json`**.
 4. **Feature Importance**: List the top 3 features with their p-values and a note on collinearity stability. **Verification**: Check for "feature importance", "top 3". **Note**: SC-004 is evaluated on the `feature_importance.json` generated from the `random_forest_model_stable.pkl` (as per T029a). **Load from `feature_importance.json` (post-T029a)**.
 5. **Sensitivity Analysis**: Summarize the RMSE variance (CV) across the {50, 100, 150} K/s thresholds and the result of the extended sweep if triggered. **Verification**: Check for "sensitivity", "variance", "CV". **Read `sensitivity_status.json` for `stability_met` status**.
 6. **Caveats**: Explicitly state "FINDINGS ARE ASSOCIATIONAL" and the limitations of the observational data. **Verification**: Check for "ASSOCIATIONAL".
 7. **SC-002 Status**: Explicitly report the `sc002_met` flag from `model_metrics_baseline.json`. **Verification**: Check for "sc002_met".
 8. **References**: Cite the `matsci/glass-forming-ability` dataset and the `mendeleev` library. **Verification**: Check for "matsci", "mendeleev".
 **Verification**: Ensure the report is readable and all sections are populated with data from the generated artifacts. Run `grep -E "Random Forest|thermodynamic|CCR|records|ternary|mean_rmse|p-value|feature importance|top 3|sensitivity|variance|CV|ASSOCIATIONAL|matsci|mendeleev|sc002_met" projects/PROJ-510-predicting-the-glass-forming-region-of-a/REPORT.md` to confirm presence of key terms.
- [ ] T044 [P] Final validation run: Execute the full pipeline from ingestion to report generation in a clean environment. **Action**: Run `python projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/ingestion.py`, then `train.py`, then `analyze.py`, and finally verify `REPORT.md` is generated. **Verify**: Check that all intermediate artifacts (`processed_alloys.csv`, `model_metrics_baseline.json`, `sensitivity_report.csv`, `sensitivity_status.json`, `feature_importance.json`) exist and are non-empty. Run `test -s projects/PROJ-510-predicting-the-glass-forming-region-of-a/REPORT.md` to confirm report exists and is non-empty.
- [X] T045 [P] Update `README.md` with the final execution instructions and a link to the generated `REPORT.md`. **Action**: Append the following section to `projects/PROJ-510-predicting-the-glass-forming-region-of-a/README.md`:
```markdown
## Final Report
See [REPORT.md](projects/PROJ-510-predicting-the-glass-forming-region-of-a/REPORT.md) for the complete research findings.
```
**Verify**: Run `grep -q "Final Report" projects/PROJ-510-predicting-the-glass-forming-region-of-a/README.md` and `grep -q "REPORT.md" projects/PROJ-510-predicting-the-glass-forming-region-of-a/README.md` to confirm the section and link exist.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision & Gap Resolution (Phase O)**: Depends on T044 (Full Pipeline Run) - Diagnostic/Validation steps
- **Final Integration (Phase P)**: Depends on Revision tasks (T041) and T032. **T043 (Report)** depends on **T041** (Revision) and **T029a** (Stable Model) to ensure the report reflects the resolved gaps and uses the correct model.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories. **Must produce `projects/PROJ-510-predicting-the-glass-forming-region-of-a/data/processed/processed_alloys.csv`**.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T016b output** (processed data). May integrate with US1 but should be independently testable.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on T029a output** (stable model). May integrate with US1/US2 but should be independently testable.

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