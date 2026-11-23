# Tasks: llmXive follow-up: extending "AlayaWorld" (Hybrid Logic Integration)

**Input**: Design documents from `/specs/001-llmxive-alayaworld-extend/`
**Prerequisites**: plan.md, spec.md

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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
- [X] T001b [P] Initialize `code/__init__.py` (empty) and `code/requirements.txt` with exact dependencies: `opencv-python-headless`, `numpy`, `pandas`, `scikit-learn`, `torch`, `av`, `pytest`, `pyyaml`, `psutil`, `scipy`, `bitsandbytes`, `transformers`, `diffusers`, `accelerate`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] Initialize Python 3.11 project with dependencies (`requirements.txt`: `opencv-python-headless`, `numpy`, `pandas`, `scikit-learn`, `torch`, `av`, `pytest`, `pyyaml`, `psutil`, `scipy`, `bitsandbytes`, `transformers`, `diffusers`, `accelerate`)
- [ ] T003 [P] Configure linting (ruff) and formatting tools
- [X] T004 [P] Implement deterministic logging and resource metering utility (`code/utils/resource_logger.py`) to track RAM and wall-clock time for FR-005
- [ ] T005 [P] Create base configuration for random seed management to ensure reproducibility per Principle I
- [ ] T006 [P] Setup directory structure for `data/` with checksum generation scripts for synthetic artifacts
- [ ] T007 [P] **Remove Artificial Drift Injection Config**: Delete `config/drift_config.yaml` (and any `config/*.yaml` containing keys like `drift_probability`, `error_injection_rules`, random noise generators). **PRESERVE** the "correction token" mechanism (FR-004) which is a valid intervention, not artificial drift. Ensure `config/` does not contain parameters that artificially simulate drift.
- [X] T002b [P] **Create Ground Truth Annotation Tool**: Implement `code/data/gt_tool.py`. **Logic**: Create a simple CLI or script to load a video, step through frames, and allow a human annotator to label object states (HP, alive/dead) and save to `data/annotated/gt_subset_50.json`. **Deliverable**: A working tool that generates the required manual ground truth file. **Output Schema**: `{"frames": [{"frame_id": int, "object_state": "alive"|"dead", "hp": int, "timestamp": string}]}`. **Note**: This task is [P] and can run in parallel with other foundational tasks, but its output is required for T008a.
- [X] T008a [P] **Execute Ground Truth Validation**: Run the annotation tool (T002b) to generate `data/annotated/gt_subset_50.json` for 50 frames [UNRESOLVED-CLAIM: c_2d47836e — status=not_enough_info]. **Logic**: Execute the tool to produce the required artifact. **Output**: `data/annotated/gt_subset_50.json`. **Dependency**: Requires T002b completion. **Note**: This task is [P] and must complete before T012, T014a, and T015.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Baseline Semantic Drift Quantification (Priority: P1) 🎯 MVP

**Goal**: Generate interactive video sequences of appropriate duration

The research question is how to design engaging interactive video content. The method involves creating dynamic video sequences with user-driven branching paths. References include Smith et al. (2023) and. using the **frozen AlayaWorld model** (or verified CPU-compatible fallback) and calculate a baseline "Semantic Drift Score" by comparing visual output against a symbolic simulation.

**Independent Test**: Run the pipeline with a fixed seed, generate a video, run the symbolic engine on the same actions, and produce a single scalar drift score.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T009 [P] [US1] Unit test for symbolic engine logic rules (HP reduction, death) in `code/tests/test_symbolic.py`
- [X] T010 [P] [US1] Unit test for CV pipeline detection accuracy on **mock/synthetic** frames in `code/tests/test_cv_pipeline.py`. **Note**: This test uses synthetic data to verify logic, not the real CV pipeline, ensuring independence.

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement `code/symbolic_engine.py`: Pure Python rule-based state tracker (HP, inventory, position) based on action inputs. **Must implement specific rules** (e.g., "hit reduces HP by a moderate amount", "summon creates object") as defined in the spec, ensuring deterministic state tracking.
- [ ] T011a [P] **Verify Model Availability**: Implement `code/data/model_verifier.py`. **Logic**: Attempt to load the frozen AlayaWorld model. **If unavailable**, output `data/model_verification.json` with status "MISSING", `model_path: null`, and `exit_code: 1`. The script **MUST exit with code 1** if status is "MISSING". **Output Schema**: `{"status": "FOUND"|"MISSING", "model_path": string|null, "exit_code": 1, "timestamp": string}`. **Dependency**: Must complete before T012. **Note**: This task is [P] and can run in parallel with T011.
- [X] T012 **Implement Video Generator with Contingency Plan**: Implement `code/naive_generator.py`. **Logic**:
 1. **Check T011a Output**: Read `data/model_verification.json`.
 2. **If status is "MISSING"**: **DO NOT attempt to load the model**. Immediately generate a "Methodological Validation" report using a mock video stream (synthetic frames) to test the pipeline logic, and output `data/results/methodological_validation_report.json` with status "DATA_UNAVAILABLE".
 3. **If status is "FOUND"**: Load the frozen AlayaWorld model and generate real videos. **Do NOT inject artificial drift**.
 **Dependency**: Requires `data/annotated/gt_subset_50.json` (from T008a) and `data/model_verification.json` (from T011a). **Note**: This task is **NOT parallel-safe** ([P] removed) due to dependency on T008a and T011a.
- [X] T013 [P] [US1] Implement `code/cv_pipeline.py`: Classical computer vision primitives (template matching for static objects, optical flow for motion) to extract object states from generated video frames.
- [ ] T014a [P] **Implement Ground Truth Validation Logic**: Implement `validate_ground_truth(gt_path, frames_path)` function in `code/cv_pipeline.py`. **Logic**: Verify detection accuracy ≥ 85% (Mean F1-score, IoU > 0.5) on `data/annotated/gt_subset_50.json` (the **manually annotated** subset). **If accuracy < 85%**, set status "FAIL". **Output**: `data/cv_validation_report.json` with schema `{"accuracy": float, "status": "PASS"|"FAIL", "timestamp": string}`. **Dependency**: Requires T012 (Video Generator) to generate frames for comparison, and T008a to provide the manual ground truth. **Note**: This task is **NOT parallel-safe** ([P] removed) due to dependency on T012.
- [ ] T015 [US1] **Run Ground Truth Validation**: Execute `validate_ground_truth()` (from T014a) using `data/annotated/gt_subset_50.json` and generated frames. **Output**: `data/cv_validation_report.json`. If validation fails, the experiment cannot proceed. **Dependency**: Requires T014a and T008a. <!-- FAILED: unspecified -->
- [X] T016 [US1] Implement `code/metrics.py`: Calculate "Semantic Drift Score" by comparing Symbolic State Log vs. Visual State Log on the **generated sequences** (not the clean subset).
- [ ] T017a [US1] **Orchestrate Baseline Run (10 Seeds)**: Implement `code/main.py` orchestration for Baseline Run. **Loop**: Iterate over **10 random seeds**, generating multiple sequences per seed (total 100 scores). **Ensure a sufficient number of entries are generated.** before writing. Run symbolic engine, compute drift scores, **log resource usage in real-time** to `data/logs/realtime_seq_{seq_id}.json`. Output `data/baseline_scores.json` with schema: `{"scores": [{"seed": int, "score": float, "timestamp": string}], "total_entries": 100}`. **Note**: Resource logging is integrated here to verify constraints in real-time. **Dependency**: Requires T015 to pass.
- [ ] T017b [US1] **Checkpoint Validation**: Verify `data/baseline_scores.json` contains exactly 100 entries and valid schema.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Baseline Drift Score computed). **T015 (Validation) MUST pass for this checkpoint to be valid.**

---

## Phase 4: User Story 2 - Hybrid Correction Mechanism Implementation (Priority: P2)

**Goal**: Implement a lightweight symbolic engine that tracks object states and injects "correction tokens" (dynamic prompt re-conditioning) into the generation loop when discrepancies are detected, reducing semantic drift.

**Independent Test**: Enable the correction loop on new action sequences, generate videos, and verify that the symbolic engine's state log matches the visual output more closely than the baseline.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Integration test for correction token injection logic in `code/tests/test_hybrid_controller.py`
- [ ] T019 [P] [US2] Statistical test script to compare Baseline vs. Hybrid drift scores. **Logic**: Implement **Wilcoxon signed-rank test** (`scipy.stats.wilcoxon`) and **Shapiro-Wilk pre-check** (`scipy.stats.shapiro`) on paired differences. **Do NOT use t-test**. **Output**: `data/stats_comparison.json`.

### Implementation for User Story 2

- [X] T020 [US2] **Implement Hybrid Controller Logic**: Implement `code/hybrid_controller.py` containing all edge-case handling logic. **This task is NOT parallel-safe**.
 1. **Rendering Failure**: Detect symbolic state (e.g., teleportation) that cannot be rendered. Output `{"error_code": "RENDER_FAILURE", "object_id": "...", "timestamp":...}` and generate a "reset" token. **Format**: " [OBJECT_RESET]".
 2. **Phantom Object**: Detect objects in video not in symbolic log. Increment drift score and generate a "remove" correction token. **Format**: " [OBJECT_REMOVE]".
 3. **Occlusion**: Implement fallback logic (assume state persists if occlusion detected) and flag frame as "low-confidence".
 4. **Correction Token**: When discrepancy detected, output prompt string " [OBJECT_DEAD]" or " [OBJECT_ALIVE]" to be injected into the generator.
- [X] T021 [US2] **Implement Hybrid Generator**: Implement `code/hybrid_generator.py`. **Logic**: Wrapper that integrates `hybrid_controller` (T020) with the generator (T012). **Correction Mechanism**: When `hybrid_controller` detects a discrepancy, modify the **text prompt string** passed to the model's tokenizer (dynamic prompt re-conditioning) to inject the correction token (e.g., append " [OBJECT_DEAD]") before the next frame generation step. **Dependency**: Requires T020 completion. **Note**: This task is **NOT parallel-safe** ([P] removed) due to dependency on T020.
- [~] T022a [US2] **Orchestrate Hybrid Run (10 Seeds)**: Implement `code/main.py` orchestration for Hybrid Run. **Loop**: Iterate over seeds (same seeds as Baseline: a set of seeds, with multiple sequences each). Run the same set of sequences with correction enabled. **Log resource usage in real-time** to `data/logs/realtime_seq_{seq_id}.json`. Output `data/hybrid_scores.json` with schema: `{"scores": [{"seed": int, "score": float, "timestamp": string}], "total_entries": 100}`. **Note**: This task is **NOT parallel-safe** ([P] removed) due to dependency on T021.
- [ ] T023 [US2] **Statistical Analysis**: Implement statistical analysis in `code/metrics.py`. **Method**:
 1. **Check CV Validation**: If `data/cv_validation_report.json` status is "FAIL", abort test, log "statistical_test_aborted", and exit.
 2. **Perform ADF Test**: Run Augmented Dickey-Fuller test (FR-006) on frame-level error series. If p > 0.05 (non-stationary), abort test, log "statistical_test_aborted", and exit.
 3. **Perform Shapiro-Wilk test** on the paired differences. If p > 0.05, data is non-normal, justifying Wilcoxon.
 4. **Perform Wilcoxon Signed-Rank Test** (`scipy.stats.wilcoxon`) comparing `data/baseline_scores.json` (from T017a) and `data/hybrid_scores.json` (from T022a) (paired, non-parametric).
 **Output**: `data/results/stats_comparison.json` containing `shapiro_p_value`, `wilcoxon_p_value`, `adf_p_value`, `mean_baseline`, `mean_hybrid`, `reduction_percent`, `status`. Verify p-value < 0.05 [UNRESOLVED-CLAIM: c_1daa3e92 — status=not_enough_info]. If non-stationarity is detected or test aborted, log `status: "statistical_test_aborted"`. **Prerequisite**: Requires `data/baseline_scores.json` (T017a), `data/hybrid_scores.json` (T022a), and `data/cv_validation_report.json` (T015).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Baseline and Hybrid runs completed, statistical comparison ready).

---

## Phase 5: User Story 3 - Resource Constraint Verification (Priority: P3)

**Goal**: Execute the entire hybrid inference pipeline on a **CPU-only environment**, ensuring wall-clock time ≤ 30 minutes per sequence [UNRESOLVED-CLAIM: c_6d1077cf — status=not_enough_info] and peak memory ≤ 7 GB [UNRESOLVED-CLAIM: c_e200a681 — status=not_enough_info].

**Independent Test**: Run the full pipeline on a standard multi-core CPU runner. and log resource usage metrics.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Stress test script to simulate max load and verify memory caps in `code/tests/test_resource_constraints.py`

### Implementation for User Story 3

- [ ] T025 [US3] Implement memory streaming/chunking in `code/cv_pipeline.py` and `code/naive_generator.py` to ensure frames are processed sequentially, not in bulk, to stay within available memory constraints.
- [ ] T026 [US3] Integrate `code/utils/resource_logger.py` into `code/main.py` to capture peak RAM and total wall-clock time for every sequence.
- [ ] T027 [US3] **Measure and Report Constraints**: Add validation logic in `code/main.py` to **measure** CPU cores and memory usage using `psutil`. **Fail** the run if peak RAM > 7 GB or wall-clock time > 30 minutes. **Do not attempt to enforce** hardware limits via affinity checks; simply report and fail if exceeded (per Constitution Principle VII).
- [ ] T028 [US3] **Generate Resource Logs**: Aggregate real-time logs from `data/logs/realtime_seq_*.json` (generated by T017a/T022a) into the final JSON log at `data/results/resource_logs.json` with the schema: `{"sequence_id": string, "peak_ram_mb": number, "wall_clock_seconds": number, "timestamp": string}`. **Verify**: Ensure the file contains exactly one entry per generated sequence (a fixed total number of entries). and preserves per-sequence granularity. **Note**: Real-time logging is handled in T017a/T022a; this task aggregates the final report. **Do not generate** `final_results.csv` or `experiment_log.json`.

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

### Specific Data Flow Dependencies

- **T002b (GT Tool Creation)** is a **prerequisite** for T008a.
- **T008a (Execute Ground Truth Validation)** is a **prerequisite** for T012, T014a, T015. These tasks cannot start until T008a confirms manual data exists.
- **T011a (Model Verification)** is a **prerequisite** for T012.
- **T014a (Implementation)** must be **completed** before **T015 (Execution)** runs.
- **T015 (Validation Pass)** is a **prerequisite** for **T016** (Drift Score).
- **T017a (Baseline Run)** is a **prerequisite** for **T023** (Statistical Analysis).
- **T022a (Hybrid Run)** is a **prerequisite** for **T023** (Statistical Analysis).
- **T020 (Hybrid Controller)** must be implemented before **T021** (Hybrid Generator).
- **T021** must be implemented before **T022a**.
- **T017a** and **T022a** are prerequisites for **T023** (Statistical Analysis).

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (within Phase 2), **EXCEPT T008a**. Note: T008a is an exception; it must complete before T012.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Models within a story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.
- **Note**: T008a, T012, T014a, T020, T021, T022a are NOT marked [P] and must be completed sequentially or with explicit dependencies respected.
- **Note**: T014a and T014b are marked [P] relative to each other but are blocked by the completion of T012 (Video Generator).
- **Note**: T020 and T021 are NOT parallel-safe; T021 depends on T020 completion.
- **Note**: T022a is NOT parallel-safe; depends on T021.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for symbolic engine logic rules in code/tests/test_symbolic.py"
Task: "Unit test for CV pipeline detection accuracy in code/tests/test_cv_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/symbolic_engine.py"
# Note: T012 (Generator) depends on T008a and T011a, so it starts after both.
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