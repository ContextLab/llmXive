# Tasks: llmXive Follow-up: Extending "Enhancing Train-Free Infinite-Frame Generation for Consistent Long Vid"

**Input**: Design documents from `/specs/001-llmxive-flow-correction/`
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

- [ ] T001a [US0] Create `projects/PROJ-874-llmxive-follow-up-extending-enhancing-tr/` directory structure: `code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/`, `docs/`, `contracts/`. **Deliverable**: Verify directories exist via `ls`. Execute `ls -R` to confirm structure. <!-- ATOMIZE: resolved -->
- [X] T001b [US0] Create `projects/PROJ-874-llmxive-follow-up-extending-enhancing-tr/data/raw/`, `data/processed/`, `data/results/` directories
- [X] T001c [US0] Create `projects/PROJ-874-llmxive-follow-up-extending-enhancing-tr/tests/contract/`, `tests/integration/`, `tests/unit/` directories

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004a [US0] Implement `code/config.py` with seed management, dataset paths, and state update logic
- [X] T004b [US0] Create `.github/workflows/ci.yml` defining the CPU and constrained RAM limits.
- [ ] T003 [P] [US0] Configure linting (ruff/flake8) and formatting (black) tools.
- [ ] T005 [P] [US0] Create `contracts/dataset.schema.yaml` and `contracts/metrics.schema.yaml`. **Implement md5/sha256 checksumming logic in `code/download.py` and verification in `code/config.py`.**
- [X] T006 [P] [US0] Setup `code/utils/video.py` for frame extraction and basic video I/O
- [X] T008 [P] [US0] Configure error handling and logging infrastructure in `code/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducible Baseline Execution (Priority: P1) 🎯 MVP

**Goal**: Execute MIGA pipeline in two modes (Full Self-Reflection, Naive) on NarrLV/VBench data to establish baselines.

**Independent Test**: Running `code/generate.py --mode baseline-full` and `--mode baseline-naive` produces video files and logs wall-clock time without crashing on CPU. **Also verifies that T017 (Pilot Study) runs successfully and produces `data/pilot_variance.json`.**

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Contract test for data download in `tests/contract/test_download.py`
- [X] T011 [P] [US1] Integration test for generation pipeline in `tests/integration/test_generation.py`

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/download.py` to fetch NarrLV/VBench datasets via HuggingFace `datasets` library. **Must include pre-flight validation to check for existence of ALL required dataset files (NarrLV and VBench) BEFORE generation begins. If missing, ABORT with clear error listing missing files (FR-001). Implement md5/sha256 checksumming and verification.** (FR-001)
- [X] T012a [US1] Implement `code/download.py` pre-flight validation function to check for existence of *all* required dataset files (NarrLV and VBench) *before* generation begins, aborting with a clear error if any are missing (FR-001)
- [ ] T013 [US1] Implement `code/generate.py` with `--mode baseline-full` (self-reflection enabled) and `--mode baseline-naive` (self-reflection disabled). **Must include logic to record total end-to-end wall-clock time per video (including data loading and model initialization overhead) to `results/generation_times.log` with key 'total_wall_clock_time' in ISO8601 format (FR-002, Constitution VI).** (FR-002)
- [ ] T014a [US1] Implement `code/generate.py` logging logic for **isolated inference time**. **Must record 'video_id', 'mode', and 'inference_time_seconds' (seconds) as JSON lines to `results/generation_times.log`. Use `time.time()` before and after the actual generation step only, excluding data loading and model initialization.** (FR-002, Constitution VI)
- [ ] T014b [US1] Verify wall-clock time logging format. **Run `code/generate.py` with a dummy prompt. Verify `results/generation_times.log` exists and contains valid JSON lines with keys 'video_id', 'mode', 'total_wall_clock_time', and 'inference_time_seconds'.**
- [X] T017 [US1] Implement and run a pilot study script (`code/pilot_study.py`) on N=5 samples to calculate empirical variance for power analysis, saving results to `data/pilot_variance.json`. **Output JSON MUST contain keys: 'mean', 'std', 'n_samples', 'metric_name'** (SC-006 prerequisite)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Deterministic Flow-Based Correction (Priority: P2)

**Goal**: Apply RAFT-Small (CPU) optical flow and non-differentiable warping/smoothing to naive baseline outputs.

**Independent Test**: Running `code/correct.py` on naive videos produces warped videos and flow fields within 6 hours on 2-core CPU.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for flow field schema in `tests/contract/test_flow_schema.py`
- [X] T019 [P] [US2] Integration test for flow correction pipeline in `tests/integration/test_flow_correction.py`

### Implementation for User Story 2

- [X] T020a [US2] Implement `code/utils/flow_benchmark.py` to verify RAFT-Small FP16 feasibility on CPU. **Must run a small benchmark (1 frame) and report success/failure. If FP16 fails (OOM), report fallback to FP32.**
- [X] T020 [P] [US2] Implement `code/utils/flow.py` to load RAFT-Small model. **Depends on T020a completion. Use FP16 if T020a succeeded, otherwise FP32.** (FR-003)
- [X] T021 [US2] Implement `code/correct.py` to compute optical flow fields between consecutive frames of naive baseline videos. **Depends on T013 completion. Must include step to verify existence of naive baseline videos (T013 output) and abort with error if missing** (FR-003, FR-001)
- [ ] T022 [US2] Implement non-differentiable warping and smoothing logic using flow fields to generate Condition C outputs. **Algorithm: `cv2.remap` with bilinear interpolation. Input: `data/processed/flow_fields/`. Output: `data/processed/corrected_videos/`. Must include step to verify existence of flow fields (T021 output) and abort with error if missing** (FR-004)
- [ ] T023 [US2] Implement fallback logic for failed flow estimation (e.g., extreme motion blur) using **temporal nearest-neighbor interpolation of flow vectors**. **Algorithm: If flow estimation fails for a frame (e.g., NaNs or extreme values), locate the nearest valid flow vector (u, v) from adjacent frames (t-1 or t+1) based on spatial proximity. Copy the (u, v) vector components directly from the neighbor frame to the failed frame. Do NOT average or interpolate between vectors. Trigger: If flow estimation fails for a frame. Log format: JSON with 'video_id', 'frame_idx', 'fallback_reason'. Verify fallback triggers only on specific failure modes (e.g., blur detection).** (FR-004)
- [ ] T024 [US2] Add detection and logging for frames with invalid pixel artifacts (tearing) due to severe 3D drift, flagging them for manual review instead of silently corrupting video. **Detection: Check for pixel value > 255 or < 0 after warping. Log format: JSON with 'video_id', 'frame_idx', 'artifact_type'. Output file: `results/invalid_frames.log`.** (FR-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Comparative Analysis and 3D Drift Limitation Mapping (Priority: P3)

**Goal**: Compute metrics (VBench, FVD, Object Permanence), perform statistical testing, and identify failure cases.

**Independent Test**: Running `code/evaluate.py` and `code/analyze.py` generates a CSV report and statistical summary with p-values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T037 [P] [US3] Contract test for metrics schema in `tests/contract/test_metrics_schema.py` (Renamed from T024 to resolve ID collision)
- [X] T025 [P] [US3] Integration test for statistical analysis in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [~] T030a [US3] Implement `code/analyze.py` power analysis function using `statsmodels.stats.power` based on pilot variance from T017. **Must calculate power for N=50. If power < 0.8, the report MUST explicitly state the study is underpowered. MUST generate `results/power_analysis_report.md` documenting the finding (even if failure) and ABORT subsequent statistical tests (T027/T028) or flag them as invalid.** (SC-006 prerequisite)
- [X] T027 [US3] Implement `code/analyze.py` to perform Shapiro-Wilk test for normality on metric differences. **Logic: If p < 0.05, reject normality and default to Wilcoxon. If p >= 0.05, assume normality and use paired t-test.** (FR-006)
- [X] T028a [US3] Implement `code/analyze.py` function `check_normality()` to run Shapiro-Wilk and return dict with 'p_value', 'is_normal'. **Signature: `check_normality(differences) -> dict`**. (FR-006)
- [ ] T028b [US3] Implement `code/analyze.py` function `run_significance_test()` to perform Wilcoxon signed-rank if normality rejected (p<0.05), else paired t-test. **Logic: Call `check_normality`. If `is_normal` is False, use Wilcoxon. Return dict with 'test_type', 'p_value', 'statistic'.** (FR-006)
- [ ] T029 [US3] Implement failure case identification logic: flag videos where object permanence drops ≥5% or VBench score drops ≥0.1 compared to naive baseline. **Output must be written to `results/failure_cases.json`. MUST log explicit note: "These are 2D perceptual proxies and do not guarantee 3D geometric correctness" (FR-007)**
- [ ] T031 [US3] Generate CSV report containing all metrics and a final statistical summary with p-values. **Depends on successful completion of T030a. File: `results/metrics.csv`. Delimiter: ','. Columns: 'video_id', 'condition', 'vbench_score', 'fvd', 'object_permanence', 'p_value', 'test_type', 'power_sufficient' (boolean). Logic: Derive 'power_sufficient' from T030a output (power >= 0.8). Verify this derivation. If T aborts, this task must NOT run.** (SC-006)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032a [P] [US0] Update `quickstart.md` with new CLI flags and dataset requirements. **Also verify `state.yaml` is updated with new artifact hashes.**
- [X] T032b [P] [US0] Generate `docs/paper/methodology.md` draft based on implementation
- [ ] T033b [P] [US0] Implement `--profile_memory` flag in `code/generate.py` and associated logging logic. **Must use `memory_profiler` to track RSS during execution and log peak usage to `results/memory_profile.log`.**
- [ ] T033 [P] [US0] Code cleanup and refactoring to ensure memory footprint < 6GB peak. **Tool: `memory_profiler`. Command: `code/generate.py --profile_memory`. Verification: Parse `results/memory_profile.log` and assert max RSS < 6GB. Depends on T033b.** (Constitution VI)
- [ ] T034a [P] [US0] Measure and log RAFT-Small inference time per frame on CPU. **Metric: 'mean_inference_time_per_frame'. File: `results/raft_timing.log`. Format: JSON line with 'video_id', 'mean_time'.** (SC-005, Constitution VI)
- [ ] T035 [P] [US0] Additional unit tests for metric calculation logic in `tests/unit/`
- [ ] T036 [P] [US0] Run `quickstart.md` validation to ensure end-to-end reproducibility. **Script: `validate_repro.py`. Expected exit code: 0. Check: All artifacts exist and checksums match.**

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
- **User Story 2 (P2)**: Depends on User Story 1 (needs naive baseline videos from T013) - Must run after T013 completes. T020 depends on T004a (config) and T020a (benchmark). T021 explicitly depends on T013 completion.
- **User Story 3 (P3)**: Depends on User Story 1 (T013), User Story 2 (T022), AND Pilot Study (T017) - Must run after T013, T022, and T017 complete. **T030a (Power Analysis) is a hard gate for T027/T028. T031 depends on successful completion of T030a.**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
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
Task: "Contract test for data download in tests/contract/test_download.py"
Task: "Integration test for generation pipeline in tests/integration/test_generation.py"

# Launch all models for User Story 1 together:
Task: "Implement code/download.py to fetch NarrLV/VBench datasets"
Task: "Implement code/generate.py with baseline modes"
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
 - Developer B: User Story 2 (after US1 data is ready)
 - Developer C: User Story 3 (after US1 & US2 data is ready)
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
- **Critical Constraint**: All tasks must run on free CPU-only CI (limited cores, sufficient RAM, no GPU). No 8-bit/4-bit quantization or CUDA dependencies.
- **Note on T007**: Task T007 was removed. T020 is the sole creator of `code/utils/flow.py`.
- **Note on T009**: Task T009 was removed. Requirements merged into T004.
- **Note on T024**: The duplicate T024 in Phase 5 was renamed to T037.
- **Note on T020**: T020 depends on T020a completion. It is marked [P] as it can be scheduled once T020a artifact is ready.
- **Note on T030a**: T030a is a prerequisite for T027/T028. If power < 0.8, T027/T028 must be aborted or flagged. T031 depends on T030a success.
- **Note on T015/T016**: Tasks T015 and T016 have been removed. Their logic (validation and error handling) has been merged directly into T012 and T013.
- **Note on T003**: Removed dependency on T004b; linting config is independent.
- **Note on T033/T033a**: T033b implements the `--profile_memory` flag; T033 verifies the memory constraint.