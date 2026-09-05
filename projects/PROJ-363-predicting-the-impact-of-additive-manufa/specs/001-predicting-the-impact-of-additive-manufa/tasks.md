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

- [X] T001a [P] Create `code/`, `tests/`, `data/`, `results/`, `models/` directories at repository root. **Verification**: Run `ls -R` to confirm directory structure exists.
- [X] T001b [P] Create `projects/PROJ-363-predicting-the-impact-of-additive-manufa/` subdirectory structure if required by plan. **Verification**: Run `ls -R projects/PROJ-363-predicting-the-impact-of-additive-manufa/` to confirm structure.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002a [P] Create Python virtual environment (`venv`) in the project root. **Verification**: Run `python -m venv.venv` and confirm the directory exists.
- [X] T002b [P] Install dependencies from `requirements.txt` into the virtual environment. **Verification**: Run `pip list` and confirm `pandas`, `scikit-learn`, `shap`, `matplotlib`, `seaborn`, `pyyaml`, `jsonschema` are installed.
- [X] T002c [P] Initialize project configuration (e.g., `pyproject.toml` or `setup.cfg`) for linting and formatting. **Verification**: Run `black --version` and `ruff --version` to confirm tools are available.
- [X] T004b [P] **Schema Generation**: Create `contracts/` directory and `contracts/dataset.schema.yaml` defining the following required columns and types: `laser_power` (float), `scan_speed` (float), `hatch_spacing` (float), `layer_thickness` (float), `porosity` (float). **Verification**: Validate the YAML syntax and ensure it matches the `plan.md` Project Structure definition.
- [X] T005 [P] Implement `code/utils.py` with helper functions for logging, seed setting, and state hash updating.
- [X] T007 Create `state/` directory and initial `state.yaml` for artifact versioning.
- [X] T011 [P] **Verified Accuracy Gate (Material Check)**: Implement `code/verify_material.py` to perform the mandatory pre-download check. **Logic**: 1) Read the target dataset URL from `plan.md` or `research.md`. 2) Download the **first 100 lines** of the CSV file to a temporary location. 3) Search the content for the string "316L" (case-insensitive). 4) **If found**: Write a `verification_status.json` to `data/raw/` with `{"verified": true, "material": "316L", "timestamp": "..."}` and delete the temp file. 5) **If NOT found**: Raise a `RuntimeError` with "Material Mismatch: Expected 316L, not found in content" and exit with code 1. **Constraint**: This task MUST run BEFORE T012 (Download) and MUST NOT download the full dataset. **Verification**: Run `python code/verify_material.py` against a known 316L URL and a non-316L URL to confirm it passes and fails correctly.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Download a public LPBF 316L dataset, parse CSVs, handle missing values, normalize features, and engineer Volumetric Energy Density.

**Independent Test**: Verify the existence of `data/processed/cleaned_316L.csv` containing normalized columns, zero nulls, and the derived `energy_density` column.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/download_data.py` to fetch the verified 316L LPBF dataset from the canonical source (Zenodo/OpenML) using `wget` or `urllib`. **Constraint**: Use ONLY the URL specified in the `plan.md` "Verified Datasets" block. **Dependency**: Must run after T011 (Verification) confirms `verification_status.json` exists. **Logic**: Download the **full** file to `data/raw/`. Compute a cryptographic checksum of the raw file. Update `state.yaml` with the checksum. **Verification**: Confirm `data/raw/` contains the full file and `state.yaml` is updated.
- [X] T014 [US1] Implement `code/preprocess.py` to load raw data, map column synonyms, and impute missing numerical values using the **median** of the respective column. **Synonym Mapping Logic**: Implement a comprehensive dictionary mapping common variations to standard schema: `{'P': 'laser_power', 'laser_power': 'laser_power', 'v': 'scan_speed', 'scan_speed': 'scan_speed', 'h': 'hatch_spacing', 'hatch_spacing': 'hatch_spacing', 't': 'layer_thickness', 'layer_thickness': 'layer_thickness', 'Power': 'laser_power', 'Speed': 'scan_speed', 'Hatch': 'hatch_spacing', 'Thickness': 'layer_thickness'}`. If a required column is found with an unmapped name, **fail gracefully** with a clear error listing expected vs. found columns. **Logic for Ev**: 1) **Filter out** rows where `scan_speed`, `hatch_spacing`, or `layer_thickness` are <= 0 to prevent division by zero. 2) If raw parameters (power, speed, hatch, thickness) are present, **calculate** `VolumetricEnergyDensity` ($E_v = P / (v \cdot h \cdot t)$) for every record where parameters > 0. 3) If raw parameters are missing but an `energy_density`, `Ev`, or `VolumetricEnergyDensity` column exists, **use** the provided column. **Only** if NEITHER raw parameters nor an energy density column exist, raise a clear error and halt. Do NOT fall back to synthetic data. **Note on Zero Variance**: If any input feature (power, speed, etc.) has zero variance after imputation, log a warning but retain the feature; only halt if the target variable (porosity) has zero variance.
- [X] T015 [US1] Implement `code/preprocess.py` to detect "Degenerate Dataset" (zero porosity variance). **Logic**: Run this check immediately after T014 (post-imputation). If variance is zero (or < 1e-6), **write a status file** `data/processed/degenerate_flag.json` containing `{"reason": "Zero porosity variance", "status": "degenerate"}` and update `state.yaml` with `degenerate: true`. Then **raise `SystemExit(1)`** to halt the pipeline immediately, preventing downstream tasks (T016, T018) from running. **Verification**: Confirm the flag file, state update, and pipeline halt exist after running on a degenerate dataset.
- [X] T016a [US1] Implement `code/preprocess.py` to normalize input features (power, speed, hatch, thickness) to [0, 1] range.
- [X] T016b [US1] Implement `code/preprocess.py` to create distinct feature subsets: `X_raw` (only raw parameters) and `X_derived` (only Ev) to enforce FR-010 (no multicollinearity). **Save both subsets to `data/processed/X_raw.csv` and `data/processed/X_derived.csv`**.
- [X] T017b [US1] Implement `code/preprocess.py` to validate the **processed** data against `contracts/dataset.schema.yaml` (Depends on T004b, T014). **Logic**: Load the schema and validate the DataFrame (post-mapping, post-imputation, post-normalization). Exit with clear error if validation fails. **Verification**: Confirm validation passes on clean data and fails on malformed data.
- [X] T018 [US1] Save final processed dataset to `data/processed/cleaned_316L.csv` and update `state.yaml` with the new hash.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Contract tests ensure data integrity before modeling. These tasks depend on implementation tasks and CANNOT run in parallel with them.

- [ ] T054 [US1] Contract test: Validate `data/processed/cleaned_316L.csv` against `contracts/dataset.schema.yaml` in `tests/contract/test_dataset_schema.py` (Depends on T004b, T018)
- [X] T010 [US1] Unit test: **Write** logic to verify median imputation with synthetic missing data in `tests/unit/test_preprocessing.py` (Can be written in parallel with T014 logic, executed after)
- [X] T011b [US1] Unit test: **Write** logic to verify normalization scaling to [0, 1] range in `tests/unit/test_preprocessing.py` (Can be written in parallel with T016a logic, executed after)
- [X] T046 [P] [US1] Unit test: Write `tests/unit/test_download.py` to simulate a network failure (e.g., mock `urllib` to raise an exception) and verify that `download_data.py` raises the expected `RuntimeError` and does NOT produce a synthetic file.
- [X] T047 [P] [US1] Contract test: Write `tests/contract/test_degenerate_dataset.py` to inject a CSV with zero porosity variance and verify that `preprocess.py` writes the `degenerate_flag.json`, updates `state.yaml`, and exits with code 1.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (clean data ready).

---

## Phase 4: User Story 2 - Model Training and Validation (Priority: P2)

**Goal**: Train Gradient Boosting and MLP regression models using k-fold cross-validation on the preprocessed data, and evaluate performance.

**Independent Test**: Verify generation of two model files (`.pkl`) in `models/artifacts/`, a JSON report in `results/reports/` with RMSE/R² for 5 folds.

### Implementation for User Story 2 (Raw Parameters)

- [X] T021 [US2] Implement `code/train_models.py` to load `data/processed/cleaned_316L.csv` (Depends on T018) and the `data/processed/X_raw.csv` (Depends on T016b), split into features (X) and target (y).
- [X] T022 [US2] Implement `code/train_models.py` to train a Gradient Boosting Regressor on `X_raw` using 5-fold CV, ensuring no GPU usage.
- [X] T023 [US2] Implement `code/train_models.py` to train a Multi-Layer Perceptron (MLP) Regressor on `X_raw` using 5-fold CV, ensuring CPU-only execution and fixed seed.
- [X] T024 [US2] Implement `code/train_models.py` to compute RMSE and R² for each of the 5 folds and the aggregate mean performance for `X_raw` models.
- [X] T025 [US2] Save trained Gradient Boosting and MLP models (trained on `X_raw`) to `models/artifacts/` (`.pkl` format).
- [X] T026 [US2] Save performance metrics (RMSE, R² per fold, mean) for `X_raw` to `results/reports/model_metrics_raw.json`.
- [X] T027 [US2] Update `state.yaml` with hashes of model artifacts and metrics report for `X_raw`.
- [X] T027b [US2] Verify SC-001: Explicitly instantiate `sklearn.dummy.DummyRegressor(strategy='mean')`, run 5-fold CV on `X_raw`, compute mean R², and compare it against the best model's mean R². **Logic**: Log "PASS" if (Best Model R² > Dummy R²) AND (Best Model R² ≥ 0.65). **If FAIL, raise `RuntimeError` with "Success Criterion SC-001 Failed" and exit(1)**. Write the result to `results/reports/model_metrics_raw.json` under the key `sc001_success_check`.

### Implementation for User Story 2 (Derived Feature Subset)

- [X] T021b [US2] Implement `code/train_models.py` to load `data/processed/cleaned_316L.csv` and the `data/processed/X_derived.csv`, split into features (X) and target (y).
- [X] T022b [US2] Implement `code/train_models.py` to train a Gradient Boosting Regressor on `X_derived` using 5-fold CV.
- [X] T023b [US2] Implement `code/train_models.py` to train a Multi-Layer Perceptron (MLP) Regressor on `X_derived` using 5-fold CV.
- [X] T024b [US2] Implement `code/train_models.py` to compute RMSE and R² for each of the 5 folds and the aggregate mean performance for `X_derived` models.
- [X] T025b [US2] Save trained Gradient Boosting and MLP models (trained on `X_derived`) to `models/artifacts/` (`.pkl` format).
- [X] T026b [US2] Save performance metrics (RMSE, R² per fold, mean) for `X_derived` to `results/reports/model_metrics_derived.json`.
- [X] T027c [US2] Update `state.yaml` with hashes of model artifacts and metrics report for `X_derived`.
- [X] T027d [US2] Verify SC-001 for Derived Subset: Explicitly instantiate `sklearn.dummy.DummyRegressor(strategy='mean')`, run 5-fold CV on `X_derived`, compute mean R², and compare it against the best model's mean R². **Logic**: Log "PASS" if (Best Model R² > Dummy R²) AND (Best Model R² ≥ 0.65). **If FAIL, raise `RuntimeError` with "Success Criterion SC-001 Failed" and exit(1)**. Write the result to `results/reports/model_metrics_derived.json` under the key `sc001_success_check`.

### Model Selection Logic

- [X] T028 [US2] **Model Selection**: Implement logic to parse `results/reports/model_metrics_raw.json` and `results/reports/model_metrics_derived.json`. Compare the mean R² scores of the best models from each subset. Select the model (raw or derived) with the **highest** mean R². Write the selection decision (model type, path, R² score) to `state/selected_model.yaml`.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test: Verify 5-fold CV splits are reproducible with fixed seed in `tests/unit/test_training.py`
- [X] T020 [P] [US2] Unit test: Verify CPU-only execution constraint (no CUDA device assignment) in `tests/unit/test_training.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (models trained and evaluated on both subsets).

---

## Phase 5: User Story 3 - Explainability and Statistical Analysis (Priority: P3)

**Goal**: Generate SHAP plots and perform statistical significance testing (Permutation Importance and SHAP Bootstrapping) to interpret model drivers.

**Independent Test**: Verify generation of a SHAP summary plot in `results/plots/` and a statistical report table in `results/reports/` with 95% Bootstrap CIs on SHAP values.

### Implementation for User Story 3 (Selected Best Model)

- [X] T030 [US3] Implement `code/analyze_explainability.py` to **load** the model selected in T028 (read from `state/selected_model.yaml`). **Logic**: If `state/selected_model.yaml` indicates `X_raw`, load `models/artifacts/best_raw_model.pkl` and `data/processed/X_raw.csv`. If `X_derived`, load `models/artifacts/best_derived_model.pkl` and `data/processed/X_derived.csv`.
- [X] T031 [US3] Implement `code/analyze_explainability.py` to **calculate SHAP values** and generate a summary plot saved to `results/plots/shap_summary_{selected_subset}.png`. **Dependency**: Depends on T030.
- [X] T033a [US3] **SHAP Bootstrap Confidence Intervals**: Implement `code/analyze_explainability.py` to:
 1. **Bootstrap Resampling**: Resample the dataset with replacement `N` times (e.g., 1000) to create bootstrap samples.
 2. **SHAP Recalculation**: For each bootstrap sample, recompute SHAP values using the trained model.
 3. **CI Calculation**: For each feature, calculate the 2.5th and 97.5th percentiles of the distribution of SHAP values across all bootstrap samples to form the **95% Confidence Intervals**.
 4. **Output**: Save the final statistical report (feature name, mean SHAP value, 95% CI lower bound, 95% CI upper bound) to `results/reports/shap_bootstrap_ci_{selected_subset}.json`. **Dependency**: Depends on T031 (SHAP values) and T030 (Model).
- [X] T033b [US3] **Statistical Significance via Permutation Importance**: Implement `code/analyze_explainability.py` to:
 1. **Permutation Test**: Perform Permutation Importance testing with **1,000 permutations** as mandated by FR-007.
 2. **Metric Calculation**: Calculate the change in model performance (R²) for each permuted feature.
 3. **p-value Calculation**: Calculate the p-value for each feature by comparing its permutation importance against a null distribution (generated by permuting the target variable or using a dummy model).
 4. **Significance Determination**: A feature is deemed statistically significant if its p-value is < 0.05.
 5. **Output**: Save the final statistical report (feature name, permutation importance score, p-value, significance flag) to `results/reports/permutation_importance_{selected_subset}.json`. **Dependency**: Depends on T030.
- [X] T033c [US3] **Reporting**: Ensure `code/analyze_explainability.py` explicitly reports the p-values calculated in T033b and logs which features meet the SC-002 success criterion (p < 0.05). **Output**: Update `results/reports/permutation_importance_{selected_subset}.json` to include a summary of significant features.

### Comparison and Reporting

- [X] T034 [US3] Ensure `code/analyze_explainability.py` explicitly logs the sample size (N) used for Permutation Importance and states the significance threshold (p < 0.05) in the output report header.
- [X] T035 [US3] **Separate Model Comparison**: Implement `code/analyze_explainability.py` to **compare** the feature importance and SHAP values from `X_raw` (if available) and `X_derived` (if available) to validate physical intuition, **strictly ensuring** that the comparison is performed on **separate model outputs** and does NOT involve a joint analysis or combined model inputs (enforcing FR-010). **Metric**: Calculate Spearman correlation between feature importance ranks of the two models and generate a side-by-side bar chart. **Output**: Save a comparison report in `results/reports/feature_comparison.json` containing: `{"spearman_correlation": <float>, "significant_features_raw": [...], "significant_features_derived": [...]}`.
- [X] T036 [US3] Update `state.yaml` with hashes of plots and statistical reports.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T055 [P] [US3] Unit test: Verify Permutation Importance calculation logic (e.g., change in R²).
- [X] T029 [P] [US3] Unit test: Verify SHAP value calculation consistency.

**Checkpoint**: All user stories should now be independently functional (explainability and insights generated).

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] **Documentation**: Implement `docs/README.md` and `docs/usage.md`. **Deliverables**: 1) `README.md` with project overview, installation instructions, and quickstart guide. 2) `usage.md` with detailed usage instructions for each script (download, preprocess, train, analyze). **Verification**: Run `python code/download_data.py --help` (or equivalent) and verify the output matches the documentation. Ensure `README.md` contains the exact command to run the full pipeline.
- [X] T038 Code cleanup and refactoring of `code/utils.py` and error handling
- [X] T040 [P] Verify all artifacts in `state.yaml` match the latest hashes
- [X] T045 [US1] **Robustness Enforcement**: Update `code/download_data.py` to ensure that ANY failure in fetching the real dataset (network error, 404, timeout) immediately raises a `RuntimeError` with a clear message. **Constraint**: Remove any `try/except` blocks that might catch these errors and attempt to generate synthetic data or fallback to a mock dataset. The script must fail loudly to prevent the execution gate from accepting fabricated data.

---

## Phase 7: Execution & Validation

**Purpose**: Final verification of the entire pipeline and readiness for review.

**Goal**: Run the full pipeline end-to-end and validate all success criteria.

- [ ] T050 [P] **Full Pipeline Execution**: Execute the complete pipeline in order: `verify_material.py` → `download_data.py` → `preprocess.py` → `train_models.py` → `analyze_explainability.py`. **Constraint**: Must complete within the -hour CI limit. **Verification**: Confirm all expected artifacts exist in `data/`, `models/`, `results/`, and `state.yaml` is fully updated.
- [ ] T051 [P] **Success Criteria Validation**: Run `tests/contract/test_success_criteria.py` to verify:
 1. SC-001: Model R² > Dummy R² AND R² ≥ 0.65 (for selected model).
 2. SC-002: At least one feature has p < 0.05 in Permutation Importance.
 3. SC-003: Pipeline completed within 6 hours (log check).
 4. SC-004: Final dataset has zero missing values.
- [ ] T052 [P] **Artifact Integrity Check**: Verify SHA-256 hashes in `state.yaml` match the actual files in `data/`, `models/`, and `results/`.
- [ ] T053 [P] **Documentation Review**: Ensure `docs/README.md` accurately reflects the final pipeline structure and all command-line arguments.
- [ ] T054 [P] **Contract Test Execution**: Execute `tests/contract/test_dataset_schema.py` to validate `data/processed/cleaned_316L.csv` against `contracts/dataset.schema.yaml`. **Dependency**: T004b (Schema), T018 (Processed Data). **Verification**: Test passes and returns exit code 0.

**Checkpoint**: Project is fully validated, reproducible, and ready for final review.

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
- **User Story 2 (P2)**: Depends on US1 completion (requires `cleaned_316L.csv` and T016b feature subsets)
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

## Parallel Example: User Story 1

```bash
# Launch implementation tasks sequentially:
Task: "Implement download_data.py" -> "Implement preprocess.py" -> "Run validation"

# Launch tests after implementation:
Task: "Contract test for dataset schema in tests/contract/test_dataset_schema.py"
Task: "Unit test for median imputation in tests/unit/test_preprocessing.py"
Task: "Unit test for normalization in tests/unit/test_preprocessing.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (clean data exists)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Models trained)
4. Add User Story 3 → Test independently → Deploy/Demo (Insights generated)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data)
 - Developer B: Foundational/Contracts (if not done)
3. Once US1 completes:
 - Developer A: User Story 2 (Training)
 - Developer B: User Story 3 (Explainability - can prepare logic in parallel but needs model)
4. Stories complete and integrate independently

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
- **Revision Note**: Phase 7 removed. Robustness logic (streaming, material check) was invalid or misplaced. Valid robustness (error handling) is now integrated into Phase 3 tasks (T012, T014). Added tasks to train and analyze both `X_raw` and `X_derived` subsets to satisfy US-3 comparison requirement. Explicitly added T012b for Material Mismatch check to satisfy plan.md Verified Accuracy Gate. Added T027d for dummy baseline on derived subset. Added T028 for model selection logic. Consolidated statistical tasks into T033c with corrected p-value logic. Marked Phase 1 tasks as [X] with verification steps. Fixed T017 to run before T014. Removed T013. Fixed T037 to be concrete. Updated T012b to specify `research.md` key path. Updated T014 to specify column names for energy density fallback and clarify zero-variance handling.
- **Revision Note R2**: Removed T012b (circular dependency on research.md). Added T004b (schema generation in Phase 2). Removed T041, T042, T043, T044 (redundant/contradictory/gold-plating). Rewrote T033c to implement SHAP Bootstrapping for 95% CIs as per FR-007. Updated T027b/T027d to verify both SC-001 conditions (R² ≥ 0.65 AND > Dummy).
- **Revision Note R3**: Added T045 to explicitly enforce the "No Synthetic Fallback" rule in `download_data.py` by ensuring any failure to fetch real data raises an exception immediately. Added T046 to add a specific unit test verifying that `download_data.py` raises an exception on a simulated network failure, ensuring no silent fallback occurs. Added T047 to add a contract test verifying that `preprocess.py` halts with a specific error code if the raw data contains zero porosity variance, ensuring the "Degenerate Dataset" check is robust.
- **Revision Note R4**: **Critical Fixes**: 1) Replaced T033c (SHAP Bootstrapping) with T033a (Permutation Importance 1000 perms) and T033b (p-value reporting) to satisfy FR-007 and SC-002. 2) Added T011 (Material Verification Gate) before T012 to satisfy plan.md Verified Accuracy Gate. 3) Updated T014 to explicitly include "filter out rows with zero parameters" to prevent division by zero. 4) Split T002 into T002a, T002b, T002c for executability. 5) Updated T004b to list specific columns.
- **Revision Note R5**: **Corrected T033a** to implement **SHAP Bootstrap Confidence Intervals** (resampling + percentiles) as required by FR-007, moving Permutation Importance to T033b. **Corrected T011** to use a temp-download-verify-delete pattern to satisfy Data Hygiene. **Corrected T014** to include full synonym mapping. **Corrected T015** to implement graceful flagging (file + state) instead of hard crash. **Corrected T034b** to explicitly forbid joint analysis.
- **Revision Note R6**: **Corrected T011** to download full file to temp for verification (fixing partial fetch violation). **Corrected T014** to include full synonym map. **Corrected T015** to write flag file and exit 0. **Corrected T033a** to implement SHAP Bootstrapping (resampling + percentiles). **Corrected T034b** to explicitly forbid joint analysis and define Spearman correlation metric.
- **Revision Note R7 (Current)**: **Split T011 and T012** to strictly enforce "Verify BEFORE Download" (T011 now metadata check, T012 full download). **Updated T033a** to explicitly define SHAP Bootstrap CI algorithm (N resamples, 2.5/97.5 percentiles). **Updated T014** to mandate full synonym mapping. **Updated T015** to write `degenerate_flag.json` and update `state.yaml` instead of exiting. **Updated T034b** to explicitly forbid joint analysis and define output schema (Spearman float + chart). **Updated T011** to use HEAD request/small fetch instead of "first 100 rows".
- **Revision Note R8**: **Added Phase 7** to ensure final pipeline execution and success criteria validation. **Added T050, T051, T052, T053** to cover end-to-end execution, success criteria checks, artifact integrity, and documentation review. This ensures the project is fully validated before final review.
- **Revision Note R9 (Final)**: **Fixed Duplicate IDs**: Renamed duplicate T028 (Phase 5) to T055. Renamed duplicate T033b (Reporting) to T033c. Renamed T034b to T035 for sequential clarity. **Fixed T017 Logic**: Removed T017 (raw validation). Added T017b (processed validation). **Fixed T015 Logic**: Updated to halt pipeline (exit 1) on degenerate detection. **Fixed T011 Logic**: Updated to use content-based verification (first 100 lines). **Fixed T027b/T027d**: Added `raise RuntimeError` on failure. **Removed T009**: Consolidated into T054 (Phase 7). **Removed T004**: Merged into T004b. **Removed T054 from Phase 3**: Kept only in Phase 7.