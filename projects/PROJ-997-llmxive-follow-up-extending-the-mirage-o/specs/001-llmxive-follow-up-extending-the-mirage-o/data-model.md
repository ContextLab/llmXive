# Data Model: llmXive follow‑up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

## Overview
Defines the schemas for the core artifacts produced by the pipeline: the ground‑truth dataset, the trained predictor, per‑sample prediction results, and the final metrics report. All files are immutable after creation, accompanied by SHA‑256 checksums recorded in `state/`.

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
| `kl_div_fp8` | number or null | KL divergence FP16 ↔ FP8 (null if FP8 not generated). |
| `quantization_level` | string (`"INT4"`, `"INT8"` or `"FP8"`) | Level used for this row (for stratified analysis). |
| `timestamp` | string (date‑time) | Generation timestamp (UTC). |
| `hardware_source` | string (`"CPU"`) | Device that performed the quantized inference (always CPU). |
| `prompt_length_bin` | string (`"short"`, `"medium"`, `"long"`, nullable) | Binned token length for difficulty stratification. |

*All fields are required except `kl_div_fp8` and `prompt_length_bin` (which may be null).*

### GapPredictor (model artifact)

| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | `"KernelRidge"` (or `"MLP"` if swapped). |
| `kernel_params` | object | Hyper‑parameters (e.g., `alpha`, `kernel`). |
| `feature_names` | array[string] | Names of PCA components used for training. |
| `training_metrics` | object | `r2_score`, `mean_absolute_error`, `pearson_correlation` on validation set. |
| `content_hash` | string | SHA‑256 of the serialized model file. |

### GapPredictionResult (per‑sample evaluation)

| Field | Type | Description |
|-------|------|-------------|
| `input_id` | string | Sample identifier. |
| `predicted_gap` | number (≥ 0) | Model‑predicted KL divergence. |
| `actual_gap` | number (≥ 0) | Ground‑truth KL divergence. |
| `absolute_error` | number (≥ 0) | `|predicted_gap − actual_gap|`. |
| `quantization_level` | string (`"INT4"`, `"INT8"`, `"FP8"`) | Quantization level. |

### MetricsReport (final summary)

| Section | Contents |
|---------|----------|
| `correlation_results` | Pearson r per quantization level; boolean `bound_consistency` for each ε (0.05, 0.1, 0.15). |
| `statistical_tests` | Paired t‑statistic, raw p‑value, Bonferroni‑adjusted p, optional permutation p‑value, textual `conclusion`. |
| `latency_reduction` | `proxy_latency_ms`, `baseline_latency_ms`, `reduction_percentage`. |
| `collinearity_check` | VIF for `gradient_norm` and `local_curvature`. |
| `runtime` | Total wall‑clock time (seconds); must be ≤ 21600 s (6 h). |

## Data Flow
1. **Prompt download** → GSM8K (`datasets`).  
2. **Feature extraction** (`extract_features.py`) → `gradient_norm`, `local_curvature`.  
3. **Quantized inference** (`llama_engine.py` / `onnx_fp8_engine.py`) → logits per bit‑width → KL divergence; records `hardware_source`.  
4. **Combine** → `training_sample.parquet` (conforms to `dataset.schema.yaml`).  
5. **Preprocess** (`preprocess.py`) → stratified train/val split, PCA, VIF diagnostics.  
6. **Train** (`train_predictor.py`) → `gap_predictor.pkl` (`predictor.schema.yaml`).  
7. **Evaluate** (`evaluate_predictor.py`) → `gap_predictions.parquet` (`gap_prediction_result.schema.yaml`) and `metrics.json` (`metrics.schema.yaml`).  
8. **Benchmark** (`mipu_benchmark.py`) → latency & paired scores → final `metrics.json`.  
9. **Runtime Guard** (`measure_runtime.py`) → `runtime.json` validated against SC‑005.

## Constraints
* **Immutability** – Files are never overwritten; new derivations receive new filenames.  
* **Checksums** – Every file under `data/` is SHA‑256‑hashed; hashes stored in `state/projects/PROJ-997-...yaml`.  
* **No PII** – GSM8K prompts are public; no personal data introduced.

---
