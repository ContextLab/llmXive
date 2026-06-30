# Data Model: Reproduce & Validate SpatialBench

## Overview
This document defines the data structures for the `SpatialBench` reproduction pipeline. It ensures that the output artifacts (JSON results, memory logs) are structured, validated, and consistent with the specification.

## Constants
- `MAX_RAM_MB = 6144`  # Upper RAM usage limit (≈6 GB) enforced by the runner.

## Input Data

### Scene Configuration
- **Type**: `dict`
- **Description**: Configuration for a single scene to be processed.
- **Fields**:
    - `scene_id` (str): Unique identifier (e.g., `"DTU_001"`).
    - `domain` (str): `"DTU"` or `"ScanNet"`.
    - `path` (str): Local path to scene data (depth, color, camera intrinsics).
    - `resolution` (tuple): `(height, width)` for input resizing (optional).

### Model Configuration
- **Type**: `dict`
- **Description**: Configuration for the model to be evaluated.
- **Fields**:
    - `model_name` (str): Identifier (e.g., `"depth_anything_v2"`).
    - `weights_path` (str): Path to model weights.
    - `device` (str): Always `"cpu"` for this feature.
    - `precision` (str): `"float32"`.

## Output Data

### Benchmark Results (JSON)
- **File**: `results_subset.json`
- **Schema**: `contracts/benchmark_results.schema.yaml`
- **Structure**:
    ```json
    {
      "run_metadata": {
        "timestamp": "ISO8601",
        "device": "cpu",
        "subset_size": 5,
        "models_tested": ["model_A", "model_B", "model_C"]
      },
      "results": [
        {
          "scene_id": "DTU_001",
          "domain": "DTU",
          "model_name": "depth_anything_v2",
          "metrics": {
            "abs_rel": 0.05,
            "delta1": 0.95,
            "delta2": 0.98,
            "delta3": 0.99
          },
          "status": "success"
        }
      ]
    }
    ```
- **Validation**:
    - `abs_rel` must be > 0.
    - `delta` values must be in `[0, 1]`.
    - `status` must be `"success"` or `"skipped"` or `"error"`.
    - `delta3` is **optional**; it may be omitted if not calculated.

### Memory Log (JSON)
- **File**: `memory_log.json`
- **Schema**: `contracts/memory_log.schema.yaml`
- **Structure**:
    ```json
    [
      {
        "timestamp": "ISO8601",
        "step": "loading_model",
        "ram_mb": 2048,
        "limit_mb": 6144
      },
      {
        "timestamp": "ISO8601",
        "step": "inference_scene_1",
        "ram_mb": 4096,
        "limit_mb": 6144
      }
    ]
    ```
- **Purpose**: To verify that the process never exceeded the `MAX_RAM_MB` safety limit (Edge Case: Memory Limit).

## Data Flow

1.  **Load**: `runner.py` loads `Scene Config` and `Model Config`.
2.  **Process**: For each scene:
    - Monitor RAM (using `MAX_RAM_MB`).
    - Load model (if not cached).
    - Run inference.
    - Calculate metrics (`metrics.py`).
    - Log RAM usage.
3.  **Aggregate**: Combine per‑scene results into `Benchmark Results`.
4.  **Visualize**: `visualizer.py` reads `Benchmark Results` and `Memory Log` to generate PNG/HTML.