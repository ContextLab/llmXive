# Tasks: AdaPlanBench Reproduction & Validation

**Input**: Design documents from `/specs/668-ada-plan-bench-reproduction/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

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

- [X] T001 [P] Create project directory structure `src/ada_bench`, `tests/unit`, `tests/integration`, `outputs/` per implementation plan
- [X] T002 [P] Initialize Python 3.11 virtual environment and create `requirements.txt` with `pytest`, `requests`, `huggingface_hub`, `jsonschema`, `numpy`, `transformers` (CPU-optimized). **Note**: `git` is a system dependency and must be installed via `apt-get install git` (see T002b), NOT added to `requirements.txt`.
- [X] T002b [P] Ensure `git` is installed on the runner (e.g., via `apt-get install git` or equivalent) to support submodule initialization (FR-001).
- [X] T003 [P] Configure `.gitignore` to exclude `outputs/`, `__pycache__`, and `.env` files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `src/ada_bench/__init__.py` to expose version and core modules
- [X] T004b [P] Define `src/ada_bench/schema/task_schema.json` containing the JSON schema for task instances (fields: `id`, `goal`, `constraints`, `domain`, `metadata`) to enable validation.
- [X] T005 [P] Create `src/ada_bench/data_loader.py` to load and validate `domain_metadata/housing/final/query_housing_macgyver_resample.json` from the git submodule, using `task_schema.json` (T004b) for validation and raising clear, specific errors for missing fields or corrupted JSON.
- [X] T006 [P] Implement `src/ada_bench/constraints/checker.py` to identify and report the *first* violated constraint in a plan, ensuring deterministic feedback for the revision loop.
- [X] T007 [P] Create `src/ada_bench/utils/logger.py` to configure structured logging for plan revisions, constraint violations, and API errors.
- [X] T008 [P] Implement `src/ada_bench/utils/retry_handler.py` to handle LLM API timeouts/errors with **exactly 3 retries** and exponential backoff (FR-004).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Environment Initialization & Dependency Resolution (Priority: P1) 🎯 MVP

**Goal**: Ensure the benchmark runs in a CPU-only CI environment without manual intervention or GPU requirements.

**Independent Test**: Can be fully tested by running the setup script in a fresh Docker container (CPU-only) and verifying that `python -c "import ada_bench; from ada_bench.runner import run_task"` executes without import errors or CUDA warnings.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Unit test `tests/unit/test_data_loader.py` verifying `load_and_validate()` raises specific errors on corrupted JSON or missing schema fields (referencing T004b/T005).
- [X] T009 [P] [US1] Integration test `tests/integration/test_env_init.py` verifying no CUDA libraries are imported on a CPU-only runner.

### Implementation for User Story 1

- [X] T010 [US1] Implement `src/ada_bench/agents/mock_agent.py` as a deterministic agent that returns fixed plans for infrastructure testing (never used for metric calculation).
- [X] T011 [US1] Implement `src/ada_bench/agents/cpu_llm_agent.py` wrapping **TinyLlama-Chat-v1.0** with **4-bit quantization (bitsandbytes)** and **explicit `device_map='cpu'`** for CPU-only inference. **Must assert** that `load_in_8bit` is NOT used and `device_map` is strictly 'cpu' to prevent accidental GPU fallback (FR-001).
- [X] T012 [US1] Update `src/ada_bench/runner.py` to initialize the environment, load data via `data_loader.py` (T005), and verify `domain_metadata` files exist before proceeding.
- [X] T013 [US1] Add validation logic in `runner.py` to ensure no GPU-related imports succeed on the CI runner (FR-001).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Single-Task Execution & Artifact Generation (Priority: P1)

**Goal**: Execute the benchmark loop for a single task using the Mock Agent to verify plan generation, constraint feedback, and revision logic.

**Independent Test**: Can be tested by running a single task with `mock_agent` and verifying the output log contains: Initial Plan -> Constraint Violation -> Revised Plan -> Final Result.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T014 [P] [US2] Contract test `tests/contract/test_single_task_flow.py` verifying the JSON output structure matches the spec (initial_plan, feedback_history, final_plan, success_status). **Must ensure** the test fails if the mock agent never triggers a violation (false positive check).

### Implementation for User Story 2

- [X] T015 [US2] Implement `src/ada_bench/runner.py` core loop: `initial_plan = agent.generate()`, `feedback = checker.check(plan)`, `if feedback: revised_plan = agent.revise(plan, feedback)`. **Note**: This task depends on the *interface* of agents (T010/T011), allowing parallel development with US1.
- [X] T016 [US2] Implement `src/ada_bench/metrics/calculator.py` stubs to prepare for metric calculation, ensuring `success_status` is tracked.
- [X] T017 [US2] Implement artifact serialization in `runner.py` to write results to `outputs/<task_id>_result.json` with required fields (FR-003).
- [X] T018 [US2] Add integration test `tests/integration/test_runner.py` that runs a single task with `mock_agent` and asserts the presence of at least one constraint violation and one revision in the log.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Full-Scale Reproduction & Metric Validation (Priority: P2)

**Goal**: Run the benchmark on a stratified subset (20 tasks) using the CPU-tractable LLM to validate the "adaptive planning accuracy" metric and constraint accumulation trend.

**Independent Test**: Run the subset and verify the merged results file reports an accuracy metric and that the trend shows correlation between constraint count and failure rate.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US3] Integration test `tests/integration/test_subset_run.py` running 20 tasks and verifying `outputs/merged_results.json` exists with valid float accuracy.

### Implementation for User Story 3

- [X] T019 [US3] **Data Exploration**: Implement `src/ada_bench/utils/data_explorer.py` to load the full dataset and report the distribution of constraint counts (0, 1, 2, 3+). **Prerequisite for T020** to ensure stratification logic is feasible.
- [X] T020 [US3] **Stratified Sampling**: Implement `src/ada_bench/stratified_sampler.py` to select a subset of tasks. **Strategy**: Select **up to 5** tasks per constraint count stratum (0, 1, 2, 3+). If a stratum has a **small number** of tasks, select **all available** in that stratum to ensure the task does not fail on missing data (executable fallback).
- [X] T021 [US3] Update `src/ada_bench/runner.py` to support batch execution using the `cpu_llm_agent` (T011) and the `stratified_sampler` (T020).
- [X] T022 [US3] Implement `src/ada_bench/metrics/calculator.py` to compute `adaptive_planning_accuracy` (successful final plans / total tasks) and log constraint accumulation per task (FR-005, FR-006).
- [X] T023b [US3] **SC-005 Assertion**: Implement logic in `src/ada_bench/reporter.py` to explicitly verify the boolean condition: "At least one task in the subset encountered ≥2 constraints". This must be a pass/fail check, distinct from trend analysis.
- [X] T024 [US3] Implement `src/ada_bench/reporter.py` to generate a summary report comparing the observed accuracy and constraint trends against the paper's qualitative claims (SC-004).
- [X] T025 [US3] Add error handling in `runner.py` to catch LLM timeouts, apply retry logic (T008), and log failures as "timeout/error" rather than crashing the batch (FR-004).

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T026 [P] Documentation updates in `README.md` detailing how to run the subset evaluation and interpret results.
- [X] T027 Code cleanup and refactoring of `runner.py` to separate batch logic from single-task logic.
- [X] T028 [P] Run `pytest` with coverage to ensure all critical paths (retry logic, constraint checking, metric calculation) are tested. **Target**: `>=80%` coverage on `src/ada_bench` (`pytest --cov=src/ada_bench --cov-report=term-missing`).
- [X] T029 [P] Validate `quickstart.md` (if generated) against the actual execution flow on a clean runner.

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
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Depends on `mock_agent` interface (T010)
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Depends on `cpu_llm_agent` (T011) and `stratified_sampler` (T020)

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
Task: "Unit test tests/unit/test_data_loader.py"
Task: "Integration test tests/integration/test_env_init.py"

# Launch all models for User Story 1 together:
Task: "Implement src/ada_bench/agents/mock_agent.py"
Task: "Implement src/ada_bench/agents/cpu_llm_agent.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Environment & Mock Agent)
4. Complete Phase 4: User Story 2 (Single Task Loop & Artifacts)
5. **STOP and VALIDATE**: Test single task flow with Mock Agent to ensure loop logic is correct
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 + 2 → Test single task loop → Demo (MVP!)
3. Add User Story 3 (Stratified Subset + CPU LLM) → Test metric calculation → Demo
4. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Environment & Mock Agent)
   - Developer B: User Story 2 (Runner Logic & Artifacts)
3. Once US1 & US2 are stable:
   - Developer C: User Story 3 (CPU LLM Integration & Metrics)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: Avoid any task requiring CUDA, `load_in_8bit`, or large LLMs; all inference must be CPU-tractable (TinyLlama) or mocked.
- **Stratification**: T020 uses flexible logic ("up to 5, or all available") to handle data distribution variance.
- **Submodule**: T002b ensures `git` binary is available before T005 attempts to load data.