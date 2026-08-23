# Tasks: 001-garment-text-fidelity

**Input**: Design documents from `/specs/001-llmxive-follow-up-extending-fashionchame/`
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

- [ ] T001 [P] Initialize project directory structure: create `code/`, `data/raw/`, `data/processed/`, `tests/unit/`, `tests/integration/` at repository root
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (torch-cpu, transformers, opencv-python, scikit-learn, scipy, datasets, lpips, pandas, pyyaml, jsonschema). **Depends on**: T001, T003

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T042a [P] **Spec Amendment Task (Part 1)**: Update `spec.md` (FR-002, FR-010, FR-011, Assumptions) and `plan.md` to replace "Human3.6M" with "DeepFashion2" and replace "skeletal joint velocity" with "optical flow magnitude" for motion labels. **Deliverable**: Updated `spec.md` and `plan.md` files.
- [ ] T042b [P] **Spec Amendment Task (Part 2)**: Commit changes from T042a to git repository. **Depends on**: T042a. **Deliverable**: Git commit with updated `spec.md` and `plan.md`.
- [X] T004 [P] Implement `code/src/pipeline/validate_citations.py` (FR-014) to verify DeepFashion2 URL and model references using Reference-Validator Agent logic (title-token-overlap >= 0.7)
- [X] T005 [P] Implement `code/src/pipeline/manifest.py` (FR-013) for content hashing of code and data artifacts
- [X] T006 Create base configuration in `code/config/settings.yaml` (thresholds, paths, seeds, streaming chunk sizes)
- [ ] T007 [P] Implement `code/src/data/loader.py` (FR-002, FR-011) with `datasets.load_dataset(..., streaming=True)` for DeepFashion2 parquet. **Depends on**: T042b. **NOTE**: Implements DeepFashion2 per Plan decision after Spec Amendment.
- [X] T008 [P] Implement `code/src/data/prompt_gen.py` (FR-008) for blind metadata-to-text prompt generation
- [X] T009 [P] Implement `code/src/metrics/fidelity.py` (FR-003) for LPIPS and SSIM computation on CPU
- [X] T010 [P] Implement `code/src/metrics/latency.py` (FR-007) for frame-level inference timing
- [X] T011 [P] Implement `code/src/pipeline/streaming.py` (FR-012) for memory-triggered batched processing (trigger at 6.5 GB)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Feature-Stratified Fidelity Benchmarking (Priority: P1) 🎯 MVP

**Goal**: Run a controlled experiment to determine which garment attributes degrade when switching from image to text references.

**Independent Test**: The system ingests a stratified subset of DeepFashion2, runs the text-driven adapter, and outputs a JSON report with distinct fidelity scores for color, pattern, and texture.

### Tests for User Story 1 (OPTIONAL) ⚠️

- [X] T012 [P] [US1] Unit test for `FeasibilityFilter` logic in `tests/unit/test_loader.py`
- [X] T013 [P] [US1] Integration test for full benchmark pipeline in `tests/integration/test_fidelity_benchmark.py`

### Implementation for User Story 1

- [X] T014 [US1] Implement `code/src/data/feasibility_filter.py` (FR-011) to tag clips by `GarmentFeatureClass` (color, pattern, texture) using DeepFashion2 metadata. **Depends on**: T042b. **NOTE**: Deviates from FR-011 Human3.6M mandate per Plan (amended).
- [X] T015 [US1] Implement VLM verification step in `code/src/data/feasibility_filter.py` to exclude low-confidence prompts. **Specs**: Use `blip-large` model, with a configurable confidence threshold, output JSON with prompt/image_id/reason.
- [X] T016 [US1] Implement `code/src/data/stratified_subset.py` to select a benchmark subset ensuring class balance. **Depends on**: T015.
- [X] T017 [US1] Implement `code/src/adapters/text_cross_attention.py` (FR-001) to map frozen CLIP text embeddings to reference KV slots
- [X] T018 [US1] Implement `code/src/pipeline/runner.py` (FR-009) to execute the original image-driven baseline on the subset defined in T016. **Depends on**: T016, T042b.
- [X] T019 [US1] Implement `code/src/pipeline/runner.py` logic to execute the text-driven adapter on the subset defined in T016. **Depends on**: T016, T042b.
- [ ] T021 [US1] Implement edge case handling in `code/src/data/feasibility_filter.py` for ambiguous prompts (VLM confidence < 0.8 or conflicting attributes). **Output**: Generate `data/processed/filtered_subset_manifest.json` listing excluded samples. **Depends on**: T015.
- [ ] T020 [US1] Implement `code/src/pipeline/reporter.py` to aggregate LPIPS/SSIM scores by `GarmentFeatureClass` and calculate relative fidelity loss. **Output**: `data/processed/fidelity_report.json` with keys `mean_lpips`, `mean_ssim`, `relative_loss_percent` per class. **Constraint**: MUST consume ONLY samples from `data/processed/filtered_subset_manifest.json` (exclude Low Confidence). **Depends on**: T018, T019, T021. **Verification**: Verify schema and add test `test_reporter_aggregates_by_class()`.
- [ ] T022 [US1] Implement edge case handling for low sample counts (<10 per class) to skip statistical tests. **Specs**: If N < 30, raise `ValueError` with message "Insufficient samples for ANOVA". **Depends on**: T020.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Real-Time Latency Verification (Priority: P2)

**Goal**: Verify that the text adapter does not introduce prohibitive latency on CPU hardware.

**Independent Test**: The system processes a short video clip on a multi-core CPU and reports average inference time per frame against a real-time threshold.

### Tests for User Story 2 (OPTIONAL) ⚠️

- [X] T023 [P] [US2] Unit test for latency thresholding logic in `tests/unit/test_latency.py`

### Implementation for User Story 2

- [ ] T028-config [US2] Define sample size for latency verification and establish the 50ms threshold in `settings.yaml`. **Output**: Config value `latency_threshold_ms = 50`.
- [ ] T028-logic [US2] Implement `code/src/metrics/latency.py` function `evaluate_latency_pass_fail(average_latency_ms, threshold_ms)` that returns a JSON object `{"status": "PASS" | "FAIL", "average_ms": <float>}`. **Depends on**: T028-config.
- [X] T024 [US2] Implement `code/src/pipeline/runner.py` logic to measure end-to-end inference time per frame (FR-007). **Depends on**: T018, T019, T011, T016, T028-config.
- [X] T025 [US2] Implement `code/src/pipeline/runner.py` logic to flag frames exceeding a defined latency threshold and identify bottleneck. **Specs**: Insert timers around `text_encoder.encode()`, `adapter.forward()`, and `backbone.generate()` functions. **Depends on**: T028-logic.
- [X] T026 [US2] Implement `code/src/pipeline/runner.py` streaming/batched mode logic using `code/src/pipeline/streaming.py` (FR-012) with memory trigger at 6.5 GB. **Depends on**: T011.
- [X] T027 [US2] Implement moving average calculation for latency in streaming mode in `code/src/metrics/latency.py`
- [X] T029 [US2] Verify CPU-only execution path in `code/src/pipeline/runner.py` ensures no CUDA calls (FR-004)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance & Sensitivity Analysis (Priority: P3)

**Goal**: Confirm observed fidelity differences are statistically significant and robust.

**Independent Test**: The system executes ANOVA on fidelity scores and performs a sensitivity sweep of the optical flow consistency threshold.

### Tests for User Story 3 (OPTIONAL) ⚠️

- [X] T030 [P] [US3] Unit test for ANOVA and Bonferroni correction in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [X] T031 [US3] Implement `code/src/stats/significance.py` (FR-005) to perform ANOVA on fidelity scores across feature classes. **Depends on**: T020 (Report Aggregation).
- [X] T032 [US3] Implement Bonferroni correction logic in `code/src/stats/significance.py` for multiple hypothesis tests. **Depends on**: T031.
- [ ] T034-extended [US3] Implement `code/src/stats/motion_labels.py` to derive 'ground-truth motion labels' from **optical flow magnitude** (calculated from video frames) since skeletal velocity is unavailable in DeepFashion2. **Output**: `data/processed/motion_labels.json` containing `frame_id`, `optical_flow_magnitude`, `motion_label` (High/Low). **Depends on**: T042b. **NOTE**: Replaces FR-010 skeletal derivation with valid DeepFashion2 proxy.
- [ ] T033 [US3] Implement `code/src/stats/sensitivity.py` (FR-006) to sweep optical flow consistency threshold {0.01, 0.05, 0.1}. **Depends on**: T009, T014, T034-extended. **Verification**: Verify `motion_labels.json` exists and is non-empty before sweep.
- [ ] T035 [US3] Implement `code/src/stats/sensitivity.py` to generate the threshold variation table. **Output**: `data/processed/sensitivity_analysis.csv` with columns `threshold`, `fp_rate`, `fn_rate`. **Depends on**: T033, T034-extended.
- [X] T036 [US3] Implement edge case handling in `code/src/stats/significance.py` for low power (N<30) scenarios

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T037 [P] Run full benchmark on a representative clip subset and generate `data/processed/fidelity_report.json`. **Depends on**: T020, T024, T031, T035.
- [ ] T038 [P] Generate `data/processed/manifest.json` with content hashes
- [ ] T039 [P] Update `docs/quickstart.md` with instructions for running the benchmark
- [ ] T040 [P] Run `pytest` to ensure all unit and integration tests pass
- [ ] T041 [P] Verify `code/src/pipeline/runner.py` completes within 6 hours on CPU free-tier

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
Task: "Unit test for FeasibilityFilter logic in tests/unit/test_loader.py"
Task: "Integration test for full benchmark pipeline in tests/integration/test_fidelity_benchmark.py"

# Launch all models for User Story 1 together:
Task: "Implement FeasibilityFilter logic in code/src/data/feasibility_filter.py"
Task: "Implement VLM verification step in code/src/data/feasibility_filter.py"
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
- **Dataset Note**: All data loading tasks MUST use `datasets.load_dataset(..., streaming=True)` with DeepFashion2. Do NOT use Human3.6M.
- **Memory Constraint**: Ensure `runner.py` implements the 6.5 GB memory trigger for streaming mode (T011).
- **No Synthetic Data**: Do NOT implement synthetic data fallbacks. Fail loudly if real data fetch fails.
- **Spec Amendment**: Tasks T042a and T042b are mandatory and blocking for all data processing tasks.
- **Motion Labels**: Motion labels are derived from optical flow magnitude (T034-extended), not skeletal velocity, due to DeepFashion2 dataset constraints.
- **Optical Flow Implementation**: T034-extended must implement optical flow calculation using `cv2.calcOpticalFlowFarneback` or `cv2.calcOpticalFlowPyrLK` on sampled frames to compute magnitude, ensuring the calculation is optimized for CPU execution to avoid exceeding the 6-hour runtime limit.
- **Data Streaming**: T007 and T034-extended must strictly adhere to streaming patterns; do not load full video sequences into memory. Process frame pairs in chunks to calculate flow magnitude.