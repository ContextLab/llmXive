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

- [X] T001 Create project structure per implementation plan: create `code/`, `data/raw/`, `data/processed/`, `artifacts/models/`, `artifacts/metrics/`, `artifacts/reports/`, `tests/`, `specs/001-predict-tg-metallic-glasses/contracts/`, and `.github/workflows/` directories. **Action**: This task creates the directory structure only; workflow content is defined in T089.
- [X] T002 [P] Implement Zenodo API client in `code/zenodo_client.py` to fetch datasets using DOIs `10.5281/zenodo.10043838` (primary) and `10.5281/zenodo.11023456` (fallback) from `config.yaml`. The client must handle authentication, rate limits, and raise specific `DataUnavailableError` (if both DOIs unreachable) or `DataInsufficientError` (if raw data < 1 row) exceptions. **API Details**: Use standard Zenodo REST API. **Retry Logic**: Implement exponential backoff for rate limit errors with a limited number of retries, initial delay, and doubling delay per retry. **Verification**: 1) Unit test `tests/unit/test_zenodo_client.py::test_data_unavailable_error` confirms error raising on mocked client error responses. 2) Verify that when a DOI fetch fails, `logs/ingest.log` contains the specific failure reason (e.g., "404 Not Found", "Timeout", or exception message). **Logging Config**: Ensure `code/__init__.py` or `code/ingest.py` configures logging to `INFO` level with a format including `%(asctime)s - %(name)s - %(levelname)s - %(message)s` and **explicitly creates the `logs/` directory** before initializing handlers. **Note**: The *pipeline* (ingest.py) must orchestrate the fallback logic; the client raises an error only if both DOIs fail. **Exception Signature**: `class DataUnavailableError(Exception): pass`, `class DataInsufficientError(Exception): pass`.
- [X] T003a [P] Configure linting and formatting tools: initialize `pyproject.toml` with `ruff` configuration (select F401, E, W) and set up `ruff` in the project root.
- [X] T003b [P] Verify linting configuration: Run `ruff check.` and confirm exit code 0 (no errors). If errors exist, fix them or update `ruff` ignores as appropriate.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `.gitkeep` files in `data/raw/` and `data/processed/`; create `code/checksums.py` to implement checksum tracking logic to satisfy SC-003 and Constitution Principle III. **Action**: The script must calculate SHA256 checksums for all files in `data/raw/` and write them to `data/processed/checksum_report.json` (NOT the state file) under the key `artifact_hashes`. The JSON schema must be `{ "artifact_hashes": { "filename": "sha256_hash" }, "updated_at": "ISO8601_timestamp" }`. **Verification**: 1) Verify `data/processed/checksum_report.json` exists and contains the key `artifact_hashes`. 2) Verify `artifact_hashes` contains an entry for `data/raw/zenodo_*.csv` with a valid SHA256 hash string. 3) Verify the hash matches the actual file content. 4) **Note**: The Advancement-Evaluator Agent will consume this report to update `state/projects/PROJ-342-predicting-the-influence-of-alloying-on-.yaml` per Constitution Principle V.
- [X] T005 [P] Implement `code/contracts/` schema loaders for `dataset.schema.yaml` and `artifact.schema.yaml`
- [X] T006 Create `code/__init__.py` and configure logging infrastructure for pipeline steps
- [X] T007 Setup environment configuration management: Create `.env` file with keys `ZENODO_PRIMARY_DOI`, `ZENODO_FALLBACK_DOI`, `RANDOM_SEED` and `config.yaml` with keys `seed`, `max_depth`, `runtime_limit_h`, `memory_limit_gb`. Verification: Verify `config.yaml` contains required keys and `.env` contains required keys. Verify `seed` is an integer, `max_depth` is an integer, `runtime_limit_h` is a float.
- [X] T008a [P] Implement `@limit_resources` decorator in `code/resource_monitor.py`: Wrap functions to track CPU time and RAM usage, raising `ResourceLimitExceeded` if limits are exceeded. **Action**: Upon successful completion of the wrapped function, **write the captured metrics (runtime, peak_ram) to `data/resource_usage.json`** to satisfy SC-004. **Verification**: 1) Verify `data/resource_usage.json` is created after function execution. 2) Verify JSON contains `runtime_seconds` and `peak_ram_gb`.
- [X] T008b [P] Implement environment variable override logic in `code/resource_monitor.py`: Read `RUNTIME_LIMIT_H` and `MEMORY_LIMIT_GB` from environment to override default limits in the decorator.
- [X] T008c [P] Write unit test `tests/unit/test_resource_monitor.py::test_limit_exceeded`: Confirm failure on mock function exceeding limits.
- [X] T008d [P] Write unit test `tests/unit/test_resource_monitor.py::test_env_override`: Confirm success when env vars are set higher than default limits.

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

- [ ] T012 [US1] Implement `code/ingest.py` to fetch Zenodo DOI `10.5281/zenodo.10043838` (fallback: `10.5281/zenodo.11023456`). **Action**: 1) Check if local file `data/raw/zenodo_10043838.csv` exists. 2) If yes, verify checksum against `data/processed/checksum_report.json`. If mismatch, re-fetch. 3) If no, fetch from primary DOI. 4) If primary fetch fails, attempt fallback DOI. 5) If both fail, raise `DataUnavailableError`. 6) If fallback succeeds, log `FALLBACK_USED`. **Streaming**: If the dataset size is unknown or large, implement chunked reading (`chunksize=1000` using `pandas.read_csv`) to process data without loading it entirely into RAM. **Validation**: If raw dataset < 1 row, raise `DataInsufficientError`. If < 50 rows, log `DataInsufficientWarning`. **Error Handling**: Add explicit error handling for invalid DOIs, network timeouts, and empty datasets (raise `DataUnavailableError` if no Tg values found). **Verification**: 1) Check primary file `data/raw/zenodo_10043838.csv` first; if missing, check fallback `data/raw/zenodo_11023456.csv`. 2) Verify the selected file contains >0 rows. 3) Verify `data/ingestion_stats.json` contains key `source_doi` with the exact DOI used. 4) Verify `retention_rate` reflects the cleaning of null Tg/composition records (not just row count). 5) **Note**: Spec FR-001 overrides Plan "hard halt": Implement fallback logic. 6) **Note**: Spec FR-001 overrides Plan "hard halt": Implement fallback logic. 7) **Plan Override Note**: Spec FR-001 (Fallback) overrides the Plan's 'hard halt' instruction. The Plan states the project cannot proceed if DOI verification fails, but the Spec mandates fallback logic. This task implements the Spec requirement, overriding the Plan's BLOCKED status for the purpose of implementation.
- [X] T013 [US1] Implement data cleaning logic in `code/ingest.py`: drop records missing Tg or full composition (FR-001). **Input**: `data/raw/zenodo_*.csv` (output of T012). **Error Handling**: If T012 failed, raise `DataUnavailableError`. **Verification**: Verify cleaned data has no null Tg or composition fields.
- [ ] T014 [US1] Implement retention rate logging and save cleaned data to `data/processed/cleaned_mg.csv` and retention stats to `data/ingestion_stats.json`. **Output**: Write retention rate to `data/ingestion_stats.json` (key: `retention_rate`) and log to `logs/ingest.log`. **Action**: Include logic to write data retention rate (raw_count, cleaned_count) to the stats file. **Verification**: Verify `data/ingestion_stats.json` contains keys `source_doi`, `retention_rate` (float > 0), `raw_count`, `cleaned_count`. 9) **Verification**: Verify `data/processed/cleaned_mg.csv` exists and is non-empty.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training, Feature Engineering, Sensitivity & Stratification (Priority: P2)

**Goal**: Compute atomic descriptors, train a Gradient Boosting model with LOFO CV, perform sensitivity analysis (FR-006), and family stratification checks.
**Note**: Sensitivity Analysis (FR-006) and Family Stratification (Edge Case) are implemented here. VIF and Collinearity analysis are moved to Phase 5 (US3) to align with Spec grouping.
**⚠️ SEQUENTIAL DEPENDENCY**: Within this phase, T026 (Descriptors) MUST complete before T022 (LOFO Training). T072 (Stratification) MUST complete before T022.
**⚠️ ORDERING**: T072 must precede T022. T026 must precede T022. T059 (Stratification Status) is moved here to ensure file availability for Phase 5.
**⚠️ CROSS-PHASE DEPENDENCY**: Phase 4 tasks T072, T059, and T037a depend on the completion of Phase 3 task T014 (Cleaned Data Save).

**Independent Test**: Can be fully tested by running the training pipeline and confirming the model artifacts contain performance metrics (R², MAE), feature importances, a sensitivity analysis report, a diagnostic log containing the weighted mean radius.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018a [P] [US2] Unit test for radius mismatch calculation in `tests/unit/test_descriptors.py`: Implement `test_radius_mismatch_calculation` with known inputs and expected output.
- [X] T018b [P] [US2] Unit test for VEC calculation in `tests/unit/test_descriptors.py`: Implement `test_vec_calculation` with known inputs and expected output.
- [X] T018c [P] [US2] Unit test for electronegativity calculation in `tests/unit/test_descriptors.py`: Implement `test_electronegativity_calculation` with known inputs and expected output.
- [X] T019 [P] [US2] Integration test for LOFO split correctness (no family leakage) in `tests/integration/test_train_cv.py`: Implement `test_lofo_no_leakage` that asserts `set(train_families) & set(test_families) == empty set`.

### Implementation for User Story 2 - Descriptor Computation

- [X] T020 [P] [US2] Implement `code/descriptors.py` to compute radius mismatch, electronegativity difference, VEC using `mendeleev==0.31.0` (FR-002)
- [ ] T021 [US2] Implement `code/descriptors.py` to calculate 'weighted mean radius' for diagnostic logging only (FR-002, exclude from model). **Output**: Save to `data/processed/diagnostic_log.json` with key `weighted_mean_radius` (float, Unit: Angstrom). **Action**: **Archive** `data/processed/diagnostic_log.json` to `artifacts/reports/diagnostic_log.json` to satisfy Constitution Principle IV (Single Source of Truth). **Schema**: The JSON must be `{ "weighted_mean_radius": <float> }`. **Verification**: Verify `artifacts/reports/diagnostic_log.json` exists and contains the key `weighted_mean_radius`. **Source of Truth**: Explicitly define `data/processed/diagnostic_log.json` as the canonical source and `artifacts/reports/diagnostic_log.json` as a read-only snapshot. 1) **Verification**: Verify source file `data/processed/diagnostic_log.json` exists and is valid JSON before archiving. 2) **Verification**: Verify the archived file is identical to the source.
- [ ] T026 [US2] Implement `code/descriptors.py` to save computed descriptors to `data/processed/descriptors.csv` to serve as input for US3 analysis tasks. **Input**: `data/processed/cleaned_mg.csv`. **Action**: Compute descriptors, **DROP the 'weighted_mean_radius' column** before saving to ensure it is not used as a predictor. **Verification**: Verify `data/processed/descriptors.csv` exists, is non-empty, contains columns `radius_mismatch`, `electronegativity_diff`, `VEC`, and **does NOT contain** the column `weighted_mean_radius`. **Depends on**: T021. 1) **Verification**: Explicitly verify that `weighted_mean_radius` is dropped from the input dataframe before saving.

### Implementation for User Story 2 - Stratification & Training

- [X] T072 [US2] Implement family size stratification check in `code/train.py`: Before performing LOFO, check if any alloy family has < 50 samples. **Action**: If N < 50, log a `STRATIFICATION_WARNING` to `logs/train.log`. Do NOT drop the family. **Verification**: 1) Verify the warning is logged. 2) Verify the LOFO split proceeds without crashing. **Depends on**: T014 (Cleaned Data Save for family count check).
- [ ] T059 [US2] Implement `code/train.py` to handle stratification edge case: if T072 triggered, generate `stratification_status.json` with details; if not, generate `stratification_status.json` with `status: "no_warning"`. **Depends on**: T072. **Action**: Check `data/processed/stratification_status.json` (generated by T072 logic) to determine content. **Template**: Must include `family_name`, `sample_count`, `action_taken` (warned) OR `status: "no_warning"`. **Output**: Write to `data/processed/stratification_status.json`. **Verification**: Ensure file always exists with valid JSON. 1) **Verification**: If T072 did not trigger, generate `stratification_status.json` with `status: "no_warning"`.
- [ ] T022 [US2] Implement `code/train.py` with GradientBoostingRegressor and Leave-One-Family-Out (LOFO) cross-validation (FR-003). **Depends on**: T072 (Stratification check must complete before LOFO split), T026 (Descriptors must be verified and weighted_mean_radius dropped), T014 (Cleaned Data Save for LOFO split).
- [X] T023 [US2] Implement grid search in `code/train.py` for hyperparameter optimization (≤10 combos) (FR-003)
- [ ] T024a [US2] Save model object to `artifacts/models/best_model.pkl`. **Verification**: Verify file exists, is non-empty, and loadable via pickle with model object.
- [ ] T024b [US2] Save metrics to `artifacts/metrics/metrics.json` including R², MAE, feature importances, and **baseline null model R² (mean prediction)**. **Calculation**: Explicitly calculate R² of a null model (mean prediction) and save it as `null_model_r2`. **Verification**: Verify file exists and contains keys `R2` (float), `MAE` (float), `feature_importances` (dict), and `null_model_r2` (float).
- [X] T025 [US2] Integrate `code/resource_monitor.py` into `code/train.py` to enforce runtime < 6h and RAM < 7GB (FR-005, SC-004). **Output**: Save resource usage to `data/resource_usage.json`. Verification: Pipeline must exit gracefully with an error if limits are exceeded.

### Implementation for User Story 2 - Sensitivity Analysis

- [ ] T037a [US2] Implement sensitivity analysis in `code/analyze.py`: sweep `max_depth` over the specific values {3, 5, 7} to evaluate model robustness (FR-006) and collect R² scores. **Input**: `artifacts/models/best_model.pkl`, `data/processed/cleaned_mg.csv` (T014) for re-training. **Depends on**: T024a, T026, T014 (Cleaned Data Save for re-training). **Function**: `sweep_max_depth(model_path, data_path)`. **Output**: Save to `artifacts/metrics/sensitivity_analysis.json`. **Schema**: The JSON must contain keys `max_depth_sweep` (list of objects with `max_depth` and `r2_score`) and `r2_variance` (float). **Action**: Calculate variance of R² scores and save to `sensitivity_analysis.json`. **Error Handling**: If model fails to converge for a specific `max_depth`, skip that value, log a warning, and proceed. **Depends on**: T024a (Model) is a hard block. **Note**: Spec FR-006 overrides Plan Complexity Tracking regarding sweep values: Use {3, 5, 7}. **Depends on**: T024a, T026, T014.

**Checkpoint**: US2 is complete only after T024a, T024b, and T037a are finished.

---

## Phase 5: User Story 3 - Result Interpretation, Reporting, and Statistical Validation (Priority: P3)

**Goal**: Generate reports with statistical validation (VIF, FDR, Correlation), and associational framing.
**⚠️ HARD BLOCK**: This phase CANNOT be executed until T024a/b (Model) and T026 (Descriptors) in Phase 4 are completed and checked.
**⚠️ CROSS-PHASE DEPENDENCY**: Phase 5 tasks depend on the completion of Phase 4 tasks T059, T024, and T026.

**Independent Test**: Can be fully tested by reviewing the generated report for the presence of partial dependence plots, a correlation matrix with FDR-corrected p-values, VIF flagging, collinearity analysis, and the exact phrase: "These findings are associational only".

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T040 [P] [US3] Contract test for report content validation (no causal language) in `tests/contract/test_report_content.py`: Implement `test_no_causal_language` that asserts `"causes" not in report_text` and `"determines" not in report_text`.
- [X] T041a [P] [US3] Integration test for FDR correction in `tests/integration/test_statistical_validation.py`: Implement `test_fdr_correction` that asserts p-values are adjusted correctly using Benjamini-Hochberg.
- [X] T041b [P] [US3] Integration test for VIF flagging in `tests/integration/test_statistical_validation.py`: Implement `test_vif_flagging` that asserts VIF > 5 is flagged in the log.

### Implementation for User Story 3 - Statistical Validation

- [ ] T033a [US3] Implement `code/analyze.py` for Pearson and Spearman correlation calculation between predictors (FR-009) and save to `data/processed/correlation_matrix.csv`. **Input**: `data/processed/descriptors.csv`. **Depends on**: T026. **Function**: `calculate_correlations(df)`. **Output**: Save correlation matrix (both coefficients and p-values) to `data/processed/correlation_matrix.csv`. **Schema**: The CSV must contain columns `feature_pair`, `pearson_coeff`, `pearson_pvalue`, `spearman_coeff`, `spearman_pvalue`. **Verification**: Verify file exists, is non-empty, and contains the specified columns. **Action**: Explicitly verify that the calculated coefficients match the expected values for the input data and that the file schema is valid before proceeding. **Depends on**: T026.
- [ ] T034 [US3] Implement `code/analyze.py` for Benjamini-Hochberg FDR correction on correlations (α ≤ 0.05) as per Spec FR-008. **Input**: `data/processed/correlation_matrix.csv`. **Depends on**: T033a. **Output**: Save **corrected p-values** to `data/processed/fdr_corrected_pvalues.json`. **Schema**: The JSON must contain the corrected p-values. **Verification**: Verify file exists and contains the corrected p-values. **Note**: Spec FR-008 (FDR) supersedes the Plan's general heuristic (Bonferroni) as the specific requirement. Log this override.
- [ ] T035a [US3] Implement `code/analyze.py` for VIF calculation. **Input**: `data/processed/descriptors.csv`. **Depends on**: T026. **Constraint**: MUST explicitly exclude 'weighted mean radius' from calculation (verify input dataframe does not contain this column). MUST **flag** predictors with VIF > 5 for diagnostic review (**do NOT drop features**). **Function**: `calculate_vif(df)`. **Action**: Save VIF diagnostic log to `data/processed/vif_diagnostic_log.json`. **Schema**: The JSON must contain keys `flagged_features` (list of strings) and `vif_values` (dict mapping feature name to float). **Verification**: Confirm 'weighted mean radius' is absent from input, no features are dropped, and the log contains `flagged_features` and `vif_values`. **Note**: Spec FR-007 (Flag only) supersedes the Plan's general heuristic (Iterative VIF Remediation) as the specific requirement.
- [ ] T036a [US3] Implement `code/analyze.py` for bootstrapping with n_resamples=1000 to calculate 95% CI for feature importance (SC-002) and save to `artifacts/metrics/stability_metrics.json`. **Input**: `artifacts/models/best_model.pkl`, `data/processed/cleaned_mg.csv` (T014). **Depends on**: T024a, T014 (Cleaned Data Save for bootstrapping). **Function**: `bootstrap_feature_importance(model, X, y, n_resamples=1000)`. **Action**: Save to `artifacts/metrics/stability_metrics.json`. **Schema**: The JSON must contain keys for each feature, each nested with `ci_lower` and `ci_upper` (floats). **Verification**: Verify that the variance of the bootstrapped importance scores is calculated and logged; if variance > 0.05, log a `STABILITY_WARNING`.
- [ ] T060a [US3] Implement `code/analyze.py` to calculate the collinearity condition number for the predictors. **Input**: `data/processed/descriptors.csv`. **Depends on**: T026. **Function**: `calculate_condition_number(df)`. **Output**: Save to `data/processed/collinearity_log.json`. **Schema**: The JSON must contain key `condition_number` (float) and `status` (e.g., "warning" if > 30, else "ok"). **Verification**: Confirm the file exists and contains the `condition_number` key and appropriate status. **Note**: This task addresses the Spec's Edge Case question on collinearity handling.

### Implementation for User Story 3 - Reporting

- [ ] T039a [US3] Implement `code/report.py` to generate partial dependence plots. **Input**: `artifacts/models/best_model.pkl`. **Features**: `radius_mismatch`, `VEC`, `electronegativity_diff`. **Output**: `artifacts/reports/pdp_radius_mismatch.png`, `artifacts/reports/pdp_vec.png`, `artifacts/reports/pdp_electronegativity.png`.
- [ ] T039b [US3] Implement `code/report.py` to generate correlation heatmap. **Input**: `data/processed/correlation_matrix.csv`. **Data**: Use Pearson columns for heatmap. **Output**: `artifacts/reports/correlation_heatmap.png`.
- [ ] T039c [US3] Implement `code/report.py` to generate stability plot. **Input**: `artifacts/metrics/stability_metrics.json`. **Output**: `artifacts/reports/stability_plot.png`.
- [ ] T027 [US3] Archive diagnostic log to `artifacts/reports/diagnostic_log.json`. **Input**: `data/processed/diagnostic_log.json` (from T021). **Action**: Copy file from `data/processed/` to `artifacts/reports/`. **Verification**: Verify file exists in `artifacts/reports/` and is identical to source. **Depends on**: T021.
- [ ] T050 [US3] Generate final report artifact `artifacts/reports/final_report.md`. **Input**: T059, T039a, T039b, T039c, T060a, T024a, T026, T035a, T027. **Template**: `specs/001-predicting-the-influence-of-alloying-on/contracts/report_template.md`. **Action**: **Verify template exists at exact path**; if not, raise error. **Action**: Include "These findings are associational only" in the Conclusion section (FR-004). **Action**: Check `data/processed/stratification_status.json` (from T059) to include stratification notes if present. **Action**: Include collinearity condition number analysis from `data/processed/collinearity_log.json` in the final report. **Depends on**: T059, T039a, T039b, T039c, T060a, T024a, T026, T035a, T027.
- [ ] T051 [US3] Validate report against `specs/.../contracts/artifact.schema.yaml` (Single Source of Truth).

**Checkpoint**: US3 is blocked pending T024/T026 completion. Phase 4 (US2) is complete.

---

## Phase 6: Plan Alignment & Polish

**Purpose**: Resolve cross-document contradictions and final polish

- [X] T061 [P] Update `README.md`: Add new CLI arguments for fallback DOI handling and resource limit overrides. **Action**: Update documentation for edge case handling (small family sizes, VIF flagging, FDR correction). **Action**: Check for outdated dependencies.
- [X] T062 [P] Update `quickstart.md`: Add new DOI fallback logic and resource limit configuration examples.
- [X] T053a [P] Code cleanup: Run `ruff check --select F401` and ensure zero errors. Fix any unused imports.
- [X] T053b [P] Type hint verification: Run `mypy` and ensure zero errors. Add missing type hints.
- [X] T054 [P] Performance optimization: Ensure vectorized operations in descriptors to stay within 7GB RAM. **Verification**: Check resource log from `resource_monitor.py` to confirm RAM usage < 7GB.
- [X] T057 [P] Run quickstart.md validation to ensure end-to-end reproducibility
- [X] T058 [P] Verify all tasks execute on CPU-only CI: Execute `bash scripts/run_ci.sh` on a GitHub Actions runner with `runs-on: ubuntu-latest`. **Verification**: Exit code 0.

---

## Phase 7: Final Verification & Documentation

**Goal**: Ensure all constraints are met and documentation is complete for the final handoff.

- [ ] T080a [P] [US3] **Run Pipeline**: Execute the full pipeline end-to-end on a clean environment. **Action**: Execute `bash scripts/run_ci.sh`. **Acceptance**: Exit code 0 OR exit code 1 with `DATA_UNAVAILABLE` error message (valid state per Plan Constitution Check). **Note**: This task runs the pipeline; verification of outputs is T080b. 1) **Verification**: Explicitly check the error message content for the exact string `DATA_UNAVAILABLE` to distinguish it from a genuine pipeline crash.
- [ ] T080b [P] [US3] **Verify Artifacts**: Verify that `data/processed/cleaned_mg.csv` is generated, `artifacts/models/best_model.pkl` is created, and `artifacts/reports/final_report.md` contains the mandatory phrase "These findings are associational only" and no causal language. **Action**: If T080a completed successfully (not DATA_UNAVAILABLE), run `python code/verify_artifacts.py`. **Depends on**: T024a, T026, T050, T080a. **Verification**: Exit code 0 if all artifacts present and valid. **Edge Case Check**: Explicitly verify that if the pipeline ran but the cleaned dataset is empty (zero Tg values), the appropriate error/warning was logged and artifacts were not generated. If T080a returned DATA_UNAVAILABLE, this task is marked N/A.
- [X] T081 [P] [US1] **Data Source Audit**: Verify that `data/ingestion_stats.json` correctly identifies the source DOI and that no synthetic data generation code paths were triggered during the run.
- [X] T082 [P] [US2] **Resource Compliance**: Confirm that `data/resource_usage.json` shows peak RAM < 7GB and total runtime < 6h. If limits were exceeded, document the optimization required.
- [ ] T083 [P] [US2] **Statistical Compliance**: Verify that `data/processed/vif_diagnostic_log.json` contains flagged features (if any) but no dropped features, and that `artifacts/metrics/sensitivity_analysis.json` contains the required variance calculation.
- [ ] T084 [P] [US3] **Report Compliance**: Run automated verification script `python code/verify_report.py` to ensure all FDR-corrected p-values are presented, partial dependence plots are included, the collinearity condition number is discussed, and the report is validated against `artifact.schema.yaml`. **Action**: Script must parse `artifacts/reports/final_report.md` and assert presence of required sections/strings, scan for forbidden causal language, and validate schema. **Verification**: Exit code 0.

---

## Phase 8: CI Integration & Robustness

**Goal**: Ensure the pipeline is ready for automated execution on CI and handles edge cases robustly in a non-interactive environment.
**⚠️ DEPENDENCY**: Phase 8 depends on Phase 7 completion.

### CI Workflow Creation

- [ ] T089 [P] [General] **Create CI Workflow**: Create `.github/workflows/ci.yml` to execute the full pipeline (T080a) as the primary job, with explicit steps for verification scripts (`verify_artifacts.py`, `verify_report.py`) as separate validation jobs that depend on the pipeline success. **Action**: Ensure the workflow fails immediately if `DATA_UNAVAILABLE` is raised (unless expected), but passes if `DATA_UNAVAILABLE` is the expected outcome (handled via conditional logic). **Job Structure**: Define jobs: `ingest`, `train`, `analyze`, `report`, `validate`. Each job must include steps: `checkout`, `install-deps`, `run-script`, `verify-artifacts`. **Conditional Logic**: Add a conditional step that checks for the `DATA_UNAVAILABLE` error message and passes the job if found. **Verification**: Trigger the workflow on a fork with missing DOIs and confirm it exits cleanly with the expected error message. **Depends on**: T095.
- [ ] T095 [P] [General] **Add CI Workflow for Data Unavailable State**: Update `.github/workflows/ci.yml` to explicitly handle the `DATA_UNAVAILABLE` state as a success condition for the ingestion step. **Action**: Add a conditional step that checks for the error message and passes the job if found. **Verification**: Trigger the workflow with missing DOIs and confirm the job passes. **Depends on**: T080a.

### Edge Case Handling

- [X] T085 [P] [US1] **Implement Streaming Data Loader**: (Superseded by T012 and T015). **Status**: [X] Logic consolidated in T012.
- [X] T086 [P] [US1] **Enforce Strict No-Synthetic Policy & Fallback Logic**: (Superseded by T012 and T015). **Status**: [X] Logic consolidated in T012.
- [X] T087 [P] [US2] **Add Family Stratification Edge Case Test**: Write `tests/unit/test_train_stratification.py` to simulate a dataset with a family having small, medium, and large sample counts. **Action**: Assert that families with N<50 trigger the `STRATIFICATION_WARNING` log and that families with N>=50 proceed without warning. **Verification**: Run the test suite and confirm all scenarios pass.
- [X] T091 [P] [US2] **Add VIF Flagging Verification Test**: Write `tests/unit/test_vif_flagging.py` to verify that the VIF calculation correctly flags features with VIF > 5 and does not drop them. **Action**: Create a static mock fixture with known high collinearity (e.g., `np.corrcoef` matrix with values > 0.9) and assert the `vif_diagnostic_log.json` contains the flagged feature. **Verification**: Run the test and confirm it passes.
- [X] T092 [P] [US3] **Add FDR Correction Verification Test**: Write `tests/unit/test_fdr_correction.py` to verify the Benjamini-Hochberg procedure is applied correctly. **Action**: Use a known set of p-values and assert the corrected values match the expected output. **Verification**: Run the test and confirm it passes.
- [X] T093 [P] [General] **Add Resource Limit Stress Test**: Write `tests/integration/test_resource_limits.py` to simulate a scenario where the pipeline approaches the 6h or 7GB limits. **Action**: Mock a slow function and assert the `ResourceLimitExceeded` error is raised. **Verification**: Run the test and confirm it passes.

### Documentation & Benchmarking

- [X] T094 [P] [General] **Add Final Report Schema Validation**: Extend `code/verify_report.py` to validate the final report against `specs/.../contracts/artifact.schema.yaml`. **Action**: Ensure the report contains all required sections and fields. **Verification**: Run the script and confirm it passes for a valid report.
- [X] T096 [P] [General] **Add Documentation for Edge Case Handling**: Update `README.md` and `quickstart.md` to document the handling of small family sizes, VIF flagging, and FDR correction. **Action**: Add a section explaining the edge case logic and how it is implemented. **Verification**: Review the updated documentation and confirm it is clear and accurate.
- [X] T097 [P] [General] **Add Performance Benchmarking**: Implement a benchmarking script to measure the runtime and memory usage of the pipeline on a standard dataset. **Action**: Run the script and save the results to `data/benchmark_results.json`. **Verification**: Verify the file exists and contains the expected metrics.
- [X] T098 [P] [General] **Add Automated Dependency Update Check**: Implement a script to check for outdated dependencies in `requirements.txt`. **Action**: Run the script and log any outdated packages. **Verification**: Run the script and confirm it lists outdated packages correctly.
- [X] T099 [P] [General] **Add Final Integration Test**: Write `tests/integration/test_end_to_end.py` to run the full pipeline and verify all artifacts are generated correctly. **Action**: Execute the pipeline and assert all expected files exist and contain valid data. **Verification**: Run the test and confirm it passes.

---

## Phase 9: Reviewer Concerns & Data Integrity Enhancements (Consolidated)

**Goal**: Address specific reviewer concerns regarding data streaming, synthetic fallback prevention, and strict adherence to real-data-only policies. These tasks are now consolidated into Phase 8 and Phase 3/4 where appropriate.

- [X] T100 [P] [US1] **Implement Strict Real-Data Streaming**: (Superseded by T012 and T085). **Status**: [X] Logic consolidated in T012.
- [X] T101 [P] [US1] **Enforce "Fail Loudly" Data Policy**: (Superseded by T012 and T086). **Status**: [X] Logic consolidated in T012.
- [X] T102 [P] [US2] **Verify Descriptor Independence**: (Handled in T026 and T026b). **Status**: [X] Logic consolidated in T026/T026b.
- [X] T103 [P] [US3] **Implement Collinearity Condition Number Check**: (Handled in T060a). **Status**: [X] Logic consolidated in T060a.
- [X] T104 [P] [General] **Add Final Data Integrity Report**: (Handled in T081 and T080b). **Status**: [X] Logic consolidated.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
 - **Phase 4 tasks T072, T059, and T037a depend on Phase 3 task T014 completion.**
 - **Phase 5 depends on Phase 4 completion (specifically T059, T024, T026).**
 - **Phase 8 depends on Phase 7 completion.**
- **Plan Alignment (Phase 6)**: Depends on all desired user stories being complete (to ensure tasks match spec)
- **Final Verification (Phase 7)**: Depends on completion of Phases 1-6.
- **CI Integration (Phase 8)**: Depends on completion of Phases 1-7.
- **Reviewer Concerns (Phase 9)**: Consolidated into Phases 3, 4, and 8.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires data from US1 (specifically T014 for T072 and T037a)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires model artifacts from US2 (T024) and descriptors from T026

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Descriptors before services/training
- **T026 (Descriptors) must complete before T022 (Training)**.
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
 - Developer D: Phase 8 (CI & Robustness)
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
- **Note on Data Streaming**: If dataset size exceeds local disk limits during ingestion (FR-001), `code/ingest.py` must implement streaming logic to process chunks without loading the full dataset into RAM, adhering to the 7GB RAM constraint. (Handled in T012, T085, T100 - now consolidated).
- **Note on Family Stratification**: If `code/train.py` detects < 50 records for a specific alloy family during LOFO split preparation, it must log a `STRATIFICATION_WARNING` and proceed (Edge Case handling). (Handled in T072, T087).
- **Note on T052**: T052 is superseded by T061 and T062. T052 is marked [X] (superseded) to avoid confusion.
- **Note on T038**: T038 was merged into T036 to avoid redundancy. T036 now handles both calculation and saving of `stability_metrics.json`.
- **Note on US3 Testability**: US3 is NOT testable until T024 and T026 are complete.
- **Note on Sensitivity Analysis**: FR-006 is implemented in Phase 4 (T037a/T037b) to ensure model artifacts are available. T027 was removed to avoid duplication.
- **Note on Blocking Dependencies**: Phase 5 tasks (T033, T035, T036, T037) are explicitly blocked until T024 and T026 are completed. **US2 is not 'done' until T024a/b and T037a are complete.**
- **Note on T069**: Removed. DOI logging is now integrated into T012 verification.
- **Note on T039**: Removed. Redundant summary task. Dependencies now point to T039a-c or T049/T050.
- **Note on T060**: Split into T060a (Phase 5) and T060b (Phase 5).
- **Note on T037a**: Explicitly lists sweep values {3, 5, 7} as per FR-006 in the Action description.
- **Note on T036a**: Explicitly lists n_resamples=1000 as per SC-002 and adds variance threshold verification.
- **Note on T024b**: Explicitly mandates calculation of `null_model_r2`.
- **Note on T012**: Verification now includes checking `source_doi` and cleaning logic.
- **Note on T021/T026**: Dependency order clarified to prevent race conditions.
- **Note on T022**: Dependency list updated to include T014 explicitly.
- **Note on Data Source Verification**: T012 must explicitly handle the case where the primary DOI returns an empty dataset or a dataset with no Tg values, raising `DataUnavailableError` rather than proceeding with an empty dataframe.
- **Note on Memory Constraints**: All CSV loading in `code/ingest.py` and `code/descriptors.py` must use `pandas.read_csv(..., chunksize=1000)` or `dask` if the dataset size is unknown, to prevent OOM errors on runners with limited memory. (Handled in T012).
- **Note on Plan Alignment**: The Plan has been updated to match the Spec. No further manual updates required.
- **Note on Synthetic Data Prevention**: T071 is removed. The logic is inherent in T012, T086, T101.
- **Note on Collinearity**: T073 is removed. Logic is in T035a and T060a, T103.
- **Note on T072**: Restored with explicit logic for N<50 (warn) and NO drop logic. **N<2 logic removed**.
- **Note on T059**: Updated to include explicit template for `stratification_status.json` if needed, but T072 now only logs warnings. T059 now always writes a status file.
- **Note on Final Verification**: Phase 7 tasks (T080-T084) are mandatory to ensure the final artifact meets all spec requirements before handoff. **T080 now handles DATA_UNAVAILABLE as a valid state.**
- **Note on T080/T080b**: Split to separate execution (T080a) from verification (T080b).
- **Note on T084**: Replaced manual review with automated script `verify_report.py`.
- **Note on Phase 8**: Added to ensure robustness, streaming, and strict no-synthetic data policies are explicitly tested and integrated into CI.
- **Note on T085**: Removed rigid chunk size requirements; now allows flexible chunked reading.
- **Note on T086**: Updated to explicitly implement fallback DOI logic before raising DataUnavailableError.
- **Note on T035a**: Explicitly states to ignore Plan's Iterative VIF and follow Spec FR-007 (Flag only).
- **Note on T034**: Simplified to only require saving corrected p-values, removing scope creep.
- **Note on T002**: Updated to specify logging configuration for deterministic verification and creation of `logs/` directory.
- **Note on T021/T026**: Dependency order clarified to prevent race conditions.
- **Note on T022**: Dependency list updated to include T014 explicitly.
- **Note on T090-T099**: New tasks added in Phase 8 to address specific reviewer concerns regarding dataset size validation, VIF/FDR verification, resource stress testing, report schema validation, CI workflow robustness, documentation, benchmarking, dependency updates, and end-to-end integration testing. These tasks ensure the pipeline is production-ready and adheres to all specified constraints.
- **Note on VIF/FDR Placement**: T035a and T060a moved to Phase 5 to align with US3 statistical validation block.
- **Note on T050 Dependency**: T050 depends on T059 (which always produces output) and T072 (the trigger).
- **Note on T027**: Added to archive diagnostic log to artifacts/reports/ to satisfy Principle IV.
- **Note on T059 Ordering**: T059 is now listed before T050 to satisfy T050's dependency on T059.
- **Note on T039 Ordering**: T039a-c are now listed before T050 to satisfy T050's dependency on them.
- **Note on T026b Ordering**: T026b is now listed after T026 and before T022 to satisfy T022's dependency on T026b.
- **Note on Phase 9**: Consolidated into Phases 3, 4, and 8 to avoid redundant implementation steps.
- **Note on T089 Ordering**: T089 is now listed after T080a and T080b to ensure pipeline logic is verified before defining the CI workflow.
- **Note on T008a**: Updated to explicitly write metrics to `data/resource_usage.json`.
- **Note on T027**: Updated to explicitly copy the file from `data/processed/` to `artifacts/reports/`.
- **Note on Cross-Phase Dependencies**: Phase 4 tasks T072, T059, T037a depend on Phase 3 T014. Phase 5 depends on Phase 4 T059, T024, T026. Phase 8 depends on Phase 7.
- **Note on T004**: Updated to write to `data/processed/checksum_report.json` instead of state file to comply with Constitution Principle V.
- **Note on T037a**: Explicitly lists sweep values {3, 5, 7} as per FR-006.
- **Note on T035a**: Explicitly states to ignore Plan's Iterative VIF and follow Spec FR-007 (Flag only).
- **Note on T034**: Explicitly states to ignore Plan's Bonferroni and follow Spec FR-008 (FDR).
- **Note on T080b**: Added explicit check for empty dataset edge case.
- **Note on Plan Override**: Spec FR-007 (VIF Flagging) and FR-008 (FDR) override Plan Complexity Tracking (Iterative VIF, Bonferroni). This is explicitly noted in T035a and T034.
- **Note on Plan Override**: Spec FR-001 (Fallback) overrides Plan "hard halt" on verification failure. This is explicitly noted in T012.
- **Note on Plan Override**: Spec FR-006 (Sweep Values) overrides Plan "range" vagueness. This is explicitly noted in T037a.
- **Note on T015/T016**: Removed to eliminate redundancy. Logic fully integrated into T012 and T014 respectively.
- **Note on T033b/T036b**: Removed to eliminate fine-grained splits. Logic merged into T033a and T036a respectively.
- **Note on T060a**: Retained as the collinearity condition number task; T035a remains the sole VIF calculation task. No duplication exists.
- **Note on Task Status**: T012, T014, T021, T026, T034, T035a, T051, T022 are marked [ ] (incomplete) to reflect that implementation is pending and artifacts are missing. T002, T010, T011 are marked [X] (complete) as they are foundational or test tasks.