# Tasks: Reproduce & Validate Bidirectional Evolutionary Search (BES)

**Input**: Design documents from `/specs/637-reproduce-validate-bes/`
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

- [X] T001 Create project structure per implementation plan (`external/BES`, `inference/`, `tests/`)
- [X] T002 Initialize Python 3.11 project with CPU-only dependencies (`torch`, `transformers`, `scikit-learn`, `llama-cpp-python`)
- [X] T003 [P] Configure linting and formatting tools (`ruff`, `black`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 [P] Clone and verify `external/BES` git submodule integrity
- [X] T005 [P] Implement CPU-only configuration override in `inference/config/local_openai_config.py` (disable CUDA, set `device="cpu"`)
- [X] T006 [P] Setup robust retry logic with exponential backoff for LLM provider connectivity in `inference/scripts/utils.py`
- [X] T007 Create base logging infrastructure with explicit event markers for "forward expansion" and "backward decomposition" in `inference/scripts/logger.py`
- [X] T008 Setup environment variable management for CI timeouts and memory limits in `inference/config/env_config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute BES Inference Pipeline on Benchmark Task (Priority: P1) 🎯 MVP

**Goal**: Verify the vendored BES codebase runs end-to-end on `circle_packing` within 30 mins on CPU, producing valid artifacts.

**Independent Test**: CI executes `run_evo.py` with fixed seed; exits 0; generates files in `inference/results/circle_packing/`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Contract test for output schema in `tests/contract/test_output_schema.py`
- [X] T010 [P] [US1] Integration test for pipeline execution timeout in `tests/integration/test_pipeline_timeout.py`

### Implementation for User Story 1

- [X] T011 [US1] Implement `inference/scripts/run_evo.py` entry point with CPU constraints and timeout handling
- [X] T012 [US1] Implement `inference/scripts/evaluate.py` stub to validate solution files exist and are non-empty
- [X] T013 [US1] Add retry logic for LLM provider in `inference/scripts/run_evo.py` (max 3 retries, exponential backoff)
- [X] T014 [US1] Ensure `inference/scripts/run_evo.py` logs "forward expansion" and "backward decomposition" events
- [X] T015 [US1] Verify graceful failure with distinct exit code if LLM provider is unreachable

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Solution Correctness Against Paper Metrics (Priority: P2)

**Goal**: Confirm generated solutions satisfy geometric constraints and meet the "operational test for improvement" defined by `evaluate.py`.

**Independent Test**: `evaluate.py` runs on generated artifacts and returns a pass/fail metric based on constraints.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Unit test for geometric constraint validation logic in `tests/unit/test_evaluator.py`
- [X] T017 [P] [US2] Integration test for solution validity reporting in `tests/integration/test_solution_validity.py`

### Implementation for User Story 2

- [X] T018 [P] [US2] Implement geometric constraint checker (circle overlap detection) in `inference/scripts/evaluate.py`
- [X] T019 [US2] Implement "operational test for improvement" logic in `inference/scripts/evaluate.py` (compare score vs baseline)
- [X] T020 [US2] Add detailed logging of specific constraint violations (e.g., "circle overlap detected") in `inference/scripts/evaluate.py`
- [X] T021 [US2] Integrate `evaluate.py` results into the main pipeline output in `inference/results/circle_packing/summary.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproduce Bidirectional Search Dynamics (Priority: P3)

**Goal**: Verify the "bidirectional" nature (forward expansion + backward decomposition) is actually occurring, not just greedy search.

**Independent Test**: Logs show ≥5 "backward decomposition" events; goal tree structure shows depth > 1.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US3] Contract test for log event format in `tests/contract/test_log_events.py`
- [X] T023 [P] [US3] Integration test for bidirectional event counting in `tests/integration/test_bidirectional_events.py`

### Implementation for User Story 3

- [X] T024 [P] [US3] Implement log parser to count "backward decomposition" events in `inference/scripts/log_analyzer.py`
- [X] T025 [US3] Implement goal tree serialization to verify depth > 1 in `inference/scripts/state_tracker.py`
- [X] T026 [US3] Add validation step to ensure ≥5 backward decomposition events occur before final solution generation
- [X] T027 [US3] Update `inference/results/circle_packing/summary.json` to include bidirectional event counts and tree depth metrics

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reviewer Concerns & Validation (Addressing Prior Research)

**Purpose**: Address specific concerns raised by Alan Turing (operational metric rigor) and Stephen Wolfram (computational irreducibility).

### Implementation for Reviewer Concerns

- [X] T028 [US2] [Review: Turing] Implement explicit numerical estimate of storage capacity for "history of states" in `inference/scripts/memory_tracker.py` to address entropy concerns
- [X] T029 [US3] [Review: Turing] Refine `evaluate.py` to strictly distinguish between "mere change" and "genuine increase in capability" using a fixed fitness function threshold
- [X] T030 [US3] [Review: Wolfram] Add documentation and logging in `inference/scripts/run_evo.py` explicitly acknowledging the "computational irreducibility" of the search space
- [X] T031 [US3] [Review: Wolfram] Ensure the search does not claim to predict mutation outcomes analytically; rely on empirical run results for validation
- [X] T032 [US3] [Review: Wolfram] Verify that the "bidirectional" search explores a sufficient sample of the rule space (forward/backward) without assuming a gradient

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T033 [P] Documentation updates in `docs/reproducibility.md` detailing CPU-only execution and timeout handling
- [X] T034 Code cleanup and refactoring of logging infrastructure
- [X] T035 Performance optimization to ensure memory footprint < 6 GB during tree expansion
- [X] T036 [P] Additional unit tests for memory tracking in `tests/unit/test_memory_tracker.py`
- [X] T037 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T011 (run_evo.py) for input artifacts
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T011 and T007 (logging) for event data
- **Reviewers (Phase 6)**: Depends on US1, US2, US3 completion to validate specific claims

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
Task: "Contract test for output schema in tests/contract/test_output_schema.py"
Task: "Integration test for pipeline execution timeout in tests/integration/test_pipeline_timeout.py"

# Launch all models for User Story 1 together:
Task: "Implement run_evo.py entry point"
Task: "Implement evaluate.py stub"
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
5. Add Phase 6 (Reviewer Concerns) → Validate against specific academic critiques
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Pipeline Execution)
   - Developer B: User Story 2 (Validation Logic)
   - Developer C: User Story 3 (Bidirectional Dynamics)
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
- **Critical Constraint**: All tasks MUST run on CPU-only CI (limited vCPU, 7GB RAM, No GPU). No CUDA, no 8-bit quantization requiring GPU.
