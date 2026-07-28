# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Sleep Architecture

**Input**: Design documents from `/specs/001-gut-microbiome-sleep-architecture/`
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

- [X] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`, `data/config/`)
- [X] T002 Initialize Python 3.11 project with dependencies: `pandas`, `scipy`, `statsmodels`, `numpy`, `scikit-learn`, `pyyaml`, `scikit-bio`, `pytest`, `spiec-easi`, `sparcc`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a Define predictor schema (taxa) in `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml` **referencing `data/config/required_variables.yaml` for the explicit list of required predictor variables.**
- [X] T004b Define outcome schema (sleep metrics) in `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml` **referencing `data/config/required_variables.yaml` for the explicit list of required outcome variables.**
- [X] T004c **IMPLEMENT `data/config/required_variables.yaml`**: Generate this file by extracting the explicit list of required predictor and outcome variables directly from `spec.md` (FR-001, Edge Cases). **Logic**: Parse `spec.md` for variable names (e.g., "SWS duration", "REM duration", "taxon_01"...). **Output**: `data/config/required_variables.yaml` with schema: `required_predictors: [string], required_outcomes: [string]`. **This is the Single Source of Truth for variable lists used in T012/T078.**
- [X] T005a Define output schema (CorrelationResult structure) in `specs/001-gut-microbiome-sleep-architecture/contracts/output.schema.yaml`
- [X] T006 Implement data loading utilities in `code/ingest.py` (CSV/TSV reader, column validation)
- [X] T006d **IMPLEMENT CHECKSUM SCHEMA AND RECORDING**: Implement `record_artifact_checksum(file_path, state_file)` in `code/reference_validator.py`. **Schema**: `artifact_hashes: { "<file_path>": "sha256:<hash>" }`. **Constraint**: This step MUST be invoked by T015 (Orchestration) as a blocking step before analysis begins. **Addresses Constitution Principle I & III.**
- [X] T007 Configure CI workflow in `.github/workflows/analysis.yml` to run on `ubuntu-latest` with CPU/GB RAM limits
- [X] T008 Setup environment configuration management (`.env` template, `requirements.txt`)
- [X] T009a [P] Define Reference-Validator Agent schema in `code/reference_validator.py`
- [X] T009b [P] Implement Reference-Validator Agent logic and integrate gate in CI (`.github/workflows/analysis.yml`) to fail build if citations are unverified (Note: Gate operates in 'Logic Only' mode for synthetic data as per Plan's 'Verified Accuracy' strategy).
- [X] T021c [P] Define configuration list of definitionally related taxa pairs in `data/config/definitionally_related_pairs.yaml`. **Format**: YAML list of lists `[[taxon_A, taxon_B],...]`. **Schema**: `pairs: [[string, string],...]`. **Addresses FR-006.**
- [X] T021f [P] **IMPLEMENT STATIC COLLINEARITY DETECTION AND GENERATE ARTIFACT**: Implement "Perfect Multicollinearity" detection algorithm in `code/diagnostics.py` (static analysis of T021c config) and generate output artifact `data/metadata/static_collinearity_map.json`. **Input**: `data/config/definitionally_related_pairs.yaml` (list of lists). **Output**: `data/metadata/static_collinearity_map.json` (JSON map of flagged pairs). **DEPENDS ON T021c.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion, Validation, and Pipeline Execution (Priority: P1) 🎯 MVP

**Goal**: Ingest raw data, validate variable presence, and ensure pipeline runs within 6 hours on CPU-only CI.

**Independent Test**: Run ingestion against a mock dataset missing "SWS duration"; verify system halts with specific error. Run dummy pipeline on CI; verify completion < 6h.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py` (Depends on T004a, T004b, T005a). **This task validates the existence and structure of the schema files (T004a/b), NOT the validation logic implementation (T012).**
- [X] T011 [P] [US1] Integration test for missing variable error handling in `tests/integration/test_missing_variable.py`

### Implementation for User Story 1

- [X] T012 [US1] **IMPLEMENT VALIDATION LOGIC AND METRICS GENERATION**: Implement `validate_variables()` in `code/ingest.py` to check for required predictors (taxa) and outcomes (sleep metrics) defined in `data/config/required_variables.yaml` (output of T004c). **CRITICAL**: Calculate the percentage of required variables successfully loaded, include the list of missing variables in the output JSON, and WRITE the metric file (`data/results/variable_load_metrics.json`) TO DISK BEFORE ANY EXIT CALL. **Schema**: `{"status": "PASS" | "FAIL", "percentage_loaded": float, "missing_variables": [string], "total_required": int}`. **Verification**: Verify file exists and contains keys: `status`, `percentage_loaded`, `missing_variables`, `total_required`. **Addresses FR-001 and SC-001.**
- [X] T013 [US1] Implement `load_data()` in `code/ingest.py` to read CSV/TSV, **READ the percentage metric from `data/results/variable_load_metrics.json` (output of T012)**, and **halt execution with `sys.exit(1)`** if the percentage is < 100% with specific error message (e.g., "Variable 'SWS duration' is missing") per FR-001. **DEPENDS ON T012 writing the artifact first.** **Error Handling**: If `variable_load_metrics.json` is missing or malformed, raise `FileNotFoundError` with message "CRITICAL: Validation artifact missing. Cannot proceed." and exit.
- [X] T014 Implement outlier detection logic in `code/ingest.py` (IQR method: >1.5x IQR above 75th or < 1.5x IQR below 25th)
- [ ] T014b [US1] **IMPLEMENT OUTLIER FILTERING AND REPORT GENERATION**: Implement data filtering step in `code/ingest.py` to remove flagged outliers and output the filtered dataset to `data/processed/filtered_data.parquet`. **DEPENDS ON T014.** **CRITICAL**: Also generate `data/results/outlier_report.json` containing the count of excluded points and the list of excluded row indices. **Schema**: `{"count": int, "excluded_indices": [int]}`. **Addresses FR-001.**
- [ ] T014c [US1] Register the checksum for `data/processed/filtered_data.parquet` in `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml` per Constitution Principle III. **DEPENDS ON T014b.**
- [X] T015 Implement pipeline orchestration in `code/main.py` to sequence ingestion, validation, and execution. **Constraint**: Must invoke T006d (checksum recording) as a blocking step before proceeding to analysis.
- [ ] T016 [US1] **IMPLEMENT EXECUTION TIMING CHECK AND EVIDENCE GENERATION**: Implement execution timing check in `code/main.py` to log start/end times, assert < 6 hours, and **generate timing evidence artifact (JSON log at `data/results/timing_evidence.json`)** to satisfy SC-004. **CRITICAL**: If the time limit is exceeded, the system MUST **HALT** (`sys.exit(1)`) with a "TIMEOUT" error. **Output**: `data/results/timing_evidence.json`. **DEPENDS ON T014b, T015.**
- [X] T016a [US1] Create script in `code/run_stress_test.py` to execute the full pipeline on the `ubuntu-latest` runner. **DEPENDS ON T016.**
- [X] T016b [US1] Add assertion logic in `code/run_stress_test.py` to verify total execution time is < 6 hours. **DEPENDS ON T016a.**
- [ ] T016c [US1] Generate `data/results/stress_test_report.json` with pass/fail status and timing details. **DEPENDS ON T016b.**
- [X] T017 [US1] Add logging for ingestion and validation steps in `code/ingest.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Robust Associational Correlation Analysis (Priority: P2)

**Goal**: Compute correlations with automatic method selection (ZINB/Spearman/Pearson) and FDR correction, explicitly framing results as associational.

**Independent Test**: Run analysis on synthetic data with known zero-inflation; verify ZINB selection and correct coefficients. Verify BH-adjusted p-values and associational language in report.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for correlation output schema in `tests/contract/test_output_schema.py`
- [X] T019 [P] [US2] Integration test for method selection logic (Zero-inflated vs Non-normal) in `tests/integration/test_method_selection.py`

### Implementation for User Story 2

- [X] T020 Implement data distribution checks in `code/analysis.py` (Shapiro-Wilk test, zero proportion calculation) **AND check for zero-inflation (zeros > 30% OR Shapiro-Wilk p < 0.05)**. **DEPENDS ON T014b.**
- [X] T020a Implement compositionality detection in `code/transform.py` and integrate `scikit-bio` libraries if available. **Output: `data/metadata/compositionality_flag.json`.**
- [X] T022a [P] **IMPLEMENT COMPOSITIONALITY CHECK**: Verify `data/metadata/compositionality_flag.json` exists and is valid. **DEPENDS ON T020a.**
- [X] T022 Implement CLR transformation in `code/transform.py` using `scikit-bio` for compositional data handling (fallback if SparCC unavailable). **CONDITIONAL**: Only run if T021 selects a method requiring compositional correction and the compositionality flag is set (from T020a). **Output**: `data/processed/processed_data.parquet`. **DEPENDS ON T022a.**
- [X] T021 **IMPLEMENT CORRELATION METHOD SELECTION**: Implement `select_correlation_method()` in `code/analysis.py` with explicit decision logic **strictly following FR-002**: 1) If zero-inflation (zeros > 30% OR Shapiro-Wilk p < 0.05), use a Zero-Inflated Negative Binomial (ZINB) or Hurdle model; 2) Else if non-normality is detected (Shapiro-Wilk p < 0.05), use Spearman rank correlation; 3) Else use Pearson correlation. **CRITICAL**: Do NOT use library availability as a fallback. If the required library is missing, the pipeline must fail loudly. **MUST read `data/metadata/compositionality_flag.json` and zero proportion from T020**. **DEPENDS ON T022** (if CLR selected).
- [X] T023 Implement ZINB/Hurdle model fitting in `code/analysis.py` using `statsmodels` for zero-inflated cases
- [X] T024 Implement Spearman and Pearson correlation functions in `code/analysis.py`
- [ ] T025 **IMPLEMENT FDR CORRECTION AND OUTPUT**: Implement Benjamini-Hochberg FDR correction in `code/analysis.py` to adjust p-values (q ≤ 0.05) and write the full correlation matrix to `data/results/correlation_matrix.json`. **DEPENDS ON T022** (if CLR selected) **and T023/T024**.
- [ ] T026 Extend pipeline orchestration in `code/main.py` to import and call US2 modules **without modifying T015 logic**; **DEPENDS ON T022, T025, T026a.**
- [X] T027 Add logging for analysis steps in `code/analysis.py`

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently

---

## Phase 4.5: Integration & Reporting (Cross-Story)

**Purpose**: Integrate US1 and US2 artifacts into final report and verify cross-story consumption.

- [X] T026a [P] **IMPLEMENT COMPOSITIONALITY CHECK**: Verify `data/metadata/compositionality_flag.json` exists and is valid. **DEPENDS ON T020a.**
- [ ] T026a Implement `enforce_associational_framing()` in `code/report.py` to scan generated text for causal language ('causes', 'leads to', 'effect') and replace with 'associational with', 'correlates with', 'relationship'.
- [ ] T026 Integrate diagnostics into `code/main.py` and append results to final report. **DEPENDS ON T022, T025, T026a.**

**Checkpoint**: US1 and US2 are integrated

---

## Phase N+3: Compute Optimization & Streaming (Priority: P6)

**Purpose**: Ensure the pipeline respects CPU/GPU constraints and handles large datasets via strict RAM limits without fabrication or runner changes.

**SERIALIZATION NOTE**: T058 determines the path. T059 (STREAM) and T060 (FAIL) are mutually exclusive branches based on T058's output, not sequential steps.

- [X] T058 **IMPLEMENT COMPUTE STRATEGY AND RAM CHECK**: Implement a RAM check to estimate memory usage. **Formula**: `estimated_gb = (num_rows * avg_row_bytes * 1.1) / (1024^3)`. **Constants**: `avg_row_bytes = 1024`, `scaling_factor = 1.1`, `size_per_element = 1024`, `threshold_gb = 7.0`. **Output**: `data/results/compute_strategy.json` with status: `OK`, `STREAM`, or `FAIL`. **Constraint**: If status is `FAIL` or `STREAM` but analysis logic does not support chunked input, trigger T060.
- [X] T059 **IMPLEMENT STREAMING LOGIC**: If T058 returns `STREAM` AND analysis logic supports chunked input, switch to chunked processing using `pandas.read_csv(..., chunksize=...)`. **Constraint**: If T058 returns `STREAM` but the analysis logic (e.g., ZINB) does not support chunked input, trigger T060 (Hard Halt) immediately. **Note**: T059 and T060 are mutually exclusive branches based on T058 output.
- [ ] T060 Implement a hard halt logic in `code/main.py` if the RAM check fails (T058 returns `FAIL`) or if `STREAM` is requested but not supported. **Addresses Assumption-001.**

**Checkpoint**: Pipeline is robust against large datasets and respects compute constraints.

---

## Phase N+4: Real-Data Execution & GPU Offload Verification (Priority: P7)

**Purpose**: Execute the pipeline on a real dataset (if available) or a verified large-sample proxy, ensuring streaming and RAM logic functions correctly without fabrication.

- [X] T064 **STREAMING EXECUTION TEST**: Run the pipeline on a large dataset (real or proxy). **DEPENDS ON T058, T059, T070.**
- [X] T065 **VALIDATE STREAMING OUTPUT**: Verify that the output from T064 is correct and meets the requirements of the project (no data loss in chunks). **DEPENDS ON T064.**
- [X] T066 Execute the full pipeline on the real dataset if available. **DEPENDS ON T051b (SUCCESS), T064, T065.**

**Checkpoint**: The pipeline has been successfully executed on real data with streaming and RAM logic, and the results have passed a fabrication audit.

---

## Phase N+5: Data Source Resolution & Pipeline Re-Enablement (Priority: P8)

**Purpose**: Resolve the "No Verified Real Dataset" blocker identified in Phase N+2 by enforcing single-source data requirements and re-enabling the full analysis on real data if found.

- [ ] T051a **IMPLEMENT FETCH LOGIC**: Implement `fetch_real_data()` in `code/ingest.py` to attempt download from verified sources (NCBI, Zenodo) using specific IDs. **Output**: `data/raw/real_data.csv`.
- [X] T051b **IMPLEMENT FETCH EXECUTION AND STOP LOGIC**: Execute T051a. **Constraint**: If T051a fails (no data found), the pipeline MUST **STOP** and transition to T053a (Synthetic Validation) ONLY AFTER T055 (Gate) confirms no synthetic fallback occurred. **Output**: `data/metadata/fetch_status.json`.
- [X] T053a **UPDATE PLAN FOR SYNTHETIC SCOPE**: Update `plan.md` to reflect "Pipeline Validation Study" scope if T051b fails. **DEPENDS ON T051b.**
- [X] T053d **IMPLEMENT SYNTHETIC VALIDATION**: Run the pipeline on synthetic data if real data is unavailable. **DEPENDS ON T053a.**
- [X] T055 **REAL DATA GATE**: Implement a CI gate that verifies no synthetic data was used if real data was expected. **Constraint**: MUST run AFTER T051b to verify no synthetic fallback occurred. **DEPENDS ON T051b.**
- [X] T056 **VERIFICATION**: Verify that the pipeline correctly handles the "No Real Data" state. **DEPENDS ON T055.**
- [ ] T069 **RE-ENABLE REAL DATA PIPELINE**: Modify `code/main.py` and `code/ingest.py` to accept the validated real data (if found).
- [ ] T070 **LARGE PROXY GENERATOR**: Create a script in `code/generate_large_proxy.py` that generates a verified large proxy dataset. **Schema**: A dataset comprising a substantial number of subjects (rows) and taxa (columns: `subject_id`, `taxon_01`...`taxon_50` (float64, normal dist, seed=42), `sleep_metric_1`...`sleep_metric_4`). **Output**: `data/raw/large_proxy.csv`. **Addresses Assumption-001 and Streaming Test requirements.**

**Checkpoint**: The project transitions from a "Pipeline Validation Study" to a biological discovery study using real, single-source data, with all gates passed and results validated.

---

## Phase N+6: Review Resolution & Final Validation (Priority: P10)

**Purpose**: Address specific reviewer concerns regarding the "Pipeline Validation Study" scope, the lack of real data, and the robustness of the synthetic validation logic. Ensure all artifacts are consistent with the current state of the project.

- [X] T072 **DOCUMENT REAL DATA IMPOSSIBILITY**: Generate `docs/real_data_impossibility_report.md` documenting the search for a valid dataset.
- [X] T072a **IMPLEMENT SEARCH AND SCORING**: Implement a systematic search for real datasets. **Search Terms**: ["gut microbiome sleep", "metagenomics polysomnography", "sleep architecture microbiome"]. **Repositories**: NCBI, Zenodo. **Algorithm**: `The feasibility score will be calculated as the minimum of a normalized upper bound and the product of the count of verified sources and a a weighting factor within a moderate range.`. **Output**: `data/metadata/search_findings.json` with schema: `{"sources": [...], "feasibility_score": float}`.
- [ ] T073 Update `code/constitution_checker.py` to correctly identify the project as "Synthetic Only".

**Checkpoint**: The project is fully documented as a "Pipeline Validation Study", all constitutional checks pass for the synthetic scope, and the roadmap for future real-data integration is clearly defined.

---

## Dependencies & Execution Order

(As described in previous versions)
