# Tasks: Exploring the Correlation Between Molecular Complexity and Degradation Rates in Pharmaceuticals

**Input**: Design documents from `/specs/001-molecular-complexity-degradation/`
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

- [X] T001 Create project structure per implementation plan (projects/PROJ-071-exploring-the-correlation-between-molecu/)
- [X] T002 Initialize Python project with requirements.txt (rdkit, pandas, scikit-learn, numpy, matplotlib, seaborn, pyyaml, requests, datasets)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data directories: `data/raw/`, `data/processed/`, `data/output_schema.yaml`
- [X] T005 [P] Implement `code/__init__.py` and logging configuration
- [X] T006 [P] Create `tests/conftest.py` for shared fixtures and random seed management
- [X] T007 Create base data models (Molecule, DegradationRecord) in `code/models.py`
- [ ] T008 Configure error handling and logging infrastructure for pipeline failures

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Complexity Metric Calculation (Priority: P1) 🎯 MVP

**Goal**: Retrieve FDA-approved structures, verify degradation data availability (Data Availability Gate), and compute molecular descriptors.

**Independent Test**: The pipeline can be run in isolation to produce a CSV file containing SMILES, calculated metrics, and degradation half-lives. The test verifies that the file exists, has no missing values in key columns, and that the calculated metrics match known reference values for a small subset of test molecules.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/ingest.py`: Fetch FDA-approved structures from HuggingFace (`Synthyra/FDA-Approved-Drugs`) and check for degradation columns. **Dependency**: No upstream tasks.
- [ ] T013 [US1] Implement Data Availability Gate in `code/ingest.py`: If degradation data missing or N < 30, generate `data_insufficiency_report.md` and exit. **Dependency**: T012 (Fetch data).
- [X] T014 [US1] Implement `code/descriptors.py`: Calculate TPSA, Rotatable Bond Count, MW, Aromatic Ring Count, Wiener Index, Zagreb Index using RDKit. **Dependency**: T012 (Fetch data).
- [ ] T015 [US1] Implement error handling in `code/descriptors.py`: Flag/exclude molecules with non-standard valence, log SMILES to `data/errors.log`. **Dependency**: T014 (Descriptors).
- [~] T016 [US1] Merge structural and degradation data in `code/ingest.py`, filter for valid SMILES and non-null degradation values. **Dependency**: T012 (Fetch), T014 (Descriptors).
- [~] T017 [US1] Save merged dataset to `data/processed/merged_drugs.csv` and generate checksums in `data/checksums.txt`. **Dependency**: T016 (Merge).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER implementation, ensure they PASS**

- [~] T010 [US1] Unit test for RDKit descriptor calculation in `tests/test_descriptors.py`. Function: `test_tpsa_wiener_zagreb_aspirin`. **Assertion**: `{{claim:c_5b0172db}}` and `CalcWienerIndex` wrapper output matches reference value within 1e-4. **Dependency**: T014.
- [~] T011 [US1] Integration test for data ingestion gate in `tests/test_pipeline.py`. Function: `test_insufficient_data_gate`. **Assertion**: Mock dataset with N=29; verify `data_insufficiency_report.md` is generated, contains "N < 30" message, and `assert exit_code == 0`. **Dependency**: T013.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlation Analysis and Regression Modeling (Priority: P2)

**Goal**: Standardize degradation units, stratify by conditions, perform correlation analysis, and fit regression models with cross-validation.

**Independent Test**: The analysis script can be run on the P1 output dataset to generate a correlation matrix and regression coefficients. The test verifies that the output includes p-values, R² scores, and that the models are trained using K-fold cross-validation.

### Implementation for User Story 2

- [~] T020 [US2] Implement `code/standardize.py`: Convert rate constants (k) to half-lives (t1/2) and standardize time units to hours. **Dependency**: T017 (Merged dataset).
- [~] T020b [US2] Implement `code/standardize.py`: Implement Arrhenius normalization logic (t1/2_std = t1/2_meas * exp(Ea/R * (1/T_meas - 1/T_std))). Check for Ea availability; if Ea is missing, flag record as 'unnormalized'. **Dependency**: T020 (Unit Conversion).
- [~] T021a [US2] Implement `code/standardize.py`: Data Coverage Check. Calculate the percentage of records in the FULL dataset (pre-stratification) that have pH and temperature data. Log the decision (include/exclude covariates) based on the ≥50% threshold. **Dependency**: T020 (Unit Conversion).
- [~] T021 [US2] Implement `code/standardize.py`: Stratification logic. Filter for "Standard" conditions (25°C, pH 7.4) OR records normalized by T020b to create the `standard_subset` for primary regression. Exclude 'Unnormalized' records (missing Ea) from the `standard_subset` but retain them in a separate `descriptive_table`. **Dependency**: T020b (Normalization), T021a (Coverage Check).
- [~] T022 [US2] Implement `code/analysis.py`: Compute Pearson and Spearman correlation matrices on the `standard_subset`; identify pairs with |r| ≥ 0.5 and p < 0.05. **Dependency**: T021 (Stratified data).
- [~] T022a [US2] Implement sensitivity analysis in `code/analysis.py`: Sweep correlation thresholds over a range of moderate to high values and save the count of significant correlations for each threshold to `data/processed/sensitivity_analysis.json`. **Dependency**: T021 (Stratified data).
- [~] T023 [US2] Implement Multiple Linear Regression (MLR) in `code/analysis.py` **operating strictly on the `standard_subset`** defined in T021. **Dependency**: T021 (Stratified data).
- [~] T023b [US2] Implement conditional covariate modeling in `code/analysis.py`: Use the decision logged in T021a to determine if pH/temp should be included as covariates. If T021a logged "include", add covariates; if "exclude", use baseline model. **Model must run only on `standard_subset`**. **Dependency**: T021a (Coverage Check), T023 (MLR).
- [~] T024 [US2] Implement LASSO regression with k-fold cross-validation in `code/analysis.py` **operating strictly on the `standard_subset`** to identify parsimonious features. **Dependency**: T023 (MLR) and T021.
- [~] T025 [US2] Implement residual diagnostics in `code/analysis.py`: Perform Shapiro-Wilk (normality) and Breusch-Pagan (homoscedasticity) tests on model residuals. **Dependency**: T023, T024.
- [~] T025a [US2] Verify Correlation Significance (SC-002/SC-003) in `code/analysis.py`: Assert that output p-values meet thresholds (p < 0.05). Log PASS/FAIL status to `analysis_results.json` under key `correlation_significance_pass`. **Dependency**: T022.
- [~] T025b [US2] Verify Residual Diagnostics (SC-004) in `code/analysis.py`: Assert that Shapiro-Wilk p > 0.05 and Breusch-Pagan p > 0.05. Log PASS/FAIL status to `analysis_results.json` under key `residual_diagnostics_pass`. **Dependency**: T025.
- [~] T026 [US2] Save analysis results (coefficients, p-values, R², sensitivity analysis) to `data/processed/analysis_results.json` and verify the file contains the R² key and passes JSON schema validation. **Dependency**: T025a, T025b, T022a.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T018 [US2] Unit test for unit conversion logic in `tests/test_standardize.py`. Function: `test_k_to_half_life_conversion`. **Assertion**: `t1_2 = ln(2)/0.01` equals `69.31` hours within 0.01. **Dependency**: T020.
- [~] T019 [US2] Unit test for regression diagnostics in `tests/test_analysis.py`. Function: `test_shapiro_wilk_breusch_pagan`. **Assertion**: Known normal residual set returns p > 0.05 for Shapiro-Wilk; known heteroscedastic set returns p < 0.05 for Breusch-Pagan. **Dependency**: T025.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reproducibility Reporting (Priority: P3)

**Goal**: Generate diagnostic plots and a reproducible report documenting code, data versions, and results.

**Independent Test**: The script generates a set of PNG/SVG files and a summary report. The test verifies that the plots exist, show the expected regression lines and residual patterns, and that the report includes the exact dataset hashes and code version used.

### Implementation for User Story 3

- [~] T032 [US3] Implement `code/viz.py`: Generate scatter plots with regression lines for top correlated features; **save to `data/outputs/scatter_tpsa_vs_half_life.png`**, etc. **Dependency**: T026 (Analysis results).
- [ ] T033 [US3] Implement `code/viz.py`: Generate residual diagnostic plots (histogram, QQ-plot, residuals vs fitted); **save to `data/outputs/residuals.png`**, `qq_plot.png`. **Dependency**: T025 (Diagnostics).
- [ ] T034 [US3] Implement `code/report.py`: Generate `results_report.md` summarizing methodology, coefficients, and R² scores. **Dependency**: T026, T032, T033.
- [ ] T035 [US3] Implement reproducibility check in `code/report.py`: Log RDKit/scikit-learn versions, dataset URLs, retrieval dates, and file hashes. **Dependency**: T034.
- [ ] T036 [US3] Save all plots to `data/outputs/` and final report to `results_report.md`; **verify the existence of the required plot files** (`scatter_tpsa_vs_half_life.png`, `residuals.png`, `qq_plot.png`) and the report file, ensuring each plot file has a non-zero size. **Dependency**: T032, T033, T034, T035.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [US3] Integration test for report generation in `tests/test_pipeline.py`. Function: `test_report_generation_and_plots`. **Assertion**: Verify `results_report.md` contains `dataset_hash` field, code version, and all expected sections; verify `data/outputs/` contains at least 5 PNG files with non-zero size. **Dependency**: T036.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Documentation updates in `quickstart.md` and `README.md`
- [ ] T038 Code cleanup and refactoring (ensure no hardcoded paths)
- [ ] T039 Performance optimization: Ensure chunked processing if dataset > 5GB
- [ ] T040 [P] Additional unit tests for edge cases (empty datasets, invalid SMILES) in `tests/unit/`
- [ ] T041 Run `quickstart.md` validation to ensure full pipeline executes within 6 hours on free-tier runner

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
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
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
Task: "Unit test for RDKit descriptor calculation (test_tpsa_wiener_zagreb)..."
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
- **Critical**: Ensure `code/standardize.py` explicitly implements Arrhenius normalization (T020b) if Ea is available, and excludes records only if Ea is missing, satisfying FR-009.
- **Critical**: Ensure `code/analysis.py` includes covariate modeling if T021a logs "include" (FR-004) and performs sensitivity sweeps (T022a).
- **Critical**: Ensure all regression tasks (T023, T023b, T024) operate strictly on the `standard_subset` defined in T021.