# Tasks: Reproduce & Validate VideoKR

**Input**: Design documents from `/specs/667-reproduce-validate-videokr/`
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

- [X] T001 [P] Create directory structure: `src/videokr_validation/`, `tests/`, `scripts/`, `artifacts/`, and explicitly `artifacts/logs/` per plan.md

- [X] T002 [P] Initialize `requirements.txt` with CPU-only constraints: `torch` (CPU-only build), `transformers`, `accelerate`, `pandas`, `pyarrow`. **Explicitly remove** `bitsandbytes`, `flash-attn`, and any GPU-specific dependencies from the file before installation.

- [X] T003 [P] Create `scripts/setup_env_cpu.sh` to install dependencies and verify CPU-only import success

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `src/videokr_validation/utils.py` with `check_cpu_only()` (skips GPU libs), `calculate_memory_footprint(model_name, batch_size)`, `verify_environment()` (checks CUDA and logs status), and `verify_environment()` functions

- [X] T005 [P] Implement `src/videokr_validation/__init__.py` to expose version and utility functions

- [X] T006 [P] Create `tests/unit/test_imports.py` to verify no CUDA errors on import of `llamafactory` and `lmms_eval`

- [X] T007 [P] Create `tests/contract/test_data_schema.py` to validate JSONL/Parquet schema (fields: `video_path`, `question`, `answer`, `rationale`)

- [X] T008 [P] Create `tests/contract/test_log_schema.py` to validate log format (timestamps, step counts)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Environment Initialization and Dependency Resolution (Priority: P1) 🎯 MVP

**Goal**: Initialize a CPU-only runtime, install dependencies without GPU errors, and verify core imports.

**Independent Test**: Run `scripts/setup_env_cpu.sh` and `python -c "import llamafactory; print('Import OK')"` on a 2 CPU/7GB RAM runner; must exit 0.

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement `scripts/setup_env_cpu.sh` to install `requirements.txt` **after patching** to remove GPU-only packages, and verify that no GPU binaries are present in the installed environment

### Verification & Run for User Story 1

- [X] T013 [P] [US1] [Run] Execute `src/videokr_validation/utils.py` function `verify_environment()` (depends on T004) and log environment details (Python version, torch version, memory available) to `artifacts/logs/env.log`

### Tests for User Story 1

- [X] T009 [P] [US1] Unit test `test_cpu_only_check` in `tests/unit/test_imports.py` to assert `not torch.cuda.is_available()` on CPU runner

- [X] T010 [P] [US1] Unit test `test_skip_gpu_deps` in `tests/unit/test_imports.py` to verify `bitsandbytes` is skipped or mockable

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Data Preparation and Subsampling Execution (Priority: P2)

**Goal**: Execute data preparation on a subsampled dataset (≤100 examples) or synthetic mock data, ensuring schema validity and memory safety.

**Independent Test**: Run `src/videokr_validation/data_prep.py --limit 100`; verify output file < 10MB and schema matches contract.

### Implementation for User Story 2

- [X] T016 [P] [US2] Implement `src/videokr_validation/data_prep.py` with `--limit` argument and **dynamic retry logic**: if a `MemoryError` or `OOM` occurs during loading, automatically retry with `--limit 10`

- [X] T017 [US2] Implement `src/videokr_validation/data_prep.py` logic for "Synthetic Mock Mode": generate synthetic video tensors (shape: [T, H, W, 3], dtype: float32) and text pairs if real data path is invalid (Fallback only)

- [X] T018 [US2] Implement `src/videokr_validation/data_prep.py` logic to write output to `artifacts/data/subsampled.jsonl` (or `.parquet`)

- [X] T019 [US2] Add error handling in `src/videokr_validation/data_prep.py` to fail gracefully with "Data path not found" if neither real nor synthetic data is usable

### Tests for User Story 2

- [X] T014 [P] [US2] Contract test `test_data_schema_limit_100` in `tests/contract/test_data_schema.py` to verify output fields exist and file size < 10MB

- [X] T015 [P] [US2] Integration test `test_synthetic_mock_mode` in `tests/integration/test_full_pipeline.py` to verify synthetic data generation when real data is missing

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validation Run on Small Model and Dataset (Priority: P3)

**Goal**: Execute a 1-step training/evaluation dry-run with a small CPU-compatible model (no hardcoded default; user must provide or system selects based on memory budget) to verify integration.

**Independent Test**: Run `src/videokr_validation/train_dryrun.py --max_steps 1`; verify log contains "Step 1 completed" and exits 0 within 20 mins.

### Implementation for User Story 3

- [X] T022 [P] [US3] Implement `src/videokr_validation/train_dryrun.py` with `--model_name_or_path` (no default; user must provide). Add logic to validate model size parameters before loading; if estimated footprint > 6.5GB, abort or fallback to a smaller model/data-only mode

- [X] T023 [US3] Implement `src/videokr_validation/train_dryrun.py` logic to perform a pre-flight memory check using `utils.calculate_memory_footprint(model_name, batch_size)` and abort if > 6.5 GB

- [X] T024 [US3] Implement `src/videokr_validation/train_dryrun.py` logic to use `device_map='cpu'` and `low_cpu_mem_usage=True`

- [X] T025 [US3] Implement `src/videokr_validation/train_dryrun.py` to write execution logs to `artifacts/logs/train.log` including "Training started" and "Step X completed"

- [X] T026 [US3] Implement `src/videokr_validation/train_dryrun.py` to output a final status JSON to `artifacts/logs/reproduction_report.json` with schema: `{status, error_message, step_count, memory_peak}`

- [X] T031 [US3] Implement `src/videokr_validation/data_prep.py` (or dedicated script) to perform a Video I/O Stress Test: decode a single frame from a real video (if available) to verify temporal sampling logic

### Tests for User Story 3

- [X] T020 [P] [US3] Integration test `test_dry_run_memory_check` in `tests/integration/test_full_pipeline.py` to verify `calculate_memory_footprint` aborts if > 6.5GB (depends on T023)

- [X] T021 [P] [US3] Contract test `test_log_schema_step_1` in `tests/contract/test_log_schema.py` to verify "Step 1" entry exists in `train.log`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T027 [P] Documentation updates: Add `README.md` instructions for running the CPU-only validation pipeline locally and in CI

- [X] T028 Code cleanup: Remove any hardcoded GPU device strings or CUDA-specific imports from `src/`

- [X] T029 [P] Add `tests/integration/test_full_pipeline.py` to run the full sequence: Setup -> Data Prep -> Dry Run

- [X] T030 [P] Run quickstart.md validation to ensure all paths and scripts are executable

- [X] T032 [P] Update `src/videokr_validation/utils.py` to include the explicit abort logic for memory checks as described in T023

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
Task: "Unit test test_cpu_only_check in tests/unit/test_imports.py"
Task: "Unit test test_skip_gpu_deps in tests/unit/test_imports.py"

# Launch all models for User Story 1 together:
Task: "Create directory structure..."
Task: "Initialize requirements.txt..."
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