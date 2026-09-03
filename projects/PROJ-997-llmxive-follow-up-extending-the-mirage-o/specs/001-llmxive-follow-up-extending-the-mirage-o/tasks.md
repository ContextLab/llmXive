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
- [X] T009 Create `src/config/env_config.py` with a `load_config()` function reading from `.env` and create `.env.example` with keys for MODEL_PATH, DATASET_ID, ACCEPTANCE_THRESHOLD
- [X] T017 [P] Implement logging infrastructure: Create `src/services/logger.py` with a `get_logger()` function that writes to `logs/pipeline.log` in **JSON lines format** with keys `sample_id`, `status` (success/error/skipped), and `error_code` (if applicable). This ensures reproducibility and documented derivation as per Constitution Principle I. **Dependency**: T017 is a shared resource available immediately after Phase 2 initialization; it does not block the start of US1 tasks but must be initialized before T015 execution.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Hardware-Validated Gap Dataset Generation (Priority: P1) 🎯 MVP

**Goal**: Generate a dataset pairing full-precision training signals with ground-truth policy divergence measured by CPU-based quantized inference.

**Independent Test**: A CSV/Parquet file exists containing rows with `input_id`, `gradient_norms`, `local_curvature`, `quantized_logits`, and `calculated_kl_divergence`. The `calculated_kl_divergence` column must be non-zero for a statistically significant portion of the dataset.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for KL divergence calculation edge cases (zero-divergence) in `tests/unit/test_gap_calculator.py`
- [X] T011 [P] [US1] Integration test for data streaming and schema validation in `tests/integration/test_data_generation.py`

### Implementation for User Story 1

**⚠️ Parallel Execution (Prerequisites for T015)**: Tasks T012, T013, T014 can run in parallel with each other but MUST all complete before T015 begins. T015 orchestrates the paired loop.

- [X] T012 [P] [US1] Implement `src/services/feature_extractor.py`: Load a full-precision Llama model of standard scale, specifically `meta-llama/Llama-3-8B` in BF16 precision. Extract gradient norms (Lp) and local curvature (Hutchinson's estimator) for GSM8K/Ultrachat samples. **Dependency**: T012 can start immediately after Phase 2 (Foundational) is complete.
- [X] T013 [US1] Implement `src/services/quantized_inference.py`: Wrap `llama-cpp-python` to run INT4, INT8, and FP8 inference on CPU. **Model Files**: Expect quantized models in `data/raw/` with naming convention `model-Q4_K_M.gguf` (INT4), `model-Q8_0.gguf` (INT8), and `model-FP8.gguf` (FP8). **Error Handling**: If `llama_cpp.LlamaError` or `OSError` occurs, **LOG THE ERROR AND SKIP THE SAMPLE**. Do NOT fail the entire pipeline. This aligns with Spec Edge Case 3 to ensure partial dataset completion. **Dependency**: T013 can start immediately after Phase 2 (Foundational) is complete.
- [X] T014 [US1] Implement `src/services/gap_calculator.py`: Compute exact KL divergence between full-precision and quantized logits; add epsilon for numerical stability. **Dependency**: T014 can start immediately after Phase 2 (Foundational) is complete.
- [X] T015 [US1] **Wrapper Task**: Implement `src/cli/generate_dataset.py`. This single task orchestrates the full pipeline:
 1. **Stream**: Load GSM8K/Ultrachat prompts using `datasets.load_dataset(..., streaming=True)`.
 2. **Extract**: For each sample, extract features using T012.
 3. **Infer**: Run quantized inference for INT4, INT8, and FP8 levels using T013.
 4. **Calculate**: Compute KL divergence using T014.
 5. **Monitor**: Track elapsed time. If `elapsed_time + (estimated_time_per_sample * remaining_samples) > 6 hours` (SC-005 total constraint) AND `current_sample_count > 300`, stop after the current batch. If `current_sample_count <= 300`, continue until completion or 6-hour limit.
 6. **Validate**: Ensure at least one sample exists for each quantization level (INT4, INT8, FP8) in the output. **FAIL LOUDLY** ONLY if any level has ZERO samples. This prevents total abort on transient errors while ensuring coverage.
 7. **Store**: Save `training_sample.parquet` with `quantized_logits` as numerical lists.
 **Dependencies**: Must run after T012, T013, T014, T017.
- [X] T016 [US1] Modify `src/cli/generate_dataset.py` to append a summary log entry at the end of execution recording the **actual observed proportion** of samples with non-zero `calculated_kl_divergence` and report it in the pipeline log
- [X] T018 [US1] Implement `src/services/vif_checker.py`: Calculate Variance Inflation Factor (VIF) for gradient norms and curvature on the generated dataset; log results to `logs/pipeline.log` to validate the Assumption before model training

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3.2: Feature Diagnostics (Post-Data Generation)

**Purpose**: Validate dataset features before model training

- [X] T019 [US1] Implement `src/cli/validate_features_diagnostic.py`: Load `training_sample.parquet`, **import the VIF calculation module from src/services/vif_checker.py (implemented in T018)**, and **perform a hard-stop check**. If VIF > 10 (2005.02245, https://arxiv.org/abs/2005.02245), **HALT THE PIPELINE** with a fatal error and a clear message requiring feature re-selection or dimensionality reduction. Do NOT proceed to model training if collinearity is high. Log results to `logs/pipeline.log`. **Dependency**: Must run after T015. **Tag**: [US1] (Validation of US1 data).

**Checkpoint**: Features validated

---

## Phase 4: User Story 2 - Training-Signal Predictor Model (Priority: P2)

**Goal**: Train a lightweight regression model (KRR) to predict the hardware-measured policy gap using only training-side features.

**Independent Test**: A trained model artifact exists that outputs a predicted divergence value. The model achieves a Pearson correlation coefficient (r) of > 0.8 on a held-out validation set. [UNRESOLVED-CLAIM: c_7aa7d297 — status=not_enough_info]

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for KRR training pipeline and hyperparameter grid in `tests/unit/test_predictor.py`
- [X] T021 [P] [US2] Integration test for model evaluation against test set in `tests/integration/test_model_training.py`

### Implementation for User Story 2

- [X] T021A [US2] Implement `src/cli/prepare_data_split.py`: Load `training_sample.parquet`, **stratify by quantization level** (column name: `quantization_level`), and **concatenate stratified splits into a single training set**. Write train/val/test splits to `data/processed/split_train.parquet`, `data/processed/split_val.parquet`, and `data/processed/split_test.parquet`. **Verification**: **FAIL LOUDLY** if any split lacks samples from one or more quantization levels (e.g., if a level was dropped by T013), as this violates FR-004 and SC-004. Update the split metadata to record which levels are present. **Dependency**: Must run after T019.
- [X] T021 [US2] Implement `src/cli/train_predictor.py`: Load stratified `train.parquet` (output of T021A). **Pre-training Verification**: Explicitly assert that the training set contains samples from all three quantization levels (INT4, INT8, FP8). **FAIL LOUDLY** if any level is missing to satisfy FR-004. Train KRR and save model artifact to `data/models/gap_predictor.pkl`. **Verification**: Task is complete ONLY when `gap_predictor.pkl` exists and can be loaded. **Dependency**: Must run after T021A.
- [X] T022 [US2] Implement evaluation logic in `src/services/evaluator.py`: Calculate Pearson correlation (r) and MAE between predicted and actual divergence on test set
- [X] T022A [US2] Implement `src/cli/evaluate_on_test.py`: Load `test.parquet` (output of T021A), load `gap_predictor.pkl` (output of T021), and run the evaluation logic from T022 against the test set; report metrics to `data/processed/test_metrics.json`. **Verification**: Task is complete ONLY when `test_metrics.json` exists with valid data. **Dependency**: Must run after T021.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Bound Verification & Statistical Validation (Priority: P3)

**Goal**: Verify theoretical bounds across quantization levels and statistically compare proxy vs. baseline MIPU loops.

**Independent Test**: A report exists showing correlation > 0.8 for at least one quantization level and a paired t-test result (p > 0.05) comparing policy acceptance rates.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for report schema in `tests/contract/test_report_schema.py`
- [X] T025 [P] [US3] Integration test for end-to-end statistical validation in `tests/integration/test_validation.py`

### Implementation for User Story 3

**⚠️ Sequential Execution**: T026A -> T026 -> T027 -> T028 -> T029. T027B and T031 run after T028.

- [X] T026A [US3] Implement `src/cli/synchronize_inputs.py`: Generate a fixed set of input prompts with a **fixed random seed (seed=42)** and write them to `data/processed/synchronized_inputs.json`. **Define RL Task**: The task is **GSM8K** correctness. The 'reward' is a binary indicator that is positive if the model's generated answer matches the ground truth, and negative otherwise. **Remove** any custom 'stop/continue' action space. **Edge Case Injection**: **Select samples from the GSM8K dataset** that naturally exhibit **low complexity** using the deterministic rule: `answer_token_length <= 5`. Append these samples to the input set until the edge case count reaches at least 5% of the target n=300 (or a minimum of 30 samples) to ensure statistical power. **Verification**: Task must verify that the generated JSON contains these specific edge case prompts and meets the minimum count. This artifact serves as the single source of truth for both T027 and T028 to ensure paired t-test validity. **Dependency**: Must run before T026.
- [X] T026 [US3] Implement `src/cli/orchestrate_baseline_proxy.py`: Load `test.parquet`, set a **fixed random seed**, and **load synchronized inputs from T026A** (`data/processed/synchronized_inputs.json`). Trigger T027 (baseline) and T028 (proxy) with these shared inputs to ensure valid paired comparison. **Remove** any logic that 'triggers' T027/T028; this task only prepares and passes inputs. **Dependency**: Must run after T026A.
- [X] T027 [US3] Implement `src/cli/run_baseline_sync.py`: Execute the **full-hardware-sync baseline** by running actual quantized inference for every sample in the test set (using the same quantization levels as the dataset). **Scoring**: Calculate **binary reasoning scores** (1 if answer matches GSM8K ground truth, 0 otherwise). **Crucially, also calculate a binary 'acceptance_rate'**: Accept if `score > threshold` (threshold defined in `src/config/env_config.py`, default 0.5). **Latency Metric**: `policy_evaluation_time` MUST include the full time taken for the hardware sync check **including the inference time itself** (the cost being replaced). Output results to `data/processed/baseline_metrics.json` with schema `{"acceptance_rate": float, "reasoning_score": float, "timing_metadata": {"total_time": float, "inference_only_time": float, "policy_evaluation_time": float}}`. **Verification**: Task is complete ONLY when `baseline_metrics.json` exists with valid data. **Dependency**: Must run after T026 and T026A.
- [X] T028 [US3] Implement `src/cli/run_proxy_loop.py`: Simulate MIPU loop (Proxy Policy vs. **Baseline from T027**) on test set. **Execute** against the synchronized inputs from T026A to generate `proxy_metrics.json`. Calculate **binary reasoning scores** (same metric as T027) and final reasoning scores based on the **RL task definition** (GSM8K correctness). Perform paired t-test comparing Proxy vs. Baseline (FR-006). **Proxy Policy Logic**: Accept if predicted gap < 0.1. [UNRESOLVED-CLAIM: c_3960cb3a — status=not_enough_info] **Output Schema**: `{"acceptance_rate": float, "reasoning_score": float, "timing_metadata": {"total_time": float, "prediction_only_time": float, "policy_evaluation_time": float}}`. **Verification**: Task is complete ONLY when `proxy_metrics.json` exists with valid data. **Dependency**: Must run after T027 and T026A.
- [X] T029 [US3] Implement statistical comparison in `src/utils/stats.py`: Perform **paired t-test** on acceptance rates and final **binary reasoning scores** from T027 and T028. **Statistical Validity Check**: Before running the t-test, perform a **Shapiro-Wilk test** on the differences of the binary scores. If normality is violated (p < 0.05), **switch to McNemar's test** or a permutation test. Apply **Bonferroni correction** for multiple comparisons. **Generate `data/processed/t_test_results.json`** with schema `{"p_value": float, "statistic": float, "method": "bonferroni_corrected_t_test | mcnemar_test | permutation_test", "adjusted_alpha": float, "normality_check": {"shapiro_p_value": float, "method_used": "..."}}`. **Verification**: Task is complete ONLY when `t_test_results.json` exists with valid data. **Dependency**: Must run after T027 and T028.
- [X] T027B [US3] **Merged Task**: Implement `src/cli/verify_bound_consistency.py`. This task merges the calculation and final aggregation logic into a single step.
 1. Load `gap_predictor.pkl` (from T021) and `test.parquet` (from T021A).
 2. Verify `|predicted - actual| < 0.1` holds **separately for INT4, INT8, and FP8 levels**.
 3. Calculate the percentage of samples satisfying the bound for each level.
 4. **Aggregate results** into a global consistency metric.
 5. **Generate `data/processed/consistency_report.json`** with schema `{"per_level_correlations": {"INT4": float, "INT8": float, "FP8": float}, "global_consistency_metric": float, "per_level_satisfaction_pct": {"INT4": float, "INT8": float, "FP8": float}}`.
 **Verification**: Task is complete ONLY when `consistency_report.json` exists with valid data. **Dependency**: Must run after T028, T015, **T021 (model training)**, and **T022 (evaluation)**. **Note**: Requires the `gap_predictor.pkl` from T021 to generate 'predicted' values. **Explicitly requires per-level breakdown** to satisfy FR-007.
- [X] T031 [US3] Implement `src/cli/check_generalizability.py`: Perform a domain sensitivity check to verify the GSM8K subset is representative of the target domain. Compare performance metrics on the GSM8K subset against a held-out subset of a different domain (if available) or analyze the distribution of difficulty scores within GSM8K. **Generate `data/processed/generalizability_report.json`** with findings. **Dependency**: Must run after T028.
- [X] T030 [US3] Implement `src/services/latency_meter.py`: Measure time for **policy evaluation step** (KRR prediction) vs. **baseline policy evaluation step** (time to run full hardware sync check for the same prompt, **including inference**). **Read `policy_evaluation_time` from `baseline_metrics.json` (T027) and `prediction_only_time` (proxy evaluation) from `proxy_metrics.json` (T028)**. **Handle missing keys**: If `policy_evaluation_time` is missing, default to 0 and log a warning. **Calculate `latency_reduction_percentage`** using formula: `(baseline_policy_eval_time - proxy_policy_eval_time) / baseline_policy_eval_time * 100`; **verify** if the reduction meets the ≥90% target (SC-002); write `proxy_policy_eval_time`, `baseline_policy_eval_time`, `reduction_percentage`, `target_met` (boolean) to `data/processed/latency_metrics.json`. **Verification**: Task is complete ONLY when `latency_metrics.json` exists with valid data. **Dependency**: Must run after T027 and T028.
- [X] T033 [US3] Generate final research report with all metrics, plots, and statistical conclusions in `docs/reports/001-llmxive-mipu-gap-bounds.md`, including **latency_reduction_percentage** for the **policy evaluation step** (SC-002), consistency findings, **Bonferroni correction method**, and adjusted alpha threshold. **Time Budget Check**: At the start of execution, check the remaining time budget. If less than 15 minutes remain, **prioritize core artifacts** (metrics.json, plots) and **truncate non-essential narrative** to ensure the 6-hour SC-005 limit is respected. **Dependency**: Must run after T027B, T029, T030, T031.
- [X] T034 [US3] Update `state/projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o.yaml` to set `updated_at` to current ISO 8601 timestamp and populate `artifact_hashes` with SHA-256 checksums of `data/processed/*.parquet`, `data/models/*.pkl`, `data/processed/*.json`, and `docs/reports/*.md`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035A [P] Polish and Cleanup: Update `README.md` with installation steps, dependencies, and usage examples.
- [ ] T035B [P] Polish and Cleanup: Generate `docs/api.md` with function signatures for all public modules in `src/`.
- [ ] T035C [P] Polish and Cleanup: Remove unused imports, optimize loops in `generate_dataset.py`, and verify streaming works correctly (<7GB memory).
- [ ] T035D [P] Polish and Cleanup: Run `quickstart.md` validation and ensure no PII in logs.
- [X] T036 [P] [US1] Implement `src/cli/verify_model_availability.py`: Check for existence of `meta-llama/Llama-3-8B` and required quantized `.gguf` files in `data/raw/` before starting T015. If missing, **FAIL LOUDLY** with a clear error message indicating which files are missing and how to obtain them (e.g., HuggingFace link or conversion script). This prevents T015 from failing mid-execution due to missing resources. **Dependency**: Must run before T015.
- [X] T037 [P] [US1] Implement `src/services/quantization_level_validator.py`: A dedicated module to verify that the input dataset contains valid, non-empty logits for all three quantization levels (INT4, INT8, FP8) before passing to T014. If any level is missing or invalid, raise a specific `MissingQuantizationLevelError` with the affected sample ID. **Dependency**: Must be complete before T015.
- [X] T038 [P] [US2] Implement `src/cli/validate_stratification.py`: A post-split validation script for T021A that loads `split_train.parquet`, `split_val.parquet`, and `split_test.parquet` and asserts that the distribution of `quantization_level` is statistically similar across splits (e.g., using Chi-Square test). Log the p-value to `logs/pipeline.log`. **Dependency**: Must run after T021A.
- [ ] T039 [P] [US3] Implement `src/cli/generate_visualization_report.py`: Create a `docs/reports/001-llmxive-mipu-gap-bounds_viz.md` containing: 1) Scatter plot of Predicted vs Actual Divergence (colored by quantization level), 2) Bar chart of Bound Satisfaction % per level, 3) Box plot of Reasoning Scores (Proxy vs Baseline). **Dependency**: Must run after T027B and T029.

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

# Launch all models/services for User Story 1 together (Parallel Execution Required):
Task: "Implement src/services/feature_extractor.py"
Task: "Implement src/services/quantized_inference.py"
Task: "Implement src/services/gap_calculator.py"
# All three must complete before T015 begins.
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
- **Critical Constraint**: Data splitting (T021A) MUST stratify by quantization level to ensure joint training (FR-004) and enforce n >= 300 floor, but MUST **FAIL LOUDLY** if levels are missing.
- **Critical Constraint**: Bound verification (T027B) MUST report consistency across all three levels (INT4, INT8, FP8) with a per-level breakdown; no arbitrary pass/fail threshold. **This task now includes aggregation logic previously in T032.**
- **Critical Constraint**: Latency measurement (T030) MUST isolate the 'policy evaluation step' and record the specific metric for SC-002, comparing policy evaluation time vs prediction time.
- **Critical Constraint**: T015 MUST pair feature extraction and inference for every sample across all three quantization levels.
- **Critical Constraint**: T026 MUST synchronize seeds and inputs for T027/T028.
- **Critical Constraint**: T021A MUST assert all quantization levels are present in splits (or adapt sample size), but **FAIL LOUDLY** if missing.
- **Critical Constraint**: T013 MUST log and skip on transient engine failure, but abort if a level is unsupported. **UPDATED**: T013 must log and skip on errors to preserve data hygiene.
- **Critical Constraint**: T026A MUST define the RL task as GSM8K correctness (no custom actions) and inject natural edge cases (no synthetic data) using deterministic selection rules.
- **Critical Constraint**: T015 MUST validate all quantization levels but **FAIL LOUDLY** only if a level has ZERO samples.
- **Critical Constraint**: T015 MUST enforce the 6-hour runtime limit dynamically and reduce by sample count, but **STOP GRACEFULLY** at n=300.
- **Critical Constraint**: T030 MUST compare `policy_evaluation_time` from baseline vs `prediction_only_time` from proxy.
- **Critical Constraint**: T015 MUST store `quantized_logits` as numerical lists, not base64 strings.
- **Critical Constraint**: T027B MUST depend on T021 (model training) to access the predictor.
- **Critical Constraint**: T027 MUST output `acceptance_rate` for statistical comparison.
- **Critical Constraint**: T027 MUST use binary GSM8K correctness for scoring.
- **Critical Constraint**: T015 MUST use dynamic time budgeting based on SC-005 (6h total).
- **Critical Constraint**: T021, T027, T029 MUST explicitly generate their output files and include verification steps to ensure artifact existence.
- **Critical Constraint**: T032 has been removed; its logic is merged into T027B.
- **Critical Constraint**: T036, T037, T038, T039 MUST be completed to ensure robustness of data availability, quantization integrity, stratification validity, and visualization completeness.
- **Critical Constraint**: T019 MUST halt the pipeline if VIF > 10 to ensure statistical validity.
- **Critical Constraint**: T029 MUST perform a normality check and fallback to McNemar's test if normality is violated.
- **Critical Constraint**: T021 MUST verify all quantization levels are present in the training set before training.
- **Critical Constraint**: T033 MUST check the time budget and truncate non-essential artifacts if needed to meet the 6-hour limit.
- **Critical Constraint**: T027 MUST include inference time in `policy_evaluation_time` to accurately measure the cost being replaced.