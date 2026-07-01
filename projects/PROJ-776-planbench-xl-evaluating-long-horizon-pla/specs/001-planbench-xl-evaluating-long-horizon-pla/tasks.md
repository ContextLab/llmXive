# Tasks: PlanBench-XL Reproduction & Validation

**Input**: Design documents from `/specs/001-planbench-xl-reproduction/`
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

- [X] T001 Create project structure per implementation plan: `src/validation/`, `src/analysis/`, `tests/`, `external/PlanBench-XL/`
- [X] T002 Initialize Python 3.11 project with `requirements.txt` containing: `openai`, `pyyaml`, `pandas`, `tqdm`, `pytest`, `requests`
- [X] T003 [P] Configure `.gitignore` to exclude `results/`, `__pycache__/`, `*.pyc`, and `.env` files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/validation/check_submodule.py` to verify `external/PlanBench-XL/data/` contains `tasks.json`, `database.json`, `scripts/run_retail_batch.py`, AND `blocker_tools.json` (FR-002, FR-003, Assumption 2). Script must exit with non-zero code if any file is missing.
- [X] T005 [P] Implement `src/validation/check_api_keys.py` to scan environment variables for required keys. Logic must distinguish between: (a) missing key for a single model -> log warning and skip; (b) missing keys for ALL models -> log hard error and exit non-zero (FR-006, US-1, Constitution Principle II).
- [X] T006 [P] Create `src/config/loader.py` to parse YAML configs (`retail_gpt5.4_blocker.yaml`, etc.) and validate `noise_ratio` and `task_count` parameters (FR-001, FR-003).
- [X] T007 Implement `src/validation/check_timeouts.py` to enforce 60s per tool and 300s per task limits using `asyncio.wait_for` wrappers (cross-platform reliable) instead of `signal` (FR-004, US-1). Export a `wrap_tool_call(func)` decorator.
- [X] T008 [P] Create `src/config/model_filter.py` to reject configurations requiring GPU (e.g., local CUDA models). If a GPU model is detected, the script MUST log a specific error and exit with non-zero code (SC-004).
- [X] T009 Implement `src/utils/logger.py` to ensure all execution traces and errors are written to structured JSON in `results/` (FR-005).
- [X] T018 [US2] Implement `src/config/condition_injector.py` to handle runtime interception of tool calls. Strategy: Monkey-patch the `tools` dictionary in the global scope of `external/PlanBench-XL/scripts/run_retail_batch.py` (or its imported module) before execution. For "blocker" condition, wrap tool functions to return "tool unavailable" errors. For "noise" condition, inject misleading descriptions into the tool context. This satisfies FR-002 (runtime interception) and FR-003 (noise injection).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute Baseline Reproduction (Priority: P1) 🎯 MVP

**Goal**: Execute the `run_retail_batch.py` script on a 5-task subset using `gpt-5.4-mini` to verify end-to-end execution and artifact generation.

**Independent Test**: Run `scripts/run_reproduction.py` with `--task-count 5 --model gpt-5.4-mini`. Verify exit code 0 and existence of `results/eval_results.json` with valid metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [US1] Integration test in `tests/integration/test_baseline_run.py::test_baseline_run_generates_schema` that runs a real 5-task batch (mocking only the network if necessary for speed, but validating real logic flow) and asserts `results/eval_results.json` contains keys `[accuracy, task_id, success]`. (Principle V: Real-call testing).

### Implementation for User Story 1

- [X] T012 [US1] Create wrapper script `scripts/run_reproduction.py` that:
    1. Loads config and checks API keys (T005).
    2. Checks submodule (T004).
    3. Iterates through model configurations: if key missing, skip model and log warning; if all missing, exit non-zero.
    4. Invokes `external/PlanBench-XL/scripts/run_retail_batch.py` with CLI args `--task-count 5 --model gpt-5.4-mini --output-dir results/`.
    5. Imports and applies timeout wrappers from T007 (`src/validation/check_timeouts.py`) to the execution flow.
    6. Orchestrates `src/analysis/parse_logs.py` (T013) to generate `results/eval_results.json` immediately after the run. (FR-001, US-1, FR-006).
- [X] T013 [US1] Implement `src/analysis/parse_logs.py` to read raw task logs from `results/task_logs/`, aggregate them, and write `results/eval_results.json` containing `accuracy`, `task_id`, `success` keys (FR-005, US-1).
- [X] T014 [US1] Add error handling in `scripts/run_reproduction.py` to catch API failures and log them without crashing the batch (US-1, Edge Case 1).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Blocking & Noise Conditions (Priority: P2)

**Goal**: Validate that the "blocking" and "noise" simulation mechanisms correctly degrade performance compared to the baseline.

**Independent Test**: Run `scripts/run_reproduction.py` with `--condition blocker` and `--condition noise`. Verify `eval_results.json` shows strictly lower accuracy than baseline and logs contain specific "tool blocked" or "distracting" events.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Contract test in `tests/contract/test_condition_validation.py` asserting that blocking logs contain "tool unavailable" and noise logs contain "distracting" strings.
- [X] T017 [P] [US2] Integration test in `tests/integration/test_condition_impact.py` comparing baseline vs. blocker accuracy metrics (must be lower).

### Implementation for User Story 2

- [X] T019 [US2] Update `scripts/run_reproduction.py` to accept `--condition` argument (default, blocker, noise). If `blocker` or `noise` is selected, import and apply the monkey-patching logic from T018 (`src/config/condition_injector.py`) before invoking the external script. (FR-001, US-2).
- [X] T020 [US2] Implement `src/analysis/compare_conditions.py` to:
    1. Read `results/baseline.json` (from T013) and `results/blocker.json` (from US2 run).
    2. Calculate `baseline_accuracy`, `blocker_accuracy`, and `drop_percent`.
    3. Write a JSON summary to `results/condition_comparison.json` with these keys.
    4. **Enforce SC-002**: If `blocker_accuracy` is NOT strictly lower than `baseline_accuracy`, the script MUST exit with a non-zero code and print a failure message. (US-2, SC-002).
- [X] T021 [US2] Add logging in `src/analysis/compare_conditions.py` to explicitly flag that the study is **underpowered (n=5)** and that statistical significance (p-values) cannot be reliably calculated, as per the Plan's explicit limitation. Log a warning: "Sample size n=5 is insufficient for statistical significance; trend analysis only." (US-2, Plan Summary).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Comparative Analysis Report (Priority: P3)

**Goal**: Aggregate results from all runs into a `reproduction_report.md` with comparison tables and discrepancy analysis.

**Independent Test**: Run `scripts/generate_report.py`. Verify `reproduction_report.md` exists, contains a populated comparison table, and lists any discrepancies or `[DEFERRED]` flags.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T022 [P] [US3] Unit test in `tests/unit/test_report_generation.py` verifying that the report template renders correctly with mock JSON data.
- [X] T023 [P] [US3] Validation test in `tests/contract/test_report_schema.py` ensuring no empty cells in the comparison table.

### Implementation for User Story 3

- [X] T024 [US3] Implement `src/analysis/generate_report.py` to:
    1. Read `results/eval_results.json` (PRODUCED BY T013) and `results/condition_comparison.json` (PRODUCED BY T020) as primary inputs.
    2. Aggregate metrics and generate `reproduction_report.md`.
    3. Include a comparison table of accuracy scores for each model/condition pair.
    4. Compare reproduced values against paper baselines (if available) and flag `[NEEDS CLARIFICATION]` if diff > 5%.
    5. Include a "Discrepancies" section documenting methodological differences (e.g., seed, API version) and the underpowered study nature (Principle IV). (FR-007, US-3).
- [X] T026 [US3] Implement `src/analysis/check_disk_usage.py` to verify total `results/` size is < 500MB and log a warning if exceeded (SC-005).
- [X] T027 [US3] Ensure the "Discrepancies" section in `reproduction_report.md` explicitly states the study is underpowered (n=5) and cannot claim statistical significance (Plan Summary).

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T028 [P] Add `tests/integration/test_full_pipeline.py` to run the entire flow: Setup -> Baseline -> Conditions -> Report
- [X] T029 [P] Update `README.md` with instructions on how to run the reproduction pipeline and expected outputs
- [X] T030 [P] Run `src/validation/check_disk_usage.py` as a pre-commit hook or CI step to ensure SC-005 compliance
- [X] T031 [P] Verify `reproduction_report.md` passes the "no empty cells" check (SC-003)
- [X] T032 Run quickstart.md validation if available

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Relies on US-1 execution logic but adds condition logic
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Aggregates results from US-1 and US-2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Config loaders before execution scripts
- Execution scripts before analysis/report generation
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T005, T006, T008) can run in parallel
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Integration test for baseline run in tests/integration/test_baseline_run.py::test_baseline_run_generates_schema"

# Launch all models for User Story 1 together:
Task: "Create wrapper script scripts/run_reproduction.py"
Task: "Implement src/analysis/parse_logs.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (run 5 tasks, check JSON)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Validate blocking/noise)
4. Add User Story 3 → Test independently → Deploy/Demo (Generate Report)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Baseline Execution)
   - Developer B: User Story 2 (Condition Logic)
   - Developer C: User Story 3 (Report Generation)
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
- **Critical Constraint**: All tasks must run on CPU-only CI with limited cores and constrained memory. No GPU models, no 8-bit quantization, no large local LLMs.
- **Data Integrity**: Do not synthesize fake data. Use real `tasks.json` from the vendored submodule.
- **Timeouts**: Use `asyncio.wait_for` (T007) for cross-platform reliability.
- **Statistical Significance**: Acknowledge n=5 is insufficient; report trends, not p-values (T021).