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

- [X] T001 Create project structure per implementation plan (`code/`, `tests/`, `data/`, `data/config/`)
- [X] T002 Initialize Python 3.11 project with dependencies: `pandas`, `scipy`, `statsmodels`, `numpy`, `scikit-learn`, `pyyaml`, `scikit-bio`, `pytest`, `spiec-easi`, `sparcc`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a Define predictor schema (taxa) in `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml` **referencing `data/config/required_variables.yaml` for the explicit list of required predictor variables.**
- [X] T004b Define outcome schema (sleep metrics) in `specs/001-gut-microbiome-sleep-architecture/contracts/dataset.schema.yaml` **referencing `data/config/required_variables.yaml` for the explicit list of required outcome variables.**
- [X] T004c **IMPLEMENT `data/config/required_variables.yaml`**: Generate this file by manually defining the explicit list of required predictor and outcome variables. **Logic**: Since `spec.md` only provides examples, this task requires manual definition. **Output**: `data/config/required_variables.yaml` with schema: `required_predictors: [string], required_outcomes: [string]`. **Template List**: `required_predictors: ["Bacteroides", "Firmicutes", "Actinobacteria", "Proteobacteria", "Fusobacteria"]`, `required_outcomes: ["REM_duration", "SWS_duration", "Wake_after_sleep_onset", "Total_sleep_time"]`. **This is the Single Source of Truth for variable lists used in T012/T078.**
- [X] T005a Define output schema (CorrelationResult structure) in `specs/001-gut-microbiome-sleep-architecture/contracts/output.schema.yaml`
- [X] T006 Implement data loading utilities in `code/ingest.py` (CSV/TSV reader, column validation)
- [X] T006d **IMPLEMENT CHECKSUM SCHEMA AND RECORDING (Logic Only)**: Implement `record_artifact_checksum(file_path, state_file)` in `code/reference_validator.py`. **Schema**: `artifact_hashes: { "<file_path>": "sha256:<hash>" }`. **Constraint**: This step MUST be invoked by T015 (Orchestration) as a blocking step before analysis begins. **IMPORTANT**: For this "Pipeline Validation Study" (synthetic data), this task operates in "Logic Only" mode: it records checksums for generated synthetic files but does NOT enforce a blocking gate for external citation verification (which has no input). **Addresses Constitution Principle I & III.**
- [X] T007 Configure CI workflow in `.github/workflows/analysis.yml` to run on `ubuntu-latest` with CPU/GB RAM limits
- [X] T008 Setup environment configuration management (`.env` template, `requirements.txt`)
- [X] T009a [P] Define Reference-Validator Agent schema in `code/reference_validator.py`
- [X] T009b [P] **IMPLEMENT REFERENCE-VALIDATOR AGENT (Logic Only)**: Implement Reference-Validator Agent logic and integrate gate in CI (`.github/workflows/analysis.yml`). **Constraint**: For this "Pipeline Validation Study" (synthetic data), the gate MUST operate in "Logic Only" mode: it validates the *structure* of the pipeline and synthetic data generation logic, but it MUST NOT fail the build if no real-world citations are found (as per Plan's "Verified Accuracy" strategy). **Addresses Constitution Principle I & II.**
- [X] T021c [P] Define configuration list of definitionally related taxa pairs in `data/config/definitionally_related_pairs.yaml`. **Format**: YAML list of lists `[[taxon_A, taxon_B],...]`. **Schema**: `pairs: [[string, string],...]`. **Addresses FR-006.**
- [X] T021f_new [P] **IMPLEMENT DYNAMIC COLLINEARITY DETECTION**: Implement "Perfect Multicollinearity" detection algorithm in `code/diagnostics.py` using **matrix rank check** (e.g., `numpy.linalg.matrix_rank`) on the predictor matrix for pairs listed in `data/config/definitionally_related_pairs.yaml`. **Constraint**: This task MUST dynamically detect linear dependence via matrix rank check as mandated by FR-006, rather than just reading a config file. **Output**: `data/metadata/static_collinearity_map.json` (JSON map of flagged pairs detected via rank check). **DEPENDS ON T021c.**

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

- [X] T012 [US1] **IMPLEMENT VALIDATION LOGIC AND METRIC PERSISTENCE**: Implement `validate_variables()` in `code/ingest.py` to check for required predictors (taxa) and outcomes (sleep metrics) defined in `data/config/required_variables.yaml`. **CRITICAL**: Calculate the percentage of required variables successfully loaded, include the list of missing variables in the return object, and **ALWAYS WRITE** `data/results/variable_load_metrics.json` with status, percentage, missing variables, and total required, regardless of pass/fail status. **Schema (File)**: `{"status": "PASS" | "FAIL", "percentage_loaded": float, "missing_variables": [string], "total_required": int}`. **Addresses FR-001 and SC-001.**
- [X] T012b [US1] **IMPLEMENT ARTIFACT PERSISTENCE**: Ensure `validate_variables()` writes `data/results/variable_load_metrics.json` to disk immediately upon completion of validation logic, before any other logic proceeds. **DEPENDS ON T012.**
- [X] T013 [US1] **IMPLEMENT IMMEDIATE HALT LOGIC**: Implement `load_data()` in `code/ingest.py` to call T012. **CRITICAL**: If T012 returns "FAIL", **HALT EXECUTION** (`sys.exit(1`) immediately with the specific error message (e.g., "Variable 'SWS duration' is missing"). **DO NOT** read from disk. If T012 returns "PASS", proceed to read the artifact from T012b (which is now written). **Addresses FR-001.**
- [X] T014 Implement outlier detection logic in `code/ingest.py` (IQR method: >1.5x IQR above 75th or < 1.5x IQR below 25th)
- [X] T014b [US1] **IMPLEMENT OUTLIER FILTERING AND REPORT GENERATION**: Implement data filtering step in `code/ingest.py` to remove flagged outliers and output the filtered dataset to `data/processed/filtered_data.parquet`. **DEPENDS ON T014.** **CRITICAL**: Also generate `data/results/outlier_report.json` containing the count of excluded points and the list of excluded row indices. **Schema**: `{"count": int, "excluded_indices": [int]}`. **Addresses FR-001.**
- [X] T014c [US1] Register the checksum for `data/processed/filtered_data.parquet` in `state/projects/PROJ-340-investigating-the-correlation-between-gu.yaml` per Constitution Principle III. **DEPENDS ON T014b.**
- [X] T015 Implement pipeline orchestration in `code/main.py` to sequence ingestion, validation, and execution. **Constraint**: Must invoke T006d (checksum recording) as a blocking step before proceeding to analysis.
- [X] T016 [US1] **IMPLEMENT EXECUTION TIMING CHECK AND EVIDENCE GENERATION**: Implement execution timing check in `code/main.py` to log start/end times, assert < 6 hours, and **generate timing evidence artifact **(JSON log at `data/results/timing_evidence.json`) to satisfy SC-004. **CRITICAL**: If the time limit is exceeded, the system MUST **HALT** (`sys.exit(1`) with a "TIMEOUT" error. **Output**: `data/results/timing_evidence.json`. **DEPENDS ON T014b, T015.**
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

- [X] T020 Implement data distribution checks in `code/analysis.py` (Shapiro-Wilk test, zero proportion calculation) **AND check for zero-inflation **(zeros > 30% OR Shapiro-Wilk p < 0.05). **DEPENDS ON T014b.**
- [X] T020a Implement compositionality detection in `code/transform.py` and integrate `scikit-bio` libraries if available. **Output: `data/metadata/compositionality_flag.json`.**
- [X] T022a [P] **IMPLEMENT COMPOSITIONALITY CHECK**: Verify `data/metadata/compositionality_flag.json` exists and is valid. **DEPENDS ON T020a.**
- [X] T021 **IMPLEMENT CORRELATION METHOD SELECTION**: Implement `select_correlation_method()` in `code/analysis.py` with explicit decision logic **strictly following FR-002**: 1) If zero-inflation (zeros > 30% OR Shapiro-Wilk p < 0.05), use a Zero-Inflated Negative Binomial (ZINB) or Hurdle model; 2) Else if non-normality is detected (Shapiro-Wilk p < 0.05), use Spearman rank correlation; 3) Else use Pearson correlation. **CRITICAL**: Do NOT use library availability as a fallback. If the required library is missing, the pipeline must fail loudly. **MUST read `data/metadata/compositionality_flag.json` and zero proportion from T020**. **CRITICAL**: This task MUST generate `data/metadata/method_selection_log.json` documenting the specific statistical tests performed (Shapiro-Wilk p-value, zero proportion), the decision logic path taken, and the final selected method. **DEPENDS ON T020, T020a, T022a**.
- [X] T022 Implement CLR transformation in `code/transform.py` using `scikit-bio` for compositional data handling (fallback if SparCC unavailable). **CONDITIONAL**: Only run if T021 selects a method requiring compositional correction and the compositionality flag is set (from T020a). **Output**: `data/processed/processed_data.parquet`. **DEPENDS ON T021, T022a.**
- [X] T023 Implement ZINB/Hurdle model fitting in `code/analysis.py` using `statsmodels` for zero-inflated cases
- [X] T024 Implement Spearman and Pearson correlation functions in `code/analysis.py`
- [X] T025 **IMPLEMENT FDR CORRECTION AND OUTPUT**: Implement Benjamini-Hochberg FDR correction in `code/analysis.py` to adjust p-values (q ≤ 0.05) and write the full correlation matrix to `data/results/correlation_matrix.json`. **DEPENDS ON T022** (if CLR selected) **and T023/T024**.
- [X] T026 [US2] **EXTEND PIPELINE ORCHESTRATION**: Extend pipeline orchestration in `code/main.py` to import and call US2 modules **after** analysis modules (T022, T025) are complete. **DEPENDS ON T022, T025**. **Note**: T026 no longer depends on T087 (Report Generation) to avoid circular dependency.

**Checkpoint**: At this point, User Story 2 should be fully functional and testable independently

---

## Phase 4.5: Integration, Diagnostics & Reporting (Cross-Cutting)

**Purpose**: Integrate US1 and US2 artifacts, implement missing diagnostics (Sensitivity, VIF, Power), and enforce associational framing.

- [X] T078 [US3] **IMPLEMENT SENSITIVITY ANALYSIS**: Implement logic to re-run significance tests at p < 0.01, p < 0.05, and p < 0.10 using results from T025. **Output**: `data/results/sensitivity_analysis.json` with percentage change in significant findings for each threshold. **Addresses FR-005 and SC-002.**
- [X] T079 [US3] **IMPLEMENT VIF CALCULATION**: Implement Variance Inflation Factor (VIF) calculation in `code/diagnostics.py` for all predictors *excluding* those flagged as "Perfect Multicollinearity" in `data/metadata/static_collinearity_map.json` (output of T021f_new). **Output**: `data/results/vif_report.json` with VIF values and flags for VIF > 5. **Addresses FR-006 and SC-003.** **DEPENDS ON T021f_new.**
- [X] T080 [US3] **IMPLEMENT POWER ANALYSIS**: Implement power analysis in `code/diagnostics.py` to calculate minimum sample size required to detect r ≥ 0.3 with power ≥ 0.80 at α = 0.05. **Output**: `data/results/power_analysis.json` with calculated N and "Underpowered" flag if N < calculated threshold. **Addresses FR-006 and SC-005.**
- [X] T087 [US2] **IMPLEMENT REPORT GENERATION WITH ASSOCIATIONAL FRAMING**: Implement `generate_report()` in `code/report.py`. **CRITICAL**: This task MUST enforce associational language **during generation** (e.g., via strict template constraints) rather than post-hoc scanning. The report MUST explicitly state "These results represent an associational relationship" and prohibit causal language like "causes" or "leads to". **Output**: `data/results/final_report.md`. **DEPENDS ON T025, T078, T079, T080, T022a, T026**. **Addresses FR-004.**

**Checkpoint**: US1 and US2 are integrated; Diagnostics complete.

---

## Phase N+4: Real-Data Execution & GPU Offload Verification (Priority: P7) - REMOVED
**Note**: This phase was removed. The project is scoped as a "Pipeline Validation Study" using synthetic data. Real-data execution is out of scope for this phase.

---

## Phase N+5: Data Source Resolution & Pipeline Re-Enablement (Priority: P8)

**Purpose**: Resolve the "No Verified Real Dataset" blocker identified in Phase N+2 by enforcing single-source data requirements and re-enabling the full analysis on real data if found, with seamless fallback to synthetic validation.

- [X] T051a **IMPLEMENT FETCH LOGIC**: Implement `fetch_real_data()` in `code/ingest.py` to attempt download from verified sources (NCBI, Zenodo) using specific IDs. **Output**: `data/raw/real_data.csv`.
- [X] T051b **IMPLEMENT FETCH EXECUTION AND STATUS LOGGING**: Execute T051a. **Constraint**: If T051a fails (no data found), **DO NOT STOP**. Instead, write `data/metadata/fetch_status.json` with `{"status": "FAIL", "reason": "No real data found"}` and allow the pipeline to proceed to T053a (Synthetic Validation). If T051a succeeds, write `{"status": "SUCCESS"}`. **Output**: `data/metadata/fetch_status.json`.
- [X] T051c **DATA AVAILABILITY GATE**: Implement a gate task that checks `data/metadata/fetch_status.json`. **Output**: `real_data_available` boolean. **DEPENDS ON T051b.**
- [X] T053a **UPDATE PLAN FOR SYNTHETIC SCOPE**: Update `plan.md` to reflect "Pipeline Validation Study" scope if T051b fails. **DEPENDS ON T051b.**
- [X] T053d **IMPLEMENT SYNTHETIC VALIDATION**: Run the pipeline on synthetic data if real data is unavailable. **DEPENDS ON T053a.**
- [X] T055a **VALIDATE SYNTHETIC FALLBACK LOGIC**: Implement a task to verify that the pipeline correctly transitions to synthetic validation when `data/metadata/fetch_status.json` indicates failure. **Output**: `data/results/fallback_validation_report.json`. **Addresses the removed T055 concern.**
- [X] T056 **VERIFICATION**: Verify that the pipeline correctly handles the "No Real Data" state. **DEPENDS ON T051b.**
- [X] T070 **LARGE PROXY GENERATOR**: Create a script in `code/generate_large_proxy.py` that generates a verified large proxy dataset. **Schema**: A dataset comprising a substantial number of subjects (rows) and taxa (columns: `subject_id`, `taxon_01`...`taxon_50` (float64, normal dist, seed=42), `sleep_metric_1`...`sleep_metric_4`). **Output**: `data/raw/large_proxy.csv`. **Addresses Assumption-001 and robustness testing requirements for the statistical engine.**

**Checkpoint**: The project transitions from a "Pipeline Validation Study" to a biological discovery study using real, single-source data, with all gates passed and results validated.

---

## Phase N+6: Review Resolution & Final Validation (Priority: P10)

**Purpose**: Address specific reviewer concerns regarding the "Pipeline Validation Study" scope, the lack of real data, and the robustness of the synthetic validation logic. Ensure all artifacts are consistent with the current state of the project.

- [X] T072 **DOCUMENT REAL DATA IMPOSSIBILITY**: Generate `docs/real_data_impossibility_report.md` documenting the search for a valid dataset.
- [X] T073 Update `code/constitution_checker.py` to correctly identify the project as "Synthetic Only".

**Checkpoint**: The project is fully documented as a "Pipeline Validation Study", all constitutional checks pass for the synthetic scope, and the roadmap for future real-data integration is clearly defined.

---

## Phase N+7: Robustness & Scale Verification (Priority: P9) - NEW

**Purpose**: Address reviewer concerns regarding the "Pipeline Validation Study" scope by verifying the statistical engine's robustness against large-scale synthetic data and ensuring the "No Real Data" transition is seamless.

- [X] T074 [US1] **IMPLEMENT LARGE-SCALE SYNTHETIC DATA STREAMING**: Implement `generate_large_proxy_streaming()` in `code/generate_large_proxy.py` to create a synthetic dataset with N > 1000 subjects and > 500 taxa, streaming it in chunks to `data/processed/large_proxy_chunked.parquet` to verify memory constraints (Assumption-001). **Constraint**: Must NOT load the entire dataset into RAM at once; must use `pandas` chunking or `dask` to process in < 7GB RAM. **Output**: `data/results/large_scale_validation_report.json` with memory usage stats and execution time. **Addresses Assumption-001 and SC-004.**
- [X] T075 [US3] **IMPLEMENT POWER ANALYSIS SENSITIVITY**: Extend T080 to run power analysis across a range of effect sizes (r = 0.1 to 0.5) and sample sizes, outputting a sensitivity curve to `data/results/power_sensitivity_curve.json`. **Addresses FR-006 and SC-005.**
- [X] T076 [US2] **IMPLEMENT COMPOSITIONAL DATA EDGE CASE TEST**: Create a synthetic dataset with extreme compositionality (sum of taxa = 1.0 exactly) and verify that T021 correctly selects CLR + ZINB/Spearman and that T022 correctly applies the transformation without numerical instability. **Output**: `data/results/compositionality_edge_case_report.json`. **Addresses Edge Cases.**
- [X] T077 [US3] **IMPLEMENT OUTLIER IMPACT ANALYSIS**: Re-run the correlation analysis (T025) on the dataset with outliers removed (T014b) and compare results to the unfiltered dataset, outputting the delta in significant findings to `data/results/outlier_impact_report.json`. **Addresses Edge Cases.**

**Checkpoint**: The project has been rigorously tested against scale, edge cases, and sensitivity requirements, confirming the robustness of the "Pipeline Validation Study" findings.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup **(Phase 1) No dependencies - can start immediately
- **Foundational **(Phase 2) Depends on Setup completion - BLOCKS all user stories
- **User Stories **(Phase 3+) All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish **(Final Phase) Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 **(P1) Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 **(P2) Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 **(P3) Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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