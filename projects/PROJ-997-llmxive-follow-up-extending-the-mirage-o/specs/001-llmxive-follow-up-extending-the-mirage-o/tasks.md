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

- [X] T001a [P] Create project directories: Create directories `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/`, `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/lib/`, `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/services/`, `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/`, `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/config/`, `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/models/`, `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/tests/`, `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/data/raw/`, `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/data/processed/`, `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/data/models/`, `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/docs/reports/`. **Verification**: Verify each directory exists via `os.path.isdir` after creation.
- [X] T001b [P] Initialize Python packages: Create `__init__.py` files in each of the directories created in T001a to ensure valid Python package structure.
- [X] T002 Create `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/requirements.txt` containing: `transformers>=4.30.0`, `llama-cpp-python>=0.2.0`, `scikit-learn>=1.3.0`, `datasets>=2.14.0`, `pandas>=2.0.0`, `numpy>=1.24.0`, `torch>=2.0.0`, `pytest>=7.0.0`, `einops>=0.6.0`, `seaborn>=0.12.0`, `matplotlib>=3.7.0`
- [X] T003 [P] Configure linting and formatting: Create `.ruff.toml` with ruff config and `pyproject.toml` with `[tool.black]` section

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can begin

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/lib/streaming_utils.py` for chunked dataset loading and checksumming
- [X] T006 [P] Create `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/lib/error_handling.py` with strict failure modes (no synthetic fallbacks)
- [X] T007 Define `TrainingSample`, `QuantizedInferenceResult`, and `GapPredictionResult` classes in `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/models/entities.py`. `TrainingSample` must contain `input_id`, `gradient_norms`, `local_curvature`, `quantized_logits`, and `calculated_kl_divergence`. `QuantizedInferenceResult` must contain `quantized_logits` and `kl_divergence` (for FR-002/003). `GapPredictionResult` must contain `predicted_gap`.
- [X] T008 Create `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/config/logging_config.py` that configures a FileHandler to `logs/pipeline.log` with JSON formatting
- [X] T009 Create `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/config/env_config.py` with a `load_config()` function reading from `.env` and create `.env.example` with keys for MODEL_PATH, DATASET_ID, ACCEPTANCE_THRESHOLD
- [X] T017 [P] Implement logging infrastructure: Create `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/services/logger.py` with a `get_logger()` function that writes to `logs/pipeline.log` in **JSON lines format** with keys `sample_id`, `status` (success/error/skipped), and `error_code` (if applicable). This ensures reproducibility and documented derivation as per Constitution Principle I. **Dependency**: T017 is a shared resource available immediately after Phase 2 initialization; it does not block the start of US1 tasks but must be initialized before T015 execution.
- [X] T036 [P] [US1] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/verify_model_availability.py`: Check for existence of `meta-llama/Llama-3-8B` and required quantized `.gguf` files in `data/raw/` before starting T015. If missing, **FAIL LOUDLY** with a clear error message indicating which files are missing and how to obtain them (e.g., HuggingFace link or conversion script). This prevents T015 from failing mid-execution due to missing resources. **Dependency**: Must run before T015.
- [X] T037 [P] [US1] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/services/quantization_level_validator.py`: A dedicated module to verify that the input dataset contains valid, non-empty logits for all three quantization levels (INT4, INT8, FP8) before passing to T014. If any level is missing or invalid, raise a specific `MissingQuantizationLevelError` with the affected sample ID. **Dependency**: Must be complete before T015.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Hardware-Validated Gap Dataset Generation (Priority: P1) 🎯 MVP

**Goal**: Generate a dataset pairing full-precision training signals with ground-truth policy divergence measured by CPU-based quantized inference.

**Independent Test**: A CSV/Parquet file exists containing rows with `input_id`, `gradient_norms`, `local_curvature`, `quantized_logits`, and `calculated_kl_divergence`. The `calculated_kl_divergence` column must be non-zero for a statistically significant portion of the dataset.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for KL divergence calculation edge cases (zero-divergence) in `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/tests/unit/test_gap_calculator.py`
- [X] T011 [P] [US1] Integration test for data streaming and schema validation in `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/tests/integration/test_data_generation.py`

### Implementation for User Story 1

**⚠️ Parallel Execution (Prerequisites for T015)**: Tasks T012, T013, T014 can run in parallel with each other but MUST all complete before T015 begins. T015 orchestrates the paired loop.

- [X] T012 [P] [US1] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/services/feature_extractor.py`: Load a full-precision Llama model of standard scale, specifically `meta-llama/Llama-3-8B` in BF16 precision. **Implement a Synthetic Training Step**: For the first 300 GSM8K samples (seed=42), generate a perturbed target (e.g., shift logits by small noise) and compute MSE loss between model output and perturbed target. Perform a backward pass to compute **gradient norms** (Lp) and **local curvature** (Hutchinson's estimator) from this defined loss. **Dependency**: T012 can start immediately after Phase 2 (Foundational) is complete.
- [X] T013 [US1] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/services/quantized_inference.py`: Wrap `llama-cpp-python` to run INT4, INT8, and FP8 inference on CPU. **Model Files**: Expect quantized models in `data/raw/` with naming convention `model-Q4_K_M.gguf` (INT4), `model-Q8_0.gguf` (INT8), and `model-FP8.gguf` (FP8). **Error Handling**: If `llama_cpp.LlamaError` or `OSError` occurs, **LOG THE ERROR AND SKIP THE SAMPLE**. Do NOT fail the entire pipeline. This aligns with Spec Edge Case 3 to ensure partial dataset completion. **Dependency**: T013 can start immediately after Phase 2 (Foundational) is complete.
- [X] T014 [US1] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/services/gap_calculator.py`: Compute exact KL divergence between full-precision and quantized logits; add epsilon for numerical stability. **Dependency**: T014 can start immediately after Phase 2 (Foundational) is complete.
- [X] T015 [US1] **Wrapper Task**: Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/generate_dataset.py`. This single task orchestrates the full pipeline:
 1. **Stream**: Load GSM8K prompts using `datasets.load_dataset(..., streaming=True)`.
 2. **Extract**: For each sample, extract features using T012.
 3. **Infer**: Run quantized inference for INT4, INT8, and FP8 levels using T013.
 4. **Calculate**: Compute KL divergence using T014.
 5. **Monitor**: Track elapsed time. If `elapsed_time + (estimated_time_per_sample * remaining_samples) > 6 hours` (SC-005 total constraint) AND `current_sample_count > 300`, stop after the current batch. If `current_sample_count <= 300`, continue until completion or 6-hour limit. **estimated_time_per_sample** is derived from a **rolling average of the last 10 samples**.
 6. **Validate**: Ensure at least one sample exists for *each* quantization level that was successfully attempted. If a level has ZERO samples, **FAIL LOUDLY** with a clear error message indicating which level is missing and that the pipeline cannot proceed without joint training data (per FR-004). This resolves the T013 skip vs T015 fail contradiction by clarifying that level-level coverage is mandatory.
 7. **Store**: Save `training_sample.parquet` with `quantized_logits` as numerical lists.
 **Dependencies**: Must run after T012, T013, T014, T017, T036, T037.
- [X] T016 [US1] Modify `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/generate_dataset.py` to append a summary log entry at the end of execution recording the **actual observed proportion** of samples with non-zero `calculated_kl_divergence` and report it in the pipeline log
- [X] T018 [US1] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/services/vif_checker.py`: Calculate Variance Inflation Factor (VIF) for gradient norms and curvature on the generated dataset; log results to `logs/pipeline.log` to validate the Assumption before model training

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 3.2: Feature Diagnostics (Post-Data Generation)

**Purpose**: Validate dataset features before model training

- [X] T019 [US1] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/extract_features_pca.py`: Load `training_sample.parquet`, perform **Principal Component Analysis (PCA)** on gradient norms and curvature to reduce dimensionality if needed, and save the transformed features to `data/processed/features_pca.parquet`. This task corresponds to the Plan's T019 'Feature Extraction & PCA'. **Dependency**: Must run after T015.
- [X] T019c [US1] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/prepare_vif_data.py`: Load `features_pca.parquet` (output of T019) and prepare data for VIF calculation. **Dependency**: Must run after T019.
- [X] T019d [US1] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/calculate_vif.py`: Load prepared data from T019c, **import the VIF calculation module from projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/services/vif_checker.py (implemented in T018)**, and calculate VIF. Log results to `logs/pipeline.log`. **Dependency**: Must run after T019c.
- [X] T019e [US1] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/evaluate_vif.py`: Load VIF results from T019d. If VIF > 10 (2005.02245, https://arxiv.org/abs/2005.02245), **HALT THE PIPELINE** with a fatal error and a clear message requiring feature re-selection or dimensionality reduction. Do NOT proceed to model training if collinearity is high. **Dependency**: Must run after T019d. **Tag**: [US1] (Validation of US1 data).

**Checkpoint**: Features validated

---

## Phase 4: User Story 2 - Training-Signal Predictor Model (Priority: P2)

**Goal**: Train a lightweight regression model (KRR) to predict the hardware-measured policy gap using only training-side features.

**Independent Test**: A trained model artifact exists that outputs a predicted divergence value. The model achieves a Pearson correlation coefficient (r) of > 0.8 on a held-out validation set. [UNRESOLVED-CLAIM: c_899b84a2 — status=not_enough_info]

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for KRR training pipeline and hyperparameter grid in `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/tests/unit/test_predictor.py`
- [X] T021 [P] [US2] Integration test for model evaluation against test set in `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/tests/integration/test_model_training.py`

### Implementation for User Story 2

- [X] T023 [US2] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/stratify_training_data.py`: Load `training_sample.parquet`, **stratify by quantization level** (column name: `quantization_level`), and **concatenate stratified splits into a single training set**. This task corresponds to the Plan's T023 'Stratify Training Data'. **Dependency**: Must run after T019e.
- [X] T021A [US2] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/prepare_data_split.py`: Load stratified data from T023, and **create train/val/test splits**. Write splits to `data/processed/split_train.parquet`, `data/processed/split_val.parquet`, and `data/processed/split_test.parquet`. **Verification**: If a quantization level is missing from a split due to skipped samples (per Edge Case 3), **PROCEED WITH AVAILABLE LEVELS** and log a warning. Do NOT fail the pipeline. Update the split metadata to record which levels are present. **Dependency**: Must run after T023.
- [X] T021 [US2] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/train_predictor.py`: Load stratified `train.parquet` (output of T021A). **Pre-training Verification**: Explicitly assert that the training set contains samples from available quantization levels. Train KRR and save model artifact to `data/models/gap_predictor.pkl`. **Verification**: Task is complete ONLY when `gap_predictor.pkl` exists and can be loaded. **Dependency**: Must run after T021A.
- [X] T022 [US2] Implement evaluation logic in `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/services/evaluator.py`: Calculate Pearson correlation (r) and MAE between predicted and actual divergence on test set
- [X] T022A [US2] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/evaluate_on_test.py`: Load `test.parquet` (output of T021A), load `gap_predictor.pkl` (output of T021), and run the evaluation logic from T022 against the test set; report metrics to `data/processed/test_metrics.json`. **Verification**: Task is complete ONLY when `test_metrics.json` exists with valid data. **Dependency**: Must run after T021.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Bound Verification & Statistical Validation (Priority: P3)

**Goal**: Verify theoretical bounds across quantization levels and statistically compare proxy vs. baseline MIPU loops.

**Independent Test**: A report exists showing correlation > 0.8 for at least one quantization level and a paired t-test result (p > 0.05) comparing policy acceptance rates.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T024 [P] [US3] Contract test for report schema in `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/tests/contract/test_report_schema.py`
- [X] T025 [P] [US3] Integration test for end-to-end statistical validation in `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/tests/integration/test_validation.py`

### Implementation for User Story 3

**⚠️ Sequential Execution**: T026A -> T026 -> T027 -> T027B -> T031. T030 runs after T027.

- [X] T026A [US3] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/synchronize_inputs.py`: Generate a fixed set of input prompts with a **fixed random seed (seed=42)** and write them to `data/processed/synchronized_inputs.json`. **Define RL Task**: The task is **GSM8K** correctness. The 'reward' is a binary indicator that is positive if the model's generated answer matches the ground truth, and negative otherwise. **Remove** any custom 'stop/continue' action space. **Edge Case Injection**: **Select samples from the GSM8K dataset** that naturally exhibit **low complexity** using the deterministic rule: `answer_token_length <= 5`. Use the **Llama-3-8B tokenizer** to determine token length. Append these samples to the input set until the edge case count reaches at least 5% of the target n=300 (or a minimum of 30 samples) to ensure statistical power. [UNRESOLVED-CLAIM: c_9cdfb5db — status=not_enough_info] **Verification**: Task must verify that the generated JSON contains these specific edge case prompts and meets the minimum count. This artifact serves as the single source of truth for both T027 and T028 to ensure paired t-test validity. **Dependency**: Must run before T026.
- [X] T026 [US3] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/orchestrate_baseline_proxy.py`: Load `test.parquet`, set a **fixed random seed**, and **load synchronized inputs from T026A** (`data/processed/synchronized_inputs.json`). Trigger T027 (paired execution) with these shared inputs to ensure valid paired comparison. **Remove** any logic that 'triggers' T027/T028; this task only prepares and passes inputs. **Dependency**: Must run after T026A.
- [X] T027 [US3] **Merged Task**: Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/run_paired_mipu.py`. This task merges T027 (Baseline) and T028 (Proxy) into a single execution flow.
 1. Load `test.parquet` and `gap_predictor.pkl`.
 2. For each sample in `synchronized_inputs.json`:
 a. Extract features.
 b. Calculate predicted gap.
 c. **Dynamic Decision**: If `predicted_gap < 0.1`, use Proxy (fast KRR prediction) to determine acceptance. Else, use Full-Hardware-Sync (run actual quantized inference via T013 logic) to determine acceptance.
 d. **Dual Execution**: For EACH sample, run BOTH the Proxy policy (using predictor) AND the Full-Hardware-Sync policy (using actual inference) to generate paired acceptance rates.
 e. Record `acceptance_rate_proxy`, `acceptance_rate_sync`, and `reasoning_score` for the sample.
 f. Record `policy_evaluation_time` (includes full inference time if Sync, or prediction time if Proxy).
 3. Output results to `data/processed/paired_mipu_metrics.json` with schema `{"acceptance_rate_proxy": float, "acceptance_rate_sync": float, "reasoning_score": float, "timing_metadata": {"total_time": float, "inference_only_time": float, "policy_evaluation_time": float, "proxy_count": int, "sync_count": int}}`.
 4. Perform paired t-test on `acceptance_rate_proxy` vs `acceptance_rate_sync` comparing the two policies on the SAME inputs. **Statistical Validity Check**: Before running the t-test, perform a **Shapiro-Wilk test** on the differences. If normality is violated (p < 0.05), **switch to McNemar's test** or a permutation test. **Apply Bonferroni correction** for multiple comparisons (3 quantization levels). **Generate `data/processed/t_test_results.json`** with schema `{"p_value": float, "statistic": float, "method": "bonferroni_corrected_t_test | mcnemar_test | permutation_test", "adjusted_alpha": float, "normality_check": {"shapiro_p_value": float, "method_used": "..."}}`.
 **Verification**: Task is complete ONLY when `paired_mipu_metrics.json` and `t_test_results.json` exist with valid data. **Dependency**: Must run after T026 and T026A.
- [X] T027B [US3] **Merged Task**: Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/verify_bound_consistency.py`. This task merges the calculation and final aggregation logic into a single step.
 1. Load `gap_predictor.pkl` (from T021) and `test.parquet` (from T021A).
 2. Verify `|predicted - actual| < 0.1` holds **separately for INT4, INT8, and FP8 levels**.
 3. Calculate the percentage of samples satisfying the bound for each level.
 4. **Aggregate results** into a global consistency metric.
 5. **Generate `data/processed/final_consistency_summary.json`** with schema `{"per_level_correlations": {"INT4": float, "INT8": float, "FP8": float}, "global_consistency_metric": float, "per_level_satisfaction_pct": {"INT4": float, "INT8": float, "FP8": float}}`.
 **Verification**: Task is complete ONLY when `final_consistency_summary.json` exists with valid data. **Dependency**: Must run after T027, T015, **T021 (model training)**, and **T022 (evaluation)**. **Note**: Requires the `gap_predictor.pkl` from T021 to generate 'predicted' values. **Explicitly requires per-level breakdown** to satisfy FR-007.
- [X] T031 [US3] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/check_generalizability.py`: Perform a domain sensitivity check to verify the GSM8K subset is representative of the target domain. Compare performance metrics on the GSM8K subset against a held-out subset of a different domain (if available) or analyze the distribution of difficulty scores within GSM8K. **Generate `data/processed/generalizability_report.json`** with findings. **Dependency**: Must run after T027.
- [X] T030 [US3] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/services/latency_meter.py`: Measure time for **full MIPU loop** (KRR prediction + inference) vs. **baseline full-hardware-sync method** (full inference). **Read `total_time` from `paired_mipu_metrics.json` (T027) and calculate baseline time** (sum of all sync times if all were sync). **Handle missing keys**: If `total_time` is missing, default to 0 and log a warning. **Calculate `latency_reduction_percentage`** using formula: `(baseline_total_time - proxy_total_time) / baseline_total_time * 100`; **verify** if the reduction meets the ≥90% target (SC-002); write `proxy_total_time`, `baseline_total_time`, `reduction_percentage` (in **seconds**, rounded to **2 decimal places**), `target_met` (boolean) to `data/processed/latency_metrics.json`. **Verification**: Task is complete ONLY when `latency_metrics.json` exists with valid data. **Dependency**: Must run after T027.
- [X] T033 [US3] Generate final research report with all metrics, plots, and statistical conclusions in `docs/reports/001-llmxive-mipu-gap-bounds.md`, including **latency_reduction_percentage** for the **full MIPU loop** (SC-002), consistency findings, **Bonferroni correction method**, and adjusted alpha threshold. **Time Budget Check**: At the start of execution, check the remaining time budget. If less than 15 minutes remain, **prioritize core artifacts** (metrics.json, plots) and **truncate non-essential narrative** to ensure the 6-hour SC-005 limit is respected. **Dependency**: Must run after T027B, T027, T030, T031.
- [X] T034 [US3] Update `state/projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o.yaml` to set `updated_at` to current ISO 8601 timestamp and populate `artifact_hashes` with SHA-256 checksums of `data/processed/*.parquet`, `data/models/*.pkl`, `data/processed/*.json`, and `docs/reports/*.md`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T035A [P] Polish and Cleanup: Update `README.md` with installation steps, dependencies, and usage examples. **Add a "Usage" section with the command `python projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/generate_dataset.py --seed 42`**.
- [ ] T035B [P] Polish and Cleanup: Generate `docs/api.md` with function signatures for all public modules in `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/`.
- [ ] T035C [P] Polish and Cleanup: Remove unused imports, optimize loops in `generate_dataset.py`, and verify streaming works correctly (<7GB memory). **Optimize loops to reduce memory usage to < 4GB**.
- [ ] T035D [P] Polish and Cleanup: Run `quickstart.md` validation and ensure no PII in logs.
- [X] T038 [P] [US2] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/validate_stratification.py`: A post-split validation script for T021A that loads `split_train.parquet`, `split_val.parquet`, and `split_test.parquet` and asserts that the distribution of `quantization_level` is statistically similar across splits (e.g., using Chi-Square test). Log the p-value to `logs/pipeline.log`. **Dependency**: Must run after T021A.
- [ ] T039 [P] [US3] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/generate_visualization_report.py`: Create a `docs/reports/001-llmxive-mipu-gap-bounds_viz.md` containing: 1) Scatter plot of Predicted vs Actual Divergence (colored by quantization level), 2) Bar chart of Bound Satisfaction % per level, 3) Box plot of Reasoning Scores (Proxy vs Baseline). **Dependency**: Must run after T027B and T027.
- [X] T040 [P] [US3] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/validate_statistical_power.py`: Calculate the statistical power (1 - beta) for the paired t-test in T027 given the observed effect size and sample size (n=300). If power < 0.8, **log a WARNING** and append a "Power Analysis" section to the final report (T033) detailing the limitation. **Dependency**: Must run after T027.
- [X] T041 [P] [US1] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/audit_data_integrity.py`: Generate a checksum manifest for `training_sample.parquet` and verify that no rows were dropped silently during the streaming process by comparing the input prompt count (from `synchronized_inputs.json` if available, or the dataset split) against the final output row count. **Dependency**: Must run after T015.
- [ ] T042 [P] [US2] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/verify_model_robustness.py`: Run a sensitivity analysis on the KRR model (T021) by perturbing input features (gradient norms, curvature) by ±5% and measuring the variance in predicted divergence. Log the coefficient of variation to `data/processed/model_robustness.json`. **Dependency**: Must run after T022A.
- [ ] T043 [P] [US3] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/generate_reproducibility_pack.py`: Bundle the final `training_sample.parquet`, `gap_predictor.pkl`, `synchronized_inputs.json`, and `metrics.json` into a single zip archive with a `manifest.json` containing all checksums and environment variables used. **Dependency**: Must run after T033.
- [ ] T044 [P] [US1] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/streaming_memory_profiler.py`: Instrument `generate_dataset.py` to log peak memory usage per 50-sample batch. If peak memory exceeds 6GB, **abort** and log a critical error suggesting a smaller batch size or reduced model quantization. **Dependency**: Must run after T015.
- [ ] T045 [P] [US1] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/quantization_level_coverage_audit.py`: Verify that the final `training_sample.parquet` contains at least 100 samples for each quantization level (INT4, INT8, FP8). If any level has <100 samples, **fail** and report the specific level and count to prevent statistical underpowering in T027B. **Dependency**: Must run after T015.
- [ ] T046 [P] [US2] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/hyperparameter_sweep_krr.py`: Run a grid search for KRR kernel parameters (RBF, Poly) and regularization alpha on the training set, selecting the best model based on validation set correlation. **Dependency**: Must run after T021A and before T021.
- [ ] T047 [P] [US3] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/latency_breakdown_analyzer.py`: Decompose `policy_evaluation_time` in T027 into `inference_time`, `feature_extraction_time`, and `model_prediction_time`. Generate `data/processed/latency_breakdown.json` to identify bottlenecks. **Dependency**: Must run after T027.
- [ ] T048 [P] [US1] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/kl_divergence_distribution_plot.py`: Generate a histogram of `calculated_kl_divergence` values from `training_sample.parquet` to visualize the distribution of quantization gaps. Save to `docs/reports/kl_distribution.png`. **Dependency**: Must run after T015.
- [ ] T049 [P] [US3] Implement `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/bonferroni_correction_validator.py`: Verify that the Bonferroni correction applied in T027 correctly adjusts the alpha threshold for the number of quantization levels tested. Log the adjusted alpha and compare against the raw p-value. **Dependency**: Must run after T027.