# Data Model: llmXive follow-up: extending "KVarN: Variance-Normalized KV-Cache Quantization Mitigates Error Accum"

## Overview

This document defines the data structures, schemas, and relationships used in the `llmXive` follow-up research project. The data model supports the generation of **synthetic attention trajectories**, the training of a static prior model, and the simulation of long-horizon autoregressive generation with dynamic error accumulation.

## Key Entities

### 1. AttentionTrajectory
Represents a single sequence of attention matrices and their derived statistics over time.
- **SequenceID**: Unique identifier (UUID).
- **Dimensions**: Fixed at 128x128.
- **Properties**:
  - `drift_parameters`: Object containing parameters used to generate the trajectory (e.g., noise variance, skewness target).
  - `regime_type`: Enum { "Standard", "HighOrderMoments", "Sparse" }.
- **Steps**: List of `AttentionStep` objects ([deferred] entries).

### 2. AttentionStep
Represents a single step $t$ in an `AttentionTrajectory`.
- **StepIndex**: Integer (0 to 999).
- **Properties**:
  - `mean`: Float, mean of the matrix elements.
  - `variance`: Float, variance of the matrix elements.
  - `skewness`: Float, skewness of the matrix elements.
  - `kurtosis`: Float, kurtosis of the matrix elements.
  - `sparsity`: Float, proportion of zero elements.
  - `epsilon_applied`: Float, the epsilon floor used for normalization.
- **Derived**:
  - `scaling_factor_gt`: Float, ground truth scaling factor from **Sequential Sinkhorn** (accounts for cumulative error).
  - `scaling_factor_pred`: Float (optional), predicted by MLP.
  - `sinkhorn_converged`: Boolean.
  - `cumulative_error_state`: Float, the accumulated quantization error from steps 0..t-1.

### 3. ScalingFactor
A scalar value representing the optimal variance-normalization factor.
- **Value**: Float.
- **Source**: Either "SequentialSinkhorn" (ground truth), "MLP" (prediction), or "ClosedForm" (baseline).
- **Context**: Linked to a specific `AttentionStep`.

### 4. SimulationRun
An instance of the autoregressive generation simulation.
- **RunID**: Unique identifier.
- **Method**: Enum { "KVarN", "StaticPrior", "ClosedForm" }.
- **Steps**: Integer, number of steps (e.g., [deferred]).
- **Metrics**:
  - `accumulated_kl_divergence`: Float, sum of KL-divergence over all steps.
  - `per_token_latency`: Float, average wall-clock time per token.
  - `final_error`: Float, error at the last step.
  - `theoretical_lower_bound`: Float, analytical noise floor (FR-008).
- **Parameters**:
  - `epsilon_floor`: Float used in the run.
  - `seed`: Integer random seed.
  - `regime_type`: Enum { "Standard", "HighOrderMoments", "RealWorldProxy" }.

### 5. ModelError
Record of prediction error for a specific attention step.
- **StepID**: Reference to `AttentionStep`.
- **Predicted**: Float.
- **GroundTruth**: Float.
- **MSE**: Float, squared difference.
- **BaselineMSE**: Float, squared difference against closed-form baseline.

## Data Flow

1. **Generation**: `synthetic_attention.py` creates `AttentionTrajectory` instances and computes `ScalingFactor` (Ground Truth) using the Sequential Sinkhorn solver. Output: `data/raw/synthetic_attention_trajectories.parquet`.
2. **Training**: `train.py` reads the trajectories, trains the MLP, and outputs `ModelError` records. Output: `data/processed/model_predictions.json`.
3. **Simulation**: `autoregressive_loop.py` uses the trained model to simulate generation, maintaining cumulative error state. Output: `data/processed/simulation_results.csv` (containing `SimulationRun` metrics).
4. **Analysis**: `stats.py` aggregates `SimulationRun` metrics, performs t-tests, and generates `ModelError` aggregates. Output: `data/final/statistical_summary.json`.

## File Formats

- **Input/Output**: Parquet (for large trajectory datasets to save space), CSV (for tabular metrics), JSON (for nested structures like model weights or complex simulation logs).
- **Checkpoints**: Model weights saved as `.pt` (PyTorch) or `.npz` (NumPy).

## Constraints

- **Numerical Stability**: All variance calculations must include a small positive epsilon floor to ensure numerical stability.
- **Uniqueness**: Every `RunID`, `SequenceID`, and `StepIndex` must be unique within their respective datasets.
- **Immutability**: Raw data files (`data/raw/`) must never be modified. Derivations go to `data/processed/`.
- **Dynamic Consistency**: The `cumulative_error_state` in `AttentionStep` must be consistent with the error accumulation model used in the simulation.