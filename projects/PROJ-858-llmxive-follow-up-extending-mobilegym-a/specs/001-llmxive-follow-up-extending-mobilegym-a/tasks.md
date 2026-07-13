# Tasks: State-Guided Curriculum for MobileGym

**Input**: Design documents from `/specs/001-state-guided-curriculum/`
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

- [X] T001 Create project structure per implementation plan with explicit directories: `code/`, `code/scheduler/`, `code/training/`, `code/analysis/`, `code/utils/`, `data/raw/`, `data/processed/`, `data/validation/`, `tests/unit/`, `tests/integration/`, `contracts/`.
- [X] T002 Initialize Python project with `requirements.txt`: Pin `mobilegym` by fetching from the official repository URL ` and immediately recording the specific git commit hash in `data/raw/.checksums.txt` to ensure reproducibility.
- [X] T003 [P] Configure linting (`ruff`) and formatting (`black`) tools
- [X] T004 [P] Setup GitHub Actions CI workflow for CPU-only runner (multiple vCPU, sufficient RAM)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement `code/utils/constants.py` with time limits (6h), success thresholds, and coverage vector schema definitions (read schema from `contracts/coverage.schema.yaml`).
- [X] T006 Implement `code/utils/logging.py` for structured JSON logging and error handling
- [X] T007 Create `code/utils/data_loader.py` to fetch and checksum MobileGym tasks (raw data preservation)
- [X] T008 Implement `code/scheduler/state_coverage.py` skeleton for binary vector initialization
- [X] T009 Implement `code/scheduler/curriculum_scheduler.py` skeleton with two-phase logic stubs
- [ ] T010 Setup `data/raw/.checksums.txt` and `data/processed/` directory structure
- [ ] T011 Initialize `data/processed/scheduler_trace.json` schema and directory structure (required before T020).
- [ ] T012 [P] Define "semantic state proxies" (e.g., `dark_mode`, `unread_count`) in `code/utils/constants.py` by reading the full list from `contracts/coverage.schema.yaml` key `semantic_proxies` to ensure US1 has necessary constants.
- [ ] T013 [US1] Implement hard wall-clock time limit enforcement (watchdog) in `code/training/runner.py` to satisfy FR-004.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dynamic Curriculum Scheduler (Priority: P1) 🎯 MVP

**Goal**: Implement the dynamic scheduler that selects tasks based on state coverage and difficulty.

**Independent Test**: The scheduler can be tested in isolation by feeding it a mock history of state coverage vectors and verifying that it outputs a batch of task parameters that maximizes entropy or targets a moderate success rate range.

### Implementation for User Story 1 (Must precede tests)

- [X] T014 [US1] Implement Phase 1 logic (target coverage < 5%) in `code/scheduler/curriculum_scheduler.py`
- [~] T015 [US1] Implement Phase logic (target moderate success rate) with dynamic range expansion (10-90%) in `code/scheduler/curriculum_scheduler.py`
- [~] T016 [US1] Implement fallback to maximum entropy if no tasks meet criteria (including after a range of expansion) in `code/scheduler/curriculum_scheduler.py`.
- [~] T017 [US1] Implement 'Static Random' baseline scheduler logic (random sampling) in `code/scheduler/curriculum_scheduler.py` to satisfy FR-003 experimental control.
- [~] T018 [US1] Add logging for `metrics_triggered` to `data/processed/scheduler_trace.json` (Constitution Principle VI), ensuring the log entry includes the specific state variable names (e.g., 'dark_mode') and their transition values that triggered the selection. <!-- FAILED: unspecified -->
- [~] T019 [US1] Implement deadlock prevention (random selection if all states covered) in `code/scheduler/curriculum_scheduler.py`

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests AFTER implementation to ensure the module exists to be tested.**

- [~] T020 [P] [US1] Generate 'mock history of state coverage vectors' data fixture required for US-001 independent test in `tests/fixtures/mock_coverage_history.json`. (Must run before T021-T023).
- [~] T021 [P] [US1] Unit test for low-coverage selection logic in `tests/unit/test_scheduler_low_coverage.py` using data from T020.
- [~] T022 [P] [US1] Unit test for 30-70% "sweet spot" selection in `tests/unit/test_scheduler_sweet_spot.py` using data from T020.
- [~] T023 [P] [US1] Unit test for fallback logic (entropy/random) in `tests/unit/test_scheduler_fallback.py` using data from T020.
- [~] T024 [P] [US1] Implement latency benchmarking harness in `tests/integration/test_scheduler_latency.py` to verify scheduler latency < 10% of batch execution time (runtime behavior check).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - State Coverage Instrumentation (Priority: P2)

**Goal**: Instrument MobileGym to track binary State Coverage Vectors after every rollout.

**Independent Test**: The instrumentation can be tested by running a fixed sequence of known state transitions in the simulator and verifying that the resulting JSON state handler output correctly flips the corresponding bits in the coverage vector.

### Implementation for User Story 2

- [~] T025 [US2] Implement state transition detection logic in `code/scheduler/state_coverage.py`
- [~] T026 [US2] Implement parallel rollout aggregation logic to merge vectors safely in `code/scheduler/state_coverage.py` <!-- FAILED: unspecified -->
- [~] T027 [US2] Add error handling to skip malformed JSON rollouts without crashing the batch in `code/scheduler/state_coverage.py`
- [~] T028 [US2] Write aggregated coverage vectors to `data/processed/coverage_vectors.json` with checksums
- [~] T029 [US2] Generate the 'held-out test set' containing state variables NOT present in the training-time State Coverage Vector to satisfy FR-005 transfer evaluation requirements.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US2] Unit test for binary vector bit-flipping on state change in `tests/unit/test_state_coverage.py`
- [ ] T031 [P] [US2] Integration test for parallel rollout aggregation without race conditions in `tests/integration/test_parallel_coverage.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Convergence Analysis (Priority: P3)

**Goal**: Compare convergence speed and Sim-to-Real transfer robustness between dynamic and static baselines.

**Independent Test**: The analysis pipeline can be tested by running two pre-recorded training logs through the evaluation script to ensure it correctly generates plots and calculates variance metrics.

### Implementation for User Story 3

- [ ] T032 [US3] Implement `code/training/runner.py` to orchestrate Static Random vs. State-Guided runs using identical **Qwen3-VL-4B-Instruct** model configuration (including quantization level and context window) to ensure experimental control; this task MUST generate `baseline_logs.json` for the Static Random run and `experimental_logs.json` for the State-Guided run.
- [ ] T033 [US3] Implement `code/analysis/convergence.py` to calculate steps-to-target (read success rate threshold from config file) and report absolute/percentage difference.
- [ ] T034 [US3] Implement `code/analysis/transfer.py` to evaluate on held-out test set (with state variables NOT present in the training-time State Coverage Vector).
- [ ] T035 [US3] Implement variance calculation of success rates across high state-dependency apps in `code/analysis/transfer.py`
- [ ] T036 [US3] Generate "Success Rate vs. Steps" plots and save to `data/processed/`

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T037 [P] [US3] Unit test for convergence step calculation in `tests/unit/test_convergence.py`
- [ ] T038 [P] [US3] Unit test for variance calculation across high-dependency apps in `tests/unit/test_transfer.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Methodological Validity & Sensitivity Analysis (Priority: P2)

**Goal**: Validate that State Coverage Vector variables are a statistically significant proxy for task difficulty.

**Independent Test**: The analysis script can be tested by correlating binary coverage vectors against actual success rates, verifying Pearson's r ≥ 0.5.

### Implementation for User Story 4

- [ ] T039 [US4] Implement `code/analysis/sensitivity.py` to compute **Pearson correlation coefficient (r)** between the **scalar count (sum of 1s) derived from the binary State Coverage Vector** and success rate on a held-out validation set.
- [ ] T040 [US4] Implement logic to flag "Invalid Proxy" if r < 0.3 and recommend expanding variable set
- [ ] T041 [US4] Implement "Proxy Validated" logging if r ≥ 0.5
- [ ] T042 [US4] Generate sensitivity analysis report in `data/processed/sensitivity_report.md`

### Tests for User Story 4 (OPTIONAL - only if tests requested) ⚠️

- [ ] T043 [P] [US4] Unit test for Pearson correlation calculation on mock data in `tests/unit/test_sensitivity.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Documentation updates in `docs/` (include scheduler trace explanation)
- [ ] T045 Code cleanup and refactoring of `code/scheduler/` and `code/analysis/`
- [ ] T046 [P] Additional unit tests for edge cases (empty batches, malformed data) in `tests/unit/`
- [ ] T047 Run quickstart.md validation to ensure end-to-end pipeline works on CPU-only runner
- [ ] T048 Verify all artifacts (logs, vectors, reports) are checksummed and reproducible

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Provides data for US1 but can be developed in parallel
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires US1 and US2 to be functional for full integration, but analysis logic can be stubbed
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Independent validation logic

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Constants before Services
- Services before Endpoints/Analysis scripts
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models/Constants within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for low-coverage selection logic in tests/unit/test_scheduler_low_coverage.py"
Task: "Unit test for 30-70% sweet spot selection in tests/unit/test_scheduler_sweet_spot.py"

# Launch all models for User Story 1 together:
Task: "Implement Phase 1 logic in code/scheduler/curriculum_scheduler.py"
Task: "Implement Phase 2 logic in code/scheduler/curriculum_scheduler.py"
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
5. Add User Story 4 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Scheduler)
 - Developer B: User Story 2 (Instrumentation)
 - Developer C: User Story 3 (Analysis)
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
- **CPU Constraint**: Ensure all model loading and training tasks use CPU-optimized configs (Qwen-VL-4B-Instruct, quantization if needed) and do not exceed 7GB RAM.
- **Data Integrity**: All raw data must be checksummed; no synthetic/fake data generation tasks are allowed.
- **Plan Discrepancy Note**: The plan.md summary and T032 now consistently use "Qwen3-VL-4B-Instruct", resolving the previous contradiction with the Spec.