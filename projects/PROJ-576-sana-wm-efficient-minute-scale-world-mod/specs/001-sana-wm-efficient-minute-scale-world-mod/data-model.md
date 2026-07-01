# Data Model: Reproduce & Validate SANA-WM

## Overview

This document defines the data structures used for input configuration, camera poses, and output metrics for the SANA-WM reproduction pipeline.

## Entities

### 1. CameraPose
Represents the 6-DoF camera trajectory for a single video clip.

**Schema**: `contracts/CameraPose.schema.yaml` (See Contracts)
**Description**: A sequence of extrinsic matrices (4x4) and intrinsic matrices (3x3) for each frame.
**Source**: `external/Sana/asset/sana_wm/*.npy`
**Validation Logic**: The raw `.npy` file is loaded into memory, converted to a JSON object containing `pose_type`, `shape`, `frames`, and `file_path`, and then validated against the `CameraPose` JSON schema. This ensures the input data meets the structural requirements before being passed to the generation pipeline.

### 2. InferenceConfig
Configuration parameters for the generation run.

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `prompt` | string | Text prompt for generation | "A cat walking on a leash" |
| `pose_file` | string | Path to `.npy` camera pose file | Required |
| `duration` | float | Duration in seconds | 4.0 |
| `resolution` | string | Target resolution (e.g., "480p", "720p") | "480p" |
| `steps` | int | Number of diffusion steps | 20 |
| `device` | string | Hardware target ("cpu", "cuda") | "cpu" |
| `seed` | int | Random seed for reproducibility | 42 |

### 3. MetricsReport
Output metrics generated upon completion.

**Schema**: `contracts/MetricsReport.schema.yaml` (See Contracts)
**Description**: Captures performance and resource usage.

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | Unique identifier for the run |
| `timestamp` | string | ISO 8601 timestamp |
| `status` | string | "success", "oom", "timeout", "error" |
| `total_time_seconds` | float | Wall-clock time |
| `peak_memory_gb` | float | Peak RAM usage in GB |
| `frames_generated` | int | Total frames output |
| `fps` | float | Effective frames per second |
| `error_message` | string | (Optional) Error details if status != success |
| `pose_drift_error` | float | (Optional) Calculated drift error for SC-002 |

## Data Flow

1.  **Input**: `InferenceConfig` + `CameraPose` (`.npy`)
2.  **Pre-Validation**: Load `.npy` -> Convert to JSON -> Validate against `contracts/CameraPose.schema.yaml`.
3.  **Process**: `sana_inference_pipeline.py` (CPU Mode)
4.  **Post-Validation**: Estimate pose from video -> Calculate Drift Error -> Compare against threshold.
5.  **Output**: `GeneratedVideo` (`.mp4`) + `MetricsReport` (`.json`)