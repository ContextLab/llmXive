# Data Model: llmXive follow-up: extending "AlayaWorld: Long-Horizon and Playable Video World Generation"

## Overview

This document defines the data structures used to track symbolic states, visual observations, and drift metrics throughout the hybrid inference pipeline. All data is stored in JSON or CSV format for portability and validation.

## Entities

### 1. Action Sequence
A discrete list of user inputs driving the simulation.

| Field | Type | Description |
| :--- | :--- | :--- |
| `sequence_id` | string | Unique identifier for the action sequence. |
| `actions` | list[string] | Ordered list of actions (e.g., `["summon", "hit", "die"]`). |
| `seed` | integer | Random seed used for generation. |
| `timestamp_start` | string (ISO) | Start time of the sequence. |

### 2. Symbolic State Log
Time-series record of logical object states derived from the rule-based engine.
**Note**: This log serves as the **Ground Truth** for CV validation.

| Field | Type | Description |
| :--- | :--- | :--- |
| `log_id` | string | Unique identifier for the log. |
| `sequence_id` | string | Reference to the action sequence. |
| `frame_index` | integer | Frame number (0-indexed). |
| `objects` | list[object] | List of object states at this frame. |
| `objects[].id` | string | Unique object ID. |
| `objects[].hp` | integer | Current HP (0 = dead). |
| `objects[].exists` | boolean | Whether the object exists in the logical world. |
| `objects[].position` | list[float] | Logical (x, y) position. |
| `state_hash` | string | SHA-256 hash of the state at this timestep (for immutability proof). |

### 3. Visual State Log
Time-series record of object states derived from computer vision analysis of the generated video.

| Field | Type | Description |
| :--- | :--- | :--- |
| `log_id` | string | Unique identifier for the log. |
| `sequence_id` | string | Reference to the action sequence. |
| `frame_index` | integer | Frame number (0-indexed). |
| `objects` | list[object] | List of detected object states. |
| `objects[].id` | string | Detected object ID (matched to symbolic). |
| `objects[].detected` | boolean | Whether the object was visually detected. |
| `objects[].confidence` | float | Detection confidence (0.0 - 1.0). |
| `objects[].position` | list[float] | Visual (x, y) position. |
| `objects[].is_phantom` | boolean | True if detected but not in symbolic log. |

### 4. Drift Result
Aggregated metrics for a single sequence.

| Field | Type | Description |
| :--- | :--- | :--- |
| `sequence_id` | string | Unique identifier. |
| `mode` | string | "baseline" or "hybrid". |
| `drift_score` | float | Normalized drift score (0.0 - 1.0). |
| `intrinsic_drift` | float | Drift caused by the model's generative errors (deconvoluted from noise). |
| `observational_noise` | float | Drift caused by CV measurement error. |
| `permanence_violations` | integer | Count of objects alive in video but dead in logic. |
| `phantom_objects` | integer | Count of objects in video but not in logic. |
| `cv_accuracy` | float | Validation accuracy (from FR-007, measured against Symbolic GT). |
| `is_valid` | boolean | True if `cv_accuracy` ≥ 0.85. |
| `resource_usage` | object | Memory and time metrics. |
| `resource_usage.peak_ram_gb` | float | Peak RAM in GB. |
| `resource_usage.wall_clock_min` | float | Wall-clock time in minutes. |

### 5. Ground Truth Annotation
Manually annotated frames for CV validation (by human observers).
**Note**: In this project, "Ground Truth" is derived from the **Symbolic Engine's state log**, not human observation.

| Field | Type | Description |
| :--- | :--- | :--- |
| `annotation_id` | string | Unique identifier. |
| `frame_path` | string | Path to the image file. |
| `objects` | list[object] | Ground truth object states (from **Symbolic Engine**). |
| `objects[].id` | string | Object ID. |
| `objects[].exists` | boolean | True if object is present. |
| `objects[].bbox` | list[int] | Bounding box [x, y, w, h] (derived from symbolic position if applicable). |

## Storage Location

- **Raw Data**: `data/raw/` (if provided)
- **Annotations**: `data/ground_truth/`
- **Logs**: `data/processed/` (Symbolic and Visual logs)
- **Results**: `data/results/` (Drift results, statistical reports, resource logs)