# Tasks: The Influence of Narrative Framing on Attitudes Towards AI Assistance

**Input**: Design documents from `/specs/001-narrative-framing-ai-attitudes/`
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

- [ ] T001 Create project structure per implementation plan (`code/`, `data/`, `tests/`, `data/raw/`, `data/processed/`, `data/stimuli/`, `data/ethics/`)
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (`pandas`, `numpy`, `scipy`, `statsmodels`, `textstat`, `vaderSentiment`, `pytest`)
- [ ] T003 [P] Configure linting (flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/00_ethics_gate.py` to check for IRB approval existence and block execution if missing (Constitution VI)
- [X] T005 Create base data schemas and validation utilities in `code/utils/data_validation.py`
- [X] T006 Setup random seed management utility in `code/utils/random_utils.py` to ensure reproducibility across all scripts
- [ ] T007 Configure logging infrastructure in `code/utils/logger.py` for audit trails of data processing steps
- [ ] T008 [US3] Implement `code/00_power_analysis.py` to perform prospective power analysis (G*Power equivalent) calculating required N for 80% power at d=0.4, alpha=0.05, and enforce the N=300 target for recruitment planning (FR-009, SC-002)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Stimulus Generation and Randomization (Priority: P1) 🎯 MVP

**Goal**: Generate two distinct, sentiment-balanced vignette texts and implement a randomized assignment script that assigns participants to conditions with a 50/50 split.

**Independent Test**: The system can be tested by running the stimulus generation script to output two CSV files (one per condition) and verifying via a unit test that the randomization script assigns unique user IDs to conditions with a 50/50 split distribution (within statistical tolerance) over a sufficiently large number of simulated runs.

### Sub-phase 3A: Test File Creation (Prerequisite to Implementation)

- [ ] T009 [P] [US1] Create test file `tests/test_stimuli.py` with test for readability check (Flesch-Kincaid diff ≤ 2.0)
- [~] T010 [P] [US1] Create test file `tests/test_stimuli.py` with test for sentiment check (VADER diff ≤ 0.05)
- [~] T011 [P] [US1] Create test file `tests/test_randomization.py` with test for randomization distribution (k runs, balanced split)

### Sub-phase 3B: Implementation

- [~] T012 [US1] Implement the stimulus generation script to generate "Partner" and "Tool" vignettes based on a controlled template, ensuring no other linguistic variables change
- [~] T013 [US1] Integrate `textstat` in `code/01_stimulus_generation.py` to calculate Flesch-Kincaid scores and enforce ≤ 2.0 point difference (FR-001, SC-001)
- [~] T014 [US1] Integrate `vaderSentiment` in `code/01_stimulus_generation.py` to calculate compound scores, enforce ≤ 0.05 difference, AND implement a rejection/regeneration loop with a `max_attempts` limit (e.g., 10) and a fallback strategy to log a warning and halt if constraints cannot be met (FR-010, SC-005)
- [~] T015 [US1] Implement `code/02_randomization.py` to Assign a unique Participant ID to exactly one condition (Partner/Tool) with a balanced ratio. (FR-002)
- [~] T016 [US1] Export generated vignettes to `data/stimuli/vignettes_partner.csv` and `data/stimuli/vignettes_tool.csv`
- [~] T017 [US1] Implement logic to immediately write randomization metadata (Participant ID, Condition, Timestamp) to `data/processed/randomization_log.json` BEFORE survey display to prevent drift (US-1, Constitution III)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Data Collection and Validation (Priority: P2)

**Goal**: Collect survey responses for attitude, perceived usefulness, trust, and manipulation checks, exporting them as a structured CSV with quality flags.

**Independent Test**: The system can be tested by submitting synthetic survey data for a cohort of participants (balanced across conditions) and verifying that the export process produces a CSV where all required columns exist, missing values are flagged, and the manipulation check correctly identifies participants who failed to recognize the framing.

### Pilot Study Validation (Must precede Main Data Collection)

- [~] T024 [US2] Implement `code/03_pilot_study.py` to execute a pilot study (n≥30) and validate that the manipulation check question accurately discriminates between readers and non-readers (FR-011)
- [~] T025 [P] [US2] Run pilot study validation and log results to `data/processed/pilot_validation_report.json`

### Main Data Collection Implementation

- [~] T019 [US2] Implement `code/04_data_collection.py` to ingest raw survey data (simulated or imported) and map responses to `Participant` entities
- [ ] T020 [P] [US2] Implement validation logic in `code/04_data_collection.py` to ensure Likert scales are integers within the expected range. (US-2, FR-003)
- [ ] T021 [P] [US2] Implement logic to flag `manipulation_check_failed` boolean based on the manipulation check question response (US-2, FR-003)
- [ ] T022 [US2] Implement logic to exclude partial responses (participants who abandoned halfway) from the final dataset (Edge Case)
- [ ] T023 [US2] Export cleaned data to `data/processed/cleaned_responses.csv` with columns: `participant_id`, `condition`, `manipulation_check`, `manipulation_check_failed`, AND individual raw item responses: `attitude_item_1` through `attitude_item_7`, `usefulness_item_1` through `usefulness_item_3`, `trust_item_1` through `trust_item_4` (FR-003, Constitution VII)
- [ ] T018 [P] [US2] Unit test for data validation (Likert range, no duplicates) in `tests/test_data_collection.py`
- [ ] T019 [P] [US2] Unit test for manipulation check flagging logic in `tests/test_data_collection.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Reporting (Priority: P3)

**Goal**: Perform independent-samples t-tests (or Welch's correction) and non-parametric Mann-Whitney U tests to compare conditions, calculating effect sizes and 95% confidence intervals.

**Independent Test**: The system can be tested by feeding it a synthetic dataset with a known effect size (e.g., d = 0.5) and verifying that the analysis script correctly identifies a significant difference (p < 0.05) and reports an effect size within 10% of the input value.

**Prerequisite**: T023 must be complete before T029 begins.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for Welch's t-test calculation and effect size (Cohen's d) in `tests/test_analysis.py`
- [ ] T027 [P] [US3] Unit test for Benjamini-Hochberg correction in `tests/test_analysis.py`
- [ ] T028 [P] [US3] Unit test for sensitivity analysis (exclusion of failed manipulation checks) in `tests/test_analysis.py`

### Implementation for User Story 3

- [ ] T029 [US3] Implement `code/05_analysis.py` to load `data/processed/cleaned_responses.csv`
- [ ] T030 [P] [US3] Implement normality check (Shapiro-Wilk) and homogeneity of variance check (Levene's) in `code/05_analysis.py` to justify test selection (US-3)
- [ ] T031a [US3] Implement independent-samples t-test (or Welch's t-test) for the Attitude Scale comparing Partner vs. Tool conditions (FR-004, FR-008)
- [ ] T031b [US3] Implement independent-samples t-test (or Welch's t-test) for the Usefulness Scale comparing Partner vs. Tool conditions (FR-004, FR-008)
- [ ] T031c [US3] Implement independent-samples t-test (or Welch's t-test) for the Trust Scale comparing Partner vs. Tool conditions (FR-004, FR-008)
- [ ] T032 [P] [US3] Calculate Cohen's d effect sizes and 95% confidence intervals for all primary comparisons (FR-005)
- [ ] T033 [US3] Implement Benjamini-Hochberg procedure to adjust p-values for the family of three tests (FR-006, SC-003)
- [ ] T034 [US3] Implement sensitivity analysis: re-run primary t-tests excluding participants where `manipulation_check_failed` is true (FR-007)
- [ ] T040 [US3] Perform full-sample robustness check: re-run t-tests INCLUDING all participants (ignoring manipulation check failures) to compare results against the primary analysis (Edge Cases, FR-007)
- [ ] T035 [US3] Implement robustness checks: Mann-Whitney U test and linear regression controlling for age/gender (US-3)
- [ ] T036 [US3] Implement power analysis (MDES) to calculate observed power based on actual N collected, compare against target, and flag the report as 'insufficient power' if N < 300 (FR-009, SC-002)
- [ ] T037 [US3] Generate final analysis report in `data/processed/analysis_report.json` containing p-values, t-statistics, Cohen's d, adjusted p-values, power flags, and robustness check results
- [ ] T045 [US3] Transform `data/processed/analysis_report.json` into a human-readable Markdown report (`data/processed/analysis_report.md`) with interpretations and effect sizes for the final paper (Constitution IV)
- [ ] T038 [US3] Ensure all statistical computations use only CPU-based libraries (`scipy`, `statsmodels`) and the entire pipeline completes in <30 minutes on a Multi-core CPU-only runner

The research question is [REDACTED], the method is [REDACTED], and the references are [REDACTED]. (FR-008, SC-004)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `docs/` summarizing the experimental design and analysis pipeline
- [ ] T041 Code cleanup and refactoring of `code/` directory
- [ ] T042 Performance optimization of `code/05_analysis.py` to ensure it stays well under the 30-minute runtime limit
- [ ] T043 [P] Additional unit tests (if requested) in `tests/`
- [ ] T044 Run `quickstart.md` validation to ensure the full pipeline runs end-to-end

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 (stimuli) and US2 (data) to run analysis

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
# Launch all test file creation for User Story 1 together (if tests requested):
Task: "Create test file tests/test_stimuli.py with test for readability check"
Task: "Create test file tests/test_stimuli.py with test for sentiment check"
Task: "Create test file tests/test_randomization.py with test for randomization distribution"

# Launch all models for User Story 1 together (Sequential within file):
Task: "Implement code/01_stimulus_generation.py to generate vignettes"
Task: "Integrate textstat in code/01_stimulus_generation.py"
Task: "Integrate vaderSentiment in code/01_stimulus_generation.py (Sequential to T012)"
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