# Tasks: llmXive follow‑up — Hardware‑validated bounds on the quantization policy gap (MIPU)

**Inputs**: `spec.md`, `plan.md`, contracts in `specs/001-llmxive-follow-up-extending-the-mirage-o/contracts/`, and any existing verified artifacts.

The study is organized into three research phases. All tasks are expressed as canonical checklist items of the form  

```
- [ ] T### [USx?] description … with file path(s)
    • verification: …
```  

Only scientific‑level actions appear; generic scaffolding (directory creation, linting, platform‑state writes) is omitted because the platform supplies those utilities.

---

## Phase 1 – Setup and first end‑to‑end analysis  

- [ ] T015 [US001] Generate the hardware‑ground‑truth dataset (gradient norms, local curvature, and KL divergences for INT4, INT8, and FP8) using `code/cli/generate_ground_truth.py`.  
    • The script extracts training‑side features from a full‑precision Llama‑2‑3B checkpoint, runs **CPU‑only** quantized inference via `llama_engine.py` for INT4 and INT8, attempts FP8 via `onnx_fp8_engine.py`, and writes `data/processed/training_sample.parquet` (conforms to `dataset.schema.yaml`).  
    • If the CPU run exceeds 5 h or OOM, the script **fails loudly** (no GPU off‑load) so the execution stage can report the failure.  
    • verification: script exits with status 0; the Parquet file contains ≥ 300 rows for each present quantization level; for each level the proportion of rows with non‑zero KL ≥ 5 %; `hardware_source` column is present and **must be "CPU" for all rows**; schema validation passes.

- [ ] T016 [US001] Validate dataset statistics and write a summary JSON with `code/cli/validate_dataset_stats.py`.  
    • Loads `data/processed/training_sample.parquet`, computes mean, std, and the non‑zero‑KL proportion for every quantization level, and writes `data/metrics/dataset_stats.json`.  
    • verification: script exits with status 0; the JSON contains keys `nonzero_kl_proportion_int4`, `nonzero_kl_proportion_int8`, `nonzero_kl_proportion_fp8` (if FP8 present) and each value ≥ 0.05; a SHA‑256 checksum of the dataset is recorded in the JSON.

- [ ] T019 [US001] Extract training‑side features (gradient norm and local curvature) from the full‑precision model with `code/data/extract_features.py`.  
    • Reads GSM8K prompts, performs a single forward‑backward pass on the FP16 Llama‑2‑3B model, and writes `data/processed/features.parquet`.  
    • verification: script exits with status 0; the Parquet file contains columns `input_id`, `gradient_norm`, `local_curvature` of numeric type; running with `--seed 42` yields identical values across runs.

- [ ] T023 [US001] Preprocess the dataset: stratified train/validation split, PCA, and VIF diagnostics with `code/data/preprocess.py`.  
    • Uses `training_sample.parquet` and `features.parquet` to (a) create balanced splits `data/processed/train_split.parquet` and `data/processed/val_split.parquet` stratified by `quantization_level` and `prompt_length_bin`, (b) apply PCA retaining ≥ 99 % variance, (c) compute Variance Inflation Factors for `gradient_norm` and `local_curvature`.  
    • Writes the PCA model to `model/pca.pkl` and a diagnostics JSON to `data/metrics/preprocess.json`.  
    • verification: script exits with status 0; each split contains ≥ 150 samples per quantization level; VIF values ≤ 10; PCA explained variance ≥ 0.99; all output files pass their respective schemas.

---

## Phase 2 – Model training, evaluation, and bound verification  

- [ ] T021 [US002] Train a Kernel Ridge Regression predictor on the training split using `code/models/train_predictor.py`.  
    • Reads `train_split.parquet`, fits a KRR model (hyper‑parameter grid limited to 5 combos), and writes the serialized model to `model/gap_predictor.pkl` and hyper‑parameters to `data/metrics/krr_hyperparams.json`.  
    • verification: model loads without error; JSON contains fields `alpha` and `kernel`; training runtime is logged; the script exits with status 0.

- [ ] T022 [US002] Evaluate the trained predictor on the held‑out validation split with `code/models/evaluate_predictor.py`.  
    • Produces per‑sample predictions `data/processed/gap_predictions.parquet` (conforms to `gap_prediction_result.schema.yaml`) and a summary `data/metrics/evaluation.json` containing Pearson r, MAE, and bound‑consistency flags for ε ∈ {0.05, 0.1, 0.15}.  
    • verification: script exits with status 0; overall Pearson r ≥ 0.8; MAE < 0.1; for ε = 0.1 the proportion of samples with `|predicted‑actual| < 0.1` is ≥ 0.95 for each quantization level; `bound_consistency` fields are `true`.

- [ ] T027 [US003] Run the MIPU benchmark comparing the proxy loop (using the predictor) against the full‑hardware‑sync baseline on a 100‑prompt RL reasoning task with `code/validation/mipu_benchmark.py`.  
    • Writes `data/processed/mipu_proxy_results.parquet`, `data/processed/mipu_baseline_results.parquet`, and latency metrics `data/metrics/latency.json`.  
    • verification: script exits with status 0; both result files contain identical `input_id` sets; `latency.json` records `proxy_latency_ms`, `baseline_latency_ms`, and `reduction_percentage` ≥ 90 %.

- [ ] T028 [US003] Perform statistical comparison of proxy vs. baseline with `code/validation/statistical_test.py`.  
    • Computes a paired t‑test on final reasoning scores, applies Bonferroni correction for the three quantization levels, and falls back to a 10 000‑permutation test if Shapiro‑Wilk rejects normality. Outputs `data/metrics/statistical_tests.json`.  
    • verification: script exits with status 0; raw `p_value` > 0.05 and `bonferroni_corrected_p` > 0.05; if a permutation test is used, its `p_value` > 0.05; `conclusion` reads “No significant degradation (p > 0.05)”.

- [ ] T029 [US003] Verify bound consistency across all quantization levels with `code/validation/verify_bound_consistency.py`.  
    • Reads `gap_predictions.parquet` and writes `data/metrics/bound_consistency.json` reporting, for each level, `satisfaction_rate` (proportion with |error| < 0.1) and a boolean `bound_consistency`.  
    • verification: script exits with status 0; `satisfaction_rate` ≥ 0.95 and `bound_consistency` = true for INT4, INT8, and FP8 (if present).

- [ ] T031 [SC‑005] End‑to‑end runtime audit with `code/cli/measure_runtime.py`.  
    • Wraps the full pipeline (T015 → T029), records total wall‑clock time and the number of samples processed, and writes `data/metrics/runtime.json`.  
    • verification: script exits with status 0; `total_seconds` ≤ 21600 (6 h); `sample_count` ≥ 300 and matches the row count of the validation split.

---

## Phase 3 – Reproducibility, reporting, and handoff  

- [ ] T032 [SC‑005] Aggregate all metric artifacts into a single `metrics.json` that validates against `metrics.schema.yaml` using `code/cli/aggregate_results.py`.  
    • Merges correlation results, statistical‑test outcomes, latency reduction, collinearity diagnostics, and runtime into `data/metrics/metrics.json`.  
    • verification: script exits with status 0; `metrics.json` passes schema validation (no extra properties, all required sections present).

- [ ] T033 [US003] Write the final research report `docs/reports/001-llmxive-mipu-gap-bounds.md` and update `quickstart.md` with the reproducible command chain.  
    • The report links to figures under `figures/`, includes tables derived directly from `metrics.json`, discusses edge‑case handling (zero KL, flat gradients, engine load failures), and cites the validation results.  
    • verification: markdown file exists; CI executes the command sequence documented in `quickstart.md` and confirms that all downstream artifacts (`training_sample.parquet`, `gap_predictions.parquet`, `metrics.json`, etc.) are produced without manual intervention.

- [ ] T034 [SC‑005] Archive immutable SHA‑256 hashes for provenance with `code/cli/archive_hashes.py`.  
    • Computes hashes for every file under `data/`, `model/`, and `figures/`, writes `state/artifact_hashes.yaml`.  
    • verification: script exits with status 0; the YAML lists a hash entry for **every** file in the mentioned directories; the verifier confirms the manifest matches the filesystem contents.

---  

*All tasks are ordered to respect data flow: feature extraction precedes ground‑truth generation, which precedes validation, which precedes model training, which precedes evaluation and benchmark, culminating in reproducibility and handoff.* 