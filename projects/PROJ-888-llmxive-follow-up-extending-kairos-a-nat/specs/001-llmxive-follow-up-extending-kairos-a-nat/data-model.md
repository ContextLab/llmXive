# Data Model: llmXive follow-up: extending "Kairos: A Native World Model Stack for Physical AI"

## Overview

This document defines the data structures used throughout the project, ensuring consistency between the quantization pipeline, the model training loop, and the analysis phase. All data is derived from the LIBERO benchmark and transformed into discrete representations.

## Entity Definitions

### 1. DiscreteStateVector
Represents the quantized state of the embodied agent at a single time step.

- **Type**: JSON Object / Dictionary
- **Fields**:
  - `timestep` (int): The global time step index.
  - `bit_depth` (int): The quantization level used (4, 8, or 16).
  - `proprioception` (list[int]): Discretized joint angles/positions.
  - `object_states` (list[dict]): List of object states.
    - `obj_id` (int): Unique object identifier.
    - `position` (list[int]): Discretized [x, y, z] coordinates.
    - `velocity` (list[int]): Discretized [vx, vy, vz]. **Derived via finite differencing of positions.**
    - `collision_flag` (int): Binary (0 or 1).
  - `noise_level` (float): The standard deviation of Gaussian noise applied (if any).

### 2. PredictionHorizon
Defines the scope of a prediction task.

- **Type**: Integer
- **Values**: 100, 250, 500 (as per spec).
- **Usage**: Used to slice sequences for training and evaluation.

### 3. ErrorMetric
Composite record for statistical analysis.

- **Type**: JSON Object / Dictionary
- **Fields**:
  - `run_id` (string): Unique identifier for the experiment run.
  - `bit_depth` (int): Quantization level.
  - `horizon` (int): Prediction horizon used.
  - `mse` (float): Raw Mean Squared Error.
  - `mse_normalized` (float): MSE divided by state space dimensionality.
  - `quantization_noise_floor` (float): Theoretical MSE of the quantization process.
  - `mse_adjusted` (float): `mse_normalized` - `quantization_noise_floor`. **Primary metric for stability threshold.**
  - `cumulative_error_rate` (float): Slope of error growth over time.
  - `p_value` (float): Result of statistical test vs. baseline.
  - `is_significant` (bool): True if p < 0.05.
  - `degradation_factor` (float): Ratio of discrete MSE to continuous baseline MSE.

## Data Flow

1.  **Raw Input**: `LIBERO_Parquet` (Continuous floats).
2.  **Transformation**: `Quantizer` (Continuous -> Discrete, with finite differencing for velocity).
3.  **Intermediate**: `DiscreteStateVector` (JSON).
4.  **Model Input**: Tensorized `DiscreteStateVector` (CPU).
5.  **Model Output**: `PredictedDiscreteStateVector`.
6.  **Analysis**: `ErrorMetric` (Aggregated statistics).

## Storage Layout

- **`data/raw/`**: Raw parquet files (downloaded via streaming, not stored permanently if possible, or stored with checksum).
- **`data/derived/quantized_4bit/`**: JSON files containing `DiscreteStateVector` for 4-bit.
- **`data/derived/quantized_8bit/`**: JSON files containing `DiscreteStateVector` for 8-bit.
- **`data/derived/quantized_16bit/`**: JSON files containing `DiscreteStateVector` for 16-bit.
- **`data/results/`**: `ErrorMetric` JSON files for each run.

## Constraints

- **Integrity**: No floating-point values in `DiscreteStateVector` fields (except `noise_level`).
- **Range**: All integer values must be within $[0, 2^{\text{bit\_depth}} - 1]$.
- **Validation**: All derived files must be validated against `contracts/dataset.schema.yaml` before training.
- **Derivation**: `velocity` fields MUST be derived via finite differencing, not natively extracted.