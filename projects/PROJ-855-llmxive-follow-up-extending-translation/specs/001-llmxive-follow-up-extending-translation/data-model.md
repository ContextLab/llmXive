# Data Model: llmXive follow-up: extending "Translation as a Bridging Action"

## Overview

This document defines the data structures for the synthetic generation pipeline, the training dataset, and the model outputs. All data is stored in Parquet format for efficient I/O and schema enforcement.

## Entities

### 1. ManipulationEpisode
A single record representing one bi-manual manipulation attempt.

**Source**: `code/generate_data.py`  
**Target**: `data/raw/episodes.parquet`

| Column Name | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `episode_id` | `string` | Unique identifier (UUID) | Unique, non-null |
| `geometry` | `struct` | Initial object bounding box | Contains `min_x`, `min_y`, `min_z`, `max_x`, `max_y`, `max_z` |
| `translation_sequence` | `list<list<float>>` | Sequence of 3D translation vectors | Shape: [T, 3]; T=10 (time steps) |
| `tipping_angle` | `float` | Max deviation of COM from base (degrees) | ≥ 0.0 |
| `slippage_distance` | `float` | Max relative displacement at contact (meters) | ≥ 0.0 |
| `stability_label` | `int` | Binary outcome (1=Success, 0=Failure) | 0 or 1 |
| `metadata` | `struct` | Simulation parameters | Contains `seed`, `object_mass`, `friction_coeff`, `noise_sigma` |

**Derived Logic**:
*   `stability_label` = 1 if `tipping_angle` < 15.0 AND `slippage_distance` < 0.02
*   `stability_label` = 0 otherwise
*   **Exclusion**: No columns for rotation, torque, or force exist.

### 2. TrainingBatch
A processed batch of episodes prepared for model input.

**Source**: `code/utils/data_utils.py`  
**Target**: `data/processed/train_batch_*.parquet`

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `input_translation` | `tensor` | Normalized translation sequence (T, 3) |
| `input_geometry` | `tensor` | Normalized bounding box (6) |
| `target_label` | `int` | Stability label |

### 3. ModelPrediction
Output of the inference/evaluation step.

**Source**: `code/evaluate.py`  
**Target**: `data/processed/predictions.parquet`

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `episode_id` | `string` | Reference to original episode |
| `model_pred_prob` | `float` | Probability of success (0.0-1.0) |
| `model_pred_label` | `int` | Thresholded prediction (0.5) |
| `baseline_pred_label` | `int` | Prediction from geometry-only model |
| `shuffled_pred_label` | `int` | Prediction from shuffled-translation model |
| `actual_label` | `int` | Ground truth |
| `correct_model` | `bool` | True if `model_pred_label` == `actual_label` |
| `correct_baseline` | `bool` | True if `baseline_pred_label` == `actual_label` |
| `correct_shuffled` | `bool` | True if `shuffled_pred_label` == `actual_label` |

### 4. MetricsReport
Final statistics linked to data checksums for traceability (Principle IV).

**Source**: `code/evaluate.py`  
**Target**: `data/processed/metrics_report.json`

| Field | Type | Description |
| :--- | :--- | :--- |
| `data_checksum` | `string` | Hash of `data/raw/episodes.parquet` from `data/checksums.json` |
| `model_accuracy` | `float` | Accuracy of translation-only model on test set |
| `baseline_accuracy` | `float` | Accuracy of geometry-only baseline |
| `shuffled_accuracy` | `float` | Accuracy of shuffled-translation control |
| `accuracy_diff_vs_baseline` | `float` | `model_accuracy` - `baseline_accuracy` |
| `accuracy_diff_vs_shuffled` | `float` | `model_accuracy` - `shuffled_accuracy` |
| `mcnemar_pvalue_baseline` | `float` | p-value from McNemar's test (Model vs. Baseline) |
| `mcnemar_pvalue_shuffled` | `float` | p-value from McNemar's test (Model vs. Shuffled) |
| `timestamp` | `string` | ISO timestamp of generation |

## Data Flow

1.  **Generation**: `generate_data.py` → `ManipulationEpisode` (Raw Parquet).
2.  **Validation**: Schema check against `contracts/dataset.schema.yaml`; checksum recorded in `data/checksums.json`.
3.  **State Sync**: `data/checksums.json` synchronized with `state/projects/...yaml` (Principle V).
4.  **Preprocessing**: `data_utils.py` → `TrainingBatch` (Normalized tensors).
5.  **Training**: `train_model.py` → Model Weights (`.pt`).
6.  **Evaluation**: `evaluate.py` → `ModelPrediction` (Parquet) AND `MetricsReport` (JSON).
7.  **Analysis**: `evaluate.py` → McNemar's Test Statistics (in `MetricsReport`).

## Constraints & Validations

*   **Translation Only**: Validation script MUST fail if any column containing "rot", "quat", "torque", or "force" is detected in the raw dataset.
*   **Label Consistency**: `tipping_angle` and `slippage_distance` MUST be re-calculated from the raw physics log if the label is missing or inconsistent.
*   **Novelty**: Test set geometries MUST be disjoint from training set geometries (checked by hash of bounding box parameters).
*   **Traceability**: `MetricsReport` MUST contain the `data_checksum` matching the input data to satisfy Principle IV.