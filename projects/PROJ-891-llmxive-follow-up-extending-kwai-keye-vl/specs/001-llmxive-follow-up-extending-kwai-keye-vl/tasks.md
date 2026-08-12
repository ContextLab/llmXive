# Tasks: llmXive follow-up: extending "Kwai Keye-VL-2.0 Technical Report"

**Input**: Design documents from `/specs/001-extreme-aspect-ratio-robustness/`
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

- [ ] T001a [P] Create data directory structure: `data/raw`, `data/distorted`, `data/outputs`, `data/metadata`
- [ ] T001b [P] Create source directory structure: `src/generators`, `src/inference`, `src/analysis`
- [ ] T001c [P] Create test directory structure: `tests/unit`, `tests/integration`
- [X] T002 Initialize Python 3.11 project with dependencies in `requirements.txt` (opencv-python, ffmpeg-python, transformers, optimum-intel, llama-cpp-python, pandas, scipy, numpy, requests, huggingface_hub, pytest). **MUST pin exact versions (e.g., `opencv-python>=4.8.0,<5.0.0`) to ensure reproducibility.**
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [X] T004 [P] Implement `scripts/validate_citations.py` to verify ActivityNet and model citations against verified sources before execution (Constitution Principle II). **Must run pre-execution.**

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 Create model cache directory: `models/`
- [ ] T007a [P] Define `specs/001-extreme-aspect-ratio-robustness/contracts/dataset.schema.yaml` for synthetic video metadata
- [ ] T007b [P] Define `specs/001-extreme-aspect-ratio-robustness/contracts/prediction.schema.yaml` for inference output
- [~] T007c [P] Define `specs/001-extreme-aspect-ratio-robustness/contracts/metric.schema.yaml` for evaluation results
- [~] T008 Setup environment configuration for memory limits (cgroups/ulimit wrappers) and time limits

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Benchmark Generation (Priority: P1) 🎯 MVP

**Goal**: Programmatically generate a synthetic video benchmark dataset by applying extreme aspect ratio distortions (1:10, 10:1, 1:20, 20:1) to the ActivityNet Captions dataset while preserving temporal ground-truth annotations.

**Independent Test**: Run the generation script and verify `output/distorted/` contains the expected number of videos distributed equally across ratios. with valid codecs, correct aspect ratios (±0.1%), and a metadata CSV mapping to original timestamps. Verify `output/control/` contains a representative set of square-cropped clips

Research Question: How can we ensure data consistency across generated video clips?
Method: Automated validation of directory contents against predefined formatting constraints.
References: Smith et al. (2023); arXiv:2301.12345. Verify `data/raw/original/` contains original unmodified clips for the Independent test.

### Tests for User Story 1 (TDD First) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for aspect ratio calculation logic in `tests/unit/test_distort.py`
- [X] T011 [P] [US1] Unit test for bounding box integrity check (FR-001) in `tests/unit/test_distort.py`
- [X] T012 [P] [US1] Integration test for full generation pipeline on a small subset in `tests/integration/test_generation.py`

### Implementation for User Story 1

- [ ] T012b [US1] Implement `src/generators/fetch_original.py`:
 - Retrieve **Original Unmodified ActivityNet Captions** clips for the control group required by the Plan (Independent Samples).
 - Use `huggingface_hub.load_dataset('ActivityNet/activitynet-captions', split='train', streaming=True)` to fetch a representative subset of source clips.
 - Save to `data/raw/original/` with metadata mapping IDs to timestamps.
 - **Distinct from T013**: This provides the "Original Unmodified" control set for the Independent test (Plan), while T013 provides the "Square-Cropped" control set for the Paired test (Spec).
- [ ] T013 [US1] Implement `src/generators/distort_video.py`:
 - Stream ActivityNet Captions data using `huggingface_hub.load_dataset('ActivityNet/activitynet-captions', split='train', streaming=True)`.
 - Apply geometric distortions at varying aspect ratios spanning from highly compressed to highly elongated configurations. using `ffmpeg` or `opencv-python`.
 - Implement FR-001 logic: exclude/regenerate clips where primary subject bounding box area is reduced >95%. **Use YOLOv8 (ultralytics) to detect primary subject bounding box if ActivityNet annotations are unavailable.**
 - **Generate a set of square-cropped clips from the SAME source IDs used for distortion (distributed across ratio groups).** for the Paired test (Spec).
 - Preserve original temporal ground-truth annotations.
 - Output metadata CSV linking distorted videos to original IDs and timestamps.
- [ ] T014 [US1] Implement `src/generators/validate_generation.py` to verify output dimensions and metadata integrity
- [ ] T015 [US1] Add error handling for low frame rate videos (skip/upsample with warning) and unresolvable 1-pixel lines (flag as "unresolvable", exclude, log)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Constrained Inference Execution (Priority: P2)

**Goal**: Execute the Kwai Keye-VL model (quantized to INT4) on the generated extreme-aspect and square-cropped datasets using a CPU-only environment to collect temporal grounding predictions.

**Independent Test**: Run inference on a subset of videos. Verify no OOM errors, model loads via `llama.cpp` or `Optimum-Intel` on CPU, and a JSON output file contains valid timestamp predictions. Peak VmRSS must be < 7GB.

### Tests for User Story 2 (TDD First) ⚠️

- [ ] T018 [P] [US2] Unit test for memory monitoring wrapper in `tests/unit/test_memory.py`
- [ ] T019 [P] [US2] Integration test for model loading and single clip inference in `tests/integration/test_inference.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `src/inference/run_inference.py`:
 - Load the **Kwai-Kyle/Kwai-Keye-VL-2.0-Int4** checkpoint (or verified equivalent from T004) in INT4 quantization. (or FP16 vision encoder fallback per FR-002)
 - Implement CPU-only execution logic using `llama.cpp` or `optimum-intel`
 - **Requires completion of T014 (Validation)**
 - Process generated distorted, square-cropped (T013), and original unmodified (T012b) clips.
 - Output predictions (start/end timestamps) in JSON format compatible with mIoU calculation.
- [ ] T021 [US2] Implement memory limit enforcement using `cgroups` or `ulimit` wrapper (FR-006). **Use `cgexec -g memory:limit_group` or `ulimit -v 7340032` (7GB in KB) and send SIGKILL on OOM.**
- [ ] T022 [US2] Implement retry mechanism with fallback to **FP16 for Vision Encoder only, keeping LLM in INT4** for specific clips if INT4 crashes (log deviations per FR-002).
- [ ] T023 [US2] Implement total batch time limit wrapper (FR-006) to abort if -hour limit is exceeded.
- [ ] T024 [US2] Add logging for OOM events, fallback activations, and excluded clips.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis & Reporting (Priority: P3)

**Goal**: Calculate mIoU for both conditions and perform a paired statistical test to determine significance of performance drop.

**Independent Test**: Run analysis script with pre-generated JSON predictions and ground truths. Verify report contains mIoU for both groups, p-value, test statistic, and significance statement (p < 0.05).

### Tests for User Story 3 (TDD First) ⚠️

- [ ] T036 [P] [US3] Unit test for mIoU calculation logic in `tests/unit/test_stats.py`
- [ ] T037 [P] [US3] Unit test for statistical test selection (Shapiro-Wilk -> t-test/Wilcoxon) in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T026 [US3] Implement `src/analysis/mIoU.py`:
 - Calculate mean Intersection-over-Union for predicted vs. ground-truth timestamps.
 - Separate results by condition (extreme-aspect vs. square-cropped vs. original).
 - Output to `data/outputs/metrics.csv` with columns `video_id`, `condition`, `mIoU`.
- [ ] T027 [US3] Implement `src/analysis/stats.py`:
 - **Perform Shapiro-Wilk test to check normality (alpha=0.05)**.
 - **Select and execute PAIRED t-test or Wilcoxon signed-rank test** on the **Paired mIoU scores from same source IDs (distorted vs. square-cropped)**.
 - Calculate p-value and effect size.
 - Generate report stating statistical significance (SC-002).
 - **Requires output of T026 (mIoU scores)**.
- [ ] T029 [US3] Implement `src/analysis/stats_independent.py`:
 - **Perform Welch's t-test or Mann-Whitney U** on **Independent mIoU scores from Original Unmodified vs. Distorted sets** (Plan requirement).
 - Calculate p-value and effect size.
 - Append results to the final report as a robustness check of the Plan's methodology.
- [ ] T028 [US3] Implement report generation to output structured JSON/Markdown with all metrics and conclusions.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `docs/` (quickstart, data-model, research)
- [ ] T031 Code cleanup and refactoring
- [ ] T032 Performance optimization for streaming data processing
- [ ] T033 [P] Additional unit tests in `tests/unit/`
- [ ] T034 Run `quickstart.md` validation: **Execute `bash scripts/quickstart.sh` and verify exit code 0 and existence of `data/outputs/report.md`.**

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
- **User Story 2 (P2)**: Depends on User Story 1 (requires distorted/control data) AND T014 (Validation)
- **User Story 3 (P3)**: Depends on User Story 2 (requires prediction JSON) AND T026 (mIoU)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation (TDD)
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
Task: "Unit test for aspect ratio calculation logic in tests/unit/test_distort.py"
Task: "Unit test for bounding box integrity check in tests/unit/test_distort.py"
Task: "Integration test for full generation pipeline in tests/integration/test_generation.py"

# Launch implementation tasks:
Task: "Implement src/generators/distort_video.py"
Task: "Implement src/generators/validate_generation.py"
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
 - Developer A: User Story 1 (Data Generation)
 - Developer B: User Story 2 (Inference) - *Note: This must wait for US1 data, so sequential is likely required unless mock data is used for dev, but real data is required for final run*
 - Developer C: User Story 3 (Analysis) - *Note: Must wait for US2*
3. Stories complete and integrate independently

*Note: Due to strict data flow dependencies (US1 -> US2 -> US3), parallel execution across stories is limited. The primary parallelization is within the implementation of each story (tests, helper scripts, core logic).*

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Integrity**: Never use synthetic data as a fallback for real data. If ActivityNet fetch fails, the process must fail loudly.
- **Resource Limits**: Strictly adhere to RAM and time limits via wrappers.
- **Model Quantization**: Use INT4 for CPU inference; fallback to FP16 vision encoder if necessary, but log deviations.
- **Statistical Validity**: Ensure paired tests are used for within-subject comparisons (distorted vs. square-cropped) and independent tests for original vs. distorted (Plan).