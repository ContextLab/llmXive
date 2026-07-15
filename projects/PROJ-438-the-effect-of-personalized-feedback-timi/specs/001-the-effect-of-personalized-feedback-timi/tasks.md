# Tasks: The Effect of Personalized Feedback Timing on Skill Acquisition

**Input**: Design documents from `/specs/001-feedback-timing-analysis/`
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

- [X] T001 Create `projects/PROJ-438-the-effect-of-personalized-feedback-timi/code/` directory at the correct project path (Plan.md Project Structure)
- [X] T002 Create `projects/PROJ-438-the-effect-of-personalized-feedback-timi/data/raw/`, `data/processed/`, `data/cache/`, and `data/checksums/` directories with `.gitkeep`
- [X] T003 Create `projects/PROJ-438-the-effect-of-personalized-feedback-timi/tests/` directory at repository root
- [X] T004 Initialize Python 3.11 project with dependencies: pandas, numpy, statsmodels, pyyaml, requests, tqdm, scipy, pytest
- [X] T005 [P] Configure linting (flake8/black) and formatting tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Update spec.md FR-005 and User Story 3 header to explicitly mandate 'Cluster-Robust OLS' instead of 'Linear Mixed-Effects Models (LMM)' to align with Plan.md (Resolution of FR-005 vs Plan contradiction) <!-- ATOMIZE: requested -->
- [X] T007 [P] Implement configuration loader for dataset URLs and hyperparameters in `projects/PROJ-438-the-effect-of-personalized-feedback-timi/code/config.py`
- [X] T008 [P] Setup logging infrastructure to `projects/PROJ-438-the-effect-of-personalized-feedback-timi/code/logging_config.py` for reproducible audit trails
- [ ] T009 Create base data schema validation utilities in `projects/PROJ-438-the-effect-of-personalized-feedback-timi/code/schema.py` (aligns with `contracts/dataset.schema.yaml`)
- [ ] T010 Implement checksum utility for raw data integrity in `projects/PROJ-438-the-effect-of-personalized-feedback-timi/code/checksums.py`
- [X] T011 [P] Update spec.md Assumptions section to explicitly state that 'final grade' proxy validation is performed by the automated 'Reference-Validator Agent' (FR-008 alignment)
- [X] T012 [P] Update spec.md FR-007 to explicitly mandate calculation of 'significance flip rate' (conclusion change) in addition to 'significance stability' (FR-007/SC-003 alignment)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Download and preprocess OULAD data (Priority: P1) 🎯 MVP

**Goal**: Download OULAD, filter for courses with assessment/forum events, and extract learner records with feedback timestamps, grades, and completion status.

**Independent Test**: Can be fully tested by running `projects/PROJ-438-the-effect-of-personalized-feedback-timi/code/download_data.py` and `projects/PROJ-438-the-effect-of-personalized-feedback-timi/code/preprocess.py` and verifying the output CSV contains ≥10,000 learner records with non-null feedback interval, final grade, and completion status values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T013 [P] [US1] Unit test for OULAD URL accessibility and response validation in `projects/PROJ-438-the-effect-of-personalized-feedback-timi/tests/test_download.py`
- [ ] T014 [P] [US1] Unit test for course filtering logic (assessment + forum presence) in `projects/PROJ-438-the-effect-of-personalized-feedback-timi/tests/test_preprocess.py`
- [ ] T015 [P] [US1] Integration test for full data pipeline on a small sample (N=100) in `projects/PROJ-438-the-effect-of-personalized-feedback-timi/tests/test_pipeline_sample.py`

### Implementation for User Story 1

- [X] T016 [US1] Implement `projects/PROJ-438-the-effect-of-personalized-feedback-timi/code/download_data.py` to fetch OULAD from https://analyse.kmi.open.ac.uk/open_dataset and save to `data/raw/` (FR-001)
- [X] T017 [US1] Implement `projects/PROJ-438-the-effect-of-personalized-feedback-timi/code/preprocess.py` to filter courses by "assessment" and "forum" events and extract `is_complete` (FR-002)
- [~] T018 [US1] Implement logic to exclude learners with no recorded forum interactions (cannot compute interval) and log the exclusion count (Edge Case)
- [~] T019 [US1] Implement logic to exclude courses with <50 learners and log the exclusion count (Assumptions)
- [ ] T020 [US1] Generate `data/processed/learners_raw.csv` containing ≥10,000 records with required fields (SC-004)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Calculate feedback timing intervals and bin students (Priority: P2)

**Goal**: Compute inter-event intervals between submissions and responses, then bin students into "Immediate", "Delayed", or "Variable" groups.

**Independent Test**: Can be fully tested by running `projects/PROJ-438-the-effect-of-personalized-feedback-timi/code/compute_intervals.py` on a sample of 100 learners and verifying that each is assigned to exactly one timing group with correct boundary classification.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T021 [P] [US2] Unit test for interval calculation precision (≥0.1h) in `projects/PROJ-438-the-effect-of-personalized-feedback-timi/tests/test_intervals.py`
- [X] T022 [P] [US2] Unit test for binning logic boundaries (<2h, 2h-48h, >48h) in `projects/PROJ-438-the-effect-of-personalized-feedback-timi/tests/test_binning.py`

### Implementation for User Story 2

- [X] T023 [US2] Implement `projects/PROJ-438-the-effect-of-personalized-feedback-timi/code/compute_intervals.py` to calculate time delta between submission and response in hours (FR-003)
- [~] T024 [US2] Implement median calculation per learner to determine their representative feedback interval; **Skip exclusion logic (handled in US1)** (Edge Case)
- [~] T025 [US2] Implement binning logic to assign "Immediate" (<2h), "Delayed" (2h–48h), or "Variable" (>48h) groups (FR-004)
- [ ] T026 [US2] Generate `data/processed/learners_binned.csv` with interval and group columns (US-2)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Fit Model and perform post-hoc comparisons (Priority: P3)

**Goal**: Fit Cluster-Robust OLS with feedback group as fixed effect, perform Tukey HSD post-hoc tests, and run sensitivity analysis.

**Independent Test**: Can be fully tested by running `projects/PROJ-438-the-effect-of-personalized-feedback-timi/code/models.py` and `projects/PROJ-438-the-effect-of-personalized-feedback-timi/code/sensitivity.py` and verifying output includes Cohen's d, p-values, and stability metrics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Unit test for model fitting on synthetic data with known coefficients in `projects/PROJ-438-the-effect-of-personalized-feedback-timi/tests/test_ols.py`
- [X] T028 [P] [US3] Unit test for Tukey HSD adjustment logic in `projects/PROJ-438-the-effect-of-personalized-feedback-timi/tests/test_posthoc.py`

### Implementation for User Story 3

- [X] T029 [US3] Implement `projects/PROJ-438-the-effect-of-personalized-feedback-timi/code/models.py` to fit Cluster-Robust OLS (clustering by course ID) with feedback group as fixed effect (Plan: Technical Context, Complexity Tracking; FR-005)
- [~] T030 [US3] Implement extraction of Cohen's d effect sizes and p-values for pairwise comparisons (FR-005)
- [~] T031 [US3] Implement Tukey HSD post-hoc pairwise comparisons to control family-wise error rate (FR-006, SC-002)
- [X] T032 [US3] Implement `projects/PROJ-438-the-effect-of-personalized-feedback-timi/code/sensitivity.py` to sweep 2h and 48h boundaries by ±0.01h, ±0.05h, ±0.1h and output intermediate data for stability calculation (FR-007)
- [~] T033 [US3] Calculate and report "significance stability" (proportion of shifts where p < 0.05) using output from T032 (FR-007, SC-003)
- [~] T034 [US3] Calculate and report "significance flip rate" (proportion of shifts where the *conclusion* changes) as required by SC-003 (SC-003)
- [ ] T035 [US3] Generate `data/processed/results_metrics.csv` with effect sizes, p-values, and sensitivity stats (SC-001)
- [ ] T036 [US3] Generate `data/processed/significance_stability_report.csv` explicitly documenting the stability metric and flip rate (FR-007, SC-003)
- [~] T037 [US3] Verify "significance flip rate" against SC-003 and log the result (SC-003)
- [~] T038 [US3] Compare calculated effect sizes against the ≥0.3 target and flag the result in the final output (SC-001)
- [~] T039 [US3] Run Reference-Validator Agent on candidate literature citations to verify "final grade" as a proxy for "skill acquisition" (FR-008, Constitution Principle II) <!-- ATOMIZE: requested -->
- [ ] T040 [US3] Implement `projects/PROJ-438-the-effect-of-personalized-feedback-timi/code/report.py` to generate final analysis report including the verified citation (FR-008)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [~] T041 [P] Documentation updates: Add usage instructions to `README.md`
- [~] T042 [P] Documentation updates: Add API/implementation docs to `docs/` <!-- SKIPPED: YAML+regex parse failed (mapping values are not allowed here
 in "<unicode string>", line 2, column 13:
 contents: |
 ^) -->
- [~] T043 Code cleanup and refactoring of `projects/PROJ-438-the-effect-of-personalized-feedback-timi/code/` scripts
- [~] T044 Performance optimization: verify pipeline runs ≤6h on 2 CPU cores (Assumptions)
- [~] T045 [P] Additional unit tests for edge cases (missing timestamps, empty courses) in `tests/unit/`
- [~] T046 Run `quickstart.md` validation to ensure reproducibility

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
- **User Story 2 (P2)**: Depends on US1 completion (requires `learners_raw.csv`)
- **User Story 3 (P3)**: Depends on US2 completion (requires `learners_binned.csv`)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
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
Task: "Unit test for OULAD URL accessibility in tests/test_download.py"
Task: "Unit test for course filtering logic in tests/test_preprocess.py"

# Launch all models for User Story 1 together:
Task: "Implement code/download_data.py"
Task: "Implement code/preprocess.py"
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
- **CPU Constraint**: All statistical models must run on 2 CPU cores, ~7 GB RAM, ≤6h. No GPU/CUDA, no 8-bit quantization, no deep learning. Use statsmodels/scikit-learn.
- **Data Integrity**: All analysis must use real OULAD data. No synthetic/fake data generation for input metrics.