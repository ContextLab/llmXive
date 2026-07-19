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
- [X] T006d_new [P] Define `synthetic_provenance_schema.yaml` in `specs/001-gut-microbiome-sleep-architecture/contracts/` to satisfy Constitution Principle I (Reproducibility) for synthetic data, explicitly NOT a Chain-of-Custody log. **Renamed from T006d to avoid semantic conflict with Principle VI.**
- [X] T006e_new [P] Update constitution check logic in `code/reference_validator.py` or `code/constitution_checker.py` to validate against `synthetic_provenance_schema.yaml`. **DEPENDS ON T006d_new**.
- [X] T006c_new [P] Generate synthetic "provenance" log file in `data/metadata/synthetic_provenance.json` using the schema defined in T006d_new (Note: This is a placeholder artifact for the 'Pipeline Validation Study' scope; no real biological samples exist, so no CoC log is generated). **Renamed from T006c to reflect new schema.**
- [X] T007 Create base data loading utilities in `code/ingest.py` (CSV/TSV reader, column validation)
- [X] T008 Configure CI workflow in `.github/workflows/analysis.yml` to run on `ubuntu-latest` with CPU/GB RAM limits
- [X] T009 Setup environment configuration management (`.env` template, `requirements.txt`)
- [X] T009a [P] Define Reference-Validator Agent schema in `code/reference_validator.py`
- [X] T009b [P] Implement Reference-Validator Agent logic and integrate gate in CI (`.github/workflows/analysis.yml`) to fail build if citations are unverified (Note: Gate operates in 'Logic Only' mode for synthetic data as per Plan's 'Verified Accuracy' strategy).
- [X] T021b [P] Define configuration list of definitionally related taxa pairs in `data/config/definitionally_related_pairs.yaml` to support collinearity detection.

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

- [X] T012 [US1] Implement `validate_variables()` in `code/ingest.py` to check for required predictors (taxa) and outcomes (sleep metrics) defined in `dataset.schema.yaml`, calculate the percentage of required variables successfully loaded, **and include the list of missing variables in the output JSON**, and output the metric to `data/results/variable_load_metrics.json`. **Addresses SC-001 traceability gap.**
- [X] T013 [US1] Implement `load_data()` in `code/ingest.py` to read CSV/TSV, consume the percentage metric from `data/results/variable_load_metrics.json` (output of T012), **persist the check result (including the percentage and list of missing variables) to `data/results/variable_load_metrics.json`**, and **halt execution with `sys.exit(1)`** if the percentage is < 100% with specific error message (e.g., "Variable 'SWS duration' is missing") per FR-001. This ensures SC-001 is met even on partial failure.
- [X] T014 [US1] Implement outlier detection logic in `code/ingest.py` (IQR method: >1.5x IQR above 75th or <1.5x below 25th) and flag exclusion
- [X] T014b [US1] Implement data filtering step in `code/ingest.py` to remove flagged outliers and output the filtered dataset to `data/processed/filtered_data.parquet`. **DEPENDS ON T014**.
- [X] T014c [US1] Register the checksum for `data/processed/filtered_data.parquet` in `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml` per Constitution Principle III. **DEPENDS ON T014b**.
- [X] T015 [US1] Implement pipeline orchestration in `code/main.py` to sequence ingestion, validation, and execution
- [X] T016 [US1] Implement execution timing check in `code/main.py` to log start/end times, assert < 6 hours, and **generate timing evidence artifact (JSON log at `data/results/timing_evidence.json`)** to satisfy SC-004
- [X] T016a [US1] Create script in `code/run_stress_test.py` to execute the full pipeline on the `ubuntu-latest` runner. **DEPENDS ON T016**.
- [X] T016b [US1] Add assertion logic in `code/run_stress_test.py` to verify total execution time is < 6 hours. **DEPENDS ON T016a**.
- [X] T016c [US1] Generate `data/results/stress_test_report.json` with pass/fail status and timing details. **DEPENDS ON T016b**.
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
- **T021c MUST run before T020 and T021** as a pre-check to detect collinearity before distribution analysis.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for correlation output schema in `tests/contract/test_output_schema.py`
- [X] T019 [P] [US2] Integration test for method selection logic (Zero-inflated vs Non-normal) in `tests/integration/test_method_selection.py`

### Implementation for User Story 2

- [X] T021c [US2] Implement "Perfect Multicollinearity" pre-check in `code/diagnostics.py` via matrix rank check for definitionally related taxa (from T021b) using the *loaded* data. This task must **flag the pair as "Perfect Multicollinearity" in the output report** without halting the pipeline, per FR-006. It must **log a warning** and append the flag to the collinearity report. **DEPENDS ON T014b (filtered_data.parquet) AND T021b. MUST EXECUTE BEFORE T020 AND T021.**
- [X] T020 [US2] Implement data distribution checks in `code/analysis.py` (Shapiro-Wilk test, zero proportion calculation) **DEPENDS ON COMPLETION OF T014b (filtered_data.parquet) AND T021c (collinearity gate)**
- [X] T022a [US2] Implement compositionality detection in `code/transform.py` and integrate `sparcc`/`spiecaei` libraries if available (Note: If import fails, log warning and skip compositionality check; fallback to CLR transformation).
- [X] T022 [US2] Implement CLR transformation in `code/transform.py` using `scikit-bio` for compositional data handling (fallback if SparCC unavailable)
- [X] T021 [US2] Implement `select_correlation_method()` in `code/analysis.py` with explicit decision logic **strictly following FR-002**: 1) If zero-inflation (zeros > 30% OR Shapiro-Wilk p < 0.05) -> **ZINB/Hurdle**, 2) Else if non-normal (Shapiro-Wilk p <  0.05) -> **Spearman**, 3) Else -> **Pearson**. Compositionality detection (T022a) is a secondary check applied only if the primary method is valid. **Returns a dict with keys: `method_name`, `params`, `reason`**. **DEPENDS ON T020, T021c (collinearity gate), T022a**.
- [X] T023 [US2] Implement ZINB/Hurdle model fitting in `code/analysis.py` using `statsmodels` for zero-inflated cases
- [X] T024 [US2] Implement Spearman and Pearson correlation functions in `code/analysis.py`
- [X] T025 [US2] Implement Benjamini-Hochberg FDR correction in `code/analysis.py` to adjust p-values (q ≤ 0.05) and **output the full correlation matrix (including raw and adjusted p-values) to `data/results/correlation_matrix.json`**. **Addresses missing producer for T030.**
- [X] T026 [US2] Implement report generation in `code/report.py` ensuring all findings are labeled "associational", causal language is prohibited, and **consumes the timing evidence artifact from `data/results/timing_evidence.json` (output of T016) and correlation results from T025** for the final report **DEPENDS ON COMPLETION OF T016 AND T025**. **Moved to Phase 4.5 for integration.**
- [X] T027 [US2] Extend pipeline orchestration in `code/main.py` to import and call US2 modules **without modifying T015 logic**; T027 relies on T015's base orchestration functions

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4.5: Integration & Reporting (Cross-Story)

**Purpose**: Integrate US1 and US2 artifacts into final report and verify cross-story consumption.

- [X] T026a [P] [Integration] Implement integration test in `tests/integration/test_report_generation.py` to verify that `code/report.py` (T026) correctly consumes `data/results/timing_evidence.json` (US1) and `data/results/correlation_matrix.json` (US2) and produces a valid final report. **Addresses missing test for T026.**

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
- [X] T031 [US3] Implement VIF calculation in `code/diagnostics.py` for multivariate predictors (flag VIF > 5). **Use the result of T021c (Perfect Multicollinearity check) to skip VIF calculation for flagged pairs**; only calculate VIF for non-collinear predictors. Output to `data/results/collinearity_report.json`. **DEPENDS ON T021c AND T025**.
- [X] T033 [US3] Implement power analysis in `code/diagnostics.py` to calculate minimum N for r ≥ 0.3, power ≥ 0.80, α = 0.05
- [X] T034 [US3] Integrate diagnostics into `code/main.py` and append results to final report
- [X] T035 [US3] Update `code/report.py` to include "Power Limitation" warnings if N is insufficient

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
1. **For T048 (Execution)**: Run the pipeline with a real dataset (if available) or trigger the fetch; **verify that the system halts execution with a specific error message citing the missing source and does NOT fallback to synthetic data.**
2. **For T048a (Documentation)**: Verify that `docs/multi_cohort_integration_plan.md` or `docs/real_data_impossibility_report.md` exists and documents the impossibility of finding a single dataset or proposes a multi-cohort strategy.
3. **For T048b (Validation Script)**: Run T048b and verify `data/results/real_data_validation_report.json` contains specific error types (e.g., MissingDataError) and does not contain synthetic data fallback logs.

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [X] T041 [P] [US4] Contract test for real-data ingestion in `tests/contract/test_real_data_ingestion.py`
- [X] T042 [P] [US4] Integration test for real-data pipeline execution in `tests/integration/test_real_data_pipeline.py`

### Implementation for User Story 4

- [X] T043 [US4] Implement real data loader in `code/ingest.py` that fetches data from a verified real source (e.g., `datasets.load_dataset()` with a specific, verified ID or a direct URL to a verified file). **If the fetch fails or no real data is available, the loader MUST raise a `MissingDataError` with the specific message "Real data fetch failed: [Error Details]. Execution halted to prevent fabrication." and halt execution (sys.exit(1)). DO NOT fallback to synthetic data.** **Addresses fabrication concern.**
- [X] T044 [US4] Implement real data validation in `code/ingest.py` to check for required variables in the real dataset and log specific missing variables.
- [X] T045 [US4] Update `code/main.py` to support a `--real-data` flag that switches the pipeline from synthetic to real data mode, ensuring the real data loader (T043) is invoked.
- [X] T046 [US4] Update `code/report.py` to include a "Data Source" section that explicitly states whether the analysis was performed on synthetic or real data, and includes the source citation if real data was used.
- [X] T047 [US4] Add a task to document the process for obtaining and verifying real datasets in `docs/real_data_sources.md`, including links to verified repositories and instructions for data access.
- [ ] T048 [US4] Run the full pipeline with a real dataset (if available) and verify that the results are plausible and that the pipeline handles any real-world data issues gracefully. **Output artifact: `data/results/real_data_validation_report.json`**. **If no real dataset is available, this task is skipped and T048a is executed instead.**
- [ ] T048a [US4] Document the impossibility of finding a single real dataset or propose a multi-cohort integration strategy. **Output: `docs/multi_cohort_integration_plan.md` or `docs/real_data_impossibility_report.md`**. **This is a documentation task, not an execution task.** **DEPENDS ON T049 (Search) if applicable.**
- [ ] T048b [US4] Implement a validation script in `code/validate_real_data.py` to run the pipeline against real data (or simulated failure) and output a structured report of errors encountered. **Output: `data/results/real_data_validation_report.json`**. **Addresses granularity concern.**

**Checkpoint**: Pipeline is validated against both synthetic and real data (if available), ensuring robustness and readiness for production use with real-world datasets.

---

## Phase N+2: Data Availability & Source Verification (Priority: P5)

**Goal**: Address the critical gap of missing verified real-world datasets containing both metagenomic and sleep data. Establish a rigorous process for sourcing, validating, and integrating real data to transition from a "Pipeline Validation Study" to a biological discovery study.

**Independent Test**: Successfully identify, document, and validate at least one real-world dataset (or a verified proxy) that contains both modalities, or formally document the impossibility of such a dataset and propose a multi-cohort integration strategy.

- [ ] T049 [US5] Conduct a systematic literature and database search for public datasets containing paired gut metagenomics and polysomnography/actigraphy data. **Output: `docs/real_data_sources.md` (updated with findings)**.
- [ ] T050 [US5] Evaluate identified datasets for data quality, variable completeness, and privacy constraints. **Output: `data/metadata/dataset_evaluation_matrix.csv`**.
- [ ] T051 [US5] If a suitable single dataset is found: Implement a specific, verified data fetcher in `code/ingest.py` that downloads and validates this dataset. **Output: `data/raw/[dataset_name].csv` and `data/results/dataset_validation_report.json`**.
- [ ] T052 [US5] If no single dataset exists: Design and implement a multi-cohort integration strategy (e.g., harmonizing sleep data from one cohort with microbiome data from another, if metadata allows). **Output: `docs/multi_cohort_integration_plan.md`**.
- [ ] T053 [US5] Update `plan.md` and `spec.md` to reflect the transition from synthetic validation to real-data analysis, including any changes to the research question or methodology necessitated by the available real data.
- [ ] T054 [US5] Re-run the full pipeline with the real (or integrated) data and compare results against the synthetic baseline. **Output: `data/results/real_vs_synthetic_comparison_report.json`**.

**Checkpoint**: A verified real-data source is identified, integrated, and the pipeline has been validated against it, or a formal plan for multi-cohort integration is established and documented.

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
- **T021/T021b/T022a Ordering Note**: Tasks are ordered T020 -> T021c -> T022a -> T021 to ensure Method Selection (T021) is driven strictly by Distribution Checks (T020) and pre-checks (T021c, T022a), preserving the FR-002 priority tree. T021b (config) must be completed before T021c.
- **T021c Placement Note**: T021c has been moved to Phase 4 (US2) to ensure it runs on actual data artifacts (`filtered_data.parquet`) rather than in Phase 2 where data does not exist. **It must run BEFORE T020 and T021 to act as a pre-check.**
- **Real Data Constraint**: The project currently operates under a "Pipeline Validation Study" scope due to the lack of verified real-world data. T049-T054 are critical to transitioning to a biological discovery study. The synthetic data generator (T006) is a temporary placeholder for this phase.
- **Data Loader Integrity**: The real data loader (T051) MUST NOT fall back to synthetic data if the real fetch fails. It must fail loudly, allowing the execution stage to discover and resolve the data source issue. This is a hard constraint to prevent fabrication.
- **Synthetic Data Integrity**: Tasks T006d_new and T006c_new generate a `synthetic_provenance.json` artifact, NOT a Chain-of-Custody log, to avoid violating Constitution Principle VI which applies only to actual biological samples.