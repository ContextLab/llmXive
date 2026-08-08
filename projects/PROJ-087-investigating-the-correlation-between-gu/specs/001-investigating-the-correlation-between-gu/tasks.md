# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Sleep Quality

**Input**: Design documents from `/specs/001-gene-regulation/`
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

- [X] T001 Create project structure per implementation plan: Execute `mkdir -p src data/raw data/processed tests/unit tests/integration docs` and create empty `__init__.py` in `src`, `tests`, `tests/unit`, `tests/integration`.
- [X] T002 Initialize Python 3.11 project with pinned dependencies: Create `requirements.txt` containing `pandas>=2.0`, `scikit-bio>=0.5.9`, `scipy>=1.10`, `matplotlib>=3.7`, `seaborn>=0.12`, `requests>=2.28`, `pytest>=7.0`, `pydantic>=2.0`, `ruff>=0.1.0`. Run `pip install -r requirements.txt` then `pip freeze > requirements.txt`.
- [X] T003 [P] Configure linting (ruff) and formatting (black): Create `pyproject.toml` with `[tool.ruff]` rules set to `["E", "F", "W", "I"]` and `[tool.black]` line-length 88.
- [X] T004 [P] Setup data directory structure (`data/raw/`, `data/processed/`, `data/processed/plots/`): Ensure directories exist and contain `.gitkeep` files. **Note**: These are infrastructure tasks independent of data source verification.
- [X] T005 [P] Create base configuration loader in `src/config.py`: Implement `load_config()` function reading `DATA_URL`, `RANDOM_SEED`, and `LOG_LEVEL` from environment variables with defaults.
- [X] T006 [P] Implement logging infrastructure in `src/logging_config.py`: Configure root logger with format `%(asctime)s - %(levelname)s - %(message)s` and level `INFO`.
- [X] T009 [P] Setup content hashing utility in `src/utils/hashing.py`: Implement `def compute_sha256(file_path: str) -> str` function. **Note**: Dependency for T016, T035.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

**Note**: Specific data models are defined here based on the spec, not the data source.

- [X] T037 [P] [US1] Define Pydantic models (`MicrobiomeSample`, `SleepMetric`, `CorrelationResult`) in `src/models/schemas.py` based on the spec's Key Entities. **This task is independent of data availability; models are derived from the spec.**
- [X] T010 [P] [US1] Unit test for antibiotic exclusion logic in `tests/unit/test_ingestion.py`: Implement `test_antibiotic_exclusion_logic()` verifying samples with `antibiotic_use_last_3m=True` are filtered. **Use hardcoded small test dataframes within the test function. No data fetch required.**
- [X] T011 [P] [US1] Unit test for sleep data validation in `tests/unit/test_ingestion.py`: Implement `test_sleep_data_validation()` verifying samples with null `sleep_efficiency` or `sleep_duration_hours` are filtered. **Use hardcoded small test dataframes within the test function. No data fetch required.**
- [X] T038 [P] [US1] Write unit tests for models in `tests/unit/test_models.py`: Implement `test_microbiome_sample_instantiation()` and `test_sleep_metric_instantiation()`.

**Checkpoint**: Infrastructure and Models ready. Proceed to Phase 3 for Data Feasibility Check.

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**⚠️ CRITICAL BLOCKER**: The plan states the project is BLOCKED until a verified dataset is found. **T012c and T012d are the hard gates.** If T012c or T012d fails, T013-T017 and T020a-T020b are BLOCKED. The tasks T013-T017 below are **DEFERRED** until T012c passes.

**Goal**: Automatically download, filter, and merge microbiome data with sleep metadata, excluding samples with antibiotic use or missing sleep data.

**Independent Test**: The pipeline can be tested by running the ingestion script and verifying that the output CSV contains only rows where `antibiotic_use_last_3m` is false/null and `sleep_efficiency`/`sleep_duration_hours` are not null.

### Data Feasibility Check (Gate)

- [X] T012c [US1] Implement Data Feasibility Check (URL) in `src/ingestion.py`: Verify the existence of the verified data source URL (from plan.md). **If the URL is missing or invalid, write `data/processed/ingestion_report.json` with `status: "blocked"`, `reason: "No verified data source found"`, and `measurement_status: "unmeasurable"`, then signal the orchestrator to skip downstream tasks.** This task MUST pass (or report blocked status) before any data download tasks (T013-T017) are executed.
- [X] T012d [US1] [BLOCKED UNTIL T012c PASSES] Implement Schema Verification in `src/ingestion.py`: Fetch a sample/headers of the source. Verify file format (BIOM/CSV) and presence of required columns (`antibiotic_use_last_3m`, `sleep_efficiency`, `sleep_duration_hours`). **If missing, update `data/processed/ingestion_report.json` with `status: "blocked"`, `reason: "Missing required columns"`, and `measurement_status: "unmeasurable"`.**
- [X] T012e [US1] [BLOCKED UNTIL T012c PASSES AND T012d FAILS] Handle Schema Verification Failure: If T012d fails, generate `data/processed/ingestion_report.json` with `status: "blocked"`, `reason: "Schema mismatch: Missing required columns"`, and `measurement_status: "unmeasurable"`. **This task ensures a clear blocked report is generated if the schema check fails.**

### Happy Path Implementation (Executed ONLY if T012c & T012d Pass)

- [X] T013 [US1] [BLOCKED UNTIL T012c PASSES AND T012d PASSES] Implement download logic with exponential backoff in `src/ingestion.py`. **Must use the verified URL from the plan's '# Verified datasets' block. This is the Happy Path execution of FR-001.**
- [X] T014 [US1] [BLOCKED UNTIL T012c PASSES AND T012d PASSES] Implement filtering logic in `src/ingestion.py` to exclude antibiotic users and missing sleep data. **This task generates the exclusion counts. This is the Happy Path execution of FR-002.**
- [X] T015a [US1] [BLOCKED UNTIL T014 PASSES] Implement merging of OTU tables and metadata in `src/ingestion.py`. **Implementation must use chunked processing (e.g., `pandas.read_csv(chunksize=...)`) if necessary to ensure memory usage stays under 7 GB RAM as per FR-007.**
- [X] T015b [US1] [BLOCKED UNTIL T015a PASSES] Implement memory-efficient data loading in `src/ingestion.py` using generators or chunked iteration to satisfy FR-007. **This task ensures the merging logic handles large datasets without exceeding RAM limits.**

### Alpha-Diversity Computation (Moved to Phase 3 to satisfy FR-003 Coverage)

- [X] T020a [US1] [BLOCKED UNTIL T015b PASSES] Implement alpha-diversity computation (Shannon, Simpson, Observed OTUs) in `src/diversity.py`. **Requires: data/processed/cleaned_microbiome_sleep.csv (from T016). If input missing, raise FileNotFoundError. Implementation must use chunked processing if necessary to ensure memory usage stays under 7 GB RAM as per FR-007.**
- [X] T020b [US1] [BLOCKED UNTIL T020a PASSES] Implement memory-efficient alpha-diversity calculation in `src/diversity.py` using sparse matrices or chunked iteration to satisfy FR-007. **This task ensures the diversity computation handles large datasets without exceeding RAM limits.**

### Ingestion Completion

- [X] T016 [US1] [BLOCKED UNTIL T020b PASSES] Save cleaned dataset to `data/processed/cleaned_microbiome_sleep.csv`. **Verification**: Assert file exists, row count > 0, and SHA-256 hash recorded in `data/processed/checksums.json` AND `state/projects/PROJ-087-investigating-the-correlation-between-gu.yaml` to satisfy Constitution Principle III.
- [X] T017 [US1] [BLOCKED UNTIL T016 PASSES] Log exclusion rates to satisfy SC-001: Capture `total_initial_sample_count`, `excluded_count`, `exclusion_proportion`, and `status` (e.g., "success") in `data/processed/ingestion_report.json`. **Verification**: Assert file exists and contains these keys.

### Blocked State Handling (Global - If T012c Fails)

- [X] T017b [US1] [BLOCKED UNTIL T012c FAILS] Generate Blocked Ingestion Report: Create `data/processed/ingestion_report.json` with `status: "blocked"`, `reason: "No verified data source found"`, and `measurement_status: "unmeasurable"`. **Verification**: Assert file exists and contains these keys.
- [X] T025b [US2] [BLOCKED UNTIL T012c FAILS] Generate Blocked Analysis Report: Create `data/processed/correlation_results.csv` with `status: "blocked"`, `reason: "No verified data source found"`, and empty correlation columns. **Moved from Phase 4 to Phase 3 for immediate blocking.**
- [X] T031b [US3] [BLOCKED UNTIL T012c FAILS] Generate Blocked Final Report: Create `data/processed/reports/blocked_report.md` with Markdown format, explicitly stating "Project Blocked: No Verified Data Source Found" and including the `reason` and `status` fields from the ingestion report. **Moved from Phase 5 to Phase 3 for immediate blocking.**

**Checkpoint**: If T012c passes, US1 is functional. If T012c fails, T017b, T025b, T031b generate the blocked reports.

---

## Phase 4: User Story 2 - Statistical Correlation Analysis (Priority: P2)

**Goal**: Compute Spearman rank correlations between alpha-diversity indices and sleep metrics with Benjamini-Hochberg correction.

**Independent Test**: The analysis script can be tested on a small, synthetic dataset with known correlation coefficients to verify that the calculated Spearman r-values and adjusted p-values match expected mathematical results.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for Spearman correlation calculation in `tests/unit/test_correlation.py`: Implement `test_spearman_correlation_calculation()` using hardcoded test data.
- [X] T019 [P] [US2] Unit test for Benjamini-Hochberg correction in `tests/unit/test_correlation.py`: Implement `test_benjamini_hochberg_correction()` using hardcoded test data.

### Implementation for User Story 2

- [X] T021 [US2] [BLOCKED UNTIL T020a PASSES] Implement Spearman rank correlation test between diversity indices and sleep variables in `src/correlation.py`.
- [X] T022 [US2] [BLOCKED UNTIL T021 PASSES] Implement Benjamini-Hochberg FDR correction on p-values in `src/correlation.py`.
- [X] T023 [US2] [BLOCKED UNTIL T022 PASSES] Flag correlations: Add column `is_moderate` (|r| > 0.3) and column `is_significant` (q-value < 0.05) to the results DataFrame in `src/correlation.py` to satisfy SC-002 machine-verifiability. **Note: `is_meaningful` removed to avoid conflating separate criteria.**
- [X] T024 [US2] [BLOCKED UNTIL T023 PASSES] Save correlation results (r, p, q, significance, is_moderate, is_significant, status) to `data/processed/correlation_results.csv`. **Verification**: Assert file exists, contains columns [r, p, q, is_moderate, is_significant, status], and row count > 0 (or status=blocked if no data).
- [X] T025 [US2] [BLOCKED UNTIL T024 PASSES] Implement logic to handle "No significant associations" case gracefully in `src/correlation.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (if T012c passed) or report blocked status (if T012c failed).

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate scatterplots with regression lines and boxplots by sleep quartiles for significant correlations.

**Independent Test**: The visualization module can be tested by generating a plot file and verifying that the output image file exists, contains the correct axis labels, and displays the regression line.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for plot generation in `tests/unit/test_viz.py`: Implement `test_scatterplot_generation()` using hardcoded test data.

### Implementation for User Story 3

- [X] T027 [US3] [BLOCKED UNTIL T024 PASSES] Implement scatterplot generation with regression lines for significant correlations in `src/viz.py`.
- [X] T028 [US3] [BLOCKED UNTIL T024 PASSES] Implement boxplot generation by sleep quartile in `src/viz.py`.
- [X] T028b [US3] [BLOCKED UNTIL T024 PASSES] Implement placeholder plot generation for "No significant associations" in `src/viz.py`. **Generates a placeholder image file to satisfy FR-006 edge case handling.**
- [X] T029a [US3] [BLOCKED UNTIL T024 PASSES] Save correlation summary table to `data/processed/reports/correlation_summary.csv`. **Deliverable: CSV file containing r, p, q, is_moderate, is_significant columns.**
- [X] T029b [US3] [BLOCKED UNTIL T029a PASSES] Save manifest of all generated artifacts to `data/processed/reports/manifest.json`. **Deliverable: JSON file listing all output files and their SHA-256 hashes.**
- [X] T030 [US3] [BLOCKED UNTIL T028 PASSES] Save all plot artifacts to `data/processed/plots/`. **Filenames**: `scatterplot_shannon_sleep.png`, `boxplot_sleep_quartile.png`. **Verification**: Assert files exist.

### Blocked State Handling (If T012c Fails)

- [X] T031b [US3] [BLOCKED UNTIL T012c FAILS] Generate Blocked Final Report: Create `data/processed/reports/blocked_report.md` with Markdown format, explicitly stating "Project Blocked: No Verified Data Source Found" and including the `reason` and `status` fields from the ingestion report. **Moved from Phase 5 to Phase 3 for immediate blocking.**

**Checkpoint**: All user stories should now be independently functional or report blocked status.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032a [P] Documentation updates: Add 'Usage Examples' section to `README.md`.
- [X] T032b [P] Documentation updates: Add 'Data Source' section to `README.md`.
- [X] T032c [P] Documentation updates: Add 'Pipeline Flow' section to `docs/`.
- [X] T033 Code cleanup and refactoring: Remove unused imports and refactor T014 to use generator expressions for memory efficiency.
- [X] T035 [P] [BLOCKED UNTIL T030 PASSES] Implement `tests/integration/test_reproducibility.py`: Run the full pipeline twice, compute **SHA-256 hashes** of `data/processed/cleaned_microbiome_sleep.csv` and all files in `data/processed/plots/`, and assert the hashes match between runs to verify reproducibility (SC-005). **Record hashes in `state/projects/PROJ-087-investigating-the-correlation-between-gu.yaml` and `data/processed/checksums.json` to satisfy Constitution Principle III.**
- [X] T036 Run quickstart.md validation

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
 - **T012c/T012d** must pass before T013-T017 and T020a-T020b execute.
 - If T012c fails, T017b, T025b, T031b generate the blocked reports.
- **User Story 2 (P2)**: Depends on User Story 1 (needs cleaned data from T016)
 - **T020a** (Diversity) must pass before **T021** (Correlation) executes.
 - If T012c fails, T025b generates the blocked report.
- **User Story 3 (P3)**: Depends on User Story 2 (needs correlation results from T024)
 - If T012c fails, T031b generates the blocked report.

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
Task: "Unit test for antibiotic exclusion logic in tests/unit/test_ingestion.py"
Task: "Unit test for sleep data validation in tests/unit/test_ingestion.py"

# Launch all models for User Story 1 together (after T012c passes):
Task: "Define Pydantic models in src/models/schemas.py"
Task: "Write unit tests for models in tests/unit/test_models.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: Data Feasibility Check (T012c)
4. **STOP and VALIDATE**: If T012c fails, generate T017b, T025b, T031b (Blocked Report). If T012c passes, proceed to T013-T017 and T020a-T020b.
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
 - Developer A: User Story 1 (Ingestion) - **Must pass T012c first**
 - Developer B: User Story 2 (Analysis - can start once T016 is done)
 - Developer C: User Story 3 (Viz - can start once T024 is done)
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
- **CRITICAL**: All data processing must run within 7GB RAM and 6 hours on CPU-only runner. Use chunked processing if needed.
- **CRITICAL**: Do not fabricate data. If the verified dataset is missing, T012c must halt the pipeline with a clear status report.
- **CRITICAL**: T013-T017 and T020a-T020b are BLOCKED until T012c succeeds. If T012c fails, the project remains BLOCKED as per plan.md.
- **CRITICAL**: T020a depends on T016 output.
- **NOTE**: Mock data paths have been removed. Pipeline validation is performed via unit tests with hardcoded data.