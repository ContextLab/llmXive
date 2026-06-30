# Tasks: Reproduce & Validate ResearchClawBench

**Input**: Design documents from `/specs/001-reproduce-researchclawbench-a-benchmark-for-end-to/`
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

- [X] T001 Create project structure with specific directories: `src/cli`, `src/validation`, `src/config`, `tests/contract`, `tests/integration`, `tests/unit`, `results/`, `data/`
- [X] T002 Initialize Python 3.11 project with `researchclawbench` (vendored), `pytest`, `pyyaml`, `requests`, `jsonschema` dependencies
- [X] T003 [P] Configure linting and formatting tools (black, ruff)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Verify existence of `external/ResearchClawBench` and `tasks/Astronomy_000` (or equivalent)
- [X] T005 [P] Create `src/config/mock_agent.yaml` defining a deterministic, CPU-only agent stub
- [X] T006 [P] Implement `src/cli/rcb_runner.py` wrapper with unconditional exponential backoff retry logic (a limited number of attempts, initial delay 2s) for network calls
- [X] T007 [P] Create `src/validation/rubric_checker.py` to parse `checklist.json`, validate weight sums (sum == 100), and raise `ValueError` on deviation
- [X] T008 [P] Setup environment configuration management: create `src/config/env.yaml`, define schema for API keys/paths, and verify `rcb_runner.py` loads configuration successfully
- [X] T009 [P] Implement `src/validation/synthetic_generator.py` to produce Golden and Negative test artifacts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute Single-Task Reproduction (Priority: P1) 🎯 MVP

**Goal**: Execute the benchmark evaluation on a single task (`Astronomy_000`) using the mock agent to verify pipeline integrity without GPU/API dependencies.

**Independent Test**: Run `rcb-eval --task Astronomy_000 --agent mock` and verify `results/Astronomy_000_score.json` exists with status 0.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for `rcb-eval` CLI entry point in `tests/contract/test_cli.py`
- [X] T011 [P] [US1] Integration test for missing data file handling in `tests/integration/test_missing_data.py`

### Implementation for User Story 1

- [X] T013 [US1] Implement `src/validation/task_validator.py` to raise `FileNotFoundError` for missing CSV/PDF in `tasks/<ID>/data/`
- [X] T014 [US1] Integrate `src/cli/rcb_runner.py` to invoke the vendored `rcb-eval` with the `mock` agent config
- [X] T016 [US1] Add logging for execution trace and error messages to `stderr` using JSON format (levels: INFO, ERROR); verify log message "Error: File not found" appears on stderr when data is missing
- [X] T017 [US1] Verify `results/Astronomy_000_score.json` generation and schema compliance

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Multimodal Rubric Scoring (Priority: P2)

**Goal**: Verify that the evaluation engine correctly parses `checklist.json` and applies weighted criteria to synthetic artifacts (Golden/Negative cases) to produce reproducible scores.

**Independent Test**: Run scorer on a "Negative Case" (missing figure) and verify score deduction matches rubric weight.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for `checklist.json` schema validation in `tests/contract/test_rubric_schema.py`
- [X] T019 [P] [US2] Integration test for synthetic artifact scoring in `tests/integration/test_synthetic_scoring.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Create `src/validation/scorer.py` to parse `checklist.json` and map weights to artifact types
- [X] T021 [US2] Implement logic in `src/validation/scorer.py` to detect missing figures/text in synthetic outputs
- [X] T022 [US2] Update `src/validation/synthetic_generator.py` to create a "Negative Case" (missing specific figure)
- [X] T023 [US2] Implement `src/validation/synthetic_generator.py` to create a "Golden Case" (all artifacts present)
- [X] T024 [US2] Integrate scorer with `rcb_runner.py` to output detailed rubric breakdown in `results/<ID>_score.json`
- [X] T025 [US2] Add validation to ensure score deduction equals rubric weight for missing artifacts

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproduce Cross-Agent Aggregation (Priority: P3)

**Goal**: Execute evaluation for multiple distinct agent configurations on 1 task and verify aggregation of scores into a summary report.

**Independent Test**: Run aggregation script on two mock runs and verify `summary.json` contains correct mean and std dev.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T026 [P] [US3] Contract test for `summary.json` schema in `tests/contract/test_aggregation_schema.py`
- [X] T027 [P] [US3] Integration test for aggregation of failed runs in `tests/integration/test_failed_aggregation.py`

### Implementation for User Story 3

- [X] T028 [P] [US3] Create `src/validation/aggregator.py` to load multiple `results/<ID>_score.json` files
- [X] T029 [US3] Implement mean and standard deviation calculation in `src/validation/aggregator.py`
- [X] T030 [US3] Implement logic to handle failed runs (exclude or mark as "failed" in summary)
- [X] T031 [US3] Generate `results/summary.json` with per-agent scores and aggregate statistics
- [X] T032 [US3] Verify aggregation logic against manual calculation of two mock scores

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T044 [P] Documentation updates in `docs/` including `quickstart.md` with steps to run `rcb-eval --task Astronomy_000 --agent mock`
- [X] T045 Code cleanup and refactoring: extract retry logic from `src/cli/rcb_runner.py` to a new utility module `src/utils/retry.py`; verify that cyclomatic complexity of `rcb_runner.py` is reduced to < 10 after extraction
- [X] T046 Performance optimization: cache synthetic artifacts in `data/cache/`; measure execution time with `time` command to ensure < 30 min per task
- [X] T047 [P] Additional unit tests in `tests/unit/`: add `test_rubric.py::test_weight_sum_validation` and `test_aggregator.py::test_mean_calculation`
- [X] T048 Security hardening: sanitize file paths using `os.path.realpath` to prevent path traversal; verify with test case attempting `../../etc/passwd`
- [X] T049 [P] Run `quickstart.md` validation: execute commands in a fresh venv and verify exit code 0
- [X] T050 [P] Run final integration test suite: execute `tests/integration/` and verify all tests pass

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Contract test for rcb-eval CLI entry point in tests/contract/test_cli.py"
Task: "Integration test for missing data file handling in tests/integration/test_missing_data.py"

# Launch all models for User Story 1 together:
Task: "Implement src/validation/task_validator.py to raise FileNotFoundError for missing CSV/PDF"
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
- **CPU Constraint**: All tasks must run on a limited CPU and RAM configuration without GPU acceleration.
- **Data Constraint**: All data files must be present in `tasks/` directory; no external downloads during execution.