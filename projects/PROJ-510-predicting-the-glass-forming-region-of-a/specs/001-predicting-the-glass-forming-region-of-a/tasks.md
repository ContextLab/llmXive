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

## Phase 0: Research & Data Strategy

**Purpose**: Verify data sources and define research strategy.

- [ ] T000a [P] **Research Document Creation**: Create `docs/research.md`.
 1. Verify BMG dataset contains `critical_cooling_rate` and ternary alloy entries.
 2. Define thermodynamic formulas and validate against literature.
 3. Document the verified URL for the dataset source: `https://zenodo.org/record/XXXXX` (or specific figshare record ID).
 4. Document specific literature source for thermodynamic formulas (e.g., "Hume-Rothery rules" or specific paper DOI).
 5. **Deliverable**: `docs/research.md` with verified URLs and formula definitions.

## Phase 1: Data Modeling & Contracts

**Purpose**: Define data models and validation contracts.

- [ ] T001a-1 [P] Create root project directories: `data/`, `code/`, `tests/`, `docs/`.
- [ ] T001a-2 [P] Create placeholder files: `README.md` (empty) and `.gitignore` (standard Python).
- [ ] T001a-3 [P] Write validation script `projects/PROJ-510-predicting-the-glass-forming-region-of-a/code/validate_setup.py` to check:
 1. Existence of directories `data/`, `code/`, `tests/`, `docs/`.
 2. Existence of `README.md` and `.gitignore`.
 3. Write permissions for `data/` and `code/`.
 4. **Directory Creation**: If `data/logs/` does not exist, create it before attempting to write logs.
 5. **Log Output**: If any check fails, write a JSON object to `data/logs/setup_validation.json` with the following schema:
    ```json
    {
      "status": "FAIL",
      "timestamp": "<ISO8601>",
      "error_code": "<ONE_OF: DIR_MISSING, FILE_MISSING, PERM_DENIED>",
      "details": "<string describing the missing item>"
    }
    ```
    If all checks pass, write `{"status": "PASS", "timestamp": "<ISO8601>"}`.
 6. **Exit Code Logic**: The script MUST exit with code `1` IF AND ONLY IF the generated JSON log contains `"status": "FAIL"`. Otherwise, it MUST exit with code `0`.
 7. **Deliverable**: `data/logs/setup_validation.json` and correct exit code.
- [ ] T001a-4 [P] Execute validation script to ensure setup correctness.
- [ ] T001b [P] Create source code structure: empty `__init__.py`, `utils.py`, `ingestion.py`, `features.py`, `train.py`, `analyze.py`. Add `requirements.txt` with:
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
- [ ] T001c [P] Populate `__init__.py` and core modules with basic imports and docstrings.
- [ ] T001d [P] Create test package: `tests/__init__.py`, `test_features.py`, `test_ingestion.py`, `test_train.py`, `test_analyze.py`.
- [ ] T002 Initialize Python project with dependencies (install `requirements.txt`).
- [ ] T003 [P] Configure linting (flake8/black) with `.flake8` and `pyproject.toml`.
- [ ] T004 [P] Setup `data/raw/`, `data/processed/`, and `data/logs/` directories with `.gitignore` (ignore `*.csv`, `*.pkl`, `*.json`, keep `README.md`).
- [ ] T005 [P] [US1] Implement `code/utils.py` with periodic table lookup helpers (`mendeleev`) and logging.
- [ ] T006 [P] [US1] Create `contracts/dataset.schema.yaml` defining `AlloyRecord` fields.
- [ ] T006a [P] **Data Model Document**: Create `docs/data-model.md` defining `AlloyRecord`, `ModelMetrics`, `SensitivityReport` entities.
- [ ] T007 [P] [US2, US3] Create `contracts/model_output.schema.yaml` defining `ModelMetrics` and `SensitivityReport`.
- [ ] T007b [P] [US2, US3] Update `plan.md` to document schema versioning and JSON‑Schema enforcement.

## Phase 2: Configuration & Dependency Validation (Setup Prerequisites)

**Purpose**: Establish configuration and validate dependencies before core logic.

- [ ] T008 [P] [US1] **Configuration Management**: Create `config.yaml` to centralize hyperparameters and thresholds.
 1. Move hard-coded values (`random_state`, `test_size`, `thresholds`, `n_permutations`, `n_splits`) into `config.yaml`.
 2. **Requirement**: All scripts (T012a, T014a, T021, T028a, T074b) must read from `config.yaml`.
 3. **Constraint**: The values for `n_splits` (5), `test_size` (0.2), and `thresholds` ([50, 100, 150]) are **LOCKED** to the spec's requirements. If `config.yaml` contains different values, the script must raise a `ValueError`.
 4. **Error Logging**: If a fetch fails, write a **JSON Lines** file (one object per line) to `data/logs/fetch_error.log` with the following schema:
    ```json
    {"timestamp": "<ISO8601>", "error_code": "<NETWORK|TIMEOUT|HTTP>", "url": "<string>", "message": "<string>"}
    ```
    **Example**:
    ```
    {"timestamp": "2026-07-26T10:00:00Z", "error_code": "NETWORK", "url": "https://example.com/data", "message": "Connection timed out after 30s"}
    {"timestamp": "2026-07-26T10:01:00Z", "error_code": "HTTP", "url": "https://example.com/data", "message": "404 Not Found"}
    ```
 5. **Deliverable**: `config.yaml`.
- [ ] T009 [P] Configure `pytest` and enforce `random_state=42` in `utils.py`.
- [ ] T082a [P] **Data Flow Validator Implementation**: Implement `code/verify_data_flow.py`.
 1. Create a dependency graph validator that checks for the existence and validity of input files before allowing downstream execution.
 2. If a required upstream artifact is missing or invalid, raise `ValueError` with a clear message.
 3. **Deliverable**: `code/verify_data_flow.py`.
- [ ] T082b [P] **Data Flow Validator Execution**: Execute `code/verify_data_flow.py`.
 1. Verify that all downstream tasks can only execute if upstream tasks have generated required artifacts.
 2. Write `data/logs/data_flow_validation.json` with `{"status": "pass|fail", "missing_dependencies": list}`.
 3. **Deliverable**: `data/logs/data_flow_validation.json`.
- [ ] T085a [P] **Config Lock Implementation**: Implement `code/verify_config_locks.py`.
 1. Load `config.yaml` and verify `n_splits=5`, `test_size=0.2`, `thresholds=[50, 100, 150]`.
 2. If violated, raise `ValueError` citing specific spec requirement (e.g., "SC-002 requires n_splits=5").
 3. **Deliverable**: `code/verify_config_locks.py`.
- [ ] T085b [P] **Config Lock Execution**: Execute `code/verify_config_locks.py`.
 1. Verify locked values match spec.
 2. Write `data/logs/config_lock_verification.json` with `{"status": "pass|fail", "violations": list}`.
 3. **Deliverable**: `data/logs/config_lock_verification.json`.

## Phase 3: User Story 1 - Data Ingestion and Thermodynamic Feature Engineering (Priority: P1)

**Goal**: Download experimental data, filter for valid ternary alloys, and compute thermodynamic descriptors.

- [ ] T012a [US1] **Ingestion & Filtering Implementation**: Implement `code/ingestion.py`.
 1. Load the verified dataset via `requests.get("https://zenodo.org/record/XXXXX/files/...")` or equivalent verified URL from `docs/research.md`. **DO NOT** use Hugging Face datasets library for this specific source unless the source is explicitly verified in `docs/research.md` as an experimental source.
 2. **Schema Validation**: Immediately check that the dataset schema contains the `critical_cooling_rate` column. If missing, raise `ValueError("Verified Data Source Mismatch: Dataset lacks critical_cooling_rate column.")`.
 3. Filter for ternary alloys: parse the `composition` string using a **robust parser** that splits into tokens and validates exactly three distinct elements.
    - **Whitespace Handling**: Strip all leading/trailing whitespace from the composition string before parsing.
    - **Missing Amounts**: If an element has no amount specified (e.g., "Fe Cu Ni"), **REJECT** the row. Do NOT default to 1.0.
    - **Edge Case Examples**:
      - Input: "  Fe20Cu50Ni30  " -> Parsed: `[("Fe", 20.0), ("Cu", 50.0), ("Ni", 30.0)]`
      - Input: "Fe Cu Ni" -> **REJECTED** (MALFORMED_COMPOSITION)
      - Input: "Fe20Cu50" -> Excluded (NON_TERNARY)
 4. Exclude rows missing `critical_cooling_rate` or with malformed composition; log exclusions to `data/logs/exclusion_log.txt` using the **exact format**:
    `EXCLUSION: <row_index> - <reason> - <raw_composition>`
    Where `<reason>` MUST be one of the following controlled vocabulary strings:
    - `MISSING_CCR` (if critical_cooling_rate is null/NaN)
    - `NON_TERNARY` (if not exactly 3 elements)
    - `MALFORMED_COMPOSITION` (if parsing fails OR amounts are missing)
    - `INVALID_ELEMENT` (if an element symbol is not found in mendeleev)
 5. **Data Volume Handling**: Process data in chunks of **5000 rows**.
    - Accumulate rows until buffer size reaches 5000.
    - Convert buffer to `pandas.DataFrame`.
    - Process and append valid rows to the final output file.
    - **Explicitly handle final partial chunks** to ensure no data loss for datasets < 5000 rows.
 6. **Source Labeling**: Add a column `source_label` with value `'verified_experimental_source'` to every row.
 7. **Error Handling**: Implement a retry mechanism for transient network failures (e.g., 3 retries with exponential backoff) before raising `ValueError`.
 8. **Deliverable**: `code/ingestion.py`.
- [ ] T012b [US1] **Ingestion Validation Implementation**: Implement `code/validate_ingestion.py`.
 1. Load `data/processed/processed_alloys_raw.csv`.
 2. If N < 500, raise `ValueError("Data availability error: N < 500.")`.
 3. If 500 <= N < 1000, log `WARNING`.
 4. If N >= 1000, log `INFO`.
 5. **Deliverable**: `code/validate_ingestion.py`.
- [ ] T012c [P] **Power Analysis Implementation**: Implement `code/analyze_power.py`.
 1. Calculate statistical power loss if N < 1000.
 2. Write `data/logs/power_analysis.json`.
 3. **Deliverable**: `code/analyze_power.py`.
- [ ] T012d [P] **Ingestion Execution**: Execute `code/ingestion.py` and `code/validate_ingestion.py`.
 1. Generate `data/processed/processed_alloys_raw.csv`.
 2. Generate `data/logs/ingestion_status.json` (structured JSON log for every run, recording success/failure and details).
 3. **Deliverable**: `data/processed/processed_alloys_raw.csv`, `data/logs/ingestion_status.json`.
- [ ] T014a [US1] **Feature Engineering Implementation**: Implement `code/features.py`.
 1. Implement `calc_mixing_enthalpy`: Use pairwise enthalpy from `mendeleev`. **NO Fallback**. If data missing, raise `ValueError` with the **exact message**:
    `Missing data for pair: <Element1>-<Element2>`
    Where `<Element1>` and `<Element2>` are the two elements in the pair, **sorted alphabetically by element symbol** (e.g., "Al-Fe", not "Fe-Al").
 2. Implement `calc_size_mismatch` and `calc_electronegativity_variance`.
 3. **Dependency**: This task relies on the `AlloyRecord` definition in `docs/data-model.md` (T006a).
 4. **Deliverable**: `code/features.py`.
- [ ] T014b [US1] **Feature Engineering Execution**: Execute `code/features.py`.
 1. Compute features and save to `data/processed/processed_alloys.csv`.
 2. **Deliverable**: `data/processed/processed_alloys.csv`.
- [ ] T010a [US1] Unit test `test_features.py::test_mixing_enthalpy`:
 - Implement unit tests verifying the `calc_mixing_enthalpy` function against known periodic table values.
 - Ensure the test passes for valid ternary compositions and correctly handles edge cases (including the specific error message format).
- [ ] T010b [US1] Unit test `test_features.py::test_size_mismatch`:
 - Implement unit tests verifying the `calc_size_mismatch` and `calc_electronegativity_variance` functions.
- [ ] T016a [US1] **Save Engineered Dataset**: Load `data/processed/processed_alloys_raw.csv` and append computed features.
 - Ensure the file contains exactly the columns defined in `contracts/dataset.schema.yaml`.
 - **Deliverable**: `data/processed/processed_alloys.csv`.
- [ ] T016b [US1] **Validate Processed Data**: Load `data/processed/processed_alloys.csv`.
 - **Schema Check**: Use `jsonschema` to validate against `contracts/dataset.schema.yaml`.
 - **Data Volume Check**: If N < 500, raise `ValueError`.
 - **Deliverable**: `data/logs/schema_validation_status.json`.
- [ ] T016c [US1] **Data Availability Audit**: Count valid ternary alloys.
 - Write `data/logs/data_availability_audit.json`.
 - **Deliverable**: `data/logs/data_availability_audit.json`.
- [ ] T017 [US1] After filtering, assert that `critical_cooling_rate` variance > 0; otherwise raise `ValueError`.

## Phase 4: User Story 2 - Model Training and Cross-Validation (Priority: P2)

**Goal**: Train a Random Forest regressor with k-fold cross-validation and evaluate against a null model.

- [ ] T019 [US2] **Critical**: Validate Total Dataset Size (Pre-Split).
 - Load `data/processed/processed_alloys.csv`.
 - If `len(df) < 500`, raise `ValueError`.
 - **Deliverable**: `data/logs/training_set_validation.json`.
- [ ] T020 [US2] Load `processed_alloys.csv`; perform a standard train-test split (`random_state=42`, `test_size=0.2`).
 - Split the data into `data/processed/train_set.csv` and `data/processed/test_set.csv`.
 - Save the split indices to `data/models/split_indices.json`.
 - **Deliverable**: `data/processed/train_set.csv`, `data/processed/test_set.csv`, `data/models/split_indices.json`.
- [ ] T020b [P] **Shared CV Splitter**: Instantiate a `KFold(n_splits=5, shuffle=True, random_state=42)` object.
 - **Action**: Configure the splitter. Do NOT save indices here; T021 will save them.
 - **Deliverable**: Configured splitter object (used in T021).
- [ ] T021a [US2] **Train RF Model**: Train `RandomForestRegressor` on `data/processed/train_set.csv` using the splitter from T020b.
 - **Deliverable**: Trained model (in memory).
- [ ] T021b [US2] **Null Model CV**: Train `DummyRegressor` on the **same training split** using the **same folds**.
 - Perform k-fold cross-validation on the Dummy model.
 - **Deliverable**: Dummy CV scores.
- [ ] T021c [US2] **Statistical Comparison**: Perform a **two-sided paired t-test** using `scipy.stats.ttest_rel` comparing RF vs Dummy CV scores.
 - Evaluate the RF model on the held-out test set and calculate test RMSE.
 - **Rounding**: Round `p_value` and `t_statistic` to **6 decimal places** in the JSON output.
 - **Deliverable**: Statistical comparison data.
- [ ] T021d [P] **Training Execution & Save**: Execute training and save artifacts.
 1. Save fold indices to `data/models/cv_folds_indices.json`.
 2. Save `data/models/cv_metrics.json`, `data/models/null_model_cv_scores.json`, `data/models/statistical_comparison.json`, `data/models/test_metrics.json`.
 3. Save `data/models/random_forest_model.pkl`.
 4. **Deliverable**: All above JSON and PKL files.
- [ ] T083a [P] **CV Fold Validator Implementation**: Implement `code/validate_cv_folds.py`.
 1. Load `data/models/cv_folds_indices.json`.
 2. Verify folds are mutually exclusive and collectively exhaustive.
 3. Raise `ValueError` if any violation is detected.
 4. **Deliverable**: `code/validate_cv_folds.py`.
- [ ] T083b [P] **CV Fold Validator Execution**: Execute `code/validate_cv_folds.py`.
 1. Verify fold integrity.
 2. Write `data/logs/cv_fold_integrity.json` with `{"status": "pass|fail", "violations": list}`.
 3. **Deliverable**: `data/logs/cv_fold_integrity.json`.
- [ ] T024c [US2] Gate task (Non-Blocking):
 - Load `statistical_comparison.json`.
 - If `sc002_met` is `false`, log a **WARNING** and save `sc002_status: FAILED` to `data/models/sc002_status.json`.
 - If `sc002_met` is `true`, log success and save `sc002_status: PASSED`.

## Phase 5: User Story 3 - Feature Importance and Sensitivity Analysis (Priority: P3)

### Collinearity Detection and Stability Check (Pre-Analysis)

- [ ] T029a [US3] **Detect Collinearity**:
 1. Load the initial model and processed dataset.
 2. Compute Pearson correlation matrix.
 3. Flag any pair with |ρ| > 0.8; write `collinearity_report.json`.
 4. Record initial model's metrics in `data/models/initial_model_metrics.json`.
 - **Deliverable**: `collinearity_report.json`, `data/models/initial_model_metrics.json`.
- [ ] T029b [US3] **Collinearity Resolution**:
 1. Load `collinearity_report.json`.
 2. If collinearity exists:
 - Compute **Permutation Importance** (not SHAP) for the current model.
 - Identify the feature with the **lowest** permutation importance among collinear pairs.
 - **Constraint**: **DO NOT** drop core descriptors (`mixing_enthalpy`, `atomic_size_mismatch`, `electronegativity_variance`).
 - If lowest importance feature is a core descriptor: Mark as "No Valid Candidate" and flag model as "unstable" in the report.
 - If candidate found: Retrain RF excluding that feature. Save as `random_forest_model_stable.pkl`.
 3. **Output**: `data/models/collinearity_decision.json`, `data/models/random_forest_model_stable.pkl`.
 - **Deliverable**: `data/models/collinearity_decision.json`, `random_forest_model_stable.pkl`.
- [ ] T084a [P] **Permutation Validator Implementation**: Implement `code/validate_permutation_importance.py`.
 1. Load `feature_importance.json`.
 2. Verify p-values are calculated using a one-sample t-test against the permutation distribution.
 3. Verify top-2 features have p-values < 0.05.
 4. Verify that the number of permutations matches the specification.
 5. Raise `ValueError` if validation fails.
 6. **Deliverable**: `code/validate_permutation_importance.py`.
- [ ] T084b [P] **Permutation Validator Execution**: Execute `code/validate_permutation_importance.py`.
 1. Verify statistical rigor.
 2. Write `data/logs/permutation_importance_validation.json` with `{"status": "pass|fail", "violations": list}`.
 3. **Deliverable**: `data/logs/permutation_importance_validation.json`.

### Permutation Importance (SC‑004)

- [ ] T028a [US3] **Permutation Importance Implementation**: Implement `code/compute_importance.py`.
 1. Using the **stable model**, compute permutation importance (`n_permutations=1000`, `random_state=42`).
 2. Calculate p-values using a **one-sample t-test**.
 3. **Deliverable**: `code/compute_importance.py`.
- [ ] T028b [P] **Permutation Importance Execution**: Execute `code/compute_importance.py`.
 1. Generate `feature_importance.json`.
 2. Log whether at least one thermodynamic feature is in the top‑2 with `p_value < 0.05`.
 3. **Deliverable**: `feature_importance.json`.

### Sensitivity Analysis (SC‑003)

- [ ] T031a [US3] **Sensitivity Analysis Implementation**: Implement `code/sensitivity_analysis.py`.
 1. Load the **stable model** and the **full processed dataset**.
 2. **Threshold Sweep Logic**:
 - Define thresholds: `[50, 100, 150]` K/s.
 - For each threshold `T`:
 - Calculate RMSE of continuous predictions on the **full test set**.
 - Binarize target and predictions, calculate F1-score.
 - Record `rmse_continuous` and `f1_score`.
 3. **Stability Check**:
 - Calculate `rmse_variance` (rounded to **6 decimal places**) and `f1_variance`.
 - **Constraint**: Thresholds must be fixed as per spec (50, 100, 150) OR derived from a documented physical rationale.
 - **Tie-Breaking Rule**: If `rounded_variance == (0.10 * mean_rmse_continuous)`, the status MUST be set to `'FAIL'`. The condition for `'PASS'` is strictly `rounded_variance < (0.10 * mean_rmse_continuous)` for binarized cases. For continuous cases, use "negligible margin" (e.g., < 5% or as defined in spec).
 - Set `stability_status` to either `'PASS'` or `'FAIL'` (case-sensitive).
 4. Write `sensitivity_report.csv`.
 5. **Deliverable**: `code/sensitivity_analysis.py`.
- [ ] T031b [P] **Sensitivity Analysis Execution**: Execute `code/sensitivity_analysis.py`.
 1. Generate `sensitivity_report.csv` and `sensitivity_status.json`.
 2. **Deliverable**: `sensitivity_report.csv`, `sensitivity_status.json`.
- [ ] T030c [US3] Verification of sensitivity stability:
 - Load `sensitivity_status.json`; assert `stability_met` is `true`. If not, log a **WARNING** and save `sc003_status: FAILED`.

## Phase 6: Polish & Cross‑Cutting Concerns

- [ ] T034 [P] Documentation updates: README with execution instructions. **Note**: Specific caveats and "ASSOCIATIONAL" framing are enforced by the report generation script (T074b) and constitution checks.
- [ ] T035 Ensure `random_state=42` is used consistently across all scripts.
- [ ] T036 Performance optimization: confirm pipeline completes within 6 h on CPU.
 1. **Execution**: Run `time python -m code.pipeline` (or equivalent full pipeline script).
 2. **Deliverable**: `data/logs/performance_benchmark.json` containing total execution time.
- [ ] T037 [P] **Schema Validation**: Run `validate_schemas.py` to ensure all artifacts match contracts.
 - **Script Definition**: Create `code/validate_schemas.py`. It must load `contracts/dataset.schema.yaml` and `contracts/model_output.schema.yaml`. It must iterate through all generated JSON/CSV artifacts in `data/` and `data/models/` and validate them against the schemas.
 - **Output**: Print "Validation Passed" and exit with code 0 if all match. Print "Validation Failed" and list errors, then exit with code 1 if any mismatch.
 - **Deliverable**: `code/validate_schemas.py`.
- [ ] T038 Security hardening: scan for hard‑coded secrets; ensure only verified URL is used.

## Phase Q: Verification & Compliance (Moved to after Phase U for Execution Flow)

**Purpose**: Ensure all outputs meet the "Real Data Only" and "No Fabrication" constitution gates.

- [ ] T046 [P] **Data Source Audit**: Write `code/audit_data_source.py` to verify that `data/processed/processed_alloys.csv` contains a `source_label` column explicitly set to "verified_experimental_source" and that no synthetic data flags exist.
- [ ] T047 [P] **Result Reproducibility Check**: Re-run `code/ingestion.py` and `code/features.py` in a fresh environment and compare the content hash (SHA-256) of the output `processed_alloys.csv` against the original run hash stored in `data/logs/ingestion_hash.txt`.
 - **Constraint**: Before hashing, the CSV file MUST be normalized to **UTF-8 encoding** with **LF (Unix-style) line endings**.
 - **Deliverable**: `data/logs/reproducibility_check.json`.
- [ ] T048 [P] **Statistical Significance Gate**: Create a script `code/check_sc002.py` that parses `statistical_comparison.json` and logs a **WARNING** if `sc002_met` is false.
- [ ] T049 [P] **Sensitivity Gate**: Create a script `code/check_sc003.py` that parses `sensitivity_status.json` and logs a failure if `stability_met` is false.

## Phase U: Revision & Gap Resolution (Moved before Phase Q for Script Creation)

**Purpose**: Address specific reviewer concerns regarding audit execution, task granularity, and final validation steps.

- [ ] T065 [P] [US1] **Audit Execution Fix**: Execute `code/audit_data_source.py` and ensure `data/logs/data_source_audit.json` is populated.
- [ ] T066 [P] [US2] **Statistical Audit Execution**: Execute `code/check_sc002.py`. Ensure it correctly parses `statistical_comparison.json` and writes a valid `data/logs/statistical_significance_audit.json`.
- [ ] T067 [P] [US3] **Sensitivity Audit Execution**: Execute `code/check_sc003.py`. Ensure it correctly parses `sensitivity_status.json` and writes a valid `data/logs/sensitivity_stability_audit.json`.
- [ ] T068 [P] **Report Validation Script**: Create `code/validate_report.py` to programmatically verify that `REPORT.md` contains the required sections.
- [ ] T069 [P] **Atomic Pipeline Test**: Break down T061 into discrete steps: 1. Clean environment setup, 2. Data ingestion run, 3. Feature engineering run, 4. Model training run, 5. Analysis run, 6. Report generation. Verify artifacts after each step.
- [ ] T070 [P] **Documentation Review Checklist**: Create `docs/review_checklist.md` listing specific criteria for README.md and REPORT.md.
- [ ] T071 [P] **Code Quality Metrics**: Run `flake8` and `black --check` on the entire `code/` directory. Fix any linting errors or formatting issues found.
- [ ] T072 [P] **Constitutional Compliance Script**: Create `code/verify_constitution.py` to automatically check all constitutional principles.

## Phase T: Final Review & Compliance Verification

**Purpose**: Ensure the entire pipeline and its outputs meet all constitutional gates and specification requirements before final delivery.

- [ ] T057 [P] [US1] **Data Source Verification**: Execute `code/audit_data_source.py`.
 - **Deliverable**: `data/logs/data_source_audit.json`.
- [ ] T058 [P] [US2] **Statistical Significance Confirmation**: Run `code/check_sc002.py`.
 - **Deliverable**: `data/logs/statistical_significance_audit.json`.
- [ ] T059 [P] [US3] **Sensitivity Stability Confirmation**: Run `code/check_sc003.py`.
 - **Deliverable**: `data/logs/sensitivity_stability_audit.json`.
- [ ] T060 [P] **Final Report Validation**: Ensure `REPORT.md` includes all required sections.
 - **Execution**: Run `code/validate_report.py` and verify exit code 0.
 - **Deliverable**: `data/logs/report_validation_status.json`.
- [ ] T061a [P] **Atomic Pipeline Test - Ingestion**: Execute `code/ingestion.py` in a clean environment. Verify `data/processed/processed_alloys_raw.csv` is generated.
- [ ] T061b [P] **Atomic Pipeline Test - Features**: Execute `code/features.py`. Verify `data/processed/processed_alloys.csv` is generated.
- [ ] T061c [P] **Atomic Pipeline Test - Training**: Execute `code/train.py`. Verify `data/models/random_forest_model.pkl` and `data/models/cv_metrics.json` are generated.
- [ ] T061d [P] **Atomic Pipeline Test - Analysis**: Execute `code/analyze.py`. Verify `data/models/feature_importance.json` and `data/models/sensitivity_status.json` are generated.
- [ ] T061e [P] **Atomic Pipeline Test - Report**: Execute `code/generate_report.py` (or T074c logic). Verify `REPORT.md` is generated.
- [ ] T061f [P] **Atomic Pipeline Test - Final Verification**: Run all audit scripts (T046-T049) and verify all JSON logs are present and valid.
- [ ] T062a [P] **README Completeness**: Verify `README.md` contains execution instructions, dataset source URL, random seed information, and associational framing note.
 - **Deliverable**: `data/logs/readme_checklist.json`.
- [ ] T062b [P] **REPORT.md Completeness**: Verify `REPORT.md` contains all required sections.
 - **Deliverable**: `data/logs/report_checklist.json`.
- [ ] T063 [P] **Code Quality Final Review**: Perform a final code review to ensure all code follows best practices.
 - **Execution**: Run `flake8 code/` and `black --check code/`.
 - **Deliverable**: `data/logs/linting_report.txt`.
- [ ] T064 [P] **Constitutional Compliance Audit**: Conduct a final audit to ensure all constitutional principles are fully satisfied.
 - **Execution**: Run `code/verify_constitution.py` and **write results to `data/logs/constitutional_compliance_report.json`**.
 - **Deliverable**: `data/logs/constitutional_compliance_report.json`.
- [ ] T086a [P] **Artifact Consistency Implementation**: Implement `code/verify_artifact_consistency.py`.
 1. Parse `REPORT.md` and extract all numerical metrics.
 2. Compare these against the values in `cv_metrics.json`, `statistical_comparison.json`, `feature_importance.json`, and `sensitivity_status.json`.
 3. Raise `ValueError` if any discrepancy is found.
 4. **Deliverable**: `code/verify_artifact_consistency.py`.
- [ ] T086b [P] **Artifact Consistency Execution**: Execute `code/verify_artifact_consistency.py`.
 1. Verify consistency.
 2. Write `data/logs/artifact_consistency_validation.json` with `{"status": "pass|fail", "discrepancies": list}`.
 3. **Deliverable**: `data/logs/artifact_consistency_validation.json`.

## Phase V: Final Gap Resolution & Missing Task Implementation

**Purpose**: Address specific reviewer concerns regarding missing implementation steps, task granularity, and final validation gaps identified in the audit.

- [ ] T073 [P] [US1] **Verification: Data Streaming**: Execute `code/ingestion.py` with a large dataset (or simulated large stream) to verify that the chunked processing (5000 rows) completes without OOM.
 - **Action**: Run the script and log memory usage peaks.
 - **Deliverable**: `data/logs/streaming_strategy.json`.
- [ ] T074a [P] **Create Report Template**: Create `docs/report_template.md` with the exact Markdown structure for `REPORT.md`.
 1. Title, Date, Author.
 2. Executive Summary.
 3. Data Source & Methodology.
 4. Statistical Significance (SC-002).
 5. Feature Importance (SC-004).
 6. Sensitivity Analysis (SC-003).
 7. Limitations and Caveats (Associational Framing).
 8. **Deliverable**: `docs/report_template.md`.
- [ ] T074b [P] **Report Generation Script Implementation**: Create `code/generate_report.py`.
 1. Read `docs/report_template.md` and all JSON artifacts.
 2. Populate the template with actual values.
 3. **Mapping Logic**: Insert metrics from JSONs into specific sections using the placeholder syntax `{{variable_name}}` (e.g., `{{mean_rmse}}`).
 4. **Critical**: If `sensitivity_status.json` indicates `stability_met: false`, insert a prominent warning.
 5. **Constraint**: The script MUST fail with a `ValueError` if any `{{...}}` placeholder remains in the output text after substitution.
 6. **Deliverable**: `code/generate_report.py`.
- [ ] T074c [P] **Report Generation Execution**: Execute `code/generate_report.py`.
 1. Generate `REPORT.md`.
 2. **Deliverable**: `REPORT.md`.
- [ ] T075 [P] [US3] **Missing Task: Collinearity Resolution Script**: Create `code/resolve_collinearity.py` to automate the logic described in T029b.
 - **Action**: Implement the loop that detects collinearity, identifies the lowest permutation importance feature, drops it if not a core descriptor, and retrains the model.
 - **Requirement**: Ensure the script respects the "Core Feature Handling" constraint.
 - **Deliverable**: `code/resolve_collinearity.py` and `data/models/collinearity_decision.json`.
- [ ] T076 [P] **Missing Task: Final Integration Test**: Create `tests/integration/test_full_pipeline.py` to run the entire pipeline end-to-end.
 - **Action**: Write a test that executes `ingestion.py`, `features.py`, `train.py`, `analyze.py`, and `generate_report.py` in sequence.
 - **Requirement**: Assert that all expected output files exist and contain valid data.
 - **Deliverable**: `tests/integration/test_full_pipeline.py`.
- [ ] T077 [P] **Missing Task: Error Handling for Missing Dependencies**: Add robust error handling for missing optional dependencies.
 - **Action**: Update `code/utils.py` to check for required imports at startup and raise a clear `ImportError`.
 - **Deliverable**: Updated `code/utils.py`.
- [ ] T078 [P] **Missing Task: Configuration Management**: (Moved to Phase 2 as T008). This task is now obsolete in Phase V.
 - **Action**: N/A.
- [ ] T079 [P] **Missing Task: Documentation of Data Flow**: Create `docs/data_flow.md` to visualize the data flow between tasks.
 - **Action**: Document the input/output relationships.
 - **Requirement**: Include a diagram (Mermaid or ASCII).
 - **Deliverable**: `docs/data_flow.md`.
- [ ] T080 [P] **Missing Task: Performance Benchmarking**: Add a benchmarking task to measure execution time of each phase.
 - **Action**: Instrument scripts to log execution time.
 - **Requirement**: Ensure the total pipeline time is logged.
 - **Deliverable**: `data/logs/performance_benchmark.json`.
- [ ] T081 [P] [US3] **Removed**: Continuous RMSE Variance Calculation logic has been integrated into T031. This task is no longer required.

## Phase W: Review-Driven Gap Resolution (Removed - Tasks Moved to Appropriate Phases)

**Purpose**: Address specific reviewer concerns regarding task ordering, data flow dependencies, and missing validation steps identified in the latest analysis.

- [ ] T082 [P] [US1] **Data Flow Dependency Check**: (Moved to Phase 2 as T082a/b).
- [ ] T083 [P] [US2] **Cross-Validation Fold Integrity**: (Moved to Phase 4 as T083a/b).
- [ ] T084 [P] [US3] **Permutation Importance Statistical Rigor**: (Moved to Phase 5 as T084a/b).
- [ ] T085 [P] **Configuration Lock Verification**: (Moved to Phase 2 as T085a/b).
- [ ] T086 [P] **Final Artifact Consistency Check**: (Moved to Phase T as T086a/b).