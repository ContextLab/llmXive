# Tasks: llmXive follow-up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

**Input**: Design documents from `/specs/001-llmxive-mipu-gap-bounds/` (research.md, data-model.md, contracts/)
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Revision note (re-plan)**: The duplicate task identity `T021` (used for both a unit-test task and the `train_predictor.py` task) has been repaired: the predictor-training task is now **T021B**, and the evaluation task is now **T022A**. All requirements and verified artifacts are preserved. Rejected tasks **T039** and **T042** are reopened below with complete, verifiable deliverables. Remaining pending polish tasks (formerly T035A–D, T043–T049) have been consolidated into grouped substantive tasks without dropping acceptance criteria.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Paths are relative to the repository root; the project lives under `projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/`.

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001a [P] Create project directories: `code/`, `code/lib/`, `code/services/`, `code/cli/`, `code/config/`, `code/models/`, `tests/`, `data/raw/`, `data/processed/`, `data/models/`, `docs/reports/`. **Verification**: each directory exists via `os.path.isdir`.
- [ ] T001b [P] Initialize Python packages: `__init__.py` files in each directory from T001a.
- [ ] T002 Create `requirements.txt` containing: `transformers>=4.30.0`, `llama-cpp-python>=0.2.0`, `scikit-learn>=1.3.0`, `datasets>=2.14.0`, `pandas>=2.0.0`, `numpy>=1.24.0`, `torch>=2.0.0`, `pytest>=7.0.0`, `einops>=0.6.0`, `seaborn>=0.12.0`, `matplotlib>=3.7.0`.
- [ ] T003 [P] Configure linting and formatting: `.ruff.toml` and `pyproject.toml` with `[tool.black]`.

---

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T005 [P] Implement `code/lib/streaming_utils.py` for chunked dataset loading and checksumming.
- [ ] T006 [P] Create `code/lib/error_handling.py` with strict failure modes (no synthetic fallbacks).
- [ ] T007 Define `TrainingSample`, `QuantizedInferenceResult`, and `GapPredictionResult` classes in `code/models/entities.py`. `TrainingSample` must contain `input_id`, `gradient_norms`, `local_curvature`, `quantized_logits`, and `calculated_kl_divergence` (FR-002/003). `GapPredictionResult` must contain `predicted_gap`.
- [ ] T008 Create `code/config/logging_config.py` (FileHandler to `logs/pipeline.log`, JSON formatting).
- [ ] T009 Create `code/config/env_config.py` with `load_config()` and `.env.example` (MODEL_PATH, DATASET_ID, ACCEPTANCE_THRESHOLD).
- [ ] T017 [P] Implement `code/services/logger.py` with `get_logger()` writing JSON lines to `logs/pipeline.log` with keys `sample_id`, `status`, `error_code` (Constitution Principle I).
- [ ] T036 [P] [US1] Implement `code/cli/verify_model_availability.py`: check for `meta-llama/Llama-3-8B` and quantized `.gguf` files in `data/raw/`; FAIL LOUDLY listing missing files and how to obtain them. Runs before T015.
- [ ] T037 [P] [US1] Implement `code/services/quantization_level_validator.py`: verify the input dataset contains valid non-empty logits for INT4, INT8, FP8 before T014; raise `MissingQuantizationLevelError` with the affected sample ID. Runs before T015.

---

## Phase 3: User Story 1 — Hardware-Validated Gap Dataset Generation (P1) 🎯 MVP

**Independent Test**: `training_sample.parquet` exists with `input_id`, `gradient_norms`, `local_curvature`, `quantized_logits`, `calculated_kl_divergence`; the KL column is non-zero for a statistically significant portion of rows.

- [ ] T010 [P] [US1] Unit test for KL divergence edge cases (zero-divergence) in `tests/unit/test_gap_calculator.py`.
- [ ] T011 [P] [US1] Integration test for data streaming and schema validation in `tests/integration/test_data_generation.py`.
- [ ] T012 [P] [US1] Implement `code/services/feature_extractor.py`: load `meta-llama/Llama-3-8B` in BF16; synthetic training step on first 300 GSM8K samples (seed=42) — perturbed target, MSE loss, backward pass — computing gradient norms (Lp) and local curvature (Hutchinson's estimator).
- [ ] T013 [US1] Implement `code/services/quantized_inference.py`: wrap `llama-cpp-python` for INT4/INT8/FP8 CPU inference; expect `model-Q4_K_M.gguf`, `model-Q8_0.gguf`, `model-FP8.gguf` in `data/raw/`. On `llama_cpp.LlamaError`/`OSError`, log and skip the sample (Spec Edge Case 3).
- [ ] T014 [US1] Implement `code/services/gap_calculator.py`: exact KL divergence between full-precision and quantized logits with epsilon for numerical stability.
- [ ] T015 [US1] Implement `code/cli/generate_dataset.py` orchestrating: (1) stream GSM8K via `datasets.load_dataset(..., streaming=True)`; (2) extract features (T012); (3) quantized inference for all three levels (T013); (4) KL divergence (T014); (5) time monitoring per SC-005 (rolling average of last 10 samples; stop early only if >300 samples done); (6) validate at least one sample per quantization level — FAIL LOUDLY if any level has zero samples (FR-004); (7) save `data/processed/training_sample.parquet`. Runs after T012–T014, T017, T036, T037.
- [ ] T016 [US1] Append summary log entry to `generate_dataset.py` recording the actual observed proportion of non-zero `calculated_kl_divergence` samples.
- [ ] T018 [US1] Implement `code/services/vif_checker.py`: VIF for gradient norms and curvature; log to `logs/pipeline.log`.

---

## Phase 3.2: Feature Diagnostics

- [ ] T019 [US1] Implement `code/cli/extract_features_pca.py`: PCA on gradient norms/curvature from `training_sample.parquet`; save `data/processed/features_pca.parquet`. Runs after T015.
- [ ] T019c [US1] Implement `code/cli/prepare_vif_data.py` from `features_pca.parquet`. Runs after T019.
- [ ] T019d [US1] Implement `code/cli/calculate_vif.py` using `vif_checker.py`; log results. Runs after T019c.
- [ ] T019e [US1] Implement `code/cli/evaluate_vif.py`: if VIF > 10, HALT with fatal error requiring feature re-selection. Runs after T019d.

---

## Phase 4: User Story 2 — Training-Signal Predictor Model (P2)

**Independent Test**: `data/models/gap_predictor.pkl` exists, loads, and achieves Pearson r > 0.8 on the held-out test set (SC-001).

- [ ] T020 [P] [US2] Unit test for KRR training pipeline and hyperparameter grid in `tests/unit/test_predictor.py`.
- [ ] T021A [US2] Implement `code/cli/prepare_data_split.py`: load stratified data from T023; create train/val/test splits written to `data/processed/split_train.parquet`, `split_val.parquet`, `split_test.parquet`. If a quantization level is missing from a split, PROCEED with available levels, log a warning, and record present levels in split metadata. Runs after T023.
- [ ] T021B [US2] Implement `code/cli/train_predictor.py` (formerly the duplicate-ID T021): load `split_train.parquet`; assert training set contains samples from all available quantization levels; train KRR; save `data/models/gap_predictor.pkl`. **Verification**: artifact exists and loads. Runs after T021A.
- [ ] T022 [US2] Implement evaluation logic in `code/services/evaluator.py`: Pearson r and MAE between predicted and actual divergence.
- [ ] T022A [US2] Implement `code/cli/evaluate_on_test.py`: load `split_test.parquet` and `gap_predictor.pkl`; run evaluator; write `data/processed/test_metrics.json`. **Verification**: file exists with valid data. Runs after T021B.
- [ ] T023 [US2] Implement `code/cli/stratify_training_data.py`: stratify `training_sample.parquet` by `quantization_level` and concatenate into a single training set. Runs after T019e.
- [ ] T038 [P] [US2] Implement `code/cli/validate_stratification.py`: assert `quantization_level` distribution is similar across splits (Chi-Square test); log p-value. Runs after T021A.

---

## Phase 5: User Story 3 — Bound Verification & Statistical Validation (P3)

**Independent Test**: report showing correlation > 0.8 for at least one quantization level and a paired t-test result (p > 0.05) comparing policy acceptance rates.

- [ ] T024 [P] [US3] Contract test for report schema in `tests/contract/test_report_schema.py`.
- [ ] T025 [P] [US3] Integration test for end-to-end statistical validation in `tests/integration/test_validation.py`.
- [ ] T026A [US3] Implement `code/cli/synchronize_inputs.py`: fixed seed (42) input set written to `data/processed/synchronized_inputs.json`. RL task = GSM8K correctness with binary reward. Edge-case injection: GSM8K samples with `answer_token_length <= 5` (Llama-3-8B tokenizer) appended until ≥5% of n=300 (min 30). Verify the JSON contains these prompts and meets the minimum count. Single source of truth for T026/T027.
- [ ] T026 [US3] Implement `code/cli/orchestrate_baseline_proxy.py`: load `split_test.parquet`, fixed seed, load `synchronized_inputs.json`; prepare and pass shared inputs (no triggering logic). Runs after T026A.
- [ ] T027 [US3] Implement `code/cli/run_paired_mipu.py`: for each synchronized sample, extract features, predict gap; dynamic decision (predicted < 0.1 → proxy, else full hardware sync); dual execution of both policies; record `acceptance_rate_proxy`, `acceptance_rate_sync`, `reasoning_score`, `policy_evaluation_time`. Output `data/processed/paired_mipu_metrics.json` with timing metadata (total_time, inference_only_time, policy_evaluation_time, proxy_count, sync_count). Paired t-test with Shapiro-Wilk normality check (fall back to McNemar/permutation if violated), Bonferroni correction for 3 levels; output `data/processed/t_test_results.json` with p_value, statistic, method, adjusted_alpha, normality_check. **Verification**: both JSON files exist with valid data. Runs after T026, T026A.
- [ ] T027B [US3] Implement `code/cli/verify_bound_consistency.py`: load `gap_predictor.pkl` and `split_test.parquet`; verify `|predicted - actual| < 0.1` separately for INT4, INT8, FP8 (FR-007); compute per-level satisfaction percentages and aggregate global consistency; write `data/processed/final_consistency_summary.json` with `per_level_correlations`, `global_consistency_metric`, `per_level_satisfaction_pct`. Runs after T021B, T022A, T027.
- [ ] T030 [US3] Implement `code/services/latency_meter.py`: read `total_time` from `paired_mipu_metrics.json` (default 0 with warning if missing); compute baseline as sum of all sync times; `latency_reduction_percentage = (baseline - proxy)/baseline * 100`; verify ≥90% target (SC-002); write `proxy_total_time`, `baseline_total_time`, `reduction_percentage` (seconds, 2 decimals), `target_met` to `data/processed/latency_metrics.json`. Runs after T027.
- [ ] T031 [US3] Implement `code/cli/check_generalizability.py`: domain sensitivity check (GSM8K subset vs. held-out different-domain subset, or within-GSM8K difficulty distribution); write `data/processed/generalizability_report.json`. Runs after T027.
- [ ] T033 [US3] Generate final research report `docs/reports/001-llmxive-mipu-gap-bounds.md` with all metrics, plots, statistical conclusions, latency reduction (SC-002), consistency findings, Bonferroni method and adjusted alpha. Time-budget check: if <15 min remain, prioritize core artifacts. Runs after T027B, T027, T030, T031.
- [ ] T034 [US3] Update `state/projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o.yaml`: set `updated_at` (ISO 8601) and populate `artifact_hashes` with SHA-256 checksums of `data/processed/*.parquet`, `data/models/*.pkl`, `data/processed/*.json`, `docs/reports/*.md`.
- [ ] T040 [P] [US3] Implement `code/cli/validate_statistical_power.py`: compute power (1 − β) for the T027 paired t-test given observed effect size and n=300; if power < 0.8, log WARNING and append a "Power Analysis" section to the final report. Runs after T027.
- [ ] T041 [P] [US1] Implement `code/cli/audit_data_integrity.py`: checksum manifest for `training_sample.parquet`; verify no silent row drops by comparing input prompt count against final output row count. Runs after T015.

---

## Phase 6: Redo of verifier-rejected tasks

- [ ] T039 [P] [US3] **REDO** Implement `code/cli/generate_visualization_report.py` as a COMPLETE, runnable script (no truncation) that reads `data/processed/final_consistency_summary.json`, `data/processed/paired_mipu_metrics.json`, and `split_test.parquet` predictions, and generates three plots saved under `docs/reports/figures/`: (1) scatter of predicted vs. actual divergence colored by quantization level, (2) bar chart of bound-satisfaction % per level, (3) box plot of reasoning scores (Proxy vs. Baseline). Then write `docs/reports/001-llmxive-mipu-gap-bounds_viz.md` embedding all three figures with Markdown image links and a short caption per figure. **Verification**: the script runs end-to-end without error, all three PNG files exist, and the `_viz.md` file exists containing links to all three figures. Runs after T027 and T027B.
- [ ] T042 [P] [US2] **REDO** Implement `code/cli/verify_model_robustness.py` as a COMPLETE, runnable script (no truncation): load `gap_predictor.pkl` and `split_test.parquet`; perturb input features (gradient norms, curvature) by ±5% with fixed seed; measure variance in predicted divergence across perturbations; compute the coefficient of variation; write `data/processed/model_robustness.json` with schema `{"perturbation_pct": 0.05, "coefficient_of_variation": float, "per_feature_cv": {"gradient_norm": float, "local_curvature": float}, "n_samples": int}`. **Verification**: script runs end-to-end and `data/processed/model_robustness.json` exists with valid numeric values. Runs after T022A.

---

## Phase 7: Consolidated validation, robustness, and handoff

- [ ] T050 [US1] Dataset coverage and memory audit: extend `code/cli/generate_dataset.py` (or a companion `code/cli/quantization_level_coverage_audit.py`) to (a) verify `training_sample.parquet` contains at least 100 samples per quantization level (INT4, INT8, FP8), failing with the specific level and count otherwise, and (b) log peak memory usage per 50-sample batch, aborting with a critical error if peak memory exceeds 6 GB. Also generate a histogram of `calculated_kl_divergence` saved to `docs/reports/kl_distribution.png`. **Verification**: audit output present in `logs/pipeline.log` with per-level counts and peak-memory entries; `kl_distribution.png` exists. Runs after T015.
- [ ] T051 [US2] KRR hyperparameter sweep: implement `code/cli/hyperparameter_sweep_krr.py` — grid search over kernels (RBF, Poly) and regularization alpha on `split_train.parquet`, selecting the best model by validation-set Pearson correlation; save the best model to `data/models/gap_predictor.pkl` (overwriting only if validation correlation improves) and record the sweep grid and selected hyperparameters in `data/processed/krr_sweep_results.json`. **Verification**: sweep JSON exists with grid and selected params; `gap_predictor.pkl` reloads. Runs after T021A and before re-running T021B/T022A if the model changes.
- [ ] T052 [US3] Latency breakdown and Bonferroni validation: implement `code/cli/latency_breakdown_analyzer.py` decomposing `policy_evaluation_time` from `paired_mipu_metrics.json` into `inference_time`, `feature_extraction_time`, and `model_prediction_time`, writing `data/processed/latency_breakdown.json`; and `code/cli/bonferroni_correction_validator.py` verifying the T027 correction adjusts alpha for 3 quantization levels, logging adjusted alpha vs. raw p-value. **Verification**: both JSON/log outputs exist with valid values. Runs after T027.
- [ ] T053 [P] Reproducibility pack and documentation handoff: (a) implement `code/cli/generate_reproducibility_pack.py` bundling `training_sample.parquet`, `gap_predictor.pkl`, `synchronized_inputs.json`, and final metrics into a zip with `manifest.json` (checksums + environment variables); (b) update `README.md` with installation, dependencies, and a Usage section including `python projects/PROJ-997-llmxive-follow-up-extending-the-mirage-o/code/cli/generate_dataset.py --seed 42`; (c) generate `docs/api.md` with public function signatures for `code/` modules; (d) run `quickstart.md` validation and confirm no PII in logs. **Verification**: zip with manifest exists, README contains the usage command, `docs/api.md` exists, quickstart check passes. Runs after T033 and T039.

---

## Dependencies and requirement coverage

- **FR-001 (feature extraction)**: T012, T015 — `python code/cli/generate_dataset.py --seed 42`.
- **FR-002 (CPU quantized inference)**: T013, T036, T037, T015.
- **FR-003 (exact KL divergence)**: T014, T010, T015.
- **FR-004 (joint KRR across INT4/INT8/FP8)**: T023, T021A, T021B, T051.
- **FR-005 (Pearson r on held-out set)**: T022, T022A, T038.
- **FR-006 (paired t-test proxy vs. baseline)**: T026A, T026, T027, T040, T052.
- **FR-007 (bound consistency across three levels)**: T027B, T039.
- **SC-001**: T022A; **SC-002**: T030, T052; **SC-003**: T027; **SC-004**: T027B; **SC-005**: T015 time monitoring, T050 memory audit.

**Execution order**: Phase 1 → Phase 2 → T012/T013/T014 (parallel) → T015 → Phase 3.2 → T023 → T021A → T021B → T022A → T026A → T026 → T027 → T027B/T030/T031/T040 (parallel after T027) → T033 → T034 → Phase 6/7 (T039, T042, T050–T053 as dependencies allow).

## Revision behavior

Verified checked tasks are preserved with their identities (duplicate `T021` identity repaired by renaming the predictor-training task to T021B; no requirements dropped). T039 and T042 are reopened per verifier rejection with complete deliverable specifications. Pending polish tasks were consolidated into T050–T053, retaining every acceptance criterion (coverage audit, memory profiling, KL histogram, hyperparameter sweep, latency breakdown, Bonferroni validation, reproducibility pack, README/API docs, quickstart/PII check).
