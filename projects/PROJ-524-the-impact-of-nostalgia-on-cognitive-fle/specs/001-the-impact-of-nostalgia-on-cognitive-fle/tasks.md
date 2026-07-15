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

- [ ] T001a [P] Create data directory: `data/raw/`
- [ ] T001b [P] Create data directory: `data/processed/`
- [ ] T001c [P] Create data directory: `data/results/`
- [ ] T001d [P] Create empty placeholder files: `code/__init__.py`, `tests/__init__.py`, `README.md`
- [ ] T001e [P] Create stimuli directory: `data/stimuli/`

- [ ] T002 [P] Create `requirements.txt` with pinned versions for: pandas, scipy, statsmodels, numpy, pyyaml, openml, datasets, requests
- [~] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on plan.md):

- [X] T004 [P] Implement `code/utils.py` with checksum (SHA-256) helpers, logging setup, and versioning logic
- [X] T005 [P] Setup `code/reference_validator.py` to validate citations and enforce title overlap ≥ 0.7
- [X] T006 [P] Create base configuration management in `code/config.py` (env vars, paths)
- [ ] T007 [P] Setup `contracts/` directory and generate `dataset.schema.yaml` and `output.schema.yaml` based on plan.md entities

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Pre-processing (Priority: P1) 🎯 MVP

**Goal**: Ingest publicly available WCST/Executive Function data and nostalgia stimuli, validate age ≥ 65, and produce a clean, aligned dataframe.

**Independent Test**: The system can be fully tested by running the data loader script on a source dataset containing at least 100 records and verifying the output contains a dataframe with all valid participant records found, matching stimulus IDs, and non-null cognitive metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Contract test for schema validation in `tests/contract/test_dataset_schema.py`
- [X] T009 [P] [US1] Integration test for data ingestion pipeline in `tests/integration/test_ingestion.py`

### Implementation for User Story 1

- [X] T010 [P] [US1] Implement `code/ingestion.py` to fetch data from OpenML/HuggingFace or load local files with checksum verification
- [X] T011 [P] [US1] Implement data validation logic in `code/ingestion.py`: filter `age >= 65`, exclude missing `stimulus_type`, log `ERR_MISSING_AGE_FIELD`
- [ ] T012 [US1] **COMBINED EXCLUSION LOGIC**: Implement logic to handle missing age (check `birth_year` fallback), missing cognitive scores, and invalid records. Exclude records and write a **single consolidated** `data/processed/exclusion_log.json` containing counts for `ERR_MISSING_AGE_FIELD`, `ERR_MISSING_BIRTH_YEAR`, `ERR_MISSING_SCORE`.
- [~] T013b [US1] **NEW**: Validate presence of 'MMSE' column in raw dataset; if missing, set `has_mmse=False` flag in config and log warning `ERR_MMSE_MISSING`. If present, set `has_mmse=True`.
- [ ] T014a [US1] Create `data/processed/cleaned_dataset.csv` with columns: `participant_id`, `stimulus_type` (nostalgia/control), `perseverative_errors`, `categories_completed`, `age`. **Depends on T012 (exclusions) and T013b (MMSE flag for downstream filtering logic).**
- [~] T014b [US1] **NEW**: Calculate and log the percentage of valid records (age ≥ 65, non-null metrics) vs total raw input records in `data/processed/validity_metrics.json` to satisfy SC-001.
- [~] T015 [US1] **REVISED**: Implement stimulus file integrity check: Fetch canonical checksum from the dataset's `metadata.json` or fallback to GitHub release asset checksum; compare against local file SHA-256; log mismatch as `ERR_STIMULUS_CORRUPT`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis and Hypothesis Testing (Priority: P2)

**Goal**: Execute statistical comparison of cognitive flexibility metrics between nostalgia and control conditions using Welch's t-test (between-subjects), calculate effect sizes, and apply corrections.

**Independent Test**: The analysis can be fully tested by running the statistical module on a synthetic dataset with known effect sizes and verifying the output correctly identifies the calculated p-value and calculates the Cohen's d within a reasonable margin of error.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Contract test for statistical output schema in `tests/contract/test_analysis_output.py`
- [X] T017 [P] [US2] Integration test for statistical pipeline with synthetic data in `tests/integration/test_analysis.py`

### Implementation for User Story 2

- [X] T018 [P] [US2] Implement `code/analysis.py` statistical functions: **Welch's independent samples t-test (NOT paired)**. **NOTE: This overrides spec FR-002 per Plan.md Critical Design Note. Kickback required for spec amendment.**
- [~] T019 [US2] Implement multiple-comparison correction (Bonferroni) for `perseverative_errors` and `categories_completed`
- [~] T020 [US2] Calculate and report Cohen's d with 95% confidence intervals for all primary comparisons
- [~] T021 [US2] Calculate statistical power and Minimum Detectable Effect Size (MDES) for the observed effect; **Append power and MDES values to `data/results/statistical_report.json`**
- [ ] T022 [US2] Generate `data/results/statistical_report.json` containing p-values, corrected p-values, effect sizes, **power**, **MDES**, and power analysis results
- [~] T023 [US2] Add error handling for cases where variance is zero or sample size is too small

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Sensitivity Analysis and Robustness Check (Priority: P3)

**Goal**: Perform sensitivity analysis by sweeping significance thresholds and checking robustness against cognitive impairment exclusions.

**Independent Test**: The system can be tested by running the sensitivity module with a predefined set of thresholds (e.g., 0.01, 0.05, 0.1) and verifying the output table shows how the "significance" status changes across these values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Contract test for sensitivity report schema in `tests/contract/test_sensitivity_output.py`
- [ ] T025 [P] [US3] Integration test for sensitivity analysis pipeline in `tests/integration/test_sensitivity.py`

### Implementation for User Story 3

- [ ] T026 [P] [US3] Implement sensitivity sweep in `code/analysis.py`: test thresholds {, 0.1} and other representative significance levels
- [ ] T027 [US3] **REVISED**: Implement robustness check: **Read `MMSE` column values** from the dataset. If `has_mmse=True` (from T013b), exclude participants with `MMSE < 24` and re-run analysis. If `False`, log `ERR_MMSE_MISSING_SKIPPED` and skip this filter step.
- [ ] T028 [US3] Generate `data/results/sensitivity_report.json` with significance status per threshold and subset comparison
- [ ] T029 [US3] Add logic to flag "sensitive to threshold choice" if p-value is borderline (≈ 0.05)
- [ ] T030 [US3] Update final report to include sensitivity analysis summary and stability metrics

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [ ] T031 [P] Documentation updates in `README.md` and `docs/`
- [ ] T032 Code cleanup and refactoring
- [ ] T033 [P] Additional unit tests in `tests/unit/`
- [ ] T034 [P] Run `code/reference_validator.py` to validate all citations in the final report
- [ ] T035b [P] **NEW**: Implement runtime monitoring logic: **If runtime > 6 hours, log warning `WARN_TIMEOUT` but continue to completion** (per FR-007)
- [ ] T036a [US1/US2/US3] **NEW**: Parse source metadata from `data/raw/` (metadata.json or CSV headers) to extract validation study citation
- [ ] T036b [US1/US2/US3] **NEW**: Run `code/reference_validator.py` on extracted citation (from T036a) to verify against primary source (format/existence check)
- [ ] T036d [US1/US2/US3] **NEW**: Fetch the cited study's full metadata (via DOI/URL) to verify the `stimuli_validated` claim (content check) for SC-006.
- [ ] T036c [US1/US2/US3] **NEW**: Generate `paper/001_results.md` including verified citation status (from T036b) and scientific validity status (from T036d).

- [ ] T037 [P] Update `state/state.yaml` with final artifact hashes and timestamps

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

- **T001a, T001b, T001c, T001d, T001e**: No dependencies.
- **T002, T003**: Depends on T001a-T001e.
- **T004-T007**: Depends on T002, T003.
- **T008-T009**: Depends on T004-T007.
- **T010-T015**: Depends on T004-T007.
- **T012**: Depends on T010.
- **T013b**: Depends on T010 (needs ingestion to check column).
- **T014a**: Depends on T011, T012, T013b.
- **T014b**: Depends on T010, T012 (needs total raw count and excluded count).
- **T016-T023**: Depends on T014a.
- **T024-T030**: Depends on T022.
- **T034-T037**: Depends on T022, T030.
- **T036a**: Depends on T014a (needs metadata from processed/raw data).
- **T036b**: Depends on T036a (needs extracted citation).
- **T036d**: Depends on T036b (needs the citation to fetch content).
- **T036c**: Depends on T036b, T036d.
- **T037**: Depends on T036c.

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
- **Critical**: Ensure all statistical tests use Welch's independent samples t-test (between-subjects) as per plan.md, NOT paired t-tests.
- **Critical**: If real-world data is unavailable, clearly label results as simulation-only in the final report.
- **Critical**: T013b must run before T027 to ensure MMSE column existence is validated before filtering.
- **Critical**: T036a must run before T036b (citation extraction precedes verification).
- **Critical**: T012 handles ALL exclusion logic to prevent race conditions on `exclusion_log.json`.
- **Critical**: T014b must run after T012 to calculate valid record percentages.
- **Critical**: T014a depends on T013b for the `has_mmse` flag context.