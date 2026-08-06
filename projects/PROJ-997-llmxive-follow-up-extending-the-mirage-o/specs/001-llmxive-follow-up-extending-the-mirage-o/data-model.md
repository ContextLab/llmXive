# Data Model: llmXive follow-up: extending "The Mirage of Optimizing Training Policies: Monotonic Inference Polici"

## Overview

This document defines the data structures used throughout the project, ensuring consistency between data generation, model training, and validation. The data model is designed to support the "Hardware-Grounded Validation" principle by strictly separating training-side features from hardware-measured targets.

## Entities

### 1. TrainingSample

Represents a single input instance used for feature extraction and gap calculation.

**Fields**:
- `input_id`: Unique identifier for the sample (string).
- `prompt`: The input prompt text (string).
- `gradient_norm`: **RESTORED**. The L2 norm of the gradients w.r.t. input embeddings (float). Required by FR-001.
- `local_curvature`: **RESTORED**. The local curvature estimate via Hutchinson's estimator (float). Required by FR-002.
- `logits_magnitude`: **DEPRECATED**. Removed as a primary feature; retained only for legacy reference if needed.
- `quantization_level`: The quantization level used for the ground-truth measurement (enum: "INT4", "INT8", "FP8").
- `quantized_logits`: The logits output from the quantized engine (array of floats).
- `full_precision_logits`: The logits output from the full-precision engine (array of floats).
- `kl_divergence`: The calculated KL divergence between full-precision and quantized logits (float).
- `ground_truth_answer`: The ground-truth answer for the prompt (string, nullable). Only populated for GSM8K subset.
- `is_reasoning_task`: Boolean flag indicating if the sample is from the GSM8K reasoning subset (boolean).
- `processing_status`: Status of the sample processing (enum: "success", "skipped", "error").
- `error_message`: Error message if processing failed (string, nullable).

**Constraints**:
- `kl_divergence` must be non-negative.
- `processing_status` must be "success" for the sample to be used in model training.
- `gradient_norm` and `local_curvature` must be extracted from the full-precision model state.
- `ground_truth_answer` must be present if `is_reasoning_task` is true.

### 2. GapPredictionResult

Represents the output of the Gap Predictor model.

**Fields**:
- `input_id`: Unique identifier for the sample (string).
- `predicted_gap`: The predicted KL divergence from the model (float).
- `actual_gap`: The ground-truth KL divergence (float).
- `absolute_error`: |predicted_gap - actual_gap| (float).
- `quantization_level`: The quantization level used (enum: "INT4", "INT8", "FP8").

**Constraints**:
- `absolute_error` must be non-negative.
- `predicted_gap` must be non-negative.

## Data Flow

1.  **Input**: Prompts (from GSM8K or Ultrachat_200k).
2.  **Feature Extraction**: `TrainingSample` is populated with `gradient_norm` and `local_curvature` (via forward/backward passes).
3.  **Inference**: `TrainingSample` is populated with `quantized_logits` and `full_precision_logits`.
4.  **Gap Calculation**: `kl_divergence` is computed and stored in `TrainingSample`.
5.  **Model Training**: `TrainingSample` (with `processing_status` = "success") is used to train the `GapPredictor`.
6.  **Prediction**: `GapPredictionResult` is generated for test samples.
7.  **Validation**: `GapPredictionResult` is used to compute correlation, MAE, and bound verification.

## Storage Format

- **Raw Data**: Parquet files in `data/raw/` (streamed from verified sources if used, or locally generated).
- **Processed Data**: Parquet files in `data/processed/` containing `TrainingSample` records.
- **Model Artifacts**: Pickle files in `data/models/` containing the trained KRR model.
- **Results**: JSON/CSV files in `data/results/` containing `GapPredictionResult` records.

## Versioning

- **Schema Version**: 1.0.1
- **Last Updated**: 2026-08-06
- **Change Log**: Restored `gradient_norm` and `local_curvature`. Removed `logits_magnitude` as primary feature. Added `ground_truth_answer` and `is_reasoning_task` to support the Static RL Simulation and t-test on reasoning scores.