# Tasks: Agents' Last Exam Reproduction

**Input**: Design documents from `/specs/688-agents-last-exam-repro/`
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

- [X] T001 Create project structure per implementation plan in `projects/688-agents-last-exam-repro/`
- [X] T002 Initialize Python 3.10+ project with `pip` dependencies (`docker`, `pytest`, `pyyaml`)
- [X] T003 [P] Configure linting (flake8) and formatting (black) tools in `projects/688-agents-last-exam-repro/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `scripts/setup-plan.sh` to clone `agents-last-exam` submodule to `external/` and install dependencies
- [X] T005 [P] Implement `scripts/run-task.sh` wrapper with 60-minute timeout enforcement (FR-006)
- [X] T006 [P] Implement `scripts/generate-report.sh` to aggregate artifacts and create `validation_report.md`
- [X] T007 Create `contracts/task_artifact.schema.yaml` defining `trajectory.json` and `summary.json` structure
- [X] T008 Create `contracts/validation_report.schema.yaml` defining the report structure
- [X] T009 [P] Implement API key detection and graceful error handling logic in `scripts/setup-plan.sh` (FR-004)
- [X] T010 [P] Implement logic to ensure `artifacts/` directory structure exists in `scripts/setup-plan.sh` (PREREQ for T020)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Environment Initialization and Sanity Check (Priority: P1) 🎯 MVP

**Goal**: Initialize the `ale_run` environment, clone the submodule, and verify the entry point is executable without runtime errors.

**Independent Test**: Execute `scripts/setup-plan.sh` and verify `python -m ale_run --help` returns usage text (not a traceback).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Contract test for submodule integrity check in `tests/contract/test_submodule.py`
- [X] T012 [P] [US1] Integration test for `ale_run --help` execution in `tests/integration/test_entrypoint.py`

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement submodule cloning logic in `scripts/setup-plan.sh` (FR-001)
- [X] T014 [P] [US1] Implement dependency installation logic in `scripts/setup-plan.sh` (FR-001)
- [X] T015 [US1] Create integration test file `tests/integration/test_entrypoint.py` to verify `ale_run/__main__.py` is importable (FR-004)
- [X] T016 [US1] Add logging to `scripts/setup-plan.sh` logging "Setup Complete" on exit 0 and "Error: <msg>" on exit non-zero to stdout

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Single Task Execution and Artifact Generation (Priority: P1)

**Goal**: Execute a single representative task (e.g., `ar_full_300`) using a `dummy` agent to validate the pipeline, sandbox, and artifact generation.

**Independent Test**: Run `scripts/run-task.sh ar_full_300` and verify `artifacts/ar_full_300/trajectory.json` and `summary.json` exist and match schema.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Contract test for artifact schema validation in `tests/contract/test_artifacts.py`
- [X] T018 [P] [US2] Integration test for timeout enforcement (60m) in `tests/integration/test_timeout.py`

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement task runner wrapper in `scripts/run-task.sh` to invoke `ale_run` with dummy agent config (FR-002)
- [X] T020 [US2] Implement sandbox failure handling in `scripts/run-task.sh` to log error, write FAILED status to `summary.json`, and proceed to next task or exit cleanly (FR-007)
- [X] T021 [US2] Implement timeout logic (kill process after 60m) in `scripts/run-task.sh` (FR-006)
- [X] T022 [US2] Integrate artifact schema validation step in `scripts/run-task.sh` by calling `validate_json(artifacts/[task_id]/trajectory.json, contracts/task_artifact.schema.yaml)` (FR-003)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validation Report Generation (Priority: P2)

**Goal**: Aggregate results and generate `validation_report.md` comparing observed outcomes to paper claims (with N=1 limitation noted).

**Independent Test**: Run `scripts/generate-report.sh` and verify `output/validation_report.md` exists and contains a "Comparison to Paper Claims" section.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US3] Contract test for report schema compliance in `tests/contract/test_report.py`
- [X] T024 [P] [US3] Integration test for report generation with missing artifacts in `tests/integration/test_report_gen.py`

### Implementation for User Story 3

- [X] T025 [P] [US3] Implement artifact aggregation logic in `scripts/generate-report.sh`
- [X] T026 [US3] Implement report generation logic in `scripts/generate-report.sh` to produce `output/validation_report.md` including the Comparison to Paper Claims section (FR-005)
- [X] T027 [US3] Implement dynamic report generation logic to aggregate actual execution data for the "Limitations" section (FR-005)
- [X] T028 [US3] Implement dynamic logic to compare binary outcomes against the paper's tier description in `scripts/generate-report.sh` (FR-005)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029 [P] Update `README.md` with installation instructions for `ale_run` and `scripts/setup-plan.sh` usage examples
- [X] T030 [P] Refactor `scripts/run-task.sh` to use a helper function for logging
- [X] T031 [P] Reduce `scripts/run-task.sh` startup time significantly.
- [X] T032 [P] Additional unit tests for edge cases (corrupted submodule, network failure)
- [X] T033 [P] Security hardening for environment variable handling
- [X] T034 [P] Run quickstart.md validation

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
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Depends on US1 environment setup
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Depends on US2 artifact generation

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
Task: "Contract test for submodule integrity check in tests/contract/test_submodule.py"
Task: "Integration test for ale_run --help execution in tests/integration/test_entrypoint.py"

# Launch all models for User Story 1 together:
Task: "Implement submodule cloning logic in scripts/setup-plan.sh"
Task: "Implement dependency installation logic in scripts/setup-plan.sh"
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