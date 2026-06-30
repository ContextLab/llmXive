# Data Model: Reproduce & Validate LocateAnything (Eagle)

## Overview

This document defines the data structures used for the inference results and evaluation metrics. These structures are validated against the schemas in `contracts/`.

## Entities

### InferenceResult

Represents the output of a single inference run on an image.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `image_id` | string | Unique identifier for the image (e.g., filename or hash). | Yes |
| `prompt` | string | The text prompt used for grounding (e.g., "Locate the dog"). | Yes |
| `predicted_boxes` | list[dict] | List of bounding boxes. Each box has `x_min`, `y_min`, `x_max`, `y_max` (normalized 0-1). | Yes |
| `inference_time_ms` | float | Time taken for the forward pass in milliseconds. | Yes |
| `peak_memory_mb` | float | Peak RAM usage in megabytes during inference. | Yes |
| `status` | string | "success" or "error". | Yes |
| `error_message` | string | Error details if status is "error". | No |
| `pbd_serial_overhead_ms` | float | Difference between Serial Fallback time and PBD time. Negative if PBD was faster. 0 if Serial Fallback not run. | Yes |

### EvaluationMetric

Represents the aggregate performance on a benchmark subset.

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `benchmark_name` | string | Name of the benchmark (e.g., "flickr30k_subset"). | Yes |
| `subset_size` | integer | Number of images evaluated. | Yes |
| `mean_iou` | float | Mean Intersection-over-Union score across the subset. Set to -1 if Ground Truth is missing. | Yes |
| `throughput_images_per_sec` | float | Average number of images processed per second. | Yes |
| `total_runtime_sec` | float | Total time taken for the evaluation run. | Yes |
| `peak_memory_mb` | float | Peak RAM usage during the evaluation run. | Yes |
| `pass_claim` | boolean | True if the mean_iou is within a reasonable range of the paper's claim (or if the pipeline is validated). | Yes |
| `memory_limit_pass` | boolean | True if peak_memory_mb was below 7000 MB (SC-003). | Yes |
| `ground_truth_available` | boolean | True if bounding box ground truth was available for IoU calculation. | Yes |
| `validation_mode` | string | "real", "synthetic", or "pipeline_only". Indicates the nature of the validation. | Yes |
| `ground_truth_source` | string | Description of the ground truth source (e.g., "synthetic_injection", "verified_dataset", "none"). | Yes |

## Data Flow

1.  **Input**: Sample image (from verified dataset or synthetic) + Text prompt.
2.  **Processing**: `Eagle` model (CPU) -> PBD -> Bounding Boxes.
3.  **Output**: `InferenceResult` (JSON).
4.  **Aggregation**: Multiple `InferenceResult` -> `EvaluationMetric` (JSON).
5.  **Reporting**: `EvaluationMetric` + `InferenceResult` logs -> `reproduction_report.md`.
