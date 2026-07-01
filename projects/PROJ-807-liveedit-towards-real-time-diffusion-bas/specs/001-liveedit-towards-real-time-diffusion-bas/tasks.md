# Tasks: LiveEdit: Towards Real-Time Diffusion-Based Streaming Video Editing

**Input**: Design documents from `/specs/807-liveedit-real-time-diffusion-bas/`
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

- [X] T001 Create project structure per implementation plan (`src/liveedit`, `tests/`, `results/`)
- [X] T002 Initialize Python 3.10 project with `requirements.txt` (torch-cpu, diffusers, transformers, opencv-python, pandas, pytest)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `src/liveedit/__init__.py` and package structure
- [X] T005 [P] Implement `src/liveedit/validators.py` for missing mask (Abort with specific error, NO no-op per Plan/Constitution) and corrupted weight detection (FR-005, Edge Cases)
- [X] T006 [P] Create `contracts/benchmark_result.schema.json` defining FPS, relative speedup, noise floor, flicker score
- [X] T007 Create `contracts/output_manifest.schema.json` defining video/metric output paths
- [X] T008 Configure error handling and logging infrastructure in `src/liveedit/logger.py`
- [X] T009 Setup environment configuration management for chunk size and sample paths

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Validate End-to-End Execution (Priority: P1) 🎯 MVP

**Goal**: Execute `author-kit` on CPU with chunked processing, ensuring no OOM and valid output artifacts.

**Independent Test**: Run `src/liveedit/runner.py` with sample input; verify exit code 0 and existence of output video/metrics within 6h.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation. These run SEQUENTIALLY after implementation.**

- [X] T010 [US1] Contract test for runner output schema in `tests/contract/test_runner_output.py`
- [X] T011 [US1] Integration test for chunked processing memory limit in `tests/integration/test_chunked_memory.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `src/liveedit/runner.py` with CPU-only configuration injection, ChunkIterator logic, and author-kit inference call (return dict: video_path, fps). **MUST use real sample data; no mocks.**
- [X] T013a [US1] Implement `ChunkIterator` class in `src/liveedit/runner.py` for sequential frame loading (Part of T013 logic)
- [X] T013b [US1] Implement `ChunkBoundaryHandler` in `src/liveedit/runner.py` for seam artifact prevention (Part of T013 logic)
- [X] T013c [US1] Implement `MemoryCleanup` logic in `src/liveedit/runner.py` for garbage collection between chunks (Part of T013 logic)
- [X] T015 [US1] Implement artifact saving logic to `results/videos/` and `results/metrics/` (FR-002)
- [X] T016 [US1] Add validation and error handling: **Abort (no no-op)** for missing masks, **Abort** for corrupted weights (Edge Cases, Plan Override)
- [X] T017 [US1] Add logging for execution flow and chunk boundaries

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Reproduce Quantitative Benchmarks (Priority: P2)

**Goal**: Calculate relative metrics (Speedup, Stability) and noise floor on CPU, avoiding invalid absolute comparisons.

**Independent Test**: Execute `src/liveedit/benchmark.py`; verify JSON output contains relative speedup ≥ 1.0 and noise floor calibration.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for benchmark JSON schema in `tests/contract/test_benchmark_schema.py`
- [X] T019 [P] [US2] Integration test for relative metric calculation logic in `tests/integration/test_metrics.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `src/liveedit/benchmark.py` with stubs: `class BenchmarkResult`, `def calc_fps()`, `def calc_noise_floor()`
- [X] T021 [US2] Implement FPS calculation for both Distilled and Baseline runs in `src/liveedit/benchmark.py`
- [X] T022 [US2] Implement Relative Speedup calculation (Distilled FPS / Baseline FPS) in `src/liveedit/benchmark.py`; **Log absolute metrics and Flag SC-002 as BLOCKED in final report**
- [X] T023 [US2] Implement Background Stability metric (Distilled vs Baseline PSNR/SSIM) in `src/liveedit/benchmark.py`; **Log absolute metrics and Flag SC-003 as BLOCKED in final report**
- [X] T024a [US2] Select static video sample for noise floor calibration in `src/liveedit/benchmark.py`
- [X] T024b [US2] Process sample to generate noise map in `src/liveedit/benchmark.py`
- [X] T024c [US2] Calculate variance threshold (Noise Floor) in `src/liveedit/benchmark.py`
- [X] T025 [US2] Implement Chunk Boundary Score calculation in `src/liveedit/benchmark.py`; **Log data for T040 report**
- [X] T026 [US2] Integrate benchmark runner with `runner.py`: **Update runner.py (Phase 3 artifact) to call benchmark.py functions** for post-processing (FR-003)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Validate Qualitative Artifacts (Priority: P3)

**Goal**: Verify background stability and lack of flickering via automated frame-difference analysis.

**Independent Test**: Generate video output; run frame-diff tool; verify flicker score < 3x noise floor.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test for flicker score output in `tests/contract/test_flicker_score.py`
- [X] T028 [P] [US3] Integration test for frame-difference stability in `tests/integration/test_stability.py`

### Implementation for User Story 3

- [X] T029a [P] [US3] Implement `src/liveedit/utils/flicker_utils.py` with `def calc_flicker_score()` and `def calc_noise_floor()` utilities (Decoupled from benchmark.py)
- [X] T029b [P] [US3] Implement frame-difference utility in `src/liveedit/utils/frame_diff.py`
- [X] T030 [US3] Implement Flicker Score calculation (Output variance / Noise Floor) in `src/liveedit/benchmark.py` using utilities from T029a
- [X] T031 [US3] Integrate flicker verification into `src/liveedit/runner.py` post-processing (Call `flicker_utils` from T029a)
- [X] T032 [US3] Generate visual debug artifacts (difference maps) in `results/debug/` for manual inspection
- [X] T033 [US3] Validate background stability against mask regions (FR-004): **Calculate flicker_score; assert flicker_score < 3 * noise_floor**

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034 [P] Documentation updates in `docs/` and `README.md`
- [X] T035 Code cleanup and refactoring of `src/liveedit`
- [X] T036 Performance optimization for chunk size tuning
- [X] T037 [P] Additional unit tests in `tests/unit/`
- [X] T038 Run `quickstart.md` validation
- [X] T039 Finalize report on Spec Conflicts (SC-002, SC-003) as "BLOCKED" with relative metric justification
- [X] T040 [P] **Report Chunk Boundary Score as FAIL (Spec Gap)** in final report (Data from T025)

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (videos) for benchmarking
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 output (videos) for frame analysis

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
Task: "Contract test for runner output schema in tests/contract/test_runner_output.py"
Task: "Integration test for chunked processing memory limit in tests/integration/test_chunked_memory.py"

# Launch all models for User Story 1 together:
Task: "Implement src/liveedit/runner.py with CPU-only configuration injection"
Task: "Implement chunked video loading logic in src/liveedit/runner.py to handle GB RAM limit"
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
- **Critical Note on Metrics**: This project explicitly implements **Relative Metrics** (Distilled vs. Baseline on CPU) due to scientific invalidity of comparing CPU FPS to likely GPU paper claims. SC-002 and SC-003 are flagged as "BLOCKED" in the plan; tasks focus on the relative implementation.
- **Task Execution Order**: T013a → T013b → T013c (Sequential within runner.py); T024a → T024b → T024c (Sequential); T010/T011 run after T012/T013.