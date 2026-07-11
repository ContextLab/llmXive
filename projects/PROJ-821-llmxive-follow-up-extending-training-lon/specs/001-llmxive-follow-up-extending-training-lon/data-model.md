# Data Model: llmXive follow-up: extending "Training Long-Context Vision-Language Models Effectively with Generali"

## Overview

This document defines the data structures used for the synthetic data generation, inference execution, and statistical analysis. All data is stored in JSONL (for line-by-line processing) or Parquet (for aggregation) formats to optimize I/O on the constrained CI runner.

## Entities

### 1. SyntheticSample
Represents a single input instance for the experiment.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `sample_id` | `string` | Unique identifier (UUID). | Immutable. |
| `arm_type` | `string` | Experimental arm: "A" (Constant Text) or "B" (Constant Total). | Enum: "A", "B". |
| `text_token_count` | `integer` | Number of text tokens. | Constant for Arm A; variable for Arm B. |
| `image_count` | `integer` | Number of images in the context. | Range: 0 to 20. |
| `visual_token_count` | `integer` | Total visual tokens (derived from images). | Linearly proportional to `image_count`. |
| `total_token_count` | `integer` | Total tokens (Text + Visual). | Constant for Arm B; variable for Arm A. |
| `needle_location` | `integer` | Token index of the needle. | Random, but consistent for difficulty. |
| `needle_value` | `string` | The unique token value. | Unique per sample. |
| `text_content` | `string` | The padded/reduced text content. | Must not contain the needle value outside `needle_location`. |
| `image_paths` | `list[string]` | Paths/URLs to images. | Length == `image_count`. |
| `difficulty_score` | `float` | Hardness of the needle retrieval. | Constant across all samples. |

### 2. InferenceResult
Represents the output of the model on a specific sample.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `sample_id` | `string` | FK to `SyntheticSample`. | Matches `sample_id`. |
| `retrieved_value` | `string` | The token extracted by the model. | May be `null` on failure. |
| `is_correct` | `boolean` | True if `retrieved_value` == `needle_value`. | Binary. |
| `inference_time_ms` | `float` | Time taken for inference. | Positive float. |
| `peak_memory_mb` | `float` | Peak RAM usage during inference. | Must be < 7000 MB. |
| `status` | `string` | `success`, `oom`, `timeout`, `error`. | Enum. |
| `error_message` | `string` | Error details if `status` != `success`. | Optional. |

### 3. DensityBucket
Aggregated statistics for a specific visual density level.

| Attribute | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `density_level` | `integer` | Number of images (0, 5, 10, 15, 20). | Unique per row. |
| `arm_type` | `string` | Experimental arm: "A" or "B". | Enum: "A", "B". |
| `total_samples` | `integer` | Count of samples in this bucket. | > 0. |
| `successful_samples` | `integer` | Count of samples with `status` == `success`. | ≤ `total_samples`. |
| `correct_count` | `integer` | Count of `is_correct` == True. | ≤ `successful_samples`. |
| `accuracy_rate` | `float` | `correct_count / successful_samples`. | Range: 0.0 to 1.0. |
| `avg_inference_time_ms` | `float` | Mean inference time. | Positive. |
| `avg_peak_memory_mb` | `float` | Mean peak memory. | Positive. |

## Data Flow

1. **Generation**: `generator.py` produces `data/synthetic/raw/samples.jsonl` (with `arm_type` field).
2. **Inference**: `runner.py` reads `samples.jsonl`, writes `data/results/raw/inference_logs.jsonl`.
3. **Aggregation**: `aggregator.py` reads `inference_logs.jsonl`, writes `data/results/aggregated/buckets.csv` (grouped by `arm_type` and `density_level`).
4. **Analysis**: `stats.py` reads `buckets.csv`, outputs statistical reports (separate for Arm A and Arm B).

## File Formats

- **JSONL**: Used for intermediate data to allow streaming processing and reduce memory footprint.
- **Parquet**: Used for final aggregated results if the dataset grows large (optional).
- **CSV**: Used for statistical input/output.