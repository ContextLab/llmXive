# Tasks: Reproduce & Validate SANA-WM

**Input**: Design documents from `/specs/576-reproduce-validate-sana-wm/`
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
  - Delivered as a MVP increment
  
  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a Create project directory structure: `src/`, `tests/`, `output/`, `contracts/`, `scripts/`
- [X] T001b Initialize `scripts/init_project.sh` to set up Python 3.10+ virtual environment and install dependencies (`torch` CPU-only, `diffusers`, `transformers`, `opencv-python`, `numpy`, `accelerate`, `psutil`, `pytest`, `colmap`)
- [X] T002 [P] Configure linting and formatting tools (ruff/black)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `contracts/CameraPose.schema.yaml` defining the JSON schema for intrinsic/extrinsic matrices
- [X] T005 Implement `src/utils/pose_validator.py` to load `.npy` files, convert to JSON, and validate against `contracts/CameraPose.schema.yaml` (FR-006)
- [X] T006 [P] Create `src/utils/metrics_logger.py` to capture wall-clock time, frames generated, and peak RAM usage (FR-005)
- [X] T007 Create base `InferenceConfig` dataclass/schema matching plan requirements
- [X] T008 Configure error handling for OOM and CUDA fallback failures (Edge Cases)
- [X] T009 Setup environment configuration for `CUDA_VISIBLE_DEVICES=""` enforcement
- [X] T021 Implement `src/utils/pose_drift_estimator.py` using SfM (COLMAP or alternative) to calculate reprojection error. **Deliverable**: Script accepting input video and ground-truth pose `.npy`, outputting a JSON file `output/drift_metrics.json` containing `{"drift_percentage": float}`. (Prerequisite for US2 validation)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute Minimum Viable Inference Pipeline (Priority: P1) 🎯 MVP

**Goal**: Verify the SANA-WM pipeline initializes, loads weights on CPU, and generates a video artifact without crashing.

**Independent Test**: Execute `diffusion/longsana/pipeline/sana_inference_pipeline.py` with a sample prompt and verify `.mp4` output exists and exit code is 0.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for model loading in `tests/integration/test_sana_wm_inference.py` (Verify no CUDA errors)
- [X] T011 [P] [US1] Integration test for video generation in `tests/integration/test_sana_wm_inference.py` (Verify file creation)

### Implementation for User Story 1

- [X] T012 [US1] Implement CPU-only wrapper script `scripts/run_cpu_inference.py` to enforce `device="cpu"` and disable CUDA (FR-002)
- [X] T012b [US1] Extend `scripts/run_cpu_inference.py` to parse explicit CLI argument `--device cpu` and validate it, satisfying US-1 Acceptance Scenario 2 requirement for explicit user-controlled flags.
- [X] T013 [US1] Integrate `src/utils/metrics_logger.py` into the inference pipeline to log runtime data (FR-005)
- [X] T014 [US1] Execute inference with sample prompt "A cat walking on a leash" and short duration (4s)
- [X] T015 [US1] Verify output video file is generated in `output/videos/` with valid extension (`.mp4`/`.webm`) and file size > 0 (FR-004, SC-005)
- [X] T016 [US1] Add graceful OOM handling logic: Use `psutil` to poll memory; if usage > 7GB, raise `CustomOOMError` with message "OOM detected (RAM > 7GB). Suggest downsampling resolution or frame count." and exit with code 137 (Edge Case)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Validate 6-DoF Camera Control & Trajectory Adherence (Priority: P2)

**Goal**: Generate videos using specific 6-DoF pose inputs and validate adherence via Automated Pose Drift Error.

**Independent Test**: Run inference with `demo_0_pose.npy`, generate video, run SfM-based drift estimation, and verify drift error ≤ 5%.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T017 [P] [US2] Contract test for pose input validation in `tests/integration/test_sana_wm_inference.py`
- [X] T018 [P] [US2] Integration test for pose drift calculation in `tests/integration/test_sana_wm_inference.py`

### Implementation for User Story 2

- [X] T019 [US2] Integrate `src/utils/pose_validator.py` to explicitly run validation against `external/Sana/asset/sana_wm/demo_0_pose.npy` and `demo_0_intrinsics.npy` before generation. Assert schema compliance (FR-003, FR-006).
- [X] T020 [US2] Modify `scripts/run_cpu_inference.py` to accept `.npy` pose files as arguments
- [X] T022 [US2] Execute generation for 5 distinct trajectories from `external/Sana/asset/sana_wm/`
- [X] T023 [US2] Run `src/utils/pose_drift_estimator.py` (from T021) on generated videos to calculate reprojection error. Log results to `output/metrics.json` with key `pose_drift_error`. (FR-005, SC-002)
- [X] T024b [US2] Implement automated verification logic: Parse `output/metrics.json`, check if `pose_drift_error` ≤ 5%. Count successes. Assert that at least 4 out of 5 runs meet the threshold (SC-002). **Do not use visual inspection.**

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Benchmark Throughput & Resource Usage on CPU (Priority: P3)

**Goal**: Measure inference time and peak memory for a 4-second clip to establish feasibility baseline.

**Independent Test**: Run timed inference for 4s clip, record metrics, confirm time < 4h and RAM < 7GB.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Contract test for resource limits in `tests/integration/test_sana_wm_inference.py`

### Implementation for User Story 3

- [X] T026 [US3] Configure `scripts/run_cpu_inference.py` to run a standard 4-second, 720p (or lower if OOM) generation
- [X] T027 [US3] Execute timed run and capture `metrics.json` containing total time and peak RAM (FR-005)
- [X] T028 [US3] Verify execution time ≤ 4 hours (SC-004)
- [X] T029 [US3] Verify peak RAM < 7 GB (SC-003)
- [X] T030 [US3] Document "Minute-Scale Efficiency" claim as deferred in `research.md`. **Deliverable**: Append section `## Deferred Claims` with text: "The minute-scale efficiency claim is deferred due to hardware constraints (CPU-only runner). Only sub-minute feasibility was validated."

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Aggregate all `metrics.json` files into a final validation report
- [X] T032 Run `quickstart.md` validation to ensure documentation matches execution
- [X] T033 Code cleanup and refactoring of utility scripts
- [X] T034 [P] Final integration test run covering all 3 user stories
- [X] T035 [P] Final validation report: Explicitly assert SC-005 (Artifact Valid) by confirming all generated videos are non-empty and valid format, removing any "[deferred]" ambiguity from the final status.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires `pose_validator.py` (T005) and `pose_drift_estimator.py` (T021) from Phase 2
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Reuses `metrics_logger.py` from Phase 2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2), **EXCEPT T005 which depends on T004**
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for model loading in tests/integration/test_sana_wm_inference.py"
Task: "Integration test for video generation in tests/integration/test_sana_wm_inference.py"

# Launch all models for User Story 1 together:
Task: "Implement CPU-only wrapper script scripts/run_cpu_inference.py"
Task: "Integrate metrics_logger into the inference pipeline"
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