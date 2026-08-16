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

- [X] T001a Create `code/__init__.py`
- [X] T001b Create `code/ingest.py`
- [X] T001c Create `code/transform.py`
- [X] T001d Create `code/analysis.py`
- [X] T001e Create `code/diagnostics.py`
- [X] T001f Create `code/report.py`
- [X] T001g Create `code/main.py`
- [X] T001h Create `code/synthetic_data.py`
- [X] T001i Create `code/reference_validator.py`
- [X] T001j Create `code/verify_artifacts.py`
- [X] T002a Create `tests/__init__.py`
- [X] T002b Create `tests/contract/__init__.py`
- [X] T002c Create `tests/unit/__init__.py`
- [X] T002d Create `tests/integration/__init__.py`
- [X] T003a Create `tests/contract/test_dataset_schema.py`
- [X] T003b Create `tests/contract/test_output_schema.py`
- [X] T003c Create `tests/unit/test_validation.py`
- [X] T003d Create `tests/unit/test_method_selection.py`
- [X] T003e Create `tests/integration/test_pipeline_synthetic.py` <!-- FAILED: unspecified -->
- [X] T003f Create `tests/integration/test_pipeline_real_data_fail.py`
- [X] T004a Create `data/raw/.gitkeep`
- [X] T004b Create `data/processed/.gitkeep`
- [X] T004c Create `data/results/.gitkeep`
- [X] T004d Create `data/config/.gitkeep`
- [X] T004e Create `data/metadata/.gitkeep`
- [X] T004f Create `data/citations/.gitkeep`
- [X] T005a Generate `requirements.txt` with pinned versions for `pandas`, `scipy`, `statsmodels`, `numpy`, `scikit-learn`, `pyyaml`, `scikit-bio`, `pytest`, `spiec-easi`, `sparcc`
- [ ] T005b Create `.gitignore` (exclude `data/raw/*`, `data/processed/*`, `data/results/*`, `__pycache__`, `.env`, `*.pyc`, `.pytest_cache`)
- [ ] [P] T006 Configure linting: Create `.flake8` (max-line-length=100, ignore=E501,W503) and `pyproject.toml` (black config: line-length=100, target-version=py311)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin. Includes mode-switching logic, synthetic data generation, and variable population to enable the "Pipeline Validation Study".

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007a **IMPLEMENT `data/config/required_variables.yaml`**: Define the *schema* (types, constraints) of required predictor and outcome variables in `data/config/required_variables.yaml`. **Constraint**: Do NOT hardcode specific variable names. The file must define the *types* of variables required. **Output**: `data/config/required_variables.yaml` with schema: `required_predictors: [string], required_outcomes: [string]`. **This is the Single Source of Truth for variable lists used in T012/T078.**
- [X] T007b Define predictor schema (taxa) in `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml` **referencing `data/config/required_variables.yaml` for the explicit list of required predictor variables.** **DEPENDS ON T007a.**
- [X] T007c Define outcome schema (sleep metrics) in `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml` **referencing `data/config/required_variables.yaml` for the explicit list of required outcome variables.** **DEPENDS ON T007a.**
- [X] T008a Define output schema (CorrelationResult structure) in `specs/001-gut-microbiome-sleep-architecture/contracts/output.schema.yaml`
- [X] T009a Implement data loading utilities in `code/ingest.py` (CSV/TSV reader, column validation)
- [X] T009b_schema [P] **DEFINE CHECKSUM SCHEMA**: Define the checksum schema in `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml` under `artifact_hashes`. **Schema**: `artifact_hashes: { "<file_path>": "sha256:<hash>" }`. **Addresses Constitution Principle I & III.**
- [X] T009b_impl [P] **IMPLEMENT CHECKSUM RECORDING**: Implement `record_artifact_checksum(file_path, state_file)` in `code/reference_validator.py`. **Constraint**: This step MUST be invoked by T015 (Orchestration) as a blocking step before analysis begins. **IMPORTANT**: For this "Pipeline Validation Study" (synthetic data), this task operates in "Logic Only" mode: it records checksums for generated synthetic files but does NOT enforce a blocking gate for external citation verification (which has no input). **Addresses Constitution Principle I & III.**
- [X] T009b_init [P] **INITIALIZE CHECKSUM STATE**: Create `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml` with an empty `artifact_hashes` map and record checksums for schema files (T007b/c) and the synthetic generator script (T010) once generated. **Constraint**: This task MUST run AFTER T010. **Addresses Constitution Principle I & III.**
- [X] T010 Configure CI workflow in `.github/workflows/analysis.yml` to run on `ubuntu-latest` with CPU/GB RAM limits
- [X] T011 Setup environment configuration management (`.env` template, `requirements.txt`)
- [X] T012a [P] Define Reference-Validator Agent schema in `code/reference_validator.py`
- [X] T012b [P] **IMPLEMENT REFERENCE-VALIDATOR AGENT**: Implement Reference-Validator Agent logic and integrate gate in CI (`.github/workflows/analysis.yml`). **Constraint**: The agent MUST strictly enforce Constitution Principle II: if citations are missing or unreachable, the build MUST fail with a score of 0.0. **EXCEPTION**: If `data/metadata/validation_mode_flag.json` indicates synthetic mode, the agent MUST verify that *no* external citations exist in the report and pass the gate with a 'Logic Only' status. **Addresses Constitution Principle I & II.**
- [X] T013f_algo [P] **IMPLEMENT DYNAMIC COLLINEARITY DETECTION**: Implement "Perfect Multicollinearity" detection algorithm in `code/diagnostics.py` using **matrix rank check** (e.g., `numpy.linalg.matrix_rank`) on the predictor matrix. **Constraint**: This task MUST dynamically detect linear dependence via matrix rank check as mandated by FR-006. **Logic**: Perform full matrix rank check on the predictor matrix. **Output**: `data/metadata/static_collinearity_map.json` (JSON map of flagged pairs detected via rank check).
- [X] T013f_io [P] **WRITE COLLINEARITY OUTPUT**: Write the `static_collinearity_map.json` file to disk based on the output of T013f_algo. **DEPENDS ON T013f_algo.** **Schema**: `{"pairs": [{"taxon_a": "string", "taxon_b": "string", "reason": "Perfect Multicollinearity"}]}`. **Addresses FR-006.**
- [X] T014a [P] **IMPLEMENT VALIDATION MODE LOGIC**: Implement `set_validation_mode()` in `code/ingest.py` to enable synthetic data generation for the "Pipeline Validation Study". **Constraint**: This task MUST be executed BEFORE T015 (Orchestration) to ensure the pipeline can run on synthetic data if no real data is present. **Output**: `data/metadata/validation_mode_flag.json` indicating if synthetic mode is active. **Addresses Plan.md "Critical Scope Note" and resolves conflict with T016/T017.**
- [X] T015 [P] **IMPLEMENT SYNTHETIC DATA GENERATOR**: Create `code/synthetic_data.py` to generate a deterministic mock dataset with known ground truths. **Schema**: `columns: [taxon_A, taxon_B,..., REM_duration, SWS_duration,...]`, `types: [float,...]`, `ground_truths: { 'taxon_A vs REM': 0.5 }`. **Constraint**: Must use a fixed random seed (e.g., `np.random.seed()`). **Output**: `data/raw/synthetic_data.csv`. **Metadata Output**: `data/metadata/synthetic_metadata.json` containing the list of variable names used for generation. **Addresses Plan.md "Critical Scope Note" for Pipeline Validation.**
- [X] T016 [P] **IMPLEMENT REAL DATA SOURCE CONFIGURATION**: Create `data/config/real_data_sources.yaml` to store the specific IDs/URLs for verified real datasets (e.g., NCBI BioProject IDs, Zenodo DOIs). **Constraint**: This file must be empty initially and populated only during the research phase when a real source is verified. **Addresses Constitution Principle II.**
- [X] T017 [P] **UPDATE FETCH LOGIC TO USE CONFIG**: Refactor `code/ingest.py` `fetch_real_data()` to read from `data/config/real_data_sources.yaml`. If the file is empty or contains no valid sources, the function MUST raise `RealDataFetchError` immediately. **Addresses FR-001 and "Fail Loudly" rule.**
- [X] T018_init [P] **INITIALIZE VERIFIED CITATIONS LIST**: Create `data/citations/verified_dois.yaml` with an empty list structure and a header note indicating it must be populated by the research phase. **Output**: `data/citations/verified_dois.yaml`. **Addresses FR-006 and Constitution Principle II.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Validation, and Pipeline Execution (Priority: P1) 🎯 MVP

**Goal**: Ingest raw data, validate variable presence, and ensure pipeline runs within 6 hours on CPU-only CI.

**Independent Test**: Run ingestion against a mock dataset missing "SWS duration"; verify system halts with specific error. Run dummy pipeline on CI; verify completion < 6h.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T019 [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py` (Depends on T007b, T007c, T008a). **This task validates the existence and structure of the schema files (T007b/c).**
- [ ] [P] T020 [US1] Integration test for missing variable error handling in `tests/integration/test_missing_variable.py`. **DEPENDS ON T021, T022.**

### Implementation for User Story 1

- [X] T021 [US1] **IMPLEMENT VALIDATION LOGIC AND METRIC PERSISTENCE**: Implement `validate_variables()` in `code/ingest.py` to check for required predictors (taxa) and outcomes (sleep metrics) defined in `data/config/required_variables.yaml`. **CRITICAL**: Calculate the percentage of required variables successfully loaded, include the list of missing variables in the return object, and **ALWAYS WRITE** `data/results/variable_load_metrics.json` with status, percentage, missing variables, and total required, regardless of pass/fail status. **Schema **(File): `{"status": "PASS" | "FAIL", "percentage_loaded": float, "missing_variables": [string], "total_required": int}`. **Denominator **(total_required) **Addresses FR-001 and SC-001.** **DEPENDS ON T007a.**
- [X] T021b [US1] **IMPLEMENT ARTIFACT PERSISTENCE**: Ensure `validate_variables()` writes `data/results/variable_load_metrics.json` to disk immediately upon completion of validation logic, before any other logic proceeds. **DEPENDS ON T021.**
- [X] T022 [US1] **IMPLEMENT IMMEDIATE HALT LOGIC**: Implement `load_data()` in `code/ingest.py` to call T021. **CRITICAL**: If T021 returns "FAIL", **WRITE A STRUCTURED FAILURE REPORT** (`data/results/validation_failure_report.json`) containing the error details, missing variables, and timestamp. **THEN** halt execution (`sys.exit(1`) immediately with the specific error message (e.g., "Variable 'SWS duration' is missing"). **DO NOT** read from disk. If T021 returns "PASS", proceed to read the artifact from T021b (which is now written). **Schema for Failure Report**: `{"status": "FAIL", "error_code": "MISSING_VARIABLES", "missing_variables": [string], "timestamp": "ISO8601", "message": "String"}`. **Addresses FR-001 and ensures SC-001/SC-002/SC-005 are measurable even on failure.** **DEPENDS ON T021.**
- [X] T023 Implement outlier detection logic in `code/ingest.py` (IQR method: >1.5x IQR above 75th or < 1.5x IQR below 25th)
- [X] T023b [US1] **IMPLEMENT OUTLIER FILTERING AND REPORT GENERATION**: Implement data filtering step in `code/ingest.py` to remove flagged outliers and output the filtered dataset to `data/processed/filtered_data.parquet`. **DEPENDS ON T023.** **CRITICAL**: Also generate `data/results/outlier_report.json` containing the count of excluded points and the list of excluded row indices. **Schema**: `{"count": int, "excluded_indices": [int]}`. **Addresses FR-001.**
- [X] T023c [US1] Register the checksum for `data/processed/filtered_data.parquet` in `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml` per Constitution Principle III. **DEPENDS ON T023b.** **Note**: Future work may include streaming support for large datasets, but current implementation is scoped to N < 1000 per Assumption-001 and does not support streaming.
- [X] T024 Implement pipeline orchestration in `code/main.py` to sequence ingestion, validation, and execution. **Constraint**: Must invoke T009b_impl (checksum recording) as a blocking step before proceeding to analysis. **DEPENDS ON T014a, T015.**
- [X] T025 [US1] **IMPLEMENT EXECUTION TIMING CHECK AND EVIDENCE GENERATION**: Implement execution timing check in `code/main.py` to log start/end times, assert < 6 hours, and **generate timing evidence artifact **(JSON log at `data/results/timing_evidence.json`) to satisfy SC-004. **CRITICAL**: The check is performed *after* pipeline completion. If the time limit is exceeded, the system MUST record a "TIMEOUT" status in the artifact and exit with code 1, but NOT abort mid-execution. **Schema for Evidence**: `{"start_time": "ISO8601", "end_time": "ISO8601", "duration_hours": float, "status": "PASS" | "FAIL", "limit_hours": 6.0}`. **Addresses FR-007 and SC-004.** **DEPENDS ON T023b, T024, T014a.**
- [X] T026 [US1] Add logging for ingestion and validation steps in `code/ingest.py`
- [X] T027 [US1] **IMPLEMENT REAL-DATA FETCHING WITH STRICT FAIL-LOUD BEHAVIOR**: Refactor `code/ingest.py` to remove any "fallback to synthetic" logic from the critical path. Implement `fetch_real_data()` to attempt download from verified sources (NCBI, Zenodo) using specific IDs. **Constraint**: If the fetch fails, the function MUST raise a specific `RealDataFetchError` with a clear message citing the missing source. **Exception Class Definition**: `class RealDataFetchError(Exception): def __init__(self, source_id, message): super().__init__(f"RealDataFetchError: Source {source_id} not found. {message}")`. **EXCEPTION**: If `data/metadata/validation_mode_flag.json` indicates synthetic mode, skip this step and proceed to synthetic generation. **Output**: `data/raw/real_data.csv` (if successful). **Addresses FR-001 and the "Fail Loudly" rule.**
- [X] T028 [US1] **IMPLEMENT REAL-DATA GATE IN ORCHESTRATION**: Update `code/main.py` to check for the existence of `data/raw/real_data.csv` before proceeding. **CRITICAL**: If missing, check `data/metadata/validation_mode_flag.json`. If validation mode is active, proceed to synthetic data generation (T015). If not, **HALT** with a clear error message: "Real data not found. Aborting pipeline. Please provide a verified real dataset." **Addresses the "No Silent Fallback" rule.** **Constraint**: If `data/metadata/validation_mode_flag.json` indicates synthetic mode is active, the pipeline may proceed with synthetic data generation instead of halting. **DEPENDS ON T014a, T015.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Robust Associational Correlation Analysis (Priority: P2) & User Story 3 - Diagnostics

**Goal**: Compute correlations with automatic method selection (ZINB/Spearman/Pearson) and FDR correction, explicitly framing results as associational. Perform sensitivity, collinearity, and power analysis.

**Independent Test**: Run analysis on synthetic data with known zero-inflation; verify ZINB selection and correct coefficients. Verify BH-adjusted p-values and associational language in report.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T029 [P] [US2] Contract test for correlation output schema in `tests/contract/test_output_schema.py`
- [X] T030 [P] [US2] Integration test for method selection logic (Zero-inflated vs Non-normal) in `tests/integration/test_method_selection.py`. **DEPENDS ON T031, T032.**

### Implementation for User Story 2

- [X] T031 Implement data distribution checks in `code/analysis.py` (Shapiro-Wilk test, zero proportion calculation) **AND check for zero-inflation **(zeros > 30% OR Shapiro-Wilk p < 0.05). **DEPENDS ON T023b.**
- [X] T031a Implement compositionality detection in `code/transform.py` and integrate `scikit-bio` libraries if available. **Output: `data/metadata/compositionality_flag.json`.**
- [X] T032a [P] **IMPLEMENT COMPOSITIONALITY CHECK**: Verify `data/metadata/compositionality_flag.json` exists and is valid. **DEPENDS ON T031a.**
- [X] T032 **IMPLEMENT CORRELATION METHOD SELECTION**: Implement `select_correlation_method()` in `code/analysis.py` with explicit decision logic **strictly following FR-002**: 1) If zero-inflation (zeros > 30% OR Shapiro-Wilk p < 0.05), use a Zero-Inflated Negative Binomial (ZINB) or Hurdle model; 2) Else if non-normality is detected (Shapiro-Wilk p < 0.05), use Spearman rank correlation; 3) Else use Pearson correlation. **CRITICAL**: Do NOT use library availability as a fallback. If the required library is missing, the pipeline must fail loudly. **MUST read `data/metadata/compositionality_flag.json` and zero proportion from T031**. **CRITICAL**: This task MUST generate `data/metadata/method_selection_log.json` documenting the specific statistical tests performed (Shapiro-Wilk p-value, zero proportion), the decision logic path taken, and the final selected method. **DEPENDS ON T031, T031a, T032a, T013f_io**. **Implementation**: Use `statsmodels.discrete.discrete_model.ZeroInflatedNegativeBinomialP` for ZINB fitting.
- [X] T033 Implement compositional correction logic in `code/transform.py`. **Clarification**: This task implements **CLR transformation** via `scikit-bio` as the primary method for compositional data. If `scikit-bio` is unavailable, the system MUST fail loudly. **Note**: The spec's "SHOULD use SparCC or SpiecEasi" refers to alternative *correlation methods* for compositional data, not the transformation step. This task handles transformation; correlation method selection is handled in T032. **Output**: `data/processed/processed_data.parquet`. **DEPENDS ON T032, T032a**.
- [X] T034 Implement ZINB/Hurdle model fitting in `code/analysis.py` using `statsmodels` for zero-inflated cases
- [X] T035 Implement Spearman and Pearson correlation functions in `code/analysis.py`
- [X] T036 **IMPLEMENT FDR CORRECTION AND OUTPUT**: Implement Benjamini-Hochberg FDR correction in `code/analysis.py` to adjust p-values (q ≤ 0.05) and write the full correlation matrix to `data/results/correlation_matrix.json`. **DEPENDS ON T033** (if CLR selected) **and T034/T035**.
- [X] T037 [US3] **IMPLEMENT SENSITIVITY ANALYSIS**: Implement logic to re-run significance tests at p < 0.01, p < 0.05, and p < 0.10 using results from T036. **Output**: `data/results/sensitivity_analysis.json` with percentage change in significant findings for each threshold and a `stability_status` field. **Addresses FR-005 and SC-002.** **Metric**: The `stability_status` must be calculated based on the raw percentage changes reported. **Schema**: `{"threshold_0.01": {"count": int, "pct_change": float}, "threshold_0.05": {"count": int, "pct_change": float}, "threshold_0.10": {"count": int, "pct_change": float}, "stability_status": "STABLE" | "UNSTABLE"}`. **Addresses SC-002 measurability.** **DEPENDS ON T036.**
- [X] T038 [US3] **IMPLEMENT VIF CALCULATION**: Implement Variance Inflation Factor (VIF) calculation in `code/diagnostics.py` for all predictors *excluding* those flagged as "Perfect Multicollinearity" in `data/metadata/static_collinearity_map.json` (output of T013f_io). **Output**: `data/results/vif_report.json` with VIF values and flags for VIF > 5. **Addresses FR-006 and SC-003.** **Schema**: `{"predictors": [{"taxon": "string", "vif": float, "flag": "HIGH" | "NORMAL"}]}`. **DEPENDS ON T013f_io.**
- [X] T039 [US3] **IMPLEMENT POWER ANALYSIS**: Implement power analysis in `code/diagnostics.py` to calculate minimum sample size required to detect r ≥ 0.3 with power ≥ 0.80 at α = 0.05. **Output**: `data/results/power_analysis.json` with calculated N, "Underpowered" flag if N < calculated threshold, and a `data_source_type` field (synthetic/real) to distinguish context. **Addresses FR-006 and SC-005.** **DEPENDS ON T036.**
- [X] T040 [US2] **IMPLEMENT REPORT GENERATION WITH ASSOCIATIONAL FRAMING**: Implement `generate_report()` in `code/report.py`. **CRITICAL**: This task MUST enforce associational language **during generation** (e.g., via strict template constraints) rather than post-hoc scanning. The report MUST explicitly state "These results represent an associational relationship" and prohibit causal language like "causes" or "leads to". **Output**: `data/results/final_report.md`. **DEPENDS ON T036, T037, T038, T039, T032a**. **Addresses FR-004.**

**Checkpoint**: US1 and US2 are integrated; Diagnostics complete.

---

## Phase 5: Real-Data Readiness & Verification (Priority: P8)

**Purpose**: Prepare the pipeline for immediate execution on real data once a verified source is identified, ensuring the "No Real Data" fallback logic is correctly isolated and the real-data path is fully functional.

**Note**: The pipeline is now strictly "Real-Data Only". Synthetic data is used ONLY for logic validation during development, not as a fallback for missing real data in production runs.

- [X] T041 [US1] **IMPLEMENT REAL-DATA VALIDATION**: Extend `code/ingest.py` to validate that real data (if fetched) contains all required variables defined in `data/config/required_variables.yaml` (T007a). **Constraint**: If validation fails, **HALT** with a specific error listing missing variables. **Addresses FR-001.**
- [X] T042 [US1] **UPDATE DOCUMENTATION FOR REAL-DATA EXECUTION**: Update `quickstart.md` and `README.md` to reflect the new "Real-Data First" workflow. **Constraint**: Explicitly state that the pipeline will **FAIL** if no real data is provided (unless validation mode is active), and provide instructions for obtaining a verified dataset. **Addresses the "No Synthetic Fallback" rule.**

**Checkpoint**: The pipeline is now strictly "Real-Data Only" with a clear failure path for missing data, ensuring no silent fabrication occurs.

---

## Phase 6: Data Acquisition & Synthetic Data Logic (Priority: P4)

**Goal**: Implement the specific logic for fetching real data (when available) and generating the deterministic synthetic data required for the "Pipeline Validation Study" (Plan.md Critical Scope Note).

**Independent Test**: Verify that synthetic data generation produces identical outputs on repeated runs (deterministic) and that real data fetching halts correctly when a verified source is missing.

**[P] T043 [US1] POPULATE REQUIRED VARIABLES**: Read the variable list from the synthetic data generator (T015) metadata (`data/metadata/synthetic_metadata.json`) and write the specific variable names (e.g., "taxon_A", "REM_duration") to `data/config/required_variables.yaml`. **Constraint**: This task MUST run AFTER T015 and BEFORE T021. **Output**: `data/config/required_variables.yaml` populated with concrete variable names. **Addresses FR-001 and resolves the semantic gap between schema definition and validation.**

**Checkpoint**: Data acquisition logic is complete for both validation (synthetic) and production (real) modes.

---

## Phase 7: Integration & End-to-End Validation (Priority: P5)

**Goal**: Verify the entire pipeline executes correctly in both synthetic and real-data modes, and that all output artifacts are generated correctly.

**Independent Test**: Run the full pipeline on synthetic data and verify all JSON/Parquet artifacts exist and match schemas.

### Implementation for Integration

- [X] T044 [US1] **IMPLEMENT END-TO-END TEST FOR SYNTHETIC MODE**: Create `tests/integration/test_pipeline_synthetic.py` to run the full pipeline on `data/raw/synthetic_data.csv` and verify all output artifacts (`correlation_matrix.json`, `final_report.md`, `sensitivity_analysis.json`, `vif_report.json`, `power_analysis.json`, `timing_evidence.json`) exist and match schemas. **Addresses SC-001 to SC-005.** **DEPENDS ON T015, T024.**
- [X] T045 [US1] **IMPLEMENT END-TO-END TEST FOR REAL DATA FAILURE**: Create `tests/integration/test_pipeline_real_data_fail.py` to verify that the pipeline halts with the correct error when `data/raw/real_data.csv` is missing and validation mode is off. **Addresses FR-001.**
- [X] T046 [P] **VALIDATE ARTIFACT CHECKSUMS**: Create a script `code/verify_artifacts.py` to recalculate checksums for all generated artifacts and compare against `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml`. **Addresses Constitution Principle III.**

**Checkpoint**: Full pipeline validation complete.

---

## Phase 8: Review-Driven Robustness & Edge Case Handling (Priority: P6)

**Goal**: Address specific reviewer concerns regarding data distribution handling, edge case robustness, and methodological transparency identified in prior research-stage reviews.

**Independent Test**: Verify that the pipeline correctly handles datasets with extreme zero-inflation (>50% zeros), correctly flags and excludes outliers without breaking the pipeline, and that the method selection log clearly documents the decision path for edge cases.

- [ ] T047 [US2] **IMPLEMENT ROBUST ZERO-INFLATION HANDLING**: Refactor `code/analysis.py` to handle datasets with extreme zero-inflation (>50% zeros) without crashing. **Constraint**: If the proportion of zeros exceeds 50%, the system MUST log a warning in `data/metadata/method_selection_log.json` and proceed with the ZINB/Hurdle model, but also output a `zero_inflation_warning` flag. **Addresses Edge Case: Zero-Inflated Data.**
- [X] T048 [US1] **IMPLEMENT OUTLIER EXCLUSION LOGIC WITH REPORTING**: Ensure `code/ingest.py` correctly excludes outliers (values >1.5x IQR) and logs the exclusion count and indices in `data/results/outlier_report.json`. **Constraint**: If the A significant proportion of points is excluded from the dataset., the system MUST raise a `WARNING` in the final report and flag the dataset as "High Outlier Density". **Addresses Edge Case: Outliers.** <!-- FAILED: unspecified -->
- [X] T049 [US3] **IMPLEMENT POWER ANALYSIS FOR SMALL SAMPLES**: Refactor `code/diagnostics.py` to handle cases where N < 10. **Constraint**: If N < 10, the power analysis MUST output "Insufficient Data" and set the `minimum_sample_size` to `None`, while flagging the study as "Severely Underpowered". **Addresses Edge Case: Sample Size / Power.**
- [X] T050 [US2] **IMPLEMENT COMPOSITIONALITY CHECK WITH FALLBACK**: If `scikit-bio` is unavailable for CLR transformation, the system MUST fall back to a simple log-ratio transformation (log(x+1)) and log the fallback in `data/metadata/compositionality_flag.json`. **Constraint**: The fallback MUST be explicitly documented in the final report. **Addresses Edge Case: Compositional Data.**
- [ ] T051 [US2] **IMPLEMENT METHOD SELECTION TRANSPARENCY**: Ensure `data/metadata/method_selection_log.json` includes the raw p-values from the Shapiro-Wilk test and the exact zero proportion calculated, not just the final decision. **Addresses FR-002 and methodological transparency.** <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->

**Checkpoint**: Robustness and edge case handling complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup **(Phase 1): No dependencies - can start immediately
- **Foundational **(Phase 2): Depends on Setup completion - BLOCKS all user stories
- **User Stories **(Phase 3+): All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish **(Final Phase): Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 **(P1): Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 **(P2): Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 **(P3): Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
