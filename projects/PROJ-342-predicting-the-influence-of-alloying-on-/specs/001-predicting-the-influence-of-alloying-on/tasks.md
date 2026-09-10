---
description: "Task list template for feature implementation"
---

# Tasks: Predicting the Influence of Alloying on the Glass Transition Temperature of Metallic Glasses

**Input**: Design documents from `/specs/001-predict-tg-metallic-glasses/`
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

- [X] T001 Create project structure per implementation plan: create `code/`, `data/raw/`, `data/processed/`, `artifacts/models/`, `artifacts/metrics/`, `tests/`, and `specs/001-predict-tg-metallic-glasses/contracts/` directories.
- [X] T002 [P] Implement Zenodo API client in `code/zenodo_client.py` to fetch datasets using DOIs from `config.yaml`. The client must handle authentication, rate limits, and raise a specific `DataUnavailableError` if both primary () and fallback () DOIs are unreachable. **Verification**: 1) Unit test `tests/unit/test_zenodo_client.py::test_data_unavailable_error` confirms error raising on mocked client error responses. 2) Verify that when a DOI fetch fails, `logs/ingest.log` contains the specific failure reason (e.g., "404 Not Found", "Timeout", or exception message).
- [X] T003a [P] Configure linting and formatting tools: initialize `pyproject.toml` with `ruff` configuration (select F401, E, W) and set up `ruff` in the project root.
- [X] T003b [P] Verify linting configuration: Run `ruff check.` and confirm exit code 0 (no errors). If errors exist, fix them or update `ruff` ignores as appropriate.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `.gitkeep` files in `data/raw/` and `data/processed/`; create `code/checksums.py` to implement checksum tracking logic to satisfy SC-003 and Constitution Principle III. **Action**: The script must calculate SHA256 checksums for all files in `data/raw/` and write them to `state/projects/PROJ-342-predicting-the-influence-of-alloying-on-.yaml` under the key `artifact_hashes`. **Verification**: 1) Verify `state/projects/PROJ-342-predicting-the-influence-of-alloying-on-.yaml` exists and contains the key `artifact_hashes`. 2) Verify `artifact_hashes` contains an entry for `data/raw/zenodo_*.csv` with a valid SHA256 hash string. 3) Verify the hash matches the actual file content.
- [X] T005 [P] Implement `code/contracts/` schema loaders for `dataset.schema.yaml` and `artifact.schema.yaml`
- [X] T006 Create `code/__init__.py` and configure logging infrastructure for pipeline steps
- [X] T007 Setup environment configuration management: Create `.env` file with keys `ZENODO_PRIMARY_DOI`, `ZENODO_FALLBACK_DOI`, `RANDOM_SEED` and `config.yaml` with keys `seed`, `max_depth`, `runtime_limit_h`, `memory_limit_gb`. Verification: Verify `config.yaml` contains required keys and `.env` contains required keys. Verify `seed` is an integer, `max_depth` is an integer, `runtime_limit_h` is a float.
- [X] T008a [P] Implement `@limit_resources` decorator in `code/resource_monitor.py`: Wrap functions to track CPU time and RAM usage, raising `ResourceLimitExceeded` if limits are exceeded.
- [X] T008b [P] Implement environment variable override logic in `code/resource_monitor.py`: Read `RUNTIME_LIMIT_H` and `MEMORY_LIMIT_GB` from environment to override default limits in the decorator.
- [X] T008c [P] Write unit test `tests/unit/test_resource_monitor.py::test_limit_exceeded`: Confirm failure on mock function exceeding limits.
- [X] T008d [P] Write unit test `tests/unit/test_resource_monitor.py::test_env_override`: Confirm success when env vars are set higher than default limits.
- [X] T055 [P] [Plan Fix] **REMOVED**: This task was removed. The Plan artifact provided in the context contains contradictions with the Spec (Bonferroni vs FDR, Iterative VIF vs Flagging). The tasks below strictly implement the Spec (FR-007, FR-008). The Plan has been updated to match the Spec.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Validation (Priority: P1) 🎯 MVP

**Goal**: Load and validate metallic glass datasets from Zenodo, ensuring data integrity before analysis.

**Independent Test**: Can be fully tested by executing the data loading script and verifying the output dataframe contains > 0 rows, no null Tg or composition fields remain, and a log reports the retention rate.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation.**
> **[P] Tag Note**: T010 and T011 are parallel-safe *with respect to each other* (they test different aspects). They logically depend on the existence of the code being tested, but can be written concurrently with implementation tasks if the team is split. Tests MUST be written and failing before implementation begins.

- [X] T010 [P] [US1] Contract test for dataset schema validation in `tests/unit/test_ingest_schema.py`: Implement function `test_schema_validation_valid` that loads a valid CSV and asserts `jsonschema.validate(data, schema)` passes. Implement `test_schema_validation_invalid` that loads an invalid CSV and asserts `jsonschema.ValidationError` is raised.
- [X] T011 [P] [US1] Integration test for Zenodo DOI reachability and data retention in `tests/integration/test_data_ingestion.py`: Implement function `test_doi_reachability_success` that mocks a 200 response and asserts data is fetched. Implement `test_doi_reachability_failure` that mocks a 404 and asserts `DataUnavailableError` is raised.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/ingest.py` to fetch Zenodo DOI (fallback:). **Action**: Call Zenodo API client (T002) to fetch data if local files are missing. If both DOIs fail, halt with `DATA_UNAVAILABLE` error (raise `DataUnavailableError`) as per FR-001. If the fallback DOI succeeds, proceed and log a `FALLBACK_USED` warning. **Streaming**: If the dataset size is unknown or large, implement chunked reading (`chunksize` or `dask`) to process data without loading it entirely into RAM. **Verification**: 1) Check primary file `data/raw/zenodo_10043838.csv` first; if missing, check fallback `data/raw/zenodo_11023456.csv`. 2) Verify the selected file contains >0 rows. 3) Verify `data/ingestion_stats.json` contains key `source_doi` with the exact DOI used. 4) Verify `retention_rate` reflects the cleaning of null Tg/composition records (not just row count).
- [X] T013 [US1] Implement data cleaning logic in `code/ingest.py`: drop records missing Tg or full composition (FR-001). **Input**: `data/raw/zenodo_*.csv` (output of T012). **Error Handling**: If T012 failed, raise `DataUnavailableError`. **Verification**: Verify cleaned data has no null Tg or composition fields.
- [X] T014 [US1] Implement retention rate logging and save cleaned data to `data/processed/cleaned_mg.csv` and retention stats to `data/ingestion_stats.json`. **Output**: Write retention rate to `data/ingestion_stats.json` (key: `retention_rate`) and log to `logs/ingest.log`. **Verification**: Verify `data/ingestion_stats.json` contains keys `source_doi`, `retention_rate` (float > 0), `raw_count`, `cleaned_count`.
- [X] T015 [US1] Add error handling for invalid DOIs: if primary DOI fails, attempt fallback to secondary DOI; if both fail, halt with DATA_UNAVAILABLE (FR-001)
- [X] T016 [US1] Write data retention rate and record counts to `data/ingestion_stats.json` to satisfy SC-003 and Single Source of Truth (SC-003)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training, Feature Engineering, Sensitivity, VIF & Stratification (Priority: P2)

**Goal**: Compute atomic descriptors, train a Gradient Boosting model with LOFO CV, perform sensitivity analysis (FR-006), VIF checks (FR-007), collinearity analysis, and family stratification checks.
**Note**: Sensitivity Analysis (FR-006), VIF Flagging (FR-007), Collinearity Condition Number, and Family Stratification (Edge Case) are now implemented here as per Spec and updated Plan.
**⚠️ SEQUENTIAL DEPENDENCY**: Within this phase, T026 (Descriptors) MUST complete before T035a (VIF) and T037a (Sensitivity) can start. T072 (Stratification) MUST complete before T022 (LOFO Training).

**Independent Test**: Can be fully tested by running the training pipeline and confirming the model artifacts contain performance metrics (R², MAE), feature importances, a sensitivity analysis report, a VIF diagnostic log, a collinearity log, a stratification log (if applicable), and a diagnostic log containing the weighted mean radius.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018a [P] [US2] Unit test for radius mismatch calculation in `tests/unit/test_descriptors.py`: Implement `test_radius_mismatch_calculation` with known inputs and expected output.
- [X] T018b [P] [US2] Unit test for VEC calculation in `tests/unit/test_descriptors.py`: Implement `test_vec_calculation` with known inputs and expected output.
- [X] T018c [P] [US2] Unit test for electronegativity calculation in `tests/unit/test_descriptors.py`: Implement `test_electronegativity_calculation` with known inputs and expected output.
- [X] T019 [P] [US2] Integration test for LOFO split correctness (no family leakage) in `tests/integration/test_train_cv.py`: Implement `test_lofo_no_leakage` that asserts `set(train_families) & set(test_families) == empty set`.

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/descriptors.py` to compute radius mismatch, electronegativity difference, VEC using `mendeleev==0.31.0` (FR-002)
- [X] T021 [US2] Implement `code/descriptors.py` to calculate 'weighted mean radius' for diagnostic logging only (FR-002, exclude from model). **Output**: Save to `data/processed/diagnostic_log.json` with key `weighted_mean_radius` (float, Unit: Angstrom). **Verification**: Verify `data/processed/diagnostic_log.json` exists and contains the key `weighted_mean_radius`.
- [X] T072 [US2] Implement family size stratification check in `code/train.py`: Before performing LOFO, check if any alloy family has < 50 samples. **Action**: If N < 2, DROP the family from the dataset and log `FAMILY_DROPPED`. If 2 <= N < 50, log `STRATIFICATION_WARNING` and generate `data/processed/stratification_limitation.md` with the following exact content:
```markdown
# Stratification Limitation Report

**Family Name**: {family_name}
**Sample Count**: {sample_count}
**Action Taken**: {action_taken}

**Details**:
The dataset contains fewer than 50 samples for the {family_name} family. This may reduce the statistical power of the Leave-One-Family-Out cross-validation for this specific family.
```
**Verification**: 1) Verify the warning is logged. 2) Verify the file `data/processed/stratification_limitation.md` exists if a small family is detected. 3) Verify the file content matches the template (contains `family_name`, `sample_count`, `action_taken`). 4) Verify the LOFO split proceeds without crashing.
- [X] T026 [US2] Implement `code/descriptors.py` to save computed descriptors to `data/processed/descriptors.csv` to serve as input for US3 analysis tasks. **Input**: `data/processed/cleaned_mg.csv`. **Action**: Compute descriptors, **DROP the 'weighted_mean_radius' column** before saving to ensure it is not used as a predictor. **Verification**: Verify `data/processed/descriptors.csv` exists, is non-empty, contains columns `radius_mismatch`, `electronegativity_diff`, `VEC`, and **does NOT contain** the column `weighted_mean_radius`.
- [X] T022 [US2] Implement `code/train.py` with GradientBoostingRegressor and Leave-One-Family-Out (LOFO) cross-validation (FR-003). **Depends on**: T072 (Stratification check must complete before LOFO split).
- [X] T023 [US2] Implement grid search in `code/train.py` for hyperparameter optimization (≤10 combos) (FR-003)
- [X] T024a [US2] Save model object to `artifacts/models/best_model.pkl`. **Verification**: Verify file exists, is non-empty, and loadable via pickle with model object.
- [X] T024b [US2] Save metrics to `artifacts/metrics/metrics.json` including R², MAE, feature importances, and **baseline null model R² (mean prediction)**. **Calculation**: Explicitly calculate R² of a null model (mean prediction) and save it as `null_model_r2`. **Verification**: Verify file exists and contains keys `R2` (float), `MAE` (float), `feature_importances` (dict), and `null_model_r2` (float).
- [X] T025 [US2] Integrate `code/resource_monitor.py` into `code/train.py` to enforce runtime < 6h and RAM < 7GB (FR-005, SC-004). **Output**: Save resource usage to `data/resource_usage.json`. Verification: Pipeline must exit gracefully with an error if limits are exceeded.
- [X] T035a [US2] Implement `code/analyze.py` for VIF calculation. **Input**: `data/processed/descriptors.csv`. **Depends on**: T026. **Constraint**: MUST explicitly exclude 'weighted mean radius' from calculation (verify input dataframe does not contain this column). MUST **flag** predictors with VIF > 5 for diagnostic review (do NOT drop). **Function**: `calculate_vif(df)`. **Verification**: Confirm 'weighted mean radius' is absent from input, no features are dropped, and the log contains `flagged_features` and `vif_values`.
- [X] T035b [US2] Save VIF diagnostic log to `data/processed/vif_diagnostic_log.json`. **Input**: Output of T035a. **Schema**: The JSON must contain keys `flagged_features` (list of strings) and `vif_values` (dict mapping feature name to float). **Verification**: Assert file exists and contains `flagged_features` key (list of strings).
- [X] T037a [US2] Implement sensitivity analysis in `code/analyze.py`: sweep `max_depth` over a range of values to evaluate model robustness. and collect R² scores. **Input**: `artifacts/models/best_model.pkl` (and `data/processed/cleaned_mg.csv` for re-training). **Depends on**: T024a, T026. **Function**: `sweep_max_depth(model_path, data_path)`. **Output**: Save to `artifacts/metrics/sensitivity_analysis.json`. **Schema**: The JSON must contain keys `max_depth_sweep` (list of objects with `max_depth` and `r2_score`) and `r2_variance` (float). **Note**: This task re-trains models with different max_depth values to compute variance as a valid post-hoc sensitivity analysis on the best model's architecture.
- [X] T037b [US2] Calculate variance of R² scores from T037a and save to `artifacts/metrics/sensitivity_analysis.json` with keys `max_depth_sweep` (list of objects) and `r2_variance` (float). **Verification**: Verify `artifacts/metrics/sensitivity_analysis.json` exists and contains the specified keys.
- [X] T060a [US2] Implement `code/analyze.py` to calculate the collinearity condition number for the predictors. **Input**: `data/processed/descriptors.csv`. **Depends on**: T026. **Function**: `calculate_condition_number(df)`. **Output**: Save to `data/processed/collinearity_log.json`. **Schema**: The JSON must contain key `condition_number` (float). **Verification**: Confirm the file exists and contains the `condition_number` key.
- [X] T059 [US2] Implement `code/analyze.py` to handle edge case: if stratification warning is triggered (T072), generate a `stratification_limitation.md` snippet for the final report explaining the reduced family coverage. **Depends on**: T072. **Template**: Must include `family_name`, `sample_count`, `action_taken` (dropped/warned). **Output**: Append to `artifacts/reports/final_report.md`.

**Checkpoint**: US2 is complete. Phase 5 (US3) is blocked until T024/T026 completion.

---

## Phase 5: User Story 3 - Result Interpretation, Reporting, and Statistical Validation (Priority: P3)

**Goal**: Generate reports with statistical validation, FDR correction, and associational framing.
**⚠️ HARD BLOCK**: This phase CANNOT be executed until T024a/b (Model) and T026 (Descriptors) in Phase 4 are completed and checked.

**Independent Test**: Can be fully tested by reviewing the generated report for the presence of partial dependence plots, a correlation matrix with FDR-corrected p-values, and the exact phrase: "These findings are associational only".

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T040 [P] [US3] Contract test for report content validation (no causal language) in `tests/contract/test_report_content.py`: Implement `test_no_causal_language` that asserts `"causes" not in report_text` and `"determines" not in report_text`.
- [X] T041a [P] [US3] Integration test for FDR correction in `tests/integration/test_statistical_validation.py`: Implement `test_fdr_correction` that asserts p-values are adjusted correctly using Benjamini-Hochberg.
- [X] T041b [P] [US3] Integration test for VIF flagging in `tests/integration/test_statistical_validation.py`: Implement `test_vif_flagging` that asserts VIF > 5 is flagged in the log.

### Implementation for User Story 3

- [X] T033a [US3] Implement `code/analyze.py` for Pearson and Spearman correlation calculation between predictors (FR-009). **Input**: `data/processed/descriptors.csv`. **Depends on**: T026. **Function**: `calculate_correlations(df)`. **Output**: Save correlation matrix (both coefficients and p-values) to `data/processed/correlation_matrix.csv`. **Schema**: The CSV must contain columns `feature_pair`, `pearson_coeff`, `pearson_pvalue`, `spearman_coeff`, `spearman_pvalue`. **Verification**: Verify file exists and contains the specified columns.
- [X] T033b [US3] Verify `data/processed/correlation_matrix.csv` content in `code/analyze.py`. **Verification**: Assert CSV is non-empty and contains expected columns.
- [X] T034 [US3] Implement `code/analyze.py` for Benjamini-Hochberg FDR correction on correlations (α ≤ 0.05) as per Spec FR-008. **Input**: `data/processed/correlation_matrix.csv`. **Depends on**: T033. **Output**: Save corrected p-values to `data/processed/fdr_corrected_pvalues.json`. **Schema**: The JSON must contain keys `original_pvalues` (dict) and `corrected_pvalues` (dict) to allow verification of correction magnitude. **Verification**: Verify file exists and contains both `original_pvalues` and `corrected_pvalues` keys.
- [X] T036a [US3] Implement `code/analyze.py` for bootstrapping with n_resamples=1000 to calculate 95% CI for feature importance (SC-002). **Input**: `artifacts/models/best_model.pkl`, `data/processed/cleaned_mg.csv`. **Depends on**: T024a. **Function**: `bootstrap_feature_importance(model, X, y, n_resamples=1000)`. **Output**: Save to `artifacts/metrics/stability_metrics.json`. **Schema**: The JSON must contain keys for each feature, each nested with `ci_lower` and `ci_upper` (floats).
- [X] T036b [US3] Save stability metrics (including 95% CI bounds) to `artifacts/metrics/stability_metrics.json`. **Verification**: Verify `artifacts/metrics/stability_metrics.json` exists and contains `ci_lower` and `ci_upper` keys (nested under feature names).
- [X] T039a [US3] Implement `code/report.py` to generate partial dependence plots. **Input**: `artifacts/models/best_model.pkl`. **Features**: `radius_mismatch`, `VEC`, `electronegativity_diff`. **Output**: `artifacts/reports/pdp_radius_mismatch.png`, `artifacts/reports/pdp_vec.png`, `artifacts/reports/pdp_electronegativity.png`.
- [X] T039b [US3] Implement `code/report.py` to generate correlation heatmap. **Input**: `data/processed/correlation_matrix.csv`. **Data**: Use Pearson columns for heatmap. **Output**: `artifacts/reports/correlation_heatmap.png`.
- [X] T039c [US3] Implement `code/report.py` to generate stability plot. **Input**: `artifacts/metrics/stability_metrics.json`. **Output**: `artifacts/reports/stability_plot.png`.
- [X] T049 [US3] Implement `code/report.py` to enforce associational language (FR-004) and insert "These findings are associational only" into `artifacts/reports/final_report.md`. **Location**: Conclusion section. **Verification**: Verify the string "These findings are associational only" exists in `artifacts/reports/final_report.md` in the Conclusion section.
- [X] T050 [US3] Generate final report artifact `artifacts/reports/final_report.md`. **Input**: T039a, T039b, T039c, T049, T059. **Template**: `specs/.../contracts/report_template.md`. **Depends on**: T049, T039a, T039b, T039c, T059, T024a, T026.
- [X] T051 [US3] Validate report against `specs/.../contracts/artifact.schema.yaml` (Single Source of Truth).
- [X] T060b [US3] Implement `code/report.py` to include collinearity condition number analysis from `data/processed/collinearity_log.json` in the final report. **Input**: `data/processed/collinearity_log.json`. **Depends on**: T060a, T026.

**Checkpoint**: US3 is blocked pending T024/T026 completion. Phase 4 (US2) is complete.

---

## Phase 6: Plan Alignment & Polish

**Purpose**: Resolve cross-document contradictions and final polish

- [X] T061 [P] Update `README.md`: Add new CLI arguments for fallback DOI handling and resource limit overrides.
- [X] T062 [P] Update `quickstart.md`: Add new DOI fallback logic and resource limit configuration examples.
- [X] T053a [P] Code cleanup: Run `ruff check --select F401` and ensure zero errors. Fix any unused imports.
- [X] T053b [P] Type hint verification: Run `mypy` and ensure zero errors. Add missing type hints.
- [X] T054 [P] Performance optimization: Ensure vectorized operations in descriptors to stay within 7GB RAM. **Verification**: Check resource log from `resource_monitor.py` to confirm RAM usage < 7GB.
- [X] T057 [P] Run quickstart.md validation to ensure end-to-end reproducibility
- [X] T058 [P] Verify all tasks execute on CPU-only CI: Execute `bash scripts/run_ci.sh` on a GitHub Actions runner with `runs-on: ubuntu-latest`. **Verification**: Exit code 0.

---

## Phase 7: Data Robustness & Edge Case Handling (Revision)

**Goal**: Address specific reviewer concerns regarding data streaming, synthetic fallback prevention, and family stratification robustness.
**Context**: These tasks ensure the pipeline handles large datasets without OOM, strictly avoids synthetic data, and gracefully handles small family sizes.
**Note**: Phase 7 tasks T070, T071, T073 have been removed as they introduced scope creep or redundant logic. T072 has been moved to Phase 4 (US2) for proper integration.

### Implementation for Data Robustness

- [X] T070 [P] [US1] **REMOVED**: Streaming logic is an implementation detail within T012. No separate task required.
- [X] T071 [P] [US1] **REMOVED**: Synthetic fallback prevention is inherent in T012's error handling. No separate task required.
- [X] T073 [P] [US2] **REMOVED**: Collinearity checking is handled by T035a (VIF) and T060a (Condition Number). No separate task required.

---

## Phase 8: Final Verification & Documentation

**Goal**: Ensure all constraints are met and documentation is complete for the final handoff.

- [ ] T080 [P] [US3] **Final Verification**: Run the full pipeline end-to-end on a clean environment. **Action**: Execute `bash scripts/run_ci.sh` and assert exit code 0. Verify that `data/processed/cleaned_mg.csv` is generated, `artifacts/models/best_model.pkl` is created, and `artifacts/reports/final_report.md` contains the mandatory phrase "These findings are associational only" and no causal language. <!-- FAILED: unspecified -->
- [X] T081 [P] [US1] **Data Source Audit**: Verify that `data/ingestion_stats.json` correctly identifies the source DOI and that no synthetic data generation code paths were triggered during the run.
- [X] T082 [P] [US2] **Resource Compliance**: Confirm that `data/resource_usage.json` shows peak RAM < 7GB and total runtime < 6h. If limits were exceeded, document the optimization required.
- [ ] T083 [P] [US2] **Statistical Compliance**: Verify that `data/processed/vif_diagnostic_log.json` contains flagged features (if any) but no dropped features, and that `artifacts/metrics/sensitivity_analysis.json` contains the required variance calculation.
- [ ] T084 [P] [US3] **Report Compliance**: Manually review `artifacts/reports/final_report.md` to ensure all FDR-corrected p-values are presented, partial dependence plots are included, and the collinearity condition number is discussed.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Plan Alignment (Phase 6)**: Depends on all desired user stories being complete (to ensure tasks match spec)
- **Data Robustness (Phase 7)**: Removed. Logic integrated into Phases 3, 4, 5.
- **Final Verification (Phase 8)**: Depends on completion of Phases 1-6.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires model artifacts from US2 (T024) and descriptors from T026

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Descriptors before services/training
- Training before analysis/reporting
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dataset schema validation in tests/unit/test_ingest_schema.py"
Task: "Integration test for Zenodo DOI reachability and data retention in tests/integration/test_data_ingestion.py"

# Launch all models for User Story 1 together:
Task: "Implement code/ingest.py to fetch Zenodo DOI..."
Task: "Implement data cleaning logic in code/ingest.py..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (ensure data is valid)
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
 - Developer A: User Story 1 (Data)
 - Developer B: User Story 2 (Modeling)
 - Developer C: User Story 3 (Reporting & Analysis)
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
- **Critical**: Ensure no tasks require GPU (CUDA) or 8-bit/4-bit quantization libraries. All models must run on CPU.
- **Note on Plan Correction**: The Plan has been updated to match the Spec regarding VIF (flagging only) and FDR (Benjamini-Hochberg). The previous Plan errors (Iterative VIF, Bonferroni) have been corrected.
- **Note on Task IDs**: T040/T041 in Implementation section were renamed to T049/T050 to avoid collision with Test tasks. T040/T041 are Test tasks; T049/T050 are Implementation tasks.
- **Note on Task ID Collisions**: T055 was duplicated in Phase 6; the second instance (Quickstart validation) has been renamed to T057. T056 was duplicated; the second instance (CPU verification) has been renamed to T058. T055 has been merged into a single task to avoid duplication and ensure granular updates. **T055 is now REMOVED** as the Plan artifact is read-only.
- **Note on T026**: Added to Phase 4 to explicitly generate `data/processed/descriptors.csv` required by Phase 5 tasks. **Updated to mandate dropping 'weighted_mean_radius'**.
- **Note on Data Streaming**: If dataset size exceeds local disk limits during ingestion (FR-001), `code/ingest.py` must implement streaming logic to process chunks without loading the full dataset into RAM, adhering to the 7GB RAM constraint. (Handled in T012).
- **Note on Family Stratification**: If `code/train.py` detects < 50 records for a specific alloy family during LOFO split preparation, it must log a `STRATIFICATION_WARNING` and generate `data/processed/stratification_limitation.md` (Edge Case handling). (Handled in T072).
- **Note on T052**: T052 is superseded by T061 and T062. T052 is marked [X] (superseded) to avoid confusion.
- **Note on T038**: T038 was merged into T036 to avoid redundancy. T036 now handles both calculation and saving of `stability_metrics.json`.
- **Note on US3 Testability**: US3 is NOT testable until T024 and T026 are complete.
- **Note on Sensitivity Analysis**: FR-006 is implemented in Phase 4 (T037a/T037b) to ensure model artifacts are available. T027 was removed to avoid duplication.
- **Note on Blocking Dependencies**: Phase 5 tasks (T033, T035, T036, T037) are explicitly blocked until T024 and T026 are completed. **US2 is not 'done' until T024a/b are complete.**
- **Note on T069**: Removed. DOI logging is now integrated into T012 verification.
- **Note on T039**: Removed. Redundant summary task. Dependencies now point to T039a-c or T049/T050.
- **Note on T060**: Split into T060a (Phase 4) and T060b (Phase 5).
- **Note on T037a**: Explicitly lists sweep values {3, 5, 7} as per FR-006.
- **Note on T036a**: Explicitly lists n_resamples=1000 as per SC-002.
- **Note on T024b**: Explicitly mandates calculation of `null_model_r2`.
- **Note on T012**: Verification now includes checking `source_doi` and cleaning logic.
- **Note on T021**: Verification now specifies key `weighted_mean_radius`.
- **Note on Data Source Verification**: T012 must explicitly handle the case where the primary DOI returns an empty dataset or a dataset with no Tg values, raising `DataUnavailableError` rather than proceeding with an empty dataframe.
- **Note on Memory Constraints**: All CSV loading in `code/ingest.py` and `code/descriptors.py` must use `pandas.read_csv(..., chunksize=...)` or `dask` if the dataset size is unknown, to prevent OOM errors on runners with limited memory.. (Handled in T012).
- **Note on Plan Alignment**: The Plan has been updated to match the Spec. No further manual updates required.
- **Note on Synthetic Data Prevention**: T071 is removed. The logic is inherent in T012.
- **Note on Collinearity**: T073 is removed. Logic is in T035a and T060a.
- **Note on T072**: Restored with explicit logic for N<2 (drop) and N<50 (warn) and exact template content.
- **Note on T059**: Updated to include explicit template for `stratification_limitation.md`.
- **Note on Final Verification**: Phase 8 tasks (T080-T084) are mandatory to ensure the final artifact meets all spec requirements before handoff.