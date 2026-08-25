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

- [X] T001a [P] Initialize `code/` directory: create `code/` at repository root.
- [X] T001b [P] Initialize `data/` directory: create `data/` at repository root.
- [X] T001c [P] Initialize `tests/` directory: create `tests/` at repository root.
- [X] T002 Initialize Python 3.11 project with `requirements.txt`. **Constraint**: MUST pin exact versions for all dependencies (e.g., `torch==2.0.0+cpu`, `transformers==4.30.0`, `opencv-python==4.8.0.74`, `scikit-learn==1.3.0`, `scipy==1.11.0`, `datasets==2.14.0`, `lpips==0.1.4`, `pandas==2.0.3`, `pyyaml==6.0.1`, `jsonschema==4.18.0`, `psutil==5.9.5`). **Depends on**: T001a, T001b, T001c.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools. **Depends on**: T002.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Execution Order**: Tasks in this phase must be executed sequentially where dependencies exist, despite phase grouping.

- [X] T042a-002-spec [P] **Spec Amendment Task (FR-002)**: Update `spec.md` (FR-002) to replace "Human3.6M" with "DeepFashion2" and specify `datasets.load_dataset(..., streaming=True)`. **Deliverable**: Updated `spec.md` with specific text changes.
- [X] T042a-002-plan [P] **Plan Amendment Task (FR-002)**: Update `plan.md` (Section 2) to replace "Human3.6M" with "DeepFashion2" and specify streaming strategy. **Deliverable**: Updated `plan.md` with specific text changes.
- [X] T042c-002 [P] **Verify Spec Amendment (FR-002)**: Run `code/src/pipeline/validate_spec_amendments.py` to verify that `spec.md` and `plan.md` contain the required DeepFashion2 and streaming changes. **Deliverable**: Verification log confirming changes. **Depends on**: T042a-002-spec, T042a-002-plan.
- [X] T042a-010-spec [P] **Spec Amendment Task (FR-010)**: Update `spec.md` (FR-010) to replace "skeletal joint velocity" with "optical flow magnitude" for motion labels. **Deliverable**: Updated `spec.md` with specific text changes.
- [X] T042a-010-plan [P] **Plan Amendment Task (FR-010)**: Update `plan.md` (Section 3.2) to reflect optical flow magnitude as the motion proxy. **Deliverable**: Updated `plan.md` with specific text changes.
- [X] T042c-010 [P] **Verify Spec Amendment (FR-010)**: Run `code/src/pipeline/validate_spec_amendments.py` to verify that `spec.md` and `plan.md` contain the required optical flow changes. **Deliverable**: Verification log confirming changes. **Depends on**: T042a-010-spec, T042a-010-plan.
- [X] T042a-011-spec [P] **Spec Amendment Task (FR-011)**: Update `spec.md` (FR-011) to replace "skeletal velocity" filtering with "optical flow magnitude" and VLM confidence filtering for DeepFashion2. **Deliverable**: Updated `spec.md` with specific text changes.
- [X] T042a-011-plan [P] **Plan Amendment Task (FR-011)**: Update `plan.md` (Section 3.1) to reflect optical flow and VLM filtering. **Deliverable**: Updated `plan.md` with specific text changes.
- [X] T042c-011 [P] **Verify Spec Amendment (FR-011)**: Run `code/src/pipeline/validate_spec_amendments.py` to verify that `spec.md` and `plan.md` contain the required filtering changes. **Deliverable**: Verification log confirming changes. **Depends on**: T042a-011-spec, T042a-011-plan.
- [X] T042a-034 [P] **Spec Amendment Task (Downsampling)**: Update `spec.md` (FR-010) to explicitly authorize the 5:1 frame downsampling ratio for motion labeling to ensure runtime < 6h. **Deliverable**: Updated `spec.md` with specific text changes.
- [X] T042c-034 [P] **Verify Spec Amendment (Downsampling)**: Run `code/src/pipeline/validate_spec_amendments.py` to verify the downsampling authorization in `spec.md`. **Deliverable**: Verification log confirming changes. **Depends on**: T042a-034.
- [X] T042b [P] **Spec Amendment Task (Part 2)**: Commit changes from T042a-* and T042c-* to git repository. **Depends on**: T042c-002, T042c-010, T042c-011, T042c-034. **Deliverable**: Git commit with updated `spec.md` and `plan.md`.
- [X] T007 [P] Implement `code/src/data/loader.py` (FR-002, FR-011) with `datasets.load_dataset(..., streaming=True)` for DeepFashion2 parquet. **Depends on**: T042b. **NOTE**: Implements DeepFashion2 per Plan decision after Spec Amendment.
- [X] T034-sub [P] **Define Downsampling Ratio**: Write `optical_flow_subsampling_ratio: a subsampling ratio will be applied to the optical flow computation to balance computational efficiency and motion field resolution, following the methodology outlined in prior work (DOI:10.xxxx/xxxxx).` to `code/config/settings.yaml` under the `motion` key. **Output**: `code/config/settings.yaml` updated. **Depends on**: T042b.
- [X] T034-extended [P] **Motion Labeling Logic**: Implement `code/src/stats/motion_labels.py` to derive 'ground-truth motion labels' from **optical flow magnitude** (calculated from video frames) using `cv2.calcOpticalFlowFarneback` on sampled frames (every nth frame as defined in T034-sub). **Output**: Logic to generate `data/processed/motion_labels.json` containing `frame_id`, `optical_flow_magnitude`, `motion_label` (High/Low). **Constraint**: Must be CPU-optimized. **Requirement**: Implement frame downsampling (process every nth frame) to ensure runtime < 6h. **Depends on**: T042b, T007, T034-sub.
- [X] T007-verify [P] **Verification Script**: Create `tests/scripts/verify_streaming.py` to verify `loader.py` yields a substantial number of records without OOM. **Depends on**: T007. **Note**: Integration script verifying record count.
- [X] T007-test [P] Unit test for `loader.py` streaming: `tests/unit/test_loader_streaming.py` verifies A substantial volume of records yield without OOM. **Depends on**: T007. **Note**: Unit test for streaming logic.
- [X] T004 [P] Implement `code/src/pipeline/validate_citations.py` (FR-014) to verify DeepFashion2 URL and model references using Reference-Validator Agent logic (title-token-overlap >= 0.7). **Constraint**: Must verify URLs return 200 OK status code before processing.
- [X] T005 [P] Implement `code/src/pipeline/manifest.py` (FR-013) for content hashing of code and data artifacts.
- [X] T006 [P] Create base configuration in `code/config/settings.yaml` with exact structure:
 ```yaml
 experiment:
 seed: 42
 streaming_chunk_size: a configurable parameter optimized for balancing latency and throughput
 motion:
 optical_flow_threshold: a value determined through empirical calibration to balance motion sensitivity and noise robustness.
 optical_flow_subsampling_ratio: a configurable subsampling ratio for optical flow processing.
 model:
 vlm_confidence_threshold: A high-confidence threshold will be established to filter model outputs.
 blip_model_id: "Salesforce/blip-large"
 benchmark:
 latency_threshold_ms: null # Deferred per FR-007
 ```
 **Depends on**: T042b.
- [X] T008 [P] Implement `code/src/data/prompt_gen.py` (FR-008) for blind metadata-to-text prompt generation. **Constraint**: Must be integrated with VLM verification (T015) before use.
- [X] T009 [P] Implement `code/src/metrics/fidelity.py` (FR-003) for LPIPS and SSIM computation on CPU.
- [X] T010 [P] Implement `code/src/metrics/latency.py` (FR-007) for frame-level inference timing.
- [X] T011 [P] Implement `code/src/pipeline/streaming.py` (FR-012) for memory-triggered batched processing. **Constraint**: Must use `psutil` to monitor memory usage in real-time. **Trigger**: Must trigger batched processing when RAM usage exceeds a high threshold, potentially impacting system stability (). Research Question: How does memory consumption scale with dataset size? Method: Empirical benchmarking using controlled variable loads.. **Verification**: Verify memory trigger activates at 6.5 GB ± 5% using psutil. **Depends on**: T007.
- [X] T047 [P] **Define Runner Interface**: Implement `code/src/pipeline/runner_interface.py` as an abstract base class defining the `run_benchmark` and `measure_latency` methods. **Constraint**: Must enforce CPU-only device initialization in the interface. **Depends on**: T006.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Feature-Stratified Fidelity Benchmarking (Priority: P1) 🎯 MVP

**Goal**: Run a controlled experiment to determine which garment attributes degrade when switching from image to text references.

**Independent Test**: The system ingests a stratified subset of DeepFashion2, runs the text-driven adapter, and outputs a JSON report with distinct fidelity scores for color, pattern, and texture.

**⚠️ Execution Order**: Within this phase, tasks must be executed sequentially where dependencies exist. T020 must wait for T018, T019, T021 to complete.

### Tests for User Story 1 (OPTIONAL) ⚠️

- [X] T012 [P] [US1] Unit test for `FeasibilityFilter` logic in `tests/unit/test_feasibility_filter.py`. **Depends on**: None (Write first, fails initially). **Note**: Follows TDD; written before implementation T014 to ensure testability.
- [X] T013 [P] [US1] Integration test for full benchmark pipeline in `tests/integration/test_fidelity_benchmark.py`. **Depends on**: T014, T015, T016, T017, T018, T019, T021, T047.

### Implementation for User Story 1

- [X] T014 [US1] Implement `code/src/data/feasibility_filter.py` (FR-011) to tag clips by `GarmentFeatureClass` (color, pattern, texture) using DeepFashion2 metadata. **Depends on**: T042b, T034-extended. **NOTE**: Uses optical flow magnitude from T034-extended.
- [X] T015 [US1] Implement VLM verification step in `code/src/data/feasibility_filter.py` to exclude low-confidence prompts. **Specs**: Use model ID `Salesforce/blip-large`, load with `device='cpu'`, `torch_dtype=torch.float`, `trust_remote_code=False`. Apply configurable confidence threshold (from `settings.yaml`), output JSON to `data/processed/vlm_confidence_log.json`. **Depends on**: T014, T006.
- [X] T016 [US1] Implement `code/src/data/stratified_subset.py` to select a benchmark subset ensuring class balance. **Constraint**: Must consume `vlm_confidence_log.json` from T015 to filter low-confidence samples before stratification. **Depends on**: T015.
- [X] T017 [US1] Implement `code/src/adapters/text_cross_attention.py` (FR-001) to map frozen CLIP text embeddings to reference KV slots. **Constraint**: Must explicitly initialize on CPU (`device='cpu'`). **Depends on**: T047.
- [X] T018 [US1] Implement `code/src/pipeline/runner.py` (FR-009) to execute the original image-driven baseline on the subset defined in T021. **Depends on**: T016, T042b, T021, T047.
- [X] T019 [US1] Implement `code/src/pipeline/runner.py` logic to execute the text-driven adapter on the subset defined in T021. **Depends on**: T016, T042b, T021, T047.
- [X] T021 [US1] Implement edge case handling in `code/src/data/feasibility_filter.py` for ambiguous prompts (VLM confidence < 0.8 or conflicting attributes). **Output**: Generate `data/processed/filtered_subset_manifest.json` (valid samples only). **Constraint**: Manifest MUST include `optical_flow_magnitude` values and the specific threshold used for filtering for each sample. **Depends on**: T015, T016. **NOTE**: Resolves ambiguity on artifact scope.
- [X] T020 [US1] Implement `code/src/pipeline/reporter.py` to aggregate LPIPS/SSIM scores by `GarmentFeatureClass` and calculate relative fidelity loss. **Output**: `data/processed/fidelity_report.json` with exact schema:
 ```json
 {
 "summary": {
 "total_samples": "<int>",
 "classes_evaluated": ["<str>",...]
 },
 "per_class": {
 "<class_name>": {
 "mean_lpips": "<float>",
 "mean_ssim": "<float>",
 "relative_loss_percent": "<float>",
 "sample_count": "<int>"
 }
 }
 }
 ```
 **Constraint**: MUST consume ONLY samples from `data/processed/filtered_subset_manifest.json`. **Includes**: Edge case handling for low sample counts (<10 per class) - raises `ValueError` with message "Insufficient samples for ANOVA". **Depends on**: T018, T019, T021. **Must wait for completion of T018, T019, T021**. **Verification**: Verify schema and add test `tests/unit/test_reporter.py::test_reporter_aggregates_by_class()`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Real-Time Latency Verification (Priority: P2)

**Goal**: Verify that the text adapter does not introduce prohibitive latency on CPU hardware.

**Independent Test**: The system processes a short video clip on a multi-core CPU and reports average inference time per frame against an empirical target.

### Tests for User Story 2 (OPTIONAL) ⚠️

- [X] T023 [P] [US2] Unit test for latency thresholding logic in `tests/unit/test_latency.py`. **Depends on**: T028-logic.

### Implementation for User Story 2

- [X] T028-config [US2] Define sample size for latency verification and establish a configurable target in `code/config/settings.yaml` (key `latency_threshold_ms`). **Output**: Config value `latency_threshold_ms: null` (Deferred per FR-007). **Note**: This is a target for analysis; the status is determined by empirical measurement. **Depends on**: T006.
- [X] T028-logic [US2] Implement `code/src/metrics/latency.py` function `evaluate_latency(average_latency_ms)` that returns a JSON object `{"average_ms": <float>, "status": "MEASURED", "threshold_ms": null}` (since threshold is deferred). **Constraint**: Must perform actual measurement, not return hardcoded "DEFERRED". **Depends on**: T028-config.
- [X] T024 [US2] Implement `code/src/pipeline/runner.py` logic to measure end-to-end inference time per frame (FR-007). **Depends on**: T018, T019, T011, T047, T028-config. **Note**: Removed dependency on T016 to allow independent subset selection for latency testing.
- [X] T025 [US2] Implement `code/src/pipeline/runner.py` logic to flag frames exceeding a defined latency threshold and identify bottleneck. **Specs**: Insert timers around `text_encoder.encode()`, `adapter.forward()`, and `backbone.generate()` functions. **Output**: Generate `data/processed/latency_breakdown.json` containing per-component timings (encoder, adapter, backbone). **Depends on**: T024, T028-logic. **NOTE**: T025 is a sub-task of T024 analysis.
- [X] T026 [US2] Implement `code/src/pipeline/runner.py` streaming/batched mode logic using `code/src/pipeline/streaming.py` (FR-012) with memory trigger at 6.5 GB. **Depends on**: T011.
- [X] T027 [US2] Implement moving average calculation for latency in streaming mode in `code/src/metrics/latency.py`. **Depends on**: T028-logic, T026.
- [X] T028-report [US2] Generate `data/processed/latency_verification_report.json` containing average latency, threshold (null), and status "MEASURED" based on empirical data. **Constraint**: Must include breakdown from `data/processed/latency_breakdown.json`. **Unit**: milliseconds. **Depends on**: T024, T028-logic. **NOTE**: Explicitly resolves coverage-5e9650ac by generating the required artifact with empirical validation.
- [X] T029 [P] Verify CPU-only execution path in `code/src/pipeline/runner.py` ensures no CUDA calls (FR-004). **Depends on**: T018, T019.
- [X] T048 [P] **Verify CPU Initialization**: Implement `tests/unit/test_cpu_init.py` to verify that `text_cross_attention.py` and `runner.py` explicitly initialize models on `device='cpu'` and raise an error if CUDA is detected. **Depends on**: T017, T018, T019.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Significance & Sensitivity Analysis (Priority: P3)

**Goal**: Confirm observed fidelity differences are statistically significant and robust.

**Independent Test**: The system executes ANOVA on fidelity scores and performs a sensitivity sweep of the optical flow consistency threshold.

### Tests for User Story 3 (OPTIONAL) ⚠️

- [X] T030 [P] [US3] Unit test for ANOVA and Bonferroni correction in `tests/unit/test_stats.py`. **Depends on**: T031, T032.

### Implementation for User Story 3

- [X] T031 [US3] Implement `code/src/stats/significance.py` (FR-005) to perform ANOVA on fidelity scores across feature classes. **Constraint**: Must explicitly verify that input data is stratified by `GarmentFeatureClass` (Color, Pattern, Texture) before running the test. If not stratified, raise `ValueError`. **Depends on**: T020 (Report Aggregation).
- [X] T032 [US3] Implement Bonferroni correction logic in `code/src/stats/significance.py` for multiple hypothesis tests. **Depends on**: T031.
- [X] T036 [US3] Implement edge case handling in `code/src/stats/significance.py` for low power (N<30) scenarios. **Constraint**: Perform Power Analysis. If N<30, output results with a "Low Power Warning" flag in the report and explicitly state the limitation. If N<10, raise `ValueError` with message "Insufficient samples for statistical analysis". **Depends on**: T031.
- [X] T033 [US3] Implement `code/src/stats/sensitivity.py` (FR-006) to sweep optical flow consistency threshold across a range of values. **Depends on**: T009, T014, T034-extended. **Verification**: Verify `motion_labels.json` exists and is non-empty before sweep.
- [X] T035 [US3] Implement `code/src/stats/sensitivity.py` to generate the threshold variation table. **Output**: `data/processed/sensitivity_analysis.csv` with columns `threshold`, `robustness_metric`. **Calculation**: Iterate threshold from a low value to a higher value in incremental steps. `robustness_metric` = Pearson correlation coefficient between predicted motion labels and ground truth labels derived from T034-extended. **Depends on**: T033, T034-extended.
- [X] T037 [P] Run full benchmark on a representative clip subset and generate `data/processed/fidelity_report.json`. **Depends on**: T020, T024, T031, T035, T011, T007. **Note**: T011 and T007 now include the merged memory safety and data integrity constraints.
- [X] T038 [P] Generate `data/processed/manifest.json` with content hashes. **Execution**: Run `code/src/pipeline/manifest.py` against all artifacts in `data/processed/` and `code/`. **Depends on**: T037. **NOTE**: Explicitly resolves coverage-0e1fbe8d by defining the execution step.
- [X] T039 [P] Update `docs/quickstart.md` with instructions for running the benchmark. **Depends on**: T037.
- [X] T040 [P] Run `pytest` to ensure all unit and integration tests pass. **Depends on**: T037.
- [X] T041 [P] Verify `code/src/pipeline/runner.py` completes within 6 hours on CPU free-tier. **Depends on**: T037.
- [ ] T043 [P] **Revision Fix FR-002**: Refactor `code/src/data/loader.py` to enforce strict streaming mode with `datasets.load_dataset(..., streaming=True)` and add explicit error handling that raises `RuntimeError` if the fetch fails, ensuring no synthetic fallback is used. **Depends on**: T007. **Rationale**: Addresses reviewer concern about potential synthetic fallbacks and ensures strict adherence to the streaming constraint for DeepFashion2.
- [ ] T044 [P] **Revision Fix FR-010**: Refactor `code/src/stats/motion_labels.py` to calculate optical flow magnitude using `cv2.calcOpticalFlowFarneback` on a strictly sampled frame sequence (every 5th frame) and implement a chunked processing loop to prevent OOM during flow calculation. **Depends on**: T034-extended. **Rationale**: Addresses reviewer concern about CPU runtime limits and OOM risks during optical flow computation on large video frames.
- [ ] T045 [P] **Revision Fix FR-005**: Refactor `code/src/stats/significance.py` to explicitly validate input stratification by `GarmentFeatureClass` before running ANOVA and ensure Bonferroni correction is applied to the p-values of all pairwise comparisons. **Depends on**: T031, T032. **Rationale**: Addresses reviewer concern that non-parametric alternatives might be used instead of the mandated ANOVA and ensures statistical rigor.
- [ ] T046 [P] **Revision Fix FR-011**: Refactor `code/src/data/feasibility_filter.py` to strictly enforce the VLM confidence threshold (>= 0.8) using `Salesforce/blip-large` and explicitly tag samples with `GarmentFeatureClass` from DeepFashion2 metadata, raising an error if tags are missing. **Depends on**: T014, T015. **Rationale**: Addresses reviewer concern about noisy attribute annotations and ensures the filter logic correctly identifies and excludes low-confidence samples without fallback.

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
- All Foundational tasks marked [P] can run in parallel (within Phase 2) **EXCEPT** where explicit ordering constraints are noted (e.g., T034-extended after T007)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for FeasibilityFilter logic in tests/unit/test_feasibility_filter.py"
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
- **Spec Amendment**: Tasks T042a-* and T042c-* are mandatory and blocking for all data processing tasks.
- **Motion Labels**: Motion labels are derived from optical flow magnitude (T034-extended), not skeletal velocity, due to DeepFashion2 dataset constraints. T034-extended is now in Phase 2 to unblock US1.
- **Optical Flow Implementation**: T034-extended must implement optical flow calculation using `cv2.calcOpticalFlowFarneback` or `cv2.calcOpticalFlowPyrLK` on sampled frames to compute magnitude, ensuring the calculation is optimized for CPU execution to avoid exceeding the 6-hour runtime limit.
- **Data Streaming**: T007 and T034-extended must strictly adhere to streaming patterns; do not load full video sequences into memory. Process frame pairs in chunks to calculate flow magnitude.
- **Latency Verification**: The 50ms threshold is a target for analysis (FR-007 'deferred'). T028-config and T028-logic define the target, T028-report generates the artifact with empirical validation (MEASURED) rather than a hardcoded 'DEFERRED'.
- **Revision Concern FR-002/FR-010**: Ensure `loader.py` strictly uses `streaming=True` and `optical_flow.py` processes frame pairs in chunks to prevent OOM.
- **Revision Concern FR-005**: Ensure `significance.py` explicitly implements ANOVA and Bonferroni correction. Do NOT use non-parametric alternatives (Kruskal-Wallis) as the spec mandates ANOVA.
- **Revision Concern FR-011**: Ensure `feasibility_filter.py` correctly tags `GarmentFeatureClass` from DeepFashion2 metadata and strictly enforces the VLM confidence threshold without fallback.
- **Ordering Note**: Phase 2 tasks T007 and T034-extended have explicit ordering (T034-extended after T007). Phase 3 tasks T018, T019, T021 must complete before T020.
- **Revision Concerns**: Tasks T043, T044, T045, T046 are mandatory revision tasks to address specific reviewer concerns regarding data integrity, memory safety, statistical validity, and filtering logic. These must be completed before the final polish phase.
- **Downsampling Authorization**: T034-sub and T042a-034 explicitly authorize the 5:1 downsampling ratio to ensure scope alignment.
- **CPU Initialization**: T048 ensures all model components are explicitly initialized on CPU.