# Tasks: Causal Forcing++ Reproduction & Validation

**Input**: Design documents from `/specs/580-reproduce-causal-forcing-validation/`
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

- [X] T001 Create directory structure `specs/580-reproduce-causal-forcing-validation/scripts/` and `specs/580-reproduce-causal-forcing-validation/configs/`
- [X] T002 Initialize Python 3.10 virtual environment and install base dependencies (`pytest`, `pyyaml`, `jsonschema`, `psutil`)
- [X] T003 [P] Configure linting (flake8/black) for the `specs/580-reproduce-causal-forcing-validation/` directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `specs/580-reproduce-causal-forcing-validation/contracts/validation_report.schema.yaml` defining the JSON schema for the final report
- [X] T005 [P] Create `specs/580-reproduce-causal-forcing-validation/contracts/artifact_manifest.schema.yaml` defining the schema for generated artifacts
- [X] T006 [P] Implement `specs/580-reproduce-causal-forcing-validation/scripts/memory_monitor.py` utility to log peak RAM usage via `psutil`. **Interface**: Must write a JSON object to `data/memory_log.json` with keys `step_name`, `peak_ram_gb`, and `timestamp`.
- [X] T007 [P] Ensure `data/` directory exists for log artifacts.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Environment Initialization and Dependency Resolution (Priority: P1) 🎯 MVP

**Goal**: Ensure the `Causal-Forcing` submodule is initialized, dependencies are resolved, and core modules import successfully on a CPU-only runner.

**Independent Test**: Execute `python -c "import wan; import model; import pipeline"` in the project environment without `ModuleNotFoundError` or `ImportError`.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [Depends: T002] [US1] Unit test for submodule hash verification in `specs/580-reproduce-causal-forcing-validation/tests/test_validate_env.py`
- [X] T009 [P] [Depends: T002] [US1] Unit test for import success in `specs/580-reproduce-causal-forcing-validation/tests/test_imports.py`

### Implementation for User Story 1

- [X] T010 [US1] Implement `specs/580-reproduce-causal-forcing-validation/scripts/validate_env.py` to: 1) Run `git submodule update --init` for `external/Causal-Forcing`, 2) Verify commit hash matches spec, 3) Install `external/Causal-Forcing/requirements.txt` and `long_video/requirements.txt`, 4) Execute import checks for `wan`, `model`, and `pipeline`. Exit code 1 if any step fails with specific error message.
- [X] T011 [US1] Add logging in `validate_env.py` to record environment setup duration and exit status.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Lightweight Inference Execution (Priority: P1)

**Goal**: Execute the inference pipeline with minimal configuration to generate a valid video artifact within memory and time limits.

**Independent Test**: Run `demo.py` with `--num_steps 2 --frames 16` and verify a `.mp4` file > 1KB is generated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T015 [P] [US2] Contract test for video artifact existence and codec validation in `specs/580-reproduce-causal-forcing-validation/tests/test_inference_artifact.py`
- [X] T016 [P] [US2] Integration test for CPU fallback logic in `specs/580-reproduce-causal-forcing-validation/tests/test_cpu_inference.py`

### Implementation for User Story 2

- [X] T017 [P] [US2] Create `specs/580-reproduce-causal-forcing-validation/configs/cpu_inference_override.yaml` setting `num_steps=2`, `frames=16`, `resolution=256x256`. **Schema**: Must conform to the structure expected by `demo.py` (keys: `model`, `steps`, `frames`, `resolution`, `device`).
- [X] T018 [US2] Implement `specs/580-reproduce-causal-forcing-validation/scripts/run_inference_cpu.py` to check for `wan_t2v_1_3B` weights and fail fast if missing.
- [X] T019 [US2] Implement `specs/580-reproduce-causal-forcing-validation/scripts/run_inference_cpu.py` to force `device="cpu"` and `torch.float16` (with fallback to `float32` if OOM).
- [X] T020 [US2] Implement `specs/580-reproduce-causal-forcing-validation/scripts/run_inference_cpu.py` to execute `demo.py` with the override config.
- [X] T021 [US2] Implement `specs/580-reproduce-causal-forcing-validation/scripts/run_inference_cpu.py` to validate generated `.mp4` file size > 1KB and valid headers.
- [X] T022 [US2] Integrate `memory_monitor.py` into `run_inference_cpu.py` to log peak RAM usage to `data/memory_log.json` with `step_name="inference"` in JSON format.
- [X] T023 [US2] Add logic to handle `CUDA out of memory` by catching the exception and logging "Memory Limit Exceeded" with a specific exit code.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Training Step Validation (Priority: P2)

**Goal**: Execute a single training step using synthetic data to verify loss computation, gradient flow, and checkpoint saving.

**Independent Test**: Run `train.py` with `--max_steps 5` and verify a checkpoint `.pt` file > 100KB is written with valid state dict.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Unit test for synthetic data loader shape validation in `specs/580-reproduce-causal-forcing-validation/tests/test_synthetic_loader.py`
- [X] T025 [P] [US3] Integration test for gradient non-zero check in `specs/580-reproduce-causal-forcing-validation/tests/test_training_gradients.py`

### Implementation for User Story 3

- [X] T026 [P] [US3] Create `specs/580-reproduce-causal-forcing-validation/configs/cpu_training_override.yaml` setting `max_steps=5`, `batch_size=1`, `synthetic_data=true`. **Schema**: Must conform to `train.py` config structure (keys: `steps`, `batch_size`, `data_source`, `device`).
- [X] T027 [US3] Implement `specs/-reproduce-causal-forcing-validation/scripts/run_training_dummy.py` to instantiate a dummy `DataLoader` yielding random tensors with shape `(1, 3, 256, 256)`, dtype `float32`, on `device="cpu"`.
- [X] T028 [US3] Implement `specs/580-reproduce-causal-forcing-validation/scripts/run_training_dummy.py` to force `device="cpu"` and disable gradient checkpointing if needed.
- [X] T029 [US3] Implement `specs/580-reproduce-causal-forcing-validation/scripts/run_training_dummy.py` to execute `train.py` for a minimal number of steps.
- [X] T030 [US3] Implement `specs/580-reproduce-causal-forcing-validation/scripts/run_training_dummy.py` to verify loss values are finite (not NaN/Inf) and specifically that the `causal_cd` or `dmd` loss function is being called and producing non-zero values.
- [X] T031 [US3] Implement `specs/580-reproduce-causal-forcing-validation/scripts/run_training_dummy.py` to verify gradient L2-norms are non-zero (confirming backpropagation).
- [X] T032 [US3] Implement `specs/580-reproduce-causal-forcing-validation/scripts/run_training_dummy.py` to save and validate checkpoint file size > 100KB, and load the checkpoint to assert that specific tensor shapes (e.g., attention layers) match the expected model architecture.
- [X] T033 [US3] Integrate `memory_monitor.py` into `run_training_dummy.py` to log peak RAM usage to `data/memory_log.json` with `step_name="training"` in JSON format.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reporting & Compliance (Priority: P2)

**Goal**: Aggregate results into a validation report and ensure compliance with resource constraints.

**Independent Test**: `validation_report.json` must exist, pass schema validation, and confirm all FRs and SCs are met.

### Implementation for Phase 6

- [X] T034 [P] [US3] Implement `specs/580-reproduce-causal-forcing-validation/scripts/generate_report.py` to aggregate logs, artifact paths, and exit codes.
- [X] T035 [P] [US3] Implement `specs/580-reproduce-causal-forcing-validation/scripts/generate_report.py` to include peak RAM usage and total runtime.
- [X] T036 [US3] Implement `specs/580-reproduce-causal-forcing-validation/scripts/generate_report.py` to validate output against `contracts/validation_report.schema.yaml` (structure only).
- [X] T037 [US3] Implement `specs/580-reproduce-causal-forcing-validation/scripts/run_all_validation.sh` to orchestrate the execution of `validate_env.py`, `run_inference_cpu.py`, `run_training_dummy.py`, and `generate_report.py` sequentially. Include a step to log the "Default SSoT Principles" mapping used for validation.
- [X] T038 [US3] Implement explicit schema validation in `run_all_validation.sh` (or a wrapper script) that uses `jsonschema` to validate `validation_report.json` against `contracts/validation_report.schema.yaml` and fails the build if invalid.
- [X] T039 [US3] Implement `specs/580-reproduce-causal-forcing-validation/scripts/validate_resources.py` to: 1) Read `data/memory_log.json` produced by T022/T033, 2) Calculate the maximum peak RAM across all steps, 3) Assert that max RAM < 7GB (SC-005). If exceeded, log "SC-005 VIOLATION: RAM > 7GB" and exit with code 1.
- [X] T040 [US3] Create `specs/580-reproduce-causal-forcing-validation/scripts/run_schema_validation.py` to explicitly load `validation_report.json` and run it against `contracts/validation_report.schema.yaml` using `jsonschema`, exiting with code 1 if invalid.

**Checkpoint**: Final validation report generated and compliant

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Reporting (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Requires successful environment setup
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Requires successful environment setup
- **Reporting (Phase 6)**: Requires completion of US1, US2, and US3

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Config files before execution scripts
- Execution scripts before validation logic
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Config creation and script implementation for different USs can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for submodule hash verification in specs/580-reproduce-causal-forcing-validation/tests/test_validate_env.py"
Task: "Unit test for import success in specs/580-reproduce-causal-forcing-validation/tests/test_imports.py"

# Launch all models for User Story 1 together:
Task: "Implement validate_env.py to run git submodule update"
Task: "Implement validate_env.py to install requirements"
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
- **CRITICAL**: All inference and training tasks MUST enforce CPU-only execution and synthetic data to comply with free CI constraints (limited vCPU and RAM).
- **Note on data-model.md**: While the plan references `data-model.md`, the config schemas are defined inline in T017 and T026 to ensure self-contained task execution.
- **Note on Constitution**: The validation uses "Default SSoT Principles" as a fallback since `constitution.md` was not provided.