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

| ID | Description | File(s) |
|----|-------------|---------|
- [ ] T015 [US001] Generate the hardware‑ground‑truth dataset by (1) extracting `gradient_norm` and `local_curvature` from the full‑precision Llama‑3‑8B model, (2) running **CPU‑only** `llama.cpp` quantized inference for INT4, INT8, and FP8 on each GSM8K prompt, (3) computing KL divergence against the full‑precision logits, and (4) writing a Parquet file `data/processed/training_sample.parquet` that conforms to `dataset.schema.yaml`.   <!-- FAILED-IN-EXECUTION: code/cli/generate_ground_truth.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/cli/generate_ground_truth.py exit=1 --> <!-- FAILED-IN-EXECUTION: tests/cli/test_generate_ground_truth.py exit=4 -->
    • verification: script exits with status 0; the Parquet file contains ≥ 100 rows for **each** quantization level; a downstream check confirms that the `kl_div_*` column is non‑zero for > 5 % of rows (p < 0.05); **all rows have `hardware_source` == "CPU".**  

- [ ] T016 [US001] Validate dataset statistics and write `data/metrics/dataset_stats.json`. The script loads `training_sample.parquet`, computes descriptive statistics (means, stds, proportion of non‑zero KL), checks that the non‑zero KL proportion exceeds the 5 % threshold, and records a SHA‑256 checksum of the dataset.   <!-- FAILED-IN-EXECUTION: code/cli/generate_ground_truth.py exit=1; code/cli/validate_dataset_stats.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/cli/validate_dataset_stats.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/cli/generate_ground_truth.py exit=1; code/cli/validate_dataset_stats.py exit=1 -->
    • verification: JSON file exists, contains fields `nonzero_kl_proportion`, `mean_kl_int4`, `mean_kl_int8`, `mean_kl_fp8`; the `nonzero_kl_proportion` value is ≥ 0.05 and the script exits with status 0.  

- [ ] T019 [US001] Extract training‑side features only (gradient norms, local curvature) and optionally apply PCA. Implemented in `code/data/extract_features.py`. The script reads the raw prompts, runs a single forward‑backward pass on the full‑precision model, and writes `data/processed/features.parquet`.   <!-- FAILED-IN-EXECUTION: code/data/extract_features.py exit=1 -->
    • verification: unit tests confirm that the output has columns `gradient_norm` and `local_curvature` with numeric types; a deterministic seed yields identical values across runs.  

- [ ] T023 [US001] Preprocess the dataset: perform a stratified train/validation split by quantization level and prompt‑length bin, compute Variance Inflation Factors (VIF) for `gradient_norm` and `local_curvature`, and store split indices in `data/processed/train_split.parquet` and `data/processed/val_split.parquet`. Implemented in `code/data/preprocess.py`.  
    • verification: split files exist; chi‑square test on quantization‑level counts yields p > 0.05 (balanced); VIF values for both features are ≤ 10.  

---

## Phase 2 – Model training, evaluation, and bound verification  

- [ ] T021 [US002] Train a Kernel Ridge Regression predictor on the training split, using the PCA‑reduced features if PCA was applied. The script `code/models/train_predictor.py` saves the serialized model to `model/gap_predictor.pkl` and writes training hyper‑parameters to `data/metrics/krr_hyperparams.json`.  
    • verification: the model file loads without error; the JSON contains `alpha` and `kernel` fields; training runtime is logged.  

- [ ] T022 [US002] Evaluate the trained predictor on the held‑out validation set. `code/models/evaluate_predictor.py` writes per‑sample predictions to `data/processed/gap_predictions.parquet` (conforming to `gap_prediction_result.schema.yaml`) and a summary metrics file `data/metrics/evaluation.json` containing Pearson r, MAE, and the bound‑consistency flag (`|predicted‑actual| < 0.1`).  
    • verification: **overall** Pearson r ≥ 0.8, MAE < 0.1, and `bound_consistency` is `true`; **per‑quantization‑level** Pearson r values (`pearson_r_int4`, `pearson_r_int8`, `pearson_r_fp8`) are each ≥ 0.8.  

- [ ] T027 [US003] Benchmark the proxy MIPU loop against the full‑hardware‑sync baseline on a small RL reasoning task. Implemented in `code/validation/mipu_benchmark.py`; the script produces `data/processed/mipu_proxy_results.parquet`, `data/processed/mipu_baseline_results.parquet`, and a latency log `data/metrics/latency.json`.  
    • verification: both result files contain the same set of `input_id`s; latency JSON records `proxy_latency_ms`, `baseline_latency_ms`, and `reduction_percentage`; **`reduction_percentage` must be ≥ 90 %**.  

- [ ] T028 [US003] Perform statistical comparison of the proxy vs. baseline. The same `mipu_benchmark.py` script (or a helper `code/validation/statistical_test.py`) computes a paired t‑test on the final reasoning scores, applies a Bonferroni correction for the three quantization levels, and writes `data/metrics/statistical_tests.json` with fields `t_statistic`, `p_value`, `bonferroni_corrected_p`, and `conclusion`. If normality fails, it falls back to a Wilcoxon signed‑rank test.  
    • verification: `p_value` > 0.05 **and** `bonferroni_corrected_p` > 0.05; `conclusion` reads “No significant degradation (p > 0.05)”.  

- [ ] T029 [US003] Verify bound consistency across all three quantization levels. A dedicated script `code/validation/verify_bound_consistency.py` reads `gap_predictions.parquet` and checks the proportion of samples where `|predicted‑actual| < 0.1` for INT4, INT8, and FP8 separately, writing `data/metrics/bound_consistency.json`.  
    • verification: each level reports a `satisfaction_rate` ≥ 0.95 **and** a boolean `bound_consistency` = true for that level, matching the `correlation_results[LEVEL].bound_consistency` field in the schema.  

- [ ] T031 [SC‑005] End‑to‑end runtime audit. `code/cli/measure_runtime.py` wraps the full pipeline (T015 → T029) and records total wall‑clock seconds in `data/metrics/runtime.json`.  
    • verification: `total_seconds` ≤ 21600 (6 h) and `sample_count` ≥ 300 **and** `sample_count` equals the number of rows in the validation split generated by T023.  

---

## Phase 3 – Reproducibility, reporting, and handoff  

- [ ] T032 [SC‑005] Aggregate all metrics into a single `metrics.json` that validates against `metrics.schema.yaml`. Implemented in `code/cli/aggregate_results.py`; the script merges correlation results, statistical tests, latency, and collinearity diagnostics into `data/metrics/metrics.json`.  
    • verification: JSON validates against `metrics.schema.yaml` (no additional properties, all required fields present) and contains the four top‑level sections: `correlation_results`, `statistical_tests`, `latency_reduction`, `collinearity_check`.  

- [ ] T013 [US003] Write the final research report. Create `docs/reports/001-llmxive-mipu-gap-bounds.md` that (a) describes methods, (b) embeds tables/figures generated directly from the metric files, (c) discusses edge‑case handling (zero KL, flat gradients, engine load failures), and (d) updates `quickstart.md` with the reproducible command chain.  
    • verification: the markdown references existing figure files under `figures/`; a CI step runs the command documented in `quickstart.md` and asserts successful generation of all downstream artifacts without manual intervention.  

- [ ] T034 [SC‑005] Archive immutable hashes for provenance. `code/cli/archive_hashes.py` computes SHA‑256 hashes for every artifact under `data/` and `model/`, writes `state/artifact_hashes.yaml`.  
    • verification: the YAML file lists a hash entry for **every** file under `data/` and `model/`; CI verifier confirms the manifest matches the actual filesystem contents.  
