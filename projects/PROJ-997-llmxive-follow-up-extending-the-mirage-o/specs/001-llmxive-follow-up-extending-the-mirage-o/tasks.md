# Tasks: llmXive follow-up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

**Input**: Design documents from `/specs/001-llmxive-mipu-gap-bounds/`
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
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create project directories: Create directories `src/`, `tests/`, `data/raw/`, `data/processed/`, `data/models/`, `docs/reports/`, `src/lib/`, `src/services/`, `src/cli/`, `src/config/`, `src/models/`.
- [X] T001b [P] Initialize Python packages: Create `__init__.py` files in each of the directories created in T001a to ensure valid Python package structure.
- [X] T002 Create `requirements.txt` containing: `transformers>=4.30.0`, `llama-cpp-python>=0.2.0`, `scikit-learn>=1.3.0`, `datasets>=2.14.0`, `pandas>=2.0.0`, `numpy>=1.24.0`, `torch>=2.0.0`, `pytest>=7.0.0`, `einops>=0.6.0`, `seaborn>=0.12.0`, `matplotlib>=3.7.0`
- [X] T003 [P] Configure linting and formatting: Create `.ruff.toml` with ruff config and `pyproject.toml` with `[tool.black]` section

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Setup data directory structure: Create `data/raw/`, `data/processed/`, `data/models/` directories.
- [X] T005 [P] Implement `src/lib/streaming_utils.py` for chunked dataset loading and checksumming
- [X] T006 [P] Create `src/lib/error_handling.py` with strict failure modes (no synthetic fallbacks)
- [X] T007 Define `TrainingSample` and `GapPredictionResult` classes in `src/models/entities.py`
- [X] T008 Create `src/config/logging_config.py` that configures a FileHandler to `logs/pipeline.log` with JSON formatting
- [X] T009 Create `src/config/env_config.py` with a `load_config()` function reading from `.env` and create `.env.example` with keys for MODEL_PATH, DATASET_ID
- [X] T017 [P] Implement logging infrastructure: Create `src/services/logger.py` with a `get_logger()` function that writes to `logs/pipeline.log` in **JSON lines format** with keys `sample_id`, `status` (success/error/skipped), and `error_code` (if applicable). This ensures reproducibility and documented derivation as per Constitution Principle I. **Dependency**: Must be complete before T015.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Hardware-Validated Gap Dataset Generation (Priority: P1) 🎯 MVP

**Goal**: Generate a dataset pairing full-precision training signals with ground-truth policy divergence measured by CPU-based quantized inference.

**Independent Test**: A CSV/Parquet file exists containing rows with `input_id`, `gradient_norms`, `local_curvature`, `quantized_logits`, and `calculated_kl_divergence`. The `calculated_kl_divergence` column must be non-zero for a statistically significant portion of the dataset.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for KL divergence calculation edge cases (zero-divergence) in `tests/unit/test_gap_calculator.py`
- [X] T011 [P] [US1] Integration test for data streaming and schema validation in `tests/integration/test_data_generation.py`

### Implementation for User Story 1

**⚠️ Sequential Execution**: Tasks T012, T013, T014 MUST complete before T015 begins. T015 orchestrates the paired loop.

- [X] T012 [P] [US1] Implement `src/services/feature_extractor.py`: Load a full-precision Llama model of standard scale., extract gradient norms (L2) and local curvature (Hutchinson's estimator) for GSM8K/Ultrachat samples
- [X] T013 [US1] Implement `src/services/quantized_inference.py`: Wrap `llama-cpp-python` to run INT4, INT8, and FP8 inference on CPU. **Error Handling**: If `llama_cpp.LlamaError` or `OSError` occurs due to **transient** issues (e.g., memory pressure), log a critical error and skip the sample. If the error indicates the **quantization level is unsupported** on the hardware (e.g., INT4 not available on this CPU build), log a **FATAL** error and **abort** that specific level's processing for the entire run (do not silently skip all samples for that level). This ensures all three levels (INT4, INT8, FP8) are attempted as required by FR-002 and SC-004.
- [X] T014 [US1] Implement `src/services/gap_calculator.py`: Compute exact KL divergence between full-precision and quantized logits; add epsilon for numerical stability
- [ ] T015a [US1] Implement `src/cli/generate_dataset_stream.py`: Implement the **streaming loop** that loads GSM8K/Ultrachat prompts one by one (or in small batches) using `datasets.load_dataset(..., streaming=True)`. **Dependency**: Must run after T012, T013, T014, T017.
- [ ] T015b [US1] Implement `src/cli/generate_dataset_core.py`: Implement the **core logic** for each sample: (1) Extract features (T012), (2) Run quantized inference **in a loop over INT4, INT8, and FP8 levels** (T013), (3) Calculate KL divergence (T014). **Crucial**: Ensure the loop explicitly iterates all three quantization levels for every sample to satisfy FR-002 and SC-004. Store `quantized_logits` as a **list of float32 values** (numerical, not base64 string) to facilitate immediate downstream calculation. **Dependency**: Must run after T015a.
- [ ] T015c [US1] Implement `src/cli/generate_dataset_writer.py`: Implement the **parquet writer** that aggregates results from T015b into `data/processed/training_sample.parquet` with columns: `input_id`, `gradient_norms`, `local_curvature`, `quantized_logits` (list of floats), `calculated_kl_divergence`, `quantization_level`. **Verification**: Task is complete ONLY when `data/processed/training_sample.parquet` exists, contains the specified schema, and the file size is within feasible limits (< 5GB). **Dependency**: Must run after T015b.
- [ ] T015 [US1] **Wrapper Task**: Implement `src/cli/generate_dataset.py` that **orchestrates T015a, T015b, T015c** sequentially. **Dependency**: Must run after T015a, T015b, T015c are implemented.
- [ ] T015C [US1] Implement `src/cli/monitor_runtime.py`: **Wrap** the T015 logic. Execute T015 as a subprocess. Monitor elapsed time. **If** elapsed time approaches a significant duration (e.g., 4.5 hours), **AND** the current sample count is **strictly greater than 300**, reduce the dataset size (e.g., stop streaming early) to meet the < 6 hour constraint. **If** the sample count is **at or below 300**, **FAIL LOUDLY** with a clear error message (SC-005 hard floor). **Dependency**: Must run after T015 is implemented.
- [ ] T015B [US1] Implement `src/cli/validate_dataset_levels.py`: Load `training_sample.parquet` and **log a warning** if samples for **any** of the three quantization levels (INT4, INT8, FP8) are missing or under-represented (e.g., < 10% of total). **DO NOT fail loudly**; proceed with available data to ensure resilience as per spec Edge Cases. **Dependency**: Must run after T015C (which runs T015).
- [ ] T015D [US1] Implement `src/cli/verify_dataset_completeness.py`: Load `training_sample.parquet` and compare the row count against the **target count** (original count reduced by T015C if applicable). **Log a warning** if counts do not match due to T013 skips or T015C reduction, but **DO NOT fail loudly** unless the count falls below the n=300 floor. **Dependency**: Must run after T015C.
- [X] T016 [US1] Modify `src/cli/generate_dataset.py` to append a summary log entry at the end of execution recording the **actual observed proportion** of samples with non-zero `calculated_kl_divergence` and report it in the pipeline log
- [X] T018 [US1] Implement `src/services/vif_checker.py`: Calculate Variance Inflation Factor (VIF) for gradient norms and curvature on the generated dataset; log results to `logs/pipeline.log` to validate the Assumption before model training

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3.2: Feature Diagnostics (Post-Data Generation)

**Purpose**: Validate dataset features before model training

- [ ] T018B [US1] Implement `src/cli/validate_features_diagnostic.py`: Load `training_sample.parquet`, **import the VIF calculation module from src/services/vif_checker.py (implemented in T018)**, and **log a warning** (do not raise an error) if collinearity exceeds threshold (VIF > 10) to ensure features are valid before training; log results to `logs/pipeline.log`. **Dependency**: Must run after T015D.

**Checkpoint**: Features validated

---

## Phase 4: User Story 2 - Training-Signal Predictor Model (Priority: P2)

**Goal**: Train a lightweight regression model (KRR) to predict the hardware-measured policy gap using only training-side features.

**Independent Test**: A trained model artifact exists that outputs a predicted divergence value. The model achieves a Pearson correlation coefficient (r) of > 0.8 on a held-out validation set.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Unit test for KRR training pipeline and hyperparameter grid in `tests/unit/test_predictor.py`
- [X] T020 [P] [US2] Integration test for model evaluation against test set in `tests/integration/test_model_training.py`

### Implementation for User Story 2

- [ ] T021A [US2] Implement `src/cli/prepare_data_split.py`: Load `training_sample.parquet`, **stratify by quantization level** (column name: `quantization_level`), and **concatenate stratified splits into a single training set**. Write train/val/test splits to `data/processed/split_train.parquet`, `data/processed/split_val.parquet`, and `data/processed/split_test.parquet`. **Verification**: **Log a warning** if any split lacks samples from one or more quantization levels (e.g., if a level was dropped by T013), but **DO NOT fail loudly**; proceed with available data. Update the split metadata to record which levels are present. **Dependency**: Must run after T018B.
- [ ] T021 [US2] Implement `src/cli/train_predictor.py`: Load stratified `train.parquet` (output of T021A), train KRR, and save model artifact to `data/models/gap_predictor.pkl`
- [X] T022 [US2] Implement evaluation logic in `src/services/evaluator.py`: Calculate Pearson correlation (r) and MAE between predicted and actual divergence on test set
- [ ] T022A [US2] Implement `src/cli/evaluate_on_test.py`: Load `test.parquet` (output of T021A), load `gap_predictor.pkl` (output of T021), and run the evaluation logic from T022 against the test set; report metrics to `data/processed/test_metrics.json`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Bound Verification & Statistical Validation (Priority: P3)

**Goal**: Verify theoretical bounds across quantization levels and statistically compare proxy vs. baseline MIPU loops.

**Independent Test**: A report exists showing correlation > 0.8 for at least one quantization level and a paired t-test result (p > 0.05) comparing policy acceptance rates.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for report schema in `tests/contract/test_report_schema.py`
- [X] T025 [P] [US3] Integration test for end-to-end statistical validation in `tests/integration/test_validation.py`

### Implementation for User Story 3

**⚠️ Sequential Execution**: T026A -> T026 -> T027 -> T028 -> T029. T027B and T032 run after T028.

- [ ] T026A [US3] Implement `src/cli/synchronize_inputs.py`: Generate a fixed set of input prompts with a **fixed random seed (seed=42)** and write them to `data/processed/synchronized_inputs.json`. **Define RL Task**: The task is GSM8K correctness. The 'reward' is a binary indicator that is positive if the model's generated answer matches the ground truth, and negative otherwise. **Remove** any custom 'stop/continue' action space. **Edge Case Injection**: **Identify and select 10 samples from the GSM8K dataset** that naturally exhibit **low entropy** (simple arithmetic, e.g., "What is 2+2?", "Calculate 5*5") or **near-zero gradient** characteristics (simple patterns). Append these 10 specific samples to the input set to ensure edge case coverage without introducing synthetic data bias. **Verification**: Task must verify that the generated JSON contains these specific edge case prompts. This artifact serves as the single source of truth for both T027 and T028 to ensure paired t-test validity. **Dependency**: Must run before T026.
- [X] T026 [US3] Implement `src/cli/orchestrate_baseline_proxy.py`: Load `test.parquet`, set a **fixed random seed**, and **load synchronized inputs from T026A** (`data/processed/synchronized_inputs.json`). Trigger T027 (baseline) and T028 (proxy) with these shared inputs to ensure valid paired comparison. **Remove** any logic that 'triggers' T027/T028; this task only prepares and passes inputs. **Dependency**: Must run after T026A.
- [ ] T027 [US3] Implement `src/cli/run_baseline_sync.py`: Execute the **full-hardware-sync baseline** by running actual quantized inference for every sample in the test set (using the same quantization levels as the dataset). **Scoring**: Calculate **continuous reasoning scores** derived from log-probabilities using the formula: `score = log_prob(correct_answer_token_sequence) * (1 - entropy_of_sequence)`. The `correct_answer` is retrieved from the GSM8K ground truth for each prompt. The `entropy` is calculated over the generated answer token sequence. Output results to `data/processed/baseline_metrics.json` with schema `{"acceptance_rate": float, "reasoning_score": float, "timing_metadata": {"total_time": float, "inference_only_time": float, "policy_evaluation_time": float}}`. **Note**: `policy_evaluation_time` must isolate the time taken for the hardware sync check (inference overhead) excluding prompt processing. **Verification**: Task is complete ONLY when `baseline_metrics.json` exists with valid data. **Dependency**: Must run after T026 and T026A.
- [X] T028 [US3] Implement `src/cli/run_proxy_loop.py`: Simulate MIPU loop (Proxy Policy vs. **Baseline from T027**) on test set. **Execute** against the synchronized inputs from T026A to generate `proxy_metrics.json`. Calculate **continuous reasoning scores** (same metric as T027) and final reasoning scores based on the **RL task definition** (GSM8K correctness). Perform paired t-test comparing Proxy vs. Baseline (FR-006). **Proxy Policy Logic**: Accept if predicted gap < 0.1. **Output Schema**: `{"acceptance_rate": float, "reasoning_score": float, "timing_metadata": {"total_time": float, "prediction_only_time": float, "policy_evaluation_time": float}}`. **Verification**: Task is complete ONLY when `proxy_metrics.json` exists with valid data. **Dependency**: Must run after T027 and T026A.
- [ ] T029 [US3] Implement statistical comparison in `src/utils/stats.py`: Perform **paired t-test** on acceptance rates and final **continuous reasoning scores** from T027 and T028. Apply **Bonferroni correction** for multiple comparisons. **Generate `data/processed/t_test_results.json`** with schema `{"p_value": float, "statistic": float, "method": "bonferroni_corrected_t_test", "adjusted_alpha": float}`. **Dependency**: Must run after T027 and T028.
- [ ] T027B [US3] Implement `src/cli/verify_bound_consistency.py`: Verify `|predicted - actual| < 0.1` holds **separately for INT4, INT8, and FP8 levels**. Calculate the percentage of samples satisfying the bound for each level and the global consistency metric. **Generate `data/processed/consistency_report.json`** with schema `{"per_level_correlations": {"INT4": float, "INT8": float, "FP8": float}, "global_consistency_metric": float, "per_level_satisfaction_pct": {"INT4": float, "INT8": float, "FP8": float}}`. **Verification**: Task is complete when the report is generated with all metrics; **do not enforce a specific pass/fail threshold** (e.g., 95%) as the spec only requires verification and reporting. **Dependency**: Must run after T028 and T015 (to access ground truth).
- [ ] T032 [US3] Implement `src/cli/aggregate_bound_results.py`: Aggregate the results from T027B to produce a final summary report. **Generate `data/processed/aggregated_consistency_report.json`** with the global consistency metric and a pass/fail verdict based on the threshold (if any defined in research, otherwise just report). **Dependency**: Must run after T027B.
- [X] T030 [US3] Implement `src/services/latency_meter.py`: Measure time for **policy evaluation step** (KRR prediction) vs. **baseline policy evaluation step** (time to run full hardware sync check for the same prompt). **Read `policy_evaluation_time` from `baseline_metrics.json` (T027) and `prediction_only_time` (proxy evaluation) from `proxy_metrics.json` (T028)**. **Calculate `latency_reduction_percentage`** using formula: `(baseline_policy_eval_time - proxy_policy_eval_time) / baseline_policy_eval_time * 100`; **verify** if the reduction meets the ≥90% target (SC-002); write `proxy_policy_eval_time`, `baseline_policy_eval_time`, `reduction_percentage`, `target_met` (boolean) to `data/processed/latency_metrics.json`. **Dependency**: Must run after T027 and T028.
- [X] T033 [US3] Generate final research report with all metrics, plots, and statistical conclusions in `docs/reports/001-llmxive-mipu-gap-bounds.md`, including **latency_reduction_percentage** for the **policy evaluation step** (SC-002), consistency findings, **Bonferroni correction method**, and adjusted alpha threshold
- [X] T034 [US3] Update `state/projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o.yaml` to set `updated_at` to current ISO 8601 timestamp and populate `artifact_hashes` with SHA-256 checksums of `data/processed/*.parquet`, `data/models/*.pkl`, `data/processed/*.json`, and `docs/reports/*.md`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035A [P] Polish and Cleanup: Update `README.md` with installation steps.
- [ ] T035B [P] Polish and Cleanup: Generate `docs/api.md` with function signatures.
- [ ] T035C [P] Polish and Cleanup: Remove unused imports, optimize loops in `generate_ground_truth.py`, and verify streaming works correctly (<7GB memory).
- [ ] T035D [P] Polish and Cleanup: Run `quickstart.md` validation and ensure no PII in logs.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (`training_sample.parquet`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output (`gap_predictor.pkl`) and US1 data

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for KL divergence calculation edge cases in tests/unit/test_gap_calculator.py"
Task: "Integration test for data streaming and schema validation in tests/integration/test_data_generation.py"

# Launch all models/services for User Story 1 together (Sequential Execution Required):
Task: "Implement src/services/feature_extractor.py"
Task: "Implement src/services/quantized_inference.py" (Must complete before T015)
Task: "Implement src/services/gap_calculator.py"
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
 - Developer B: User Story 2 (Model Training)
 - Developer C: User Story 3 (Validation)
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
- **Critical Constraint**: Data loaders MUST fail loudly on fetch errors; no synthetic fallbacks allowed.
- **Critical Constraint**: Streaming must be used for all dataset loading to avoid OOM on GitHub Actions runners.
- **Critical Constraint**: Quantized inference must use `llama.cpp` on CPU; if too slow, reduce sample size, do not simulate.
- **Critical Constraint**: Baseline comparison (T028) MUST use the full-hardware-sync execution from T027, not a static rule.
- **Critical Constraint**: Data splitting (T021A) MUST stratify by quantization level to ensure joint training (FR-004) and enforce n >= 300 floor, but MUST log warnings instead of failing if levels are missing.
- **Critical Constraint**: Bound verification (T027B) MUST report consistency across all three levels (INT4, INT8, FP8) with a per-level breakdown; no arbitrary pass/fail threshold.
- **Critical Constraint**: Latency measurement (T030) MUST isolate the 'policy evaluation step' and record the specific metric for SC-002, comparing policy evaluation time vs prediction time.
- **Critical Constraint**: T015 MUST pair feature extraction and inference for every sample across all three quantization levels.
- **Critical Constraint**: T026 MUST synchronize seeds and inputs for T027/T028.
- **Critical Constraint**: T021A MUST assert all quantization levels are present in splits (or adapt sample size), but log warnings instead of failing.
- **Critical Constraint**: T013 MUST log and skip on transient engine failure, but abort if a level is unsupported.
- **Critical Constraint**: T026A MUST define the RL task as GSM8K correctness (no custom actions) and inject natural edge cases (no synthetic data).
- **Critical Constraint**: T015B MUST validate all quantization levels but log warnings instead of failing if missing.
- **Critical Constraint**: T015C MUST enforce the 6-hour runtime limit *during* generation and reduce by sample count, but **HARD STOP** at n=300.
- **Critical Constraint**: T015D MUST verify dataset completeness against the *target* count (reduced if applicable).
- **Critical Constraint**: T030 MUST compare `policy_evaluation_time` from baseline vs `prediction_only_time` from proxy.
- **Critical Constraint**: T015 MUST store `quantized_logits` as numerical lists, not base64 strings.