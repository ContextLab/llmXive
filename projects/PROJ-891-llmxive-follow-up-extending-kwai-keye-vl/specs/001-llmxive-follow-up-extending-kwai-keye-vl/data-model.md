# Data Model: llmXive follow-up: extending "Kwai Keye-VL-2.0 Technical Report"

## Overview

This document defines the data structures used throughout the pipeline: input metadata, generated synthetic clips, model predictions, and evaluation metrics. All data is stored in `data/` with strict versioning and checksumming as per the project constitution.

## Entities

### 1. SourceVideoMetadata
Represents the original video entry from ActivityNet Captions.

| Field | Type | Description |
| :--- | :--- | :--- |
| `video_id` | `string` | Unique identifier from ActivityNet (e.g., `v_abc123`). |
| `duration` | `float` | Total duration in seconds. |
| `annotations` | `list[object]` | List of temporal annotations for the video. |
| `annotations[].start` | `float` | Start timestamp of the event. |
| `annotations[].end` | `float` | End timestamp of the event. |
| `annotations[].label` | `string` | Text description of the event. |
| `source_url` | `string` | URL to the original video file (for fetching). |

### 2. SyntheticVideoClip
Represents a generated video clip with specific geometric distortion.

| Field | Type | Description |
| :--- | :--- | :--- |
| `clip_id` | `string` | Unique identifier (e.g., `{video_id}_{ratio}`). |
| `source_video_id` | `string` | Link to the original `video_id`. |
| `aspect_ratio` | `string` | Target ratio (e.g., "1:10", "10:1", "1:20", "20:1"). |
| `width` | `int` | Width in pixels. |
| `height` | `int` | Height in pixels. |
| `file_path` | `string` | Relative path to the generated MP4 file. |
| `duration` | `float` | Duration (same as source). |
| `exclusion_reason` | `string` | Optional. Reason for exclusion (e.g., "semantic_loss"). |

### 3. Prediction
Represents the model's output for a specific clip.

| Field | Type | Description |
| :--- | :--- | :--- |
| `clip_id` | `string` | Link to the `SyntheticVideoClip`. |
| `predicted_start` | `float` | Predicted start timestamp. |
| `predicted_end` | `float` | Predicted end timestamp. |
| `model_version` | `string` | Version of the model used (e.g., "Kwai-Keye-VL-2.0-INT4" or "LLaVA-NeXT-34B-INT4"). |
| `inference_time` | `float` | Time taken in seconds. |
| `memory_peak_mb` | `float` | Peak VmRSS in MB. |
| `status` | `string` | "success", "oom", "error". |

### 4. EvaluationMetric
Represents the calculated performance for a single clip.

| Field | Type | Description |
| :--- | :--- | :--- |
| `clip_id` | `string` | Link to the `SyntheticVideoClip`. |
| `condition` | `string` | "extreme" or "control". |
| `ground_truth_start` | `float` | Original start timestamp. |
| `ground_truth_end` | `float` | Original end timestamp. |
| `predicted_start` | `float` | Predicted start timestamp. |
| `predicted_end` | `float` | Predicted end timestamp. |
| `IoU` | `float` | Intersection-over-Union score (0.0 to 1.0). |
| `is_valid` | `boolean` | Whether the prediction was valid (non-null). |

## Data Flow

1.  **Input**: `SourceVideoMetadata` (loaded from official ActivityNet Captions JSON).
2.  **Generation**: `SourceVideoMetadata` + `aspect_ratio` -> `SyntheticVideoClip` (MP4 file).
    *   **Control**: `SourceVideoMetadata` -> `EvaluationMetric` (using original video file).
3.  **Inference**: `SyntheticVideoClip` (and original video for control) -> `Prediction` (JSON).
4.  **Evaluation**: `Prediction` + `SourceVideoMetadata` -> `EvaluationMetric`.
5.  **Aggregation**: `EvaluationMetric` -> Statistical Report (mIoU, p-value).

## Storage Layout

```text
data/
├── raw/
│   ├── activitynet_metadata.json  # Source annotations (val_1.json, val_2.json)
│   └── activitynet_videos/        # Streamed video files (temporary)
├── distorted/
│   ├── 1_10/                      # 1:10 clips
│   ├── 10_1/                      # 10:1 clips
│   ├── 1_20/                      # 1:20 clips
│   └── 20_1/                      # 20:1 clips
├── outputs/
│   ├── predictions.json           # All predictions
│   └── metrics.csv                # All mIoU scores
└── logs/
    └── generation.log             # Exclusion reasons
```
