# Tasks: The Impact of Social Comparison on Self-Perception in AI-Generated Image Platforms

**Input**: Design documents from `/specs/001-synthetic-body-comparison/`
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

## Phase 0: Pre-Test Execution (FR-009)

**Purpose**: Execute the blind pre-test to generate the required `data/pretest/results.json` artifact BEFORE any real data collection begins.

**⚠️ CRITICAL DEPENDENCY**: This phase MUST complete successfully (producing valid results) before Phase 3 (Data Collection) can begin.

- [X] T001 [P] Run blind pre-test simulation with N=30 mock participants (as defined in Plan Phase 0) using `code/simulate_pretest.py` to rate AI vs Human images for visual indistinguishability
 - *Input*: Seed=42, Ratings ~ Normal(0, 1) for mock participants
 - *Output*: `data/pretest/results.json` containing the p-value for visual quality difference (must be > 0.05)
 - *Note*: N=30 is authorized by Plan Phase 0, not Spec Assumptions.

**Checkpoint**: Pre-test data generated; `data/pretest/results.json` exists for Phase 7 verification.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T004b [P] Create `scripts/init_structure.sh` to automate directory creation
- [X] T005 [P] Initialize Python project with `requirements.txt` (pandas, statsmodels, numpy, scipy, pytest)
- [ ] T006 [P] Configure linting (flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 [P] Create directory structure: `data/stimuli/ai/`, `data/stimuli/human/`, `data/raw/`, `data/processed/`, `data/pretest/` (Run `scripts/init_structure.sh`)
- [X] T008 [P] Implement `code/stimulus_loader.py` to load static assets and validate metadata presence
- [X] T009 [P] Setup `code/data_validation.py` framework for FR-007, FR-008 checks
- [X] T010 [P] Create base data models (Participant, Stimulus, Response) in `code/models.py`
- [X] T011 [P] Configure environment variables for random seeds: Create `.env` file with `RANDOM_SEED=42` and implement `code/analysis.py` to load via `os.environ.get('RANDOM_SEED', 42)`
- [X] T035 [P] Implement `code/data_validation.py` logic to check metadata matching (pose, lighting) between AI and Human sets (FR-008)
- [X] T036 [P] Implement `code/data_validation.py` logic to load and parse `data/pretest/results.json` to verify visual indistinguishability (p > 0.05) (FR-009)
- [X] T037 [P] Implement `scripts/gate_launch.py` script that calls validation functions from `code/data_validation.py` and raises `SystemExit(1)` if FR-008 or FR-009 validation fails
- [X] T038 [P] Implement `code/stimulus_generation.py` to record generation prompts for AI images for reproducibility (Principle VI)
- [ ] T020-impl [P] Implement `code/data_collection_interface.py` schema definition for covariates: Ensure `session_{id}.jsonl` schema includes `INCOM_score` and `usage_frequency` fields as required by US2 (FR-003)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Controlled Stimulus Presentation and Immediate Self-Report (Priority: P1) 🎯 MVP

**Goal**: Implement the randomized sequence presentation of AI/Human images and immediate BISS data capture.

**Independent Test**: A test script simulates a participant session, presenting images in random order, recording BISS scores, and verifying the output dataset contains correct labels, timestamps, and scores.

### Implementation for User Story 1 (Includes US2 Covariates)

- [X] T013 [P] [US1, US2] Implement `code/data_collection_interface.py` to present randomized sequence of AI/Human images one-by-one, prompt for BISS score immediately after each image, and collect INCOM/Usage prior to first image (FR-001, FR-002, FR-003)
 - *Schema*: Output `data/raw/session_{id}.jsonl` with flat keys: `stimulus_id`, `origin`, `timestamp`, `BISS_score`, `participant_id`, `INCOM_score`, `usage_frequency`
 - *Prompt*: "Enter BISS score (1-7): " for each image; "Enter INCOM score (non-negative range): " and "Enter weekly usage hours: " at start.
 - *Dependencies*: T008 (Stimulus Loader), T010 (Models), T020-impl (Schema)
- [ ] T014 [US1] Implement logic to ensure distinct consecutive images, maintain global randomization, and EXCLUDE partial sessions (dropouts) from analysis per Spec Edge Cases (FR-001, Edge Cases)
 - *Output*: `data/raw/session_{id}.jsonl` (consistent with T013)
 - *Note*: This task explicitly enforces exclusion of partial data.
- [ ] T015 [US1] Add logging for session start, image view, and completion events

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. Run these AFTER T013-T015 are implemented.

- [X] T016 [P] [US1] Contract test for stimulus sequence generation in `tests/unit/test_stimulus_loader.py`
- [X] T017 [P] [US1] Integration test for randomized presentation and BISS recording in `tests/integration/test_session_flow.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Baseline Covariate Collection (Priority: P2)

**Goal**: Collect INCOM scores and platform usage frequency before image exposure.
**Note**: Logic implemented in T013. This phase is for validation and integration testing only.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for intake survey schema in `tests/unit/test_intake_schema.py`
- [X] T019 [P] [US2] Integration test for covariate locking before stimulus unlock in `tests/integration/test_intake_flow.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Hypothesis Testing (Priority: P3)

**Goal**: Run LME model with "Image Type" as fixed factor, covariates, and random intercepts; apply corrections.

**Independent Test**: A test script loads a mock dataset, runs the LME pipeline, and verifies output JSON contains `f_stat`, `p_value`, `eta_squared`, and `n` with correct Bonferroni adjustment.

### Implementation for User Story 3

- [ ] T024 [P] [US3] Implement `code/analysis.py` to load `data/processed/` and validate ≥95% completeness (FR-007)
- [ ] T025 [US3] Implement LME model fitting using `statsmodels` with the exact formula: `BISS_score ~ Image_Type + INCOM + Usage_Frequency + (1 + Image_Type | Participant_ID)`
 - *Note*: Includes random slopes for Image_Type per Plan Complexity Tracking (Plan overrides Spec FR-004 intercept-only).
 - *Output*: Save model summary to `data/analysis_results.json`
- [ ] T026 [US3] Implement Bonferroni correction for multiple hypothesis tests (main effects + interactions)
- [ ] T028-impl [P] [US3] Implement Z-score based outlier detection (|Z| > 3.0) using `scipy.stats.zscore` for extreme INCOM scores as per Spec Edge Cases; flag outliers for sensitivity analysis in `data/analysis_results.json` (NO separate file)
 - *Note*: Implements flagging for sensitivity analysis only; no separate robust analysis pipeline.
- [ ] T028-exec [P] [US3] Execute sensitivity analysis: Run the outlier detection logic implemented in T028-impl on the loaded dataset and update `data/analysis_results.json` with the flagged outlier IDs
- [ ] T029 [US3] Generate `data/analysis_results.json` containing `f_stat`, `p_value`, `eta_squared`, `n`, and corrected p-values
- [ ] T030 [US3] Implement `code/traceability.py` to extract results and inject into paper template (Principle IV)

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Contract test for LME output schema in `tests/unit/test_analysis_schema.py`
- [ ] T032 [P] [US3] Integration test for full pipeline (validation -> LME -> correction) in `tests/integration/test_analysis_pipeline.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Success Criteria & Metrics Validation

**Purpose**: Explicitly calculate and report metrics required by Success Criteria (SC-004, SC-005).

- [ ] T033 [P] [SC-004] Calculate and report "completion rate" (full sequence vs enrolled) to `data/analysis_results.json` as key `completion_rate`. Note: This extends the FR-004 schema as required by SC-004.
- [ ] T034 [P] [SC-005] Instrument, log, and report analysis pipeline runtime (threshold: within acceptable operational limits) as key `pipeline_runtime_seconds` in `data/analysis_results.json`

---

## Phase 7: Pre-Test Validation & Data Integrity (FR-008, FR-009)

**Goal**: Ensure stimuli are matched and visually indistinguishable before study launch. (Implementation moved to Phase 2; this phase is for final verification and gating).

- [ ] T035-exec [P] Execute final metadata matching check (FR-008)
- [ ] T036-exec [P] Execute final visual indistinguishability check (FR-009) using `data/pretest/results.json`
- [ ] T037-exec [P] Execute `scripts/gate_launch.py` to confirm no validation failures (Blocks study launch if p < 0.05)

**Checkpoint**: Validation gates confirmed active.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `README.md` and `docs/`
- [ ] T040 [P] Run `memory_profiler` on `code/analysis.py` to verify RAM usage < 7GB
- [ ] T041 [P] Performance optimization to ensure analysis completes within ≤3600 seconds
- [ ] T042 [P] Additional unit tests for edge cases (dropouts, missing data) in `tests/unit/`
- [ ] T043 [P] Run `quickstart.md` validation to ensure all scripts run on `ubuntu-latest`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Pre-Test Execution)**: No dependencies - MUST complete FIRST before any data collection.
- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
 - **Phase 3 (US1)**: Depends on Phase 2 AND successful execution of Phase 0 (gate pass).
 - **Phase 4 (US2)**: Depends on Phase 2.
 - **Phase 5 (US3)**: Depends on Phase 3 and Phase 4.
- **Success Criteria (Phase 6)**: Depends on Analysis (Phase 5) completion.
- **Pre-Test Validation (Phase 7)**: Depends on Phase 0 (results exist) and Phase 2 (validation logic).
- **Polish (Phase 8)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) AND Phase 0 (Pre-test passed).
- **User Story 2 (P2)**: Can start after Foundational (Phase 2). (Integrated into US1 implementation).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on data from US1 and US2 being available.

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
- Pre-Test Execution (Phase 0) must complete before Phase 3 starts, but can run in parallel with Phase 1/2 implementation.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for stimulus sequence generation in tests/unit/test_stimulus_loader.py"
Task: "Integration test for randomized presentation and BISS recording in tests/integration/test_session_flow.py"

# Launch all models for User Story 1 together:
Task: "Implement data_collection_interface.py to present randomized sequence"
Task: "Implement logic to ensure distinct consecutive images"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 0: Pre-Test Execution (MUST pass)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
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
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
 - Developer D: Pre-Test Execution (Phase 0)
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
- **Critical Constraint**: All analysis tasks must run on CPU-only (no GPU); ensure `statsmodels` usage remains within standard memory constraints.
- **Data Integrity**: No fabricated data; use `simulate_participant.py` with literature-based distributions for testing only. Real data collection follows validated protocol.
- **Exclusion Rule (CRITICAL)**: Partial sessions (dropouts) MUST be excluded from analysis as per Spec Edge Cases. **Note**: The Plan's FR/SC Coverage Map mentions "partial data retained via LME" for FR-007. However, the Spec's Edge Cases explicitly state: "The system MUST exclude their partial data from the analysis... Imputation is NOT performed." The Spec's mandatory exclusion rule overrides the Plan's general note. Task T014 enforces this exclusion.
- **Model Specification**: LME model MUST include random slopes for Image Type as per Plan Complexity Tracking (Task T025).
- **Pre-Test Requirement**: `data/pretest/results.json` MUST be generated by Phase 0 tasks (T001) before Phase 7 verification.
- **Success Criteria**: T033 and T034 explicitly calculate SC-004 and SC-005 metrics.
- **Traceability**: T033 explicitly extends FR-004 schema per SC-004. T001 explicitly cites Plan Phase 0 for N=30. T025 explicitly cites Plan for random slopes.