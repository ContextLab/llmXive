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
- [X] T002 [P] Implement Zenodo API client in `code/zenodo_client.py` to fetch datasets using DOIs from `config.yaml`. The client must handle authentication, rate limits, and raise a specific `DataUnavailableError` if both primary (10.5281/zenodo.10043838) and fallback (10.5281/zenodo.11023456) DOIs are unreachable. Verification: Unit test confirms error raising on mocked client error responses.
- [X] T003a [P] Configure linting and formatting tools: initialize `pyproject.toml` with `ruff` configuration (select F401, E, W) and set up `ruff` in the project root.
- [X] T003b [P] Verify linting configuration: Run `ruff check.` and confirm exit code 0 (no errors). If errors exist, fix them or update `ruff` ignores as appropriate.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `.gitkeep` files in `data/raw/` and `data/processed/`; implement checksum tracking logic in `code/` (e.g., `code/checksums.py`) to satisfy SC-003 and Constitution Principle III.
- [X] T005 [P] Implement `code/contracts/` schema loaders for `dataset.schema.yaml` and `artifact.schema.yaml`
- [X] T006 Create `code/__init__.py` and configure logging infrastructure for pipeline steps
- [X] T007 Setup environment configuration management: Create `.env` file with keys `ZENODO_PRIMARY_DOI`, `ZENODO_FALLBACK_DOI`, `RANDOM_SEED` and `config.yaml` with keys `seed`, `max_depth`, `runtime_limit_h`, `memory_limit_gb`. Verification: Verify `config.yaml` contains required keys and `.env` contains required keys.
- [X] T008a [P] Implement `@limit_resources` decorator in `code/resource_monitor.py`: Wrap functions to track CPU time and RAM usage, raising `ResourceLimitExceeded` if limits are exceeded.
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

- [ ] T012 [US1] Implement `code/ingest.py` to fetch Zenodo DOI (fallback: 10.5281/zenodo.11023456). If both DOIs fail, halt with `DATA_UNAVAILABLE` error (raise `DataUnavailableError`) as per FR-001. If the fallback DOI succeeds, proceed and log a `FALLBACK_USED` warning. **Verification**: 1) Check primary file `data/raw/zenodo_10043838.csv` first; if missing, check fallback `data/raw/zenodo_11023456.csv`. 2) Verify the selected file contains >0 rows. 3) Verify `data/ingestion_stats.json` contains key `source_doi` with the exact DOI used. 4) Verify `retention_rate` reflects the cleaning of null Tg/composition records (not just row count). <!-- FAILED: unspecified -->
- [X] T013 [US1] Implement data cleaning logic in `code/ingest.py`: drop records missing Tg or full composition (FR-001). **Input**: Detect which of `zenodo_10043838.csv` or `zenodo_11023456.csv` exists in `data/raw/` and use that as input.
- [X] T014 [US1] Implement retention rate logging and save cleaned data to `data/processed/cleaned_mg.csv` and retention stats to `data/ingestion_stats.json`. **Output**: Write retention rate to `data/ingestion_stats.json` (key: `retention_rate`) and log to `logs/ingest.log`. **Verification**: Verify `data/ingestion_stats.json` contains key `retention_rate` with a float value > 0.
- [X] T015 [US1] Add error handling for invalid DOIs: if primary DOI fails, attempt fallback to secondary DOI; if both fail, halt with DATA_UNAVAILABLE (FR-001)
- [X] T016 [US1] Write data retention rate and record counts to `data/ingestion_stats.json` to satisfy SC-003 and Single Source of Truth (SC-003)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Model Training, Feature Engineering, and Sensitivity Analysis (Priority: P2)

**Goal**: Compute atomic descriptors, train a Gradient Boosting model with LOFO CV, and prepare artifacts for analysis.
**Note**: Sensitivity Analysis (FR-006) is implemented in Phase 5 (T037) to align with the model artifact availability. The 'weighted mean radius' diagnostic is handled here (T021).

**Independent Test**: Can be fully tested by running the training pipeline and confirming the model artifacts contain performance metrics (R², MAE), feature importances, and a diagnostic log containing the weighted mean radius.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018a [P] [US2] Unit test for radius mismatch calculation in `tests/unit/test_descriptors.py`: Implement `test_radius_mismatch_calculation` with known inputs and expected output.
- [X] T018b [P] [US2] Unit test for VEC calculation in `tests/unit/test_descriptors.py`: Implement `test_vec_calculation` with known inputs and expected output.
- [X] T018c [P] [US2] Unit test for electronegativity calculation in `tests/unit/test_descriptors.py`: Implement `test_electronegativity_calculation` with known inputs and expected output.
- [X] T019 [P] [US2] Integration test for LOFO split correctness (no family leakage) in `tests/integration/test_train_cv.py`: Implement `test_lofo_no_leakage` that asserts `set(train_families) & set(test_families) == empty set`.

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/descriptors.py` to compute radius mismatch, electronegativity difference, VEC using `mendeleev==0.31.0` (FR-002)
- [X] T021 [US2] Implement `code/descriptors.py` to calculate 'weighted mean radius' for diagnostic logging only (FR-002, exclude from model). **Output**: Save to `data/processed/diagnostic_log.json` with key `weighted_mean_radius`. **Verification**: Verify `data/processed/diagnostic_log.json` exists and contains the key `weighted_mean_radius`.
- [ ] T026 [US2] Implement `code/descriptors.py` to save computed descriptors to `data/processed/descriptors.csv` to serve as input for US3 analysis tasks. **Verification**: Verify `data/processed/descriptors.csv` exists, is non-empty, and contains columns `radius_mismatch`, `electronegativity_diff`, `VEC`.
- [X] T022 [US2] Implement `code/train.py` with GradientBoostingRegressor and Leave-One-Family-Out (LOFO) cross-validation (FR-003)
- [X] T023 [US2] Implement grid search in `code/train.py` for hyperparameter optimization (≤10 combos) (FR-003)
- [ ] T024a [US2] Save model object to `artifacts/models/best_model.pkl`. **Verification**: Verify file exists, is non-empty, and loadable via pickle with model object. <!-- FAILED: unspecified -->
- [ ] T024b [US2] Save metrics to `artifacts/metrics/metrics.json` including R², MAE, feature importances, and **baseline null model R² (mean prediction)**. **Calculation**: Explicitly calculate R² of a null model (mean prediction) and save it as `null_model_r2`. **Verification**: Verify file exists and contains keys `R2`, `MAE`, `feature_importances`, and `null_model_r2`. <!-- FAILED: unspecified -->
- [X] T025 [US2] Integrate `code/resource_monitor.py` into `code/train.py` to enforce runtime < 6h and RAM < 7GB (FR-005, SC-004). Verification: Pipeline must exit gracefully with an error if limits are exceeded.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. **Note**: T024a/b and T026 are prerequisites for Phase 5. Phase 5 tasks are blocked until T024 and T026 are checked.

---

## Phase 5: User Story 3 - Result Interpretation, Reporting, and Statistical Validation (Priority: P3)

**Goal**: Generate reports with statistical validation, FDR correction, and associational framing. Perform Sensitivity Analysis and VIF checks here as per Plan/Spec.

**Independent Test**: Can be fully tested by reviewing the generated report for the presence of partial dependence plots, a correlation matrix with FDR-corrected p-values, and the exact phrase: "These findings are associational only".
**⚠️ BLOCKING DEPENDENCY**: This phase CANNOT be executed until T024a/b (Model) and T026 (Descriptors) in Phase 4 are completed and checked.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T040 [P] [US3] Contract test for report content validation (no causal language) in `tests/contract/test_report_content.py`: Implement `test_no_causal_language` that asserts `"causes" not in report_text` and `"determines" not in report_text`.
- [X] T041a [P] [US3] Integration test for FDR correction in `tests/integration/test_statistical_validation.py`: Implement `test_fdr_correction` that asserts p-values are adjusted correctly using Benjamini-Hochberg.
- [X] T041b [P] [US3] Integration test for VIF flagging in `tests/integration/test_statistical_validation.py`: Implement `test_vif_flagging` that asserts VIF > 5 is flagged in the log.

### Implementation for User Story 3

- [ ] T033a [US3] Implement `code/analyze.py` for Pearson and Spearman correlation calculation between predictors (FR-009). **Input**: `data/processed/descriptors.csv`. **Depends on**: T026. **Function**: `calculate_correlations(df)`. **Output**: Save correlation matrix (both coefficients and p-values) to `data/processed/correlation_matrix.csv`. **Verification**: Verify file exists and contains both Pearson and Spearman columns.
- [ ] T033b [US3] Verify `data/processed/correlation_matrix.csv` content in `code/analyze.py`. **Verification**: Assert CSV is non-empty and contains expected columns. <!-- FAILED: unspecified -->
- [X] T034 [US3] Implement `code/analyze.py` for Benjamini-Hochberg FDR correction on correlations (α ≤ 0.05) as per Spec FR-008. **Input**: Results from T033. **Depends on**: T033.
- [ ] T035a [US3] Implement `code/analyze.py` for VIF calculation. **Input**: `data/processed/descriptors.csv`. **Depends on**: T026. **Constraint**: MUST explicitly exclude 'weighted mean radius' from calculation. MUST **flag** predictors with VIF > 5 for diagnostic review (do NOT drop). **Function**: `calculate_vif(df)`. **Output**: Save diagnostic log to `data/processed/vif_diagnostic_log.json` (FR-007, Spec). **Verification**: Confirm 'weighted mean radius' is excluded, no features are dropped, and the log contains the flag logic. <!-- ATOMIZE: requested -->
- [ ] T035b [US3] Verify `data/processed/vif_diagnostic_log.json` content. **Verification**: Assert file exists and contains `flagged_features` key.
- [ ] T036a [US3] Implement `code/analyze.py` for bootstrapping with n_resamples=1000 to calculate 95% CI for feature importance (SC-002). **Input**: `artifacts/models/best_model.pkl`. **Depends on**: T024a. **Function**: `bootstrap_feature_importance(model, X, y, n_resamples=1000)`. <!-- FAILED: unspecified -->
- [~] T036b [US3] Save stability metrics (including 95% CI bounds) to `artifacts/metrics/stability_metrics.json`. **Verification**: Verify `artifacts/metrics/stability_metrics.json` exists and contains `ci_lower` and `ci_upper` keys.
- [~] T037a [US3] Implement sensitivity analysis in `code/analyze.py`: sweep `max_depth` over values {3, 5, 7} and collect R² scores. **Input**: `artifacts/models/best_model.pkl` (and raw data for re-training). **Depends on**: T024a. **Function**: `sweep_max_depth(model_path, data_path)`. **Note**: This task re-trains models with different max_depth values to compute variance. <!-- FAILED: unspecified -->
- [~] T037b [US3] Calculate variance of R² scores from T037a and save to `artifacts/metrics/sensitivity_analysis.json` with keys `max_depth_sweep` and `r2_variance`. **Verification**: Verify `artifacts/metrics/sensitivity_analysis.json` exists and contains the specified keys. <!-- FAILED: unspecified -->
- [~] T039a [US3] Implement `code/report.py` to generate partial dependence plots. **Input**: `artifacts/models/best_model.pkl`. **Output**: `artifacts/reports/pdp_radius_mismatch.png`, `artifacts/reports/pdp_vec.png`, `artifacts/reports/pdp_electronegativity.png`.
- [~] T039b [US3] Implement `code/report.py` to generate correlation heatmap. **Input**: `data/processed/correlation_matrix.csv`. **Output**: `artifacts/reports/correlation_heatmap.png`.
- [~] T039c [US3] Implement `code/report.py` to generate stability plot. **Input**: `artifacts/metrics/stability_metrics.json`. **Output**: `artifacts/reports/stability_plot.png`. <!-- FAILED: unspecified -->
- [~] T049 [US3] Implement `code/report.py` to enforce associational language (FR-004) and insert "These findings are associational only" into `artifacts/reports/final_report.md`. **Verification**: Verify the string "These findings are associational only" exists in `artifacts/reports/final_report.md`. <!-- FAILED: unspecified -->
- [ ] T050 [US3] Generate final report artifact `artifacts/reports/final_report.md`. **Input**: T039a, T039b, T039c, T049. **Depends on**: T049, T039a, T039b, T039c. <!-- ATOMIZE: requested -->
- [~] T051 [US3] Validate report against `artifact.schema.yaml` (Single Source of Truth).
- [X] T059 [P] [US3] Implement `code/analyze.py` to handle edge case: if stratification warning is triggered (T022), generate a `stratification_limitation.md` snippet for the final report explaining the reduced family coverage.
- [X] T060 [US3] Implement `code/analyze.py` to explicitly calculate and log the collinearity condition condition number for the predictors to supplement VIF analysis (addressing Edge Case on collinearity). **Depends on**: T035a.
- [X] T063 [P] [US1] Add explicit validation in `code/ingest.py` to ensure Tg values are within a physically plausible range and flag outliers for review, addressing the "invalid Tg" edge case.
- [X] T064 [P] [US2] Refactor `code/train.py` to explicitly handle the case where LOFO results in a test set with 0 samples for a specific family, logging a `LOFO_EMPTY_SPLIT` warning and skipping that fold to prevent runtime errors.

**Checkpoint**: All user stories should now be independently functional (pending T024/T026 completion)

---

## Phase 6: Plan Alignment & Polish

**Purpose**: Resolve cross-document contradictions and final polish

- [~] T055 [P] Update `plan.md` to align with Spec: Replace 'Bonferroni' with 'Benjamini-Hochberg (FDR)' in FR-008 and 'Iterative VIF Remediation' with 'VIF Flagging (Diagnostic Only)' in FR-007. **Depends on**: FR-007, FR-008. **Verification**: Confirm `plan.md` 'Complexity Tracking' and 'FR/SC Coverage Map' match Spec FR-007 and FR-008.
- [ ] T061 [P] Update `README.md`: Add new CLI arguments for fallback DOI handling and resource limit overrides.
- [ ] T062 [P] Update `quickstart.md`: Add new DOI fallback logic and resource limit configuration examples.
- [ ] T053a [P] Code cleanup: Run `ruff check --select F401` and ensure zero errors. Fix any unused imports.
- [ ] T053b [P] Type hint verification: Run `mypy` and ensure zero errors. Add missing type hints.
- [ ] T054 [P] Performance optimization: Ensure vectorized operations in descriptors to stay within 7GB RAM. **Verification**: Check resource log from `resource_monitor.py` to confirm RAM usage < 7GB.
- [ ] T057 [P] Run quickstart.md validation to ensure end-to-end reproducibility
- [ ] T058 [P] Verify all tasks execute on CPU-only CI: Execute `bash scripts/run_ci.sh` on a GitHub Actions runner with `runs-on: ubuntu-latest`. **Verification**: Exit code 0.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Plan Alignment (Phase 6)**: Depends on all desired user stories being complete (to ensure tasks match spec)

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
- **Note on Plan Discrepancy (FDR vs Bonferroni)**: Spec FR-008 mandates FDR; Plan's 'Complexity Tracking' mentions Bonferroni; this is a Plan error. Task T055 updates the Plan to match the Spec.
- **Note on Plan Discrepancy (VIF)**: Spec FR-007 mandates 'flag only'. Plan's 'Complexity Tracking' mentions iterative dropping; this is a Plan error. Task T035 follows the Spec. Task T055 updates the Plan to match the Spec.
- **Note on Task IDs**: T040/T041 in Implementation section were renamed to T049/T050 to avoid collision with Test tasks. T040/T041 are Test tasks; T049/T050 are Implementation tasks.
- **Note on Task ID Collisions**: T055 was duplicated in Phase 6; the second instance (Quickstart validation) has been renamed to T057. T056 was duplicated; the second instance (CPU verification) has been renamed to T058. T055 has been merged into a single task to avoid duplication and ensure granular updates.
- **Note on T026**: Added to Phase 4 to explicitly generate `data/processed/descriptors.csv` required by Phase 5 tasks.
- **Note on Data Streaming**: If dataset size exceeds local disk limits during ingestion (FR-001), `code/ingest.py` must implement streaming logic to process chunks without loading the full dataset into RAM, adhering to the 7GB RAM constraint.
- **Note on Family Stratification**: If `code/train.py` detects < 50 records for a specific alloy family during LOFO split preparation, it must log a `STRATIFICATION_WARNING` and proceed with the available data, documenting the limitation in the final report (Edge Case handling).
- **Note on T052**: T052 is superseded by T061 and T062. T052 is marked [X] (superseded) to avoid confusion.
- **Note on T038**: T038 was merged into T036 to avoid redundancy. T036 now handles both calculation and saving of `stability_metrics.json`.
- **Note on US3 Testability**: US3 is NOT testable until T024 and T026 are complete.
- **Note on Sensitivity Analysis**: FR-006 is implemented in Phase 5 (T037a/T037b) to ensure model artifacts are available. T027 was removed to avoid duplication.
- **Note on Blocking Dependencies**: Phase 5 tasks (T033, T035, T036, T037) are explicitly blocked until T024 and T026 are completed. **US2 is not 'done' until T024a/b are complete.**
- **Note on Plan Correction**: T055 is the mechanism to correct the Plan's contradictions with the Spec. The Plan is updated by the execution of this task.
- **Note on T069**: Removed. DOI logging is now integrated into T012 verification.
- **Note on T039**: Removed. Redundant summary task. Dependencies now point to T039a-c or T049/T050.
- **Note on T060**: Removed [P] tag. Now depends on T035a.
- **Note on T037a**: Explicitly lists sweep values {3, 5, 7} as per FR-006.
- **Note on T036a**: Explicitly lists n_resamples=1000 as per SC-002.
- **Note on T024b**: Explicitly mandates calculation of `null_model_r2`.
- **Note on T012**: Verification now includes checking `source_doi` and cleaning logic.
- **Note on T021**: Verification now specifies key `weighted_mean_radius`.