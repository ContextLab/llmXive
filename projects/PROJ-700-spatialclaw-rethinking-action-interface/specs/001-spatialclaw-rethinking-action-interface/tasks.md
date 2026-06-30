# Tasks: Reproduce & Validate SpatialClaw (CPU Feasibility)

**Input**: Design documents from `/specs/700-reproduce-validate-spatialclaw/`
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

- [X] T001 Create project structure per implementation plan (`spatial_agent/`, `results/`, `logs/`)
- [X] T002 Initialize Python 3.10+ project with CPU-only dependencies (`torch`, `transformers`, `datasets`, `pandas`, `pydantic`, `psutil`, `pytest`)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `spatial_agent/core/resource_monitor.py` to enforce RAM and CPU time limits in accordance with standard research constraints [1]. (per plan.md values) and abort immediately if exceeded (FR-004). Must include peak tracking and hard abort logic (No Fallback).
- [X] T005 [P] Implement `spatial_agent/core/gpu_detector.py` to block CUDA/bitsandbytes initialization, check `torch.cuda.is_available()`, and raise `RuntimeError: GPU not available; aborting` (FR-005).
- [X] T006 [P] Create `spatial_agent/config/model/` configuration for CPU-tractable VLMs (e.g., `microsoft/Phi-3-vision-128k-instruct` default).
- [X] T007 Create `spatial_agent/config/dataset/` configuration for BLINK subset paths.
- [X] T008 Implement `spatial_agent/utils/logging.py` for structured JSON and human-readable logging (FR-006).
- [X] T009A Implement error handler for "Dataset not found" scenario with specific error code 1 and message "Dataset not found: <path>".
- [X] T009B Implement error handler for "Memory Limit Exceeded" scenario with specific error code 1 and message "Memory Limit Exceeded: <current>MB > <limit>MB".

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute End-to-End Reproduction Pipeline (Priority: P1) 🎯 MVP

**Goal**: Initialize environment, load vendored code, execute agent on BLINK subset, and produce structured logs.

**Independent Test**: Run `spatial_agent/entrypoints/run.py --dataset blink --subset 5` and verify `results/blink_subset_5.json` exists and exit code is 0.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for `spatial_agent/entrypoints/run.py` argument parsing in `spatial_agent/tests/contract/test_entrypoint.py`
- [X] T011 [P] [US1] Integration test for dataset download retry logic (a bounded number of attempts) in `spatial_agent/tests/integration/test_dataset_fetch.py`

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `spatial_agent/core/agent.py` with VLM loading logic (CPU-only), execution loop for BLINK subset, and syntax error handling (catch, log, skip/reflection).
- [X] T013 [P] [US1] Implement `spatial_agent/core/dataset_loader.py` with retry logic (up to 3 attempts) for dataset download and validation of spatial tasks presence.
- [X] T014 [US1] Implement `spatial_agent/entrypoints/run.py` to orchestrate resource monitoring (T004), agent execution (T012), dataset loading (T013), and save results to `results/blink_subset_5.json`.
- [X] T015 [US1] Add structured logging hooks in `spatial_agent/entrypoints/run.py` to capture intermediate steps and VLM prompts (FR-006).
- [X] T016 [US1] Implement graceful exit with specific error code 1 if dataset is missing (US-1 Edge Case).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate Artifact Integrity & Reproducibility (Priority: P2)

**Goal**: Validate generated outputs against dataset ground truth AND paper baselines (with warnings for invalid comparisons).

**Independent Test**: Run validation script on `results/blink_subset_5.json` and verify it flags "PASS" if accuracy matches ground truth, or "WARN: Deviation > 5%" if paper baseline comparison is attempted but statistically invalid.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Contract test for `spatial_agent/core/validator.py` schema validation in `spatial_agent/tests/contract/test_validator.py`
- [X] T018 [P] [US2] Integration test for ground truth comparison logic in `spatial_agent/tests/integration/test_validation.py`

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `spatial_agent/core/validator.py` to load `results/` JSON and compare against dataset ground truth labels.
- [X] T020 [US2] Implement logic in `spatial_agent/core/validator.py` to verify presence of `intermediate_steps` (code-as-action interface).
- [X] T021 [US2] Implement `spatial_agent/entrypoints/validate.py` to generate `validation_report.json` with PASS/WARN status.
- [X] T022 [US2] Add logic to `spatial_agent/core/validator.py` to detect model version mismatches and flag warnings (US-2 Edge Case).
- [X] T023 [US2] Integrate validation report generation with the main run pipeline (optional post-run step).
- [X] T024 [US2] Implement paper-baseline validation logic in `spatial_agent/core/validator.py` (FR-003) to compare against [deferred] baseline, flagging "WARN: Statistical Variance (Small Subset)" if n < 100, ensuring FR-003 is met while adhering to Plan's scientific rigor.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Resource Feasibility Audit (Priority: P3)

**Goal**: Enforce strict compute constraints and log resource usage. (Logic already implemented in T004; this phase is for integration and verification).

**Independent Test**: Run pipeline with resource monitor attached; verify report includes `peak_ram_mb` and `cpu_time_sec` and aborts if exceeded.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Contract test for `psutil` memory limit check in `spatial_agent/tests/contract/test_resource_monitor.py`
- [X] T026 [P] [US3] Integration test for CPU time limit enforcement in `spatial_agent/tests/integration/test_resource_limits.py`

### Implementation for User Story 3

- [X] T027 [US3] Integrate `resource_monitor` (T004) into `spatial_agent/entrypoints/run.py` to wrap the main process.
- [X] T028 [US3] Verify "GPU not available" error check in `spatial_agent/core/gpu_detector.py` (T005) is triggered on startup if CUDA is detected.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T029 [P] Documentation updates in `docs/` and `README.md`
- [X] T030 Code cleanup and refactoring of `spatial_agent/core/`
- [X] T031 Performance optimization for dataset loading
- [X] T032 [P] Additional unit tests in `spatial_agent/tests/unit/`
- [X] T033 Run `quickstart.md` validation to ensure end-to-end flow works on CI
- [X] T034 Update `spec.md` FR-004 to replace "substantial capacity/duration" with specific values "GB RAM / 6h CPU" to resolve testability gap.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 producing artifacts
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Integrated into US1 execution flow

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
Task: "Contract test for run.py argument parsing in spatial_agent/tests/contract/test_entrypoint.py"
Task: "Integration test for dataset download retry logic in spatial_agent/tests/integration/test_dataset_fetch.py"

# Launch all models for User Story 1 together:
Task: "Implement spatial_agent/core/agent.py with VLM loading, execution loop, and error handling"
Task: "Implement spatial_agent/core/dataset_loader.py with retry logic"
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