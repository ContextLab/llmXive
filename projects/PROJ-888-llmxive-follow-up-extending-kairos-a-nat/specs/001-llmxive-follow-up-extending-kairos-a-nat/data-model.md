# Data Model: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

## Overview

This document defines the data structures for the discrete state vectors, prediction horizons, and error metrics used in the study. All data artifacts are derived from the raw LIBERO dataset and transformed into JSON-serialized formats for processing.

## Entity Definitions

### 1. DiscreteStateVector
Represents the quantized state of the embodied agent at a single time step.

-   **Type**: JSON Object
-   **Fields**:
    -   `timestep`: Integer (0, 1, 2, ...)
    -   `bit_depth`: Integer (4, 8, 12, or 16)
    -   `state_vector`: List of Integers (values in range [0, 2^bit_depth - 1])
    -   `collision_flag`: Integer (0 or 1)
    -   `noise_std`: Float (0.0 to 0.5, representing injected noise level)
    -   `is_dropped`: Boolean (True if the timestep was dropped due to sparsity simulation)
    -   `source_episode_id`: String (ID of the source episode for pairing)

**Example**:
```json
{
  "timestep": 42,
  "bit_depth": 8,
  "state_vector": [12, 255, 0, 1, 180, 45],
  "collision_flag": 0,
  "noise_std": 0.1,
  "is_dropped": false,
  "source_episode_id": "libero_10_scene_3_ep_001"
}
```

### 2. PredictionHorizon
Defines the scope of the prediction task.

-   **Type**: Integer
-   **Allowed Values**: 100, 250, 500 (FR-004)
-   **Description**: The number of future time steps the model attempts to predict from the current state.

### 3. ErrorMetric
Composite record containing the performance of a model run.

-   **Type**: JSON Object
-   **Fields**:
    -   `run_id`: String (UUID for independent run)
    -   `bit_depth`: Integer
    -   `horizon`: Integer (100, 250, or 500)
    -   `mse`: Float (Mean Squared Error)
    -   `cumulative_error_rate`: Float (MSE growth per step)
    -   `noise_std`: Float
    -   `ram_peak_mb`: Float (Peak RAM usage in MB)
    -   `latency_per_step_ms`: Float (Inference latency)
    -   `entropy_score`: Float (Entropy of the quantized distribution)
    -   `is_untrained`: Boolean (True if model was trained from scratch due to missing weights)

## Data Flow

1.  **Raw Input**: HDF5/Parquet from LIBERO (verified URLs).
2.  **Processing**: `quantize.py` converts to `DiscreteStateVector` (JSON) with sparsity and noise.
3.  **Model Input**: Sequence of `DiscreteStateVector` fed to Kairos.
4.  **Model Output**: Predicted sequence of `DiscreteStateVector`.
5.  **Evaluation**: `metrics.py` calculates `ErrorMetric` for each horizon using **clean** ground truth.
6.  **Aggregation**: `stats.py` aggregates `ErrorMetric` across 10 runs for significance testing.

## Storage Layout

```text
data/
├── raw/
│   ├── libero_hdf5/          # Original HDF5 files (checksummed)
│   └── libero_parquet/       # Parquet files (checksummed)
├── processed/
│   ├── quantized_4bit/       # JSON files for 4-bit
│   ├── quantized_8bit/       # JSON files for 8-bit
│   ├── quantized_12bit/      # JSON files for 12-bit
│   └── quantized_16bit/      # JSON files for 16-bit
└── results/
    ├── mse_logs/             # ErrorMetric JSON files
    ├── checkpoints/          # Model weights (if needed)
    └── stats/                # Aggregated statistical results
```