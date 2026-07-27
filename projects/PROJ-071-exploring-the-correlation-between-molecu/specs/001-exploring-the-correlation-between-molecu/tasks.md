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
- [X] T002 Initialize Python project with requirements.txt (rdkit, pandas, scikit-learn, numpy, matplotlib, seaborn, pyyaml, requests, datasets, statsmodels, scipy)
- [X] T003 [P] Configure linting (ruff) and formatting (black)

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

**Independent Test**: The pipeline can be run in isolation to produce a CSV file containing SMILES, calculated metrics, and degradation half-lives (if available). The test verifies that the file exists, has no missing values in key columns, and that the calculated metrics match known reference values for a small subset of test molecules.

### Implementation for User Story 1

- [X] T011 [US1] **Data Source Verification**: Run `code/ingest.py` in isolation to confirm that `Synthyra/FDA-Approved-Drugs` is accessible via `streaming=True` and contains structure columns. **Action**: If the dataset is missing structure columns, fail. **Note**: This dataset contains ONLY structures. **Dependency**: T004, T002.
- [X] T012 [US1] Implement `code/ingest.py`: Fetch FDA-approved structures from HuggingFace (`Synthyra/FDA-Approved-Drugs`) using `streaming=True`. **CRITICAL**: This dataset contains ONLY structures. **DO NOT** attempt to fetch degradation data from this source. **Action**: If the fetch fails, raise `DataFetchError` immediately. **NO synthetic fallback**. **Dependency**: T011.
- [ ] T016a [US1] **Merge Structural Data**: Merge fetched data into `data/processed/structural_subset.csv`. **CRITICAL**: This task MUST produce `structural_subset.csv` regardless of whether degradation data is found. If degradation columns are missing (to be checked in T012a), merge only the structural columns and log "Source Not Found" to `data/gate_status.json`. **Output**: `data/processed/structural_subset.csv`. **Dependency**: T012.
- [ ] T016b [US1] Filter `data/processed/structural_subset.csv` for valid SMILES. **Dependency**: T016a.
- [X] T012a [US1] **Dynamic Degradation Check**: Inspect `data/processed/structural_subset.csv` (from T016a) for columns like 'half_life', 'degradation_rate', or 't12'. **Action**: If missing, set `data/gate_status.json` with `status: "FAIL"`, `reason: "No verified degradation source found"`, `N: 0`. If present, set `status: "PASS"`. **Dependency**: T016a.
- [X] T016c [US1] Explicitly count the number of rows in the filtered dataset (from T016b). **Action**: If count < 30 OR if `data/gate_status.json` indicates failure, trigger the Data Availability Gate (T013) immediately with the specific count and log to `data/gate_status.json`. **Dependency**: T016b, T012a.
- [X] T013 [US1] Implement Data Availability Gate in `code/ingest.py`: If degradation data missing, N=0, or N < 30, generate `data_insufficiency_report.md`, log the gate status (N count, Pass/Fail) to `data/gate_status.json`, and raise `DataInsufficiencyError` to halt analysis but proceed to reporting. **CRITICAL**: Logging MUST occur before exit. **Dependency**: T016c.
- [X] T013b [US1] Implement `code/run_pipeline.py` to catch `DataInsufficiencyError` raised by T013. **Action**: If caught, skip US2/US3 tasks, ensure `data_insufficiency_report.md` is the final artifact, and exit with code 0 (graceful completion of insufficiency path). **Dependency**: T013.
- [X] T014 [US1] Implement `code/descriptors.py`: Calculate TPSA, Rotatable Bond Count, MW, Aromatic Ring Count, Wiener Index, Zagreb Index using RDKit. **Dependency**: T016b.
- [X] T010 [US1] **Unit Tests for Descriptors**: Implement unit tests in `tests/test_descriptors.py` for all FR-002 metrics (TPSA, Rotatable Bond Count, MW, Aromatic Ring Count, Wiener Index, Zagreb Index) using Aspirin as the primary reference (SMILES: `CC(=O)Oc1ccccc1C(=O)O`). **Assertion**: Verify calculated values match known reference values within RDKit precision. **RDKit Version**: Must match pinned version in `requirements.txt`. **(Note: T010 uses hardcoded reference SMILES, does NOT depend on T014 or T016b)**. **Dependency**: T014, T006.
- [ ] T010g [US1] **Dataset Metric Verification**: Implement a test in `tests/test_descriptors.py` that calculates metrics for a diverse random sample (N=50) of the *fetched FDA-approved drugs* (from `data/processed/structural_subset.csv` - structures only). **Action**: Verify that calculated metrics fall within expected scientific ranges (e.g., MW > 0, TPSA >= 0) and that RDKit handles diverse structures (macrocycles, charged species) without crashing. **Verify** that the RDKit version used in the test matches the pinned version in `requirements.txt`. **Action**: If `data/gate_status.json` indicates failure (T013), skip this task and log "Skipped: No Degradation Data". **Dependency**: T014, T016d, T013.
- [ ] T015 [US1] Implement error handling in `code/descriptors.py`: Flag/exclude molecules with non-standard valence. **Action**: Wrap RDKit calls in a try/except block. If an exception occurs, log the SMILES to `data/errors.log`, exclude the record from the dataset, and continue. **Dependency**: T014.
- [X] T016d [US1] Save structural dataset to `data/processed/structural_subset.csv` (finalized) and generate checksums in `data/checksums.txt`. Use efficient data types to minimize memory usage if dataset grows. **Dependency**: T016b, T016c.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlation Analysis and Regression Modeling (Priority: P2)

**Goal**: Standardize degradation units, stratify by conditions, perform correlation analysis, and fit regression models with cross-validation.

**Independent Test**: The analysis script can be run on the P1 output dataset to generate a correlation matrix and regression coefficients. The test verifies that the output includes p-values, R² scores, and that the models are trained using K-fold cross-validation.

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/standardize.py`: Convert rate constants (k) to half-lives (t1/2) and standardize time units to hours. **Skip Arrhenius normalization** as Ea is unavailable per plan.md. **Action**: First, check `data/gate_status.json`. If status is "FAIL", skip calculation and log "Skipped: Data Insufficient". **Dependency**: T016d.
- [ ] T021 [US2] Implement `code/standardize.py`: Stratification logic. Filter for "Standard" conditions (25°C, pH 7.4) to create the `standard_subset`. **Action**: If `data/gate_status.json` indicates "FAIL", skip this task. If "PASS", proceed. **DO NOT** raise ValueError for N < 3; the upstream gate (T013) guarantees N >= 30. Save the resultant file to `data/processed/standard_subset.csv`. **Dependency**: T020, T013.
- [ ] T021b [US2] **Data Characteristics Table**: Generate a "Data Characteristics" table in `code/standardize.py` that lists the count of records excluded from the primary model due to non-standard conditions. **Output**: Save to `data/processed/data_characteristics.csv`. **Dependency**: T021.
- [ ] T021c [US2] **Audit Trail Merge**: Implement `code/standardize.py` to merge `standard_subset` and `data_characteristics.csv` (excluded records) into a single `data/processed/full_processed_state.csv` to preserve the "Single Source of Truth" for the original dataset state. **Action**: Ensure this file contains a flag indicating inclusion/exclusion status for every record. **Dependency**: T021, T021b.
- [ ] T022a [US2] **Sensitivity Analysis / Arrhenius Exclusion Log**: Implement a task in `code/standardize.py` to explicitly document the decision to exclude Arrhenius normalization due to missing Ea data. **Output**: Write a log file `data/processed/analysis_log.txt` with the specific reason and reference to the Plan. **Dependency**: T021.
- [X] T023 [US2] Implement Multiple Linear Regression (MLR) in `code/analysis.py` **operating strictly on the `standard_subset`** (read from `data/processed/standard_subset.csv`). **Dependency**: T021.
- [X] T024 [US2] Implement LASSO regression with **dynamic K-fold** cross-validation in `code/analysis.py`. Determine K as the minimum of a predefined upper bound and `n-1`. **Constraint**: Verify `K <= n-1`. If `K >= n`, set `K = n-1`. Use **GridSearchCV** with `param_grid={'alpha': [0.01, 0.1, 1.0]}` to select the optimal alpha parameter. **Read `standard_subset` from `data/processed/standard_subset.csv`**. **Note**: This task includes the sensitivity analysis functionality previously associated with T022a. **Dependency**: T021.
- [X] T025 [US2] Implement residual diagnostics in `code/analysis.py`: Perform Shapiro-Wilk (normality) and Breusch-Pagan (homoscedasticity) tests on model residuals. **Requirement**: `statsmodels` and `scipy` are explicitly required. **Dependency**: T024.
- [ ] T026 [US2] Save analysis results (coefficients, p-values, R², conclusion) to `data/processed/analysis_results.json` and verify the file contains the R² key and passes JSON schema validation. **Action**: This task explicitly consumes the output of T025 to create the final `analysis_results.json`. **Dependency**: T025.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [US2] Unit test for unit conversion logic in `tests/test_standardize.py`. Function: `test_k_to_half_life_conversion`. **Assertion**: `t1_2 = ln(2)/0.01` equals `69.31` hours within 0.01. **Dependency**: T020.
- [X] T019 [US2] Unit test for regression diagnostics in `tests/test_analysis.py`. Function: `test_shapiro_wilk_breusch_pagan`. **Assertion**: Known normal residual set returns p > 0.05 for Shapiro-Wilk; known heteroscedastic set returns p < 0.05 for Breusch-Pagan. **Dependency**: T025.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate diagnostic plots and a reproducible report documenting code, data versions, and results.

**Independent Test**: The script generates a set of PNG/SVG files and a summary report. The test verifies that the plots exist, show the expected regression lines and residual patterns, and that the report includes the exact dataset hashes and code version used.

### Implementation for User Story 3

- [~] T032 [US3] Implement `code/viz.py`: **IF** Data Availability Gate passed (N >= 30) **THEN** generate scatter plots with regression lines for top correlated features; **save to `data/outputs/scatter_tpsa_vs_half_life.png`**, etc. **ELSE** skip plotting and log "Skipped: Data Insufficient". **Dependency**: T016d, T013, T026.
- [~] T033 [US3] Implement `code/viz.py`: **IF** Data Availability Gate passed (N >= 30) **THEN** generate residual diagnostic plots (histogram, QQ-plot, residuals vs fitted) **regardless of statistical pass/fail status**; **save to `data/outputs/residuals.png`**, `qq_plot.png`. **ELSE** skip plotting and log "Skipped: Data Insufficient". **Dependency**: T025, T016d, T013.
- [X] T034 [US3] Implement `code/report.py`: Generate `results_report.md` summarizing methodology, coefficients, and R² scores. **IF** Data Availability Gate failed (N < 30), generate `data_insufficiency_report.md` instead. **Dependency**: T026, T032, T033.
- [ ] T035 [US3] Implement reproducibility check in `code/report.py`: Log RDKit/scikit-learn versions, dataset URLs, retrieval dates, and **SHA256 hash values of raw and processed files directly in the report**. **Dependency**: T034.
- [ ] T035b [US3] Implement machine-readable reproducibility log in `code/report.py`: Generate `reproducibility_log.json` containing versions, URLs, and SHA256 hashes of all data files (raw and processed). **Dependency**: T034.
- [ ] T035c [US3] **Artifact Verification Fix**: Implement a final validation step in `code/report.py` to check the file size of `analysis_results.json`. If the file is empty (0 bytes) or contains only default values, the task must **FAIL** and prevent the `research_accepted` transition unless the Data Availability Gate explicitly failed. **Dependency**: T034.
- [ ] T036 [US3] Save all plots to `data/outputs/` and final report to `results_report.md`; verify the existence of the required plot files (`scatter_tpsa_vs_half_life.png`, `residuals.png`, `qq_plot.png`) and the report file, ensuring each plot file has a non-zero size **IF** gate passed. **Dependency**: T032, T033, T034, T035.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [US3] Integration test for report generation in `tests/test_pipeline.py`. Function: `test_report_generation_and_plots`. **Assertion**: Verify `results_report.md` contains `dataset_hash` field, code version, and all expected sections; verify `data/outputs/` contains `scatter_tpsa_vs_half_life.png`, `residuals.png`, `qq_plot.png` with non-zero size **IF** N >= 30. **Dependency**: T036.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Documentation updates in `quickstart.md` and `README.md`
- [X] T038 Code cleanup and refactoring (ensure no hardcoded paths)
- [ ] T041a [P] Create `code/run_pipeline.py`: A master script that imports and executes the full pipeline (US1 -> US2 -> US3) in sequence. **Output**: This script MUST write execution metrics to `data/output/pipeline_metrics.json` including `total_duration_seconds` and `status`. **Action**: Must catch `DataInsufficiencyError` and handle graceful exit. **Dependency**: All US tasks.
- [ ] T041 [P] Execute full pipeline script (`code/run_pipeline.py`) and measure total execution time. **Output**: Verify `data/output/pipeline_metrics.json` exists and contains `total_duration_seconds`. **Dependency**: T041a.
- [X] T042 [P] Validate pipeline execution time against a defined operational threshold. **Threshold**: 21600 seconds (6 hours). **Action**: If `data/output/pipeline_metrics.json` is missing, malformed, or `total_duration_seconds` (float, 2 decimal precision) > 21600, **Raise `PerformanceThresholdError`** and block `research_accepted` transition. **Dependency**: T041.
- [X] T043 [P] Verify `requirements.txt` contains no GPU-specific libraries (e.g., `torch`, `tensorflow`) or LLM dependencies to ensure CPU-only compliance.

---

## Phase 7: Final Integration & Execution Verification

**Goal**: Ensure the entire pipeline runs end-to-end without manual intervention and produces all required artifacts.

- [ ] T054b [P] [All] **Real Data Robustness Test**: Execute `code/analysis.py` on the first 100 rows of the *actual* fetched structural dataset (from `data/processed/structural_subset.csv`) to verify that the LASSO CV and MLR models do not crash on edge cases (e.g., perfect multicollinearity, near-zero variance). **Explicitly exclude** this data from final research results. **Dependency**: T024, T023.
- [ ] T055 [P] [All] **Full Pipeline Smoke Test**: Execute `code/run_pipeline.py` end-to-end. **Success Criteria**: `data/processed/merged_drugs.csv`, `data/processed/analysis_results.json`, `results_report.md`, and `reproducibility_log.json` are all created and non-empty. **Dependency**: T041a, T016d, T026, T034.
- [ ] T055a [P] [All] **Fresh Environment Smoke Test**: Simulate a fresh environment by clearing all caches and temporary files, then re-running `code/run_pipeline.py`. **Success Criteria**: Pipeline completes successfully and produces identical hashes to T055. **Action**: Use `code/verify_hashes.py` to compare SHA256 hashes. **Dependency**: T055.
- [X] T056a [P] [All] **Automated Reproducibility Audit**: Execute a script that programmatically compares the SHA256 hashes in `reproducibility_log.json` against the actual `data/` files. **Action**: If hashes mismatch, **FAIL** the task and block `research_accepted` transition. **Dependency**: T035c, T055.
- [ ] T057 [P] [All] **Final Gate Check**: Confirm that `data/gate_status.json` accurately reflects the outcome of the Data Availability Gate (Pass/Fail) and that the pipeline logic correctly branched to either `results_report.md` or `data_insufficiency_report.md`. **Dependency**: T013, T055.

---

## Phase 8: Execution & Performance Validation

**Goal**: Ensure the pipeline meets strict performance constraints and handles edge cases in real execution environments.

- [X] T060 [P] **Edge Case Stress Test**: Execute the pipeline with a synthetic edge-case dataset containing molecules with extreme complexity, using a representative set of hardcoded SMILES strings. **Dependency**: T054b.

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
- **User Story 2 (P2)**: Depends on T016d (merged dataset) - Must wait for US1 completion
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
- Different user stories can be worked on in parallel by different team members