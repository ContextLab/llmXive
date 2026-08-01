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

- [X] T011 [US1] **Data Source Fetch**: Implement `code/ingest.py` to download `Synthyra/FDA-Approved-Drugs` from HuggingFace using `streaming=True`. **Command**: `python code/ingest.py --fetch`. **Action**: Save raw data to `data/raw/fda_structures.parquet`. **Dependency**: T004, T002.
- [X] T011c [US1] **Schema Verification**: Implement a verification step in `code/ingest.py` (or a separate script) to load `data/raw/fda_structures.parquet` and verify the presence of a `smiles` column. **Action**: If `smiles` is missing, raise a `SchemaError` and halt. **Dependency**: T011.
- [X] T011b [US1] **Static Constraint Assertion**: Implement logic to assert the Plan's Critical Constraint: "No verified public dataset containing both FDA-approved structures and experimental degradation rates was identified." **Action**: Load `data/raw/fda_structures.parquet`. Verify that NO column exists containing degradation data (e.g., `half_life`, `k_degradation`, `rate_constant`). **Action**: Write `data/gate_status.json` with `{"status": "FAIL", "reason": "No verified degradation data source found in Synthyra dataset", "N": 0}`. **Do NOT** perform an active search for ChEMBL or DrugBank. **Dependency**: T011c.
- [ ] T012 [US1] **Ingest & Gate**: Implement `code/ingest.py` to: 1) Read `data/gate_status.json`. 2) If status is "FAIL", generate `data_insufficiency_report.md` and exit cleanly. **Do NOT** create `data/processed/structural_subset.csv`. 3) If status is "PASS" (unexpected), merge structural data with degradation data on `canonical_smiles`. 4) Check for degradation columns and count valid records (N). 5) Enforce Gate: If N < 30, update `data/gate_status.json` to `{"status": "FAIL", "reason": "N < 30", "N": <count>}`, generate `data_insufficiency_report.md`, and exit. 6) If N >= 30, update status to "PASS", save merged data to `data/processed/merged_drugs.csv`, and save checksums. **Dependency**: T011, T011b, T004.
- [X] T014 [US1] Implement `code/descriptors.py`: Calculate TPSA, Rotatable Bond Count, MW, Aromatic Ring Count, Wiener Index, and Zagreb Index. **Zagreb Index Implementation**: If `rdkit.Chem.Descriptors.ZagrebIndex` is missing, implement fallback: `sum(d * d for d in [mol.GetAtomWithIdx(i).GetTotalDegree() for i in range(mol.GetNumAtoms())])`. **Dependency**: T012 (if Gate Pass) or T012 (if Gate Fail, calculate on `structural_subset.csv` if it existed, otherwise skip).
- [X] T010 [US1] **Unit Tests for Descriptors**: Implement unit tests in `tests/test_descriptors.py` for all FR-002 metrics using Aspirin as the primary reference (SMILES: `CC(=O)Oc1ccccc1C(=O)O`). **Assertion**: Verify calculated values match known reference values within RDKit precision. **RDKit Version**: Must match pinned version in `requirements.txt`. **Dependency**: T006.
- [ ] T010g [US1] **Dataset Metric Verification**: Implement a test in `tests/test_descriptors.py` that calculates metrics for a set of **hardcoded reference SMILES** (e.g., Aspirin, Caffeine, Diazepam). **Action**: Verify calculated values fall within expected scientific ranges (e.g., MW > 0, TPSA >= 0). **Dependency**: T014.
- [ ] T015 [US1] Implement error handling in `code/descriptors.py`: Flag/exclude molecules with non-standard valence. **Action**: Wrap RDKit calls in a try/except block. If an exception occurs, log the SMILES, error_type, and timestamp to `data/processed/excluded_molecules.csv`. **Schema**: `smiles` (string), `error_type` (string), `timestamp` (ISO8601). **Dependency**: T014.
- [ ] T015b [US1] **Validation of Excluded Molecules**: Implement a test in `tests/test_descriptors.py` to verify that `data/processed/excluded_molecules.csv` exists (if exclusions occurred) and contains the required schema columns. **Dependency**: T015.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Correlation Analysis and Regression Modeling (Priority: P2)

**Goal**: Standardize degradation units, stratify by conditions, perform correlation analysis, and fit regression models with cross-validation.

**Independent Test**: The analysis script can be run on the P1 output dataset to generate a correlation matrix and regression coefficients. The test verifies that the output includes p-values, R² scores, and that the models are trained using K-fold cross-validation.

### Implementation for User Story 2

- [ ] T020 [US2] **Standardization & Stratification**: Implement `code/standardize.py` to: 1) Read `data/gate_status.json`. If "FAIL", generate empty `data/processed/standard_subset.csv` with schema, write `data/stat_gate_status.json` with `{"status": "FAIL", "reason": "Data Gate Failed"}`, and exit cleanly. 2) If "PASS", convert rate constants (k) to half-lives (t1/2 = ln(2)/k), standardize time units to hours (numeric conversion). 3) Stratify: Filter for "Standard" conditions where `float(temperature_c) == 25.0` (or within 0.1 tolerance) AND `float(ph_value) == 7.4` (or within 0.1 tolerance). 4) **Verification**: Count records in `standard_subset`. If N < 30, write `data/stat_gate_status.json` with `{"status": "FAIL", "reason": "Insufficient Standard Condition Records", "N": <count>}` and exit. 5) If N >= 30, write `{"status": "PASS", "N": <count>}` and save `standard_subset`. **Dependency**: T012.
- [X] T023 [US2] Implement Multiple Linear Regression (MLR) in `code/analysis.py` **operating strictly on the `standard_subset`** (read from `data/processed/standard_subset.csv`). **Dependency**: T020.
- [X] T024 [US2] Implement LASSO regression with **dynamic K-fold** cross-validation in `code/analysis.py`. Determine K as the minimum of a predefined upper bound and a value strictly less than the total sample size n. **Constraint**: Verify K is less than n. Use **GridSearchCV** with a param_grid covering a range of alpha values. **Read `standard_subset` from `data/processed/standard_subset.csv`**. **Dependency**: T020.
- [X] T025 [US2] Implement residual diagnostics in `code/analysis.py`: Perform Shapiro-Wilk (normality) and Breusch-Pagan (homoscedasticity) tests on model residuals. **Requirement**: `statsmodels` and `scipy` are explicitly required. **Action**: Save numeric results (p-values, test statistics) to `data/processed/analysis_results.json`. **Dependency**: T024.
- [ ] T026 [US2] **Save Analysis Results**: Generate `data/processed/analysis_results.json`. **Schema**: `{"status": "PASS"|"FAIL", "N": int, "R2": float|null, "p_values": dict|null, "coefficients": dict|null, "methodology": "MLR+LASSO", "timestamp": "ISO8601", "diagnostics": {"shapiro_wilk": {"stat": float, "p": float}, "breusch_pagan": {"stat": float, "p": float}}}`. **Action**: If Gate Pass (T020/T025 success), populate with real results. If Gate Fail, populate with `status: "FAIL"`, `N: <count>`, and `null` for metrics, ensuring the artifact exists. **Dependency**: T025 (if Pass), T020 (if Fail).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate diagnostic plots and a reproducible report documenting code, data versions, and results.

**Independent Test**: The script generates a set of PNG/SVG files and a summary report. The test verifies that the plots exist, show the expected regression lines and residual patterns, and that the report includes the exact dataset hashes and code version used.

### Implementation for User Story 3

- [ ] T032 [US3] Implement `code/viz.py`: **IF** Data Availability Gate passed (N >= 30) **AND** Statistical Gate passed (N >= 30) **THEN** generate scatter plots with regression lines for top correlated features using `matplotlib.pyplot` (figure size 10x6, style `seaborn.whitegrid`); **save to `data/outputs/scatter_tpsa_vs_half_life.png`**, etc. **ELSE** (Gate Fail) **SKIP** plot generation. **Dependency**: T012, T020, T026.
- [ ] T033 [US3] Implement `code/viz.py`: **IF** Data Availability Gate passed (N >= 30) **AND** Statistical Gate passed (N >= 30) **THEN** generate residual diagnostic plots (histogram, QQ-plot, residuals vs fitted); **save to `data/outputs/residuals.png`**, `qq_plot.png`. **ELSE** (Gate Fail) **SKIP** plot generation. **Dependency**: T025, T012, T020, T026.
- [X] T034 [US3] Implement `code/report.py`: Generate `results_report.md` summarizing methodology, coefficients, and R² scores. **IF** Data Availability Gate failed (N < 30), generate `data_insufficiency_report.md` instead. **Dependency**: T026, T032, T033.
- [X] T035 [US3] Implement reproducibility check in `code/report.py`: Log RDKit/scikit-learn versions, dataset URLs, retrieval dates, and **SHA256 hash values of raw and processed files directly in the report**. **Dependency**: T034.
- [X] T035b [US3] Implement machine-readable reproducibility log in `code/report.py`: Generate `reproducibility_log.json` containing versions, URLs, and SHA256 hashes of all data files (raw and processed). **Schema**: `{"artifacts": [{"path": str, "hash": str, "lineage": {"source_path": str, "transformation": str}}]}`. **Action**: Explicitly link derived file hashes to their source files and transformation steps. **Dependency**: T034.
- [X] T035c [US3] **Artifact Verification Fix**: Implement a final validation step in `code/report.py` to check the file size of `data/processed/analysis_results.json` (if Gate Pass) or `data/data_insufficiency_report.md` (if Gate Fail). **Logic**: If Gate Pass, the file must be non-empty and contain valid data (no nulls in key fields). If Gate Fail, the file `data_insufficiency_report.md` must exist and contain the "Insufficient" text. If `analysis_results.json` is empty (0 bytes) in a PASS state, **FAIL** the task. **Dependency**: T034, T026.
- [ ] T036 [US3] Save all plots to `data/outputs/` and final report to `results_report.md`; verify the existence of the required plot files (`scatter_tpsa_vs_half_life.png`, `residuals.png`, `qq_plot.png`) and the report file. **Logic**: **IF** gate passed, verify each plot file has a non-zero size. **IF** gate failed, verify no plot files are generated (as per T032/T033) and only the report exists. **Dependency**: T032, T033, T034, T035.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T031 [US3] Integration test for report generation in `tests/test_pipeline.py`. Function: `test_report_generation_and_plots`. **Assertion**: Verify `results_report.md` contains `dataset_hash` field, code version, and all expected sections; verify `data/outputs/` contains `scatter_tpsa_vs_half_life.png`, `residuals.png`, `qq_plot.png` with non-zero size **IF** N >= 30, or verify **no** plot files exist **IF** N < 30. **Dependency**: T036.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Documentation updates in `quickstart.md` and `README.md`
- [X] T038 Code cleanup and refactoring (ensure no hardcoded paths)
- [ ] T041a [P] Create `code/run_pipeline.py`: A master script that imports and executes the full pipeline (US1 -> US2 -> US3) in sequence. **Entry Point**: `if __name__ == '__main__':`. **Action**: Check `data/gate_status.json` and `data/stat_gate_status.json` for "FAIL" status. If "FAIL", exit cleanly with status code 0 and log "Pipeline halted due to data insufficiency". **Do NOT** catch `DataInsufficiencyError`. **Output**: Write execution metrics to `data/output/pipeline_metrics.json` including `total_duration_seconds` (float, 2 decimal precision), `status` (PASS/FAIL), and `error_message` (if any). **Schema**: `{"total_duration_seconds": float, "status": str, "error_message": str|null}`. **Dependency**: `code/ingest.py`, `code/descriptors.py`, `code/standardize.py`, `code/analysis.py`, `code/report.py`.
- [ ] T041 [P] Execute full pipeline script (`code/run_pipeline.py`) and measure total execution time. **Output**: Verify `data/output/pipeline_metrics.json` exists and contains `total_duration_seconds`. **Dependency**: T041a.
- [X] T042 [P] Validate pipeline execution time against a defined operational threshold. **Threshold**: 21600 seconds (6 hours). **Action**: If `data/output/pipeline_metrics.json` is missing, malformed, or `total_duration_seconds` (float, 2 decimal precision) > 21600, **Raise `PerformanceThresholdError`** and block `research_accepted` transition. **Dependency**: T041.
- [X] T043 [P] Verify `requirements.txt` contains no GPU-specific libraries (e.g., `torch`, `tensorflow`) or LLM dependencies to ensure CPU-only compliance.

---

## Phase 7: Final Integration & Execution Verification

**Goal**: Ensure the entire pipeline runs end-to-end without manual intervention and produces all required artifacts.

- [ ] T054b [P] [All] **Real Data Robustness Test (Dry Run)**: Execute `code/analysis.py` in a "Dry Run" mode using the **real data path** (or empty path if Gate Failed). **Action**: Verify that the pipeline imports correctly, handles missing data gracefully (if Gate Failed), and does not crash. **Explicitly exclude** any results from being logged to `reproducibility_log.json` or `results_report.md` (this is a structural test only). **Dependency**: T024, T023.
- [ ] T055 [P] [All] **Full Pipeline Smoke Test**: Execute `code/run_pipeline.py` end-to-end. **Success Criteria**: `data/processed/structural_subset.csv` (if Gate Fail) OR `data/processed/merged_drugs.csv` (if Gate Pass), `data/processed/analysis_results.json`, `results_report.md` (or `data_insufficiency_report.md`), and `reproducibility_log.json` are all created and non-empty. **Dependency**: T041a, T012, T020, T026, T034.
- [ ] T055a [P] [All] **Fresh Environment Smoke Test**: Simulate a fresh environment by clearing all caches and temporary files, then re-running `code/run_pipeline.py`. **Success Criteria**: Pipeline completes successfully and produces identical hashes to T055. **Action**: Use `code/verify_hashes.py` to compare SHA256 hashes. **Dependency**: T055.
- [X] T056a [P] [All] **Automated Reproducibility Audit**: Execute a script that programmatically compares the SHA256 hashes in `reproducibility_log.json` against the actual `data/` files. **Action**: If hashes mismatch, **FAIL** the task and block `research_accepted` transition. **Dependency**: T035c, T055.
- [ ] T057 [P] [All] **Final Gate Check**: Confirm that `data/gate_status.json` accurately reflects the outcome of the Data Availability Gate (Pass/Fail) and that the pipeline logic correctly branched to either `results_report.md` or `data_insufficiency_report.md`. **Dependency**: T012, T055.

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
- **User Story 2 (P2)**: Depends on T012 (Gate Status) - Must wait for US1 completion
- **User Story 3 (P3)**: Depends on T026 (Analysis Results or Gate Fail Artifact) - Must wait for US2 completion

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