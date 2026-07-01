# Tasks: DomainShuttle Reproduction & Validation

**Input**: Design documents from `/specs/791-domainshuttle-reproduction/`
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

- [X] T001 Create project structure with directories: `src/domainshuttle/`, `tests/`, `scripts/`, `assets/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [X] T004 Create `src/domainshuttle/config.py` to manage inference configurations (frame count, resolution, seed) and enforce CPU-only flags
- [X] T005 [P] Implement `src/domainshuttle/memory_monitor.py` module using `tracemalloc` to log peak RAM usage to stderr and exit with code 1 if > 7GB
- [X] T006 [P] Create `scripts/install_deps.sh` to install system packages (ffmpeg, libgl1) and verify Python dependency tree excludes `bitsandbytes` and `cuda`
- [X] T007 Create `src/domainshuttle/__init__.py` and base module structure
- [X] T008 Configure error handling infrastructure in `src/domainshuttle/utils.py` to catch `MemoryError` and `TimeoutError` gracefully
- [X] T009 Setup environment variable configuration for `HF_HOME` and temporary disk limits in `src/domainshuttle/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Environment Setup & Dependency Resolution (Priority: P1) 🎯 MVP

**Goal**: The CI runner successfully clones the vendored `DomainShuttle` submodule, resolves all Python dependencies, and configures the environment to run inference scripts without GPU acceleration.

**Independent Test**: Can be fully tested by executing the `install.py` script and verifying that all required Python packages are installed and importable in a CPU-only context.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Write test code in `tests/unit/test_dependencies.py` to verify `requirements.txt` does not contain `bitsandbytes`, `nvidia-cuda`, or `bitsandbytes`
- [X] T011 [P] [US1] Write test code in `tests/integration/test_install.py` to run `scripts/install_deps.sh` and verify `pip list` output

### Implementation for User Story 1

- [X] T012 [P] [US1] Create `requirements.txt` pinning `torch` (CPU wheel), `diffusers`, `transformers`, `accelerate`, `clip`, `av`, `opencv-python-headless`
- [X] T013 [P] [US1] Implement `src/domainshuttle/install.py` to verify installation and import core modules (`inference`, `validator`, `config`)
- [X] T014 [US1] Implement logic in `src/domainshuttle/install.py` to explicitly check for absence of CUDA-specific imports; exit with code 1 and log error message if found
- [X] T015 [US1] Add `scripts/install_deps.sh` to install `ffmpeg` and `libgl1` system dependencies required for video processing
- [X] T016 [US1] Add validation in `src/domainshuttle/install.py` to confirm `torch.cuda.is_available()` returns `False` or is ignored
- [X] T017 [US1] Add logging in `src/domainshuttle/install.py` for successful dependency resolution and memory footprint estimation

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Tractable Inference Execution (Priority: P2)

**Goal**: The system executes a single, short-form Subject-to-Video (S2V) or Text-to-Video (T2V) generation using a lightweight model configuration on the CPU-only runner, producing a valid video artifact.

**Independent Test**: Can be tested by running a specific inference script (e.g., `examples/wan2.2_fun/predict_s2v.py` with a small sample) and verifying the output video file exists and is playable.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Write test code in `tests/unit/test_inference_config.py` to verify `inference.py` rejects `load_in_8bit=True` or `device_map="cuda"`
- [X] T019 [P] [US2] Write test code in `tests/integration/test_inference_run.py` to run inference with sample image/prompt and verify output `.mp4` exists

### Implementation for User Story 2

- [X] T020 [P] [US2] Create `src/domainshuttle/inference.py` with explicit `device="cpu"` and `load_in_8bit=False` flags. **Explicitly forbid 8-bit quantization layers**; use standard float32/float16 precision only.
- [X] T021 [US2] Implement logic in `src/domainshuttle/inference.py` to use config-defined frame count (default 16) and resolution (default 512x512) to fit 7GB RAM. **Note**: Resolution Sensitivity Analysis relies on frame count reduction (16 -> 8), NOT 8-bit quantization.
- [X] T022 [US2] Implement CLI interface in `src/domainshuttle/cli.py` accepting `--image`, `--prompt`, `--config` arguments
- [X] T023 [US2] Integrate `src/domainshuttle/memory_monitor.py` into `src/domainshuttle/inference.py` to log peak usage and fail if > 7GB
- [X] T024 [US2] Implement timeout handling in `scripts/run_inference.sh` using `timeout h` command to prevent hanging
- [X] T025 [US2] Add logic to `src/domainshuttle/inference.py` to handle missing reference images with a clear error message (not generic crash)
- [X] T026 [US2] Implement the "Resolution Sensitivity Analysis" trigger: If the 16-frame run fails (MemoryError or fidelity < 0.5) AND the total elapsed time is < 5.5 hours, automatically trigger a secondary 8-frame run. If time > 5.5h, skip secondary run and log "Timeout Risk - Sensitivity Analysis Skipped".

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Artifact Validation & Reproducibility Reporting (Priority: P3)

**Goal**: The system validates that the generated video artifacts meet the basic structural requirements (duration, resolution, format) and generates a report comparing the results against the paper's qualitative claims.

**Independent Test**: Can be tested by running a validation script that checks video metadata and generates a summary report.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Write test code in `tests/unit/test_validator.py` to verify `validator.py` checks file format, duration, and resolution
- [X] T029 [P] [US3] Write test code in `tests/integration/test_report_gen.py` to run `validator.py` on a dummy video and verify report generation

### Implementation for User Story 3

- [X] T030 [P] [US3] Create `src/domainshuttle/validator.py` to check file existence, format (`.mp4`), resolution, and duration (≥2s). **Implement Automated CLIP Proxy Fidelity Check**: Load CPU-optimized `ViT-B/32`, compute cosine similarity between reference image and first frame. Define validity as `fidelity_score > 0.5` (operationalizing SC-003 for this smoke test).
- [X] T031 [US3] Implement memory-swap logic in `src/domainshuttle/validator.py`: **Unload the video generation model completely** before loading the CLIP model to ensure the 7GB RAM limit is not exceeded when both models are active.
- [X] T032 [US3] Implement logic to compute motion score based on frame variance (standard deviation of pixel values across frames).
- [X] T033 [US3] Output `fidelity_score` and `motion_score` as normalized quantitative metrics in the validation result.
- [X] T034 [US3] Generate `reproduction_report.md` in `src/domainshuttle/report.py` including execution time, peak memory, and quantitative fidelity scores.
- [X] T035 [US3] Add logic to `src/domainshuttle/report.py` to explicitly attribute low fidelity: **IF** `fidelity_score < 0.5` (16-frame) **AND** `fidelity_score > 0.5` (8-frame), **THEN** attribute failure to "Hardware Constraint (16-frame limit)". **ELSE** attribute to "Model Incompatibility" or "Prompt Mismatch".
- [X] T036 [US3] Validate report output against Success Criteria (SC-001 to SC-004) in `src/domainshuttle/report.py`. **Replace** external methodology references (Methodology-218a9fb9, Methodology-019be52f) with inline comments or local documentation strings to ensure internal consistency.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T038 [P] Documentation updates: Update `quickstart.md` with CPU-only execution instructions
- [X] T039 Code cleanup: Remove any debug prints and ensure consistent logging across `inference.py` and `validator.py`
- [X] T040 Performance optimization: Ensure `torch.no_grad()` is used during inference to save memory
- [X] T041 [P] Additional unit tests: Cover edge cases for timeout and memory overflow in `tests/unit/`
- [X] T042 Run `quickstart.md` validation to ensure end-to-end flow works on a clean runner

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
Task: "Write test code for dependencies in tests/unit/test_dependencies.py"
Task: "Write test code for install script in tests/integration/test_install.py"

# Launch all models for User Story 1 together:
Task: "Create requirements.txt"
Task: "Implement install.py"
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