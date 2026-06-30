# Data Model: Reproduce & Validate VideoKR

## Overview

This document defines the data schemas for the subsampled VideoKR dataset and the validation log artifacts. These schemas are critical for the contract tests that verify the pipeline's output.

## Subsampled Dataset Schema

The data preparation script (`prepare_videokr_sft_data.py`) generates a JSONL file containing a subsampled version of the VideoKR training data.

### Schema: `videokr_subsample.jsonl`

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `video_path` | `string` | Yes | Path to the video file (local or URL). |
| `question` | `string` | Yes | The question associated with the video. |
| `answer` | `string` | Yes | The ground truth answer. |
| `rationale` | `string` | No | The reasoning trace (if available in the original data). |
| `source` | `string` | Yes | Identifier for the source dataset (e.g., "VideoKR"). |
| `sample_id` | `integer` | Yes | Unique identifier for the subsampled example (0 to 99). |
| `video_tensor_shape` | `string` | No | Shape of the synthetic video tensor (e.g., "(16, 224, 224, 3)") if synthetic data is used. |

**Constraints**:
- `video_path`: Must be a valid string.
- `question`, `answer`: Non-empty strings.
- `sample_id`: Must be unique and within the range [0, 99].
- `video_tensor_shape`: If present, must be a valid string representation of a 3D shape.

## Validation Log Schema

The training/evaluation script (`train_dryrun.py`) generates a log file (`train.log`) that serves as proof of execution.

### Schema: `validation_log.json`

| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `status` | `string` | Yes | Execution status: "SUCCESS", "FAILURE", or "DATA_ONLY" (if model loading was skipped). |
| `timestamp` | `string` | Yes | ISO 8601 timestamp of the run. |
| `steps_executed` | `integer` | Yes | Number of training steps completed (expected: 1 or 0 if DATA_ONLY). |
| `model_loaded` | `boolean` | Yes | Whether the model loaded successfully. |
| `data_loaded` | `boolean` | Yes | Whether the data loader yielded at least one batch. |
| `error_message` | `string` | No | Error details if `status` is "FAILURE". |
| `logs` | `array[string]` | Yes | List of log lines from the execution. |

**Constraints**:
- `status`: Must be exactly "SUCCESS", "FAILURE", or "DATA_ONLY".
- `steps_executed`: Must be ≥ 1 for a successful run, 0 for DATA_ONLY.
- `logs`: Must contain at least one entry indicating "Training started" or "Data validation started" and one indicating "Step X completed" or "Validation completed".