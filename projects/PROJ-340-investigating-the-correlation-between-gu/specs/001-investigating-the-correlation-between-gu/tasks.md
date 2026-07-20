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

- [X] T004a Define predictor schema (taxa) in `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml`
- [X] T004b Define outcome schema (sleep metrics) in `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml`
- [X] T005a Define output schema (CorrelationResult structure) in `specs/001-gut-microbiome-sleep-architecture/contracts/output.schema.yaml`
- [X] T006 [P] Implement deterministic synthetic data generator in `code/data_generator.py` (mock metagenomic counts + sleep metrics) to validate pipeline logic without real data
- [X] T006a [P] Pin random seeds in `code/data_generator.py` (e.g., `np.random.seed()`, `random.seed()`) to ensure reproducibility per Constitution Principle I
- [X] T006b [P] Pin random seeds in `code/analysis.py` and `code/diagnostics.py` (e.g., ZINB initialization, bootstrapping) to ensure reproducibility per Constitution Principle I
- [X] T006d [P] Define `synthetic_data_manifest_schema.yaml` in `specs/001-gut-microbiome-sleep-architecture/contracts/` to satisfy Constitution Principle I (Reproducibility) for synthetic data. **Explicitly excludes 'Chain-of-Custody' fields to differentiate from biological sample logs. This schema is distinct from biological provenance logs.**
- [X] T006e [P] Update constitution check logic in `code/reference_validator.py` or `code/constitution_checker.py` to validate against `synthetic_data_manifest_schema.yaml`. **DEPENDS ON T006d.**
- [X] T006c [P] Generate synthetic "manifest" log file in `data/metadata/synthetic_data_manifest.json` using the schema defined in T006d (Note: This is a placeholder artifact for the 'Pipeline Validation Study' scope; no real biological samples exist, so no CoC log is generated. **Renamed from T006c to reflect new schema and avoid CoC confusion.**)
- [X] T007 Create base data loading utilities in `code/ingest.py` (CSV/TSV reader, column validation)
- [X] T008 Configure CI workflow in `.github/workflows/analysis.yml` to run on `ubuntu-latest` with CPU/GB RAM limits
- [X] T009 Setup environment configuration management (`.env` template, `requirements.txt`)
- [X] T009a [P] Define Reference-Validator Agent schema in `code/reference_validator.py`
- [X] T009b [P] Implement Reference-Validator Agent logic and integrate gate in CI (`.github/workflows/analysis.yml`) to fail build if citations are unverified (Note: Gate operates in 'Logic Only' mode for synthetic data as per Plan's 'Verified Accuracy' strategy).
- [X] T021b [P] Define configuration list of definitionally related taxa pairs in `data/config/definitionally_related_pairs.yaml` to support collinearity detection.
- [X] T021c [P] Define config schema for collinearity pairs in `data/config/definitionally_related_pairs.yaml`. **Split from T021c_old.**
- [X] T021d [P] Implement "Perfect Multicollinearity" detection algorithm in `code/diagnostics.py` (static analysis of T021b config). **Split from T021c_old. DEPENDS ON T021c.**
- [X] T021e [P] Generate output artifact `data/metadata/collinearity_map.json` using the algorithm from T021d. **Split from T021c_old. DEPENDS ON T021d.**

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

- [X] T012 [US1] Implement `validate_variables()` in `code/ingest.py` to check for required predictors (taxa) and outcomes (sleep metrics) defined in `dataset.schema.yaml`, calculate the percentage of required variables successfully loaded, **and include the list of missing variables in the output JSON**, and output the metric to `data/results/variable_load_metrics.json`. **Addresses SC-001 traceability gap. MUST run against REAL data if available (see T051a/T056), otherwise synthetic.**
- [X] T013 [US1] Implement `load_data()` in `code/ingest.py` to read CSV/TSV, consume the percentage metric from `data/results/variable_load_metrics.json` (output of T012), **persist the check result (including the percentage and list of missing variables) to `data/results/variable_load_metrics.json`**, and **halt execution with `sys.exit(1)`** if the percentage is < 100% with specific error message (e.g., "Variable 'SWS duration' is missing") per FR-001. This ensures SC-001 is met even on partial failure.
- [X] T014 [US1] Implement outlier detection logic in `code/ingest.py` (IQR method: >1.5x IQR above 75th or <1.5x below 25th) and flag exclusion
- [X] T014b [US1] Implement data filtering step in `code/ingest.py` to remove flagged outliers and output the filtered dataset to `data/processed/filtered_data.parquet`. **DEPENDS ON T014.**
- [X] T014c [US1] Register the checksum for `data/processed/filtered_data.parquet` in `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml` per Constitution Principle III. **DEPENDS ON T014b.**
- [X] T015 [US1] Implement pipeline orchestration in `code/main.py` to sequence ingestion, validation, and execution
- [X] T016 [US1] Implement execution timing check in `code/main.py` to log start/end times, assert < 6 hours, and **generate timing evidence artifact (JSON log at `data/results/timing_evidence.json`)** to satisfy SC-004. **MUST run against REAL data if available (see T051a/T056), otherwise synthetic.**
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
- T026 depends on `data/results/timing_evidence.json` (output of T016). **Report generation (T026) is strictly blocked until T016 completes.**
- T027 depends on US2 completion.
- **T021c/T021d/T021e (Collinearity) MUST be available before T020 and T021** as a pre-check.
- **T020 (Distribution Checks) MUST precede T021 (Method Selection) and T022a (Compositionality).** This ensures FR-002 logic uses RAW data distribution.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for correlation output schema in `tests/contract/test_output_schema.py`
- [X] T019 [P] [US2] Integration test for method selection logic (Zero-inflated vs Non-normal) in `tests/integration/test_method_selection.py`

### Implementation for User Story 2

- [X] T020 [US2] Implement data distribution checks in `code/analysis.py` (Shapiro-Wilk test, zero proportion calculation) **DEPENDS ON COMPLETION OF T014b (filtered_data.parquet) AND T021e (collinearity map).**
- [X] T021 [US2] Implement `select_correlation_method()` in `code/analysis.py` with explicit decision logic **strictly following FR-002**: 1) If zero-inflation (zeros > 30% OR Shapiro-Wilk p < 0.05) -> **ZINB/Hurdle**, 2) Else if non-normal (Shapiro-Wilk p < 0.05) -> **Spearman**, 3) Else -> **Pearson**. Compositionality detection (T022a) is a secondary check applied only if the primary method is valid. **Returns a dict with keys: `method_name`, `params`, `reason`.** **DEPENDS ON T020, T021e.**
- [X] T023 [US2] Implement ZINB/Hurdle model fitting in `code/analysis.py` using `statsmodels` for zero-inflated cases
- [X] T024 [US2] Implement Spearman and Pearson correlation functions in `code/analysis.py`
- [X] T025 [US2] Implement Benjamini-Hochberg FDR correction in `code/analysis.py` to adjust p-values (q ≤ 0.05) and **output the full correlation matrix (including raw and adjusted p-values) to `data/results/correlation_matrix.json`**. **Addresses missing producer for T030.**
- [X] T027 [US2] Extend pipeline orchestration in `code/main.py` to import and call US2 modules **without modifying T015 logic**; T027 relies on T015's base orchestration functions

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4.5: Integration & Reporting (Cross-Story)

**Purpose**: Integrate US1 and US2 artifacts into final report and verify cross-story consumption.

- [X] T022a [US2] Implement compositionality detection in `code/transform.py` and integrate `sparcc`/`spiecaei` libraries if available (Note: If import fails, log warning and skip compositionality check; fallback to CLR transformation). **Output: `data/metadata/compositionality_flag.json`.** **DEPENDS ON T014b AND T021 (Method Selection).** **Moved after T021 to ensure FR-002 priority tree is respected.**
- [X] T022 [US2] Implement CLR transformation in `code/transform.py` using `scikit-bio` for compositional data handling (fallback if SparCC unavailable). **CONDITIONAL: Only run if T021 selects a method requiring compositional correction OR if T022a flags compositionality.** **DEPENDS ON T021, T022a.**
- [X] T026a [P] [Integration] Implement integration test in `tests/integration/test_report_generation.py` to verify that `code/report.py` (T026) correctly consumes `data/results/timing_evidence.json` (US1) and `data/results/correlation_matrix.json` (US2) and produces a valid final report. **Addresses missing test for T026.**
- [X] T026b [P] [Integration] Verify T026 execution is blocked until T016 and T025 artifacts exist. **DEPENDS ON T026. This task verifies the orchestration logic in main.py that enforces the blocking.**
- [X] T026 [P] [Integration] Implement report generation in `code/report.py` to consume US1 and US2 artifacts and produce the final report. **DEPENDS ON T022 (if compositional), T025, T016.**

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

- [X] T030 [US3] Implement sensitivity analysis in `code/diagnostics.py` to re-run significance at p < 0.01, p < 0.05, p < 0.10, **calculate the percentage change in significant findings**, and report the variation. Read correlation results from `data/results/correlation_matrix.json` and append results to `data/results/sensitivity_analysis.json` with keys: `threshold`, `count`, `percent_change`. **DEPENDS ON US2 COMPLETION (Correlation Results). NOT PARALLEL WITH US2 EXECUTION.**
- [X] T030a [US3] Implement stability metric calculation in `code/diagnostics.py` to compute the **coefficient of variation** of significant findings from `data/results/sensitivity_analysis.json` (output of T030), **explicitly designating this value as the 'stability metric' required by SC-002**, and store in `data/results/stability_metrics.json`. **Depends on T030.**
- [X] T031 [US3] Implement VIF calculation in `code/diagnostics.py` for multivariate predictors (flag VIF > 5). **Explicitly read `data/metadata/collinearity_map.json` (output of T021e) and skip VIF calculation for pairs flagged as 'Perfect Multicollinearity'.** Only calculate VIF for non-collinear predictors. Output to `data/results/collinearity_report.json`. **DEPENDS ON T021e AND T025.**
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
1. **For T051a (Execution)**: Run the pipeline with a real dataset (if available) or trigger the fetch; **verify that the system halts execution with a specific error message citing the missing source and does NOT fallback to synthetic data.**
2. **For T051b (Documentation)**: Verify that `docs/real_data_impossibility_report.md` exists and documents the impossibility of finding a single dataset or proposes a multi-cohort strategy.
3. **For T056 (Validation Script)**: Run T056 and verify `data/results/integrity_verification.json` contains specific error types (e.g., MissingDataError) and does not contain synthetic data fallback logs.

**⚠️ NOTE**: Phase N+1 tasks are blocked until Phase N+2 (Data Availability) identifies a dataset or confirms impossibility.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [X] T041 [P] [US4] Contract test for real-data ingestion in `tests/contract/test_real_data_ingestion.py`
- [X] T042 [P] [US4] Integration test for real-data pipeline execution in `tests/integration/test_real_data_pipeline.py`

**Checkpoint**: Pipeline is validated against both synthetic and real data (if available), ensuring robustness and readiness for production use with real-world datasets.

---

## Phase N+2: Data Availability & Source Verification (Priority: P5)

**Goal**: Address the critical gap of missing verified real-world datasets containing both metagenomic and sleep data. Establish a rigorous process for sourcing, validating, and integrating real data to transition from a "Pipeline Validation Study" to a biological discovery study.

**Independent Test**: Successfully identify, document, and validate at least one real-world dataset (or a verified proxy) that contains both modalities, or formally document the impossibility of such a dataset and propose a multi-cohort integration strategy.

- [X] T049 [US5] Conduct a systematic literature and database search for public datasets containing paired gut metagenomics and polysomnography/actigraphy data. **Output: `docs/real_data_sources.md` (updated with findings).**
- [X] T049a [US5] **ATOMIC: Identify Candidates**. Execute T049 and output a specific list of candidate dataset IDs (e.g., 'NCBI PRJNA...', 'GEO GSE...') OR 'None Found' to `data/metadata/candidate_datasets.json`. **Schema: `{candidates: [{source: string, id: string, url: string, feasibility_score: float}] | {status: 'None Found'}}`.** **This task MUST output a specific ID or 'None Found' to make T051 executable.**
- [X] T050 [US5] Evaluate identified datasets for data quality, variable completeness, and privacy constraints. **Output: `data/metadata/dataset_evaluation_matrix.csv` with columns [dataset_id, source_url, completeness_score, privacy_status, feasibility_score].**
- [X] T051a [US5] **ATOMIC: Fetch if Found**. If T049a found a valid dataset (feasibility_score > 0), implement specific, verified data fetcher in `code/ingest.py` for that ID. **Primary Target: GEO GSE (Microbiome) + SleepDataProxy (Sleep Metrics).** **Output: `data/raw/[dataset_name].csv` and `data/results/dataset_validation_report.json`.** **DEPENDS ON T049a (Dataset Found = True).** If fetch fails, trigger T052. **Schema for `fetch_attempt_report.json`: `{status: 'SUCCESS'|'FAILURE', error_code: string, error_message: string, dataset_id: string|null}`.**
- [X] T051b [US5] **ATOMIC: Document Skip if Not Found**. If T049a found no datasets (feasibility_score = 0), skip T051a and generate `docs/real_data_impossibility_report.md` confirming no dataset found. **Required Sections: [Search Methodology, Candidates Found (None), Reason for Impossibility, Recommended Next Steps].** **DEPENDS ON T049a (Dataset Found = False).**
- [X] T052 [US5] **ATOMIC: Multi-Cohort Integration**. If T051a fails to find a single dataset, design and implement a multi-cohort integration strategy (e.g., harmonizing sleep data from one cohort with microbiome data from another, if metadata allows). **Output: `docs/multi_cohort_integration_plan.md` with sections [Data Harmonization Strategy, Variable Mapping Table, Privacy Compliance Plan].**
- [X] T053a [US5] **ATOMIC: Update Plan/Spec (Documentation)**. Update `plan.md` Section 1.1 and `spec.md` Status to explicitly state: "Current scope is Pipeline Validation Study. FR-001 (Real Data Ingestion) is deferred pending dataset availability." **Output: Updated plan.md and spec.md.** **DEPENDS ON T051b (No Data) OR T051a (Data Found) OR T052 (Multi-Cohort).**
- [X] T053b [US5] **ATOMIC: Update Constitution Check (Documentation)**. Update Constitution Check table in `plan.md` to mark FR-001 as 'Deferred' rather than 'PASS'. **Output: Updated Constitution Check table.** **DEPENDS ON T053a.**
- [X] T053c [US5] **ATOMIC: Execute Synthetic Validation**. Run the full pipeline in `--synthetic` mode to validate the logic after the plan is updated to 'Synthetic Only'. **Output: `data/results/synthetic_validation_report.json`.** **DEPENDS ON T053a.**
- [X] T053d [US5] **ATOMIC: Generate Pipeline Validation Status Report**. If T051a failed (no real data found) and T051b executed, generate `data/results/pipeline_validation_status.json` with status "SYNTHETIC_ONLY", reason "No verified real dataset found", and scope "Pipeline Validation Study". **This task explicitly handles the 'Missing Data' state as a valid outcome, closing the loop on FR-001 for the synthetic phase.** **DEPENDS ON T051b.**
- [X] T054a [US5] **ATOMIC: Define Comparison Framework**. Define the framework for `real_vs_synthetic_comparison_report.json` (columns, metrics, method) **without executing it**. **Schema: `{metrics: [{name: string, formula: string, target: number}], method: string}`. Output: `data/results/comparison_framework.json`.** **DEPENDS ON T053a.**
- [X] T054b [US5] **ATOMIC: Execute Comparison**. If T051a succeeded (real data found), run the comparison. **Output: `data/results/real_vs_synthetic_comparison_report.json`.** **DEPENDS ON T051a (SUCCESS) AND T054a.**
- [X] T054c [US5] **ATOMIC: Document Skipped Comparison**. If T051a failed (no real data), document that the comparison was skipped due to lack of data. **Output: `data/results/skipped_comparison_report.json` with reason.** **DEPENDS ON T051b (SUCCESS).**
- [X] T055 [US6] **REAL DATA GATE**: Implement a strict "No-Synthetic-Fallback" gate in `code/main.py` that checks for the existence of real data artifacts before any analysis step. **Conditional**: If `--real-data` flag is set and real data is missing, raise `SystemExit` with "CRITICAL: Real data source missing. Pipeline halted to prevent fabrication." If `--synthetic` flag is set (default for Phase N+2), allow execution. **This task ensures T043's error handling is enforced at the orchestration level.**
- [X] T056 [US6] **REAL DATA VERIFICATION**: Add a post-execution verification script in `code/verify_data_integrity.py` that scans the `data/` directory for any synthetic placeholders generated during a failed real-data run. **Definition**: Files in `data/` matching `synthetic_*.csv` or containing a specific checksum marker defined in `data/metadata/synthetic_data_manifest.json`. If found and `--real-data` flag was set, fail CI with "Fabrication Detected". **Output: `data/results/integrity_verification.json`.** **DEPENDS ON T055.**
- [X] T057 [US6] Update `docs/real_data_sources.md` to include a "Data Availability Status" section that explicitly states "NO VERIFIED REAL DATASET AVAILABLE" if T049/T050 yield no results, preventing accidental assumption of data existence.

**Checkpoint**: A verified real-data source is identified, integrated, and the pipeline has been validated against it, or a formal plan for multi-cohort integration is established and documented.

---

## Phase N+3: Execution Safety & Compute Optimization (Priority: P6)

**Goal**: Ensure the pipeline respects CPU/GPU constraints and handles large datasets via streaming without fabrication.

**Independent Test**: Verify that a dataset too large for RAM triggers streaming logic; verify that a GPU-requiring task (ZINB on large data) is flagged for Kaggle offload; verify no synthetic fallback occurs.

- [ ] T058 [P] [US6] Implement streaming data loader in `code/ingest.py` using `datasets.load_dataset(..., streaming=True)` for datasets exceeding substantial RAM capacity. **Logic**: Iterate chunks, compute online statistics (mean, variance, zero-proportion), and accumulate results without loading full dataset into memory. **Addresses Rule: "Large real datasets: STREAM the real data; never shrink to a toy."**
- [ ] T059 [P] [US6] Add a "Compute Feasibility Check" in `code/main.py` that estimates RAM usage based on dataset size (N subjects × taxa count) and switches to streaming mode if > 6GB estimated usage. **Output**: `data/metadata/compute_strategy.json` indicating "RAM" or "STREAMING".
- [ ] T060 [P] [US6] Implement GPU detection logic in `code/analysis.py`. **Logic**: If ZINB/Hurdle model is selected AND dataset size > 1000 samples, detect `device="cuda"` requirement. If CUDA is unavailable on current runner, raise `GPURequiredError` with message "GPU required for ZINB on large dataset. Re-run on Kaggle GPU runner." **Addresses Rule: "Compute feasibility — CPU-first, with a real GPU escape hatch."**
- [ ] T061 [US6] Update `.github/workflows/analysis.yml` to include a `kaggle-gpu` runner job that triggers automatically if `GPURequiredError` is raised. **Logic**: Detect error, re-trigger workflow on `kaggle-gpu` runner with same inputs. **DEPENDS ON T060 (specifically, T061 runs only if T060 raises GPURequiredError). NOT PARALLEL.**
- [ ] T062 [P] [US6] Implement a "No-Synthetic-Fallback" assertion in `code/data_generator.py` that checks if `--real-data` flag is set. If set and real data is missing, raise `SystemExit` with "FABRICATION PREVENTED: Real data required but missing." **Addresses Rule: "The loader must FAIL LOUDLY, never fall back to synthetic."**
- [ ] T063 [P] [US6] Add a task to document the streaming and GPU offloading strategy in `docs/compute_strategy.md`, including examples of when each mode is triggered and the expected performance characteristics.
- [ ] T063a [P] [US6] **VERIFY 6-HOUR CONSTRAINT**: Implement a test script in `code/verify_streaming_performance.py` that simulates a large dataset (N > 1000) and verifies that the streaming logic (T058) and GPU offload logic (T060) keep the total runtime [deferred] on a standard CPU runner (or Kaggle GPU). **Output**: `data/results/streaming_performance_report.json` with pass/fail status. **Addresses FR-007 for large data scenarios.** **DEPENDS ON T058, T060.**

**Checkpoint**: The pipeline is robust against large datasets, respects compute constraints, and strictly prevents synthetic data fabrication.

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
- **T021/T021b/T022a Ordering Note**: Tasks are ordered T020 -> T021 -> T022a -> T022 to ensure Method Selection (T021) is driven strictly by Distribution Checks (T020) and pre-checks (T021e), preserving the FR-002 priority tree. T022 (Transformation) runs AFTER T021. T021b (config) must be completed before T021c. T021c is now in Phase 2.
- **Real Data Constraint**: The project currently operates under a "Pipeline Validation Study" scope due to the lack of verified real-world data. T049-T054 are critical to transitioning to a biological discovery study. The synthetic data generator (T006) is a temporary placeholder for this phase.
- **Data Loader Integrity**: The real data loader (T051) MUST NOT fall back to synthetic data if the real fetch fails. It must fail loudly, allowing the execution stage to discover and resolve the data source issue. This is a hard constraint to prevent fabrication.
- **Synthetic Data Integrity**: Tasks T006d and T006c generate a `synthetic_data_manifest.json` artifact, NOT a Chain-of-Custody log, to avoid violating Constitution Principle VI which applies only to actual biological samples. **Explicitly differentiated from biological logs.**
- **Phase N+3 Constraint**: Tasks T055-T057 are mandatory safety checks. The pipeline must NEVER proceed to analysis if real data is requested but missing. Any attempt to bypass this (e.g., via synthetic fallback) is a critical failure.
- **T053 Specific Note**: T053a, T053b, and T053c are mandatory to update the plan and spec to reflect the current "Synthetic Only" scope (if no data found) and execute the validation. T053c ensures the pipeline runs in synthetic mode after the plan update. **T053d explicitly handles the 'Missing Data' state.**
- **T049a Specific Note**: T049a MUST output a specific dataset ID or 'None Found'. If 'None Found', T051 is skipped and T051b is executed.
- **T054 Specific Note**: T054 is split into T054a (Framework), T054b (Execute if data found), and T054c (Document if data not found) to break circular dependencies.
- **T055 Specific Note**: T055 is a hard gate. If `--real-data` flag is set and T051a and T052 both fail to find real data, T055 MUST fail the build. This ensures FR-001 is not silently relaxed.
- **T056 Specific Note**: T056 verifies that no synthetic data was used when real data was expected. This ensures the integrity of the real-data analysis.
- **T058-T063 Specific Note**: These tasks address the compute feasibility and streaming rules. T058 implements streaming for large datasets. T060 detects GPU requirements and triggers offload. T062 enforces the "fail loud" rule for real data. These are mandatory for compliance with the "Compute feasibility" and "Large real datasets" rules. **T063a explicitly verifies the 6-hour constraint for these scenarios.**