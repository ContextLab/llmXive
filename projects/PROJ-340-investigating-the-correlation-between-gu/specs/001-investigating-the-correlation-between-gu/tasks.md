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
- [X] T005a Define output schema (CorrelationResult structure) in `specs/001-gut-microbiome-sleep-architecture/contracts/output.schema.yaml`
- [X] T006 [P] Implement deterministic synthetic data generator in `code/data_generator.py` (mock metagenomic counts + sleep metrics) to validate pipeline logic without real data. **SCOPE: Pipeline Validation Study ONLY. Must not be used in Real Data mode.**
- [X] T006a [P] Pin random seeds in `code/data_generator.py` (e.g., `np.random.seed()`, `random.seed()`) to ensure reproducibility per Constitution Principle I
- [X] T006b [P] Pin random seeds in `code/analysis.py` and `code/diagnostics.py` (e.g., ZINB initialization, bootstrapping) to ensure reproducibility per Constitution Principle I
- [X] T006d [P] Define `synthetic_data_manifest_schema.yaml` in `specs/001-gut-microbiome-sleep-architecture/contracts/` to satisfy Constitution Principle I (Reproducibility) for synthetic data. **Explicitly defines `schema_v1_synthetic` (with nullable `chain_of_custody_log`) and `schema_v2_real` (requires `chain_of_custody_log`). The code must enforce CoC if `schema_v2` is used. MUST record the checksum of `code/data_generator.py` in `state/projects/...yaml` `artifact_hashes` map.**
- [X] T006e [P] Update constitution check logic in `code/reference_validator.py` or `code/constitution_checker.py` to validate against `synthetic_data_manifest_schema.yaml`. **DEPENDS ON T006d.**
- [X] T006c [P] Generate synthetic "manifest" log file in `data/metadata/synthetic_data_manifest.json` using the schema defined in T006d (Note: This is a placeholder artifact for the 'Pipeline Validation Study' scope; `chain_of_custody_log` is null. **Renamed from T006c to reflect new schema and avoid CoC confusion.**)
- [X] T007 Create base data loading utilities in `code/ingest.py` (CSV/TSV reader, column validation)
- [X] T008 Configure CI workflow in `.github/workflows/analysis.yml` to run on `ubuntu-latest` with CPU/GB RAM limits
- [X] T009 Setup environment configuration management (`.env` template, `requirements.txt`)
- [X] T009a [P] Define Reference-Validator Agent schema in `code/reference_validator.py`
- [X] T009b [P] Implement Reference-Validator Agent logic and integrate gate in CI (`.github/workflows/analysis.yml`) to fail build if citations are unverified (Note: Gate operates in 'Logic Only' mode for synthetic data as per Plan's 'Verified Accuracy' strategy).
- [X] T021c [P] Define configuration list of definitionally related taxa pairs in `data/config/definitionally_related_pairs.yaml` and the schema for this config. **NEW: Atomic schema and data definition merged into one task.** **DEPENDS ON T004a, T004b.**
- [X] T021f [P] Implement "Perfect Multicollinearity" detection algorithm in `code/diagnostics.py` (static analysis of T021c config). **DEPENDS ON T021c.** **NEW: Atomic implementation.**
- [X] T021g [P] Generate output artifact `data/metadata/static_collinearity_map.json` using the algorithm from T021f. **DEPENDS ON T021f.** **Scope: ONLY definitionally related pairs from config. Does NOT detect data-driven collinearity.**

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

- [X] T012 [US1] Implement `validate_variables()` in `code/ingest.py` to check for required predictors (taxa) and outcomes (sleep metrics) defined in `dataset.schema.yaml` **by reading the list from `data/config/required_variables.yaml`**. **CRITICAL: Calculate the percentage of required variables successfully loaded, include the list of missing variables in the output JSON, and WRITE the metric file (`data/results/variable_load_metrics.json`) TO DISK BEFORE ANY EXIT CALL.** This ensures SC-001 is met even on partial failure.
- [X] T013 [US1] Implement `load_data()` in `code/ingest.py` to read CSV/TSV, **READ the percentage metric from `data/results/variable_load_metrics.json` (output of T012)**, and **halt execution with `sys.exit(1)`** if the percentage is < 100% with specific error message (e.g., "Variable 'SWS duration' is missing") per FR-001. **DEPENDS ON T012 writing the artifact first.**
- [X] T014 [US1] Implement outlier detection logic in `code/ingest.py` (IQR method: >1.5x IQR above 75th or <1.5x below 25th) and flag exclusion
- [X] T014b [US1] Implement data filtering step in `code/ingest.py` to remove flagged outliers and output the filtered dataset to `data/processed/filtered_data.parquet`. **DEPENDS ON T014.**
- [X] T014c [US1] Register the checksum for `data/processed/filtered_data.parquet` in `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml` per Constitution Principle III. **DEPENDS ON T014b.**
- [X] T015 [US1] Implement pipeline orchestration in `code/main.py` to sequence ingestion, validation, and execution
- [X] T016 [US1] Implement execution timing check in `code/main.py` to log start/end times, assert < 6 hours, and **generate timing evidence artifact (JSON log at `data/results/timing_evidence.json`)** to satisfy SC-004. **MUST run against REAL data if available (see T051), otherwise synthetic.**
- [X] T016a [US1] Create script in `code/run_stress_test.py` to execute the full pipeline on the `ubuntu-latest` runner. **DEPENDS ON T016.**
- [X] T016b [US1] Add assertion logic in `code/run_stress_test.py` to verify total execution time is < 6 hours. **DEPENDS ON T016a.**
- [X] T016c [US1] Generate `data/results/stress_test_report.json` with pass/fail status and timing details. **DEPENDS ON T016b.**
- [X] T017 [US1] Add logging for ingestion and validation steps in `code/ingest.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Robust Associational Correlation Analysis (Priority: P2)

**Goal**: Compute correlations with automatic method selection (ZINB/Spearman/Pearson) and FDR correction, explicitly framing results as associational.

**Independent Test**: Run analysis on synthetic data with known zero-inflation; verify ZINB selection and correct coefficients. Verify BH-adjusted p-values and associational language in report.

**⚠️ SERIALIZATION NOTE**:
- T020, T021, T022, T023, T024, T025 depend on `data/processed/filtered_data.parquet` (output of T014b). **US2 execution is strictly blocked until T014b completes.**
- T026 depends on `data/results/timing_evidence.json` (output of T016) and `data/processed/processed_data.parquet`. **Report generation (T026) is strictly blocked until T016 and T022/T014b complete.**
- T027 depends on US2 completion.
- **T021f (Static Collinearity) MUST be available before T020 and T021** as a pre-check.
- **T022a (Compositionality) MUST precede T021 (Method Selection)** to inform the decision tree.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for correlation output schema in `tests/contract/test_output_schema.py`
- [X] T019 [P] [US2] Integration test for method selection logic (Zero-inflated vs Non-normal) in `tests/integration/test_method_selection.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement data distribution checks in `code/analysis.py` (Shapiro-Wilk test, zero proportion calculation) **AND check for zero-inflation (zeros > 30% OR Shapiro-Wilk p < 0.05)**. **DEPENDS ON COMPLETION OF T014b (filtered_data.parquet).**
- [X] T020a [US2] **ATOMIC**: If T020 detects zero-inflation, mark path as 'ZINB' and skip CLR transformation. If not zero-inflated, check for compositionality. **Output: `data/metadata/distribution_flags.json`.** **DEPENDS ON T020.**
- [X] T022a [US2] Implement compositionality detection in `code/transform.py` and integrate `sparcc`/`spiecaei` libraries if available (Note: If import fails, log warning and skip compositionality check; fallback to CLR transformation). **Output: `data/metadata/compositionality_flag.json`.** **DEPENDS ON T014b.** **MUST run BEFORE T021 to inform method selection.**
- [X] T021 [US2] Implement `select_correlation_method()` in `code/analysis.py` with explicit decision logic **strictly following FR-002**: 1) If zero-inflation (zeros > 30% OR Shapiro-Wilk p < 0.05) -> **ZINB/Hurdle**, 2) Else if non-normal (Shapiro-Wilk p < 0.05) -> **Spearman**, 3) Else -> **Pearson**. **MUST read `data/metadata/compositionality_flag.json` from T022a. If compositionality is detected AND T022a failed (import error), select Spearman (safe fallback) or halt. If compositionality is detected and T022a succeeded, select 'CLR' as the transformation method.** **Unit of analysis: per-taxon for zero-inflation, global for Shapiro-Wilk.** **Returns a dict with keys: `method_name`, `params`, `reason`, `requires_clr`.** **Note: This task SELECTS the method; it does NOT execute the transformation. Execution of CLR is handled by T022.** **DEPENDS ON T020, T020a, T022a, T021f.**
- [X] T023 [US2] Implement ZINB/Hurdle model fitting in `code/analysis.py` using `statsmodels` for zero-inflated cases
- [X] T024 [US2] Implement Spearman and Pearson correlation functions in `code/analysis.py`
- [X] T025 [US2] Implement Benjamini-Hochberg FDR correction in `code/analysis.py` to adjust p-values (q ≤ 0.05) **and verify the threshold application** before outputting the full correlation matrix (including raw and adjusted p-values) to `data/results/correlation_matrix.json`. **Addresses missing producer for T030.**
- [X] T022 [US2] Implement CLR transformation in `code/transform.py` using `scikit-bio` for compositional data handling (fallback if SparCC unavailable). **CONDITIONAL: Only run if T021 selects a method requiring compositional correction AND T020a confirms data is NOT zero-inflated (CLR fails on zeros).** **DEPENDS ON T021, T022a, T020a.** **Output: `data/processed/processed_data.parquet`.** **Moved to Phase 4 to complete US2 unit.**
- [X] T027 [US2] Extend pipeline orchestration in `code/main.py` to import and call US2 modules **without modifying T015 logic**; T027 relies on T015's base orchestration functions

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4.5: Integration & Reporting (Cross-Story)

**Purpose**: Integrate US1 and US2 artifacts into final report and verify cross-story consumption.

- [X] T026a [P] [Integration] Implement `enforce_associational_framing()` in `code/report.py` to scan generated text for causal language ('causes', 'leads to', 'effect') and replace with 'associational with', 'correlates with', 'relationship'. **Addresses FR-004.** **DEPENDS ON T025.**
- [X] T026 [P] [Integration] Implement report generation in `code/report.py` to consume US1 and US2 artifacts and produce the final report. **DEPENDS ON T026a (Associational Framing), T022 (if compositional), T025, T016.** **DEPENDS ON `data/processed/processed_data.parquet` (output of T022 or T014b).**

### Tests for Integration (Phase 4.5)

- [X] T026b [P] [US-2] **Integration Test for Orchestration**: Verify T026 execution is blocked until T016 and T025 artifacts exist. **DEPENDS ON T026. This task verifies the orchestration logic in main.py that enforces the blocking.**

**Checkpoint**: US2 Transformation and Reporting complete

---

## Phase 5: User Story 3 - Threshold Sensitivity, Collinearity Diagnostics, and Power Analysis (Priority: P3)

**Goal**: Perform sensitivity analysis on thresholds, calculate VIF/collinearity diagnostics, and validate sample size power.

**Independent Test**: Run diagnostics on data with known collinearity; verify VIF calculation and linear dependence flag. Verify power analysis flags "Underpowered" if N < required.

**⚠️ SERIALIZATION NOTE**: US3 tasks depend on correlation results from US2. **US3 execution is strictly blocked until US2 completion (specifically T020-T025 output).**

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Contract test for diagnostics output in `tests/contract/test_diagnostics_schema.py`. **Must verify existence and structure of `data/results/correlation_matrix.json` (output of T025) as a required input artifact.** **Addresses missing producer verification for T030.**
- [X] T029 [P] [US3] Integration test for collinearity detection (perfect multicollinearity) in `tests/integration/test_collinearity.py`

### Implementation for User Story 3

- [X] T021h [US3] **ATOMIC**: Implement dynamic "Perfect Multicollinearity" detection in `code/diagnostics.py` by performing a **matrix rank check on the actual predictor matrix** of the loaded dataset. **Output: `data/metadata/dynamic_collinearity_map.json`** containing pairs found to be perfectly collinear in the *current data instance*. **DEPENDS ON T014b (filtered_data.parquet).** **Distinct from T021f (static config).**
- [X] T030 [US3] Implement sensitivity analysis in `code/diagnostics.py` to re-run significance at p < 0.01, p < 0.05, p < 0.10, **calculate the percentage change in significant findings**, and report the variation. Read correlation results from `data/results/correlation_matrix.json` and append results to `data/results/sensitivity_analysis.json` with keys: `threshold`, `count`, `percent_change`. **DEPENDS ON US2 COMPLETION (Correlation Results). NOT PARALLEL WITH US2 EXECUTION.**
- [X] T030a [US3] Implement stability metric calculation in `code/diagnostics.py` to compute the **coefficient of variation** of significant findings from `data/results/sensitivity_analysis.json` (output of T030), **explicitly designating this value as the 'stability metric' required by SC-002**, and store in `data/results/stability_metrics.json`. **Depends on T030.** **PASS/FAIL: If CV < 0.10, mark 'STABLE'; else 'UNSTABLE'.**
- [X] T031 [US3] Implement VIF calculation in `code/diagnostics.py` for multivariate predictors (flag VIF > 5). **Merge results from T021f (static config) and T021h (dynamic data check)**. **Skip VIF calculation for any pair flagged as 'Perfect Multicollinearity' in EITHER map.** Output to `data/results/collinearity_report.json`. **DEPENDS ON T021f AND T021h AND T025.**
- [X] T033 [US3] Implement power analysis in `code/diagnostics.py` to calculate minimum N for r ≥ 0.3, power ≥ 0.80, α = 0.05
- [X] T034 [US3] Integrate diagnostics into `code/main.py` and append results to final report
- [X] T035 [US3] Update `code/report.py` to include "Power Limitation" warnings if N is insufficient. **Explicitly outputs 'Power Limitation' to final report and `data/results/power_analysis.json` with 'status' field ('Underpowered' or 'Adequate') and 'minimum_N_required' field if N < required. This satisfies SC-005 traceability.** **Addresses SC-005 traceability.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T036 [P] Documentation updates in `docs/` and `README.md`
- [X] T037 Code cleanup and refactoring
- [X] T038 Performance optimization across all stories (ensure < 6h runtime)
- [X] T039 [P] Additional unit tests in `tests/unit/`
- [X] T040 Run quickstart.md validation

---

## Phase N+1: Real-Data Integration & Validation (Priority: P4)

**Goal**: Transition from synthetic validation to real-world data ingestion and verify pipeline robustness against actual biological data.

**Independent Test**:
1. **For T051a (Fetch Implementation)**: Verify that the fetcher code is written for a specific ID.
2. **For T051b (Fetch Execution)**: Run the pipeline with a real dataset (if available) or trigger the fetch; **verify that the system halts execution with a specific error message citing the missing source and does NOT fallback to synthetic data.**
3. **For T051c (Documentation)**: Verify that `docs/real_data_impossibility_report.md` exists and documents the impossibility of finding a single dataset or proposes a multi-cohort strategy.
4. **For T056 (Validation Script)**: Run T056 and verify `data/results/integrity_verification.json` contains specific error types (e.g., MissingDataError) and does not contain synthetic data fallback logs.

**⚠️ NOTE**: Phase N+1 tasks are blocked until Phase N+2 (Data Availability) identifies a dataset or confirms impossibility.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [X] T041 [P] [US4] Contract test for real-data ingestion in `tests/contract/test_real_data_ingestion.py`
- [X] T042 [P] [US4] Integration test for real-data pipeline execution in `tests/integration/test_real_data_pipeline.py`

**Checkpoint**: Pipeline is validated against both synthetic and real data (if available), ensuring robustness and readiness for production use with real-world datasets.

---

## Phase N+2: Data Availability & Source Verification (Priority: P5)

**Goal**: Address the critical gap of missing verified real-world datasets containing both modalities. Establish a rigorous process for sourcing, validating, and integrating real data to transition from a "Pipeline Validation Study" to a biological discovery study. **CRITICAL: Only single-source datasets (both modalities for same subjects) are valid.**

**Independent Test**: Successfully identify, document, and validate at least one real-world dataset (or a verified proxy) that contains both modalities, or formally document the impossibility of such a dataset and transition to Synthetic Validation mode.

- [X] T049 [US5] Conduct a systematic literature and database search for public datasets containing paired gut metagenomics and polysomnography/actigraphy data. **Output: `docs/real_data_sources.md` (updated with findings).**
- [X] T049a [US5] **ATOMIC: Identify Candidates**. Execute T049 and output a specific list of candidate dataset IDs (e.g., 'NCBI PRJNA...', 'GEO GSE...') OR 'None Found' to `data/metadata/candidate_datasets.json`. **Schema: `{candidates: [{source: string, id: string, url: string, feasibility_score: float}] | {status: 'None Found'}}`.** **This task MUST output a specific ID or 'None Found' to make T051 executable.** **Feasibility Score Formula: score = (completeness * weight_completeness) + (privacy * weight_privacy), where completeness is % of required variables and privacy is high if public, low if restricted.**
- [X] T050 [US5] Evaluate identified datasets for data quality, variable completeness, and privacy constraints. **Output: `data/metadata/dataset_evaluation_matrix.csv` with columns [dataset_id, source_url, completeness_score, privacy_status, feasibility_score].**
- [X] T051a [US5] **ATOMIC: Fetch Implementation**. **IF** T049a found a valid dataset with `feasibility_score >= 0.8`, implement specific, verified data fetcher in `code/ingest.py` for that ID. **Primary Target: GEO GSE (Microbiome) + SleepDataProxy (Sleep Metrics).** **Output: `code/ingest.py` with fetcher logic.** **DEPENDS ON T049a (Dataset Found = True).** **Explicitly implements FR-001 for the specific ID.**
- [X] T051b [US5] **ATOMIC: Fetch Execution**. Execute the fetcher from T051a. **Output: `data/raw/[dataset_name].csv`, `data/results/dataset_validation_report.json`, and `data/results/fetch_attempt_report.json`.** **DEPENDS ON T051a.** **Logic: 1. Fetch -> 2. If Fail (No Data): Halt & Generate `docs/real_data_impossibility_report.md` -> 3. If Success & Partial (missing specific sleep stages): Log Warning & Proceed with available metrics (Reduced Scope) -> 4. If Success & Complete: Proceed.** **This task enforces FR-001 without allowing a 'SYNTHETIC_ONLY' bypass.**
- [X] T053a [US5] **ATOMIC: Update Plan/Spec (Documentation)**. Update `plan.md` Section 1.1 and `spec.md` Status to explicitly state: "Current scope is Pipeline Validation Study. FR-001 (Real Data Ingestion) is BLOCKED pending dataset availability." **Output: Updated plan.md and spec.md.** **DEPENDS ON T051b (Data Unavailable state).**
- [X] T053b [US5] **ATOMIC: Update Constitution Check (Documentation)**. Update Constitution Check table in `plan.md` to mark FR-001 as 'Blocked' rather than 'PASS'. **Output: Updated Constitution Check table.** **DEPENDS ON T053a.**
- [X] T053c [US5] **ATOMIC: Execute Synthetic Validation**. Run the full pipeline in `--synthetic` mode to validate the logic after the plan is updated to 'Synthetic Only'. **Output: `data/results/synthetic_validation_report.json`.** **DEPENDS ON T053a. MUST verify that T055 (Real Data Gate) is bypassed by `--synthetic` flag.**
- [X] T054a [US5] **ATOMIC: Define Comparison Framework**. Define the framework for `real_vs_synthetic_comparison_report.json` (columns, metrics, method) **without executing it**. **Schema: `{metrics: [{name: string, formula: string, target: number}], method: string}`. Output: `data/results/comparison_framework.json`.** **DEPENDS ON T053a.**
- [X] T055 [US6] **REAL DATA GATE**: Implement a strict "No-Synthetic-Fallback" gate in `code/main.py` that checks for the existence of real data artifacts before any analysis step. **Conditional**: If `--real-data` flag is set and real data is missing, raise `SystemExit` with "CRITICAL: Real data source missing. Pipeline halted to prevent fabrication." If `--synthetic` flag is set (default for Phase N+2), allow execution. **This task ensures T051b's error handling is enforced at the orchestration level. MUST run AFTER T051b to verify no synthetic fallback occurred.**
- [X] T056 [US6] **REAL DATA VERIFICATION**: Add a post-execution verification script in `code/verify_data_integrity.py` that scans the `data/` directory for any synthetic placeholders generated during a failed real-data run. **Definition**: Files in `data/` matching `synthetic_*.csv` or containing a specific checksum marker defined in `data/metadata/synthetic_data_manifest.json`. If found and `--real-data` flag was set, fail CI with "Fabrication Detected". **Output: `data/results/integrity_verification.json`.** **DEPENDS ON T055.**
- [X] T057 [US6] Update `docs/real_data_sources.md` to include a "Data Availability Status" section that explicitly states "NO VERIFIED REAL DATASET AVAILABLE" if T049/T050 yield no results, preventing accidental assumption of data existence.

**Checkpoint**: A verified real-data source is identified, integrated, and the pipeline has been validated against it, or a formal plan for synthetic validation is established and documented.

---

## Phase N+3: Execution Safety & Compute Optimization (Priority: P6)

**Goal**: Ensure the pipeline respects CPU/GPU constraints and handles large datasets via strict RAM limits without fabrication or runner changes.

**Independent Test**: Verify that a dataset too large for RAM triggers a hard failure with a clear error message, forcing the user to downsample.

- [X] T058 [P] [US6] **RAM PRE-CHECK**: Implement strict RAM check in `code/main.py` that estimates RAM usage based on dataset size (N subjects × taxa count). **Formula**: `Estimate (GB) = (N_subjects * N_taxa * byte_size_per_taxon) / e`. **Logic**: If estimated usage <= 6GB, return status 'OK'. If 6GB < estimated usage <= 7GB, return status 'STREAM'. If estimated usage > 7GB, return status 'FAIL'. **Output**: `data/metadata/compute_strategy.json` indicating 'OK', 'STREAM', or 'FAIL'. **Addresses FR-007 and Rule: "Large real datasets: STREAM the real data; never shrink to a toy."**
- [X] T059 [US6] **STREAMING ENABLEMENT**: Implement streaming mode logic in `code/main.py` that activates if T058 returns status 'STREAM'. **Logic**: If status is 'STREAM', switch to chunked processing (streaming=True). **Output**: `data/metadata/compute_strategy.json` indicating 'STREAMING'. **DEPENDS ON T058.**
- [X] T059a [US6] **STREAMING LOADER IMPLEMENTATION**: Implement the chunked data loader in `code/ingest.py` using `pandas.read_csv(..., chunksize=...)` to accumulate data in `data/processed/filtered_data.parquet` without exceeding RAM. **Output**: `data/processed/filtered_data.parquet` (via chunked accumulation). **DEPENDS ON T058, T059.** **This task provides the mechanism for T064.**
- [X] T060 [US6] **RAM FAIL-FAST**: Implement hard halt logic in `code/main.py` that triggers if T058 returns status 'FAIL'. **Logic**: If status is 'FAIL', raise `SystemExit` with "CRITICAL: Dataset too large for standard runner (GB limit). Please downsample or use a smaller dataset." **Output**: `data/metadata/compute_strategy.json` indicating 'RAM_CHECK_FAILED'. **Addresses FR-007 and Rule: "Large real datasets: STREAM the real data; never shrink to a toy."** **Note: This is a FAIL-FAST on the standard runner, not an execution on a different runner. Replaces GPU offload logic to comply with 'No GPU' constraint.**
- [X] T062 [US6] Implement a "No-Synthetic-Fallback" assertion in `code/data_generator.py` that checks if `--real-data` flag is set. If set and real data is missing, raise `SystemExit` with "FABRICATION PREVENTED: Real data required but missing." **Addresses Rule: "The loader must FAIL LOUDLY, never fall back to synthetic."**
- [X] T063 [US6] Add a task to document the streaming and RAM fail strategy in `docs/compute_strategy.md`, including examples of when each mode is triggered and the expected performance characteristics.
- [X] T063a [US6] **VERIFY 6-HOUR CONSTRAINT**: Implement a test script in `code/verify_streaming_performance.py` that simulates a dataset with N=999 (max valid size) using the 'Large Proxy' from T070 and verifies that the streaming logic (T059) and RAM fail logic (T060) keep the total runtime < 6 hours on a standard CPU runner. **Output**: `data/results/streaming_performance_report.json` with pass/fail status. **Addresses FR-007 for large data scenarios.** **DEPENDS ON T058, T059, T060, T070.** **Note: Uses N=999 to comply with Assumption-001.**

**Checkpoint**: The pipeline is robust against large datasets, respects compute constraints, and strictly prevents synthetic data fabrication.

---

## Phase N+4: Real-Data Execution & GPU Offload Verification (Priority: P7)

**Goal**: Execute the pipeline on a real dataset (if available) or a verified large-sample proxy, ensuring streaming and RAM logic functions correctly without fabrication.

**Independent Test**:
1. **For T064 (Streaming)**: Run the pipeline on a dataset > 6GB (simulated or real) and verify `data/processed/` is populated via chunked processing, not a single large load.
2. **For T071 (6-Hour Stress Test)**: Run the full pipeline on a large dataset and verify execution time < 6 hours.

- [X] T070 [US6] **LARGE PROXY GENERATOR**: Create a script in `code/generate_large_proxy.py` that generates a verified large proxy dataset (N=999) using the real data schema (from T004a/b) but with synthetic values. **Logic**: Ensure the proxy is distinct from T006 (Unit Test Generator) and is explicitly marked as a 'Large Proxy' for stress testing. **Output**: `data/raw/large_proxy.csv`. **DEPENDS ON T004a, T004b.** **Note: Uses N=999 to comply with Assumption-001.**
- [X] T064 [US6] **STREAMING EXECUTION TEST**: Create a test runner script in `code/run_streaming_test.py` that loads a large real dataset (or a verified large proxy from T070) using the loader from T059a. **Logic**: Verify that memory usage stays < 7GB during execution and that `data/processed/filtered_data.parquet` is generated via chunked accumulation (T059a). **Output**: `data/results/streaming_execution_report.json` with memory peaks and chunk counts. **DEPENDS ON T058, T059, T059a, T070.**
- [X] T066 [US6] **REAL DATA INTEGRATION RUN**: If T051b succeeded (real data found), execute the full pipeline (US1-US3) on the real dataset using the streaming logic (T059) and RAM fail logic (T060) as needed. **Output**: `data/results/real_data_analysis_report.json` and the final `paper/` artifacts. **DEPENDS ON T051b (SUCCESS), T064, T065.**
- [X] T067 [US6] **FABRICATION AUDIT**: Run T056 (Integrity Verification) on the output of T066. **Logic**: Confirm `data/results/integrity_verification.json` shows "PASS" and no synthetic artifacts are present. **Output**: `data/results/fabrication_audit_report.json`. **DEPENDS ON T066, T056.**

**Checkpoint**: The pipeline has been successfully executed on real data (or a verified large proxy) with streaming and RAM logic, and the results have passed a fabrication audit.

---

## Phase N+5: Data Source Resolution & Pipeline Re-Enablement (Priority: P8)

**Goal**: Resolve the "No Verified Real Dataset" blocker identified in Phase N+2 by enforcing single-source data requirements and re-enabling the full analysis on real data if found.

**Independent Test**:
1. **For T069**: Verify that the pipeline executes successfully on the harmonized data (if found) or transitions to Synthetic Validation (if not found).
2. **For T071**: Verify that the pipeline executes on a large dataset (N=999) and completes within 6 hours.

- [X] T069 [US5] **RE-ENABLE REAL DATA PIPELINE**: Modify `code/main.py` and `code/ingest.py` to accept the validated real data (from T068 - if it existed, but since it was removed, this task now checks for the presence of a single-source dataset identified in T051b). If T051b returns 'INVALID' or 'None Found', trigger T053c (Synthetic Validation). **Output**: `data/results/real_data_validation_report.json` confirming successful ingestion or transition to synthetic mode. **DEPENDS ON T051b.**
- [X] T070 [US5] **VALIDATION OF REAL-DATA RESULTS**: Run the full analysis pipeline (US1-US3) on the real dataset (if found). Compare the resulting correlation patterns against the synthetic baseline (from T053c) to ensure no statistical artifacts were introduced. **Output**: `data/results/real_vs_synthetic_comparison.json` and an updated `paper/` draft. **DEPENDS ON T069.**
- [X] T071 [US6] **6-HOUR STRESS TEST**: Execute the full pipeline (US1-US3) on a large dataset (real or T070 proxy with N=999) to verify execution time < 6 hours. **Output**: `data/results/6_hour_stress_test_report.json` with timing evidence. **DEPENDS ON T064, T069.** **Addresses SC-004.** **Note: Uses N=999 to comply with Assumption-001.**

**Checkpoint**: The project transitions from a "Pipeline Validation Study" to a "Biological Discovery Study" using real, single-source data, with all gates passed and results validated.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **Strict Execution Serialization**:
 - **US1 (Phase 3)** must complete and produce artifacts (`filtered_data.parquet`, `timing_evidence.json`) before **US2 (Phase 4)** can execute.
 - **US2 (Phase 4)** must complete and produce artifacts (correlation results) before **US3 (Phase 5)** can execute.
 - **Parallel Code Editing**: While code files can be edited in parallel by different developers, the *runtime execution* of the pipeline is strictly serialized by data flow. Developers must be aware that their code changes will not run until the preceding stage's artifacts are generated.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (specifically T014b and T016 artifacts) for execution
- **User Story 3 (P3)**: Depends on US2 completion (specifically correlation results) for execution
- **User Story 4 (P4)**: Depends on US1, US2, and US3 completion for full pipeline integration with real data
- **User Story 5 (P5)**: Depends on the completion of the pipeline validation (US1-US3) and is a prerequisite for any meaningful real-data analysis (US4 T051/T052)
- **User Story 6 (P6)**: Depends on T043 (Real Data Loader) and T049 (Data Search) to enforce safety constraints during the transition to real data.
- **User Story 7 (P7)**: Depends on T058-T063 (Compute Safety) and T051 (Data Availability) to execute the final real-data analysis.
- **User Story 8 (P8)**: Depends on T068 (Real-Data Search) and T071 (Stress Test) to re-enable the pipeline with real data.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Integration test for missing variable error handling in tests/integration/test_missing_variable.py"

# Launch all models for User Story 1 together:
Task: "Implement validate_variables() in code/ingest.py"
Task: "Implement load_data() in code/ingest.py"
Task: "Implement outlier detection logic in code/ingest.py"
Task: "Implement data filtering step in code/ingest.py"
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
 - Developer A: User Story 1 (Code editing AND Execution)
 - Developer B: User Story 2 (Code editing ONLY; Execution blocked until A finishes US1)
 - Developer C: User Story 3 (Code editing ONLY; Execution blocked until B finishes US2)
3. **Execution Flow**: US1 must complete and produce artifacts before US2 can run. US2 must complete before US3 can run. Code editing can proceed in parallel, but the pipeline execution is strictly serialized by data flow.

---

## Notes

- [P] tasks = different files, no dependencies (except explicit dependencies noted in task description)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Execution Note**: While code files (e.g., `code/main.py`) may be edited by multiple developers in parallel, the *runtime execution* of US2 and US3 logic is strictly dependent on the successful completion and artifact generation of US1 and US2 respectively. The "Parallel Opportunities" refer to code development, not pipeline execution. US2 execution is blocked by T014b and T016. US3 execution is blocked by US2 completion.
- **T030 Specific Note**: T030 is marked [P] only relative to other US3 tasks (T031-T035). It is **NOT** parallel with US2 execution.
- **T026 Specific Note**: T026 is **NOT** parallel with US1 execution due to dependency on T016.
- **T010 Specific Note**: T010 tests schema definition existence, not validation logic implementation.
- **T021/T021b/T022a Ordering Note**: Tasks are ordered T020 -> T022a -> T021 -> T022 to ensure Method Selection (T021) is driven strictly by Distribution Checks (T020) AND Compositionality (T022a), preserving the FR-002 priority tree. T022 (Transformation) runs AFTER T021. T021b (config) must be completed before T021c. T021c is now in Phase 2. **T021f (Dynamic Check) is added to ensure T031 has complete collinearity data.** **T021 now selects method; T022 executes transformation if selected.**
- **Real Data Constraint**: The project currently operates under a "Pipeline Validation Study" scope due to the lack of verified real-world data. T049-T054 are critical to transitioning to a biological discovery study. The synthetic data generator (T006) is a temporary placeholder for this phase.
- **Data Loader Integrity**: The real data loader (T051a/T051b) MUST NOT fall back to synthetic data if the real fetch fails. It must fail loudly, allowing the execution stage to discover and resolve the data source issue. This is a hard constraint to prevent fabrication.
- **Synthetic Data Integrity**: Tasks T006d and T006c generate a `synthetic_data_manifest.json` artifact, NOT a Chain-of-Custody log, to avoid violating Constitution Principle VI which applies only to actual biological samples. **Explicitly differentiated from biological logs.**
- **Phase N+3 Constraint**: Tasks T055-T057 are mandatory safety checks. The pipeline must NEVER proceed to analysis if real data is requested but missing. Any attempt to bypass this (e.g., via synthetic fallback) is a critical failure.
- **T053 Specific Note**: T053a, T053b, and T053c are mandatory to update the plan and spec to reflect the current "Synthetic Only" scope (if no data found) and execute the validation. T053c ensures the pipeline runs in synthetic mode after the plan update. **T053d explicitly handles the 'Missing Data' state.**
- **T049a Specific Note**: T049a MUST output a specific dataset ID or 'None Found'. If 'None Found', T051b is skipped and T051c is executed.
- **T054 Specific Note**: T054 is split into T054a (Framework), T054b (Execute if data found), and T054c (Document if data not found) to break circular dependencies.
- **T055 Specific Note**: T055 is a hard gate. If `--real-data` flag is set and T051a/T051b both fail to find real data, T055 MUST fail the build. This ensures FR-001 is not silently relaxed.
- **T056 Specific Note**: T056 verifies that no synthetic data was used when real data was expected. This ensures the integrity of the real-data analysis.
- **T058-T063 Specific Note**: These tasks address the compute feasibility and streaming rules. T058 implements a three-state RAM check (OK/STREAM/FAIL). T059 enables streaming for 'STREAM'. T060 halts for 'FAIL'. T062 enforces the "fail loud" rule for real data. These are mandatory for compliance with the "Compute feasibility" and "Large real datasets" rules. **T063a explicitly verifies the 6-hour constraint for these scenarios.**
- **T064-T067 Specific Note**: These tasks (Phase N+4) are the final execution steps to validate the pipeline on real data with streaming and RAM logic. T064 validates streaming. T066 executes the full real-data analysis. T067 performs the final fabrication audit. **T064 and T065 are prerequisites for T066.**
- **T070 Specific Note**: T070 generates a 'Large Proxy' for stress testing, distinct from T006 (Unit Test Generator), to avoid violating the 'No Synthetic Fallback' constraint in Phase N+4. **Uses N=999 to comply with Assumption-001.**
- **T071 Specific Note**: T071 explicitly tests the 6-hour limit on a large dataset (N=999), satisfying SC-004.
- **T071 Specific Note**: T071 is the final validation of the 6-hour constraint on a large dataset (real or proxy). It depends on T064 (streaming) and T069 (real data ingestion). It ensures SC-004 is met for large-scale scenarios. **Uses N=999 to comply with Assumption-001.**

---

## Phase N+6: GPU Offload Verification & Scaled Real-Data Execution (Priority: P9)

**Goal**: Resolve the "No Verified Real Dataset" blocker identified in Phase N+2 by enforcing single-source data requirements and re-enabling the full analysis on real data.

**Independent Test**:
1. **For T069**: Verify that the pipeline executes successfully on the real data (if found) or transitions to Synthetic Validation (if not found).
2. **For T071**: Verify that the pipeline executes on a large dataset (N=999) and completes within 6 hours.

- [X] T069 [US5] **RE-ENABLE REAL DATA PIPELINE**: Modify `code/main.py` and `code/ingest.py` to accept the validated real data (from T051b) as a valid "Real Data" source. Remove the "No Real Data" halt condition if this specific validated artifact is present. If T051b returns 'INVALID' or 'None Found', trigger T053c (Synthetic Validation). **Output**: `data/results/real_data_validation_report.json` confirming successful ingestion or transition to synthetic mode. **DEPENDS ON T051b.**
- [X] T070 [US5] **VALIDATION OF REAL-DATA RESULTS**: Run the full analysis pipeline (US1-US3) on the real dataset (if found). Compare the resulting correlation patterns against the synthetic baseline (from T053c) to ensure no statistical artifacts were introduced. **Output**: `data/results/real_vs_synthetic_comparison.json` and an updated `paper/` draft. **DEPENDS ON T069.**
- [X] T071 [US6] **6-HOUR STRESS TEST**: Execute the full pipeline (US1-US3) on a large dataset (real or T070 proxy with N=999) to verify execution time < 6 hours. **Output**: `data/results/6_hour_stress_test_report.json` with timing evidence. **DEPENDS ON T064, T069.** **Addresses SC-004.** **Note: Uses N=999 to comply with Assumption-001.**

**Checkpoint**: The project transitions from a "Pipeline Validation Study" to a "Biological Discovery Study" using real, single-source data, with all gates passed and results validated.