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
- [X] T007 Create base data models (Molecule, DegradationRecord) in `code/models.py`
- [X] T008 Configure error handling and logging infrastructure for pipeline failures

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Complexity Metric Calculation (Priority: P1) 🎯 MVP

**Goal**: Retrieve FDA-approved structures, verify degradation data availability (Data Availability Gate), and compute molecular descriptors.

**Independent Test**: The pipeline can be run in isolation to produce a CSV file containing SMILES, calculated metrics, and degradation half-lives. The test verifies that the file exists, has no missing values in key columns, and that the calculated metrics match known reference values for a small subset of test molecules.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/ingest.py`: Fetch FDA-approved structures from HuggingFace (`Synthyra/FDA-Approved-Drugs`) and check for degradation columns. **Dependency**: No upstream tasks.
- [X] T013 [US1] Implement Data Availability Gate in `code/ingest.py`: If degradation data missing or N < 30, generate `data_insufficiency_report.md` and exit. **Dependency**: T012 (Fetch data).
- [X] T014 [US1] Implement `code/descriptors.py`: Calculate TPSA, Rotatable Bond Count, MW, Aromatic Ring Count, Wiener Index, Zagreb Index using RDKit. **Dependency**: T012 (Fetch data).
- [X] T015 [US1] Implement error handling in `code/descriptors.py`: Flag/exclude molecules with non-standard valence, log SMILES to `data/errors.log`. **Dependency**: T014 (Descriptors).
- [X] T016 [US1] Merge structural and degradation data in `code/ingest.py`, filter for valid SMILES and non-null degradation values. **Dependency**: T012 (Fetch), T014 (Descriptors).
- [X] T017 [US1] Save merged dataset to `data/processed/merged_drugs.csv` and generate checksums in `data/checksums.txt`. Use efficient data types to minimize memory usage if dataset grows. **Dependency**: T016 (Merge).

### Mandatory Verification for User Story 1 (FR-002 Compliance)

> **NOTE**: These tasks are MANDATORY to satisfy FR-002. They verify the correctness of the descriptor calculations implemented in T014.

- [X] T010a [US1] Unit test for TPSA in `tests/test_descriptors.py`. Function: `test_tpsa_aspirin`. **Assertion**: {{claim:c_47a304e7}} **Dependency**: T014.
- [X] T010b [US1] Unit test for Rotatable Bond Count in `tests/test_descriptors.py`. Function: `test_rotatable_bonds_aspirin`. **Assertion**: Calculated Rotatable Bond Count for Aspirin matches the reference value. **Dependency**: T014.
- [X] T010c [US1] Unit test for Molecular Weight in `tests/test_descriptors.py`. Function: `test_mw_aspirin`. **Assertion**: {{claim:c_c33f388c}} **Dependency**: T014.
- [X] T010d [US1] Unit test for Aromatic Ring Count in `tests/test_descriptors.py`. Function: `test_aromatic_rings_aspirin`. **Assertion**: Calculated Aromatic Ring Count for Aspirin matches reference value (1) exactly. **Dependency**: T014.
- [X] T010e [US1] Unit test for Wiener Index in `tests/test_descriptors.py`. Function: `test_wiener_index_aspirin`. **Assertion**: Calculated Wiener Index for Aspirin matches reference value (specific integer) within 1e-4. **Dependency**: T014.
- [X] T010f [US1] Unit test for Zagreb Index in `tests/test_descriptors.py`. Function: `test_zagreb_index_aspirin`. **Assertion**: Calculated Zagreb Index for Aspirin matches reference value (specific integer) within 1e-4. **Dependency**: T014.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlation Analysis and Regression Modeling (Priority: P2)

**Goal**: Standardize degradation units, stratify by conditions, perform correlation analysis, and fit regression models with cross-validation.

**Independent Test**: The analysis script can be run on the P1 output dataset to generate a correlation matrix and regression coefficients. The test verifies that the output includes p-values, R² scores, and that the models are trained using K-fold cross-validation.

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/standardize.py`: Convert rate constants (k) to half-lives (t1/2) and standardize time units to hours. **Skip Arrhenius normalization** as activation energy (Ea) is unavailable per plan.md. **Dependency**: T017 (Merged dataset).
- [X] T021 [US2] Implement `code/standardize.py`: Stratification logic. **First**, check the *full merged dataset* (from T017) for the presence of pH and Temp columns to **attempt covariate inclusion** as per FR-004. If present, log a note; if missing, log a warning that covariates will be skipped. **Then**, filter for "Standard" conditions (25°C, pH 7.4) to create the `standard_subset` for primary regression. Exclude non-standard records from the `standard_subset` but retain them in a separate `descriptive_table` for reporting. **Dependency**: T020 (Unit Conversion), T017 (Merged dataset).
- [X] T022 [US2] Implement `code/analysis.py`: Compute Pearson and Spearman correlation matrices on the `standard_subset`; identify pairs with |r| ≥ 0.5 and p < 0.05. **Dependency**: T021 (Stratified data).
- [X] T023 [US2] Implement Multiple Linear Regression (MLR) in `code/analysis.py` **operating strictly on the `standard_subset`** defined in T021. **Attempt to include pH/Temp as covariates**: If these columns exist in the full merged dataset (checked in T021), include them; otherwise, proceed with the standard subset only and log a warning. **Dependency**: T021 (Stratified data).
- [X] T024 [US2] Implement LASSO regression with **K=5** fold cross-validation in `code/analysis.py` **operating strictly on the `standard_subset`** to identify parsimonious features. Use **GridSearchCV** to select the optimal alpha parameter from a range (e.g., 0.01 to 1.0). **Dependency**: T021 (Stratified data).
- [X] T024a [US2] Unit test for LASSO K-Fold configuration in `tests/test_analysis.py`. Function: `test_lasso_kfold_config`. **Assertion**: Verify that the LASSO model is instantiated with `cv=5` and `param_grid` for alpha is defined. **Dependency**: T024.
- [X] T025 [US2] Implement residual diagnostics in `code/analysis.py`: Perform Shapiro-Wilk (normality) and Breusch-Pagan (homoscedasticity) tests on model residuals. **Dependency**: T023, T024.
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

- [X] T032 [US3] Implement `code/viz.py`: **IF** Data Availability Gate passed (N >= 30) **THEN** generate scatter plots with regression lines for top correlated features; **save to `data/outputs/scatter_tpsa_vs_half_life.png`**, etc. **ELSE** skip plotting and log "Skipped: Data Insufficient". **Dependency**: T017 (Merged dataset existence), T026 (Analysis results).
- [X] T033 [US3] Implement `code/viz.py`: **IF** Data Availability Gate passed (N >= 30) **THEN** generate residual diagnostic plots (histogram, QQ-plot, residuals vs fitted); **save to `data/outputs/residuals.png`**, `qq_plot.png`. **ELSE** skip plotting and log "Skipped: Data Insufficient". **Dependency**: T025 (Diagnostics), T017 (Merged dataset existence).
- [X] T034 [US3] Implement `code/report.py`: Generate `results_report.md` summarizing methodology, coefficients, and R² scores. **IF** Data Availability Gate failed (N < 30), generate `data_insufficiency_report.md` instead. **Dependency**: T026, T032, T033.
- [X] T035 [US3] Implement reproducibility check in `code/report.py`: Log RDKit/scikit-learn versions, dataset URLs, retrieval dates, and **SHA256 hash values of raw and processed files directly in the report**. **Dependency**: T034.
- [X] T035b [US3] Implement machine-readable reproducibility log in `code/report.py`: Generate `reproducibility_log.json` containing versions, URLs, and SHA256 hashes of all data files (raw and processed). **Dependency**: T034.
- [X] T036 [US3] **IF** Data Availability Gate passed (N >= 30) **THEN** save all plots to `data/outputs/` and final report to `results_report.md`; **verify** the existence of the required plot files (`scatter_tpsa_vs_half_life.png`, `residuals.png`, `qq_plot.png`) and the report file, ensuring each plot file has a non-zero size. **ELSE** verify `data_insufficiency_report.md` exists and **confirm T034 executed in this branch** to generate the report. **Dependency**: T032, T033, T034, T035.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T031 [US3] Integration test for report generation in `tests/test_pipeline.py`. Function: `test_report_generation_and_plots`. **Assertion**: Verify `results_report.md` contains `dataset_hash` field, code version, and all expected sections; verify `data/outputs/` contains at least 5 PNG files with non-zero size **IF** N >= 30. **Dependency**: T036.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `quickstart.md` and `README.md`
- [ ] T038 Code cleanup and refactoring (ensure no hardcoded paths)
- [ ] T041 [P] Execute full pipeline script and measure total execution time
- [ ] T042 [P] Validate pipeline execution time against a defined operational threshold
- [ ] T043 [P] Verify `requirements.txt` contains no GPU-specific libraries (e.g., `torch`, `tensorflow`) or LLM dependencies to ensure CPU-only compliance.

The research question remains: Does the pipeline meet operational latency requirements?
The method remains: Measure end-to-end execution time and compare against the threshold.
References: [Insert DOI/arXiv/author-year here] and log result

---

## Rejected Tasks (Audit Trail)

> The following tasks were considered but rejected based on project constraints and scope.

- [ ] T022a [Removed] Sensitivity Analysis: Rejected because the plan explicitly states "No synthetic data will be generated for hypothesis testing" and the scope is limited to correlation/regression on available data. Sensitivity analysis requires synthetic perturbations not supported by the current design.
- [ ] T039 [Removed] Chunked processing for datasets larger than 5GB: Rejected because the spec and plan do not define a 5GB threshold or a specific chunking requirement. The plan states "subset of FDA-approved drugs" and "process in-memory or via chunked pandas operations to fit the 7GB RAM limit" without a hard 5GB cutoff. This was scope creep.
- [ ] T040 [Removed] Additional unit tests for edge cases: Rejected as the core unit tests (T010a-T010f, T018, T019) sufficiently cover the mandatory requirements. Edge cases are handled by the error logging in T015 and the Data Availability Gate in T013.

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
- **Critical**: Ensure `code/analysis.py` includes a fallback to `scipy.stats` if `statsmodels` is unavailable or if specific tests (Breusch-Pagan) require it, ensuring the diagnostic step does not crash the pipeline.
- **Critical**: Ensure `code/report.py` includes a specific section in `results_report.md` explicitly stating the "Data Availability Gate" outcome (N=XX, Passed/Failed) as the first line of the results summary.
- **Critical**: Ensure T010a-T010f are executed to verify FR-002 compliance; they are mandatory.
- **Critical**: Ensure T021 and T023 implement the logic to *attempt* covariate inclusion before stratification.
- **Critical**: Ensure T035 logs SHA256 hash values directly in the report.
- **Critical**: Ensure T036 verifies T034 execution in both branches.
- **Critical**: Ensure T024 explicitly defines K=5 and GridSearchCV for alpha selection.
- **Critical**: Ensure T024a unit test verifies K=5 and GridSearchCV configuration.