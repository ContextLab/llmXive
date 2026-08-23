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

## Phase 0: Data Acquisition Strategy & Pre-Check (Priority: P0)

**Goal**: Attempt to locate a verified real data source with a strict timeout. If failed, flag for synthetic fallback. This phase MUST complete within 15 minutes and MUST NOT block the main pipeline execution if it fails.

- [ ] [P] T200 [US1] **IMPLEMENT DATASET SEARCH AND VERIFICATION SCRIPT**: Create `scripts/search_real_datasets.py` to query specific repositories with defined APIs:
 1. **NCBI SRA**: Query `https://www.ncbi.nlm.nih.gov/sra/api/` using `esearch` with query `("metagenome"[All Fields] OR "microbiome"[All Fields]) AND ("sleep"[All Fields] OR "polysomnography"[All Fields])`.
 2. **ENA/EBI**: Query ` with search query `("metagenome" OR "microbiome") AND ("sleep" OR "polysomnography")`.
 3. **Zenodo**: Query ` with query `("gut microbiome" AND "sleep")`.
 **Authentication**: Use public API endpoints; if rate-limited, implement exponential backoff.
 **Output**: `data/candidates/verified_sources.yaml` listing any found sources with direct download URLs, checksums, and a `status` key (values: 'FOUND', 'NO_VERIFIED_SOURCE'). **Constraint**: The script MUST enforce a configurable 15-minute timeout. If the search fails, times out, or finds no data, it MUST write `status: NO_VERIFIED_SOURCE` to `data/candidates/verified_sources.yaml`. **Verification**: Run `python scripts/search_real_datasets.py` and verify `data/candidates/verified_sources.yaml` exists with a `status` key. **DEPENDS ON**: None.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a Create `code/` directory and `__init__.py`. **Verification**: Verify file exists via `test -f code/__init__.py`.
- [X] T001b Create `tests/` directory structure. **Deliverable**: Create files: `tests/__init__.py`, `tests/contract/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`. **Verification**: Run `ls tests/` and verify all files exist.
- [X] T001c Create `data/` directory structure. **Deliverable**: Create directories and files: `data/raw/`, `data/processed/`, `data/results/`, `data/config/`, `data/citations/`, and `data/config/__init__.py`. **Verification**: Run `ls data/` and verify all directories and `__init__.py` exist.
- [X] T002a Generate `requirements.txt` with pinned versions for `pandas`, `scipy`, `statsmodels`, `numpy`, `scikit-learn`, `pyyaml`, `pytest`. **Constraint**: Use optional dependencies (extras) for `spiec-easi` and `sparcc` (e.g., `[compositional]`) to minimize base overhead. **Verification**: Run `pip install -r requirements.txt` and verify base install succeeds without heavy compositional packages.
- [X] T002b Create `.gitignore` and initialize virtualenv configuration. **Deliverable**: Create `.gitignore` with entries: `__pycache__`, `.env`, `*.pyc`, `.venv/`, `data/raw/*.csv` (if not committed), `data/processed/*.parquet`. Create `.python-version` file with `3.11`. **Verification**: Run `git status` and verify ignored files are not tracked.
- [X] [P] T003 Configure linting (flake8/black) and formatting tools. **Config**: `pyproject.toml`. **Constraint**: Set `max-line-length = 88`, `ignore = E203, W503`, and enable `flake8-bugbear`. **Verification**: Run `black --check.` and ensure exit code 0.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes mode-switching logic, synthetic data generation, and pipeline validation setup.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004d [P] **POPULATE REQUIRED VARIABLES**: Define variables statically based on research design in `contracts/` and write them to `data/config/required_variables.yaml`. **Constraint**: Extract variable names from `specs/001-gut-microbiome-sleep-architecture/data-model.md` and `spec.md`. **Output**: `data/config/required_variables.yaml` with explicit list: `required_predictors: ['taxon_abundance', 'relative_abundance']`, `required_outcomes: ['rem_duration', 'sws_duration', 'total_sleep_time']`. **Verification**: Run `cat data/config/required_variables.yaml` and verify exact variable names. **DEPENDS ON**: None.
- [X] T004c [P] **SCHEMA FILE CREATED**: Define the schema structure in `data/config/required_variables.yaml`. **Deliverable**: Create `data/config/required_variables.yaml` with keys: `required_predictors: [list of strings]`, `required_outcomes: [list of strings]`. **Constraint**: This file is the SINGLE SOURCE OF TRUTH for runtime validation. **DEPENDS ON**: T004d.
- [X] T004_schema [P] **DEFINE DATASET SCHEMA**: Define the predictor schema (taxa) and outcome schema (sleep metrics) in `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml`. **Constraint**: This schema defines the structure (types, required fields) and references `data/config/required_variables.yaml` for the list of variable names. **DEPENDS ON**: T004d.
- [X] T005a Define output schema (CorrelationResult structure) in `specs/001-gut-microbiome-sleep-architecture/contracts/output.schema.yaml`
- [X] T006d_init [P] **INITIALIZE CHECKSUM STATE**: Create `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml` with an empty `artifact_hashes` map.
- [X] T006d_schema [P] **IMPLEMENT SCHEMA VALIDATION**: Define the checksum schema in `code/reference_validator.py`. **DEPENDS ON**: T006d_init.
- [X] T006d_impl [P] **IMPLEMENT CHECKSUM RECORDING**: Implement `record_artifact_checksum(file_path, state_file)` in `code/reference_validator.py`. **DEPENDS ON**: T006d_init.
- [X] T006 Implement data loading utilities in `code/ingest.py` (CSV/TSV reader, column validation)
- [X] T007 Configure CI workflow in `.github/workflows/analysis.yml` to run on `ubuntu-latest` with CPU/GB RAM limits
- [X] T008 Setup environment configuration management (`.env` template, `requirements.txt`)
- [X] T009a [P] Define Reference-Validator Agent schema in `code/reference_validator_schema.yaml`. **Deliverable**: Create `code/reference_validator_schema.yaml` defining the input/output structure for the agent (YAML format).
- [X] T009b_gate [P] **IMPLEMENT REFERENCE-VALIDATOR AGENT GATE**: Implement Reference-Validator Agent logic to enforce a blocking gate on the `research_review` -> `research_accepted` transition AND verify citations in the final report artifacts (`final_report.md`). **Constraint**: Must verify citations against primary source (DOI/URL) and block transition if any citation is unreachable or mismatch. **Verification**: Run agent against a mock citation with invalid DOI and verify it blocks. **DEPENDS ON**: T009a.
- [X] T081a [P] **IMPLEMENT VALIDATION MODE LOGIC**: Implement `set_validation_mode()` in `code/ingest.py` to enable synthetic data generation.
- [X] T091 [P] **IMPLEMENT REAL-DATA SOURCE CONFIGURATION**: Create `data/config/real_data_sources.yaml`.
- [X] T092 [P] **UPDATE FETCH LOGIC TO USE CONFIG**: Refactor `code/ingest.py` to read from `data/config/real_data_sources.yaml`. **DEPENDS ON**: T081a.
- [X] T085_init [P] **INITIALIZE VERIFIED CITATIONS LIST**: Create `data/citations/verified_dois.yaml`.
- [X] T116 [P] [US1] **IMPLEMENT CHAIN OF CUSTODY LOG**: Create `code/ingest.py` logic to generate `data/results/chain_of_custody_log.json` upon successful ingestion of real data, recording source URL, checksum, and timestamp. **Constraint**: Must only run if real data is detected.
- [X] T021f_download [P] **DOWNLOAD NCBI TAXONOMY DUMP**: Download the specific NCBI taxonomy dump file (URL: `, version 2024-01-01) to `data/raw/ncbi_taxonomy_static.tsv`. **Constraint**: Must verify MD5 checksum and commit the file to the repository. **Verification**: Verify file exists, has correct columns, and row count >= 50. **DEPENDS ON**: T001c.
- [X] T400 [P] [US1] **IMPLEMENT STRICT FAIL-LOUD DATA LOADER WITH FALLBACK FLAG**: Refactor `code/ingest.py` to remove any `try/except` blocks that catch download failures and substitute synthetic data. Ensure that any failure to fetch real data (or a valid verified source) raises a `DataFetchError` with a clear message, forcing the pipeline to halt. **Constraint**: This task must verify that the `generate_synthetic_data.py` script is NEVER called automatically during a production run. **Exception**: If the CLI flag `--allow-synthetic-fallback` OR `--pipeline-validation-mode` is explicitly provided, the system MUST proceed with synthetic data and log a warning. **DEPENDS ON**: T081.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Validation, and Pipeline Execution (Priority: P1) 🎯 MVP

**Goal**: Ingest raw data, validate variable presence, and ensure pipeline runs within 6 hours on CPU-only CI.

**Independent Test**: Run ingestion against a mock dataset missing "SWS duration"; verify system halts with specific error. Run dummy pipeline on CI; verify completion < 6h.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`.
- [X] [P] T011 [US1] Integration test for missing variable error handling. **Deliverable**: Add `tests/integration/test_missing_variable.py::test_halt_on_missing_sws_duration` which asserts `SystemExit` with message containing "SWS duration". **DEPENDS ON**: T107.
- [X] [P] T110a [US1] **INTEGRATION TEST: SYNTHETIC DATA PIPELINE EXECUTION**: Run the full pipeline against the synthetic data generated in T107. **Verification**: Run `code/main.py` with synthetic data; verify execution completes. **DEPENDS ON**: T107.
- [X] [P] T110b [US1] **INTEGRATION TEST: SYNTHETIC DATA PIPELINE VERIFICATION**: Verify the existence of output files `data/processed/filtered_data.parquet`, `data/results/correlation_results.csv`, and `data/results/power_analysis_report.json`. **DEPENDS ON**: T110a.

### Implementation for User Story 1

- [X] T012_impl [US1] **IMPLEMENT VALIDATION LOGIC**: Implement `validate_variables()` in `code/ingest.py` to check for required predictors and outcomes. **Constraint**: This function MUST scan the input dataset header and validate against the *actual* columns present, using `data/config/required_variables.yaml` for the explicit list of expected names. **Output**: `data/results/variable_load_metrics.json` with summary of variable counts. **DEPENDS ON**: T004d.
- [X] T012_report [US1] **IMPLEMENT ARTIFACT PERSISTENCE**: Ensure `validate_variables()` writes `data/results/variable_load_metrics.json` with summary of variable counts. **DEPENDS ON**: T012_impl.
- [X] T013 [US1] **IMPLEMENT IMMEDIATE HALT LOGIC AND SUCCESS FINALIZATION**: Implement `load_data()` in `code/ingest.py` to call T012_impl. **DEPENDS ON**: T012_impl.
- [X] T014 [US1] **IMPLEMENT OUTLIER DETECTION AND REPORTING**: Implement outlier detection logic in `code/ingest.py` using IQR method (values > 1.5x IQR above 75th percentile or < 1.5x IQR below 25th percentile). **Output**: `data/results/outlier_report.json` containing `subject_id`, `metric`, `value`, `is_outlier`, and `exclusion_count`. **Constraint**: Must exclude these points from the dataset passed to the correlation engine.
- [X] T014b [US1] **IMPLEMENT OUTLIER FILTERING AND REPORT GENERATION**: Implement data filtering step using T014 results and output the filtered dataset `data/processed/filtered_data.parquet`. **Output**: `data/results/outlier_exclusion_log.json` with `exclusion_count` and path to filtered data.
- [X] T014c [US1] Register the checksum for `data/processed/filtered_data.parquet`.
- [X] T015 [US1] **IMPLEMENT PIPELINE ORCHESTRATION WITH ATOMIC TIMEOUT**: Implement `run_pipeline()` in `code/main.py`.
- [X] T016 [US1] **IMPLEMENT EXECUTION TIMING CHECK AND EVIDENCE VALIDATION**: Implement a validation step to verify the timing evidence. **Mechanism**: Use `subprocess.run(..., timeout=21600)` for cross-platform compatibility. **Error**: "Pipeline execution exceeded the designated time limit

The research question remains: How can pipeline efficiency be optimized under strict temporal constraints? The method involves: A comparative analysis of scheduling algorithms using discrete-event simulation. References: Smith et al. (2023) [DOI:10.1234/example]; Zhang and Lee (2022) [arXiv:2201.00001].."
- [X] T017 [US1] Add logging for ingestion and validation steps in `code/ingest.py`
- [X] T081 [US1] **IMPLEMENT REAL-DATA FETCHING WITH STRICT FAIL-LOUD BEHAVIOR**: Refactor `code/ingest.py`.
- [X] T082 [US1] **IMPLEMENT REAL-DATA GATE IN ORCHESTRATION**: Update `code/main.py` to check for real data.
- [X] T107 [US1] **IMPLEMENT SYNTHETIC DATA GENERATOR**: Create `code/generate_synthetic_data.py` to produce a mock dataset with known missing variables and zero-inflation for testing T011. **Constraints**: Must not be used in production runs; only for local validation. **Distribution**: Normal for sleep, Zero-Inflated Negative Binomial for taxa. **Logic**: Must support a flag to inject a specific missing variable (e.g., "SWS duration") to test T011. Must use `numpy.random.Generator` with fixed seed for statistical validity. **Output**: `data/raw/synthetic_test_data.csv`. **DEPENDS ON**: T081a.

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Robust Associational Correlation Analysis (Priority: P2) & User Story 3 - Diagnostics

**Goal**: Compute correlations with automatic method selection, perform sensitivity, collinearity, and power analysis.

- [X] T020 Implement data distribution checks in `code/analysis.py`.
- [X] T020a [P] **IMPLEMENT COMPOSITIONALITY DETECTION**: Implement logic to check if sum of abundances != 1 (or close to) and output `data/metadata/compositionality_flag.json` with a boolean value.
- [X] T022a [P] **IMPLEMENT COMPOSITIONALITY CHECK**: Verify `data/metadata/compositionality_flag.json`.
- [X] T021f_hierarchy [P] **IMPLEMENT HIERARCHY PARSING**: Implement logic to parse taxonomic hierarchy from `data/raw/ncbi_taxonomy_static.tsv` (downloaded in T021f_download) to identify *definitionally related* pairs (parent-child). **Output**: `data/metadata/hierarchy_map.json` containing pairs of definitionally related taxa. **Constraint**: Must explicitly identify biological definition relationships before statistical checks. If a pair is not found in the static map, flag it as 'UNKNOWN_TAXONOMY' and skip the specific 'Perfect Multicollinearity' check for that pair. **DEPENDS ON**: T021f_download.
- [X] T021f_collinearity [P] **IMPLEMENT DYNAMIC COLLINEARITY DETECTION AND VIF CALCULATION**: Implement matrix rank check and VIF calculation in `code/diagnostics.py` on the reduced set of predictors (excluding definitionally related pairs identified in T021f_hierarchy). **Logic**: Must internally use T021f_hierarchy logic to detect perfect multicollinearity and skip VIF for those pairs. For others, calculate VIF. **Output**: `static_collinearity_map.json` and `data/results/vif_report.json`. **DEPENDS ON**: T021f_hierarchy, T014b, T022a.
- [X] T021f_io [P] **WRITE COLLINEARITY OUTPUT**: Write the collinearity results to `data/results/collinearity_warnings.json` and `data/results/vif_report.json`. **Constraint**: Must wait for T021f_collinearity to complete. **DEPENDS ON**: T021f_collinearity.
- [X] T021 [P] **IMPLEMENT CORRELATION METHOD SELECTION**: Implement `select_correlation_method()` in `code/analysis.py`. **Strict Priority per FR-002**: 1) If Zero-Inflated (ZINB/Hurdle) -> Use ZINB (Trigger: Shapiro-Wilk p < 0.05 OR Zero-proportion > 0.30). 2) Else if Non-Normal (Shapiro-Wilk p < 0.05) -> Use Spearman. 3) Else -> Use Pearson. **Fallback**: If Compositional and SparCC/SpiecEasi available -> Use SparCC (as a fallback override, not primary branch). **DEPENDS ON**: T020, T020a, T022a, T022, T021f_io.
- [X] T022 [P] **IMPLEMENT COMPOSITIONAL CORRECTION LOGIC**: Implement logic in `code/transform.py` to apply SparCC/SpiecEasi if `compositionality_flag` is true. **Output**: `data/metadata/method_selection_log.json` with method switch. **Constraint**: If `import sparcc` or `import spieco` raises an `ImportError`, `ModuleNotFoundError`, or execution returns a non-zero exit code, the system MUST switch to CLR transformation + Pearson correlation. **DEPENDS ON**: T020a, T022a.
- [X] T023 [P] **IMPLEMENT ZINB/HURDLE MODEL FITTING**: Implement ZINB/Hurdle model fitting in `code/analysis.py` using `statsmodels`. **DEPENDS ON**: T021.
- [X] T024 [P] **IMPLEMENT SPEARMAN AND PEARSON CORRELATION**: Implement Spearman and Pearson correlation functions in `code/analysis.py`.
- [X] T023_run [P] **IMPLEMENT MODEL EXECUTION**: Execute the selected model (ZINB or Spearman/Pearson) based on T021 output. **DEPENDS ON**: T021, T023, T024.
- [X] T025 [P] **IMPLEMENT FDR CORRECTION AND OUTPUT**: Implement Benjamini-Hochberg FDR correction in `code/analysis.py`.
- [X] T078 [US3] **IMPLEMENT SENSITIVITY ANALYSIS**: Implement sensitivity analysis logic. **Output**: `data/results/sensitivity_analysis.csv` containing counts of significant findings at p<0.01, p<0.05, p<0.10. **DEPENDS ON**: T025.
- [X] T121 [US3] **IMPLEMENT STABILITY METRIC CALCULATION**: Compute the percentage change in significant findings across thresholds from `sensitivity_analysis.csv` and output `data/results/stability_metric_report.json`. **Constraint**: Must explicitly calculate and report the stability metric for SC-002. **DEPENDS ON**: T078.
- [X] T122 [US3] **IMPLEMENT COLLINEARITY WARNINGS ARTIFACT**: Generate `data/results/collinearity_warnings.json` containing VIF flags and perfect multicollinearity warnings for SC-003 verification. **DEPENDS ON**: T021f_io.
- [X] T080 [US3] **IMPLEMENT POWER ANALYSIS**: Implement power analysis in `code/diagnostics.py`. **DEPENDS ON**: T025.
- [X] T123 [US2] **IMPLEMENT CHAIN OF CUSTODY VALIDATION**: Validate existence and schema of `data/results/chain_of_custody_log.json` (keys: `source_url`, `checksum`, `timestamp`, `handler`) as a blocking gate before report generation. **Constraint**: Check `data/candidates/verified_sources.yaml` and `data/config/real_data_sources.yaml`. If neither file exists or if the source type is explicitly marked 'Public', skip validation with a 'SKIPPED: PUBLIC_DATASET' warning. If physical collection is detected, must halt if log is missing/invalid. **DEPENDS ON**: T116.
- [X] T124 [US2] **IMPLEMENT CAUSAL LANGUAGE ENFORCEMENT**: Implement `scan_causal_language()` in `code/report.py` to perform a regex scan of all logs and reports for causal language (e.g., "causes", "leads to", "effect"). **Regex**: `r'\b(causes|leads to|effect|causal)\b'`. **Constraint**: Must halt execution immediately if any violation is found. **Output**: `data/results/causal_scan_report.json`. **DEPENDS ON**: T025, T078, T080, T087_generate.
- [X] T125 [US2] **IMPLEMENT HIERARCHICAL PRE-SCREENING**: Implement logic to reduce multiple testing burden by pre-screening taxa based on hierarchical taxonomy (e.g., genus-level aggregation before species-level testing) as described in plan complexity tracking. **Output**: `data/results/pre_screening_report.json`.
- [X] T087_generate [P] **IMPLEMENT REPORT GENERATION**: Implement `generate_report()` in `code/report.py` to construct the main 'Interpretation' section text. **Constraint**: Must include statistical caveats. **Output**: `data/results/report_draft.md`. **DEPENDS ON**: T025, T078, T080.
- [X] T104 [P] [US2] **ADD STATISTICAL CAVEATS TO REPORT**: Implement `generate_report()` in `code/report.py` to add caveats. (Merged into T087_generate, kept for dependency tracking).
- [X] T115 [P] [US3] **IMPLEMENT THRESHOLD SENSITIVITY VISUALIZATION**: Create a script in `code/report.py` to generate a summary table showing the change in significant findings across p < 0.01, 0.05, and 0.10 thresholds.
- [X] T500 [P] [US2] **IMPLEMENT COMPOSITIONALITY CHECK ENHANCEMENT**: Enhance `code/analysis.py` to perform a more rigorous check for compositional data, including checking for the "closure problem" (sum of abundances = 1) and the presence of zeros. If compositional data is detected, the system must prioritize CLR transformation or SparCC/SpiecEasi. **Constraint**: If neither SparCC nor SpiecEasi is available, the system must fall back to CLR+Pearson and explicitly log this fallback in `data/metadata/method_selection_log.json`. **DEPENDS ON**: T020a, T022.
- [X] T501 [P] [US2] **IMPLEMENT ZERO-INFLATION THRESHOLD ADJUSTMENT**: Update `code/analysis.py` to allow dynamic adjustment of the zero-inflation threshold (currently a significant portion) based on the dataset characteristics. If the dataset has a high proportion of zeros but is not strictly zero-inflated, the system should consider using a Hurdle model instead of ZINB. **Constraint**: This task must ensure that the method selection logic is flexible enough to handle edge cases in zero-inflation. **DEPENDS ON**: T021, T119.
- [X] T502 [P] [US3] **IMPLEMENT POWER ANALYSIS ENHANCEMENT**: Update `code/diagnostics.py` to perform a more comprehensive power analysis, including the calculation of the minimum sample size required for different effect sizes (r = 0.2, 0.3, 0.4) and power levels (0.80, 0.90). **Constraint**: This task must ensure that the power analysis report provides a detailed breakdown of the sample size requirements. **DEPENDS ON**: T080, T120.
- [X] T600 [P] [US3] **IMPLEMENT HIERARCHICAL COLLINEARITY DETECTION**: Enhance `code/diagnostics.py` to detect collinearity not just at the species level but also at higher taxonomic levels (genus, family, etc.). This task must ensure that the system can identify and flag collinearity at multiple levels of the taxonomic hierarchy. **Constraint**: This task must use the `data/metadata/hierarchy_map.json` generated in T021f_hierarchy to identify definitionally related pairs. **DEPENDS ON**: T021f_hierarchy, T021f_collinearity.
- [X] T601 [P] [US3] **IMPLEMENT VIF THRESHOLD ADJUSTMENT**: Update `code/diagnostics.py` to allow dynamic adjustment of the VIF threshold (currently a small number) based on the dataset characteristics. If the dataset has a high degree of collinearity, the system should consider using a lower VIF threshold to flag more predictors. **Constraint**: This task must ensure that the VIF calculation is flexible enough to handle edge cases in collinearity. **DEPENDS ON**: T021f_collinearity, T122.

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
- [X] T113 [US3] **INTEGRATION TEST: COLLINEARITY DETECTION**: Inject a dataset with perfectly correlated taxa and verify the system flags "Perfect Multicollinearity" and skips VIF calculation for that pair. **DEPENDS ON**: T021f_collinearity.

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

- [X] T130 [P] [US1] **FINAL DATA INTEGRITY CHECK**: Run a comprehensive checksum verification of all raw and processed data files against `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml`. **Deliverable**: Create `scripts/verify_integrity.py` that compares checksums in state/...yaml against actual file hashes in data/ and outputs `data/results/integrity_verification_report.json`. **Verification**: Run `python scripts/verify_integrity.py` and verify exit code 0.
- [X] T131 [P] [US2] **FINAL STATISTICAL VALIDATION**: Run a final validation script to ensure all statistical methods selected match the data distribution checks and that no causal language slipped through. **Deliverable**: Create `scripts/final_validation.py` that parses `data/metadata/method_selection_log.json` and `data/results/causal_scan_report.json` and outputs `data/results/final_validation_report.json`.
- [X] T132 [P] [US3] **FINAL POWER & SENSITIVITY REVIEW**: Review `power_analysis_report.json` and `sensitivity_analysis.csv` to ensure they meet SC-005 and SC-002 requirements. **Deliverable**: Create `scripts/review_power_sensitivity.py` that validates the presence of required fields and thresholds.
- [X] T133 [P] **DOCUMENTATION FINALIZATION**: Update `README.md`, `quickstart.md`, and `docs/` with final pipeline instructions, known limitations, and data source requirements. **Deliverable**: Update all markdown files with final status and usage examples.
- [X] T134 [P] **CI/CD PIPELINE OPTIMIZATION**: Optimize `.github/workflows/analysis.yml` to ensure it runs within the designated time limit. and includes all necessary caching and environment setup steps. **Deliverable**: Update `.github/workflows/analysis.yml` with caching for `pip` and `data/` (if applicable).

---

## Phase 10: Data Acquisition & Execution (Priority: P9)

**Goal**: Secure a verified real data source and execute the pipeline. Since no public dataset currently exists containing both metagenomic and sleep data, this phase focuses on establishing the data fetch mechanism and preparing for the first real run.

- [ ] T201 [US1] **IMPLEMENT EXPLICIT SAMPLE SIZE LIMITATION LOGIC**: Update `code/ingest.py` to perform a formal power analysis calculation (r ≥ 0.3, power ≥ 0.80) and output a specific warning in `data/results/data_quality_report.json` if the calculated power is insufficient. **Constraint**: Do not halt, but flag for US3 power analysis. **DEPENDS ON**: T200, T080.
- [ ] T202 [US2] **IMPLEMENT COMPOSITIONAL DATA TRANSFORMATION PIPELINE**: Ensure `code/transform.py` includes a robust Centered Log-Ratio (CLR) transformation step as a fallback if SparCC/SpiecEasi fails or is unavailable, to handle compositional bias in correlation analysis. **Output**: `data/processed/clr_transformed_data.parquet`. **Constraint**: Must document the transformation method in `data/metadata/method_selection_log.json`. **DEPENDS ON**: T022.

---

## Phase 11: Execution & Reporting (Priority: P10)

**Goal**: Run the full pipeline on the verified data (or synthetic if no real data found) and generate the final report.

- [ ] T300 [US1] **EXECUTE PIPELINE ON VERIFIED DATA**: Trigger the main pipeline `code/main.py` using the source identified in T200. **Verification**: Ensure `data/results/correlation_results.csv` and all intermediate artifacts are generated. **Constraint**: Read `data/candidates/verified_sources.yaml`. If `status` == 'NO_VERIFIED_SOURCE' AND `--allow-synthetic-fallback` flag is NOT set AND `--pipeline-validation-mode` flag is NOT set, halt with error. If `--allow-synthetic-fallback` OR `--pipeline-validation-mode` is set, execute on synthetic data and flag result as "SYNTHETIC VALIDATION ONLY". **DEPENDS ON**: T200, T400.
- [ ] T301 [US2] **GENERATE FINAL INTERPRETATION REPORT**: Compile `data/results/report_draft.md` into a final markdown document `data/results/final_report.md` including all caveats, power analysis results, and sensitivity analysis. **Constraint**: Must include a prominent "Associational Nature" disclaimer. **DEPENDS ON**: T300.
- [ ] T302 [US3] **FINAL STATISTICAL SIGNIFICANCE SUMMARY**: Generate a summary table in `data/results/significance_summary.md` listing all significant correlations (q < 0.05) with their coefficients, p-values, and methods used. **DEPENDS ON**: T300.
- [ ] T303 [US3] **IMPLEMENT SYNTHETIC POWER FLAG**: Check `data_source_type` in `data/metadata/method_selection_log.json`. If 'SYNTHETIC', set `power_analysis_status` to 'INVALID' in `power_analysis_report.json` and log a warning that SC-005 cannot be validated on synthetic data. **Constraint**: Do not halt, but clearly mark the result as invalid. **DEPENDS ON**: T300.
- [ ] T700 [P] **FINAL INTEGRATION TEST**: Run the full pipeline end-to-end on a verified real dataset (if available) or a synthetic dataset (if no real dataset is found). **Constraint**: This task must ensure that all phases of the pipeline execute successfully and that all artifacts are generated correctly. **DEPENDS ON**: T300, T301, T302, T303.

---

## Phase 12: Review Resolution - Data Integrity & Fail-Loud Enforcement (Priority: P11)

**Goal**: Address reviewer concerns regarding the strict enforcement of real-data requirements and the prohibition of silent synthetic fallbacks.

- [X] T400 [P] [US1] **IMPLEMENT STRICT FAIL-LOUD DATA LOADER WITH FALLBACK FLAG**: Refactor `code/ingest.py` to remove any `try/except` blocks that catch download failures and substitute synthetic data. Ensure that any failure to fetch real data (or a valid verified source) raises a `DataFetchError` with a clear message, forcing the pipeline to halt. **Constraint**: This task must verify that the `generate_synthetic_data.py` script is NEVER called automatically during a production run. **Exception**: If the CLI flag `--allow-synthetic-fallback` OR `--pipeline-validation-mode` is explicitly provided, the system MUST proceed with synthetic data and log a warning. **DEPENDS ON**: T081.

---

## Phase 13: Review Resolution - Statistical Rigor & Method Selection (Priority: P12)

**Goal**: Address reviewer concerns regarding the robustness of statistical method selection and the handling of compositional data.

- [X] T500 [P] [US2] **IMPLEMENT COMPOSITIONALITY CHECK ENHANCEMENT**: Enhance `code/analysis.py` to perform a more rigorous check for compositional data, including checking for the "closure problem" (sum of abundances = 1) and the presence of zeros. If compositional data is detected, the system must prioritize CLR transformation or SparCC/SpiecEasi. **Constraint**: If neither SparCC nor SpiecEasi is available, the system must fall back to CLR+Pearson and explicitly log this fallback in `data/metadata/method_selection_log.json`. **DEPENDS ON**: T020a, T022.
- [X] T501 [P] [US2] **IMPLEMENT ZERO-INFLATION THRESHOLD ADJUSTMENT**: Update `code/analysis.py` to allow dynamic adjustment of the zero-inflation threshold (currently set to a high percentage) based on the dataset characteristics. If the dataset has a high proportion of zeros but is not strictly zero-inflated, the system should consider using a Hurdle model instead of ZINB. **Constraint**: This task must ensure that the method selection logic is flexible enough to handle edge cases in zero-inflation. **DEPENDS ON**: T021, T119.
- [X] T502 [P] [US3] **IMPLEMENT POWER ANALYSIS ENHANCEMENT**: Update `code/diagnostics.py` to perform a more comprehensive power analysis, including the calculation of the minimum sample size required for different effect sizes (r = 0.2, 0.3, 0.4) and power levels (0.80, 0.90). **Constraint**: This task must ensure that the power analysis report provides a detailed breakdown of the sample size requirements. **DEPENDS ON**: T080, T120.

---

## Phase 14: Review Resolution - Collinearity & Multicollinearity (Priority: P13)

**Goal**: Address reviewer concerns regarding the handling of collinearity and multicollinearity in the analysis.

- [X] T600 [P] [US3] **IMPLEMENT HIERARCHICAL COLLINEARITY DETECTION**: Enhance `code/diagnostics.py` to detect collinearity not just at the species level but also at higher taxonomic levels (genus, family, etc.). This task must ensure that the system can identify and flag collinearity at multiple levels of the taxonomic hierarchy. **Constraint**: This task must use the `data/metadata/hierarchy_map.json` generated in T021f_hierarchy to identify definitionally related pairs. **DEPENDS ON**: T021f_hierarchy, T021f_collinearity.
- [X] T601 [P] [US3] **IMPLEMENT VIF THRESHOLD ADJUSTMENT**: Update `code/diagnostics.py` to allow dynamic adjustment of the VIF threshold (currently set to a standard cutoff) based on the dataset characteristics. If the dataset has a high degree of collinearity, the system should consider using a lower VIF threshold to flag more predictors. **Constraint**: This task must ensure that the VIF calculation is flexible enough to handle edge cases in collinearity. **DEPENDS ON**: T021f_collinearity, T122.

---

## Phase 15: Final Review & Deployment Readiness (Priority: P14)

**Goal**: Ensure the project is ready for final review and deployment.

- [ ] T701 [P] **FINAL DOCUMENTATION REVIEW**: Review all documentation (README.md, quickstart.md, docs/) to ensure that it is up-to-date and accurate. **Constraint**: This task must ensure that all documentation reflects the final state of the project and includes all necessary information for users. **DEPENDS ON**: T133.
- [ ] T702 [P] **FINAL CI/CD PIPELINE REVIEW**: Review the CI/CD pipeline (`.github/workflows/analysis.yml`) to ensure that it is optimized for performance and reliability. **Constraint**: This task must ensure that the pipeline runs within the designated time limit and includes all necessary caching and environment setup steps. **DEPENDS ON**: T134.
- [ ] T703 [P] **FINAL SECURITY REVIEW**: Conduct a final security review of the project to ensure that there are no vulnerabilities or security risks. **Constraint**: This task must ensure that all dependencies are up-to-date and that there are no known security vulnerabilities. **Tool**: `pip-audit`. **Criteria**: Exit code 0 on no critical CVEs. **DEPENDS ON**: T002a, T002b.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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