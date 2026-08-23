# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Sleep Architecture

**Input**: Design documents from `/specs/001-gut-microbiome-sleep-architecture/`
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

- [X] T001a Create `code/` directory and `__init__.py`. **Verification**: Verify file exists via `test -f code/__init__.py`.
- [X] T001b Create `tests/` directory structure. **Deliverable**: Create files: `tests/__init__.py`, `tests/contract/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`. **Verification**: Run `ls tests/` and verify all files exist.
- [X] T001c Create `data/` directory structure. **Deliverable**: Create directories and files: `data/raw/`, `data/processed/`, `data/results/`, `data/config/`, `data/citations/`, and `data/config/__init__.py`. **Verification**: Run `ls data/` and verify all directories and `__init__.py` exist.
- [X] T002a Generate `requirements.txt` with pinned versions for `pandas`, `scipy`, `statsmodels`, `numpy`, `scikit-learn`, `pyyaml`, `pytest`. **Constraint**: Use optional dependencies (extras) for `spiec-easi` and `sparcc` (e.g., `[compositional]`) to minimize base overhead. **Verification**: Run `pip install -r requirements.txt` and verify base install succeeds without heavy compositional packages.
- [ ] T002b Create `.gitignore` and initialize virtualenv configuration. **Deliverable**: Create `.gitignore` with entries: `__pycache__`, `.env`, `*.pyc`, `.venv/`, `data/raw/*.csv` (if not committed), `data/processed/*.parquet`. Create `.python-version` file with `3.11`. **Verification**: Run `git status` and verify ignored files are not tracked.
- [ ] [P] T003 Configure linting (flake8/black) and formatting tools. **Config**: `pyproject.toml`. **Verification**: Run `black --check.` and ensure exit code 0.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes mode-switching logic, synthetic data generation, and pipeline validation setup.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004_schema [P] **DEFINE DATASET SCHEMA**: Define the predictor schema (taxa) and outcome schema (sleep metrics) in `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml`. **Constraint**: This schema defines the structure (types, required fields) and references `data/config/required_variables.yaml` for the list of variable names. **DEPENDS ON: T004c**.
- [X] T004c **SCHEMA FILE CREATED**: Define the schema structure in `data/config/required_variables.yaml`. **Deliverable**: Create `data/config/required_variables.yaml` with keys: `required_predictors: [list of strings]`, `required_outcomes: [list of strings]`, and example values based on spec.md (e.g., `taxon_abundance`, `rem_duration`). **Verification**: Run `cat data/config/required_variables.yaml` and verify structure.
- [X] T004d **POPULATE REQUIRED VARIABLES**: Define variables statically based on research design in `contracts/` and write them to `data/config/required_variables.yaml`. **Constraint**: Do NOT read from synthetic generator. Extract variable names from `specs/001-gut-microbiome-sleep-architecture/data-model.md`. **Output**: `data/config/required_variables.yaml` with explicit list. **DEPENDS ON: T004_schema**.
- [X] T005a Define output schema (CorrelationResult structure) in `specs/001-gut-microbiome-sleep-architecture/contracts/output.schema.yaml`
- [X] T006 Implement data loading utilities in `code/ingest.py` (CSV/TSV reader, column validation)
- [X] T006d_schema [P] **IMPLEMENT SCHEMA VALIDATION**: Define the checksum schema in `code/reference_validator.py`.
- [X] T006d_impl [P] **IMPLEMENT CHECKSUM RECORDING**: Implement `record_artifact_checksum(file_path, state_file)` in `code/reference_validator.py`.
- [X] T006d_init [P] **INITIALIZE CHECKSUM STATE**: Create `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml` with an empty `artifact_hashes` map.
- [X] T007 Configure CI workflow in `.github/workflows/analysis.yml` to run on `ubuntu-latest` with CPU/GB RAM limits
- [X] T008 Setup environment configuration management (`.env` template, `requirements.txt`)
- [X] T009a [P] Define Reference-Validator Agent schema in `code/reference_validator_schema.yaml`. **Deliverable**: Create `code/reference_validator_schema.yaml` defining the input/output structure for the agent (YAML format).
- [X] T009b [P] **IMPLEMENT REFERENCE-VALIDATOR AGENT**: Implement Reference-Validator Agent logic and integrate gate in CI (`.github/workflows/analysis.yml`).
- [X] T081a [P] **IMPLEMENT VALIDATION MODE LOGIC**: Implement `set_validation_mode()` in `code/ingest.py` to enable synthetic data generation.
- [X] T091 [P] **IMPLEMENT REAL-DATA SOURCE CONFIGURATION**: Create `data/config/real_data_sources.yaml`.
- [X] T092 [P] **UPDATE FETCH LOGIC TO USE CONFIG**: Refactor `code/ingest.py` to read from `data/config/real_data_sources.yaml`. **DEPENDS ON: T081a**.
- [X] T085_init [P] **INITIALIZE VERIFIED CITATIONS LIST**: Create `data/citations/verified_dois.yaml`.
- [X] T116 [P] [US1] **IMPLEMENT CHAIN OF CUSTODY LOG**: Create `code/ingest.py` logic to generate `data/results/chain_of_custody_log.json` upon successful ingestion of real data, recording source URL, checksum, and timestamp. **Constraint**: Must only run if real data is detected.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Validation, and Pipeline Execution (Priority: P1) 🎯 MVP

**Goal**: Ingest raw data, validate variable presence, and ensure pipeline runs within 6 hours on CPU-only CI.

**Independent Test**: Run ingestion against a mock dataset missing "SWS duration"; verify system halts with specific error. Run dummy pipeline on CI; verify completion < 6h.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`.
- [ ] [P] T011 [US1] Integration test for missing variable error handling. **Deliverable**: Add `tests/integration/test_missing_variable.py::test_halt_on_missing_sws_duration` which asserts `SystemExit` with message containing "SWS duration". **DEPENDS ON: T107**.
- [ ] T110 [US1] **INTEGRATION TEST: SYNTHETIC DATA PIPELINE**: Run the full pipeline against the synthetic data generated in T107 and verify all outputs are generated. **Verification**: Run `code/main.py` with synthetic data; verify existence of `data/processed/filtered_data.parquet`, `data/results/correlation_results.csv`, and `data/results/power_analysis_report.json`. **DEPENDS ON: T107**.

### Implementation for User Story 1

- [X] T012_validate [US1] **IMPLEMENT VALIDATION LOGIC**: Implement `validate_variables()` in `code/ingest.py` to check for required predictors and outcomes against `data/config/required_variables.yaml`.
- [X] T012_report [US1] **IMPLEMENT ARTIFACT PERSISTENCE**: Ensure `validate_variables()` writes `data/results/variable_load_metrics.json` with summary of variable counts. **DEPENDS ON: T012_validate**.
- [X] T013 [US1] **IMPLEMENT IMMEDIATE HALT LOGIC AND SUCCESS FINALIZATION**: Implement `load_data()` in `code/ingest.py` to call T012.
- [X] T014 [US1] **IMPLEMENT OUTLIER DETECTION AND REPORTING**: Implement outlier detection logic in `code/ingest.py` using IQR method (values > 1.5x IQR above 75th percentile or < 1.5x IQR below 25th percentile). **Output**: `data/results/outlier_report.json` containing `subject_id`, `metric`, `value`, `is_outlier`, and `exclusion_count`. **Constraint**: Must exclude these points from the dataset passed to the correlation engine.
- [X] T014b [US1] **IMPLEMENT OUTLIER FILTERING AND REPORT GENERATION**: Implement data filtering step using T014 results and output the filtered dataset `data/processed/filtered_data.parquet`. **Output**: `data/results/outlier_exclusion_log.json` with `exclusion_count` and path to filtered data.
- [X] T014c [US1] Register the checksum for `data/processed/filtered_data.parquet`.
- [X] T015 [US1] **IMPLEMENT PIPELINE ORCHESTRATION WITH ATOMIC TIMEOUT**: Implement `run_pipeline()` in `code/main.py`.
- [X] T016 [US1] **IMPLEMENT EXECUTION TIMING CHECK AND EVIDENCE VALIDATION**: Implement a validation step to verify the timing evidence. **Mechanism**: Use `subprocess.run(..., timeout=21600)` for cross-platform compatibility. **Error**: "Pipeline execution exceeded 6-hour limit."
- [X] T017 [US1] Add logging for ingestion and validation steps in `code/ingest.py`
- [X] T081 [US1] **IMPLEMENT REAL-DATA FETCHING WITH STRICT FAIL-LOUD BEHAVIOR**: Refactor `code/ingest.py`.
- [X] T082 [US1] **IMPLEMENT REAL-DATA GATE IN ORCHESTRATION**: Update `code/main.py` to check for real data.
- [ ] T107 [US1] **IMPLEMENT SYNTHETIC DATA GENERATOR**: Create `code/generate_synthetic_data.py` to produce a mock dataset with known missing variables and zero-inflation for testing T011. **Constraints**: Must not be used in production runs; only for local validation. **Distribution**: Normal for sleep, Zero-Inflated Negative Binomial for taxa. **Logic**: Must support a flag to inject a specific missing variable (e.g., "SWS duration") to test T011. Must use `numpy.random.Generator` with fixed seed for statistical validity. **Output**: `data/raw/synthetic_test_data.csv`. **DEPENDS ON: T081a**.

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Robust Associational Correlation Analysis (Priority: P2) & User Story 3 - Diagnostics

**Goal**: Compute correlations with automatic method selection, perform sensitivity, collinearity, and power analysis.

- [X] T020 Implement data distribution checks in `code/analysis.py`.
- [X] T020a [P] **IMPLEMENT COMPOSITIONALITY DETECTION**: Implement logic to check if sum of abundances != 1 (or close to) and output `data/metadata/compositionality_flag.json` with a boolean value.
- [X] T022a [P] **IMPLEMENT COMPOSITIONALITY CHECK**: Verify `data/metadata/compositionality_flag.json`.
- [X] T022 [P] **IMPLEMENT COMPOSITIONAL CORRECTION LOGIC**: Implement logic in `code/transform.py` to apply SparCC/SpiecEasi if `compositionality_flag` is true. **Output**: `data/metadata/method_selection_log.json` with method switch. **Constraint**: Must actively switch the method, not just recommend. **DEPENDS ON: T020a, T022a**.
- [X] T021f_fetch [P] **IMPLEMENT HIERARCHY DATA FETCHING**: Fetch the NCBI taxonomy dump (or equivalent) to `data/raw/ncbi_taxonomy_dump.tsv`. **Source**: NCBI Taxonomy Database. **Format**: TSV with `taxon_id`, `parent_id`, `name`. **Verification**: Verify file exists and has correct columns.
- [X] T021f_hierarchy [P] **IMPLEMENT HIERARCHY PARSING**: Implement logic to parse taxonomic hierarchy from `data/raw/ncbi_taxonomy_dump.tsv` to identify *definitionally related* pairs (parent-child). **Output**: `data/metadata/hierarchy_map.json` containing pairs of definitionally related taxa. **Constraint**: Must explicitly identify biological definition relationships before statistical checks. **DEPENDS ON: T021f_fetch**.
- [X] T021f_collinearity [P] **IMPLEMENT DYNAMIC COLLINEARITY DETECTION AND VIF CALCULATION**: Implement matrix rank check and VIF calculation in `code/diagnostics.py` on the reduced set of predictors (excluding definitionally related pairs identified in T021f_hierarchy). **Logic**: Must internally use T021f_hierarchy logic to detect perfect multicollinearity and skip VIF for those pairs. For others, calculate VIF. **Output**: `static_collinearity_map.json` and `data/results/vif_report.json`. **DEPENDS ON: T021f_hierarchy, T014b, T022a**.
- [X] T021 [P] **IMPLEMENT CORRELATION METHOD SELECTION**: Implement `select_correlation_method()` in `code/analysis.py`. **DEPENDS ON: T020, T020a, T022a, T022, T021f_collinearity**.
- [X] T023 [P] **IMPLEMENT ZINB/HURDLE MODEL FITTING**: Implement ZINB/Hurdle model fitting in `code/analysis.py` using `statsmodels`. **DEPENDS ON: T021**.
- [X] T024 [P] **IMPLEMENT SPEARMAN AND PEARSON CORRELATION**: Implement Spearman and Pearson correlation functions in `code/analysis.py`.
- [X] T023_run [P] **IMPLEMENT MODEL EXECUTION**: Execute the selected model (ZINB or Spearman/Pearson) based on T021 output. **DEPENDS ON: T021, T023, T024**.
- [X] T025 [P] **IMPLEMENT FDR CORRECTION AND OUTPUT**: Implement Benjamini-Hochberg FDR correction in `code/analysis.py`.
- [X] T078 [US3] **IMPLEMENT SENSITIVITY ANALYSIS**: Implement sensitivity analysis logic. **Output**: `data/results/sensitivity_analysis.csv` containing counts of significant findings at p<0.01, p<0.05, p<0.10. **DEPENDS ON: T025**.
- [X] T121 [US3] **IMPLEMENT STABILITY METRIC CALCULATION**: Compute the percentage change in significant findings across thresholds from `sensitivity_analysis.csv` and output `data/results/stability_metric_report.json`. **Constraint**: Must explicitly calculate and report the stability metric for SC-002. **DEPENDS ON: T078**.
- [X] T122 [US3] **IMPLEMENT COLLINEARITY WARNINGS ARTIFACT**: Generate `data/results/collinearity_warnings.json` containing VIF flags and perfect multicollinearity warnings for SC-003 verification. **DEPENDS ON: T021f_collinearity**.
- [X] T080 [US3] **IMPLEMENT POWER ANALYSIS**: Implement power analysis in `code/diagnostics.py`. **DEPENDS ON: T025**.
- [X] T123 [US2] **IMPLEMENT CHAIN OF CUSTODY VALIDATION**: Validate existence and schema of `data/results/chain_of_custody_log.json` (keys: `source_url`, `checksum`, `timestamp`, `handler`) as a blocking gate before report generation. **Constraint**: If `data/config/real_data_sources.yaml` indicates public dataset (no physical collection), skip validation with warning. If physical collection, must halt if log is missing/invalid. **DEPENDS ON: T116**.
- [X] T124 [US2] **IMPLEMENT CAUSAL LANGUAGE ENFORCEMENT**: Implement `scan_causal_language()` in `code/report.py` to perform a regex scan of all logs and reports for causal language (e.g., "causes", "leads to", "effect"). **Regex**: `r'\b(causes|leads to|effect|causal)\b'`. **Constraint**: Must halt execution immediately if any violation is found. **Output**: `data/results/causal_scan_report.json`. **DEPENDS ON: T025, T078, T080, T087_generate**.
- [X] T125 [US2] **IMPLEMENT HIERARCHICAL PRE-SCREENING**: Implement logic to reduce multiple testing burden by pre-screening taxa based on hierarchical taxonomy (e.g., genus-level aggregation before species-level testing) as described in plan complexity tracking. **Output**: `data/results/pre_screening_report.json`.
- [X] T087_generate [P] **IMPLEMENT REPORT GENERATION**: Implement `generate_report()` in `code/report.py` to construct the main 'Interpretation' section text. **Constraint**: Must include statistical caveats. **Output**: `data/results/report_draft.md`. **DEPENDS ON: T025, T078, T080**.
- [X] T104 [P] [US2] **ADD STATISTICAL CAVEATS TO REPORT**: Implement `generate_report()` in `code/report.py` to add caveats. (Merged into T087_generate, kept for dependency tracking).
- [X] T115 [P] [US3] **IMPLEMENT THRESHOLD SENSITIVITY VISUALIZATION**: Create a script in `code/report.py` to generate a summary table showing the change in significant findings across p < 0.01, 0.05, and 0.10 thresholds.

**Checkpoint**: US1 and US2 are integrated; Diagnostics complete.

---

## Phase 5: Real-Data Readiness & Verification (Priority: P8)

**Goal**: Prepare the pipeline for immediate execution on real data once a verified source is identified.

- [X] T083 [US1] **IMPLEMENT REAL-DATA VALIDATION**: Extend `code/ingest.py`.
- [X] T086 [US1] **UPDATE DOCUMENTATION FOR REAL-DATA EXECUTION**: Update documentation.

**Checkpoint**: The pipeline is now strictly "Real-Data Only" with a clear failure path for missing data.

---

## Phase 6: Data Acquisition & Synthetic Data Logic (Priority: P4)

**Goal**: Implement the specific logic for fetching real data and generating synthetic data.

- **REMOVED**: T108, T109, T117 (Streaming logic removed as scope creep per Assumption-001).

---

## Phase 7: Integration & End-to-End Validation (Priority: P5)

**Goal**: Verify the entire pipeline executes correctly in both synthetic and real-data modes.

- [X] T111 [US1] **INTEGRATION TEST: REAL DATA FETCH FAIL**: Verify that `code/ingest.py` raises a hard error when `data/config/real_data_sources.yaml` points to a non-existent URL, ensuring no synthetic fallback occurs.
- [X] T112 [US2] **INTEGRATION TEST: METHOD SELECTION LOGIC**: Run the pipeline on three distinct datasets (normal, zero-inflated, non-normal) and verify `data/metadata/method_selection_log.json` correctly identifies the method used for each.
- [ ] T113 [US3] **INTEGRATION TEST: COLLINEARITY DETECTION**: Inject a dataset with perfectly correlated taxa and verify the system flags "Perfect Multicollinearity" and skips VIF calculation for that pair. **DEPENDS ON: T021f_collinearity**.

---

## Phase 8: Review Resolution & Robustness Enhancements (Priority: P6)

**Goal**: Address specific reviewer concerns regarding data integrity, error handling, and statistical rigor.

- [X] T100 [P] [US1] **IMPLEMENT STRICT REAL-DATA FETCH GUARD**: Refactor `code/ingest.py`.
- [X] T101 [P] [US2] **IMPLEMENT ROBUST ZINB FALLBACK LOGIC**: Add a specific error handler in `code/analysis.py`.
- [X] T102 [P] [US3] **ENHANCE POWER ANALYSIS REPORTING**: Update `code/diagnostics.py`.
- [X] T103 [P] **IMPLEMENT DATA STREAMING STUB FOR FUTURE SCALABILITY**: Create a placeholder function in `code/ingest.py`.
- [X] T118 [P] [US1] **IMPLEMENT REAL-DATA SOURCE PREFERENCE**: Update `code/ingest.py` to prioritize any "VERIFIED REAL DATA SOURCE" recipe provided in execution feedback over local `real_data_sources.yaml` configurations.
- [X] T119 [P] [US2] **IMPLEMENT EXPLICIT ZERO-INFLATION LOGIC**: Ensure `code/analysis.py` strictly implements the ZINB/Hurdle selection logic for >30% zeros or Shapiro-Wilk p < 0.05, and logs the specific trigger reason in `data/metadata/method_selection_log.json`.
- [X] T120 [P] [US3] **IMPLEMENT EXPLICIT POWER LIMITATION FLAG**: Ensure `code/diagnostics.py` outputs a clear "Underpowered" flag in `power_analysis_report.json` if observed N < required N, and includes the calculated minimum N.

---

## Phase 9: Final Verification & Documentation (Priority: P7)

**Goal**: Ensure all artifacts are complete, documented, and ready for final review.

- [ ] T130 [P] [US1] **FINAL DATA INTEGRITY CHECK**: Run a comprehensive checksum verification of all raw and processed data files against `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml`. **Deliverable**: Create `scripts/verify_integrity.py` that compares checksums in state/...yaml against actual file hashes in data/ and outputs `data/results/integrity_verification_report.json`. **Verification**: Run `python scripts/verify_integrity.py` and verify exit code 0.
- [ ] T131 [P] [US2] **FINAL STATISTICAL VALIDATION**: Run a final validation script to ensure all statistical methods selected match the data distribution checks and that no causal language slipped through. **Deliverable**: Create `scripts/final_validation.py` that parses `data/metadata/method_selection_log.json` and `data/results/causal_scan_report.json` and outputs `data/results/final_validation_report.json`.
- [ ] T132 [P] [US3] **FINAL POWER & SENSITIVITY REVIEW**: Review `power_analysis_report.json` and `sensitivity_analysis.csv` to ensure they meet SC-005 and SC-002 requirements. **Deliverable**: Create `scripts/review_power_sensitivity.py` that validates the presence of required fields and thresholds.
- [~] T133 [P] **DOCUMENTATION FINALIZATION**: Update `README.md`, `quickstart.md`, and `docs/` with final pipeline instructions, known limitations, and data source requirements. **Deliverable**: Update all markdown files with final status and usage examples.
- [ ] T134 [P] **CI/CD PIPELINE OPTIMIZATION**: Optimize `.github/workflows/analysis.yml` to ensure it runs within the designated time limit. and includes all necessary caching and environment setup steps. **Deliverable**: Update `.github/workflows/analysis.yml` with caching for `pip` and `data/` (if applicable).