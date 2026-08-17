# Tasks: Predicting Solubility in Mixed Solvents with Machine Learning

**Input**: Design documents from `/specs/001-predicting-solubility-mixed-solvents/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
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

- [X] T001 Create project directory structure: `code/`, `data/raw/`, `data/processed/`, `data/artifacts/`, `tests/`, `specs/001-predicting-solubility-in-mixed-solvents/contracts/`
- [X] T002 Create Python 3.11 virtual environment and pinned dependency file: `code/requirements.txt`
- [X] T003 [P] Create linting and formatting configuration files: `.flake8` and `pyproject.toml` (with `[tool.black]` section)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure, design constraints, and safety logic that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `code/utils/constants.py` containing fixed random seeds (numpy, pandas, sklearn, xgboost) and standard file paths
- [X] T005 [P] Create `code/utils/logging.py` implementing memory/disk monitoring:
 - Define function `monitor_resources(ram_limit_gb=7.0, disk_limit_gb=14.0)`
 - Log output to stderr in JSON format: `{"timestamp": "ISO8601", "ram_gb": float, "disk_gb": float, "status": "ok"|"critical"}`
 - On critical status, print `ERROR: Resource limit exceeded` to stderr and exit with code 1.
- [X] T006 Create data directory structure: `data/raw/`, `data/processed/`, `data/artifacts/`
- [X] T006b Create `code/utils/checksums.py` to generate `data/.checksums.json`
- [X] T007 Create schema definition files: `specs/001-predicting-solubility-in-mixed-solvents/contracts/solubility_record.schema.yaml` and `specs/001-predicting-solubility-in-mixed-solvents/contracts/processed_dataset.schema.yaml`
- [X] T008 Create `code/utils/errors.py` defining `CustomDataError`, `MissingURLError`, and `InvalidStoichiometryError`
- [X] T011b [US1] **Formal Scope Amendment (Documentation)**: Update `specs/001-predicting-solubility-in-mixed-solvents/spec.md` to explicitly document the exclusion of DSSTox from FR-001, citing the Plan's "Assumptions & Gaps" section.
 - **Rationale**: Scope definition must precede implementation.
- [X] T024b [US2] **Document Constitution Precedence**: Create `data/artifacts/design_constraint_precedence.md` documenting that Constitution Principle VII (Paired t-test) overrides Spec FR-005 (Wilcoxon).
 - **Rationale**: Design decision must precede implementation of T024.
- [X] T026a [US2] **Resource Monitor (Create)**: Create `code/utils/watchdog.py` implementing a subprocess wrapper that polls the training process ID (PID) using `psutil`.
 - **Action**: If RAM > 7.0 GB or Disk > 14.0 GB, kill the training process.
 - **Logging**: Write status updates to `data/artifacts/resource_monitor.log`.
 - **Requirement**: On termination, write a 'timeout' or 'resource_exceeded' flag to the artifact log.
 - **Dependency**: T005 must be completed.
- [X] T026b [US2] **Resource Monitor (Integrate)**: Integrate the watchdog call into the training runner in `code/03_model_training.py`.
 - **Dependency**: T026a must be completed.
- [ ] T026c [US2] **Resource Monitor (Verify)**: Verify the log output of `data/artifacts/resource_monitor.log` after a test run.
 - **Action**: Execute `code/03_model_training.py` with a small dummy dataset (5 rows) to force the watchdog to trigger and write to `data/artifacts/resource_monitor.log`. If the log is missing or empty, run the dummy job explicitly to generate it.
 - **Verification**: Check that `data/artifacts/resource_monitor.log` exists and contains at least one non-empty JSON entry (e.g., `{"timestamp": "...", "ram_gb": 1.2, "status": "ok"}`).
 - **Dependency**: T026b must be completed.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Feature Engineering Pipeline (Priority: P1) 🎯 MVP

**Goal**: Ingest raw solubility data from verified EPA sources (DSSTox excluded per Plan), filter for MW < 500 Da, compute RDKit descriptors, and generate composition-weighted solvent descriptors.

**Independent Test**: The pipeline can be tested by running the data processing script on a small subset of the input files and verifying that the output CSV contains the expected columns (solute SMILES, solvent descriptors, mixture composition, calculated interaction terms) and that the row count matches the filtered dataset size.

### Implementation for User Story 1

- [X] T041 [US1] **Data Source Verification**: Implement a pre-flight check in `code/01_data_ingestion.py` to validate the specific EPA URL endpoint is reachable and returns a non-empty CSV before attempting download.
 - **Logic**: Send a HEAD request to `https://comptox.epa.gov/dashboard/datasets/solubility`. If status != 200 or Content-Length is 0, raise `MissingURLError` immediately.
 - **Rationale**: Addresses review concern regarding "silent failures" on data ingestion; ensures the pipeline fails loudly if the real source is unavailable, preventing fallback to synthetic data.
 - **Dependency**: T008 must be completed.
- [ ] T011 [US1] **Data Ingestion**: Implement `code/01_data_ingestion.py`: fetch EPA data from `https://comptox.epa.gov/dashboard/datasets/solubility` (DSSTox excluded per Plan).
 - **Output**: Write raw data to `data/raw/epa_solubility.csv`.
 - **Failure Condition**: Exit with code 1 if EPA source is unreachable (T041 must pass).
 - **Dependency**: T011b, T041 must be completed.
- [ ] T012 [US1] **Data Filtering (MW)**: Filter molecules with Molecular Weight (MW) < 500 Da in `code/01_data_ingestion.py`.
 - **Output**: Write filtered data to `data/processed/filtered_mw.csv`.
 - **Dependency**: T011 must be completed.
- [ ] T013 [US1] **Data Filtering (Composition)**: Implement composition validation in `code/01_data_ingestion.py`: reject rows where composition sum != 1.0 (within tolerance 1e-5).
 - **Output**: Write valid rows to `data/processed/cleaned_compositions.csv`.
 - **Output**: Write rejected rows to `data/artifacts/rejected_rows.csv`.
 - **Dependency**: T012 must be completed.
- [ ] T013b [US1] **Define Safety Cap**: Define a *hard safety cap* for imputation in `code/utils/constants.py` as `MAX_IMPUTATION_RATE = 0.30`.
 - **Note**: This is a safety limit to prevent resource exhaustion. The actual rate is determined by data in T013c.
 - **Dependency**: T013 must be completed (to ensure logic exists for the constant to be used).
- [ ] T013 [US1] **Data Imputation**: Implement KNN imputation for missing solvent properties in `code/01_data_ingestion.py`.
 - **Logic**: Use `n_neighbors=5` to impute columns `['solvent_desc', 'interaction_terms']`. Calculate imputation rate.
 - **Output**: Write imputed data to `data/processed/imputed_data.csv`.
 - **Output**: Log imputation rate to `data/artifacts/imputation_log.txt` (format: `{"rate": 0.XX}`).
 - **Note**: Do NOT exit on failure here; the rate is logged for T013d to evaluate.
 - **Dependency**: T013b must be completed.
- [ ] T013c [US1] **Analyze Imputation Rate**: Read `data/artifacts/imputation_log.txt` and calculate the actual rate.
 - **Action**: If rate > 0.30, write `ERROR: Imputation rate exceeded safety cap` to `data/artifacts/imputation_error.log` and exit with code 1. Else, proceed.
 - **Dependency**: T013 must be completed.
- [ ] T013d [US1] **Imputation Gate**: Read `data/artifacts/imputation_log.txt` and update `code/utils/constants.py` if the actual rate deviates significantly from the safety cap (e.g., > 0.20).
 - **Action**: If rate > 0.20 or < 0.01, update `MAX_IMPUTATION_RATE` in constants.py and document the change in `data/artifacts/imputation_threshold_decision.md`.
 - **Dependency**: T013c must be completed.
- [ ] T014 [US1] **Feature Engineering (Solute)**: Implement `code/02_feature_engineering.py` to compute RDKit descriptors for solutes.
 - **Descriptors**: Compute `MolWt`, `MolLogP`, `NumHDonors`, `NumHAcceptors`, `TPSA`, and `MorganFP_2048` (radius=2, nBits=2048).
 - **Output Columns**: `solute_molwt`, `solute_mollogp`, `solute_hdonors`, `solute_hacceptors`, `solute_tpsa`, `solute_fp`.
 - **Dependency**: T013 must be completed.
- [ ] T015 [P] [US1] **Feature Engineering (Solvent)**: Implement composition-weighted solvent descriptor calculation in `code/02_feature_engineering.py`.
 - **Logic**: Compute weighted average of properties (polarity, dielectric constant) * mole fractions.
 - **Output Columns**: `solvent_mean_polarity`, `solvent_mean_dielectric`, `solvent_desc`.
 - **Dependency**: T013 must be completed.
- [ ] T017 [US1] **Pivot Logic**: Count mixed-solvent entries in `code/02_feature_engineering.py`.
 - **Logic**: If mixed-solvent entries < 100, write `data/artifacts/pivot_decision.json` with schema `{"status": "pivoted", "reason": "Insufficient mixed solvent data (< 100 rows). Non-linear mixing hypothesis dropped. Interaction terms will be generated for pure solvents."}`. Else write `{"status": "normal"}`.
 - **Action**: This task MUST determine the strategy for T016a. If pivoted, T016b generates interaction terms for pure solvents; otherwise T016c generates for mixed solvents.
 - **Output**: Store count and decision in `data/artifacts/pivot_decision.json`.
 - **Dependency**: T015 must be completed.
- [ ] T016a [US1] **Read Pivot Decision**: Read `data/artifacts/pivot_decision.json` and set the `interaction_strategy` flag in `code/02_feature_engineering.py`.
 - **Dependency**: T017 must be completed.
- [ ] T016b [US1] **Generate Pure Solvent Interactions**: If `interaction_strategy == "pivoted"`, generate interaction terms for pure solvent descriptors in `code/02_feature_engineering.py`.
 - **Formula**: `interaction_term = solvent_mean_polarity * solvent_mean_dielectric`.
 - **Output Column**: `interaction_polarity_dielectric`.
 - **Dependency**: T016a must be completed.
- [ ] T016c [US1] **Generate Mixed Solvent Interactions**: If `interaction_strategy == "normal"`, generate interaction terms for mixed solvents in `code/02_feature_engineering.py`.
 - **Formula**: Polynomial expansion (degree 2) of `solvent_mean_polarity` (P) and `solvent_mean_dielectric` (D): `P*P`, `D*D`, `P*D`.
 - **Output Columns**: `interaction_p_sq`, `interaction_d_sq`, `interaction_p_d`.
 - **Dependency**: T016a must be completed.
- [ ] T018 [US1] Write final processed dataset to `data/processed/solubility_features.csv` with checksum.
 - **Action**: Combine solute descriptors, solvent descriptors, and interaction terms.
 - **Dependency**: T016b or T016c (whichever is active) must be completed.

### Phase 3.5: Validation Tests (Post-Implementation)

> **NOTE**: These tests run AFTER T018 to validate the generated artifacts.

- [X] T009 [US1] Create `tests/contract/test_schema_validation.py` containing function `test_solubility_record_valid`.
 - **Input**: `data/processed/solubility_features.csv`.
 - **Schema**: `specs/001-predicting-solubility-in-mixed-solvents/contracts/processed_dataset.schema.yaml`.
 - **Dependency**: T018 must be completed.
- [X] T010 [US1] Create `tests/integration/test_pipeline.py` containing function `test_ingest_sample`.
 - **Input**: `data/processed/solubility_features.csv`.
 - **Expected**: Columns `['solute_fp', 'solvent_desc', 'interaction_terms', 'logS']` present. Row count >= 10.
 - **Dependency**: T018 must be completed.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training and Baseline Comparison (Priority: P2)

**Goal**: Train Gradient Boosting and Random Forest models, compare against Abraham solvation parameter baseline, and perform statistical significance testing.

**Independent Test**: The training pipeline can be tested by executing the training script with a fixed random seed and a small hyperparameter grid, verifying that the output includes trained model artifacts and a comparison report showing RMSE and R² for all approaches.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Create `tests/contract/test_model_artifacts.py` containing function `test_model_artifact_valid` for model artifact validation
- [X] T020 [P] [US2] Create `tests/integration/test_training.py` containing function `test_training_sample`.
 - **Input**: `data/processed/solubility_features.csv`.
 - **Expected Artifact**: `data/artifacts/trained_models.pkl` containing keys: `xgboost_model`, `rf_model`, `abraham_model`, `metrics`.
 - **Metrics to Verify**: `['rmse', 'r2']` in `data/artifacts/evaluation_metrics.json`.
 - **Dependency**: T023a must be completed.

### Implementation for User Story 2

- [X] T022a [US2] **Create Abraham Params File**: Create `code/data/abraham_params.csv` with columns: `solvent_name, a, b, c, s, v, r`.
 - **Action**: Populate with hardcoded values for the top solvents (e.g., Water, Ethanol, Methanol).
 - **Fallback Logic**: If a solvent is not found, use the mean of all rows in the CSV.
 - **Dependency**: None.
- [ ] T021 [P] [US2] Implement `code/03_model_training.py` to train XGBoost and Random Forest regressors with cross-validation and hyperparameter grid (limit ≤30 mins/trial).
 - **Output**: Write trained models to `data/artifacts/xgboost_model.pkl` and `data/artifacts/rf_model.pkl`.
 - **Dependency**: T018 must be completed.
- [ ] T022 [P] [US2] **Abraham Baseline**: Implement Abraham solvation parameter model baseline in `code/03_model_training.py`.
 - **Primary**: Use `solv` package.
 - **Fallback**: If `solv` unavailable, load `code/data/abraham_params.csv` (from T022a). If specific solvent not found, use mean of all rows.
 - **Schema**: Output must contain columns [a, b, c, s, v, r, prediction].
 - **Output**: Write baseline model to `data/artifacts/abraham_model.pkl`.
 - **Dependency**: T018, T022a must be completed.
- [ ] T023a [US2] **Generate Models**: Read `data/artifacts/xgboost_model.pkl`, `rf_model.pkl`, `abraham_model.pkl` and combine them into `data/artifacts/trained_models.pkl`.
 - **Action**: Create a dictionary `{'xgboost_model': ..., 'rf_model': ..., 'abraham_model': ...}` and save as pickle.
 - **Note**: If T021 or T022 fails, this task cannot run.
 - **Dependency**: T021, T022 must be completed.
- [ ] T023b [US2] **Evaluation Metrics**: Read `data/artifacts/trained_models.pkl` and implement evaluation logic in `code/04_evaluation.py` to calculate RMSE, MAE, and R² for all models on hold-out test set.
 - **Output**: Write metrics to `data/artifacts/evaluation_metrics.json`.
 - **Dependency**: T023a must be completed.
- [ ] T024 [US2] **Statistical Test**: Read `data/artifacts/trained_models.pkl`. Implement paired t-test on absolute errors per Constitution Principle VII **[OVERRIDES FR-005]** in `code/04_evaluation.py`.
 - **Parameters**: alpha=0.05, paired t-test on absolute errors.
 - **Columns**: Compare `['abs_error_xgboost', 'abs_error_abraham']` from `data/artifacts/evaluation_metrics.json`.
 - **Output**: Write statistical test results (p-value, t-statistic) to `data/artifacts/statistical_test_results.json`.
 - **Dependency**: T023b must be completed.
- [ ] T025 [US2] Generate comparison report in `data/artifacts/training_report.json` including metrics, statistical significance (p < 0.05).
 - **Dependency**: T024 must be completed.
- [ ] T025b [US2] **R² Gate Decision**: Read `data/artifacts/evaluation_metrics.json`. If R² <= 0.70, write `data/artifacts/r2_gate_decision.json` with `{"status": "FAIL", "reason": "R² <= 0.70"}`. Else `{"status": "PASS"}`.
 - **Dependency**: T025 must be completed.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpretability and Interaction Term Analysis (Priority: P3)

**Goal**: Visualize feature importances (SHAP values), identify top interaction terms, and perform sensitivity analysis on SHAP thresholds.

**Independent Test**: The analysis can be tested by generating SHAP summary plots and feature importance tables from the trained best-performing model, verifying that specific interaction terms are ranked and visualized.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Create `tests/contract/test_shap_output.py` containing function `test_shap_format_valid` for SHAP output format validation
- [X] T028 [P] [US3] Create `tests/integration/test_sensitivity.py` containing function `test_sensitivity_sample` for sensitivity analysis integration testing

### Implementation for User Story 3

- [ ] T029a [US3] **Compute SHAP Values**: Read `data/artifacts/trained_models.pkl` (best model) and `data/processed/solubility_features.csv`.
 - **Action**: Load the best model. Sample a subset of rows from the processed dataset. Compute SHAP values.
 - **Output**: Write SHAP values to `data/artifacts/shap_values.npy`.
 - **Dependency**: T023a must be completed.
- [ ] T029b [US3] **Input Dependency**: Read `data/artifacts/trained_models.pkl` (best model). Implement SHAP value computation in `code/04_evaluation.py`.
 - **Model Key**: Use `best_model` from pickle.
 - **Background Data**: Sample 100 rows from `data/processed/solubility_features.csv`.
 - **Output**: Write SHAP values to `data/artifacts/shap_values.npy`.
 - **Dependency**: T023a must be completed.
- [ ] T030 [US3] Generate SHAP summary plot and feature importance table in `data/artifacts/shap_analysis.png` and `shap_ranking.json`.
 - **Dependency**: T029a must be completed.
- [ ] T031 [US3] Filter and rank top 5 interaction terms contributing to model variance; append to `data/artifacts/shap_ranking.json`.
 - **Dependency**: T030 must be completed.
- [ ] T032 [P] [US3] **Sensitivity Analysis**: Read `data/artifacts/shap_values.npy`. Identify top-ranked terms at low, medium, and high thresholds.
 - **Metric**: Rank by mean absolute SHAP value.
 - **Dependency**: T029a must be completed.
- [ ] T033 [US3] **Input Dependency**: Read sensitivity analysis results. Calculate Jaccard similarity between top-5 term sets at different thresholds.
 - **Target**: Minimum Jaccard similarity ≥0.6 per SC-004.
 - **Output**: Append metrics to `data/artifacts/shap_ranking.json`.
 - **Dependency**: T032 must be completed.
- [ ] T034 [US3] **Input Dependency**: Read SHAP values across CV folds. Calculate Spearman rank correlation of **feature rankings** (stability) across CV folds to verify stability (target >0.8 per SC-002).
 - **Output**: Append metrics to `data/artifacts/shap_ranking.json`.
 - **Dependency**: T033 must be completed.
- [ ] T034b [US3] **Stability Gate & Report**: Read `data/artifacts/shap_ranking.json`. If Spearman < 0.8 or Jaccard < 0.6, write `data/artifacts/stability_gate_decision.json` with `{"status": "FAIL", "reason": "Stability thresholds not met"}`. Else `{"status": "PASS"}`.
 - **Dependency**: T034 must be completed.
- [ ] T035 [US3] Generate final research report in `data/artifacts/final_report.md` containing RMSE, R², p-values, and top interaction terms.
 - **Dependency**: T034b must be completed.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Update `research.md`: append verified source URLs and pivot decisions to the "Data Sources" section
- [ ] T037 Ensure type hints are added to `code/utils/*.py` and remove unused imports
- [X] T038 [P] Refactor `code/02_feature_engineering.py` to use batch processing for RDKit calls (batch size 1000).
 - **Dependency**: Depends on completion of T014-T016.
 - **Goal**: Targeting a reduction in **wall-clock time** for the feature engineering step.
- [X] T039 [P] Add `tests/unit/test_edge_cases.py` containing functions `test_missing_data_handling` and `test_small_dataset_split`
- [X] T040 Execute `code/quickstart.sh`.
 - **Note**: If `code/quickstart.sh` does not exist, create a minimal script that prints "No quickstart instructions available" and exits 0.
 - Record the exit code and any errors in `data/artifacts/quickstart_validation.log`.

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementing
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Create tests/contract/test_schema_validation.py containing function test_solubility_record_valid"
Task: "Create tests/integration/test_pipeline.py containing function test_ingest_sample"

# Launch all models for User Story 1 together:
Task: "Implement composition validation: write filtered data to data/processed/cleaned_compositions.csv"
Task: "Implement KNN imputation: log rate to data/artifacts/imputation_log.txt and write data to data/processed/imputed_data.csv"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
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
- **Critical Constraint**: No synthetic data generation. If mixed-solvent data is insufficient, pivot to pure solvent prediction and implement interaction terms for pure solvents.
- **Critical Constraint**: Constitution Principle VII (Paired t-test) takes precedence over Spec FR-005 (Wilcoxon).
- **Critical Constraint**: All tasks must run on CPU-only CI (minimal core count, limited RAM, 14GB disk).
- **Critical Constraint**: DSSTox ingestion is excluded per Plan/Spec amendment; EPA-only data is used.
- **Critical Constraint**: T017 acts as a gate before T016a to ensure pivot logic is fully executed.
- **Critical Constraint**: Data ingestion tasks (T011) must fail loudly if the real EPA source is unreachable; no synthetic fallback is permitted.
- **Critical Constraint**: T041 ensures the data source is verified before any download attempt, preventing silent fallbacks.
- **Critical Constraint**: T024b (Design) precedes T024 (Implementation) to enforce Constitution compliance.
- **Critical Constraint**: T026a-c (Watchdog) precedes T021 (Training) to ensure safety.
- **Critical Constraint**: T009/T010 (Tests) run AFTER T018 (Data Production) to validate actual artifacts.
- **Critical Constraint**: T023a ensures `trained_models.pkl` is generated before evaluation tasks.
- **Critical Constraint**: T022a ensures Abraham params file exists before baseline training.
- **Critical Constraint**: T013b/T013c resolve the circular dependency for imputation rate.
- **Critical Constraint**: T016b/T016c provide explicit formulas for interaction terms in pivot and normal modes.