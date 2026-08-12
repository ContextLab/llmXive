# Data Model: llmXive follow-up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

## Overview

This document defines the data structures used for the `training_sample.parquet`, the `predictor` model artifact, and the `metrics` report. All data is checksummed and immutable.

## Entities

### TrainingSample
Represents a single input instance used for feature extraction and gap calculation.

| Field | Type | Description |
|-------|------|-------------|
| `input_id` | string | Unique identifier for the prompt. |
| `prompt` | string | The input text (e.g., GSM8K question). |
| `gradient_norm` | float | L2 norm of the gradient vector from full-precision training step. |
| `local_curvature` | float | Approximation of local curvature (e.g., Hessian trace diagonal). |
| `kl_div_int4` | float | KL divergence between FP16 and INT4 quantized logits. |
| `kl_div_int8` | float | KL divergence between FP16 and INT8 quantized logits. |
| `kl_div_fp8` | float | KL divergence between FP16 and FP8 quantized logits. |
| `quantization_level` | string | "INT4", "INT8", or "FP8" (for stratified analysis). |
| `timestamp` | datetime | Generation timestamp. |

### QuantizedInferenceResult
Intermediate artifact from the `llama.cpp` engine.

| Field | Type | Description |
|-------|------|-------------|
| `input_id` | string | Reference to `TrainingSample`. |
| `quantization_level` | string | "INT4", "INT8", or "FP8". |
| `logits` | array(float) | Quantized output logits (stored as float32 for analysis). |
| `log_probs` | array(float) | Log probabilities derived from logits. |
| `status` | string | "success", "failed_load", "numeric_error". |

### GapPredictor
Trained regression model artifact.

| Field | Type | Description |
|-------|------|-------------|
| `model_type` | string | "KernelRidge", "MLP", etc. |
| `kernel_params` | object | Hyperparameters (alpha, gamma, etc.). |
| `feature_names` | list(string) | ["PCA1", "PCA2"]. |
| `training_metrics` | object | R2, MAE, Pearson r on validation set. |
| `content_hash` | string | SHA-256 of the model weights/params. |

## Data Flow

1.  **Input**: `gsm8k` (raw prompts) + `llama-3-8b` (model).
2.  **Process**:
    *   `extract_features.py`: Generates `gradient_norm`, `local_curvature`.
    *   `generate_ground_truth.py`: Runs `llama.cpp` (INT4/8/FP8) → `QuantizedInferenceResult`.
    *   `utils/stats.py`: Calculates KL divergence → `TrainingSample`.
3.  **Output**: `data/processed/training_sample.parquet`.
4.  **Training**: `models/train_predictor.py` consumes `TrainingSample` → `GapPredictor`.
5.  **Validation**: `models/evaluate_predictor.py` → `data/metrics/metrics.json`.

## Constraints

*   **Immutability**: Once `training_sample.parquet` is written, it is never modified. New derivations create new files.
*   **Checksums**: All files in `data/` are checksummed (SHA-256) and recorded in `state/`.
*   **PII**: No personally identifying information is included in prompts or metadata.
