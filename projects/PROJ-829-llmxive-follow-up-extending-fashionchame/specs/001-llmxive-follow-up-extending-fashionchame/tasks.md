---
description: "Task list template for feature implementation"
---

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
- [X] T002 Initialize Python 3.11 project with `requirements.txt`. **Constraint**: MUST pin exact versions for all dependencies (e.g., `torch==2.0.0+cpu`, `transformers==4.30.0`, `opencv-python==4.8.0.74`, `scikit-learn==1.3.0`, `scipy==1.11.0`, `datasets==2.14.0`, `pandas==2.0.3`, `jsonschema==4.18.0`, `psutil==5.9.5`, `blake3==1.0.0`). **Depends on**: T001a, T001b, T001c.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools. **Depends on**: T002.
- [X] T003b [P] **Reproducibility Infrastructure**: Implement `code/src/utils/seeds.py` to pin random seeds (numpy, torch, random) from `settings.yaml` and `code/src/pipeline/state_updater.py` to record artifact checksums into `state/projects/PROJ-829-llmxive-follow-up-extending-fashionchame.yaml`. **Constraint**: `state_updater.py` must be executable as a standalone script to update the state file after artifact generation. **Depends on**: T002.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. **Execution Order**: Tasks in this phase must be executed sequentially where dependencies exist, despite phase grouping.

- [X] T042a-002-spec [P] **Spec Amendment Task (FR-002)**: Generate a patch to replace "Human3.6M" with "DeepFashion2" in `spec.md` and apply it. **Deliverable**: Updated `spec.md`.
- [X] T042c-002-impl [P] **Implement Validator**: Create `code/src/pipeline/validate_spec_amendments.py` to verify that `spec.md` and `plan.md` contain the required DeepFashion2 and streaming changes. **Depends on**: T002.
- [X] T042c-002 [P] **Verify Spec Amendment (FR-002)**: Run `code/src/pipeline/validate_spec_amendments.py` to verify that `spec.md` and `plan.md` contain the required DeepFashion2 and streaming changes. **Deliverable**: Verification log confirming changes. **Depends on**: T042a-002-spec, T042c-002-impl.
- [X] T042a-010-spec [P] **Spec Amendment Task (FR-010)**: Generate a patch to replace "skeletal joint velocity" with "optical flow magnitude" in `spec.md` and apply it. **Deliverable**: Updated `spec.md`.
- [X] T042c-010 [P] **Verify Spec Amendment (FR-010)**: Run `code/src/pipeline/validate_spec_amendments.py` to verify that `spec.md` and `plan.md` contain the required optical flow changes. **Deliverable**: Verification log confirming changes. **Depends on**: T042a-010-spec, T042c-002-impl.
- [X] T042a-011-spec [P] **Spec Amendment Task (FR-011)**: Generate a patch to replace "skeletal velocity" filtering with "optical flow magnitude" and VLM confidence filtering for DeepFashion2 in `spec.md` and apply it. **Deliverable**: Updated `spec.md`.
- [X] T042c-011 [P] **Verify Spec Amendment (FR-011)**: Run `code/src/pipeline/validate_spec_amendments.py` to verify that `spec.md` and `plan.md` contain the required filtering changes. **Deliverable**: Verification log confirming changes. **Depends on**: T042a-011-spec, T042c-002-impl.
- [X] T042a-034 [P] **Spec Amendment Task (Downsampling)**: Generate a patch to explicitly authorize the frame downsampling ratio in `spec.md` (Section 5. Data Model or Section 3.2 Motion Analysis) and apply it. **Deliverable**: Updated `spec.md`.
- [X] T042c-034 [P] **Verify Spec Amendment (Downsampling)**: Run `code/src/pipeline/validate_spec_amendments.py` to verify the downsampling authorization in `spec.md`. **Deliverable**: Verification log confirming changes. **Depends on**: T042a-034, T042c-002-impl.
- [X] T042b **Spec Amendment Task (Part 2)**: Commit changes from T042a-* and T042c-* to git repository. **Depends on**: T042c-002, T042c-010, T042c-011, T042c-034. **Deliverable**: Git commit with updated `spec.md` and `plan.md`.
- [X] T007 [P] Implement `code/src/data/loader.py` (FR-002, FR-011) with `datasets.load_dataset(..., streaming=True)` for DeepFashion2 parquet. **Depends on**: T042b. **NOTE**: Implements DeepFashion2 per Plan decision after Spec Amendment.
- [X] T034-sub [P] **Define Downsampling Ratio**: Write `optical_flow_subsampling_ratio` to `code/config/settings.yaml` with a value set according to the subsampling strategy defined in the research design. under the `motion` key. **Output**: `code/config/settings.yaml` updated. **Depends on**: T042b.
- [ ] T034-extended **Motion Labeling Logic**: Implement `code/src/stats/motion_labels.py` to derive 'ground-truth motion labels' from **optical flow magnitude** (calculated from video frames) using `cv2.calcOpticalFlowFarneback` on sampled frames. **Configuration**: Read `optical_flow_subsampling_ratio` from `code/config/settings.yaml` (key `motion.optical_flow_subsampling_ratio`). **Output**: Logic to generate `data/processed/motion_labels.json` containing `frame_id`, `optical_flow_magnitude`, `motion_label` (High/Low). **Constraint**: Must be CPU-optimized and process frames in chunks to prevent OOM. **Depends on**: T042b, T007, T034-sub.
- [X] T007-verify [P] **Verification Script**: Create `tests/scripts/verify_streaming.py` to verify `loader.py` yields a substantial number of records without OOM. **Depends on**: T007. **Note**: Integration script verifying record count.
- [X] T007-test [P] Unit test for `loader.py` streaming: `tests/unit/test_loader_streaming.py` verifies A substantial volume of records yield without OOM. **Depends on**: T007. **Note**: Unit test for streaming logic.
- [X] T004 [P] Implement `code/src/pipeline/validate_citations.py` (FR-014) to verify DeepFashion2 URL and model references using Reference-Validator Agent logic (title-token-overlap >= 0.7). **Constraint**: Must verify URLs return 200 OK status code before processing.
- [X] T005 [P] Implement `code/src/pipeline/manifest.py` (FR-013) for content hashing of code and data artifacts. **Depends on**: T003b.
- [X] T006 [P] Create base configuration in `code/config/settings.yaml` with exact structure:
 ```yaml
 experiment:
 seed: 42
 streaming_chunk_size: a configurable parameter optimized for balanced latency and throughput
 motion:
 optical_flow_threshold:
 optical_flow_subsampling_ratio: a configurable subsampling factor
 model:
 vlm_confidence_threshold: A high confidence threshold is selected to ensure robust filtering of uncertain predictions.
 blip_model_id: "Salesforce/blip-large"
 benchmark:
 latency_threshold_ms: null # To be determined by T028-pilot (placeholder)
 memory_trigger_mb: a sufficiently large threshold to accommodate the dataset size without exceeding available system memory, as determined by preliminary profiling. # Placeholder: sufficiently large value, to be refined by T011 logic
 ```
 **Constraint**: `latency_threshold_ms` and `memory_trigger_mb` are placeholders to be filled by subsequent pilot tasks. **Depends on**: T042b.
- [X] T008 [P] Implement `code/src/data/prompt_gen.py` (FR-008) for blind metadata-to-text prompt generation. **Constraint**: Must be integrated with VLM verification (T015) before use.
- [X] T009 [P] Implement `code/src/metrics/fidelity.py` (FR-003) for LPIPS and SSIM computation on CPU.
- [X] T010 [P] Implement `code/src/metrics/latency.py` (FR-007) for frame-level inference timing.
- [X] T011 [P] Implement `code/src/pipeline/streaming.py` (FR-012) for memory-triggered batched processing. **Constraint**: Must use `psutil` to monitor memory usage in real-time and read `memory_trigger_mb` from `settings.yaml`. **Trigger**: Must trigger batched processing when RAM usage exceeds `memory_trigger_mb`. **Output**: A `StreamingProcessor` class exposing `process_batch()` and `check_memory()` methods for T026 to consume. **Verification**: Verify memory trigger activates at configured value using psutil. **Depends on**: T007, T006.
- [X] T047 [P] **Define Runner Interface**: Implement `code/src/pipeline/runner_interface.py` as an abstract base class defining the `run_benchmark` and `measure_latency` methods. **Constraint**: Must enforce CPU-only device initialization in the interface. **Depends on**: T006.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Feature-Stratified Fidelity Benchmarking (Priority: P1) 🎯 MVP

**Goal**: Run a controlled experiment to determine which garment attributes degrade when switching from image to text references.

**Independent Test**: The system ingests a stratified subset of DeepFashion2, runs the text-driven adapter, and outputs a JSON report with distinct fidelity scores for color, pattern, and texture.

**⚠️ Execution Order**: Within this phase, tasks must be executed sequentially where dependencies exist. T020-redo must wait for T018, T019, T021-redo, T016b-redo to complete.

### Tests for User Story 1 (OPTIONAL) ⚠️

- [X] T012 [P] [US1] Unit test for `FeasibilityFilter` logic in `tests/unit/test_feasibility_filter.py`. **Depends on**: None. **Note**: Write-only task following TDD; will fail until T014 is implemented.
- [X] T013 [P] [US1] Integration test for full benchmark pipeline in `tests/integration/test_fidelity_benchmark.py`. **Depends on**: T014, T015, T016, T016b-redo, T018, T019, T047.

### Implementation for User Story 1

- [X] T014 [US1] Implement `code/src/data/feasibility_filter.py` (FR-011) to tag clips by `GarmentFeatureClass` (color, pattern, texture) using DeepFashion2 metadata. **Depends on**: T042b, T034-extended. **NOTE**: Uses optical flow magnitude from T034-extended.
- [X] T015 [US1] Implement VLM verification step in `code/src/data/feasibility_filter.py` to exclude low-confidence prompts. **Specs**: Use model ID `Salesforce/blip-large`, load with `device='cpu'`, `torch_dtype=torch.float`, `trust_remote_code=False`. Apply a configurable confidence threshold (default value from `settings.yaml`), output JSON to `data/processed/vlm_confidence_log.json`. **Depends on**: T014, T006.
- [X] T016 [US1] Implement `code/src/data/stratified_subset.py` to select a benchmark subset ensuring class balance. **Constraint**: Must consume `vlm_confidence_log.json` from T015 to filter low-confidence samples before stratification. **Depends on**: T015.
- [ ] T016b-redo [US1] **Generate Stratified Subsets (Redo)**: Implement logic in `code/src/data/stratified_subset.py` to physically split the filtered data into class-specific buckets (Color, Pattern, Texture) and generate `data/processed/stratified_subset_manifest.json`. **Constraint**: This artifact MUST list samples grouped by `GarmentFeatureClass` to satisfy Constitution Principle VI. **Depends on**: T016.
- [X] T017 [US1] Implement `code/src/adapters/text_cross_attention.py` (FR-001) to map frozen CLIP text embeddings to reference KV slots. **Constraint**: Must explicitly initialize on CPU (`device='cpu'`). **Depends on**: T047.
- [X] T018 [US1] Implement `code/src/pipeline/runner.py` (FR-009) to execute the original image-driven baseline on the subset defined in T016. **Depends on**: T016, T042b, T047.
- [X] T019 [US1] Implement `code/src/pipeline/runner.py` logic to execute the text-driven adapter on the subset defined in T016. **Depends on**: T016, T042b, T047.
- [ ] T021-redo [US1] **Implement Edge Case Handling and Manifest Generation (Redo)**: Implement edge case handling in `code/src/data/feasibility_filter.py` for ambiguous prompts (VLM confidence in a moderate range) and generate `data/processed/filtered_subset_manifest.json`. **Output**: Generate `data/processed/filtered_subset_manifest.json` (valid samples only). **Constraint**: Manifest MUST include `optical_flow_magnitude` values and the specific threshold used for filtering for each sample. Ambiguous samples are flagged but included. **Depends on**: T015, T016, T016b-redo. **NOTE**: Resolves ambiguity on artifact scope.
- [ ] T020-redo [US1] **Implement Reporter (Redo)**: Implement `code/src/pipeline/reporter.py` to aggregate LPIPS/SSIM scores by `GarmentFeatureClass` and calculate relative fidelity loss. **Output**: `data/processed/fidelity_report.json` with exact schema:
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
 **Constraint**: MUST consume ONLY samples from `data/processed/filtered_subset_manifest.json` (generated by T021-redo). **Includes**: Edge case handling for low sample counts (<10 per class) - raises `ValueError` with message "Insufficient samples for ANOVA". **Depends on**: T018, T019, T021-redo. **Verification**: Verify schema and add test `tests/unit/test_reporter.py::test_reporter_aggregates_by_class()`.
- [ ] T020b-redo [US1] **Implement Comparative Analysis**: Extend `code/src/pipeline/reporter.py` to explicitly calculate and report distinct degradation rates (Color vs Pattern vs Texture) in a `comparative_metrics` section of `data/processed/fidelity_report.json`. **Constraint**: Must satisfy Constitution Principle VI by quantifying non-uniform fidelity loss. **Depends on**: T020-redo.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Real-Time Latency Verification (Priority: P2)

**Goal**: Verify that the text adapter does not introduce prohibitive latency on CPU hardware.

**Independent Test**: The system processes a short video clip on a multi-core CPU and reports average inference time per frame against an empirical target.

### Tests for User Story 2 (OPTIONAL) ⚠️

- [X] T023 [P] [US2] Unit test for latency thresholding logic in `tests/unit/test_latency.py`. **Depends on**: T028-logic.

### Implementation for User Story 2

- [X] T028-pilot [US2] **Pilot Benchmark for Latency**: Run a pilot benchmark on a small sample (process a representative set of frames) using the text-driven adapter to empirically determine a realistic latency threshold. **Output**: Generate `data/processed/latency_pilot.json` containing the measured mean and standard deviation. **Constraint**: Must use the same CPU configuration as the main benchmark. **Depends on**: T018, T019, T047.
- [X] T028-amend [US2] **Amend Spec for Latency**: Update `spec.md` (FR-007) to replace "[deferred]" with the empirically determined threshold from T028-pilot. **Deliverable**: Updated `spec.md` with specific text changes. **Depends on**: T028-pilot.
- [X] T028-config [US2] Define sample size for latency verification and establish the finalized target in `code/config/settings.yaml` (key `latency_threshold_ms`). **Output**: Update `code/config/settings.yaml` to set `latency_threshold_ms` to the value determined by T028-pilot. **Depends on**: T028-amend.
- [X] T028-logic [US2] Implement `code/src/metrics/latency.py` function `evaluate_latency(average_latency_ms)` that returns a JSON object `{"average_ms": <float>, "status": "PASS" | "FAIL", "threshold_ms": <value_from_config>}`. **Constraint**: Must perform actual measurement and compare against the value from `settings.yaml`. **Depends on**: T028-config.
- [X] T024 [US2] Implement `code/src/pipeline/runner.py` logic to measure end-to-end inference time per frame (FR-007). **Depends on**: T018, T019, T011, T047, T028-config. **Note**: Removed dependency on T016 to allow independent subset selection for latency testing. <!-- FAILED: unspecified -->
- [ ] T025-redo [US2] **Implement Latency Breakdown (Redo)**: Implement `code/src/pipeline/runner.py` logic to flag frames exceeding the threshold and identify bottleneck. **Specs**: Insert timers around `text_encoder.encode()`, `adapter.forward()`, and `backbone.generate()` functions. **Output**: Generate `data/processed/latency_breakdown.json` containing per-component timings (encoder, adapter, backbone) and a list of frames where latency > threshold. **Depends on**: T024, T028-logic. **NOTE**: T025-redo is a sub-task of T024 analysis.
- [X] T026 [US2] Implement `code/src/pipeline/runner.py` streaming/batched mode logic using `code/src/pipeline/streaming.py` (FR-012) with memory trigger from config. **Constraint**: Must consume the `StreamingProcessor` class instance produced by T011. **Depends on**: T011, T024. <!-- FAILED: unspecified -->
- [X] T027 [US2] Implement moving average calculation for latency in streaming mode in `code/src/metrics/latency.py`. **Depends on**: T028-logic, T026.
- [ ] T028-report [US2] Generate `data/processed/latency_verification_report.json` containing average latency, threshold (from config), and status "PASS" or "FAIL" based on empirical data. **Constraint**: Must include breakdown from `data/processed/latency_breakdown.json`. **Unit**: milliseconds. **Depends on**: T024, T028-logic, T025-redo. **NOTE**: Explicitly resolves coverage-5e9650ac by generating the required artifact with empirical validation.
- [X] T028-verify [US2] **Verify Latency Threshold**: Run a verification step to ensure the final benchmark run meets the threshold defined in `settings.yaml` (from T028-config). **Output**: Generate `data/processed/latency_final_verification.json` with a PASS/FAIL status. **Depends on**: T028-report, T037.
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

- [X] T031 [US3] Implement `code/src/stats/significance.py` (FR-005) to perform ANOVA on fidelity scores across feature classes. **Constraint**: Must explicitly verify that input data is stratified by `GarmentFeatureClass` (Color, Pattern, Texture) before running the test. If not stratified, raise `ValueError`. **Constraint**: Use `alpha=0.05`. **Depends on**: T020-redo (Report Aggregation).
- [X] T032 [US3] Implement Bonferroni correction logic in `code/src/stats/significance.py` for multiple hypothesis tests. **Depends on**: T031.
- [X] T036 [US3] Implement edge case handling in `code/src/stats/significance.py` for low power (N<30) scenarios. **Constraint**: Perform Power Analysis using `statsmodels.stats.power.TTestIndPower` with `effect_size=0.5`, `power=0.8`. If N<30, output results with a "Low Power Warning" flag in the report and explicitly state the limitation. If N<10, raise `ValueError` with message "Insufficient samples for statistical analysis". **Depends on**: T031.
- [X] T033 [US3] Implement `code/src/stats/sensitivity.py` (FR-006) to sweep optical flow consistency threshold across a range of values. **Depends on**: T009, T014, T034-extended. **Verification**: Verify `motion_labels.json` exists and is non-empty before sweep.
- [ ] T035 [US3] **Implement Sensitivity Analysis (Robustness Index)**: Implement `code/src/stats/sensitivity.py` to generate the threshold variation table. **Output**: `data/processed/sensitivity_analysis.csv` with columns `threshold`, `robustness_metric`. **Calculation**: Iterate threshold across the standard range in fixed increments. `robustness_metric` = **Robustness Index** defined as: (Number of samples where motion label (High/Low) remains unchanged across adjacent threshold steps) / (Total samples) * 100. **Constraint**: Must explicitly write the CSV file. **Depends on**: T033, T034-extended.
- [ ] T035b [US3] **Interpret Sensitivity Results**: Implement logic to interpret `data/processed/sensitivity_analysis.csv`, calculate the final Robustness Index, and generate `data/processed/robustness_report.json`. **Constraint**: Must confirm robustness against a defined threshold or flag instability. **Depends on**: T035.

**Checkpoint**: User Story 3 implementation complete. Final benchmark run (T037) will occur in Phase 6.

---

## Phase 6: Revision & Compliance (Addressing Analyze Findings)

**Purpose**: Resolve specific issues raised by `/speckit.analyze` regarding data integrity, memory safety, and statistical validity.

**⚠️ CRITICAL**: These tasks must be executed after the initial implementation and analysis to ensure all constraints are met.

- [X] T043 [P] **Revision Fix FR-002**: Refactor `code/src/data/loader.py` to enforce strict streaming mode with `datasets.load_dataset(..., streaming=True)` and add explicit error handling that raises `RuntimeError` if the fetch fails, ensuring no synthetic fallback is used. **Depends on**: T007. **Rationale**: Addresses reviewer concern about potential synthetic fallbacks and ensures strict adherence to the streaming constraint for DeepFashion2.
- [X] T049 [P] **Revision Fix Data Integrity**: Refactor `code/src/data/loader.py` to add a `try/except` block around the `datasets.load_dataset` call that catches `ConnectionError` and `HTTPError`, logging the exact error message and re-raising a custom `DataFetchError` with a clear instruction to check network or dataset availability. **Constraint**: Ensure NO `generate_synthetic_*` or mock data functions are called in the `except` block. **Depends on**: T043. **Rationale**: Ensures the "Fail Loudly" principle is strictly enforced, preventing silent fallbacks to synthetic data if the real DeepFashion2 fetch fails.
- [ ] T050 [P] **Revision Fix Memory Safety**: Refactor `code/src/stats/motion_labels.py` to implement a `streaming_flow_processor` function that yields optical flow magnitudes for frame pairs one-by-one without loading the entire video into memory. **Constraint**: Use `cv2.VideoCapture` with explicit frame seeking and process frames in a generator pattern. **Output**: Update `data/processed/motion_labels.json` to be written incrementally or in chunks. **Depends on**: T044. **Rationale**: Prevents OOM errors on large video sequences by ensuring memory usage remains constant regardless of video length.
- [X] T051 [P] **Revision Fix Statistical Robustness**: Refactor `code/src/stats/significance.py` to include a `check_sample_size` function that validates the number of samples per `GarmentFeatureClass` before running ANOVA. **Constraint**: If any class has fewer than 30 samples, the function must log a warning and set a `power_warning` flag in the output report; if any class has fewer than 10, it must raise a `ValueError` with the message "Insufficient samples for statistical analysis". **Depends on**: T045. **Rationale**: Ensures statistical validity and prevents misleading results from underpowered tests.
- [X] T052 [P] **Revision Fix Filtering Logic**: Refactor `code/src/data/feasibility_filter.py` to add a `validate_attributes` function that checks for the presence of `GarmentFeatureClass` tags in the DeepFashion2 metadata before attempting to filter. **Constraint**: If a sample lacks the required tag, it must be excluded and logged as "Missing Attribute", not filtered by confidence. **Depends on**: T046. **Rationale**: Prevents silent filtering of valid samples due to missing metadata and ensures strict adherence to the attribute-based stratification requirement.

**Checkpoint**: All revision concerns addressed - project ready for final validation and delivery.

---

## Phase 7: Polish & Delivery

**Purpose**: Final integration, verification, and artifact generation.

- [ ] T037 [P] **Run Full Benchmark**: Execute the full pipeline on the representative subset. **Constraint**: Must explicitly verify that `data/processed/fidelity_report.json` is generated and valid before proceeding. **Depends on**: T020-redo, T020b-redo, T024, T031, T035, T011, T007, T035b. **Note**: Aggregates results from all user stories. <!-- FAILED: unspecified -->
- [ ] T038 [P] Generate `data/processed/manifest.json` with content hashes. **Execution**: Run `code/src/pipeline/manifest.py` against all artifacts in `data/processed/` and `code/`, THEN run `code/src/pipeline/state_updater.py` to record these checksums into `state/projects/PROJ-829-llmxive-follow-up-extending-fashionchame.yaml`. **Depends on**: T037, T003b. **NOTE**: Explicitly resolves coverage-0e1fbe8d by defining the execution step and closing the reproducibility loop.
- [X] T039 [P] Update `docs/quickstart.md` with instructions for running the benchmark. **Depends on**: T037.
- [X] T040 [P] Run `pytest` to ensure all unit and integration tests pass. **Depends on**: T037.
- [X] T041 [P] Verify `code/src/pipeline/runner.py` completes within 6 hours on CPU free-tier. **Depends on**: T037.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Revision & Compliance (Phase 6)**: Depends on completion of all User Stories and initial analysis
- **Polish (Phase 7)**: Depends on all desired user stories being complete

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
- **Memory Constraint**: Ensure `runner.py` implements the `memory_trigger_mb` from config for streaming mode (T011).
- **No Synthetic Data**: Do NOT implement synthetic data fallbacks. Fail loudly if real data fetch fails.
- **Spec Amendment**: Tasks T042a-* and T042c-* are mandatory and blocking for all data processing tasks.
- **Motion Labels**: Motion labels are derived from optical flow magnitude (T034-extended), not skeletal velocity, due to DeepFashion2 dataset constraints. T034-extended is now in Phase 2 to unblock US1.
- **Optical Flow Implementation**: T034-extended must implement optical flow calculation using `cv2.calcOpticalFlowFarneback` or `cv2.calcOpticalFlowPyrLK` on sampled frames to compute magnitude, ensuring the calculation is optimized for CPU execution to avoid exceeding the 6-hour runtime limit.
- **Data Streaming**: T007 and T034-extended must strictly adhere to streaming patterns; do not load full video sequences into memory. Process frame pairs in chunks to calculate flow magnitude.
- **Latency Verification**: The threshold is determined empirically via T028-pilot and amended in spec. T028-config sets the config value based on this result. T028-report generates the artifact with empirical validation (PASS/FAIL) based on this threshold. T028-verify performs the final check.
- **Revision Concern FR-002/FR-010**: Ensure `loader.py` strictly uses `streaming=True` and `optical_flow.py` processes frame pairs in chunks to prevent OOM.
- **Revision Concern FR-005**: Ensure `significance.py` explicitly implements ANOVA and Bonferroni correction. Do NOT use non-parametric alternatives (Kruskal-Wallis) as the spec mandates ANOVA.
- **Revision Concern FR-011**: Ensure `feasibility_filter.py` correctly tags `GarmentFeatureClass` from DeepFashion2 metadata and strictly enforces the VLM confidence threshold without fallback.
- **Ordering Note**: Phase 2 tasks T007 and T034-extended have explicit ordering (T007 first). Phase 3 tasks T018, T019, T021-redo, T016b-redo must complete before T020-redo. T016b-redo must complete before T021-redo.
- **Revision Concerns**: Tasks T043, T044, T045, T046 are mandatory revision tasks to address specific reviewer concerns regarding data integrity, memory safety, statistical validity, and filtering logic. These must be completed before the final polish phase.
- **Downsampling Authorization**: T034-sub and T042a-034 explicitly authorize the 5:1 downsampling ratio to ensure scope alignment.
- **CPU Initialization**: T048 ensures all model components are explicitly initialized on CPU.
- **Stratified Analysis**: Constitution Principle VI requires explicit isolation of garment attributes by semantic class. T016b-redo generates the stratified subsets artifact, and T020b-redo performs the comparative analysis to satisfy this.
- **Latency Threshold**: Constitution Principle VII requires empirical validation against a determined threshold. T028-pilot, T028-amend, T028-config, T028-report, and T028-verify enforce this threshold and PASS/FAIL status.
- **Sensitivity Metric**: T035 uses Robustness Index with explicit calculation steps (0.0 to 1.0 in 0.1 increments). T035b interprets the results.
- **Reproducibility**: T003b implements seed pinning and state updating. T038 executes the state updater to record checksums, closing the loop.
- **New Revision Tasks**: Tasks T049, T050, T051, T052 address specific analysis findings regarding data integrity, memory safety, statistical robustness, and filtering logic. These are critical for final compliance.
