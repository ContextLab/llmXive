# Tasks: Exploring the Correlation Between Molecular Complexity and Degradation Rates in Pharmaceuticals

**Input**: Design documents from `/specs/001-molecular-complexity-degradation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification. Note: Verification tasks for mandatory requirements (FR-002) are moved to Implementation and are NOT optional.

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

- [X] T001 Create project structure per implementation plan (projects/PROJ-071-exploring-the-correlation-between-molecu/)
- [X] T002 Initialize Python project with requirements.txt (rdkit, pandas, scikit-learn, numpy, matplotlib, seaborn, pyyaml, requests, datasets)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data directories: `data/raw/`, `data/processed/`, `data/output_schema.yaml`
- [X] T005 [P] Implement `code/__init__.py` and logging configuration
- [X] T006 [P] Create `tests/conftest.py` for shared fixtures and random seed management
- [X] T007 [P] Create base data models (Molecule, DegradationRecord) in `code/models.py`
- [X] T008 [P] Configure error handling and logging infrastructure for pipeline failures
- [X] T009 [P] **Schema Validation**: Validate `code/models.py` (T007) against `data/output_schema.yaml`. **Action**: If models do not match the schema, fail the task and block progression. **Dependency**: T004, T007.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Complexity Metric Calculation (Priority: P1) 🎯 MVP

**Goal**: Retrieve FDA-approved structures, verify degradation data availability (Data Availability Gate), and compute molecular descriptors.

**Independent Test**: The pipeline can be run in isolation to produce a CSV file containing SMILES, calculated metrics, and degradation half-lives. The test verifies that the file exists, has no missing values in key columns, and that the calculated metrics match known reference values for a small subset of test molecules.

### Implementation for User Story 1

- [X] T011 [US1] **Data Source Verification**: Run `code/ingest.py` in isolation to confirm that `Synthyra/FDA-Approved-Drugs` is accessible via `streaming=True` and that the dataset contains the expected degradation columns. **Action**: If the dataset is missing columns, update `code/ingest.py` to handle the specific schema of the actual dataset version found, or log a critical failure if no degradation data exists. **Dependency**: T004, T002.
- [X] T012 [US1] Implement `code/ingest.py`: Fetch FDA-approved structures AND degradation data from HuggingFace (`Synthyra/FDA-Approved-Drugs`) using `streaming=True` to handle large datasets without OOM. Implement explicit `try/except` block that catches `FileNotFoundError` or `DatasetNotFoundError` and raises a custom `DataFetchError` with a clear message, ensuring NO synthetic fallback occurs. **Dependency**: T011.
- [X] T014 [US1] Implement `code/descriptors.py`: Calculate TPSA, Rotatable Bond Count, MW, Aromatic Ring Count, Wiener Index, Zagreb Index using RDKit. **Dependency**: T012.

### Mandatory Verification for User Story 1 (FR-002 Compliance)
> **NOTE**: These tasks are MANDATORY to satisfy FR-002. They verify the correctness of the descriptor calculations implemented in T014.
> **Note**: These are Verification Tests to be run AFTER T014 implementation, grouped logically for independent shippability.

- [X] T010a [US1] Unit test for TPSA in `tests/test_descriptors.py`. Function: `test_tpsa_aspirin`. **Assertion**: {{claim:c_e650f63f}} **Dependency**: T014, T006.
- [X] T010b [US1] Unit test for Rotatable Bond Count in `tests/test_descriptors.py`. Function: `test_rotatable_bonds_aspirin`. **Assertion**: {{claim:c_d0a1bf34}} (as derived from RDKit's `CalcNumRotatableBonds`). **Dependency**: T014, T006.
- [X] T010c [US1] Unit test for Molecular Weight in `tests/test_descriptors.py`. Function: `test_mw_aspirin`. **Assertion**: {{claim:c_2c3c0dbd}} **Dependency**: T014, T006.
- [X] T010d [US1] Unit test for Aromatic Ring Count in `tests/test_descriptors.py`. Function: `test_aromatic_rings_aspirin`. **Assertion**: {{claim:c_8ef11a1c}} (consistent with RDKit's `CalcNumAromaticRings`). **Dependency**: T014, T006.
- [X] T010e [US1] Unit test for Wiener Index in `tests/test_descriptors.py`. Function: `test_wiener_index_aspirin`. **Assertion**: Calculated Wiener Index for Aspirin matches the value derived from RDKit's `CalcWienerIndex` implementation (verify against RDKit's internal calculation for the test molecule). **Dependency**: T014, T006.
- [X] T010f [US1] Unit test for Zagreb Index in `tests/test_descriptors.py`. Function: `test_zagreb_index_aspirin`. **Assertion**: Calculated Zagreb Index for Aspirin matches the value derived from RDKit's implementation (cite RDKit documentation or reference value). **Dependency**: T014, T006.

- [X] T015 [US1] Implement error handling in `code/descriptors.py`: Flag/exclude molecules with non-standard valence, log SMILES to `data/errors.log`. **Dependency**: T014.
- [X] T016a [US1] **Merge**: Merge structural and degradation data in `code/ingest.py` **without filtering** for valid SMILES or non-null degradation values yet. **Output**: `data/processed/raw_merge.csv`. **Dependency**: T012, T014.
- [X] T016b [US1] **Filter**: Filter `data/processed/raw_merge.csv` for valid SMILES and non-null degradation values. **Dependency**: T016a.
- [X] T013 [US1] Implement Data Availability Gate in `code/ingest.py`: If degradation data missing or N < 30, generate `data_insufficiency_report.md`, **log the gate status (N count, Pass/Fail) to `data/gate_status.json`**, and exit. **CRITICAL**: Logging MUST occur before exit. **Dependency**: T016b.
- [X] T017 [US1] Save merged dataset to `data/processed/merged_drugs.csv` and generate checksums in `data/checksums.txt`. Use efficient data types to minimize memory usage if dataset grows. **Dependency**: T016b.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlation Analysis and Regression Modeling (Priority: P2)

**Goal**: Standardize degradation units, stratify by conditions, perform correlation analysis, and fit regression models with cross-validation.

**Independent Test**: The analysis script can be run on the P1 output dataset to generate a correlation matrix and regression coefficients. The test verifies that the output includes p-values, R² scores, and that the models are trained using K-fold cross-validation.

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/standardize.py`: Convert rate constants (k) to half-lives (t1/2) and standardize time units to hours. **Skip Arrhenius normalization** as activation energy (Ea) is unavailable per plan.md. **Dependency**: T017.
- [X] T021 [US2] Implement `code/standardize.py`: Stratification logic. **First**, check the *full merged dataset* (from T016a) for the presence of pH and Temp columns. **Log** the presence/absence of these columns. **Then**, filter for "Standard" conditions (25°C, pH 7.4) to create the `standard_subset`. **Crucial**: Before including pH/Temp as covariates in the model, check if they exhibit variance in the dataset. If the subset has constant pH/Temp (e.g., all 7.4), **exclude** them from the regression to prevent singular matrix errors. **Explicitly check if `standard_subset` is empty (N=0)**; if empty, trigger the insufficiency logic immediately and log to `data/insufficiency_regression_report.md`. **Save `standard_subset` to `data/processed/standard_subset.csv`**. **Dependency**: T020, T016a.
- [X] T048 [US2] **Robustness Fix**: Refactor `code/analysis.py` to explicitly handle the case where the `standard_subset` has fewer than 3 samples (N < 3) after stratification. **Action**: If N < 3, log a "Data Insufficiency for Regression" warning to `analysis_results.json` and **generate `data/insufficiency_regression_report.md`** (distinct from the main gate report) and **skip** regression fitting to prevent `ValueError` in scikit-learn. **Dependency**: T021.
- [X] T022 [US2] Implement `code/analysis.py`: Compute Pearson and Spearman correlation matrices on the `standard_subset` (read from `data/processed/standard_subset.csv`); identify pairs with |r| ≥ 0.5 and p < 0.05. **Dependency**: T021.
- [X] T051 [US2] **Statistical Rigor Fix**: In `code/analysis.py` (T022), ensure that correlation coefficients are only calculated for pairs where both variables have non-zero variance. If variance is zero, log "Skipped: Zero Variance" and exclude from the matrix to prevent NaN results. **Dependency**: T022.
- [X] T023 [US2] Implement Multiple Linear Regression (MLR) in `code/analysis.py` **operating strictly on the `standard_subset`** (read from `data/processed/standard_subset.csv`). **Include pH/Temp as covariates ONLY IF** they exhibit variance in the subset (as per T021). **Explicit Logic**: If `variance(pH) > 0`, append pH to feature matrix; if `variance(Temp) > 0`, append Temp to feature matrix. Log a warning if these columns were present in the raw data but excluded due to lack of variance. **Dependency**: T021, T048.
- [X] T024 [US2] Implement LASSO regression with **dynamic K-fold** cross-validation in `code/analysis.py`. Determine K as a bounded function of n to ensure K is at most a constant fraction of n (e.g., `min(5, max(2, n//5))`). **Note**: Avoid `floor(n/2)` which may exceed n/2 on small datasets causing instability. Use **GridSearchCV** with `param_grid={'alpha': [0.01, 0.1, 1.0]}` to select the optimal alpha parameter. **Read `standard_subset` from `data/processed/standard_subset.csv`**. **This task fulfills FR-005 (Sensitivity Analysis via LASSO CV)**. **Critical Validation**: After selecting the best alpha, **explicitly check** if the resulting model meets pre-defined thresholds ($|r| \ge 0.5, p < 0.05, R^2 \ge 0.4$). If not, log a "Threshold Not Met" warning but proceed to report the actual results (do not post-hoc adjust). **Dependency**: T021, T048.
- [X] T024a [US2] Unit test for LASSO K-Fold configuration in `tests/test_analysis.py`. Function: `test_lasso_kfold_config`. **Assertion**: Verify that the LASSO model is instantiated with dynamic `cv` (min(5, max(2, n//5))) and `param_grid` for alpha is `[0.01, 0.1, 1.0]`. **Verify** that the model instance has a `cv_results_` attribute and that the final alpha matches the best score from CV. **Use a small, pinned subset of real data or a mock dataset** to ensure this test runs independently of the main pipeline's data availability. **Dependency**: T024.
- [X] T025 [US2] Implement residual diagnostics in `code/analysis.py`: Perform Shapiro-Wilk (normality) and Breusch-Pagan (homoscedasticity) tests on model residuals. **CRITICAL**: If `statsmodels` is unavailable, **implement a custom simplified Breusch-Pagan test using `numpy` and `scipy.stats`**: (1) Fit an auxiliary OLS regression of squared residuals on all independent variables; (2) Calculate the R² of this auxiliary regression; (3) Compute the LM statistic (n * R²) and compare against a chi-squared distribution with degrees of freedom equal to the number of predictors. **Do NOT** assume `scipy.stats` has a built-in Breusch-Pagan function. **Dependency**: T023, T024.
- [X] T025a [US2] Log Correlation Significance (SC-002/SC-003) in `code/analysis.py`: **Observe** p-values and log PASS/FAIL status (p < 0.05) to `analysis_results.json` under key `correlation_significance_pass`. **Do NOT raise exceptions**. **Dependency**: T022.
- [X] T025b [US2] Log Residual Diagnostics (SC-004) in `code/analysis.py`: **Observe** Shapiro-Wilk p > 0.05 and Breusch-Pagan p > 0.05. Log PASS/FAIL status to `analysis_results.json` under key `residual_diagnostics_pass`. **Do NOT raise exceptions**. **Dependency**: T025.
- [X] T025c [US2] Synthesize Correlation Conclusion in `code/analysis.py`: **Read** `analysis_results.json` (T025a, T025b) and **log** a definitive conclusion string (e.g., "Correlation exists: True/False" based on thresholds |r| ≥ 0.5, p < 0.05) to `analysis_results.json` under key `correlation_conclusion`. **Dependency**: T025a, T025b.
- [X] T026 [US2] Save analysis results (coefficients, p-values, R², conclusion) to `data/processed/analysis_results.json` and verify the file contains the R² key and passes JSON schema validation. **Dependency**: T025a, T025b, T025c.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [US2] Unit test for unit conversion logic in `tests/test_standardize.py`. Function: `test_k_to_half_life_conversion`. **Assertion**: `t1_2 = ln(2)/0.01` equals `69.31` hours within 0.01. **Dependency**: T020.
- [X] T019 [US2] Unit test for regression diagnostics in `tests/test_analysis.py`. Function: `test_shapiro_wilk_breusch_pagan`. **Assertion**: Known normal residual set returns p > 0.05 for Shapiro-Wilk; known heteroscedastic set returns p < 0.05 for Breusch-Pagan. **Dependency**: T025.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reproducibility Reporting (Priority: P3)

**Goal**: Generate diagnostic plots and a reproducible report documenting code, data versions, and results.

**Independent Test**: The script generates a set of PNG/SVG files and a summary report. The test verifies that the plots exist, show the expected regression lines and residual patterns, and that the report includes the exact dataset hashes and code version used.

### Implementation for User Story 3

- [X] T032 [US3] Implement `code/viz.py`: **IF** Data Availability Gate passed (N >= 30) **THEN** generate scatter plots with regression lines for top correlated features; **save to `data/outputs/scatter_tpsa_vs_half_life.png`**, etc. **ELSE** skip plotting and log "Skipped: Data Insufficient". **Dependency**: T017, T013, T026.
- [X] T033 [US3] Implement `code/viz.py`: **IF** Data Availability Gate passed (N >= 30) **THEN** generate residual diagnostic plots (histogram, QQ-plot, residuals vs fitted) **regardless of statistical pass/fail status**; **save to `data/outputs/residuals.png`**, `qq_plot.png`. **ELSE** skip plotting and log "Skipped: Data Insufficient". **Dependency**: T025, T017, T013.
- [X] T033a [US3] **Diagnostic Plot Generation**: Generate specific diagnostic plots for Shapiro-Wilk (Q-Q plot) and Breusch-Pagan (Residuals vs Fitted) **unconditionally**. **IF** Data Availability Gate passed, generate plots from the actual model residuals. **IF** Data Availability Gate failed, generate a "No Data Available" diagnostic plot or a placeholder indicating the gate failure, ensuring the report proves the check was attempted. **Dependency**: T025, T013.
- [X] T034 [US3] Implement `code/report.py`: Generate `results_report.md` summarizing methodology, coefficients, and R² scores. **IF** Data Availability Gate failed (N < 30), generate `data_insufficiency_report.md` instead. **Dependency**: T026, T032, T033, T033a.
- [X] T035 [US3] Implement reproducibility check in `code/report.py`: Log RDKit/scikit-learn versions, dataset URLs, retrieval dates, and **SHA256 hash values of raw and processed files directly in the report**. **Dependency**: T034.
- [X] T035b [US3] Implement machine-readable reproducibility log in `code/report.py`: Generate `reproducibility_log.json` containing versions, URLs, and SHA256 hashes of all data files (raw and processed). **Dependency**: T034.
- [X] T035c [US3] **MANDATORY VERIFICATION**: Implement a check in `code/report.py` to explicitly verify that the SHA256 hashes logged in `reproducibility_log.json` match the actual `sha256sum` of the `data/` files at runtime. If a mismatch is found, log a "Data Integrity Warning" noting the file may have been modified post-ingestion, rather than failing the build immediately. Log "PASS" or "FAIL" to `reproducibility_log.json`. **Dependency**: T035b.
- [X] T036 [US3] **IF** Data Availability Gate passed (N >= 30) **THEN** save all plots to `data/outputs/` and final report to `results_report.md`; **verify** the existence of the required plot files (`scatter_tpsa_vs_half_life.png`, `residuals.png`, `qq_plot.png`, `diagnostics.png`) and the report file, ensuring each plot file has a non-zero size. **ELSE** verify `data_insufficiency_report.md` exists and **confirm T034 executed in this branch** to generate the report. **Dependency**: T032, T033, T033a, T034, T035, T035c.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T031 [US3] Integration test for report generation in `tests/test_pipeline.py`. Function: `test_report_generation_and_plots`. **Assertion**: Verify `results_report.md` contains `dataset_hash` field, code version, and all expected sections; verify `data/outputs/` contains `scatter_tpsa_vs_half_life.png`, `residuals.png`, `qq_plot.png`, `diagnostics.png` with non-zero size **IF** N >= 30. **Dependency**: T036.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Documentation updates in `quickstart.md` and `README.md`
- [X] T038 Code cleanup and refactoring (ensure no hardcoded paths)
- [X] T041a [P] Create `code/run_pipeline.py`: A master script that imports and executes the full pipeline (US1 -> US2 -> US3) in sequence. **Output**: This script MUST write execution metrics to `data/output/pipeline_metrics.json` including `total_duration_seconds` and `status`. **Dependency**: All US tasks.
- [X] T041 [P] Execute full pipeline script (`code/run_pipeline.py`) and measure total execution time. **Output**: Verify `data/output/pipeline_metrics.json` exists and contains `total_duration_seconds`. **Dependency**: T041a.
- [X] T042 [P] Validate pipeline execution time against a defined operational threshold. **Threshold**: 21600 seconds (6 hours). **Action**: If `data/output/pipeline_metrics.json` is missing, malformed, or `total_duration_seconds` > 21600, **FAIL** the task and block `research_accepted` transition. **Dependency**: T041.
- [X] T043 [P] Verify `requirements.txt` contains no GPU-specific libraries (e.g., `torch`, `tensorflow`) or LLM dependencies to ensure CPU-only compliance.

The research question remains: Does the pipeline meet operational latency requirements?
The method remains: Measure end-to-end execution time and compare against the threshold.
References: [Insert DOI/arXiv/author-year here] and log result

---

## Phase 7: Revision & Robustness (Post-Analysis Fixes)

**Goal**: Address specific review concerns regarding data robustness, error handling, and reproducibility verification.

*Note: Critical robustness tasks T044 and T045 have been moved to Phase 3 (US1) to ensure they are available for the Data Availability Gate. T046 logic has been integrated into T025 (US2). T048 has been moved to Phase 4 to prevent regression crashes.*

- [X] T047 [US3] Enhance `code/report.py` to include a "Data Quality Summary" section that explicitly lists the number of excluded records due to invalid SMILES, missing degradation data, and non-standard conditions, citing the counts from `data/errors.log` and T021 logs. **Dependency**: T034.

- [X] T049 [US3] **Reproducibility Fix**: Update `code/report.py` to include a "Known Limitations" section in `results_report.md` that explicitly states: "No Arrhenius normalization performed due to missing Ea data" and "Covariates (pH/Temp) excluded if constant". **Dependency**: T034.

- [X] T050 [US1] **Data Integrity Fix**: Add a post-merge validation task in `code/ingest.py` (T016) that verifies the intersection of the structural dataset and degradation dataset results in a non-empty dataframe before proceeding to descriptor calculation. If the intersection is empty, trigger the Data Availability Gate (T013) immediately with a specific "No Intersection" error code and **log this specific error code to `data/gate_status.json`**. **Dependency**: T016b.

- [X] T052 [US3] **Artifact Verification Fix**: Add a final validation step in `code/report.py` (T036) that checks the file size of `analysis_results.json`. If the file is empty (0 bytes) or contains only default values (e.g., `{"correlation_conclusion": "Skipped"}`), the task must **FAIL** and prevent the `research_accepted` transition unless the Data Availability Gate explicitly failed. **Dependency**: T036.

---

## Phase 8: Final Integration & Execution Verification

**Goal**: Ensure the entire pipeline runs end-to-end without manual intervention and produces all required artifacts.

- [ ] T053 [REMOVED] **Data Source Verification**: Moved to Phase 3 as T011. <!-- ATOMIZE: requested --> <!-- ATOMIZE: requested -->
- [ ] T054 [REMOVED] **Regression Stability Test**: Removed due to synthetic data constraint violation. <!-- ATOMIZE: requested -->
- [X] T054a [P] [All] **Real Data Robustness Test**: Execute `code/analysis.py` on a **small, pinned, reproducible sample of the REAL dataset** (e.g., first 50 rows via `itertools.islice`) to verify that the LASSO CV and MLR models do not crash on edge cases (e.g., perfect multicollinearity, near-zero variance). **Explicitly exclude** this data from final research results. **Dependency**: T024, T023.
- [ ] T055 [P] [US3] **Full Pipeline Smoke Test**: Execute `code/run_pipeline.py` end-to-end. **Success Criteria**: `data/processed/merged_drugs.csv`, `data/processed/analysis_results.json`, `results_report.md`, and `reproducibility_log.json` are all created and non-empty. **Dependency**: T041a, T017, T026, T034.
- [X] T055a [P] [All] **Fresh Environment Smoke Test**: Simulate a fresh environment by clearing all caches and temporary files, then re-running `code/run_pipeline.py`. **Success Criteria**: Pipeline completes successfully and produces identical hashes to T055. **Dependency**: T055.
- [ ] T056 [REMOVED] **Reproducibility Audit**: Removed due to manual verification constraint violation. <!-- ATOMIZE: requested -->
- [ ] T056a [P] [All] **Automated Reproducibility Audit**: Execute a script that programmatically compares the SHA256 hashes in `reproducibility_log.json` against the actual `data/` files. **Action**: If hashes mismatch, **FAIL** the task and block `research_accepted` transition. **Dependency**: T035c, T055.
- [ ] T057 [P] [All] **Final Gate Check**: Confirm that `data/gate_status.json` accurately reflects the outcome of the Data Availability Gate (Pass/Fail) and that the pipeline logic correctly branched to either `results_report.md` or `data_insufficiency_report.md`. **Dependency**: T013, T055.

---

## Rejected Tasks (Audit Trail)

> The following tasks were considered but rejected based on project constraints and scope.

- [ ] T022a [REMOVED] Sensitivity Analysis: Rejected because LASSO regression with K-fold cross-validation (FR-005) IS the required sensitivity/stability analysis. No separate sensitivity task is needed. **Note**: Task T024 explicitly fulfills FR-005 requirements.
- [ ] T046 [Removed] Separate `scipy` fallback task: Rejected because the logic has been integrated directly into T025 (Residual Diagnostics) to ensure the fix is in place before the failure point.
- [ ] T053 [MOVED] Data Source Verification: Moved to Phase 3 as T011 to ensure schema verification occurs before ingestion.
- [ ] T054 [REMOVED] Regression Stability Test: Removed due to synthetic data constraint violation. Replaced by T054a using real data.
- [ ] T056 [REMOVED] Reproducibility Audit: Removed due to manual verification constraint violation. Replaced by T056a.

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
- **User Story 2 (P2)**: Depends on T017 (merged dataset) - Must wait for US1 completion
- **User Story 3 (P3)**: Depends on T026 (analysis results) - Must wait for US2 completion

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation (scaffolding) or run AFTER implementation (verification)
- Models before services
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel (if independent)
- Models within a story marked [P] can run in parallel (if independent)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement code/descriptors.py: Calculate TPSA..."
Task: "Implement error handling in code/descriptors.py..."

# Launch tests AFTER implementation:
Task: "Unit test for RDKit descriptor calculation (test_tpsa_wiener)..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify Data Availability Gate)
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
 - Developer A: User Story 1 (Ingestion & Descriptors)
 - Developer B: User Story 2 (Analysis) - *Must wait for T017*
 - Developer C: User Story 3 (Viz & Report) - *Must wait for T026*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing (scaffolding) or pass after implementation (verification)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: Ensure `code/ingest.py` strictly enforces the Data Availability Gate (N < 30) as per plan.md.
- **Critical**: Ensure `code/standardize.py` explicitly skips Arrhenius normalization (T020) as Ea is unavailable, satisfying plan.md constraints.
- **Critical**: Ensure `code/analysis.py` performs regression ONLY on the `standard_subset` (T023) and logs p-value status without crashing (T025a/T025b).
- **Critical**: Ensure all visualization tasks (T032/T033/T036) include a conditional branch to skip generation if the Data Availability Gate fails.
- **Critical**: Ensure `code/ingest.py` uses `datasets.load_dataset("Synthyra/FDA-Approved-Drugs", streaming=True)` or explicit `hf_hub_download` to handle potential dataset size without OOM, and raises an explicit error if the fetch fails (no synthetic fallback).
- **Critical**: Ensure `code/analysis.py` includes a custom implementation of the Breusch-Pagan test using numpy/scipy if statsmodels is unavailable, as described in T025.
- **Critical**: Ensure `code/report.py` includes a specific section in `results_report.md` explicitly stating the "Data Availability Gate" outcome (N=XX, Passed/Failed) as the first line of the results summary.
- **Critical**: Ensure T010a-T010f are executed to verify FR-002 compliance; they are mandatory.
- **Critical**: Ensure T021 and T023 implement the logic to **exclude** covariates from the primary model if they are constant (singular matrix), not attempt inclusion.
- **Critical**: Ensure T035 logs SHA256 hash values directly in the report.
- **Critical**: Ensure T036 verifies T034 execution in both branches.
- **Critical**: Ensure T024 explicitly defines dynamic K calculation (e.g., `min(5, max(2, n//5))`) and GridSearchCV with `param_grid={'alpha': [0.01, 0.1, 1.0]}`.
- **Critical**: Ensure T024a unit test verifies dynamic K and GridSearchCV configuration.
- **Critical**: Ensure T013 logs the PASS status of the Data Availability Gate to `data/gate_status.json` before any exit.
- **Critical**: Ensure T035c verifies hash consistency between logs and actual files, handling post-ingestion modifications gracefully.
- **Critical**: Ensure T041/T042 fail the build if duration > 6 hours.
- **Critical**: Ensure T041a explicitly writes `pipeline_metrics.json` as a side effect of execution.
- **Critical**: Ensure T047 adds a "Data Quality Summary" section to the report.
- **Critical**: Ensure T048 handles N < 3 cases in regression to prevent `ValueError` and generates `data/insufficiency_regression_report.md`.
- **Critical**: Ensure T049 documents the specific limitations regarding Arrhenius and covariates.
- **Critical**: Ensure T050 triggers the gate immediately if the structural/degradation intersection is empty and logs the specific error code.
- **Critical**: Ensure T051 handles zero-variance columns in correlation to prevent NaN.
- **Critical**: Ensure T052 fails the build if analysis results are empty/skipped without a valid Data Availability Gate failure.
- **Critical**: Ensure T054a uses a real data subset for stability testing, not synthetic data.
- **Critical**: Ensure T055a validates the full end-to-end execution path in a fresh environment.
- **Critical**: Ensure T056a performs an automated audit of the reproducibility log.
- **Critical**: Ensure T057 confirms the correct branching logic based on the Data Availability Gate.
- **Critical**: Ensure T009 validates models against `output_schema.yaml`.
- **Critical**: Ensure T011 verifies the dataset schema before ingestion.
- **Critical**: Ensure T033a generates diagnostic plots regardless of gate status.
- **Critical**: Ensure T023 explicitly includes pH/Temp if variance > 0.
- **Critical**: Ensure T024 validates the selected model against pre-defined thresholds.
- **Critical**: Ensure T024a uses a mock or small real data subset for testing.