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

- [ ] T001 Create project structure per implementation plan: Execute `mkdir -p src data/raw data/processed tests/unit tests/integration docs` and create empty `__init__.py` in `src`, `tests`, `tests/unit`, `tests/integration`.
- [ ] T002 Initialize Python 3.11 project with pinned dependencies: Create `requirements.txt` containing `pandas>=2.0`, `scikit-bio>=0.5.9`, `scipy>=1.10`, `matplotlib>=3.7`, `seaborn>=0.12`, `requests>=2.28`, `pytest>=7.0`, `pydantic>=2.0`, `ruff>=0.1.0`. Run `pip install -r requirements.txt` then `pip freeze > requirements.txt`. <!-- FAILED: unspecified -->
- [ ] T003 [P] Configure linting (ruff) and formatting (black): Create `pyproject.toml` with `[tool.ruff]` rules set to `["E", "F", "W", "I"]` and `[tool.black]` line-length 88.
- [ ] T004 [P] Setup data directory structure (`data/raw/`, `data/processed/`, `data/processed/plots/`): Ensure directories exist and contain `.gitkeep` files.
- [ ] T005 [P] Create base configuration loader in `src/config.py`: Implement `load_config()` function reading `DATA_URL`, `RANDOM_SEED`, and `LOG_LEVEL` from environment variables with defaults.
- [ ] T006 [P] Implement logging infrastructure in `src/logging_config.py`: Configure root logger with format `%(asctime)s - %(levelname)s - %(message)s` and level `INFO`.
- [ ] T009 [P] Setup content hashing utility in `src/utils/hashing.py`: Implement `def compute_sha256(file_path: str) -> str` function.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

**Note**: Specific data models are deferred to Phase 3 until the data schema is verified.

- [X] T010 [P] [US1] Unit test for antibiotic exclusion logic in `tests/unit/test_ingestion.py`: Implement `test_antibiotic_exclusion_logic()` verifying samples with `antibiotic_use_last_3m=True` are filtered.
- [X] T011 [P] [US1] Unit test for sleep data validation in `tests/unit/test_ingestion.py`: Implement `test_sleep_data_validation()` verifying samples with null `sleep_efficiency` or `sleep_duration_hours` are filtered.

**Checkpoint**: Tests for US1 ready. Implementation blocked until T012/T012b pass.

---

## Phase 3: User Story 1 - Data Ingestion and Preprocessing Pipeline (Priority: P1) 🎯 MVP

**Goal**: Automatically download, filter, and merge microbiome data with sleep metadata, excluding samples with antibiotic use or missing sleep data.

**Independent Test**: The pipeline can be tested by running the ingestion script and verifying that the output CSV contains only rows where `antibiotic_use_last_3m` is false/null and `sleep_efficiency`/`sleep_duration_hours` are not null.

**⚠️ CRITICAL BLOCKER**: The plan states the project is BLOCKED until a verified dataset is found. **T012a and T012b are the hard gates.** If T012a or T012b fails, T013-T017 and T037-T038 are BLOCKED.

### Implementation for User Story 1

- [X] T012a [US1] Implement Data Feasibility Check (URL) in `src/ingestion.py`: Verify the existence of the verified data source URL (from plan.md). **If missing, raise FileNotFoundError and exit with code 1.**
- [X] T012b [US1] [BLOCKED UNTIL T012a PASSES] Implement Schema Verification in `src/ingestion.py`: Fetch a sample/headers of the source. Verify file format (BIOM/CSV) and presence of required columns (`antibiotic_use_last_3m`, `sleep_efficiency`, `sleep_duration_hours`). **If missing, raise FileNotFoundError and exit with code 1.**
- [X] T013 [US1] [BLOCKED UNTIL T012b PASSES] Implement download logic with exponential backoff in `src/ingestion.py`. **Must use the verified URL from the plan's '# Verified datasets' block.**
- [X] T014 [US1] [BLOCKED UNTIL T012b PASSES] Implement filtering logic in `src/ingestion.py` to exclude antibiotic users and missing sleep data. **This task generates the exclusion counts.**
- [X] T015 [US1] [BLOCKED UNTIL T012b PASSES] Implement merging of OTU tables and metadata in `src/ingestion.py`.
- [ ] T016 [US1] [BLOCKED UNTIL T012b PASSES] Save cleaned dataset to `data/processed/cleaned_microbiome_sleep.csv`.
- [~] T017 [US1] [BLOCKED UNTIL T012b PASSES] Log exclusion rates to satisfy SC-001: Capture `total_initial_sample_count`, `excluded_count`, and calculate/store `exclusion_proportion` in `data/processed/ingestion_report.json`.

### Model Definition (Deferred until Schema Verified)

- [~] T037 [US1] [BLOCKED UNTIL T012b PASSES] Define Pydantic models (`MicrobiomeSample`, `SleepMetric`, `CorrelationResult`) in `src/models/schemas.py` based on the verified schema from T012b.
- [X] T038 [US1] [BLOCKED UNTIL T012b PASSES] Write unit tests for models in `tests/unit/test_models.py`: Implement `test_microbiome_sample_instantiation()` and `test_sleep_metric_instantiation()`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (if T012b passed).

---

## Phase 4: User Story 2 - Statistical Correlation Analysis (Priority: P2)

**Goal**: Compute Spearman rank correlations between alpha-diversity indices and sleep metrics with Benjamini-Hochberg correction.

**Independent Test**: The analysis script can be tested on a small, synthetic dataset with known correlation coefficients to verify that the calculated Spearman r-values and adjusted p-values match expected mathematical results.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for Spearman correlation calculation in `tests/unit/test_correlation.py`: Implement `test_spearman_correlation_calculation()`.
- [X] T019 [P] [US2] Unit test for Benjamini-Hochberg correction in `tests/unit/test_correlation.py`: Implement `test_benjamini_hochberg_correction()`.

### Implementation for User Story 2

- [ ] T020a [US2] Implement rarefaction logic in `src/diversity.py`: Create function `rarefy_table(counts, depth)` to subsample OTU tables to a fixed sequencing depth.
- [ ] T020b [US2] [BLOCKED UNTIL T020a PASSES] Implement alpha-diversity computation (Shannon, Simpson, Observed OTUs) **using the rarefied table** in `src/diversity.py`. **Requires: data/processed/cleaned_microbiome_sleep.csv (from T016).** <!-- FAILED: unspecified -->
- [ ] T021 [US2] Implement Spearman rank correlation test between diversity indices and sleep variables in `src/correlation.py`.
- [ ] T022 [US2] Implement Benjamini-Hochberg FDR correction on p-values in `src/correlation.py`.
- [ ] T023 [US2] Flag correlations: Add column `is_moderate` (|r| > 0.3) and column `is_meaningful` (q-value < 0.05 AND |r| > 0.3) to the results DataFrame in `src/correlation.py` to satisfy SC-002 machine-verifiability.
- [ ] T024 [US2] Save correlation results (r, p, q, significance, is_moderate, is_meaningful) to `data/processed/correlation_results.csv`.
- [ ] T025 [US2] Implement logic to handle "No significant associations" case gracefully in `src/correlation.py`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently.

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate scatterplots with regression lines and boxplots by sleep quartiles for significant correlations.

**Independent Test**: The visualization module can be tested by generating a plot file and verifying that the output image file exists, contains the correct axis labels, and displays the regression line.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Unit test for plot generation in `tests/unit/test_viz.py`: Implement `test_scatterplot_generation()`.

### Implementation for User Story 3

- [ ] T027 [US3] Implement scatterplot generation with regression lines for significant correlations in `src/viz.py`.
- [ ] T028 [US3] Implement boxplot generation by sleep quartile in `src/viz.py`.
- [ ] T029 [US3] Compile final report including summary table of correlations in `src/report.py`.
- [ ] T030 [US3] Save all plot artifacts to `data/processed/plots/`.
- [ ] T031 [US3] Generate final HTML/PDF report with all findings and "No significant associations" handling.

**Checkpoint**: All user stories should now be independently functional.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Documentation updates: Add 'Usage Examples' and 'Data Source' sections to `README.md` and update `docs/` with pipeline flow.
- [ ] T033 Code cleanup and refactoring: Remove unused imports and refactor T014 to use generator expressions for memory efficiency.
- [ ] T034 Performance optimization: Optimize T015 (merge) to reduce RAM usage by [deferred] using chunked processing.
- [ ] T035 [P] Implement `tests/integration/test_reproducibility.py`: Run the full pipeline twice, compute **SHA-256 hashes** of `data/processed/cleaned_microbiome_sleep.csv` and all files in `data/processed/plots/`, and assert the hashes match between runs to verify reproducibility (SC-005).
- [ ] T036 Run quickstart.md validation

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
 - **T012a/T012b** must pass before T013-T017 and T037-T038 execute.
- **User Story 2 (P2)**: Depends on User Story 1 (needs cleaned data from T016)
 - **T020a** (Rarefaction) must pass before **T020b** (Diversity) executes.
- **User Story 3 (P3)**: Depends on User Story 2 (needs correlation results from T024)

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

# Launch all models for User Story 1 together (after T012b passes):
Task: "Define Pydantic models in src/models/schemas.py"
Task: "Write unit tests for models in tests/unit/test_models.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (T012a/T012b must pass first)
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
 - Developer A: User Story 1 (Ingestion) - **Must pass T012a/T012b first**
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
- **CRITICAL**: Do not fabricate data. If the verified dataset is missing, T012a/T012b must halt the pipeline with a clear error.
- **CRITICAL**: T013-T017 and T037-T038 are BLOCKED until T012b succeeds. If T012b fails, the project remains BLOCKED as per plan.md.
- **CRITICAL**: T020b depends on T016 output.
- **CRITICAL**: T020b depends on T020a output.