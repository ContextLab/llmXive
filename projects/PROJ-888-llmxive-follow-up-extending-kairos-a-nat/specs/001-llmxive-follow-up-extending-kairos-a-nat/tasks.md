# Tasks: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

**Input**: Design documents from `/specs/001-llmxive-kairos-discrete-scaling/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- Paths shown below assume single project structure per `plan.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 [P] Initialize project structure: Create `projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat/`, `code/`, `tests/`, `data/`, `state/`, `docs/` directories. **Verification**: Run `tree -L 2 > state/directory_listing.txt` and confirm file exists with non-zero size. <!-- SKIPPED: non-mapping output -->
- [X] T001e [P] Initialize `requirements.txt` with pinned versions: torch (CPU, pin to latest stable), numpy, pandas, datasets, scikit-learn, pyyaml, pytest, h5py, arviz (use `==` for exact pinning), statsmodels, simr
- [ ] T001f [P] Create `README.md` with project overview and quickstart instructions. **Verification**: Task must output a file existence check and first 5 lines of content.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase includes shared infrastructure and data schemas only.
**Ordering Note**: T004 (Config) must be completed before T005-T008.

- [ ] T004 [P] Create `code/config.py` for seeds, paths, quantization levels [, 6, 8, 16] bits, and noise std devs. **Verification**: Run `code/utils/validate_config.py` and assert that all quantization levels [4, 6, 8, 16] exist in the config object.
- [X] T005 [P] Implement resource monitoring utilities in `code/utils/monitor.py` (RAM, CPU, time tracking)
- [X] T006 [P] Setup error handling and logging infrastructure in `code/utils/logging.py`
- [X] T007 Create base data schemas and validation logic in `code/data/schema.py` (DiscreteStateVector, ErrorMetric)
- [ ] T008 Configure checkpointing mechanism for graceful exit at h limit in `code/utils/checkpoint.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 0.5: Power Analysis (Pre-Study Requirement)

**Purpose**: Determine sample size N before data collection to satisfy FR-009.

- [ ] T004a [P] Implement `code/analysis/power_analysis.py` to perform a priori power analysis (using `simr` or manual simulation) targeting Cohen's d=0.5, Power=0.8. Output `results/power_analysis_report.json`. **Constraint**: Must run BEFORE any data collection or model training. **Verification**: Assert `results/power_analysis_report.json` exists with calculated N and a moderate effect size.

---

## Phase 3: User Story 1 - Data Construction and Quantization Pipeline (Priority: P1) 🎯 MVP

**Goal**: Convert continuous LIBERO dataset into discrete, JSON-serialized state vectors with configurable quantization and noise injection.

**Independent Test**: The pipeline can be tested by running the conversion script on a subset of LIBERO data, verifying that the output JSON files contain discrete integer values within the specified bit-depth ranges, and confirming that the total dataset size fits within the available RAM constraint. [UNRESOLVED-CLAIM: c_a98dff8d — status=not_enough_info]

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for quantized JSON schema in `tests/contract/test_quantized_schema.py`: Implement function `test_quantized_schema_4bit` asserting `all(0 <= x <= 15 for x in data)`.
- [ ] T010 [P] [US1] Integration test for full download-quantize-noise pipeline in `tests/integration/test_data_pipeline.py`: Specify input subset size (N=50 episodes), output path `data/processed/test_subset.json`, and assert `output_file_size < 100MB` and `no NaN values`.

### Implementation for User Story 1

- [ ] T014a [US1] Define interface for data pipeline components in `code/main.py` (Interface Definition): Define the signatures for download, quantize, and noise functions. **Ordering**: Must be implemented before T011-T013.
- [ ] T011 [US1] Implement `code/data/download_libero.py` to fetch HDF5 from verified HuggingFace URL using `datasets.load_dataset(..., streaming=True)` to handle shards sequentially. **Constraint**: MUST stream data in chunks; MUST NOT load full dataset into RAM. **Constraint**: If fetch fails, raise an exception and exit with code 1. NO synthetic fallback. **Verification**: Assert peak RAM usage < 2GB during processing and chunk size consistency. [UNRESOLVED-CLAIM: c_bf3fba20 — status=not_enough_info]
- [ ] T040a [US1] Implement header-only size validator in `code/main.py` (distinct step): MUST run AFTER T011 downloads the file. Validates full dataset size via header-only read to ensure < 7GB RAM constraint before processing.
- [ ] T040b [US1] Implement sample subset runner in `code/main.py` (distinct step): Run pipeline on a sample subset with logging after validation passes.
- [ ] T012 [US1] Implement `code/data/quantize.py` to convert HDF to discrete JSON vectors for quantization levels at varying bit precisions (per FR-001). **Constraint**: Ensure bin clamping. **Verification**: Assert output values are integers within [, 2^bit_depth - 1] for the specific bit depth passed.
- [ ] T013 [US1] Implement `code/data/noise.py` to inject Gaussian noise with a standard deviation scaled proportionally to the quantization step applied to continuous data before quantization, and clamp to valid discrete bins. **Verification**: Assert noise injection matches formula and values remain within discrete bins.
- [ ] T015 [US1] Implement `code/data/validator.py` to detect degenerate cases (e.g., 1-bit collapse) and raise an exception with exit code 1. **Verification**: Generate `tests/unit/test_1bit_collapse.py` that asserts the script exits with code 1 when 1-bit quantization is attempted.
- [ ] T016 [US1] Add logging for quantization levels, noise seeds, and peak RAM usage per task
- [ ] T014b [US1] Implement `code/main.py` orchestration logic to coordinate download → quantize → noise pipeline with memory monitoring. **Definition First**: This task implements the logic defined in T014a. **Ordering**: Must be placed after T011-T013.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Only Model Training and Inference (Priority: P2)

**Goal**: Load pre-trained Kairos weights, replace visual encoder with fixed discrete projection, and execute training/inference on CPU-only environment.

**Independent Test**: The model can be tested by initiating a training run with a fixed random seed, verifying that the loss trend shows convergence, confirming that the total training time is a target ≤ 4 hours (graceful exit if > 6h), and confirming that inference on a long sequence completes without CUDA errors or out-of-memory exceptions. [UNRESOLVED-CLAIM: c_696940eb — status=not_enough_info]

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`: Implement function `test_model_output_shape` asserting that the output shape corresponds to the batch dimension, a sequence length, and the dimensionality.
- [ ] T041 [P] [US2] Integration test for CPU-only training loop in `tests/integration/test_cpu_training.py`

### Implementation for User Story 2

- [ ] T018 [US2] Download, verify checksum, and cache pre-trained Kairos weights from verified HuggingFace repo to `data/models/kairos_base.pt`. **Pre-fetch Validation**: MUST validate file size before download to ensure < 7GB RAM constraint. **Constraint**: If fetch fails, raise an exception and exit with code 1. DO NOT train from scratch.
- [ ] T019 [P] [US2] Implement `code/models/kairos_adapter.py` to load pre-trained weights from `data/models/kairos_base.pt` (T018) and replace visual encoder with fixed discrete projection
- [ ] T020 [US2] Implement `code/models/training_loop.py` for CPU-only training with epoch checkpointing and 6h graceful exit. **Ordering**: Must precede inference tasks.
- [ ] T021 [US2] Implement inference engine in `code/models/inference.py` for multiple time horizons including short, medium, and long-term prediction steps (per Constitution Principle VII and FR-004). **Ordering**: Must follow training.
- [ ] T022 [US2] Invoke and configure `code/utils/monitor.py` to enforce < 7GB RAM and log latency per step. **Strictly depends on T005 completion**.
- [ ] T022b [US2] Implement aggregation logic to write `results/resource_profile.json` with keys `peak_ram_gb`, `total_time_h`, and `cpu_utilization_avg`. **Strictly depends on T022**.
- [ ] T023 [US2] Add logic to detect and prevent CUDA/bitsandbytes errors (fail loudly if detected)
- [ ] T024 [US2] Add logging for training convergence (epoch loss change < 5%) and inference latency
- [ ] T044 [US2] Implement explicit "CPU-Only" assertion in `code/models/kairos_adapter.py` that raises `RuntimeError` if any CUDA device is detected or if `device="cuda"` is passed, ensuring strict adherence to the CPU constraint.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Stability Analysis and Threshold Mapping (Priority: P3)

**Goal**: Compute MSE, cumulative error growth, and perform statistical validation to identify minimum information density thresholds.

**Independent Test**: The analysis can be tested by running the evaluation script on the model outputs, generating the error-vs-bandwidth curve, and verifying that the statistical tests (LMM) produce valid p-values and confidence intervals.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Contract test for error metric schema in `tests/contract/test_error_metrics.py`: Implement function `test_error_metrics_schema` asserting `keys include [mse, mse_ratio, cumulative_error_rate, p_value, horizon, is_significant, stability_claim_framing]`.
- [ ] T026 [P] [US3] Integration test for statistical analysis pipeline in `tests/integration/test_stability_analysis.py`: Specify running LMM, expected p-value range, and exact output path `results/stats_results.json`.

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/analysis/run_baseline.py` to generate continuous visual-modality baseline run and save metrics to `results/baseline_metrics.json`. **Ordering**: Must precede metrics calculation.
- [ ] T027 [US3] Implement `code/analysis/metrics.py` to calculate MSE normalized by state space dimensionality, cumulative error growth, and ErrorAccumulationRate (slope of MSE vs time) over multiple horizons (100, 500, 1000) (per Constitution Principle VII and FR-004). **Ordering**: Must follow baseline run (T033) and inference (T021).
- [ ] T028 [US3] Implement `code/analysis/stats.py` to perform **Linear Mixed-Effects Model (LMM)** with 'episode_id' as a random effect and 'modality' as a fixed effect. Use block-bootstrap as a mandatory fallback if LMM fails. Perform statistical validation on multiple independent runs with different noise seeds (per FR-005). Output `results/stats_results.json`.
- [ ] T029a [US3] Implement sensitivity analysis sweep across **bit-width increments** 6, 8, and 16 bits and report variation in headline error rates. **Constraint**: Include 6-bit as per FR-001.
- [ ] T029b [US3] Identify and report the specific quantization threshold where the MSE ratio exceeds the **upper bound of the confidence interval** derived from the LMM results (using metrics from `results/stats_results.json`). **Strictly depends on T029a, T027, and T028**.
- [ ] T030 [US3] Implement visualization to generate error-vs-bandwidth curve plot
- [ ] T050 [US3] Implement visualization to generate threshold map visualization
- [ ] T031 [US3] Add logic to explicitly frame stability claims as "relative degradation" against continuous baseline
- [ ] T032 [US3] Add logging for p-values, confidence intervals, and stability boundary identification
- [ ] T032b [US3] Implement logic to generate the `stability_claim_framing` field in the final results JSON, ensuring it contains the numeric `mse_ratio` or `relative_degradation`. **Strictly depends on T029b**.
- [ ] T045 [US3] Implement block-bootstrap method in `code/analysis/stats.py` as the mandatory fallback if LMM fails. **Constraint**: Do NOT implement t-test or Levene's test. The fallback must account for temporal autocorrelation. **Verification**: Assert that the bootstrap method produces valid confidence intervals when LMM is unavailable.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Documentation updates in `README.md` and `docs/`
- [ ] T034a [P] Run linting and formatting (ruff/black) on all code
- [ ] T034b [P] Refactor code to remove duplication and improve readability
- [ ] T034c [P] Update documentation based on final implementation
- [ ] T035a [P] Optimize data loading using streaming/chunking to reduce RAM peak
- [ ] T035b [P] Optimize batch sizes to balance throughput and memory usage
- [ ] T035c [P] Profile memory usage and document optimization results
- [ ] T036 [P] Additional unit tests in `tests/unit/`
- [ ] T037 Security hardening (dependency audit)
- [ ] T038 Run `quickstart.md` validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Power Analysis (Phase 0.5)**: Depends on Foundational (Phase 2) - BLOCKS data collection
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (DiscreteStateVector)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output (predictions)

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
Task: "Contract test for quantized JSON schema in tests/contract/test_quantized_schema.py"
Task: "Integration test for full download-quantize-noise pipeline in tests/integration/test_data_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/download_libero.py"
Task: "Implement code/data/quantize.py"
Task: "Implement code/data/noise.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 0.5: Power Analysis (Determine N)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add Power Analysis → Determine N
3. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
4. Add User Story 2 → Test independently → Deploy/Demo
5. Add User Story 3 → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Critical Ordering Notes

- **T014a -> T011**: T014a (Interface Definition) logically precedes T011-T013.
- **T011 -> T014b**: T014b (Orchestration Logic) strictly depends on T011-T013 being implemented.
- **T005 -> T022**: T022 (Integrate Monitor) strictly depends on T005 (Create Monitor) completion.
- **T033 -> T027**: T027 (Metrics) strictly depends on T033 (Baseline) completion.
- **T021 -> T027**: T027 (Metrics) strictly depends on T021 (Inference) completion.
- **T028 -> T029b**: T029b (Threshold) strictly depends on T028 (Stats/LMM), T029a (Sweep), and T027 (Metrics).
- **T011 (Streaming)**: T011 now includes streaming logic; T043 has been merged into T011.
- **T004 -> T005-T008**: T004 (Config) must be completed before T005-T008.
- **T004a -> T011**: Power Analysis (T004a) must be completed before data download (T011) to determine N.
- **T015**: T015 generates `tests/unit/test_1bit_collapse.py` as part of implementation.
- **T045**: T045 implements block-bootstrap only; no t-test fallback.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Data Hygiene**: All data loaders MUST fail loudly if real data fetch fails; NO synthetic fallbacks.
- **Resource Constraints**: All training/inference tasks MUST enforce reasonable RAM and time limits via checkpointing.
- **CPU-Only**: All model tasks MUST run on CPU without CUDA/bitsandbytes dependencies.
- **Constitution VII & FR-004 Supremacy**: Error metrics MUST be normalized by state space dimensionality and calculated over **100, 500, and 1000 steps**.
- **FR-001 Supremacy**: Quantization levels MUST be **4-bit, 6-bit, 8-bit, and 16-bit**.
- **FR-005**: Statistical validation MUST use **Linear Mixed-Effects Model (LMM)** or block-bootstrap.
- **FR-008**: Stability claims MUST be framed as relative degradation against a continuous baseline.
- **SC-001**: Sensitivity analysis MUST calculate and report the specific numerical threshold value where MSE exceeds the baseline increase (dynamic calculation).
- **Task T018**: NO fallback to training from scratch. If weights missing, fail hard.
- **Task T040a**: Must run AFTER T011 (Download) to ensure the file exists for header validation.
- **Task T011**: MUST use `streaming=True` with `datasets` or `h5py` iteration to prevent OOM on large datasets.
- **Task T044**: Must raise an error immediately if `torch.cuda.is_available()` returns True and `device` is not explicitly forced to "cpu".
- **Task T045**: Must log the result of the bootstrap method and the subsequent choice of statistical test (LMM vs Bootstrap) in the final report.
- **Task T029b**: Explicitly calculates threshold where MSE ratio exceeds upper bound of 95% CI to resolve SC-001.
- **Task T004a**: Must target Cohen's d=0.5 as per FR-009.
- **Task T013**: Must use exact formula `std dev = 0.1 * quantization_step`.