# Tasks: The Impact of Nostalgia on Cognitive Flexibility in Aging Adults

**Input**: Design documents from `/specs/001-nostalgia-cognitive-flexibility/`
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

- [ ] T001 [P] Create all required data directories: `data/raw/`, `data/processed/`, `data/results/`, `data/stimuli/`, `contracts/`, `code/`, `tests/`, `paper/`. **Depends on**: None.

- [X] T002 [P] Create `requirements.txt` with pinned versions for: pandas, scipy, statsmodels, numpy, pyyaml, openml, datasets, requests, pytest, black, ruff. **Depends on**: T001.

- [X] T003a [P] Create `pyproject.toml` with `[tool.black]` (line-length=88) and `[tool.ruff]` (lint.select = ["E", "F"]) sections to configure linting and formatting.
- [X] T003b [P] Verify `pyproject.toml` exists and contains valid configuration sections for black and ruff. **Depends on**: T003a.

- [X] T004 [P] Implement `code/utils.py` with checksum (SHA-256) helpers, logging setup, and versioning logic. **Depends on**: T003b.
- [X] T005 [P] Setup `code/reference_validator.py` to validate citations and enforce title overlap ≥ 0.7. **Depends on**: T004.
- [X] T006 [P] Create base configuration management in `code/config.py` (env vars, paths). **Note**: Do not store runtime flags here. **Depends on**: T004.
- [ ] T007 [P] Setup `contracts/` directory structure (files generated in Phase 2). **Depends on**: T001.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: Foundational (Contracts & Documentation)

**Purpose**: Generate required artifacts defined in plan.md Phase 1 output that block all user stories.

- [ ] T020a [P] **GENERATE CONTRACTS**: Generate `contracts/dataset.schema.yaml` and `contracts/output.schema.yaml` based on the Input/Output Schema in `spec.md`. Validate that `participant_id`, `age`, `stimulus_type`, `perseverative_errors`, `categories_completed`, and optional `MMSE` are defined. **Depends on**: T007.
- [ ] T020b [P] **GENERATE DATA MODEL**: Create `specs/001-nostalgia-cognitive-flexibility/data-model.md` explicitly documenting the entities, relationships, and the optional nature of the `MMSE` field. **Depends on**: T020a.
- [ ] T020c [P] **GENERATE QUICKSTART**: Create `specs/001-nostalgia-cognitive-flexibility/quickstart.md` with installation instructions, dependency installation, and a "Hello World" example to run the ingestion pipeline on a sample dataset. **Depends on**: T002, T003a.

**Checkpoint**: Foundational artifacts ready - User Stories can now begin.

---

## Phase 3: User Story 1 - Data Ingestion and Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Ingest publicly available WCST/Executive Function data and nostalgia stimuli, validate age ≥ 65, and produce a clean, aligned dataframe.

**Independent Test**: The system can be fully tested by running the data loader script on a source dataset containing at least 100 records and verifying the output contains a dataframe with all valid participant records found, matching stimulus IDs, and non-null cognitive metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Contract test for schema validation in `tests/contract/test_dataset_schema.py`. **Depends on**: T020a.
- [X] T009 [P] [US1] Integration test for data ingestion pipeline in `tests/integration/test_ingestion.py`. **Depends on**: T008.

### Implementation for User Story 1

- [ ] T010a [US1] **IMPLEMENT DATA INGESTION**: **Dynamically search** OpenML (`openml.datasets.list_datasets`) and HuggingFace (`datasets.list_datasets`) for datasets containing keywords "WCST", "cognitive", "aging", or "executive function". **If a dataset matching the schema is found**, fetch it. **If no valid real dataset is found**, fetch a deterministic fallback dataset (e.g., OpenML ID 12345 or a specific HuggingFace dataset) or execute `code/synthetic_data.py` with a fixed seed to generate a deterministic synthetic dataset for pipeline validation. **Set `simulation_mode=True` in `data/raw/metadata.json` and log `SIMULATION_FALLBACK` to `data/processed/exclusion_log.json`**. Save the raw fetched/generated dataset to `data/raw/raw_dataset.csv`. Validate schema contains `age`, `stimulus_type`, `perseverative_errors`, `categories_completed`. **Depends on**: T004-T007, T020a.
- [ ] T010b [US1] Validate dataset source against Constitution Principle II: Check `metadata.json` (if present) for validation study citation; if missing, log `WARN_NO_CITATION` but proceed with `simulation_mode=False` if real data fetched. Verify citation title overlap ≥ 0.7 using `code/reference_validator.py`. **Depends on**: T010a.
- [ ] T011 [P] [US1] Implement data validation logic in `code/ingestion.py`: filter `age >= 65`, exclude missing `stimulus_type`, log `ERR_MISSING_AGE_FIELD`. **Depends on**: T010a.
- [ ] T012a [US1] **AGE EXCLUSION**: Exclude records where `age` is missing or < 65. Return count of excluded records to shared state. **Depends on**: T010a, T011.
- [ ] T012b [US1] **SCORE EXCLUSION**: Exclude records where `perseverative_errors` or `categories_completed` are null. Return count of excluded records to shared state. **Depends on**: T010a, T011.
- [ ] T012d [US1] **MMSE FLAG**: Validate presence of 'MMSE' column in `data/raw/raw_dataset.csv`. **Write `has_mmse` (True/False) to `data/processed/mmse_flag.json`**. If missing, set `has_mmse=False` and log `ERR_MMSE_MISSING`. If present, set `has_mmse=True`. **Depends on**: T010a.
- [ ] T012e [US1] **MMSE EXCLUSION (IMPLEMENTATION)**: **Read `has_mmse` from `data/processed/mmse_flag.json`**. If `has_mmse=True`, implement filtering logic in `code/ingestion.py` to exclude records where `MMSE < 24` and write the filtered dataframe to `data/processed/cleaned_dataset_intermediate.csv`. Return count of excluded records to shared state. If `has_mmse=False`, log `SKIP_MMSE_EXCLUSION` and copy `data/raw/raw_dataset.csv` (with age/score exclusions already applied) to `data/processed/cleaned_dataset_intermediate.csv`. **Depends on**: T012d, T012a, T012b.
- [ ] T012c [US1] **GENERATE EXCLUSION LOG**: Read exclusion counts from shared state (T012a, T012b, T012e) and write `data/processed/exclusion_log.json` with keys `ERR_MISSING_AGE_FIELD`, `ERR_MISSING_SCORE`, `ERR_MMSE_IMPAIRED`, and `SIMULATION_FALLBACK` (if applicable). **Depends on**: T012a, T012b, T012e.
- [ ] T014a [US1] **GENERATE CLEANED DATASET**: Create `data/processed/cleaned_dataset.csv` by consuming `data/processed/cleaned_dataset_intermediate.csv` (from T012e). Columns: `participant_id`, `stimulus_type` (nostalgia/control), `perseverative_errors`, `categories_completed`, `age`. **Depends on**: T012c, T012e.
- [ ] T014b [US1] **VALIDITY METRICS**: Calculate percentage of valid records (age >= 65, non-null metrics, MMSE >= 24 if available) vs total raw input records. Write to `data/processed/validity_metrics.json`. Must satisfy SC-001 (≥90% target). **Depends on**: T012c.
- [ ] T015a [US1] **GENERATE METADATA**: Create `data/raw/metadata.json` with keys `dataset_source`, `validation_study_doi` (if found in source), `stimuli_checksums` (SHA-256 of all files in `data/stimuli/`), and `simulation_mode` (boolean). **If `data/stimuli/` is empty and `simulation_mode=True`, set `stimuli_checksums` to null and log `INFO_SIMULATION_NO_STIMULI`**. **This task MUST run regardless of data fetch success**. **Depends on**: T010a.
- [ ] T015 [US1] **STIMULUS INTEGRITY**: **Read `simulation_mode` from `data/raw/metadata.json`**. If `simulation_mode=True`, log `SKIP_STIMULUS_CHECK_SIMULATION` and complete. If `simulation_mode=False`, validate stimulus files in `data/stimuli/` against `data/raw/metadata.json` checksums. If mismatch, log `ERR_STIMULUS_CORRUPT` and halt. If missing files, log `ERR_STIMULUS_MISSING` and halt. **Depends on**: T015a, T010a.
- [ ] T015b [US1] **STIMULUS VALIDATION**: If `data/raw/metadata.json` contains `validation_study_doi`, log `INFO_STIMULUS_VALIDATED`. Else, log `WARN_STIMULUS_NO_VALIDATION`. **Depends on**: T015a.
- [ ] T042 [US1] **ENFORCE STREAMING**: Update `code/ingestion.py` to use `datasets.load_dataset(..., streaming=True)` for any dataset > 100MB to ensure RAM compliance on the 7GB runner. **Depends on**: T010a.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis and Hypothesis Testing (Priority: P2)

**Goal**: Execute statistical comparison of cognitive flexibility metrics between nostalgia and control conditions using Welch's t-test (between-subjects), calculate effect sizes, and apply corrections.

**Independent Test**: The analysis can be fully tested by running the statistical module on a synthetic dataset with known effect sizes and verifying the output correctly identifies the calculated p-value and calculates the Cohen's d within a reasonable margin of error.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T016 [P] [US2] Contract test for statistical output schema in `tests/contract/test_analysis_output.py`. **Depends on**: T020a.
- [ ] T017 [P] [US2] Integration test for statistical pipeline with synthetic data in `tests/integration/test_analysis.py`. **Depends on**: T016.

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement `code/analysis.py` statistical functions: **Welch's independent samples t-test (NOT paired)**. **Input Requirement**: Requires two distinct groups defined by `stimulus_condition` (nostalgia vs control) in the input dataframe. **NOTE: This aligns with spec FR-002 (Welch's t-test) and Plan.md between-subjects design**. **Depends on**: T014a.
- [ ] T019 [US2] **BONFERRONI CORRECTION**: Implement multiple-comparison correction (Bonferroni) for `perseverative_errors` and `categories_completed`. Adjust alpha by the number of outcomes. Report corrected p-values. **Depends on**: T018.
- [ ] T020 [US2] **EFFECT SIZE**: Calculate and report Cohen's d with 95% confidence intervals for all primary comparisons using `statsmodels.stats.power.tt_ind_solve_power` or `scipy.stats`. **Depends on**: T018.
- [ ] T021 [US2] Calculate statistical power and Minimum Detectable Effect Size (MDES) for the observed effect; **Append power and MDES values to `data/results/statistical_report.json`**. **Depends on**: T020.
- [ ] T022 [US2] Generate `data/results/statistical_report.json` containing p-values, corrected p-values, effect sizes, **power**, **MDES**, and power analysis results. **Depends on**: T019, T020, T021.
- [ ] T023 [US2] **ERROR HANDLING**: Add error handling for cases where variance is zero or sample size is too small (< 10 per group). Log `ERR_ZERO_VARIANCE` or `ERR_SMALL_SAMPLE` and skip affected test. **Depends on**: T018.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Robustness Check (Priority: P3)

**Goal**: Perform sensitivity analysis by sweeping significance thresholds and checking robustness against cognitive impairment exclusions.

**Independent Test**: The system can be tested by running the sensitivity module with a predefined set of thresholds (e.g., low, medium, and high values). and verifying the output table shows how the "significance" status changes across these values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_sensitivity_output.py`. **Depends on**: T020a.
- [ ] T025 [P] [US3] Integration test for sensitivity analysis pipeline in `tests/integration/test_sensitivity.py`. **Depends on**: T024.

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement sensitivity sweep in `code/analysis.py`: test thresholds including representative significance levels. **Depends on**: T022.
- [ ] T027a [US3] **MMSE ROBUSTNESS DATA PREP**: **Read from `data/raw/raw_dataset.csv`** (original raw data). Apply age and score exclusions (T012a, T012b) but **skip MMSE exclusion**. Write this pre-MMSE-exclusion dataset to `data/processed/cleaned_dataset_no_mmse_exclusion.csv`. **Depends on**: T010a, T012d.
- [ ] T027b [US3] **MMSE ROBUSTNESS ANALYSIS**: Re-run analysis (T018-T022) on `data/processed/cleaned_dataset_no_mmse_exclusion.csv` (output of T027a). Write results to `data/results/robustness_report.json`. **Note: This is a sensitivity check comparing with and without MMSE exclusion**. **Depends on**: T027a, T022, T012d.
- [ ] T028 [US3] **SENSITIVITY REPORT**: Generate `data/results/sensitivity_report.json` with significance status per threshold and subset comparison. **Depends on**: T026, T027b.
- [ ] T029 [US3] **BORDERLINE FLAG**: Add logic to flag "sensitive to threshold choice" if p-value is borderline (e.g., near the significance threshold). **Depends on**: T028.
- [ ] T030 [US3] **FINAL SENSITIVITY SUMMARY**: Update final report to include sensitivity analysis summary and stability metrics. **Depends on**: T028, T029.
- [ ] T041 [US3] **STRENGTHEN ROBUSTNESS**: Ensure the sensitivity analysis in `code/analysis.py` explicitly logs the "borderline" range (e.g., 0.04-0.06) and outputs a binary flag `is_sensitive_to_threshold` in `data/results/sensitivity_report.json` as required by FR-005. **Depends on**: T026.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T031a [P] **README INSTALLATION**: Update `README.md` with installation instructions, dependencies, and usage examples. **Depends on**: T002, T020c.
- [ ] T031b [P] **API DOCS**: Add API docs for `code/ingestion.py` and `code/analysis.py` functions. **Depends on**: T018, T010a.
- [ ] T032a [P] **REFACTOR ANALYSIS**: Refactor `code/analysis.py` to reduce cyclomatic complexity to < 10. **Method**: Extract data cleaning logic into `clean_data()` function in `code/ingestion.py` and split `run_analysis()` into `compute_stats()` and `generate_report()`. **Depends on**: T022.
- [ ] T032b [P] **REFACTOR INGESTION**: Refactor `code/ingestion.py` to improve modularity and error handling. **Method**: Split `fetch_data()` and `validate_schema()` into separate modules. **Depends on**: T010a.
- [ ] T033a [P] [US1] Unit test: `test_cleaning_filters_age` in `tests/unit/test_cleaning.py`. **Depends on**: T011.
- [ ] T033b [P] [US1] Unit test: `test_cleaning_filters_mmse` in `tests/unit/test_cleaning.py`. **Depends on**: T012e.
- [ ] T033c [P] [US2] Unit test: `test_welch_ttest` in `tests/unit/test_analysis.py`. **Depends on**: T018.
- [ ] T033d [P] [US3] Unit test: `test_sensitivity_sweep` in `tests/unit/test_sensitivity.py`. **Depends on**: T026.
- [ ] T034 [P] Run `code/reference_validator.py` to validate all citations in the final report. **Depends on**: T036b.
- [ ] T035b [P] **RUNTIME MONITORING**: Implement runtime monitoring logic: **If runtime > 6 hours, log warning `WARN_TIMEOUT` but continue to completion** (per FR-007). **Depends on**: T004.
- [ ] T036a [US1/US2/US3] **EXTRACT CITATION**: Parse source metadata from `data/raw/metadata.json` (from T015a) to extract `validation_study_doi`. **If missing, set to `null` and log `WARN_NO_DOI`**. **Depends on**: T015a.
- [ ] T036b [US1/US2/US3] **VERIFY CITATION**: Run `code/reference_validator.py` on extracted DOI (from T036a) to verify against primary source (format/existence check). **Depends on**: T036a.
- [ ] T036c [US1/US2/US3] **GENERATE PAPER**: Generate `paper/001_results.md` including verified citation status (from T036b), scientific validity status (from T015a/T015b), and **Stimulus Integrity status (from T015)**. **Depends on**: T036b, T015a, T015.

- [ ] T037 [P] Update `state/state.yaml` with final artifact hashes and timestamps. **Depends on**: T036c.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on cleaned data from US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on statistical results from US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Validation before Services/Analysis
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Specific Task Dependencies (Critical Execution Order)

- **T001**: No dependencies.
- **T002**: Depends on T001.
- **T003a, T003b**: Depends on T002.
- **T004-T007**: Depends on T003b.
- **T020a, T020b, T020c**: Depends on T007, T002, T003a.
- **T008-T009**: Depends on T004-T007, T020a.
- **T010a-T015b**: Depends on T004-T007, T020a.
- **T012a, T012b**: Depends on T010a.
- **T012d**: Depends on T010a (needs ingestion to check column).
- **T012e**: Depends on T012d (needs MMSE flag from JSON), T012a, T012b.
- **T012c**: Depends on T012a, T012b, T012e.
- **T014a**: Depends on T012c, T012e (consumes intermediate file).
- **T014b**: Depends on T012c.
- **T015a**: Depends on T010a (needs source info).
- **T015**: Depends on T015a, T010a.
- **T016-T023**: Depends on T014a.
- **T024-T030**: Depends on T022.
- **T027a**: Depends on T010a (raw data), T012d.
- **T027b**: Depends on T027a, T022, T012d.
- **T031a-T032b**: Depends on T014a, T022.
- **T034-T037**: Depends on T022, T030.
- **T036a**: Depends on T015a (needs metadata.json).
- **T036b**: Depends on T036a (needs extracted citation).
- **T036c**: Depends on T036b, T015a, T015.
- **T037**: Depends on T036c.
- **T042**: Depends on T010a (streaming logic integrated into ingestion).
- **T041**: Depends on T026 (borderline logic integrated into sensitivity sweep).

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
- **Critical**: Ensure all statistical tests use Welch's independent samples t-test (between-subjects) as per spec FR-002 and plan.md.
- **Critical**: If real-world data is unavailable, clearly label results as simulation-only in the final report (simulation_mode=True) and log `SIMULATION_FALLBACK`.
- **Critical**: T012d must run before T012e to ensure MMSE column existence is validated before filtering.
- **Critical**: T012e (MMSE Exclusion) is now part of the primary pipeline (US1), not just US3.
- **Critical**: T036a must run before T036b (citation extraction precedes verification).
- **Critical**: T012a, T012b, T012c, T012e handle ALL exclusion logic to prevent race conditions on `exclusion_log.json`.
- **Critical**: T014b must run after T012c to calculate valid record percentages including MMSE exclusions.
- **Critical**: T014a depends on T012e for the MMSE filter.
- **Critical**: T015a must run before T015 and T036a to provide metadata.json.
- **Critical**: T010a includes simulation mode ONLY if real fetch fails, labeled simulation_mode=True, and proceeds deterministically.
- **Critical**: T015 is conditional on `simulation_mode` to prevent failure when stimuli are missing in simulation mode.
- **Critical**: T015a generates metadata.json with simulation_mode flag regardless of data fetch success.
- **Critical**: T036c depends on T015 to ensure stimulus integrity is verified before paper generation.
- **Critical**: T003 (Linting) has been replaced by T003a/T003b to ensure executable config file creation.
- **Critical**: T042 ensures streaming is used for large datasets to comply with memory constraints.
- **Critical**: T041 ensures the borderline sensitivity flag is explicitly implemented per FR-005.
- **Critical**: T027a reads from raw data to ensure valid sensitivity analysis comparison.
- **Critical**: T012d and T012e use `data/processed/mmse_flag.json` for runtime state, not `code/config.py`.
- **Critical**: T027a reads `data/raw/raw_dataset.csv` (original fetch) to apply MMSE filter independently for robustness check.
- **Critical**: T010a saves raw data to `data/raw/raw_dataset.csv` to support T027a.
- **Critical**: T015a and T010a coordinate on `metadata.json` lifecycle (T010a sets flag, T015a finalizes metadata).
- **Critical**: T039 and T040 have been removed to resolve contradictions.
- **Critical**: T001 consolidates directory creation for clarity.