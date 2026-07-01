# Tasks: Reproduce & Validate: Scaling the Horizon, Not the Parameters

**Input**: Design documents from `/specs/806-reproduce-validate-scaling-the-horizon-not-the-parameters-r/`
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

- [X] T001 Create project structure per implementation plan: execute `mkdir -p src tests results/raw results/reports agents-a1 evaluation/Search` in `projects/806-reproduce-validate-scaling-the-horizon-not-the-parameters-r/`
- [X] T002 Initialize Python project: Create `requirements.txt` at repository root with pinned versions: `torch==2.3.0`, `transformers==4.40.0`, `accelerate==0.30.0`, `datasets==2.19.0`, `pyyaml==6.0.1`, `pytest==8.1.0`
- [X] T003 [P] Configure linting (flake8/black) and formatting tools in `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `src/cpu_adapter.py` with function `load_model_cpu(model_id)` that sets `device_map="auto"` and `torch_dtype=torch.float32` (or `float16` if supported) for CPU-only loading, ensuring no CUDA imports
- [X] T005 [P] Implement `src/resource_monitor.py` to monitor RAM/CPU usage, enforce a hard RAM limit, and enforce a CPU core limit (pin to 2 cores or fail if >2 detected) per FR-004
- [X] T006 [P] Create `src/main.py` as the canonical CI entry point that orchestrates loading, monitoring, and execution
- [X] T007 [P] Define `src/scorer.py` interface: create function signatures `calculate_score(raw_log_path)` and `generate_report(scores)` in `src/scorer.py` (implement as stubs for now, full logic in T020)
- [X] T008 Configure error handling infrastructure to emit `ERR_OOM_CPU` (exit code 1) and `TIMEOUT_EXCEEDED` (exit code 2) codes
- [X] T009 Configure environment configuration management for benchmark selection and token limits in `config.yaml` (note: a fixed hard token limit is established for automated runs, with no override permitted)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute End-to-End Reproduction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Trigger the vendored `Agents-A1` evaluation pipeline via a single command, loading a model, executing a benchmark subset, and generating raw JSON logs without manual intervention.

**Independent Test**: Run `python src/main.py --benchmark ifbench --samples 5` in a clean CPU environment and verify `results/raw/ifbench_0.json` exists within 6 hours.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST (TDD), ensure they FAIL before implementation. These can be developed in parallel with implementation (marked [P]) but cannot be EXECUTED until implementation exists.**

- [X] T010 [P] [US1] Contract test `tests/unit/test_main_execution.py::test_pipeline_creates_json` to verify `main.py` creates valid JSON output
- [X] T011 [P] [US1] Integration test `tests/integration/test_cpu_load.py::test_cpu_only_model_load` to verify no CUDA errors on CPU-only runner

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement dataset fetcher for IFBench/SciCode in `src/data_loader.py` using verified HuggingFace datasets or GitHub raw URLs (e.g., `)
- [X] T012b [US1] Implement conditional logic in `src/main.py` to skip SEAL-0 benchmark (due to missing data) and proceed with IFBench/SciCode; if ALL available benchmarks (IFBench/SciCode) fail to execute, set `feasibility_status` to `INFEASIBLE`
- [X] T013 [US1] Implement token-count cutoff logic in `src/generation_loop.py` to stop generation if `token_count > 4000` and log `TIMEOUT_EXCEEDED`
- [X] T014 [US1] Implement the main inference loop in `src/main.py` that imports and calls `generation_loop.run()` (from T013) to enforce cutoff, avoiding `run.sh` invocation and wrapping the Python logic from `agents-a1/evaluation/Search/` directly
- [X] T015 [US1] Add logic to write raw trajectory JSON logs to `results/raw/` directory
- [X] T016 [US1] Add validation to ensure no CUDA imports or `bitsandbytes` usage in `src/main.py`
- [X] T017 [US1] Add logging for trajectory truncation reasons and partial results preservation

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (producing partial results if OOM or timeout occurs)

---

## Phase 4: User Story 2 - Validate Performance Against Paper Claims (Priority: P2)

**Goal**: Compare generated raw results against specific numerical claims (e.g., IFBench ≥ 80.6) and produce a validation report.

**Independent Test**: Run `python src/main.py --benchmark ifbench --samples 5 --validate` and verify `results/reports/validation_report.json` contains the score and feasibility status.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for `scorer.py` logic comparing scores in `tests/unit/test_scorer.py`
- [X] T019 [P] [US2] Integration test for report generation in `tests/integration/test_report_gen.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Complete implementation of score aggregation logic in `src/scorer.py` to parse `results/raw/*.json` (extends T007 interface)
- [X] T021 [US2] Implement paper claim comparison logic in `src/scorer.py`: calculate `|reproduced_score - paper_score|`, set `feasibility_status` to `INCONCLUSIVE` (remove binary pass/fail indicators as per Plan), and output `difference` field
- [X] T022 [US2] Implement validation report generator in `src/scorer.py` to output `results/reports/validation_report.json` with `score`, `difference`, and `feasibility_status` fields
- [X] T023 [US2] Integrate with User Story 1 components to trigger validation automatically after inference
- [X] T024 [US2] Add logic to flag `feasibility_status` as `INFEASIBLE` if OOM/timeout prevented execution, or `INCONCLUSIVE` if sample size is small (N=5), ensuring distinct status codes are used based on failure type

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Resource & Feasibility Audit (Priority: P3)

**Goal**: Confirm the reproduction process adheres to free-tier CI constraints (≤2 CPU, ≤7 GB RAM, ≤6h) and fails gracefully if exceeded.

**Independent Test**: Run `src/main.py` on a resource-constrained runner and verify it exits with `ERR_OOM_CPU` if memory > 7 GB, or completes successfully within limits.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Stress test for memory limit in `tests/integration/test_resource_limits.py`
- [X] T026 [P] [US3] Test for graceful failure on OOM in `tests/unit/test_resource_monitor.py`

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement hard memory limit enforcement in `src/resource_monitor.py`: add watchdog thread that checks RSS memory at regular intervals and calls `os._exit(1)` with code `ERR_OOM_CPU` if > 7GB
- [X] T028 [US3] Implement exit code logic for `ERR_OOM_CPU` and `TIMEOUT_EXCEEDED` in `src/main.py`
- [X] T029 [US3] Add telemetry logging to `results/resource_log.json` capturing peak RAM, CPU usage, and wall-clock time
- [X] T030 [US3] Add logic to verify no GPU-specific libraries are imported or initialized in `src/main.py`
- [X] T031 [US3] Update `quickstart.md` to document known limitations: add section stating "SEAL-0 is excluded from automation due to missing dataset source" (no automated path exists)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T032 [P] Update `README.md` with CLI usage examples and installation instructions
- [X] T033 Refactor `src/` modules to remove unused imports and optimize data loading in `src/data_loader.py`
- [X] T034 Performance optimization for data loading in `src/data_loader.py`
- [X] T035 [P] Additional unit tests for edge cases in `tests/unit/`
- [X] T036 Security hardening of dependency imports
- [X] T037 Run `quickstart.md` validation to ensure all steps work

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (raw logs)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1/US2 execution flow

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
- All tests for a user story marked [P] can run in parallel (development)
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test test_pipeline_creates_json in tests/unit/test_main_execution.py"
Task: "Integration test test_cpu_load in tests/integration/test_cpu_load.py"

# Launch all models for User Story 1 together:
Task: "Implement dataset fetcher for IFBench/SciCode in src/data_loader.py"
Task: "Implement token-count cutoff logic in src/generation_loop.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify pipeline runs, logs created, OOM handled)
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
 - Developer A: User Story 1 (Inference Pipeline)
 - Developer B: User Story 2 (Scoring/Validation)
 - Developer C: User Story 3 (Resource Monitoring)
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
- **CRITICAL**: Do not use `bitsandbytes` or 8-bit quantization; use standard CPU precision or offloading only.
- **CRITICAL**: If a large-scale model cannot load in 7 GB RAM, the system MUST abort with `ERR_OOM_CPU` (no silent fallback).
- **CRITICAL**: Dataset fetchers must use real, reachable URLs (e.g., HuggingFace datasets, GitHub raw content), not synthetic data.
- **CRITICAL**: Report must use `feasibility_status` (INCONCLUSIVE/INFEASIBLE) instead of binary Pass/Fail.