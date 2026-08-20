# Tasks: llmXive follow-up: extending "AlayaWorld" (Synthetic Validation)

**Input**: Design documents from `/specs/001-llmxive-alayaworld-extend/`
**Prerequisites**: plan.md, spec.md

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

- [ ] T001a [P] **Create Directory Structure**: Create `projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l/code/`, `projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l/data/`, `projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l/tests/`, `projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l/config/`, `projects/PROJ-1021-llmxive-follow-up-extending-alayaworld-l/docs/`. Create empty `__init__.py` files in `code/`, `tests/`, and `config/` directories.
- [ ] T001b [P] Initialize `code/__init__.py` and `code/requirements.txt`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Initialize Python 3.11 project with dependencies (`requirements.txt`: `opencv-python-headless`, `numpy`, `pandas`, `scikit-learn`, `torch`, `av`, `pytest`, `pyyaml`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 [P] Implement deterministic logging and resource metering utility (`code/utils/resource_logger.py`) to track RAM and wall-clock time for FR-005
- [ ] T005 [P] Create base configuration for random seed management to ensure reproducibility per Principle I
- [ ] T006 [P] Setup directory structure for `data/` with checksum generation scripts for synthetic artifacts
- [ ] T007 [P] Create `config/drift_params.yaml` with a default drift probability and error injection rules for the Mock Generator
- [ ] T008 [P] **Generate Ground Truth Subset**: Create `data/gt_subset_50.json` containing **≥ 50 frames** with manually annotated object states (HP, existence, position) for CV validation. **Crucially, this subset must be generated WITHOUT the injected drift errors (clean state)** to serve as the ground truth for validation. This file must be created before T012 runs.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Semantic Drift Quantification (Priority: P1) 🎯 MVP

**Goal**: Generate 60-second interactive video sequences using the "Mock AlayaWorld" (Naive Generator) and calculate a baseline "Semantic Drift Score" by comparing visual output against a symbolic simulation.

**Independent Test**: Run the pipeline with a fixed seed, generate a video, run the symbolic engine on the same actions, and produce a single scalar drift score.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for symbolic engine logic rules (HP reduction, death) in `code/tests/test_symbolic.py`
- [ ] T010 [P] [US1] Unit test for CV pipeline detection accuracy on known synthetic frames in `code/tests/test_cv_pipeline.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `code/symbolic_engine.py`: Pure Python rule-based state tracker (HP, inventory, position) based on action inputs.
- [ ] T012 [US1] Implement `code/naive_generator.py`: Mock video generator that produces frames based on symbolic state but intentionally injects generative errors (drift) with a **known probability ([deferred])** defined in `config/drift_params.yaml` to simulate real-world failure modes.
- [ ] T013 [US1] Implement `code/cv_pipeline.py`: Classical computer vision primitives (template matching for static objects, optical flow for motion) to extract object states from generated video frames.
- [ ] T014 [P] [US1] **Implement Ground Truth Validation Logic**: Implement logic in `code/cv_pipeline.py` to verify detection accuracy ≥ 85% on `data/gt_subset_50.json` (the clean subset). **If accuracy < 85%, the pipeline must halt and log "INCONCLUSIVE"**. This validates the CV pipeline on clean data, distinct from the drift measurement on dirty data.
- [ ] T015 [US1] **Run Ground Truth Validation**: Execute the validation logic (T014) on `data/gt_subset_50.json` to generate `data/cv_validation_report.json`. If validation fails, the experiment cannot proceed.
- [ ] T016 [US1] Implement `code/metrics.py`: Calculate "Semantic Drift Score" by comparing Symbolic State Log vs. Visual State Log on the **dirty generated sequences** (not the clean subset).
- [ ] T017 [US1] Implement `code/main.py` orchestration for Baseline Run: Generate multiple sequences, run symbolic engine, compute drift scores, log resource usage (RAM, Time). Output `data/baseline_scores.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Baseline Drift Score computed).

---

## Phase 4: User Story 2 - Hybrid Correction Mechanism Implementation (Priority: P2)

**Goal**: Implement a lightweight symbolic engine that tracks object states and injects "correction tokens" (dynamic prompt re-conditioning) into the generation loop when discrepancies are detected, reducing semantic drift.

**Independent Test**: Enable the correction loop on new action sequences, generate videos, and verify that the symbolic engine's state log matches the visual output more closely than the baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Integration test for correction token injection logic in `code/tests/test_hybrid_controller.py`
- [ ] T019 [P] [US2] Statistical test script to compare Baseline vs. Hybrid drift scores (paired t-test) in `code/tests/test_statistics.py`

### Implementation for User Story 2

- [ ] T020a [P] [US2] Implement `code/hybrid_controller.py` - **Rendering Failure Logic**: Detect when symbolic state (e.g., teleportation) cannot be rendered. Output `{"error_code": "RENDER_FAILURE", "object_id": "...", "timestamp": ...}` and generate a "reset/fade" correction token. **Must be implemented first.**
- [ ] T020b [P] [US2] Implement `code/hybrid_controller.py` - **Phantom Object Logic**: Detect objects in video not in symbolic log. Increment drift score and generate a "remove" correction token. **Depends on T020a.**
- [ ] T020c [P] [US2] Implement `code/hybrid_controller.py` - **Occlusion Logic**: Implement fallback logic (assume state persists if occlusion detected) and flag frame as "low-confidence" to avoid false-positive drift penalties. **Depends on T020b.**
- [ ] T021 [US2] Implement `code/hybrid_generator.py`: Wrapper that integrates `hybrid_controller` (T020a/b/c) with `naive_generator` (T012). **Must consume correction tokens from T020a/b/c** via a defined JSON interface: `{"type": "correction", "action": "reset|remove|fade", "object_id": "...", "confidence": float}`. The wrapper must inject these tokens as keyword arguments to the generation step in `naive_generator`.
- [ ] T022 [US2] Implement `code/main.py` orchestration for Hybrid Run: Run the same set of seeds/sequences as Baseline with correction enabled. Log resource usage. Output `data/hybrid_scores.json`.
- [ ] T023 [US2] Implement statistical analysis in `code/metrics.py`: Perform paired t-test comparing Baseline vs. Hybrid drift scores (FR-006). **Inputs**: `data/baseline_scores.json` (from T017), `data/hybrid_scores.json`. **Output**: `data/stats_comparison.json`. Verify p-value < 0.05.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Baseline and Hybrid runs completed, statistical comparison ready).

---

## Phase 5: User Story 3 - Resource Constraint Verification (Priority: P3)

**Goal**: Execute the entire hybrid inference pipeline on a **CPU-only environment**, ensuring wall-clock time ≤ 30 minutes per sequence and peak memory ≤ 7 GB.

**Independent Test**: Run the full pipeline on a standard 2-core CPU runner and log resource usage metrics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Stress test script to simulate max load and verify memory caps in `code/tests/test_resource_constraints.py`

### Implementation for User Story 3

- [ ] T025 [US3] Implement memory streaming/chunking in `code/cv_pipeline.py` and `code/naive_generator.py` to ensure frames are processed sequentially, not in bulk, to stay within available memory constraints..
- [ ] T026 [US3] Integrate `code/utils/resource_logger.py` into `code/main.py` to capture peak RAM and total wall-clock time for every sequence.
- [ ] T027 [US3] Add validation logic in `code/main.py` to **explicitly enforce the 2-core CPU constraint** (via CPU affinity checks) and fail the run if wall-clock time > 30 minutes or peak RAM > 7 GB (SC-002, SC-003).
- [ ] T028 [US3] Generate final JSON logs and CSV reports containing drift scores, p-values, and resource metrics. **Output files**: `data/final_results.csv`, `data/experiment_log.json`.

**Checkpoint**: All user stories should now be independently functional and resource constraints verified.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Documentation updates in `docs/` explaining the "Mock AlayaWorld" synthetic nature and limitations.
- [ ] T030 Code cleanup and refactoring of `code/main.py` to support both Baseline and Hybrid modes cleanly.
- [ ] T031 [P] Run quickstart.md validation to ensure reproducibility.

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1's symbolic engine and CV pipeline logic being stable.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Validates the resource usage of US1 and US2 implementations.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models (Symbolic/CV) before services (Generators)
- Services before orchestration (Main)
- Core implementation before integration
- Story complete before moving to next priority

### Specific Data Flow Dependencies

- **T008 (Generate Ground Truth)** is a **prerequisite** for T012, T014, and T015. These tasks cannot start until T008 is complete.
- **T017 (Baseline Run)** is a **prerequisite** for T023 (Statistical Analysis). T023 requires `data/baseline_scores.json` generated by T017.
- **T020a (Rendering Failure)** must be implemented before T020b (Phantom Object).
- **T020b (Phantom Object)** must be implemented before T020c (Occlusion).
- T020a, T020b, and T020c modify the same file (`code/hybrid_controller.py`) and must be executed sequentially.

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
Task: "Unit test for symbolic engine logic rules in code/tests/test_symbolic.py"
Task: "Unit test for CV pipeline detection accuracy in code/tests/test_cv_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/symbolic_engine.py"
Task: "Implement code/naive_generator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Baseline Drift Score computed).
5. Deploy/demo if ready.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Hybrid Correction)
4. Add User Story 3 → Test independently → Deploy/Demo (Resource Constraints)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Baseline)
   - Developer B: User Story 2 (Hybrid)
   - Developer C: User Story 3 (Resource Constraints)
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence