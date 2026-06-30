# Tasks: Reproduce & Validate LongLive-2.0 NVFP4 Infrastructure

**Input**: Design documents from `/specs/001-reproduce-longlive-2-0/`
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

- [X] T001 Create project structure per implementation plan: `src/`, `src/configs/`, `src/scripts/`, `src/inference/`, `src/tests/` at repository root AND `contracts/` at repository root (NOT inside `src/`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 Create Python 3.10+ project with CPU-compatible dependencies (`torch`, `diffusers`, `transformers`, `opencv-python`, `pyyaml`)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T004 Create `requirements.txt` pinning CPU-only versions of `torch` and `fouroversix` (no CUDA flags)
- [X] T005 [P] Implement `src/scripts/setup_env.sh` to verify environment installation and dependency resolution
- [X] T006 [P] Create `contracts/inference_output.schema.yaml` defining valid video artifact metadata. REQUIRED fields: `artifact_path`, `duration`, `format`, `valid`. Source: `spec.md` Section 'Key Entities' and 'User Story 2'.
- [X] T007 Create `contracts/metrics_report.schema.yaml` defining `peak_ram_gb`, `execution_time`, `has_nan`, `quantization_mode_used`. NOTE: `checkpoint_status` is REMOVED from this schema because missing checkpoints cause immediate abort (see T007b); successful runs will never generate metrics with missing checkpoints.
- [X] T007b [P] Implement error handling path for missing checkpoints: Create `src/utils/error_handler.py` to log a structured 'missing_checkpoint' event to `logs/error.log`, write an error message to stderr, and exit with code 1 when checkpoints are not found, fulfilling the 'fail gracefully' requirement (FR-006).
- [X] T008 Configure error handling and logging infrastructure in `src/utils/logger.py`
- [X] T009 Setup environment configuration management to load `src/configs/inference.yaml`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Environment Initialization and Dependency Resolution (Priority: P1) 🎯 MVP

**Goal**: Initialize the project environment on a CPU-only CI runner where `fouroversix` is importable without GPU requirements.

**Independent Test**: A `pip install -r requirements.txt` and a `python -c "import fouroversix"` command run in a clean CPU-only container must complete without error.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for environment import in `tests/test_environment.py` verifying `import fouroversix` succeeds on CPU
- [X] T011 [P] [US1] Contract test for quantization module import in `tests/test_environment.py` verifying `from fouroversix.quantize import fp4_quant` loads

### Implementation for User Story 1

- [X] T012 [US1] Implement `src/scripts/setup_env.sh` to execute `pip install` and verify exit codes
- [X] T013 [US1] Create `src/utils/env_checker.py` with a `check_import()` function that attempts to import `fouroversix` and verifies the import succeeds without requiring CUDA drivers (FR-002).
- [X] T014 [US1] Add logging call in `src/scripts/setup_env.sh` to report the result of `check_import()` and confirm the environment is ready for CPU-only execution.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Inference Pipeline Execution on Sample Data (Priority: P2)

**Goal**: Execute the inference pipeline using a minimal, synthetic video prompt to verify end-to-end execution and artifact generation.

**Independent Test**: Run the inference script with a configuration pointing to a small test prompt and verify a video file is written to the output directory.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T016 [P] [US2] Integration test for synthetic video generation in `tests/test_inference.py` verifying output file creation
- [X] T017 [P] [US2] Integration test for OOM handling in `tests/test_inference.py` verifying explicit error on memory limit exceedance

### Implementation for User Story 2

- [X] T018 [P] [US2] Create `src/configs/inference.yaml` with synthetic prompt settings (2-4 frames, small batch)
- [X] T019 [US2] Implement `src/inference/inference.py` entry point to load config and execute pipeline (FR-003)
- [X] T020 [US2] Implement checkpoint validation logic in `src/inference/inference.py` to call T007b error handler if weights missing (FR-006)
- [X] T021 [US2] Implement pre-flight memory estimation in `src/inference/inference.py` to switch to sequence parallelism if RAM > 6.5GB (FR-007)
- [X] T022 [US2] Implement `src/inference/inference_sp.py` as the sequence parallel fallback for memory-constrained execution
- [X] T023 [US2] Implement artifact validation logic to ensure output `.mp4`/`.webm` is valid and non-empty (FR-004)
- [X] T024 [US2] Add logging for pipeline steps and memory usage during execution

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validation of NVFP4 Quantization and Performance Claims (Priority: P3)

**Goal**: Validate that the quantization path (or fallback) produces stable results and log performance metrics for comparison.

**Independent Test**: Execute inference with NVFP4 configuration (or fallback), capture memory usage, and log metrics to a report file.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Contract test for metrics schema in `tests/test_metrics.py` verifying `results/metrics.json` structure
- [X] T026 [P] [US3] Integration test for NaN detection in `tests/test_inference.py` verifying stability check on latent/pixel data

### Implementation for User Story 3

- [X] T027 [P] [US3] Create `src/configs/inference_nvfp4.yaml` defining NVFP4 quantization mode (or fallback emulation)
- [X] T028 [US3] Implement `src/inference/validator.py` to scan latent frames and pixel output for NaN/Inf values (SC-004). Sampling Strategy: Scan a representative subset of frames from the latent sequence and a representative subset of the final pixel output to satisfy CPU feasibility constraints (derived from Plan Phase 2, Step 2).
- [X] T029 [US3] Implement metric collection logic in `src/inference/validator.py` to record `peak_ram_gb`, `execution_time`, `fps`
- [X] T030 [US3] Implement report generation to write `results/metrics.json` conforming to `contracts/metrics_report.schema.yaml` (FR-005)
- [X] T031 [US3] Implement control case logic to log that both NVFP4 (fallback) and FP16 runs completed without NaNs (structural validity), and explicitly log the hardware difference (CPU vs Blackwell) and note the unverified nature of the "Long Video" and quantitative comparison claims (Spec US-3 Acceptance Scenario 3). DO NOT perform quantitative comparison of outputs.
- [X] T032 [US3] Add logic to explicitly log hardware difference (CPU vs Blackwell) and note unverified "Long Video" claims in the report

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T033 [P] Documentation updates in `src/README.md` covering CPU-only execution and synthetic data usage
- [X] T034 Code cleanup and refactoring of `inference.py` and `inference_sp.py`
- [X] T035 [P] Run `src/scripts/run_validation.sh` to execute the full pipeline end-to-end
- [X] T036 [P] Verify `results/metrics.json` and `outputs/` artifacts against success criteria SC-001 to SC-005
- [X] T037 [P] Run quickstart.md validation to ensure reproduction steps work on a fresh runner

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T006/T007 (contracts) for artifact validation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T018/T019 (inference logic) to run validation

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Configs before scripts
- Scripts before validation logic
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for environment import in tests/test_environment.py"
Task: "Contract test for quantization module import in tests/test_environment.py"

# Launch all implementation tasks for User Story 1 together:
Task: "Implement src/scripts/setup_env.sh to execute pip install and verify exit codes"
Task: "Create src/utils/env_checker.py with check_import() verifying import without CUDA"
Task: "Add logging call in src/scripts/setup_env.sh to report import result"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Environment ready, imports work)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Inference runs, video generated)
4. Add User Story 3 → Test independently → Deploy/Demo (Metrics logged, stability verified)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Environment)
   - Developer B: User Story 2 (Inference Pipeline)
   - Developer C: User Story 3 (Validation & Metrics)
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
- **Constraint**: All tasks must run on CPU-only CI (limited vCPU, constrained RAM) without CUDA.
- **Constraint**: Synthetic data (a small number of frames) must be used to meet the computational time limit..