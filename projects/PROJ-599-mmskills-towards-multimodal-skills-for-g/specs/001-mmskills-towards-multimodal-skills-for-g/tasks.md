# Tasks: MMSkills Reproduction & Validation

**Input**: Design documents from `/specs/001-mmskills-towards-multimodal-skills-for-g/`
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

- [X] T001 [P] Create project directory structure per `plan.md` (`src/mmskills/`, `src/external/`, `skills_library/`, `tests/`)
- [X] T002 [P] Initialize `requirements.txt` with CPU-only dependencies: `torch==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu`, `transformers`, `datasets`, `pillow`, `pandas`, `pyyaml`, `psutil`, `pytest`
- [X] T003 [P] Configure `.gitignore` to exclude `__pycache__`, `*.pyc`, and large binary assets not in `skills_library`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement Constitution Check: Create `src/mmskills/utils.py` with a function `check_constitution()` that verifies `constitution.md` exists at project root; exit with code 2 if missing
- [X] T005 [P] Implement Submodule Integrity Check: Create `src/mmskills/utils.py` function `check_submodules()` to verify `external/MMSkills` contains required files; exit with code 1 if failed
- [X] T006 [P] Create `src/mmskills/loader.py` skeleton with `SkillPackage` dataclass to hold `plan.json`, `state_cards.json`, and image paths
- [X] T007 [P] Create `src/mmskills/agent.py` skeleton with `Agent` class containing a `set_device()` method (skeleton only) and `Agent.__init__` stub (implementation deferred to T013)
- [X] T008 [P] Create `src/mmskills/evaluator.py` skeleton with `BenchmarkRunner` class and a `run_task()` method signature
- [X] T009 [P] Create `src/mmskills/utils.py` helper `timeout_decorator` that raises `TimeoutError` after 1800 seconds (FR-005)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Environment Setup & CPU-Only Execution (Priority: P1) 🎯 MVP

**Goal**: Install dependencies and execute entry point scripts in a CPU-only environment without CUDA errors.

**Independent Test**: Run `pip install -r requirements.txt` and `python run.py` in a clean environment; verify exit code 0 and no CUDA import errors.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. These tasks are sequential to implementation.**

- [X] T010 [US1] Unit test for `check_constitution()` in `tests/test_utils.py` (verify exit code 2 on missing file). **Must fail before T004 implementation.**
- [X] T011 [US1] Unit test for `check_submodules()` in `tests/test_utils.py` (verify exit code 1 on missing files). **Must fail before T005 implementation.**
- [X] T012 [US1] Integration test for `Agent.set_device()` in `tests/test_agent.py` (verify "Device: cpu" log output when GPU unavailable). **Must fail before T013 implementation.**

### Implementation for User Story 1

- [X] T013 [US1] Implement `Agent.__init__` in `src/mmskills/agent.py` to detect GPU availability and force CPU, logging the device type (FR-006). **Depends on T007.**
- [X] T014 [US1] Implement `Agent.load_model` in `src/mmskills/agent.py` to handle OOM gracefully and exit with a non-zero error code and message "OOM: Model load failed on CPU". **Do NOT attempt fallback to smaller model.** (Edge Case: Model Load Failure)
- [X] T015 [US1] Implement memory profiling logic in `src/mmskills/evaluator.py` using `psutil` to log peak RSS usage (SC-004). **Depends on T008.** (Moved from T017 to align with Plan structure)
- [X] T016 [US1] Implement `run.py` skeleton that imports `check_constitution` and `check_submodules`.
- [X] T017 [US1] Complete `run.py` entry point to call `check_constitution()` and `check_submodules()`, verify exit codes (2 and 1), and initialize the Agent (T013). **Depends on T013, T016.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Skill Loading & Structural Validation (Priority: P2)

**Goal**: Successfully load a specific multimodal skill and validate all file references (JSON + Images).

**Independent Test**: Execute a single-task run using `CHROME_Search_Web`; verify `plan.json` and `state_cards.json` parse correctly and all image paths exist.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for `SkillPackage.validate_assets()` in `tests/test_loader.py` (verify missing image detection). **Must fail before T021 implementation.**
- [X] T019 [P] [US2] Unit test for `SkillPackage.parse_plan()` in `tests/test_loader.py` (verify JSON schema compliance). **Must fail before T020 implementation.**

### Implementation for User Story 2

- [X] T020 [US2] Implement `SkillPackage.load()` in `src/mmskills/loader.py` to read `plan.json` and `state_cards.json` from `skills_library`. **Depends on T006.**
- [X] T021 [US2] Implement `SkillPackage.validate_assets()` in `src/mmskills/loader.py` to check existence of all images listed in `IMAGE_REFERENCE_LIST.md` (FR-002). **Mark missing images as "ERROR" only (FR-007).** **Depends on T020.**
- [X] T022 [US2] Implement `Agent.execute_step()` in `src/mmskills/agent.py` to parse the first step of the loaded plan (T020) and output a structured JSON action object (FR-003). **Depends on T013, T020, T021.**
- [X] T023 [US2] Add logging in `src/mmskills/agent.py` to record the specific skill step execution and any asset validation errors. **Depends on T022.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Benchmark Subset Execution & Metrics Logging (Priority: P3)

**Goal**: Run the agent on a small, fixed subset of tasks (5 tasks) from OSWorld and generate a structured metrics report.

**Independent Test**: Run evaluation script with `--num-tasks=5`; verify `metrics_summary.csv` contains `task_id`, `status`, and `duration_seconds`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test for `timeout_decorator` in `tests/test_utils.py` (verify 1800s limit enforcement). **Must fail before T009 implementation.**
- [X] T025 [P] [US3] Integration test for `BenchmarkRunner.run_subset()` in `tests/test_evaluator.py` (verify CSV generation with correct columns). **Must fail before T029 implementation.**

### Implementation for User Story 3

- [X] T026 [US3] Implement data fetcher in `src/mmskills/evaluator.py` to download the OSWorld subset (N=5) from dataset ID 'osworld/osworld-benchmark' and save to 'skills_library/osworld_subset.json' (Real Data Rule). **Depends on T008.**
- [X] T027 [US3] Implement `BenchmarkRunner.run_task()` in `src/mmskills/evaluator.py` wrapped with `timeout_decorator` to enforce 1800s limit (FR-005). **Depends on T009, T022.**
- [X] T028 [US3] Implement `BenchmarkRunner.run_subset()` to iterate over the 5 tasks (from T026), call `Agent.execute_step()` (T022), and catch `TimeoutError` to record "TIMEOUT" status. **Depends on T026, T027.**
- [X] T029 [US3] Implement metrics logger in `src/mmskills/evaluator.py` to write `metrics_summary.csv` with `task_id`, `status` (success/fail/timeout), `duration_seconds`, and `error_message` (FR-004). **Depends on T028.**
- [X] T030 [US3] Implement validation method within `BenchmarkRunner` to ensure `metrics_summary.csv` has no empty rows and all task IDs match the requested subset (N=5) per Real Data Rule (US-3 Acceptance). **Depends on T029.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031a [P] Create `docs/README.md` with instructions for running the validation suite on CPU
- [X] T031b [P] Create `docs/CI_SETUP.md` with instructions for CI environment configuration
- [X] T032a [P] Refactor `src/mmskills/` modules to remove unused imports
- [X] T032b [P] Refactor `src/mmskills/` modules to enforce type hints
- [X] T033 [P] Run `quickstart.md` validation to ensure all entry points work as documented
- [X] T034 [P] Final Constitution Re-check: Verify all changes comply with `constitution.md` principles

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 (Agent) and US2 (Loader) to execute tasks

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
- All tests for a user story marked [P] can run in parallel (but must fail before implementation)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for check_constitution() in tests/test_utils.py" (T010)
Task: "Unit test for check_submodules() in tests/test_utils.py" (T011)

# Launch all models for User Story 1 together:
Task: "Create project directory structure per plan.md" (T001)
Task: "Initialize requirements.txt with CPU-only dependencies" (T002)
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
- **CRITICAL**: All data fetches must use real, reachable URLs (e.g., HuggingFace datasets) and never generate fake data.
- **CRITICAL**: All model loads must default to CPU or a small CPU-tractable fallback; never use 8-bit/4-bit quantization requiring CUDA.