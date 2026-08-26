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

- [X] T001 [P] Initialize project directory structure: Execute `scripts/scaffold_project.sh` to create `projects/PROJ-888-llmxive-follow-up-extending-kairos-a-nat/`, `code/`, `tests/`, `data/`, `state/`, `docs/`, and `results/` directories. **Verification**: Script must generate `verify_structure.json` listing all created directories.
- [X] T001e [P] Initialize `requirements.txt` with pinned versions: torch (CPU, pin to latest stable), numpy, pandas, datasets, scikit-learn, pyyaml, pytest, h5py, arviz, statsmodels, simr (use `==` for exact pinning)
- [ ] T001f [P] Create `README.md` with project overview and quickstart instructions. **Verification**: Task must verify file contains header `# llmXive follow-up` and output first 5 lines.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase includes shared infrastructure and data schemas only.
**Ordering Note**: T004 (Config) must be completed before T005-T008.

- [X] T004 Create `code/config.py` for seeds, paths, quantization levels [4, 6, 8, 16] bits, and noise std devs. **Verification**: Task must execute `scripts/validate_config.py` and output `logs/config_validation.log`.
- [X] T005 [P] Implement resource monitoring utilities in `code/utils/monitor.py` (RAM, CPU, time tracking)
- [X] T006 [P] Setup error handling and logging infrastructure in `code/utils/logging.py`
- [X] T007 Create base data schemas and validation logic in `code/data/schema.py` (DiscreteStateVector, ErrorMetric)
- [ ] T008 Configure checkpointing mechanism for graceful exit at h limit in `code/utils/checkpoint.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 0.5: Power Analysis (New)

**Purpose**: Determine sample size N for statistical power before data collection

- [ ] T004a [P] Implement `code/analysis/power_analysis.py` to perform LMM-based power simulation (using `simr` logic) for Cohen's d=0.5, Power=0.8. **Output**: `results/power_analysis_report.json` with effect size, alpha, beta, and calculated N. **Verification**: Task must output the JSON file and print the calculated N.

**Checkpoint**: Power analysis complete - sample size N is determined

---

## Phase 3: User Story 1 - Data Construction and Quantization Pipeline (Priority: P1) 🎯 MVP

**Goal**: Convert continuous LIBERO dataset into discrete, JSON-serialized state vectors with configurable quantization and noise injection.

**Independent Test**: The pipeline can be tested by running the conversion script on a subset of LIBERO data, verifying that the output JSON files contain discrete integer values within the specified bit-depth ranges, and confirming that the total dataset size fits within the available RAM constraint. [UNRESOLVED-CLAIM: c_b5a9e700 — status=not_enough_info]

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Contract test for quantized JSON schema in `tests/contract/test_quantized_schema.py`: Implement function `test_quantized_schema_4bit` asserting `all(0 <= x <= 15 for x in data)`.
- [ ] T010 [P] [US1] Integration test for full download-quantize-noise pipeline in `tests/integration/test_data_pipeline.py`: Specify input subset size (N=50 episodes), output path `data/processed/test_subset.json`, and assert `output_file_size < 100MB` and `no NaN values`.

### Implementation for User Story 1

- [X] T014a [P] [US1] Implement `code/main.py` orchestration interface: Define the interface and dependencies for the data pipeline (download, derive, noise, quantize). **Ordering**: Must be implemented BEFORE T011-T013 to define the contract they fulfill. **Verification**: Task must output a validation log confirming interface definition.
- [ ] T011 [US1] Implement `code/data/download_libero.py` to fetch HDF5 from verified HuggingFace URL (NO synthetic fallback). **Constraint**: MUST fetch only the N=50 episode subset to satisfy RAM constraints. [UNRESOLVED-CLAIM: c_17756eb9 — status=not_enough_info] **Verification**: Task must output `data/raw/libero_subset.h5` and log.
- [ ] T043 [US1] Implement streaming chunk processor in `code/data/stream_loader.py` to handle LIBERO HDF5 shards sequentially without loading full dataset into RAM, adhering to the "STREAM real data" rule. **Constraint**: MUST use `h5py` streaming or `datasets.load_dataset(..., streaming=True)` pattern; MUST NOT fall back to synthetic data if stream fails. **Verification**: Assert chunked output integrity matches full dataset hash. **Ordering**: Integrated into T011/T012a flow.
- [ ] T040 [US1] Implement `code/main.py` validation and sampling: Validate full dataset size via header-only read (T011 output) and run pipeline on a sample subset. **Ordering**: Must run AFTER T011 downloads the file. **Verification**: Task must output `logs/validation_run.log`.
- [ ] T012a [US1] Implement `code/data/velocity_deriver.py` to perform finite differencing on *continuous* position data to derive velocity fields **BEFORE** quantization. **Constraint**: MUST operate on raw float32 data. **Verification**: Assert output velocity fields match continuous ground truth derivation within tolerance < 1e-4. [UNRESOLVED-CLAIM: c_a8cde9a0 — status=not_enough_info]
- [ ] T013 [US1] Implement `code/data/noise.py` to inject Gaussian noise (std dev = 0.1 * quantization_step) into continuous states **BEFORE** quantization to create a parallel "noise-only" dataset, modeling telemetry instability distinct from quantization error. **Verification**: Assert noise is added to continuous data and clamped after quantization. **Ordering**: Must precede T012.
- [ ] T012 [US1] Implement `code/data/quantize.py` to convert HDF to discrete JSON vectors for quantization levels at varying bit precisions (per FR-001). **Constraint**: Ensure bin clamping. **Verification**: Assert output values are integers within a non-negative range bounded by the bit depth passed.
- [ ] T015 [US1] Implement `code/data/validator.py` to detect degenerate cases (e.g., 1-bit collapse) and flag as "Invalid Data". **Verification**: Task must output a test case `tests/unit/test_validator.py::test_1bit_collapse` that verifies the script raises an exception and exits with code 1.
- [ ] T016 [US1] Implement logging in `code/main.py` to record quantization level, noise seed, and peak RAM usage to `logs/quantization_run.log` in JSON format.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Only Model Training and Inference (Priority: P2)

**Goal**: Load pre-trained Kairos weights, replace visual encoder with fixed discrete projection, and execute training/inference on CPU-only environment.

**Independent Test**: The model can be tested by initiating a training run with a fixed random seed, verifying that the loss trend shows convergence, confirming that the total training time is a target ≤ 4 hours (graceful exit if > 6h), and confirming that inference on a long sequence completes without CUDA errors or out-of-memory exceptions. [UNRESOLVED-CLAIM: c_543d6d63 — status=not_enough_info]

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T017 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`: Implement function `test_model_output_shape` asserting that the output shape corresponds to the batch dimension, a sequence length, and the dimensionality.
- [ ] T041 [P] [US2] Integration test for CPU-only training loop in `tests/integration/test_cpu_training.py`

### Implementation for User Story 2

- [ ] T018 [US2] Download, verify checksum, and cache pre-trained Kairos weights from verified HuggingFace repo to `data/models/kairos_base.pt`. **Constraint**: MUST validate file size before download to ensure < 7GB RAM constraint. [UNRESOLVED-CLAIM: c_344e8028 — status=not_enough_info] **Note**: This task strictly handles model weights; dataset subset constraints apply to training data (T011), not weights. **Verification**: Task must output `data/models/kairos_base.pt` and a checksum log.
- [ ] T018b [US2] Implement `code/models/baseline_trainer.py` to train the **Fair Baseline**: Load weights (T018), replace visual encoder with *heuristic-initialized* discrete projection layer, and fine-tune on **quantized ground truth**. **Fallback Logic**: If T018 weights are missing or invalid, this script MUST implement the fallback: initialize from scratch using heuristic initialization (matching continuous stats), train for MIN_EPOCHS=5, and verify convergence (loss change < 5% over 3 consecutive epochs). If convergence fails, flag output as `UNTRAINED_BASELINE` and EXCLUDE from relative degradation metrics (FR-008). Log the fallback trigger explicitly. **Verification**: Output `results/baseline_metrics.json`.
- [ ] T019 [P] [US2] Implement `code/models/kairos_adapter.py` to load pre-trained weights from `data/models/kairos_base.pt` (T018) or initialize heuristic weights if fallback triggered (baseline only), and replace visual encoder with fixed discrete projection
- [ ] T022 [US2] Invoke and configure `code/utils/monitor.py` to enforce < 7GB RAM and log latency per step. **Strictly depends on T005 completion**. **Ordering**: Must precede T020 and T021 to ensure monitoring is active during execution.
- [ ] T020 [US2] Implement `code/models/training_loop.py` for CPU-only training with epoch checkpointing and a graceful exit mechanism. **Ordering**: Must precede inference tasks.
- [ ] T021 [US2] Implement inference engine in `code/models/inference.py` for multiple time horizons including short, medium, and long-term prediction (per Constitution Principle VII and FR-004). **Ordering**: Must follow training.
- [ ] T023 [US2] Add logic to detect and prevent CUDA/bitsandbytes errors (fail loudly if detected)
- [ ] T024 [US2] Add logging for training convergence (epoch loss change < 5%) and inference latency
- [ ] T044 [US2] Implement explicit "CPU-Only" assertion in `code/models/kairos_adapter.py` that raises `RuntimeError` if any CUDA device is detected or if `device="cuda"` is passed, ensuring strict adherence to the CPU constraint.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Stability Analysis and Threshold Mapping (Priority: P3)

**Goal**: Compute MSE, cumulative error growth, and perform statistical validation to identify minimum information density thresholds.

**Independent Test**: The analysis can be tested by running the evaluation script on the model outputs, generating the error-vs-bandwidth curve, and verifying that the statistical tests (LMM) produce valid p-values and confidence intervals.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Contract test for error metric schema in `tests/contract/test_error_metrics.py`: Implement function `test_error_metrics_schema` asserting `keys include [mse, p_value, horizon]`.
- [ ] T026 [P] [US3] Integration test for statistical analysis pipeline in `tests/integration/test_stability_analysis.py`: Specify running **Linear Mixed-Effects Model (LMM)**, expected p-value range, and exact output path `data/results/stats.json`.

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/analysis/run_baseline.py` to generate continuous visual-modality baseline run. **Requirement**: MUST use a **heuristic-initialized** projection layer (similar to discrete model) and **fine-tune** it on quantized ground truth to isolate modality shift. **Verification**: Assert initialization parameters (mean/std) match the discrete arm. [UNRESOLVED-CLAIM: c_c75c2faf — status=not_enough_info] Save metrics to `data/results/baseline_metrics.json`. **Ordering**: Must precede metrics calculation.
- [ ] T027 [US3] Implement `code/analysis/metrics.py` to calculate **Total Mean Squared Error (MSE)** (raw) between predicted and ground-truth sequences. **Constraint**: MUST NOT subtract a theoretical "Quantization Noise Floor"; report Total MSE as the primary comparison metric. Normalization by state space dimensionality is allowed for internal calculation but the reported metric for thresholding must be Total MSE. **Ordering**: Must follow baseline run (T033) and inference (T021).
- [ ] T045 [US3] Implement Levene's test for equal variance check in `code/analysis/stats.py` before selecting LMM vs block-bootstrap, ensuring statistical validity of the chosen test method. **Ordering**: Must precede T028.
- [ ] T028 [US3] Implement `code/analysis/stats.py` to perform **Linear Mixed-Effects Model (LMM)** as the **PRIMARY** validation method (per FR-005). Use 'episode_id' as a random effect and 'modality' as a fixed effect to account for temporal autocorrelation. Perform statistical validation on multiple independent runs with different noise seeds. [UNRESOLVED-CLAIM: c_2eb52f46 — status=not_enough_info] **Constraint**: If LMM fails, fall back to block-bootstrap. **Output**: `stats_results.json` with p-values, confidence intervals, and model coefficients.
- [ ] T029a [US3] Implement sensitivity analysis sweep across **bit-width increments** including representative low, medium, and high values and report variation in headline error rates. **Constraint**: Include 6-bit as per Spec FR-006 and SC-005.
- [ ] T029b [US3] Identify and report the specific quantization threshold where the Total MSE ratio (Discrete/Continuous) exceeds the **upper bound of the 95% confidence interval for the null hypothesis (ratio=1)**. **Strictly depends on T029a and T027**. **Output**: Write the numeric threshold value to `results/stability_threshold.json`. **Verification**: Task must output the JSON file with the specific numeric value.
- [ ] T030 [US3] Implement visualization to generate error-vs-bandwidth curve plot
- [ ] T050 [US3] Implement visualization to generate threshold map visualization
- [ ] T031 [US3] Add logic to explicitly frame stability claims as "mse_ratio" OR "relative_degradation" and output the **numeric** value into the `stability_claim_framing` field in the final results JSON (per FR-008).
- [ ] T032 [US3] Add logging for p-values, confidence intervals, and stability boundary identification

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
- **Power Analysis (Phase 0.5)**: Depends on Foundational - BLOCKS User Stories
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
Task: "Implement code/data/velocity_deriver.py"
Task: "Implement code/data/noise.py"
Task: "Implement code/data/quantize.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 0.5: Power Analysis
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

- **T014a -> T011 -> T040 -> T012a -> T013 -> T012 -> T015**: T014a (Orchestration Interface) must precede implementation. T013 (Noise) MUST precede T012 (Quantization). T012a (Velocity) MUST precede T012. T015 (Validation) must follow T012.
- **T005 -> T022**: T022 (Integrate Monitor) strictly depends on T005 (Create Monitor) completion.
- **T033 -> T027**: T027 (Metrics) strictly depends on T033 (Baseline) completion.
- **T021 -> T027**: T027 (Metrics) strictly depends on T021 (Inference) completion.
- **T028 -> T029b**: T029b (Threshold) strictly depends on T028 (Stats/LMM), T029a (Sweep), and T027 (Metrics).
- **T011 (Streaming)**: T011 now includes streaming logic; T043 has been merged into T011.
- **T004 -> T005-T008**: T004 (Config) must be completed before T005-T008.
- **Horizons**: T021 and T027 MUST use horizons **100, 500, and 1000** steps.
- **Bit-widths**: Ta MUST use bit-widths **4, 6, 8, and 16**.
- **Baseline**: T033 MUST use **heuristic initialization** and **fine-tuning**, not a frozen model.
- **Threshold**: T029b MUST use the **95% CI upper bound** for the null hypothesis, not a hardcoded 1.2 multiplier.
- **T045 -> T028**: T045 (Levene's Test) MUST precede T028 (LMM) to select the correct statistical test.
- **T022 -> T020**: T022 (Monitor) MUST precede T020 (Training) to ensure monitoring is active.
- **T018 -> T018b**: T018 (Download Weights) must complete before T018b (Baseline Training) can attempt to load them. T018b handles the fallback logic if T018 fails.

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
- **Constitution VII & FR-004 Supremacy**: Error metrics MUST be normalized by state space dimensionality and calculated over **100, 500, and 1000 steps**. The reported metric for thresholding MUST be **Total MSE** (raw).
- **FR-001 Supremacy**: Quantization levels MUST be **4-bit, 6-bit, 8-bit, and 16-bit**.
- **FR-005**: Statistical validation MUST use **Linear Mixed-Effects Model (LMM)** or block-bootstrap.
- **FR-008**: Stability claims MUST be framed as "mse_ratio" OR "relative_degradation" with a **numeric** value in the `stability_claim_framing` field.
- **SC-001**: Sensitivity analysis MUST calculate and report the specific numerical threshold value where MSE exceeds the baseline increase (dynamic calculation using a high-confidence interval).
- **Task T018/T018b**: T018 strictly downloads weights. T018b handles the fallback training logic if weights are missing, using `code/models/baseline_trainer.py`. Fallback must meet convergence criteria (MIN_EPOCHS=5, loss change < 5% over 3 epochs) and be excluded from relative degradation metrics. [UNRESOLVED-CLAIM: c_e687a172 — status=not_enough_info] Fallback MUST use **heuristic initialization**.
- **Task T040**: Must run AFTER T011 (Download) to ensure the file exists for header validation.
- **Task T043**: Must ensure the `streaming=True` flag is used with `datasets` or `h5py` iteration to prevent OOM on large datasets.
- **Task T044**: Must raise an error immediately if `torch.cuda.is_available()` returns True and `device` is not explicitly forced to "cpu".
- **Task T045**: Must log the result of Levene's test and the subsequent choice of statistical test (LMM vs block-bootstrap) in the final report.
- **Task T029b**: Explicitly calculates threshold where Total MSE ratio > 95% CI upper bound for null hypothesis to resolve SC-001's "[deferred]" placeholder and must write to `results/stability_threshold.json`.
- **Plan vs Spec Conflict**: The Plan's "Critical Methodological Adjustment" (frozen baseline) is superseded by Spec FR-002 (heuristic-initialized, trained baseline). Tasks follow the Spec.