# Tasks: AnyFlow Reproduction & Validation

**Input**: Design documents from `/specs/001-anyflow-any-step-video-diffusion-model-w/`
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

## Phase 0: Research & Feasibility (Feasibility Gate)

**Purpose**: Verify model availability and CPU feasibility before implementation.

- [X] T000 [P] [Research] Perform feasibility gate check: Search HuggingFace/AnyFlow repo for a large-scale model variant, verify CPU-tractable metrics (SSIM/Flow) feasibility, and generate `research.md` with findings. **If 1.3B is not found, mark project as 'Blocked'**. This task MUST complete before any other task.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Create project structure per implementation plan: `mkdir -p src/anyflow tests/contract tests/integration tests/unit config data outputs`.
- [X] T002 [P] Initialize Python 3.10 project with CPU-only dependencies: Create `requirements.txt` containing `torch==2.1.0+cpu` (from `--extra-index-url), `diffusers==0.24.0`, `transformers==4.35.0`, `opencv-python==4.8.0`, `scikit-image==0.21.0`, `pytest==7.4.0`.
- [X] T003 [P] Configure linting (flake8) and formatting (black) tools in `pyproject.toml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Create `src/anyflow/__init__.py` to initialize the module.
- [X] T005 [P] Implement `src/anyflow/utils.py` with `check_artifact_validity()` (must return True/False, raise ValueError for invalid files; enforce: file size > 0 bytes, frame count >= 10) and `handle_oom()` logic (must log error and exit gracefully).
- [X] T006 [P] Create `config/cpu_config.yml` to override default CUDA settings and force CPU execution for `demo.py`.
- [X] T007 [P] Create `config/baseline.yml` with reference claims from `research.md` (T000) or a placeholder if T000 is not yet complete. Include example metrics like SSIM: 0.8, PSNR: dB.
- [X] T008 [P] Implement `src/anyflow/validation.py` skeleton with CPU-tractable metrics (SSIM, Optical Flow) using `scikit-image` and `opencv`.
- [X] T009 [P] Create `contracts/evaluation_report.schema.yaml` defining the JSON structure for the output report.
- [X] T010 [P] Create `contracts/dataset.schema.yaml` defining the input checkpoint and prompt schema.
- [X] T011 [P] [Research] Generate `data-model.md` documenting the input/output schemas and data flow.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Environment Initialization & Dependency Resolution (Priority: P1) 🎯 MVP

**Goal**: Initialize a clean Python environment, install dependencies, and verify imports work without CUDA errors.

**Independent Test**: Execute dependency installation script and attempt `import far.main` in a fresh Python interpreter, returning exit code 0.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Contract test for dependency installation in `tests/contract/test_dependencies.py`: Function `test_deps_install` must assert `subprocess.run(cmd).returncode == 0`.
- [X] T013 [P] [US1] Integration test for import success in `tests/integration/test_imports.py`: Function `test_import_farmain` must assert `import far.main` does not raise ImportError.

### Implementation for User Story 1

- [X] T014 [US1] Update `requirements.txt` to ensure `torch` installs the CPU-only wheel and pins versions to avoid CUDA conflicts (remove any CUDA-specific deps like `bitsandbytes` if not required for CPU).
- [X] T015 [P] [US1] Create `scripts/install_deps.sh` to run `pip install -r requirements.txt --no-cache-dir --no-deps`. **MUST run AFTER T014**.
- [X] T016 [US1] Implement `src/anyflow/inference.py` skeleton to safely import `far.main` and handle missing module errors gracefully. **This task depends on T005/T008 completion for utility functions**.
- [X] T017 [US1] Add error handling in `src/anyflow/inference.py` to detect and report `ImportError` or `ModuleNotFoundError`.
- [X] T018 [US1] Add logging in `src/anyflow/utils.py` to capture dependency resolution logs for CI debugging.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Minimal Inference Execution (Priority: P1)

**Goal**: Run `demo.py` with a small model variant (1.3B) on CPU to generate a valid `.mp4` video artifact.

**Independent Test**: Execute demo script with dummy prompt, verify a non-empty `.mp4` is written, and confirm no CUDA memory allocation occurs.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for video artifact validity in `tests/contract/test_artifact_validity.py`: Function `test_artifact_valid` must assert `video_frames >= 10 and file_size > 0`.
- [X] T020 [P] [US2] Integration test for minimal inference run in `tests/integration/test_inference_run.py`: Function `test_inference_run` must assert `video_file_exists()`.

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement `src/anyflow/inference.py` `run_inference()` function using `config/cpu_config.yml` to force CPU mode. **Must check feasibility gate (T000) before proceeding**. **This task depends on T005/T008 completion**.
- [X] T022 [US2] Implement `src/anyflow/inference.py` logic to download the 1.3B model checkpoint from URL found in `research.md` (T000) or a placeholder URL if unavailable. **If T000 reports model unavailable, exit gracefully**.
- [X] T023 [US2] Modify `demo.py` invocation in `src/anyflow/inference.py` to use `--steps 4`, `--model 1.3B`, and `--prompt "a cat"` (wrap external `demo.py` via subprocess).
- [X] T024 [US2] Integrate `src/anyflow/utils.py` `check_artifact_validity()` to ensure the output video is >1 second and >10 frames.
- [X] T025 [US2] Add OOM handling in `src/anyflow/inference.py` to catch `RuntimeError` (OOM) and exit with a clear "Out of Memory" message.
- [X] T026 [US2] Ensure `src/anyflow/inference.py` explicitly sets `device="cpu"` and disables CUDA device allocation.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Quantitative Validation Report Generation (Priority: P2)

**Goal**: Execute evaluation pipeline on generated artifacts and produce a JSON report with CPU-tractable metrics (SSIM, Optical Flow).

**Independent Test**: Run evaluation script on artifacts from US-02 and verify a `results.json` file is generated containing at least one metric.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test for report structure in `tests/contract/test_report_structure.py`: Function `test_report_structure` must assert `'ssim_score' in results`.
- [X] T028 [P] [US3] Integration test for evaluation pipeline in `tests/integration/test_evaluation.py`: Function `test_evaluation_run` must assert `results_file_exists()`.

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `src/anyflow/validation.py` `compute_ssim()` using `scikit-image` for temporal consistency (Input: two video frames, Output: scalar SSIM, window size=5). **This task extends T008**.
- [X] T030 [US3] Implement `src/anyflow/validation.py` `compute_optical_flow()` using `opencv` for motion activity. **This task extends T008**.
- [X] T031 [US3] Create `src/anyflow/eval_pipeline.py` to orchestrate: load video, run SSIM, run Flow, compare to baseline, write JSON. **This task depends on T029/T030**.
- [X] T032 [US3] Implement `src/anyflow/eval_pipeline.py` to generate `results.json` conforming strictly to `contracts/evaluation_report.schema.yaml` (created in T009). **If the schema file is missing, log an error and exit gracefully**.
- [X] T033 [US3] Add logic in `src/anyflow/eval_pipeline.py` to flag the artifact as "Invalid" if SSIM/Flow metrics are NaN or infinite.
- [X] T034 [US3] Add logging in `src/anyflow/eval_pipeline.py` to record metric values and comparison results.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Execution & Reporting (Final Deliverable)

**Purpose**: Execute the full pipeline and generate final artifacts as a distinct deliverable.

- [X] T035 [P] Run `scripts/install_deps.sh` (T015) to ensure environment is clean.
- [X] T036 [P] Execute `python src/anyflow/inference.py` to generate the video artifact (T021-T026).
- [X] T037 [P] Execute `python src/anyflow/eval_pipeline.py` to generate `results.json` and `outputs/*.mp4` (T031-T034).
- [X] T038 [P] Aggregate final report: Verify `results.json` contains valid metrics and `outputs/*.mp4` exists.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T039 [P] Documentation updates in `README.md` and `docs/`: Add "CPU-Only Constraints" section describing the 7GB RAM limit and 6h runtime.
- [X] T040 Code cleanup and refactoring in `src/anyflow/` to remove redundant imports.
- [X] T041 Performance optimization: Ensure `torch` tensors are moved to CPU explicitly to avoid implicit CUDA allocation.
- [X] T042 [P] Additional unit tests in `tests/unit/test_utils.py` for edge cases (empty frames, OOM).
- [X] T043 Run `quickstart.md` validation to ensure the full pipeline runs end-to-end on CI.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Research)**: No dependencies - MUST run first.
- **Setup (Phase 1)**: Depends on Phase 0 (if feasible).
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
- **Execution (Phase 6)**: Depends on all user stories.
- **Polish (Phase 7)**: Depends on Execution.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2).
- **User Story 2 (P1)**: Depends on US1 for environment setup.
- **User Story 3 (P2)**: Depends on US2 for generated artifacts.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Models before services.
- Services before endpoints.
- Core implementation before integration.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (after Phase 0).
- All Foundational tasks marked [P] can run in parallel (within Phase 2).
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for dependency installation in tests/contract/test_dependencies.py"
Task: "Integration test for import success in tests/integration/test_imports.py"

# Launch all models for User Story 1 together:
Task: "Create scripts/install_deps.sh"
Task: "Update requirements.txt"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Research (Feasibility Gate)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (after Phase 0)
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