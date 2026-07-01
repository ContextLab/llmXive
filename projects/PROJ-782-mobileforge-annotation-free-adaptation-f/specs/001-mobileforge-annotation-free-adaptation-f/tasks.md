# Tasks: MobileForge: Annotation-Free Adaptation for Mobile GUI Agents with Hierarchical Feedback-Guided Policy Optimization

**Input**: Design documents from `/specs/782-mobileforge-reproduction/`
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

- [X] T001 Create project structure per implementation plan (`src/mobileforge/`, `tests/`, `data/`)
- [X] T002 Initialize Python 3.10+ project with `requirements.txt` (transformers, torch-cpu, bitsandbytes-cpu, accelerate, datasets, pytest, pandas, numpy, scipy)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data contracts and schemas in `contracts/` (trajectory.schema.yaml, feedback.schema.yaml, metrics.schema.yaml)
- [X] T005 Implement memory monitoring utility in `src/mobileforge/utils/monitor.py` (FR-002: triggers shutdown at a high memory threshold)
- [X] T006 Implement timeout enforcement utility in `src/mobileforge/utils/timeout.py` (FR-006: A hard limit on the number of samples will be established. The research question, method, and references remain unchanged as per the planning document.)
- [X] T007 Create mock Android environment interface in `src/mobileforge/evaluation/androidworld/interface.py` (Headless/SIMULATION_MODE)
- [X] T008a [P] Implement base model loader function in `src/mobileforge/utils/model_loader.py` (Create function to load model from path)
- [X] T008b [P] Implement model existence check in `src/mobileforge/utils/model_loader.py` (Check for Qwen2.5-VL-7B primary and Qwen2-VL-2B fallback; exit 1 if missing)
- [X] T008c [P] Implement error handling in `src/mobileforge/utils/model_loader.py` (Print clear error message and The system returns a non-zero exit code if weights are missing., per FR-007)
- [X] T009 Configure environment variables and CI resource constraints (CPU-only, GB RAM limits)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Execute Core Reproduction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Execute the vendored MobileForge codebase end-to-end on a CPU-only CI runner to generate initial rollout artifacts and evaluation logs.

**Independent Test**: Run `rollout/run.py` with `--num-tasks 10` and verify `trajectories.jsonl` and `evaluation_results.json` exist without OOM or timeout.

### Implementation for User Story 1

- [X] T010 [US1] Implement `src/mobileforge/rollout/run.py` entry point with task sampling from AndroidWorld registry. **Deliverables**: Output `data/trajectories.jsonl`, CLI args `--num-tasks` and `--model-path`, exit code 1 on failure.
- [X] T011 [US1] Integrate memory monitor (`utils/monitor.py`) into rollout loop to enforce 6.5GB limit (FR-002: Graceful shutdown)
- [X] T012 [US1] Integrate timeout decorator (`utils/timeout.py`) into task execution loop (300s limit)
- [X] T014 [US1] Implement trajectory serialization to `data/trajectories.jsonl` (Task ID, Steps, Final Status)
- [X] T015 [US1] Implement `src/mobileforge/evaluation/androidworld/run.py` to process trajectories against registry. **Deliverables**: Input `data/trajectories.jsonl`, Output `data/evaluation_results.json` (JSON with success/failure flags). **Requirement**: Log `SIMULATION_MODE` flag if emulator fails (Edge Cases).
- [X] T016 [US1] Generate `data/evaluation_results.json` with success/failure flags per task

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Hierarchical Feedback (HiFPO) Data Generation (Priority: P2)

**Goal**: Verify that the HiFPO module correctly generates step-level feedback and corrective hints from trajectory data.

**Independent Test**: Run curriculum generator on `trajectories.jsonl` and verify `feedback.jsonl` contains `error_type` and `hint_text` (len >= 10).

**Note**: T017 can begin immediately after T014 completes (trajectories generated), not waiting for full Phase 3 completion.

### Implementation for User Story 2

- [X] T017 [US2] Implement `src/mobileforge/feedback/curriculum_generator.py` to parse `data/trajectories.jsonl`. **Deliverables**: Output `data/feedback.jsonl`.
- [X] T018 [US2] Implement feedback extraction logic: map failure states to `error_type` and `step_context`
- [X] T019 [US2] Implement hint generation logic ensuring `hint_text` is non-empty and >= 10 chars (FR-005)
- [X] T020 [US2] Implement silent failure detection: flag trajectories with no error code as `warning`
- [X] T021 [US2] Serialize feedback to `data/feedback.jsonl` with schema validation against `contracts/feedback.schema.yaml`
- [X] T022 [US2] Add logging for feedback generation stats (% coverage target, hint length distribution)

**Checkpoint**: User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Reproduce Performance Metrics Against Baseline (Priority: P3)

**Goal**: Compute and report the Pass@k success rate on the AndroidWorld benchmark and compare against baseline.

**Independent Test**: Calculate Pass@3 with 1000 bootstrap iterations for 95% CI and generate discrepancy alert if >5% diff.

**Note**: T023 can begin immediately after T016 completes (evaluation results generated), not waiting for full Phase 4 completion.

### Implementation for User Story 3

- [X] T023 [US3] Implement `src/mobileforge/metrics/pass_k.py` to aggregate `data/evaluation_results.json`. **Deliverables**: Output `data/metrics_report.json`.
- [X] T024 [US3] Implement Pass@3 calculation logic (Success within top 3 attempts)
- [X] T025 [US3] Implement A sufficient number of bootstrap iterations will be performed for 95% Confidence Interval calculation. (FR-004, SC-003)
- [X] T026 [US3] Implement baseline comparison logic (load paper reference or cached run)
- [X] T027 [US3] Implement "Discrepancy Alert" logic: flag if diff > 5% and log specific failed tasks
- [X] T028 [US3] Generate final report `data/metrics_report.json` with Pass@3, CI bounds, and comparison stats

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029 [P] Documentation updates in `research.md` (environment differences, limitations). **Dependency**: Must run after Phases 3, 4, 5 complete.
- [X] T030a [P] Code cleanup: Naming convention fixes in `src/mobileforge/utils/`
- [X] T030b [P] Code cleanup: Dead code removal in `src/mobileforge/`
- [X] T030c [P] Code cleanup: Structure refactoring in `src/mobileforge/`
- [X] T031a [P] Performance optimization: Implement `gc.collect()` after each task in `rollout/run.py`
- [X] T031b [P] Performance optimization: Verify peak RAM reduction in `tests/integration/test_memory.py`
- [X] T032 [P] Unit tests for metric calculation logic in `tests/unit/test_metrics.py`
- [X] T033 [P] Contract tests for JSON schemas in `tests/contract/test_schemas.py`
- [X] T034 Run `quickstart.md` validation to ensure pipeline executes end-to-end

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T014 (trajectories) output. **Note**: T017 can run as soon as T014 is done, not waiting for Phase 4 start.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T016 (evaluation) output. **Note**: T023 can run as soon as T016 is done, not waiting for Phase 5 start.

### Within Each User Story

- Models/Utils before Services
- Services before Endpoints/Scripts
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- T017 (US2) can start immediately after T014 (US1) completes
- T023 (US3) can start immediately after T016 (US1) completes
- All tests for a user story marked [P] can run in parallel
- T029, T030, T031 are NOT parallel with User Stories; they must run AFTER Phases 3, 4, 5 are complete.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Rollout + Eval)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Feedback Gen)
4. Add User Story 3 → Test independently → Deploy/Demo (Metrics)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Rollout/Eval)
   - Developer B: User Story 2 (Feedback) - Can start as soon as T014 is done
   - Developer C: User Story 3 (Metrics) - Can start as soon as T016 is done
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
- **Critical Constraint**: All tasks must run on CPU-only, multiple vCPUs, ~7GB RAM, 6h limit. No GPU, no 8-bit quantization requiring CUDA, no full Android emulator.
- **Resource Integrity**: FR-002 requires graceful shutdown on OOM. No fallback logic is implemented; the system must exit if RAM > 6.5GB.
- **Statistical Rigor**: SC-003 requires 1000 bootstrap iterations for CI, not Exact Binomial.