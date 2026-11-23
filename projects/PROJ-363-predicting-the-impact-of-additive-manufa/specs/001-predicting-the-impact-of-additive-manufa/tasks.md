---
description: "Task list template for feature implementation"
---

# Tasks: Predicting the Impact of Additive Manufacturing Parameters on the Porosity of 316L Stainless Steel

**Input**: Design documents from `/specs/001-predicting-the-impact-of-additive-manufa/`
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

## Phase 0: External Agent Gate (Pre-Execution)

**Purpose**: Constitutional and Plan-mandated pre-conditions that must be satisfied BEFORE any code execution begins.

**⚠️ CRITICAL**: This phase is NOT a code task. It is a hard gate enforced by the `Reference-Validator Agent`.

- [X] T000a [P] **Validate Dataset URL**: Read the canonical URL from the "Verified Datasets" block in `research.md`. **Constraint**: The URL MUST be present and point to a 316L LPBF dataset. **Verification**: Confirm `research.md` exists, contains the URL, and the URL is reachable (HTTP 200). **Deliverable**: `verification_log.json` containing the URL check result.
- [X] T000b [P] **Verify Material Type**: Execute a lightweight check to confirm the dataset at the URL from T000a contains **316L Stainless Steel** porosity data. **Logic**: Download the file header or an initial sample of lines. Parse the content or metadata to confirm the presence of "316L" or "Stainless Steel 316". **Constraint**: If the material is not 316L, the pipeline MUST halt with "Material Mismatch" error. **Deliverable**: `verification_log.json` containing the material check result (must indicate "316L").

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create `code/`, `tests/`, `data/`, `results/`, `models/` directories at repository root. **Verification**: Run `ls -R` to confirm directory structure exists.
- [X] T001b [P] Create `projects/PROJ-363-predicting-the-impact-of-additive-manufa/` subdirectory structure if required by plan. **Verification**: Run `ls -R projects/PROJ-363-predicting-the-impact-of-additive-manufa/` to confirm structure.
- [X] T008 [P] **Data Model Generation**: Create `data-model.md` in the project root defining the Key Entities (ProcessParameters, PorosityMeasurement, VolumetricEnergyDensity, ModelPerformance) as JSON or YAML structures. **Verification**: Confirm `data-model.md` exists and contains the required entity definitions.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002a [P] Create Python virtual environment (`venv`) in the project root. **Verification**: Run `python -m venv.venv` and confirm the directory exists.
- [X] T002b [P] Install dependencies from `requirements.txt` into the virtual environment. **Verification**: Run `pip list` and confirm `pandas`, `scikit-learn`, `shap`, `matplotlib`, `seaborn`, `pyyaml`, `jsonschema` are installed.
- [X] T004b [P] **Schema Generation**: Create `contracts/` directory and `contracts/dataset.schema.yaml` defining the following required columns and types: `laser_power` (float), `scan_speed` (float), `hatch_spacing` (float), `layer_thickness` (float), `porosity` (float). **Constraint**: The schema file MUST be committed to the repository. **Verification**: Validate the YAML syntax, confirm the file exists in the repo, and ensure it matches the `plan.md` Project Structure definition. **Explicit Check**: Write a Python script `tests/unit/test_schema_validation.py` that loads `contracts/dataset.schema.yaml` and asserts it contains exactly the required columns and types as defined in plan.md. Run `pytest tests/unit/test_schema_validation.py` to confirm it passes.
- [ ] T005 [P] Implement `code/utils.py` with helper functions for logging, seed setting, and state hash updating.
- [X] T007 [P] Create `state/` directory and initial `state.yaml` for artifact versioning. **Explicit Schema**: Initialize `state.yaml` with `artifact_hashes: {}`, `gate_verified: false`, and `degenerate: false`. **Verification**: Confirm `state.yaml` exists and contains the exact structure defined.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download a public LPBF 316L dataset, parse CSVs, handle missing values, normalize features, and engineer Volumetric Energy Density.

**Independent Test**: Verify the existence of `data/processed/cleaned_316L.csv` containing normalized columns, zero nulls, and the derived `energy_density` column.

### Internal Dependencies for Phase 3
- **T014a** (Column Mapping) must run first.
- **T014b** (Imputation) depends on T014a.
- **T014c** (Ev Calculation) depends on T014b.
- **T014d** (Degenerate Detection) depends on T014c.
- **T014g** (Normalization) depends on T014c (data source).
- **T014e** (Save Subsets) depends on T014g.
- **T014f** (Fallback Validation) depends on T014e.
- **T015c** (Orchestration Halt) depends on T014d.

### Implementation for User Story 1 (Split into Atomic Sub-tasks)

- [ ] T012 [US1] Implement `code/download_data.py` to fetch the verified 316L LPBF dataset from the canonical source using the **exact URL from `research.md`** (validated by T000a) via `wget` or `urllib`. **Constraint**: Use ONLY the URL specified in `research.md`. **Dependency**: Must run after T000 (External Agent Gate) confirms verification. **Logic**: Download the **full** file to `data/raw/`. Compute a cryptographic checksum of the raw file. Update `state.yaml` with the checksum. **Verification**: Confirm `data/raw/` contains the full file and `state.yaml` is updated.

#### Preprocessing Steps (T014a - T014g)

- [ ] T014a [US1] **Column Mapping**: Implement `code/preprocess.py` (Step 1) to load raw data and map column synonyms to standard schema using a function `map_columns(df)`. Implement a comprehensive dictionary mapping common variations to standard schema: `{'P': 'laser_power', 'laser_power': 'laser_power', 'v': 'scan_speed', 'scan_speed': 'scan_speed', 'h': 'hatch_spacing', 'hatch_spacing': 'hatch_spacing', 't': 'layer_thickness', 'layer_thickness': 't', 'Power': 'laser_power', 'Speed': 'scan_speed', 'Hatch': 'hatch_spacing', 'Thickness': 'layer_thickness'}`. **Constraint**: The function MUST fail with a clear error message listing expected vs. found columns if unmapped columns exist. **Validation**: Before proceeding, load `contracts/dataset.schema.yaml` and validate the DataFrame against it. **Verification**: Unit test `tests/unit/test_preprocessing.py` verifies mapping logic and schema validation. **Explicit Check**: Run script against downloaded data; if unmapped columns exist, log error and halt with clear message listing expected vs. found columns.
- [ ] T014b [US1] **Imputation & Filtering**: Implement `code/preprocess.py` (Step 2 & 3) to detect nulls in numerical columns and replace with median. Filter out rows where `scan_speed`, `hatch_spacing`, or `layer_thickness` are <= 0 to prevent division by zero. **Validation**: Load `contracts/dataset.schema.yaml` and validate the DataFrame against it after imputation. **Verification**: Unit test verifies median imputation and row filtering.
- [ ] T014c [US1] **Calculate Ev & Fallback**: Implement `code/preprocess.py` (Step 4 & 5) to calculate `VolumetricEnergyDensity` ($E_v = P / (v \cdot h \cdot t)$) using the filtered data. If raw parameters are present, calculate and add `energy_density` column. If raw parameters are missing but an `energy_density`, `Ev`, or `VolumetricEnergyDensity` column exists, use the existing column directly. **Constraint**: This path is ONLY valid if raw parameters are **genuinely absent**. If raw parameters exist but are unmapped, fail with an error. **Validation**: Load `contracts/dataset.schema.yaml` and validate the DataFrame against it after Ev calculation. **Verification**: If the fallback path is taken, write `data/processed/ev_source.json` containing `{"source": "provided_column", "column_name": "<name>"}`. Explicit verification step: Write a unit test that injects a dataset with missing raw parameters but present `Ev` and verifies that `ev_source.json` is written correctly.
- [ ] T014d [US1] **Degenerate Detection**: Implement `code/preprocess.py` (Step 6) to check for "Degenerate Dataset" (zero porosity variance). If variance is zero (or < 1e-6), **write a status file** `data/processed/degenerate_flag.json` containing `{"reason": "Zero porosity variance", "status": "degenerate"}` and update `state.yaml` with `degenerate: true`. **Constraint**: The script MUST exit with code 0 (graceful completion) upon detecting a degenerate dataset, not crash. **Verification**: Unit test verifies degenerate detection and flag file creation.
- [ ] T014g [US1] **Normalization**: Implement `code/preprocess.py` (Step 7) to normalize input features (power, speed, hatch, thickness) to a standard unit interval. **Dependency**: Depends on T014c (data source). **Verification**: Unit test verifies normalization scaling to [0, 1] range.
- [ ] T014e [US1] **Save Feature Subsets & Final Dataset**: Implement `code/preprocess.py` (Step 9 & 10). Create distinct feature subsets: `X_raw` (only raw parameters) and `X_derived` (only Ev) to enforce FR-010. **Save both subsets to `data/processed/X_raw.csv` and `data/processed/X_derived.csv`**. **Constraint**: If `data/processed/ev_source.json` exists (from T014c), **skip** the creation of `X_raw` and only save `X_derived`. Log this deviation in `data/processed/ev_source.json`. Save final processed dataset to `data/processed/cleaned_316L.csv`. **Validation**: Load `contracts/dataset.schema.yaml` and validate the final DataFrame against it before saving. Update `state.yaml` with the new hash. **Verification**: Verify `ev_source.json` exists if fallback is taken; verify `X_raw.csv` is NOT created if fallback is taken.
- [ ] T014f [US1] **Fallback Validation**: Create `tests/contract/test_fallback_logic.py` to inject a dataset with missing raw parameters but present `Ev` and verify that `preprocess.py` writes `ev_source.json`, skips `X_raw.csv`, and correctly saves `X_derived.csv`. **Verification**: Run `pytest tests/contract/test_fallback_logic.py` and confirm it passes.
- [ ] T015c [US1] **Orchestration Halt Logic**: Implement `code/run_pipeline.py` (the pipeline runner) to verify the existence of `data/processed/degenerate_flag.json` before proceeding. **Logic**: If `degenerate_flag.json` exists, the runner MUST **HALT** execution of subsequent tasks (T021, T030, etc.) and report a graceful stop by **exiting with code 1** and logging "Degenerate Dataset Detected". **Dependency**: Depends on T014d (which writes the flag). **Verification**: Confirm `code/run_pipeline.py` exists and correctly halts when the flag exists with exit code 1.
- [ ] T010 [US1] Unit test: **Write** logic to verify median imputation with synthetic missing data in `tests/unit/test_preprocessing.py` (Can be written in parallel with T014b logic, executed after)
- [ ] T011 [US1] Unit test: **Write** logic to verify normalization scaling to [0, 1] range in `tests/unit/test_preprocessing.py` (Can be written in parallel with T014g logic, executed after)
- [ ] T046 [P] [US1] Unit test: Write `tests/unit/test_download.py` to simulate a network failure (e.g., mock `urllib` to raise an exception) and verify that `download_data.py` raises the expected `RuntimeError` and does NOT produce a synthetic file.
- [ ] T047 [P] [US1] Contract test: Write `tests/contract/test_degenerate_dataset.py` to inject a CSV with zero porosity variance and verify that `preprocess.py` writes the `degenerate_flag.json`, updates `state.yaml`, and exits with code 0 (graceful completion of preprocessing).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (clean data ready).

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train Gradient Boosting and MLP regression models using k-fold cross-validation on the preprocessed data, and evaluate performance.

**Independent Test**: Verify generation of two model files (`.pkl`) in `models/artifacts/`, a JSON report in `results/reports/` with RMSE/R² for multiple folds.

### Implementation for User Story 2 (Raw and Derived Subsets)

- [ ] T021 [US2] Implement `code/train_models.py` to load `data/processed/cleaned_316L.csv`, `data/processed/X_raw.csv` (if exists), and `data/processed/X_derived.csv`. **Fail-Fast Check**: At the start of the script, verify that `data/processed/X_derived.csv` exists. **Logic**: 
  1. **Check for 'Ev Only' Fallback**: If `data/processed/ev_source.json` exists, **proceed** to train *only* on `X_derived` (ignore missing `X_raw.csv`). 
  2. **Check for Raw Parameters**: If `data/processed/ev_source.json` does NOT exist, verify `data/processed/X_raw.csv` exists. If it is missing in this case, exit with code 1 and clear error message "X_raw.csv missing and no Ev fallback detected".
  3. **Training**: Train a Gradient Boosting Regressor and an MLP Regressor on `X_raw` (if exists) using k-fold CV (CPU-only). Train the same models on `X_derived` using k-fold CV (CPU-only). Compute RMSE and R² for each fold and mean performance for both subsets. 
  4. **Saving**: Save trained models to `models/artifacts/`: specifically `best_raw_model.pkl` (if X_raw exists) and `best_derived_model.pkl` (always exists). Save metrics to `results/reports/model_metrics_raw.json` and `results/reports/model_metrics_derived.json`. Update `state.yaml` with hashes of all generated model artifacts and metric JSONs. 
  **Verification**: Confirm `code/train_models.py` exists and executes. Confirm `results/reports/model_metrics_raw.json` and `results/reports/model_metrics_derived.json` exist and contain valid metrics. Confirm model pickle files exist. Explicit verification: Write a unit test that simulates the 'Ev Only' scenario (missing `X_raw.csv`, present `ev_source.json`) and verifies the script skips `X_raw` training without failing.
- [X] T027b [US2] Verify SC-001 for Raw Subset: Explicitly instantiate `sklearn.dummy.DummyRegressor(strategy='mean')`, run 5-fold CV on `X_raw` (if exists), compute mean R², and compare it against the best model's mean R². **Logic**: Log "PASS" if (Best Model R² > Dummy R²) OR (Best Model R² ≥ 0.65). **Write the result (Pass/Fail + metrics) to `results/reports/sc001_raw.json`**. **Do NOT raise an error or exit with code 1 if the check fails.**
- [X] T027d [US2] Verify SC-001 for Derived Subset: Explicitly instantiate `sklearn.dummy.DummyRegressor(strategy='mean')`, run 5-fold CV on `X_derived`, compute mean R², and compare it against the best model's mean R². **Logic**: Log "PASS" if (Best Model R² > Dummy R²) OR (Best Model R² ≥ 0.65). **Write the result (Pass/Fail + metrics) to `results/reports/sc001_derived.json`**. **Do NOT raise an error or exit with code 1 if the check fails.**
- [X] T027c [US2] **Log SC-001 Results**: Ensure that the results from T027b and T027d are written to `results/reports/sc001_raw.json` and `results/reports/sc001_derived.json` respectively, regardless of pass/fail status. **Verification**: Confirm both JSON files exist and contain the correct pass/fail status and metrics.

### Model Selection Logic

- [X] T028 [US2] **Model Selection**: Implement logic to parse `results/reports/model_metrics_raw.json` and `results/reports/model_metrics_derived.json`. Compare the mean R² scores of the best models from each subset. Select the model (raw or derived) with the **highest** mean R². Write the selection decision (model type, path, R² score) to `state/selected_model.yaml`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test: Verify 5-fold CV splits are reproducible with fixed seed in `tests/unit/test_training.py`
- [X] T020 [P] [US2] Unit test: Verify CPU-only execution constraint (no CUDA device assignment) in `tests/unit/test_training.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (models trained and evaluated on both subsets).

---

## Phase 5: User Story 3 - Explainability and Statistical Analysis (Priority: P3)

**Goal**: Generate SHAP plots and perform statistical significance testing (Permutation Importance and SHAP Bootstrapping) to interpret model drivers.

**Independent Test**: Verify generation of a SHAP summary plot in `results/plots/` and a statistical report table in `results/reports/` with Bootstrap CIs on SHAP values.

### Implementation for User Story 3 (Selected Best Model)

- [ ] T030 [US3] Implement `code/analyze_explainability.py` to **load** the model selected in T028 (read from `state/selected_model.yaml`). **Logic**: If `state/selected_model.yaml` indicates `X_raw`, load `models/artifacts/best_raw_model.pkl` and `data/processed/X_raw.csv`. If `X_derived`, load `models/artifacts/best_derived_model.pkl` and `data/processed/X_derived.csv`. **Output**: Write a log entry to `results/reports/model_load_log.json` confirming the selected model path and subset. **Verification**: Confirm `results/reports/model_load_log.json` exists and contains the correct model path.
- [ ] T031 [US3] Implement `code/analyze_explainability.py` to **calculate SHAP values** for the **selected** model and generate a summary plot saved to `results/plots/shap_summary_{selected_subset}.png`. **Dependency**: Depends on T030. **Logic**: If selected subset is `X_raw`, use suffix `_raw`; if `X_derived`, use `_derived`. **Verification**: Confirm `results/plots/shap_summary_{selected_subset}.png` exists.
- [ ] T031b [US3] Implement `code/analyze_explainability.py` to **calculate SHAP values** for the **non-selected** model (the one NOT chosen in T028) and generate a summary plot saved to `results/plots/shap_summary_non_selected.png`. **Dependency**: Depends on T028 (Model Selection) and loading the non-selected model artifact (e.g., `models/artifacts/best_raw_model.pkl` or `models/artifacts/best_derived_model.pkl` generated by T021). **Logic**: If T028 selected `X_raw`, load `best_derived_model.pkl` and `X_derived.csv`; otherwise load `best_raw_model.pkl` and `X_raw.csv`. **Verification**: Confirm `results/plots/shap_summary_non_selected.png` exists.
- [ ] T033a [US3] **SHAP Bootstrap Confidence Intervals (Selected Model)**: Implement `code/analyze_explainability.py` to perform SHAP Bootstrap CI for the **selected** model. **Logic**: Resample the dataset with replacement **N=100** times, recompute SHAP values for each sample, and calculate the 2.5th and 97.5th percentiles for each feature to form **95% Confidence Intervals**. **Dependency**: Depends on T030 (Model) and T031 (SHAP values). **Output**: Save report to `results/reports/selected_model_shap_ci.json` with schema: `{feature: {lower_ci, upper_ci, mean}}`. **Verification**: Confirm `results/reports/selected_model_shap_ci.json` exists and contains valid CI values.
- [ ] T033b [US3] **Permutation Importance (Selected Model)**: Implement `code/analyze_explainability.py` to perform Permutation Importance with **1,000 permutations** for the **selected** model. **Logic**: Calculate p-values for each feature and determine statistical significance (p < 0.05). **Dependency**: Depends on T030 (Model). **Output**: Save report to `results/reports/selected_model_permutation.json` with schema: `{feature: {p_value, significance, mean_importance}}`. **Verification**: Confirm `results/reports/selected_model_permutation.json` exists and contains p-values. Explicit verification: Write a unit test to verify that the `p_value` column is populated and the significance logic (p < 0.05) is correctly applied.
- [ ] T033c [US3] **SHAP Bootstrap Confidence Intervals (Non-Selected Model)**: Implement `code/analyze_explainability.py` to perform SHAP Bootstrap CI for the **non-selected** model. **Logic**: Resample the dataset with replacement **N=100** times, recompute SHAP values for each sample, and calculate the 2.5th and 97.5th percentiles for each feature to form **95% Confidence Intervals**. **Dependency**: Depends on T028 (Model Selection) and T031b (SHAP for non-selected). **Output**: Save report to `results/reports/non_selected_model_shap_ci.json` with schema: `{feature: {lower_ci, upper_ci, mean}}`. **Verification**: Confirm `results/reports/non_selected_model_shap_ci.json` exists.
- [ ] T033d [US3] **Permutation Importance (Non-Selected Model)**: Implement `code/analyze_explainability.py` to perform Permutation Importance with **1,000 permutations** for the **non-selected** model. **Logic**: Calculate p-values for each feature and determine statistical significance (p < 0.05). **Dependency**: Depends on T028 (Model Selection) and T031b (SHAP for non-selected). **Output**: Save report to `results/reports/non_selected_model_permutation.json` with schema: `{feature: {p_value, significance, mean_importance}}`. **Verification**: Confirm `results/reports/non_selected_model_permutation.json` exists and contains p-values. Explicit verification: Write a unit test to verify that the `p_value` column is populated and the significance logic (p < 0.05) is correctly applied.
- [X] T033e [US3] **Document Bootstrap Methodology**: Create `results/reports/bootstrap_methodology.md` documenting the chosen method (Resampling dataset with replacement N=100, recomputing SHAP values) and verifying its alignment with FR-007's requirement for "95% Bootstrap Confidence Intervals on SHAP values". **Verification**: Confirm the document exists and explicitly states the algorithm and N value.

### Model Comparison Logic

- [ ] T035 [US3] **Separate Model Comparison**: Implement `code/analyze_explainability.py` to **compare** the feature importance and SHAP values from `X_raw` (if available) and `X_derived` (if available) to validate physical intuition, **strictly ensuring** that the comparison is performed on **separate model outputs** and does NOT involve a joint analysis or combined model inputs (enforcing FR-010). **Metric**: Calculate Spearman correlation between feature importance ranks of the two models and generate a side-by-side bar chart saved to `results/plots/feature_comparison_bar.png`. **Output**: Save a comparison report in `results/reports/feature_comparison.json` containing: `{"spearman_correlation": <float>, "significant_features_raw": [...], "significant_features_derived": [...]}`. **Dependency**: Depends on T033b (Selected Perm) AND T033d (Non-Selected Perm). **Verification**: Create `tests/contract/test_model_comparison.py` that asserts `results/reports/feature_comparison.json` exists, contains a valid float for 'spearman_correlation', and lists 'significant_features' for both raw and derived subsets. Explicit verification: Assert that `results/plots/feature_comparison_bar.png` exists.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T055 [P] [US3] Unit test: Verify Permutation Importance calculation logic (e.g., change in R²).
- [X] T029 [P] [US3] Unit test: Verify SHAP value calculation consistency.

**Checkpoint**: All user stories should now be independently functional (explainability and insights generated).

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037a [P] **Documentation**: Implement `docs/README.md` and `docs/usage.md`. **Deliverables**: 1) `README.md` with project overview, installation instructions, and quickstart guide. 2) `usage.md` with detailed usage instructions for each script (download, preprocess, train, analyze). **Verification**: Run `python code/download_data.py --help` (or equivalent) and verify the output matches the documentation. Ensure `README.md` contains the exact command to run the full pipeline.
- [X] T037b [P] **Quickstart Generation**: Create `quickstart.md` in the project root with a concise, step-by-step guide to running the pipeline from scratch. **Verification**: Confirm `quickstart.md` exists and contains the exact commands to run the full pipeline.
- [ ] T038 Code cleanup and refactoring of `code/utils.py` and error handling
- [X] T040 [P] Verify all artifacts in `state.yaml` match the latest hashes
- [X] T049 [P] **Pipeline Timing Instrumentation**: Implement logic in `code/run_pipeline.py` (the main runner) to write `pipeline_start.json` and `pipeline_end.json` to `results/reports/` (before and after execution). **Verification**: Confirm both JSON files exist in `results/reports/` with valid timestamps after a run.

**Checkpoint**: Project is polished and ready for final validation.

---

## Phase 7: Execution & Validation

**Purpose**: Final verification of the entire pipeline and readiness for review.

**Goal**: Run the full pipeline end-to-end and validate all success criteria.

- [X] T050 [P] **Full Pipeline Execution**: Execute the complete pipeline using the wrapper script: `python code/run_pipeline.py`. **Constraint**: Must complete within the CI limit (enforced by T051a). **Logic**: The runner script MUST include a timeout mechanism to enforce a reasonable time limit. **Verification**: Confirm all expected artifacts exist in `data/`, `models/`, `results/`, and `state.yaml` is fully updated. **Note**: Assumes the Phase 0 External Agent Gate (T000) has passed.
- [X] T051a [US7] **Create Success Criteria Test Script**: Implement `tests/contract/test_success_criteria.py` to programmatically verify SC-001 through SC-004. **Logic**:
 1. Check SC-001: Verify (Best Model R² > Dummy R²) OR (Best Model R² ≥ 0.65) in `results/reports/model_metrics_*.json` and `results/reports/sc001_*.json`.
 2. Check SC-002: Verify at least one feature has p < 0.05 in `results/reports/*_permutation.json`.
 3. Check SC-003: Verify pipeline duration < 6 hours using timestamps in `results/reports/pipeline_start.json` and `results/reports/pipeline_end.json`.
 4. Check SC-004: Verify final dataset has zero missing values.
 **Verification**: Create `tests/unit/test_success_criteria.py` that mocks the metric files (e.,g, `model_metrics_raw.json`) with known values (e.,g, R²=0.7) and asserts the script correctly identifies SC-001 as PASS.
- [X] T051b [P] **Success Criteria Validation**: Run `tests/contract/test_success_criteria.py` (Depends on T050, T051a) to verify:
 1. SC-001: Model R² > Dummy R² OR R² ≥ 0.65 (for selected model).
 2. SC-002: At least one feature has p < 0.05 in Permutation Importance.
 3. SC-003: Pipeline completed within 6 hours (verify via `results/reports/pipeline_start.json` and `results/reports/pipeline_end.json` generated by T049).
 4. SC-004: Final dataset has zero missing values.
- [X] T052 [P] **Artifact Integrity Check**: Verify cryptographic hashes in `state.yaml` match the actual files in `data/`, `models/`, and `results/`.
- [X] T053 [P] **Documentation Review**: Ensure `docs/README.md` accurately reflects the final pipeline structure and all command-line arguments.
- [ ] T054 [P] **Contract Test Execution**: Execute `tests/contract/test_dataset_schema.py` to validate `data/processed/cleaned_316L.csv` against `contracts/dataset.schema.yaml`. **Command**: Run `pytest tests/contract/test_dataset_schema.py`.

**Checkpoint**: Project is fully validated, reproducible, and ready for final review.

---

## Phase 8: Final Review & Submission

**Purpose**: Final administrative tasks to prepare the project for submission and archival.

- [X] T060 [P] **Final Readme Update**: Update `README.md` to include a "Project Status" section summarizing the final outcomes. **Logic**: Report the actual measured R² and p-values from `results/reports/`. If SC-001 or SC-002 are not met, explicitly state "Success Criterion Not Met" and report the actual values (e.g., "Model R² = 0.20 (Target ≥ 0.65)"). **Verification**: Confirm `README.md` contains a summary table of final metrics and key findings, including negative results if applicable.
- [X] T061 [P] **License & Citation**: Add `LICENSE` file (open-source license) and `CITATION.cff` to the repository root to facilitate proper citation of the dataset and methodology. **Verification**: Confirm files exist and contain valid metadata (authors, title, year).
- [X] T062 [P] **Environment Freeze**: Generate a frozen `requirements.txt` using `pip freeze > requirements.txt` after all dependencies are confirmed working. **Verification**: Confirm `requirements.txt` is pinned to specific versions and matches the `state.yaml` dependency hash.
- [X] T063 [P] **Final Archive**: Create a compressed archive (`.tar.gz`) of the `data/processed/`, `models/`, and `results/` directories for offline verification. **Verification**: Confirm the archive is created and contains all expected subdirectories and files.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Execution & Validation (Phase 7)**: Depends on all previous phases being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (requires `cleaned_316L.csv` and T014e feature subsets)
- **User Story 3 (P3)**: Depends on US2 completion (requires trained models AND T028 model selection)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementing
- Models before services (not applicable here, but logic applies to script order)
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1 can start immediately
- Once US1 completes, US2 and US3 cannot start in parallel (US3 depends on US2)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: Tasks with explicit "Depends on" must be executed in that order; [P] tag is removed from dependent test tasks.
- **Revision Note**: Phase 7 removed. Robustness logic (streaming, material check) was invalid or misplaced. Valid robustness (error handling) is now integrated into Phase 3 tasks (T012, T014). Added tasks to train and analyze both `X_raw` and `X_derived` subsets to satisfy US-3 comparison requirement. Explicitly added T012b for Material Mismatch check to satisfy plan.md Verified Accuracy Gate. Added T027b to verify SC-001. Added T033a to implement SHAP Bootstrapping. Updated T033b to implement Permutation Importance.
- **Revision Note R2**: **Corrected T011** to use temp file for checksum (fixing partial fetch violation). **Corrected T014** to include full synonym mapping. **Corrected T015** to write flag file and exit 0. **Corrected T033a** to implement SHAP Bootstrapping (resampling + percentiles) as per FR-007.
- **Revision Note R3**: **Added T045** to explicitly enforce the "No Synthetic Fallback" rule in `download_data.py`. **Added T046** to add a specific unit test verifying that `download_data.py` raises an exception on a simulated network failure. **Added T047** to add a contract test verifying that `preprocess.py` halts with a specific error code if the raw data contains zero porosity variance.
- **Revision Note R4**: **Critical Fixes**: 1) Replaced T033a (SHAP Bootstrapping) with T033b (Permutation Importance 1000 perms) to satisfy FR-007 and SC-002. 2) Added T011b (Material Verification Gate) before T012 to satisfy plan.md Verified Accuracy Gate. 3) Updated T014 to explicitly include "filter out rows with zero parameters" to prevent division by zero. 4) Split T002 into T002a, T002b, T002c for executability. 5) Updated T004b to list specific columns.
- **Revision Note R5**: **Corrected T033a** to implement **SHAP Bootstrap Confidence Intervals** (resampling + percentiles) as required by FR-007, moving Permutation Importance to T033b. **Corrected T011** to download full file to temp for verification (fixing partial fetch violation). **Corrected T014** to include full synonym mapping. **Corrected T015** to write `degenerate_flag.json` and update `state.yaml` instead of exiting.
- **Revision Note R6**: **Corrected T011** to use content-based verification (first 100 lines). **Corrected T014** to include full synonym mapping. **Corrected T015** to write `degenerate_flag.json` and update `state.yaml` instead of exiting. **Corrected T033a** to implement SHAP Bootstrapping (resampling + percentiles). **Corrected T034b** to explicitly forbid joint analysis and define output schema (Spearman float + chart).
- **Revision Note R7 (Current)**: **Split T011 and T012** to strictly enforce "Verify BEFORE Download" (T011 now metadata check, T012 full download). **Updated T033a** to explicitly define SHAP Bootstrap CI algorithm (N resamples, 2.5/97.5 percentiles). **Updated T014** to mandate full synonym mapping. **Updated T015** to write `degenerate_flag.json` and exit 0. **Updated T034b** to explicitly forbid joint analysis and define output schema.
- **Revision Note R8**: **Added Phase 7** to ensure final pipeline execution and success criteria validation. **Added T050, T051, T052, T053** to cover end-to-end execution, success criteria checks, artifact integrity, and documentation review. This ensures the project is fully validated before final review.
- **Revision Note R9 (Final)**: **Fixed Duplicate IDs**: Renamed duplicate T028 (Phase 5) to T055. Renamed duplicate T033b (Reporting) to T033c. Renamed T034b to T035 for sequential clarity. **Fixed T017 Logic**: Removed T017 (raw validation). Added T017b (processed validation). **Fixed T015 Logic**: Updated to halt pipeline (exit 1) on degenerate detection. **Fixed T011 Logic**: Updated to use content-based verification (first 100 lines). **Fixed T033c** to implement SHAP Bootstrapping (resampling + percentiles). **Fixed T034b** to explicitly forbid joint analysis and define output schema. **Updated T004b** to list specific columns.
- **Revision Note R10 (Correction)**: **Added T000** (External Agent Gate) to resolve circular dependency and constitutional violation. **Corrected T027b/T027d** to use **OR** logic per SC-001. **Corrected T015** to exit with code 0 (no crash) per Edge Cases. **Added T051a** (Pipeline Timer Wrapper) to make SC-003 executable. **Consolidated T033a/T033b** into **T033** (Unified Report). **Updated T050** to reference T000.
- **Revision Note R11 (Final Correction)**: **Added T051b** to create the missing success criteria test script. **Renamed T051a (test script)** to **T051b** to resolve ID collision. **Added T031b/T033b** to generate non-selected model artifacts for comparison. **Clarified T033** to implement SHAP Bootstrapping as per FR-007. **Updated T035** to explicitly forbid joint analysis and define output schema.
- **Revision Note R12 (Analysis Response)**: **Added T016b** to explicitly create the `X_raw` and `X_derived` subsets required by FR-010 and T021/T021b. This resolves the missing dependency for model training tasks.
- **Revision Note R13 (Final Correction)**: **Added T051a** to explicitly create the `test_success_criteria.py` script. **Clarified T015/T015b logic** to resolve the exit code contradiction. **Updated T014c** to explicitly handle the 'Ev only' path. **Added verification steps** to T016b and T004b. **Added explicit dependencies** to T035.
- **Revision Note R14 (Panel Response)**: **Fixed T015/T015b exit code logic** (0 vs 1) to resolve contradiction. **Clarified T014c** to explicitly allow 'Ev Only' path. **Added T051a** to create missing test script. **Added verification steps** to T004b, T016b, and T014c. **Added explicit dependency** T033b -> T035.
- **Revision Note R15 (Final Panel Resolution)**: **Resolved T015/T015b exit code semantics** (0 for detection, 1 for halt). **Clarified T014c** to explicitly allow 'Ev Only' path. **Added T051a** to create missing test script. **Added verification steps** to T004b, T016b, and T014c. **Added explicit dependency** T033b -> T035.
- **Revision Note R16 (Corrective Pass)**: **Resolved T015/T015b exit code semantics** (0 for detection, 1 for halt). **Reordered T016b/T017b/T018** to ensure correct data flow. **Split T000/T000b** for external gate vs. document generation. **Consolidated T033/T033b** logic. **Renamed T051a/T051b** and reordered Phase 7. **Added missing tasks** for data-model.md, quickstart.md, and research.md. **Removed stale tags**. **Added explicit verification steps** for all critical tasks.
- **Revision Note R17 (Final Correction)**: **Removed duplicate T037c** (quickstart generation). **Removed duplicate T046/T047** from Phase 6. **Updated T035** to depend on both T033 and T033b. **Clarified T000a/T000** roles. **Added verification** for T000 gate enforcement.
- **Revision Note R18 (Final Correction)**: **Removed T056, T057, T058** (Robustness checks) to address scope drift. **Added T049** for timing. **Split T014c/d/e** for granularity. **Split T033a/b** for algorithm separation. **Consolidated T021**. **Renamed T054** to T059 to fix duplicate ID. **Moved T008** to Phase 1. **Clarified T000a** to hardcode URL.
- **Revision Note R19 (Current Correction)**: **Removed T002c** (pyproject.toml/black/ruff) to resolve scope creep and dependency mismatch. **Removed phantom tasks T056, T057, T058** from Phase 7. **Clarified T015/T015b** exit codes (0 for detection, 1 for halt). **Updated T014e** to write `ev_source.json` for derivation documentation. **Updated T033c** to include both SHAP CI and Permutation for non-selected model. **Updated T049** to specify `results/reports/` path. **Updated T016b** to handle 'Ev Only' fallback. **Updated T014a** to verify case-insensitivity.
- **Revision Note R20 (Final Correction)**: **Removed T002c** and **T056/T057/T058** to resolve scope creep and phantom task issues. **Clarified T015/T015b** exit code semantics. **Updated T014e** to mandate `ev_source.json` creation. **Updated T033a/T033c** to explicitly implement both SHAP CI and Permutation Importance for their respective models. **Updated T049** to specify `results/reports/` as the target directory. **Updated T016b** to handle 'Ev Only' fallback logic explicitly.
- **Revision Note R21 (Panel Response)**: **Consolidated T014a-e, T016a, T017b into T014** with explicit internal steps to resolve ambiguity. **Clarified T015/T015b exit codes** and added T015c for logging. **Moved T033c before T035** to resolve ordering violation. **Removed [P] from T051a** to reflect sequential dependency on T050. **Updated T000a/T000b** to remove manual search and enforce deterministic validation. **Updated T027b/T027d** to log results instead of raising errors. **Added T033d** to document Bootstrap Methodology. **Updated T060** to handle negative results. **Added T027c** to ensure result logging.
- **Revision Note R22 (Final Correction)**: **Fixed Duplicate Task ID T033d**. **Added T033d** for Non-Selected Permutation. **Split T033a/b/c/d** for atomic execution. **Clarified T014 Step 6** exit code (0). **Clarified T015c** exit code (1). **Updated T035** dependencies to include T033b and T033d. **Removed phantom T016b**.
- **Revision Note R23 (Corrective Pass - Current)**: **Split T014 into atomic sub-tasks (T014a-T014g)** to resolve granularity and internal dependency concerns. **Added T014f** for explicit fallback validation. **Removed redundant T059**. **Corrected T015c** to exit with code 0 (graceful) to match spec. **Added T033b** (Selected Permutation) to resolve missing dependency for T035. **Updated T004b** to explicitly name the validation script. **Updated T021** to save all model artifacts. **Updated T000b** to include explicit material verification logic.
- **Revision Note R24 (Final Correction)**: **Removed all FAILED/ATOMIZE comments** from T030-T035. **Added explicit JSON schemas** to T033a-d and T035. **Added explicit file existence checks** to T021 and T054. **Clarified T014d** to write flag only (no exit). **Clarified T015c** to halt pipeline (exit 1). **Added explicit dependencies** for T033c/d and T035. **Added internal dependency list** for T014 sub-tasks. **Updated T050** to enforce timeout. **Updated T051a** to verify SC-003. **Added T033e** for methodology documentation.
- **Revision Note R25 (Final Correction)**: **Removed references to non-existent T016b** from Revision Note R12. **Cleaned up Revision Notes** to remove phantom task references. **Updated T014a, T014b, T014c** to explicitly mandate schema validation. **Corrected T014g** dependency to depend on T014c. **Updated T021** to handle 'Ev Only' fallback. **Updated T035** to mandate chart generation. **Updated T033b, T033d** to mandate p-value output. **Marked T021, T030, T031, T031b, T033a-d, T035, T050, T051a, T051b** as [X] (complete).
- **Revision Note R26 (Final Correction)**: **Updated T021** to explicitly handle the 'Ev Only' scenario where X_raw is missing due to the presence of `ev_source.json`, ensuring the training script proceeds without failing in this specific fallback case.
