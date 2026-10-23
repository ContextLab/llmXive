# Data Model: llmXive follow‑up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

## Overview
Defines the schemas for the core artifacts produced by the pipeline: the ground‑truth dataset, the trained predictor, per‑sample prediction results, and the final metrics report. All files are immutable after creation and accompanied by SHA‑256 checksums recorded in `state/`.

## Entities

### TrainingSample
| Field | Type | Description |
|-------|------|-------------|
| `input_id` | string | Unique identifier for the prompt. |
| `prompt` | string | GSM8K question text. |
| `gradient_norm` | number | L2 norm of the gradient vector (full‑precision). |
| `local_curvature` | number | Approximation of Hessian trace (full‑precision). |
| `kl_div_int4` | number | KL divergence FP16 ↔ INT4. |
| `kl_div_int8` | number | KL divergence FP16 ↔ INT8. |
| `kl_div_fp8` | number | KL divergence FP16 ↔ FP8. |
| `quantization_level` | string | `"INT4"`, `"INT8"` or `"FP8"` (used for stratified analysis). |
| `timestamp` | string (date‑time) | Generation timestamp (UTC). |
| `hardware_source` | string (optional) | `"CPU"` or `"GPU"` indicating where quantized inference ran. |
| `prompt_length_bin` | string (optional) | `"short"`, `"medium"` or `"long"` for difficulty stratification. |

*All fields are required except the optional `hardware_source` and `prompt_length_bin`, which are included for downstream covariate analysis.*

### GapPredictor (model artifact)

| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | `"KernelRidge"` (or `"MLP"` if swapped). |
| `kernel_params` | object | Hyperparameters (e.g., `alpha`, `gamma`). |
| `feature_names` | array[string] | Names of PCA components used. |
| `training_metrics` | object | `r2_score`, `mean_absolute_error`, `pearson_correlation` on validation set. |
| `content_hash` | string | SHA‑256 of serialized model file. |

### GapPredictionResult (per‑sample evaluation)

| Field | Type | Description |
|-------|------|-------------|
| `input_id` | string | Sample identifier. |
| `predicted_gap` | number | Model‑predicted KL divergence (≥ 0). |
| `actual_gap` | number | Ground‑truth KL divergence (≥ 0). |
| `absolute_error` | number | `|predicted_gap − actual_gap|`. |
| `quantization_level` | string | `"INT4"`, `"INT8"` or `"FP8"`. |

### MetricsReport (final summary)

| Section | Contents |
|---------|----------|
| `correlation_results` | Pearson r per quantization level and boolean `bound_consistency` for each ε; also reports sensitivity across ε values. |
| `statistical_tests` | Paired t‑test (`t_statistic`, `p_value`), Bonferroni‑adjusted p, optional Wilcoxon results, textual `conclusion`. |
| `latency_reduction` | `proxy_latency_ms`, `baseline_latency_ms`, `reduction_percentage`. |
| `collinearity_check` | VIF for `gradient_norm` and `local_curvature`. |
| `runtime` | Total wall‑clock time (seconds) for the entire pipeline; must be ≤ 21600 s (6 h). |

## Data Flow
1. **Prompt download** → GSM8K (`datasets`).  
2. **Feature extraction** (`extract_features.py`) → `gradient_norm`, `local_curvature`.  
3. **Quantized inference** (`llama_engine.py`) → logits per bit‑width → KL divergence; records `hardware_source`.  
4. **Combine** → `training_sample.parquet` (conforms to `dataset.schema.yaml`).  
5. **Preprocess** (`preprocess.py`) → stratified train/val split, PCA, VIF.  
6. **Train** (`train_predictor.py`) → `gap_predictor.pkl` (`predictor.schema.yaml`).  
7. **Evaluate** (`evaluate_predictor.py`) → per‑sample `gap_predictions.parquet` (`gap_prediction_result.schema.yaml`) and `metrics.json` (`metrics.schema.yaml`).  
8. **Benchmark** (`mipu_benchmark.py`) → latency & paired scores → final `metrics.json`.  
9. **Runtime Guard** (`measure_runtime.py`) → `runtime.json` validated against SC‑005.

## Constraints
* **Immutability** – Once written, files are never overwritten; new derivations receive new filenames.  
* **Checksums** – Every file under `data/` is SHA‑256‑hashed; hashes stored in `state/projects/PROJ-997-...yaml`.  
* **No PII** – Prompts are public GSM8K content; no personal data introduced.
