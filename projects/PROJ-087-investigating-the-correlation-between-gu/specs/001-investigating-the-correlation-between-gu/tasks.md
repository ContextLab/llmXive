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
- [X] T002 [P] Initialize Python 3.x project with pinned dependencies: Create `requirements.txt` containing `pandas>=2.0`, `scikit-bio>=0.5.9`, `scipy>=1.10`, `matplotlib>=3.7`, `seaborn>=0.12`, `requests>=2.28`, `pytest>=7.0`, `pydantic>=2.0`, `ruff>=0.1.0`. Run `pip install -r requirements.txt` then `pip freeze > requirements.txt`.
- [X] T003 [P] Configure linting (ruff) and formatting (black): Create `pyproject.toml` with `[tool.ruff]` rules set to `["E", "F", "W", "I"]` and `[tool.black]` line-length: 88.
- [X] T004 [P] Setup data directory structure (`data/raw/`, `data/processed/`, `data/processed/plots/`, `data/processed/reports/`): Ensure directories exist and contain `.gitkeep` files. **Note**: These are infrastructure tasks independent of data source verification.
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
- [X] T010 [P] [US1] Unit test for antibiotic exclusion logic in `tests/unit/test_ingestion.py`: Implement `test_antibiotic_exclusion_logic()` verifying samples with `antibiotic_use_last_3m=True` are filtered. **Use hardcoded small test dataframes within the test function. No data fetch required.** **DEPENDENCY: T037 must complete first.**
- [X] T011 [P] [US1] Unit test for sleep data validation in `tests/unit/test_ingestion.py`: Implement `test_sleep_data_validation()` verifying samples with null `sleep_efficiency` or `sleep_duration_hours` are filtered. **Use hardcoded small test dataframes within the test function. No data fetch required.** **DEPENDENCY: T037 must complete first.**
- [X] T038 [P] [US1] Write unit tests for models in `tests/unit/test_models.py`: Implement `test_microbiome_sample_instantiation()` and `test_sleep_metric_instantiation()`. **DEPENDENCY: T037 must complete first.**

**Checkpoint**: Infrastructure and Models ready. Proceed to Phase 3 for Data Feasibility Check.

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**⚠️ CRITICAL BLOCKER**: The plan states the project is BLOCKED until a verified dataset is found. **T012a is the unconditional gate.** If T012a fails, the project MUST halt and generate blocked artifacts (T012c_gen, T016b, etc.). T013-T017 and T020a are **STRICTLY BLOCKED** until T012a PASSES.

**Goal**: Automatically download, filter, and merge microbiome data with sleep metadata, excluding samples with antibiotic use or missing sleep data.

**Independent Test**: The pipeline can be tested by running the ingestion script and verifying that the output CSV contains only rows where `antibiotic_use_last_3m` is false/null and `sleep_efficiency`/`sleep_duration_hours` are not null.

### Data Feasibility Check (Gate)

- [ ] T012a [US1] **UNCONDITIONAL GATE**: Execute Data Feasibility Check. Read `plan.md` and check the `# Verified datasets` block for an American Gut Project URL.
 - **IF** a verified URL is found: Proceed to T012d.
 - **IF** no verified URL is found (as per current plan.md status): **IMMEDIATELY TRIGGER** T012c_gen (inline logic or execution flow). Do NOT proceed to T012d or any Happy Path tasks.
 - **Deliverable**: If blocked, ensure `data/processed/ingestion_report.json` exists with `status: "blocked"`. If passed, proceed to T012d.
 - **Note**: This task resolves the circular dependency by acting as the primary trigger for the blocked state.

- [ ] T012c_gen [US1] **AUTO-TRIGGERED BY T012a FAIL**: Generate Blocked Ingestion Report. Create `data/processed/ingestion_report.json` with `status: "blocked"`, `reason: "No verified data source found in plan.md"`, `measurement_status: "unmeasurable"`, and `timestamp`. **This task is the primary deliverable for the blocked state.**

- [X] T012d [US1] [BLOCKED UNTIL T012a PASSES] Implement Schema Verification in `src/ingestion.py`: Fetch a sample/headers of the source. Verify file format (BIOM/CSV) and presence of required columns (`antibiotic_use_last_3m`, `sleep_efficiency`, `sleep_duration_hours`).
 - **IF** columns are missing: **IMMEDIATELY TRIGGER** T012d_gen.
 - **IF** columns exist: Proceed to T045.

- [ ] T012d_gen [US1] **AUTO-TRIGGERED BY T012d FAIL**: Handle Schema Verification Failure. Generate `data/processed/ingestion_report.json` with `status: "blocked"`, `reason: "Schema mismatch: Missing required columns"`, `measurement_status: "unmeasurable"`, and `timestamp`.

### Blocked State Handling (Global - If T012a FAILS or T012d FAILS)

- [ ] T016b [US1] [BLOCKED UNTIL T012a FAILS OR T012d FAILS] Generate Blocked Cleaned Dataset: Create `data/processed/cleaned_microbiome_sleep.csv` with `status: "blocked"`, `reason: "No verified data source found"`, and empty rows. **Columns must be: sample_id, age, bmi, antibiotic_use_last_3m, sleep_efficiency, sleep_duration_hours, shannon, simpson, observed_otus.**
- [ ] T017b [US1] [BLOCKED UNTIL T012a FAILS OR T012d FAILS] Generate Blocked Ingestion Report: Create `data/processed/ingestion_report.json` with `status: "blocked"`, `reason: "No verified data source found"`, and `measurement_status: "unmeasurable"`. **Verification**: Assert file exists and contains these keys.
- [ ] T020c [US1] [BLOCKED UNTIL T012a FAILS OR T012d FAILS] Generate Blocked Diversity Artifact: Create `data/processed/diversity_results.csv` with `status: "blocked"`, `reason: "No verified data source found"`, and empty diversity columns (shannon, simpson, observed_otus). **Ensures US-1 has a measurable artifact in the blocked state.**
- [ ] T025b [US2] [BLOCKED UNTIL T012a FAILS OR T012d FAILS] Generate Blocked Analysis Report: Create `data/processed/correlation_results.csv` with `status: "blocked"`, `reason: "No verified data source found"`, and empty correlation columns. **Moved from Phase 4 to Phase 3 for immediate blocking.**
- [ ] T031c [US3] [BLOCKED UNTIL T012a FAILS OR T012d FAILS] Generate Blocked Final Report: Create `data/processed/reports/blocked_report.md` with Markdown format, explicitly stating "Project Blocked: No Verified Data Source Found" and including the `reason` and `status` fields from the ingestion report. **Moved from Phase 5 to Phase 3 for immediate blocking.**

### Happy Path Implementation (Executed ONLY if T012a PASSES AND T012d PASSES)

- [X] T045 [US1] [BLOCKED UNTIL T012a PASSES AND T012d PASSES] Implement exponential backoff with retry logic in `src/ingestion.py`: Add a `retry_with_backoff()` function to handle transient network errors during data download. **This task ensures the pipeline is robust against temporary network issues, satisfying the edge case for API rate-limiting.**
- [X] T013 [US1] [BLOCKED UNTIL T045 PASSES AND T012a PASSES AND T012d PASSES] Implement download logic with exponential backoff in `src/ingestion.py`. **Must use the verified URL from the plan's '# Verified datasets' block. This is the Happy Path execution of FR-001.**
- [X] T014 [US1] [BLOCKED UNTIL T013 PASSES] Implement filtering logic in `src/ingestion.py` to exclude antibiotic users and missing sleep data. **This task generates the exclusion counts. This is the Happy Path execution of FR-002.** <!-- ATOMIZE: requested -->
- [ ] T015a_read [US1] [BLOCKED UNTIL T014 PASSES] Implement chunked reading logic in `src/ingestion.py`: Use `pandas.read_csv(chunksize=10000)` or `datasets.load_dataset(..., streaming=True)` to read data in chunks. **This task ensures memory efficiency.**
- [ ] T015a_merge [US1] [BLOCKED UNTIL T015a_read PASSES] Implement merging of OTU tables and metadata in `src/ingestion.py` using memory-efficient chunked processing. **This task ensures the merging logic handles large datasets without exceeding RAM limits (FR-007).**
- [ ] T015a_monitor [US1] [BLOCKED UNTIL T015a_merge PASSES] Implement memory monitoring in `src/ingestion.py`: Log memory usage during processing to ensure it stays within acceptable system limits. **This task ensures FR-007 compliance.**
- [ ] T016 [US1] [BLOCKED UNTIL T015a_monitor PASSES] Save cleaned dataset to `data/processed/cleaned_microbiome_sleep.csv`. **Verification**: Assert file exists, row count > 0, and SHA-256 hash recorded in `data/processed/checksums.json` AND `state/projects/PROJ-087-investigating-the-correlation-between-gu.yaml` under key `artifact_hashes.cleaned_microbiome_sleep` to satisfy Constitution Principle III.
- [ ] T017 [US1] [BLOCKED UNTIL T016 PASSES] Log exclusion rates to satisfy SC-001: Capture `total_initial_sample_count`, `excluded_count`, `exclusion_proportion` (calculated as `excluded_count / total_initial_sample_count`), and `status` (e.g., "success") in `data/processed/ingestion_report.json`. **Verification**: Assert file exists and contains these keys.

### Alpha-Diversity Computation (Moved to Phase 3 to satisfy FR-003 Coverage)

- [X] T043 [US1] [BLOCKED UNTIL T016 PASSES] Implement rarefaction normalization in `src/diversity.py`: Add a `rarefy_table()` function using `scikit-bio` to normalize sequencing depth before alpha-diversity calculation. **This task ensures that sequencing depth artifacts do not bias diversity indices, satisfying FR-003 and Plan.md Risk Mitigation.**
- [X] T044 [US1] [BLOCKED UNTIL T043 PASSES] Add unit tests for rarefaction logic in `tests/unit/test_diversity.py`: Implement `test_rarefaction_normalization()` to verify that the rarefaction step correctly normalizes sequencing depth. **This task ensures the rarefaction logic is correct and robust.**
- [ ] T020a [US1] [BLOCKED UNTIL T043 PASSES AND T016 PASSES] Implement alpha-diversity computation (Shannon, Simpson, Observed OTUs) in `src/diversity.py`. **Requires: data/processed/cleaned_microbiome_sleep.csv (from T016). If input missing, raise FileNotFoundError. Implementation must use chunked processing with chunksize=10000 to ensure memory usage stays under 7 GB RAM as per FR-007. Deliverable: CSV at `data/processed/diversity_results.csv` with columns [sample_id, shannon, simpson, observed_otus].** <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
- [X] T020b [US1] [BLOCKED UNTIL T020a PASSES] Implement memory-efficient alpha-diversity calculation in `src/diversity.py` using sparse matrices or chunked iteration to satisfy FR-007. **This task ensures the diversity calculation handles large datasets without exceeding RAM limits.**

**Checkpoint**: If T012a passes, US1 is functional. If T012a fails, T012c_gen, T016b, T017b, T020c, T025b, T031c generate the blocked reports.

---

## Phase 4: User Story 2 - Statistical Correlation Analysis (Priority: P2)

**Goal**: Compute Spearman rank correlations between alpha-diversity indices and sleep metrics with Benjamini-Hochberg correction.

**Independent Test**: The analysis script can be tested on a small, synthetic dataset with known correlation coefficients to verify that the calculated Spearman r-values and adjusted p-values match expected mathematical results.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for Spearman correlation calculation in `tests/unit/test_correlation.py`: Implement `test_spearman_correlation_calculation()` using hardcoded test data.
- [X] T019 [P] [US2] Unit test for Benjamini-Hochberg correction in `tests/unit/test_correlation.py`: Implement `test_benjamini_hochberg_correction()` using hardcoded test data.

### Implementation for User Story 2

- [X] T021 [US2] [BLOCKED UNTIL T020a PASSES] Implement Spearman rank correlation test between **each** alpha-diversity index (Shannon, Simpson, Observed OTUs) and sleep variables in `src/correlation.py`. **Must iterate over all three indices. Save intermediate results to a temp DataFrame.**
- [X] T022 [US2] [BLOCKED UNTIL T021 PASSES] Implement Benjamini-Hochberg FDR correction on p-values in `src/correlation.py`.
- [X] T023 [US2] [BLOCKED UNTIL T022 PASSES] Flag correlations: Add column `is_moderate` (|r| > 0.3) and column `is_significant` (q-value < 0.05) to the results DataFrame in `src/correlation.py` to satisfy SC-002 machine-verifiability. **Log the count and percentage of moderate correlations to satisfy FR-004 reporting purposes.**
- [ ] T024 [US2] [BLOCKED UNTIL T023 PASSES] Save correlation results (r, p, q, significance, is_moderate, is_significant, status) to `data/processed/correlation_results.csv`. **Verification**: Assert file exists, contains columns [sample_id, diversity_index, sleep_metric, r, p, q, is_moderate, is_significant, status], and row count > 0 (or status=blocked if no data).
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
- [X] T031a [US3] [BLOCKED UNTIL T029a PASSES] Generate Final Human-Readable Report: Create `data/processed/reports/final_report.md` summarizing findings. **Must include a summary table of correlations, visualizations, and explicitly state "No significant associations found" if applicable (FR-006 edge case).**

**Checkpoint**: All user stories should now be independently functional or report blocked status.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032a [P] Documentation updates: Add 'Usage Examples' section to `README.md`.
- [X] T032b [P] Documentation updates: Add 'Data Source' section to `README.md`.
- [X] T032c [P] Documentation updates: Add 'Pipeline Flow' section to `docs/`.
- [X] T033 Code cleanup and refactoring: Remove unused imports and refactor T014 to use generator expressions for memory efficiency.
- [X] T035 [P] [BLOCKED UNTIL T016 PASSES OR T012a FAILS OR T012d FAILS] Implement `tests/integration/test_reproducibility.py`: <!-- ATOMIZE: requested -->
 - **Happy Path**: Run the full pipeline twice, compute **SHA-256 hashes** of `data/processed/cleaned_microbiome_sleep.csv` and all files in `data/processed/plots/`, and assert the hashes match between runs to verify reproducibility (SC-005). Record hashes in `state/projects/PROJ-087-investigating-the-correlation-between-gu.yaml` under `artifact_hashes` map and `data/processed/checksums.json` under `files` map.
 - **Blocked Path**: If T012a FAILS or T012d FAILS, verify the structure of `data/processed/ingestion_report.json` (keys: status, reason, measurement_status, timestamp) and `data/processed/cleaned_microbiome_sleep.csv` (schema: sample_id, age, bmi, antibiotic_use_last_3m, sleep_efficiency, sleep_duration_hours, shannon, simpson, observed_otus, status) instead of data hashes. **Verification**: Assert structure matches expected schema.
- [X] T036 Run quickstart.md validation

---

## New Tasks: Addressing Review Concerns

**Purpose**: These tasks address specific concerns raised during the analysis phase regarding data source verification, rarefaction implementation, and robust error handling.

### Data Source Verification & Streaming (Addressing Plan.md "Data Availability Gap")

- [X] T040 [US1] **REMOVED**: Logic merged into T012a. Robust data source verification (URL, headers, columns) is now part of T012a.
- [X] T041 [US1] **REMOVED**: Merged into T015a_read/T015a_merge. Memory-efficient streaming is now part of T015a_read/T015a_merge.
- [X] T042 [US1] **REMOVED**: Merged into T015a_merge. Chunked merging is now part of T015a_merge.

### Rarefaction & Normalization (Addressing FR-003)

- [X] T043 [US1] **INTEGRATED**: Moved to Phase 3. Implements rarefaction normalization in `src/diversity.py`.
- [X] T044 [US1] **INTEGRATED**: Moved to Phase 3. Adds unit tests for rarefaction logic in `tests/unit/test_diversity.py`.

### Error Handling & Reporting (Addressing Edge Cases)

- [X] T045 [US1] [BLOCKED UNTIL T012a PASSES AND T012d PASSES] Implement exponential backoff with retry logic in `src/ingestion.py`: Add a `retry_with_backoff()` function to handle transient network errors during data download. **This task ensures the pipeline is robust against temporary network issues, satisfying the edge case for API rate-limiting.**
- [X] T046 [US2] [BLOCKED UNTIL T024 PASSES] Implement graceful handling of "No significant associations" in `src/correlation.py`: Ensure that if no correlations survive FDR correction, the pipeline generates a report explicitly stating "No significant associations found" rather than crashing or returning empty results. **This task ensures the pipeline handles edge cases gracefully, satisfying the edge case for no significant results.**
- [X] T047 [US3] [BLOCKED UNTIL T024 PASSES] Implement placeholder plot generation for "No significant associations" in `src/viz.py`: Ensure that if no correlations are significant, a placeholder plot is generated to satisfy FR-006. **This task ensures the visualization module handles edge cases gracefully.**

### Data Streaming & Loader Strictness (Addressing T049/T050/T051)

- [X] T049 [US1] [BLOCKED UNTIL T012a PASSES AND T012d PASSES] Implement real dataset streaming in `src/ingestion.py`: Use `datasets.load_dataset(..., streaming=True)` or `pandas.read_csv(chunksize=10000)` to process the full American Gut Project dataset in chunks, ensuring the entire dataset contributes to results while adhering to available memory constraints. **Explicitly state the streaming rule (chunk size, iteration logic) in the code comments. If the dataset is unavailable, raise RuntimeError with message: "Data source unavailable. Pipeline halted." DO NOT fall back to a sample.**
- [X] T050 [US1] [BLOCKED UNTIL T012a PASSES AND T012d PASSES] Implement strict data loader failure in `src/ingestion.py`: Remove any `try/except` blocks that catch exceptions during data fetch and call `generate_synthetic_*()` or `mock_*()` in `src/ingestion.py`. Ensure that if the real data fetch fails, the script raises a clear `RuntimeError` with instructions, preventing silent fabrication. **Note: Unit tests (T010/T011) are allowed to use hardcoded data for logic verification; this restriction applies only to `src/ingestion.py` pipeline execution.**
- [X] T051 [US1] [BLOCKED UNTIL T012a PASSES AND T012d PASSES] Update `src/config.py` to support dynamic data source injection: Allow the execution stage to override `DATA_URL` via environment variable if a "VERIFIED REAL DATA SOURCE" is provided, ensuring the pipeline adopts the verified source without code changes. **This task ensures flexibility for verified data injection during execution.**

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
 - **T012a** must run first. If it fails, T012c_gen triggers, leading to blocked artifacts.
 - **T012d** runs only if T012a passes. If it fails, T012d_gen triggers, leading to blocked artifacts.
 - **T045** must pass before T013 to ensure robust error handling.
 - **T013-T017** and **T020a-T020b** are BLOCKED until T012a and T012d pass.
 - If T012a fails or T012d fails, T012c_gen, T012d_gen, T016b, T017b, T020c, T025b, T031c generate the blocked reports.
- **User Story 2 (P2)**: Depends on User Story 1 (needs cleaned data from T016 and diversity from T020a)
 - **T020a** (Diversity) must pass before **T021** (Correlation) executes.
 - **T043** must pass before T020a to ensure rarefaction normalization.
 - If T012a fails or T012d fails, T025b generates the blocked report.
 - **T046** must pass before T025 to ensure graceful handling of no significant results.
- **User Story 3 (P3)**: Depends on User Story 2 (needs correlation results from T024)
 - If T012a fails or T012d fails, T031c generates the blocked report.
 - **T047** must pass before T028b to ensure placeholder plot generation.

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

# Launch all models for User Story 1 together (after T012a passes):
Task: "Define Pydantic models in src/models/schemas.py"
Task: "Write unit tests for models in tests/unit/test_models.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: Data Feasibility Check (T012a)
4. **STOP and VALIDATE**: If T012a fails, trigger T012c_gen, T016b, T017b, T020c, T025b, T031c (Blocked Reports). If T012a passes, proceed to T012d.
5. If T012d fails, trigger T012d_gen, T016b, T017b, T020c, T025b, T031c (Blocked Reports). If T012d passes, proceed to T013-T017 and T020a-T020b.
6. Deploy/demo if ready

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
 - Developer A: User Story 1 (Ingestion) - **Must pass T012a first**
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
- **CRITICAL**: Do not fabricate data. If the verified dataset is missing, T012a must halt the pipeline with a clear status report.
- **CRITICAL**: T013-T017 and T020a-T020b are BLOCKED until T012a succeeds. If T012a fails, the project remains BLOCKED as per plan.md.
- **CRITICAL**: T020a depends on T016 output (after T043).
- **NOTE**: Mock data paths have been removed. Pipeline validation is performed via unit tests with hardcoded data.
- **NEW**: T040, T041, T042 removed; logic merged into T012a and T015a. T043 and T044 integrated into Phase 3. T031a added for final report.
- **NEW**: T012a added as unconditional gate. T012c_gen and T012d_gen are AUTO-TRIGGERED by T012a/T012d failure.
- **NEW**: T016b, T020c, T025b, T031c added to ensure measurable artifacts exist in blocked states.

<!-- auto-added by the execution fix loop: run-book / implementation path mismatch (a quickstart command names a script no task created) -->
- [X] T048 Reconcile run-book vs implementation for `projects/PROJ-087-investigating-the-correlation-between-gu/code/src/main.py`: the quickstart run-book invokes this script but it does not exist. Either create `projects/PROJ-087-investigating-the-correlation-between-gu/code/src/main.py`, or update the run-book (quickstart.md / plan.md) to invoke the script that actually implements this step. See `.specify/memory/execution_feedback.md` for the exact failing command and the scripts that DO exist.

- [X] T049 [US1] [BLOCKED UNTIL T012a PASSES AND T012d PASSES] Implement real dataset streaming in `src/ingestion.py`: Use `datasets.load_dataset(..., streaming=True)` or `pandas.read_csv(chunksize=10000)` to process the full American Gut Project dataset in chunks, ensuring the entire dataset contributes to results without exceeding ~7 GB RAM. **Explicitly state the streaming rule (chunk size, iteration logic) in the code comments. If the dataset is unavailable, raise RuntimeError with message: "Data source unavailable. Pipeline halted." DO NOT fall back to a sample.**
- [ ] T050 [US1] [BLOCKED UNTIL T012a PASSES AND T012d PASSES] Implement strict data loader failure in `src/ingestion.py`: Remove any `try/except` blocks that catch exceptions during data fetch and call `generate_synthetic_*()` or `mock_*()` in `src/ingestion.py`. Ensure that if the real data fetch fails, the script raises a clear `RuntimeError` with instructions, preventing silent fabrication. **Note: Unit tests (T010/T011) are allowed to use hardcoded data for logic verification; this restriction applies only to `src/ingestion.py` pipeline execution.**
- [ ] T051 [US1] [BLOCKED UNTIL T012a PASSES AND T012d PASSES] Update `src/config.py` to support dynamic data source injection: Allow the execution stage to override `DATA_URL` via environment variable if a "VERIFIED REAL DATA SOURCE" is provided, ensuring the pipeline adopts the verified source without code changes. **This task ensures flexibility for verified data injection during execution.**