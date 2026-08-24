# Tasks: llmXive follow-up: extending "AlayaWorld" (Hybrid Logic Integration)

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

- [ ] T002 [P] Initialize Python 3.11 project with dependencies (`requirements.txt`: `opencv-python-headless`, `numpy`, `pandas`, `scikit-learn`, `torch`, `av`, `pytest`, `pyyaml`, `psutil`, `scipy`)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T004 [P] Implement deterministic logging and resource metering utility (`code/utils/resource_logger.py`) to track RAM and wall-clock time for FR-005
- [ ] T005 [P] Create base configuration for random seed management to ensure reproducibility per Principle I
- [ ] T006 [P] Setup directory structure for `data/` with checksum generation scripts for synthetic artifacts
- [ ] T007 [P] Create `config/drift_params.yaml` with a default `drift_probability: 0.20` and `error_injection_rules` for the generator fallbacks.
- [ ] T008a [P] **Check for Manual Ground Truth**: Create `code/data/gt_loader.py` to check for `data/annotated/gt_subset_50_manual.json`. If present, copy to `data/annotated/gt_subset_50.json`. If missing, trigger T008b.
- [ ] T008b [P] **Generate Synthetic Ground Truth Proxy**: If T008a finds no manual data, generate `data/annotated/gt_subset_50.json` using a deterministic synthetic generator that mimics the expected object states. **CRITICAL**: This file must be marked with a `source: synthetic_proxy` flag in its header to indicate it is not human-annotated, satisfying the requirement for a mechanism to accept manual data while allowing execution. This file must be created before T012 runs.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Semantic Drift Quantification (Priority: P1) 🎯 MVP

**Goal**: Generate 60-second interactive video sequences using the **frozen AlayaWorld model** (or verified CPU-compatible fallback) and calculate a baseline "Semantic Drift Score" by comparing visual output against a symbolic simulation.

**Independent Test**: Run the pipeline with a fixed seed, generate a video, run the symbolic engine on the same actions, and produce a single scalar drift score.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for symbolic engine logic rules (HP reduction, death) in `code/tests/test_symbolic.py`
- [ ] T010 [P] [US1] Unit test for CV pipeline detection accuracy on known synthetic frames in `code/tests/test_cv_pipeline.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement `code/symbolic_engine.py`: Pure Python rule-based state tracker (HP, inventory, position) based on action inputs.
- [ ] T012 [US1] **Implement Video Generator with Fallback**: Implement `code/naive_generator.py`. **Logic**: Attempt to load the frozen AlayaWorld model from `data/models/alayaworld.pth`. **IF missing or CPU-incompatible**, load `stable-video-diffusion-img2vid` (quantized to a lower-bit representation) from HuggingFace as the verified fallback. Generate frames based on symbolic state. Inject generative errors (drift) with probability `drift_probability` read from `config/drift_params.yaml`. **Dependency**: Requires `data/annotated/gt_subset_50.json` (from T008) to define the clean state baseline for drift injection. **Note**: This task is NOT parallel-safe ([P]) due to dependency on T008.
- [ ] T013 [P] [US1] Implement `code/cv_pipeline.py`: Classical computer vision primitives (template matching for static objects, optical flow for motion) to extract object states from generated video frames.
- [ ] T014a [US1] **Implement Ground Truth Validation Logic (Clean)**: Implement logic in `code/cv_pipeline.py` to verify detection accuracy ≥ 85% on `data/annotated/gt_subset_50.json` (the clean subset). **Metric**: Mean F1-score (IoU > 0.5) across all objects. **If accuracy < 85%**, the pipeline must halt and log "INCONCLUSIVE".
- [ ] T014b [US1] **Implement Ground Truth Validation Logic (Drifted)**: Implement logic in `code/cv_pipeline.py` to verify detection accuracy ≥ 85% on the **generated video frames** (the actual drift sequences). This validates the CV pipeline on the noisy data being measured, as required by FR-003.
- [ ] T015 [US1] **Run Ground Truth Validation**: Execute the validation logic (T014a and T014b) to generate `data/cv_validation_report.json`. If either validation fails, the experiment cannot proceed.
- [ ] T016 [US1] Implement `code/metrics.py`: Calculate "Semantic Drift Score" by comparing Symbolic State Log vs. Visual State Log on the **dirty generated sequences** (not the clean subset).
- [ ] T017a [US1] **Orchestrate Baseline Run (10 Seeds)**: Implement `code/main.py` orchestration for Baseline Run. **Loop**: Iterate over a set of random seeds. Generate multiple sequences per seed. Run symbolic engine, compute drift scores, log resource usage. Output `data/baseline_scores.json` (aggregated list of 100 scores).
- [ ] T017b [US1] **Checkpoint Validation**: Verify `data/baseline_scores.json` contains exactly 100 entries.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Baseline Drift Score computed). **T015 (Clean & Drifted Validation) MUST pass for this checkpoint to be valid.**

---

## Phase 4: User Story 2 - Hybrid Correction Mechanism Implementation (Priority: P2)

**Goal**: Implement a lightweight symbolic engine that tracks object states and injects "correction tokens" (dynamic prompt re-conditioning) into the generation loop when discrepancies are detected, reducing semantic drift.

**Independent Test**: Enable the correction loop on new action sequences, generate videos, and verify that the symbolic engine's state log matches the visual output more closely than the baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Integration test for correction token injection logic in `code/tests/test_hybrid_controller.py`
- [ ] T019 [P] [US2] Statistical test script to compare Baseline vs. Hybrid drift scores (paired t-test) in `code/tests/test_statistics.py`

### Implementation for User Story 2

- [ ] T020 [US2] **Implement Hybrid Controller Logic**: Implement `code/hybrid_controller.py` containing all edge-case handling logic. **This task is NOT parallel-safe**.
    1. **Rendering Failure**: Detect symbolic state (e.g., teleportation) that cannot be rendered. Output `{"error_code": "RENDER_FAILURE", "object_id": "...", "timestamp": ...}` and generate a "reset/fade" correction token.
    2. **Phantom Object**: Detect objects in video not in symbolic log. Increment drift score and generate a "remove" correction token.
    3. **Occlusion**: Implement fallback logic (assume state persists if occlusion detected) and flag frame as "low-confidence".
    *Note: This task consolidates the logic previously split into T020a/b/c to ensure sequential implementation and state consistency.*
- [ ] T021 [US2] **Implement Hybrid Generator**: Implement `code/hybrid_generator.py`. **Logic**: Wrapper that integrates `hybrid_controller` (T020) with the generator (T012). **Correction Mechanism**: When `hybrid_controller` detects a discrepancy, modify the **text prompt string** passed to the model's tokenizer (dynamic prompt re-conditioning) to inject the correction token (e.g., append " [OBJECT_DEAD]") before the next frame generation step.
- [ ] T022a [US2] **Orchestrate Hybrid Run (10 Seeds)**: Implement `code/main.py` orchestration for Hybrid Run. **Loop**: Iterate over seeds (same seeds as Baseline). Run the same set of sequences with correction enabled. Log resource usage. Output `data/hybrid_scores.json` (aggregated list of 100 scores).
- [ ] T023 [US2] **Statistical Analysis**: Implement statistical analysis in `code/metrics.py`. **Method**: Perform paired t-test using `scipy.stats.ttest_rel(baseline_scores, hybrid_scores)` where `baseline_scores` and `hybrid_scores` are lists of 100 floats. **Output**: `data/stats_comparison.json` containing `t_statistic`, `p_value`, `mean_baseline`, `mean_hybrid`, `reduction_percent`. Verify p-value < 0.05. **Prerequisite**: Requires `data/baseline_scores.json` (T017a) and `data/hybrid_scores.json` (T022a).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Baseline and Hybrid runs completed, statistical comparison ready).

---

## Phase 5: User Story 3 - Resource Constraint Verification (Priority: P3)

**Goal**: Execute the entire hybrid inference pipeline on a **CPU-only environment**, ensuring wall-clock time ≤ 30 minutes per sequence and peak memory ≤ 7 GB.

**Independent Test**: Run the full pipeline on a standard multi-core CPU runner. and log resource usage metrics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Stress test script to simulate max load and verify memory caps in `code/tests/test_resource_constraints.py`

### Implementation for User Story 3

- [ ] T025 [US3] Implement memory streaming/chunking in `code/cv_pipeline.py` and `code/naive_generator.py` to ensure frames are processed sequentially, not in bulk, to stay within available memory constraints.
- [ ] T026 [US3] Integrate `code/utils/resource_logger.py` into `code/main.py` to capture peak RAM and total wall-clock time for every sequence.
- [ ] T027 [US3] **Measure and Report Constraints**: Add validation logic in `code/main.py` to **measure** CPU cores and memory usage using `psutil`. **Fail** the run if peak RAM > 7 GB or wall-clock time > 30 minutes. **Do not attempt to enforce** hardware limits via affinity checks; simply report and fail if exceeded (per Constitution Principle VII).
- [ ] T028 [US3] Generate final JSON logs and CSV reports containing drift scores, p-values, and resource metrics. **Output files**: `data/final_results.csv`, `data/experiment_log.json`.

**Checkpoint**: All user stories should now be independently functional and resource constraints verified.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Documentation updates in `docs/` explaining the "AlayaWorld" fallback strategy and limitations.
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
- **US1 Specific**: T015 (Validation) is a hard gate for T016 (Drift Score).

### Specific Data Flow Dependencies

- **T008a/b (Ground Truth)** is a **prerequisite** for T012, T014a, T014b, and T015. These tasks cannot start until T008 is complete.
- **T014a/b (Implementation)** must be **completed** before **T015 (Execution)** runs.
- **T015 (Validation Pass)** is a **prerequisite** for **T016** (Drift Score).
- **T017a (Baseline Run)** is a **prerequisite** for **T023** (Statistical Analysis).
- **T022a (Hybrid Run)** is a **prerequisite** for **T023** (Statistical Analysis).
- **T020 (Hybrid Controller)** must be implemented before **T021** (Hybrid Generator).
- **T021** must be implemented before **T022a**.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (within Phase 2), **EXCEPT T008**. Note: T008 is an exception; it must complete before T012.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Models within a story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.
- **Note**: T020 is NOT marked [P] and must be completed sequentially before T021.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for symbolic engine logic rules in code/tests/test_symbolic.py"
Task: "Unit test for CV pipeline detection accuracy in code/tests/test_cv_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/symbolic_engine.py"
# Note: T012 (Generator) depends on T008, so it starts after T008.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Baseline Drift Score computed, T015 passed).
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