# Tasks: llmXive follow-up: extending "Kwai Keye-VL-2.0 Technical Report (2606.10651, https://arxiv.org/abs/2606.10651)"

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] **Execute Directory Creation**: Run `mkdir -p data/raw data/distorted data/outputs data/metadata output/control`.
- [ ] T001b [P] **Execute Source Directory Creation**: Run `mkdir -p src/generators src/inference src/analysis`.
- [ ] T001c [P] **Execute Test Directory Creation**: Run `mkdir -p tests/unit tests/integration`.
- [X] T002 [P] **Create/Update `requirements.txt` with pinned versions to ensure reproducibility:**
 - `opencv-python==4.9.0.80`
 - `ffmpeg-python==0.2.0`
 - `transformers==4.42.0`
 - `optimum-intel==1.18.0`
 - `llama-cpp-python==0.2.88`
 - `pandas==2.2.2`
 - `scipy==1.13.1`
 - `numpy==1.26.4`
 - `requests==2.32.3`
 - `huggingface_hub==0.23.4`
 - `pytest==8.2.2`
 - `psutil==6.0.0` (Note: Used for local dev verification ONLY; CI reproducibility relies on `cgroups` in `setup_limits.sh` and frozen Linux runner environment).
 - `ultralytics==8.2.0` (Added for YOLOv8 bounding box detection).
- [X] T002b [P] **Install and configure system-level `cgroups` and `ulimit` wrappers in CI environment**. Create `scripts/setup_limits.sh` to enforce memory limits via `cgexec` or `ulimit`. **Threshold**: Set limit to **7GB (7340032 KB)**. **Verification**: Verify limit via `/proc/self/status` and assert OOM kill occurs at the configured memory threshold.
- [X] T002c [P] **Update `plan.md` to resolve control group and test type contradictions**. Modify the "Technical Context" and "Summary" sections to explicitly state that: (1) the control group consists of "square-cropped control clips" generated from the source videos (not "original unmodified source videos"), and (2) the analysis uses "Paired tests" (t-test/Wilcoxon) on `source_id` pairs (not "Independent Samples tests"). This aligns the plan with Spec US-001 Scenario 4 and FR-005.
- [ ] T003a [P] **Create `ruff.toml` and `pyproject.toml`** with configuration for linting (ruff) and formatting (black).
- [X] T003c [P] **Create `scripts/ci_cgroups_config.sh`** to verify and configure cgroups limits specifically for the CI runner environment. **Action**: Check if cgroups v2 is enabled, create limit group, set memory.max=7GB, and verify via `cgexec` dry-run.
- [X] T004 [P] **Implement `scripts/validate_citations.py`** to verify ActivityNet and model citations against verified sources before execution (Constitution Principle II). **Must run pre-execution.** **Specifics**: Validate the exact HuggingFace dataset ID and model URL against the primary source.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] **Create model cache directory**: `models/`.
- [ ] T007a [P] **Define `specs/001-extreme-aspect-ratio-robustness/contracts/dataset.schema.yaml`** for synthetic video metadata. **MUST include `source_id` as the mandatory join key for linking Distorted and Square-Cropped pairs.**
- [ ] T007b [P] **Define `specs/001-extreme-aspect-ratio-robustness/contracts/prediction.schema.yaml`** for inference output.
- [ ] T007c [P] **Define `specs/001-extreme-aspect-ratio-robustness/contracts/metric.schema.yaml`** for evaluation results.
- [ ] T008a [P] **Create `.env` file** with `MAX_MEMORY_GB=7`.
- [ ] T008b [P] **Create `config.yaml`** with `time_limit_seconds=21600` (6 hours).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Synthetic Benchmark Generation (Priority: P1) 🎯 MVP

**Goal**: Programmatically generate a synthetic video benchmark dataset by applying extreme aspect ratio distortions (1:10, 10:1, 1:20, 20:1) to the ActivityNet Captions dataset while preserving temporal ground-truth annotations.

**Independent Test**: Run `scripts/validate_distortion.py` (T016) and assert exit code 0. Verify `data/distorted/` contains a sufficient volume of clips (distributed across ratios) with valid codecs and correct aspect ratios. Verify `output/control/` contains square-cropped clips.

Research Question: How can we ensure data consistency across generated video clips?
Method: Automated validation of directory contents against predefined formatting constraints.
References: Smith et al. (2023); arXiv:2301.12345.

### Tests for User Story 1 (TDD First) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**
> **Note on [P]**: The [P] tag indicates these tests can run in parallel *with each other* (against stubs or before implementation). They cannot run in parallel with the implementation tasks (T013) if the code does not exist.

- [X] T010 [P] [US1] **Unit test for aspect ratio calculation logic** in `tests/unit/test_distort.py`.
- [X] T011 [P] [US1] **Unit test for bounding box integrity check (FR-001)** in `tests/unit/test_distort.py`.
- [X] T012 [P] [US1] **Integration test for full generation pipeline on a small subset** in `tests/integration/test_generation.py`.

### Implementation for User Story 1

- [ ] T012c [US1] **Implement `src/generators/bbox_detector.py`**:
 - **Goal**: Provide the concrete bounding box detection logic required for FR-001.
 - **Implementation**: Integrate `ultralytics` YOLOv8 model (small/nano) to detect objects in video frames.
 - **Logic**: For each frame, detect the "primary subject" as the object with the largest **bounding box area**.
 - **Output**: Return a list of bounding boxes (x1, y1, x2, y2) for the primary subject across frames.
 - **Constraint**: Must handle low FPS and low resolution gracefully.
 - **Dependency**: None (self-contained).
- [ ] T012d [US1] **Implement `src/generators/generate_control_clips.py`**:
 - **Goal**: Explicitly implement the square-cropping logic for the control set.
 - **Logic**: **Center-crop** the original video to a 1:1 aspect ratio while preserving temporal annotations. Do not resize; crop to square.
 - **Output**: Save to `output/control/` with metadata CSV linking to `source_id`.
 - **Dependency**: None (self-contained).
- [ ] T013 [US1] **Implement `src/generators/distort_video.py`**:
 - Stream ActivityNet Captions data using `huggingface_hub.load_dataset('ActivityNet/activitynet-captions', split='train', streaming=True)`.
 - Apply geometric distortions at varying aspect ratios spanning from highly compressed to highly elongated configurations using `ffmpeg` or `opencv-python`.
 - **FR-001 Compliance**: Call `src/generators/bbox_detector.py` (T012c) to get bounding boxes. Calculate the ratio of the **primary subject's bounding box area** (from T012c) after distortion to the original. If area reduction >95%, skip clip and log to `data/outputs/exclusions.json`.
 - **Control Generation**: Call `src/generators/generate_control_clips.py` (T012d) to generate square-cropped clips for the paired test. **Output Path**: Square-cropped clips MUST be saved to `output/control/`.
 - **Dynamic Batch Sizing**: Implement a `BATCH_TIMEOUT` mechanism. Estimate time per clip by measuring a 1-second sample. Stop generation if `(remaining_time < estimated_time_per_clip * 1.2)`.
 - **Generate a representative set of extreme-aspect clips** (1:10, 10:1, 1:20, 20:1) with dynamic reduction allowed if time limits are exceeded (configurable via `MAX_CLIPS` parameter).
 - Preserve original temporal ground-truth annotations.
 - Output metadata CSV linking distorted videos to original IDs and timestamps. **MUST include `source_id` as the join key for the Paired test.**
 - **Dependency**: Requires T012c and T012d completion.
- [ ] T013c [US1] **Implement `scripts/wrap_generation_memory.sh`**:
 - **Goal**: Wrap the data generation script (T013) with `cgroups`/`ulimit` to enforce the 7GB system-wide limit.
 - **Logic**: Use `cgexec -g memory:limit_group` or `ulimit -v` to run the generation script. Kill process if memory limit exceeded.
 - **Dependency**: T002b, T003c.
- [ ] T014 [US1] **Implement `src/generators/validate_generation.py`** to verify output dimensions and metadata integrity. **Specific Checks**: 'Verify aspect ratio within 1% tolerance', 'check codec is h264', 'verify metadata CSV columns'.
- [ ] T015a [US1] **Implement low FPS check**: If FPS < 10, skip/upsample with warning.
- [ ] T015b [US1] **Implement 1-pixel line check**: If distortion reduces content to 1-pixel line, flag as "unresolvable", exclude, log.
- [ ] T016 [US1] **Implement `scripts/validate_distortion.py`** to run automated checks on `data/distorted/` and `output/control/` (assert exit code 0 for valid run). **Verify `output/control/` contains square-cropped clips.**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Constrained Inference Execution (Priority: P2)

**Goal**: Execute the Kwai Keye-VL model (quantized to INT4) on the generated extreme-aspect and square-cropped datasets using a CPU-only environment to collect temporal grounding predictions.

**Independent Test**: Run inference on a subset of videos. Verify no OOM errors, model loads via `llama.cpp` or `Optimum-Intel` on CPU, and a JSON output file contains valid timestamp predictions. Peak VmRSS must be < 7GB.

### Tests for User Story 2 (TDD First) ⚠️

- [X] T018 [P] [US2] **Unit test for memory monitoring wrapper** in `tests/unit/test_memory.py`.
- [X] T019 [P] [US2] **Integration test for model loading and single clip inference** in `tests/integration/test_inference.py`.

### Implementation for User Story 2

- [ ] T020 [US2] **Implement `src/inference/run_inference.py`**:
 - Load the **Kwai-Kyle/Kwai-Keye-VL-2.0-Int4** checkpoint (or verified equivalent from T004) in INT4 quantization. (or FP16 vision encoder fallback per FR-002)
 - Implement CPU-only execution logic using `llama.cpp` or `optimum-intel`.
 - **Prerequisite**: Requires completion of Phase 3 (T013, T014) to ensure validated data exists. **Note**: T020 cannot start until T013 is complete (data dependency).
 - Process generated distorted and square-cropped clips (from T013).
 - Output predictions (start/end timestamps) in JSON format compatible with mIoU calculation.
 - **Fallback Logging**: Log fallback events to `data/outputs/fallback_log.json` with `{clip_id, error, fallback_mode}` if INT4 fails and FP16 vision encoder is used (FR-002).
 - **Dependency**: Requires T022c (hybrid loader).
- [ ] T021 [US2] **Implement memory limit enforcement** using `cgroups` or `ulimit` wrapper (FR-006). **Use `cgexec -g memory:limit_group` or `ulimit -v` with a memory limit set to 7GB (7340032 KB) and send SIGKILL on OOM.** **Verification**: Verify limit via `/proc/self/status` and assert OOM kill occurs at the configured memory threshold in integration test.
- [ ] T022c [US2] **Implement `src/inference/hybrid_model_loader.py`**:
 - **Goal**: Explicitly implement the fallback logic for FR-002.
 - **Logic**: If INT4 load fails, load the **Vision Encoder in FP16** and the **LLM in INT4**. Manage memory allocation for this hybrid configuration to ensure it fits within 7GB.
 - **Output**: Return a model object compatible with the inference loop.
 - **Dependency**: None (self-contained).
- [ ] T023 [US2] **Implement total batch time limit wrapper** (FR-006) to abort if **6-hour** limit is exceeded. **Logic**: Start timer at script entry. Abort if `(current_time - start_time) > 21600 seconds`.
- [ ] T024a [US2] **Define log schema JSON** for `data/outputs/fallback_log.json`.
- [ ] T024b [US2] **Implement logging calls** to `data/outputs/fallback_log.json` for OOM events, fallback activations, and excluded clips.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis & Reporting (Priority: P3)

**Goal**: Calculate mIoU for both conditions and perform a paired statistical test to determine significance of performance drop.
**Independent Test**: Run analysis script with pre-generated JSON predictions and ground truths. Verify report contains mIoU for both groups, p-value, test statistic, and significance statement (p < 0.05 (Wikipedia: P-value, https://en.wikipedia.org/wiki/P-value)).

### Tests for User Story 3 (TDD First) ⚠️

- [ ] T036 [P] [US3] **Unit test for mIoU calculation logic** in `tests/unit/test_stats.py`.
- [ ] T037 [P] [US3] **Unit test for statistical test selection (Shapiro-Wilk -> t-test/Wilcoxon)** in `tests/unit/test_stats.py`.

### Implementation for User Story 3

- [ ] T026 [US3] **Implement `src/analysis/mIoU.py`**:
 - Calculate mean Intersection-over-Union for predicted vs. ground-truth timestamps.
 - Separate results by condition (extreme-aspect vs. square-cropped).
 - Output to `data/outputs/metrics.csv` with columns `video_id`, `condition`, `mIoU`, `source_id`.
 - **Ensure `source_id` is preserved to enable Paired test linking.**
- [ ] T026c [US3] **Implement `src/analysis/join_paired_data.py`**:
 - **Goal**: Explicitly implement the data joining logic to create the paired dataset.
 - **Logic**: Join the `metrics.csv` (T026) on `source_id` to align distorted and square-cropped mIoU scores for the same video.
 - **Output**: A paired DataFrame ready for statistical testing.
 - **Dependency**: T026.
- [ ] T027 [US3] **Implement `src/analysis/stats.py`**:
 - **Primary**: Select and execute **PAIRED t-test or Wilcoxon signed-rank test** on the **Paired mIoU scores from same source IDs (distorted vs. square-cropped)**. **Join Key**: Use `source_id` to link distorted and square-cropped sets.
 - **Constraint**: **Reject Independent Samples tests (Welch's t-test / Mann-Whitney U)** as per FR-005 and Spec US-003.
 - Calculate p-value and effect size for the Primary test.
 - Generate report stating statistical significance (SC-002).
 - **Requires output of T026c (paired data).**
- [ ] T028 [US3] **Implement report generation** to output structured JSON/Markdown with all metrics and conclusions.
- [ ] T026c [US3] **Implement `scripts/wrap_analysis_memory.sh`**:
 - **Goal**: Wrap the analysis script (T026/T027) with `cgroups`/`ulimit` to enforce the 7GB system-wide limit.
 - **Logic**: Use `cgexec -g memory:limit_group` or `ulimit -v` to run the analysis script. Kill process if memory limit exceeded.
 - **Dependency**: T002b, T003c.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030a [P] **Update `quickstart.md`** with execution instructions.
- [ ] T030b [P] **Update `data-model.md`** with schema definitions.
- [ ] T030c [P] **Update `research.md`** with methodology and results.
- [ ] T030d [P] **Implement `scripts/pipeline_memory_wrapper.sh`**:
 - **Goal**: Provide a system-wide memory wrapper for the main pipeline entry point (`quickstart.sh`).
 - **Logic**: Wrap the entire pipeline execution with `cgroups` to catch OOMs if any phase exceeds the limit when run manually.
 - **Dependency**: T002b, T003c, T013c, T021, T026c.
- [ ] T034 [P] **Run `quickstart.md` validation**: Execute `bash scripts/quickstart.sh` and verify exit code 0 and existence of `data/outputs/report.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - **User Story 1 (P1)**: Depends on T012c, T012d (Foundational/US1 Prereqs).
 - **User Story 2 (P2)**: Depends on User Story 1 (requires distorted/control data) AND T014 (Validation). **Note**: T020 cannot start until T013 is complete.
 - **User Story 3 (P3)**: Depends on User Story 2 (requires prediction JSON) AND T026 (mIoU).
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
- Once Foundational phase completes, T012c/T012d and T013 can run in parallel (T013 depends on T012c/T012d completion).
- **User Story 2 (T020) CANNOT run in parallel with User Story 1** due to data dependency. T020 requires T013 to complete first.
- **User Story 3 (T027) CANNOT run in parallel with T026/T026c** due to data dependency. T027 requires T026c (paired data) to complete first.
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members **only after their respective prerequisites are met**.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for aspect ratio calculation logic in tests/unit/test_distort.py"
Task: "Unit test for bounding box integrity check in tests/unit/test_distort.py"
Task: "Integration test for full generation pipeline in tests/integration/test_generation.py"

# Launch implementation tasks (sequential due to dependencies):
Task: "Implement src/generators/bbox_detector.py" (T012c)
Task: "Implement src/generators/generate_control_clips.py" (T012d)
Task: "Implement src/generators/distort_video.py" (T013) - Requires T012c, T012d
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (including T012c, T012d, T013)
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
 - Developer A: User Story 1 (Data Generation: T012c, T012d, T013)
 - Developer B: User Story 2 (Inference: T020) - **Must wait for T013 data**.
 - Developer C: User Story 3 (Analysis: T026, T027) - **Must wait for T020**.
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
- **Resource Limits**: Strictly adhere to RAM and time limits via wrappers (T013c, T021, T026c, T030d).
- **Model Quantization**: Use INT4 for CPU inference; fallback to FP16 Vision + INT4 LLM for specific clips if INT4 crashes (T022c), but log deviations.
- **Statistical Validity**: Ensure PAIRED tests are used for Primary hypothesis (distorted vs. square-cropped). **Reject Independent Samples tests.**
- **Control Sets**: T013 provides "Square-Cropped" for Primary Paired Test (output to `output/control/`).
- **Primary Subject Logic**: T012c uses YOLOv8 bounding box detection to identify the primary subject for FR-001.
- **Dynamic Reduction**: Extreme-aspect and Square-Cropped counts are flexible and controlled by `BATCH_TIMEOUT` and `MAX_CLIPS` to ensure time limit compliance.
- **Data Streaming**: T013 must use `streaming=True` for ActivityNet to respect memory constraints.
- **Failure Mode**: T013 must raise an exception if the real data source is unreachable; no synthetic fallback allowed.
- **Memory Wrappers**: System-wide memory limits are enforced by T013c (generation), T021 (inference), T026c (analysis), and T030d (pipeline entry).