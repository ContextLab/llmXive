# Data Model: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

## Overview

This document defines the data structures used in the quantization pipeline, model training, and analysis phases. All data flows from the continuous LIBERO dataset through the quantization engine to the discrete state vectors, and finally to the error metrics and stability reports.

## Core Entities

### 1. ContinuousStateVector
*Source*: Raw LIBERO dataset (parquet).
*Description*: The ground-truth continuous state of the embodied agent at a single time step.

| Field | Type | Description |
| :--- | :--- | :--- |
| `episode_id` | `str` | Unique identifier for the episode. |
| `timestep` | `int` | Time step index within the episode. |
| `position` | `List[float]` | 3D position of the end-effector (derived from `observations.state[0:3]`). |
| `orientation` | `List[float]` | Quaternion (derived from `observations.state[3:7]`). |
| `joint_angles` | `List[float]` | Robot joint angles. |
| `task_id` | `str` | Identifier for the specific task. |

### 2. DiscreteStateVector
*Source*: Output of `data/quantize.py`.
*Description*: The quantized, JSON-serialized state vector with derived velocities and noise injection.

| Field | Type | Description |
| :--- | :--- | :--- |
| `episode_id` | `str` | Inherited from source. |
| `timestep` | `int` | Inherited from source. |
| `bit_depth` | `int` | Quantization level (4, 8, or 16). |
| `state_values` | `List[int]` | Discrete integer values in range $[0, 2^{bit\_depth} - 1]$. |
| `velocity_values` | `List[int]` | Discrete velocity values derived from continuous data, then quantized. |
| `noise_seed` | `int` | Random seed used for noise injection (for reproducibility). |
| `quantization_error` | `float` | Theoretical noise floor for this bit depth (combined with injected noise). |

### 3. PredictionHorizon
*Description*: Configuration for long-horizon prediction.

| Field | Type | Description |
| :--- | :--- | :--- |
| `horizon_length` | `int` | Number of future steps to predict (100, 250, 500, 1000). |
| `input_context_length` | `int` | Number of past steps used as context. |

### 4. ErrorMetric
*Source*: Output of `analysis/metrics.py`.
*Description*: Composite record of error analysis for a specific run and bit depth.

| Field | Type | Description |
| :--- | :--- | :--- |
| `run_id` | `str` | Unique identifier for the independent run (includes noise seed). |
| `bit_depth` | `int` | Quantization level tested. |
| `horizon_length` | `int` | Prediction horizon used. |
| `total_mse` | `float` | Mean Squared Error between prediction and ground truth. |
| `quantization_noise_floor` | `float` | Theoretical noise floor calculated from combined noise distribution. |
| `model_error` | `float` | **Total MSE** (not subtracted). |
| `cumulative_growth_rate` | `float` | Slope of error accumulation over time. |
| `baseline_continuous_error` | `float` | Error of the continuous baseline model (re-trained per-run). |
| `degradation_ratio` | `float` | `model_error` / `baseline_continuous_error`. |
| `is_stable` | `bool` | `True` if `degradation_ratio` < 1.20. |
| `mse_normalized` | `float` | MSE divided by state space dimensionality. |
| `entropy_score` | `float` | Entropy of the quantized distribution (validation metric). |
| `ram_peak_mb` | `float` | Peak RAM usage in MB. |
| `latency_per_step_ms` | `float` | Inference latency per step in milliseconds. |
| `is_untrained` | `bool` | True if model was trained from scratch due to missing weights. |
| `noise_std` | `float` | Standard deviation of injected noise. |

### 5. StabilityReport
*Source*: Output of `analysis/stats.py`.
*Description*: Aggregated results across N=10 runs.

| Field | Type | Description |
| :--- | :--- | :--- |
| `bit_depth` | `int` | The quantization level analyzed. |
| `n_runs` | `int` | Number of independent runs (≥10). |
| `mean_model_error` | `float` | Average model error across runs. |
| `std_model_error` | `float` | Standard deviation of model error. |
| `p_value` | `float` | Result of mixed-effects model or block-bootstrap test vs. baseline. |
| `is_significant` | `bool` | `True` if `p_value` < 0.05. |
| `stability_threshold_met` | `bool` | `True` if mean degradation ratio < 1.20. |
| `stability_claim_framing` | `str` | Text description of the relative degradation. |

## Data Flow

1.  **Raw Data**: `data/raw/*.parquet` (ContinuousStateVector)
2.  **Quantization**: `data/processed/quantized/*.json` (DiscreteStateVector)
    - *Transformation*: `quantize.py` (Finite differencing, binning, noise injection).
3.  **Training/Inference**: `results/runs/<run_id>/` (Model checkpoints, predictions).
4.  **Analysis**: `results/aggregate/stability_report.json` (ErrorMetric, StabilityReport).

## Constraints & Validation

- **DiscreteStateVector**: `state_values` must be integers in $[0, 2^{bit\_depth} - 1]$.
- **ErrorMetric**: `model_error` must be non-negative. `degradation_ratio` must be > 0.
- **StabilityReport**: `n_runs` must be ≥ 10.
- **1-bit Collapse**: If `bit_depth` == 1 and `len(unique(state_values))` == 1, the run is flagged as "Invalid Data" and excluded from analysis.