# Data Model: llmXive follow-up: extending "KVarN: Variance-Normalized KV-Cache Quantization Mitigates Error Accum"

## Overview

This document defines the data structures used throughout the project. All data is stored in `data/` directory, with raw generated data in `data/raw/`, processed training data in `data/processed/`, and simulation results in `data/results/`.

## Key Entities

### 1. AttentionMatrix

Represents a synthetic 128x128 attention matrix with metadata.

**Fields**:
- `id`: Unique identifier (UUID).
- `shape`: Tuple (128, 128).
- `mean`: Mean of the matrix values (float).
- `variance`: Variance of the matrix values (float).
- `sparsity_level`: Proportion of zero values (float, 0.0-1.0).
- `outlier_magnitude`: Factor by which outliers are scaled (float).
- `generated_at`: Timestamp.

**Justification for Input Features**: For the specific objective of **variance normalization** in KVarN, the optimal scaling factor is theoretically a function of the first two moments (mean and variance) alone. The Sinkhorn solver targets variance matching; thus, higher-order moments are redundant for this constraint. This justifies the use of `mean` and `variance` as the sole inputs to the static prior model.

**Example**:
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "shape": [128, 128],
  "mean": 0.023,
  "variance": 0.15,
  "sparsity_level": 0.5,
  "outlier_magnitude": 5.0,
  "generated_at": "2026-07-10T12:00:00Z"
}
```

### 2. ScalingFactor

Represents the ground-truth optimal scaling factor for an attention matrix.

**Fields**:
- `matrix_id`: Reference to `AttentionMatrix.id`.
- `optimal_scaling_factor`: The value derived from KVarN Sinkhorn optimization (float).
- `sinkhorn_iterations`: Number of iterations until convergence (int).
- `converged`: Boolean indicating successful convergence.

**Example**:
```json
{
  "matrix_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "optimal_scaling_factor": 0.85,
  "sinkhorn_iterations": 42,
  "converged": true
}
```

### 3. TrainingSample

A combined record for model training, linking matrix moments to the scaling factor.

**Fields**:
- `input_mean`: Mean of the attention matrix.
- `input_variance`: Variance of the attention matrix.
- `target_scaling_factor`: Ground-truth scaling factor.
- `split`: "train" or "test".

**Example**:
```csv
input_mean,input_variance,target_scaling_factor,split
0.023,0.15,0.85,train
0.045,0.22,0.78,test
```

### 4. SimulationRun

Records the results of a single autoregressive generation simulation.

**Fields**:
- `run_id`: Unique identifier (UUID).
- `method`: "static_prior" or "kvarn_baseline".
- `steps`: Number of autoregressive steps (e.g., 1000).
- `accumulated_kl_divergence`: Sum of KL-divergence over all steps (float).
- `per_token_latency_ms`: Average wall-clock time per token (float).
- `epsilon_floor`: Value used for variance normalization (float).
- `seed`: Random seed for reproducibility.
- `kl_divergence_sequence`: List of KL-divergence values at each step (optional, for analysis).
- `quantization_scheme`: String describing the quantization method (e.g., "Uniform_INT8_Symmetric").

**Example**:
```json
{
  "run_id": "run-001",
  "method": "static_prior",
  "steps": 1000,
  "accumulated_kl_divergence": 0.125,
  "per_token_latency_ms": 12.3,
  "epsilon_floor": 1e-6,
  "seed": 42,
  "kl_divergence_sequence": [0.0001, 0.0002, ...],
  "quantization_scheme": "Uniform_INT8_Symmetric"
}
```

## Quantization Noise Model

- **Scheme**: Uniform INT8 Quantization with symmetric range centered on the mean.
- **Noise Model**: The quantization error is modeled as uniform noise with variance proportional to the square of the step size.
- **KL-Divergence Calculation**: The KL-divergence is calculated analytically between the full-precision Gaussian distribution (approximated by the attention matrix moments) and the quantized distribution derived from the noise model. This ensures the metric is well-defined and causally linked to the scaling factor.

## Theoretical Lower Bound

- **Definition**: The analytical lower bound of KL-divergence based on the quantization noise model.
- **Purpose**: Serves as an independent ground truth to validate the static prior and KVarN baseline, avoiding circular validation.
- **Calculation**: Derived from the minimum possible error for the given quantization scheme (Uniform INT8).

## Data Flow

1. **Generation**: `synthetic_matrix_generator.py` creates `AttentionMatrix` and `ScalingFactor` records → Saved to `data/raw/synthetic_attention_matrices.jsonl`.
2. **Processing**: Script extracts moments and labels → Creates `data/processed/training_set.csv` and `test_set.csv`.
3. **Training**: MLP model is trained on `training_set.csv` → Model weights saved to `code/models/static_prior_mlp.pt`.
4. **Simulation**: `autoregressive_loop.py` runs 1,000 steps → Saves `SimulationRun` records to `data/results/simulation_run_XXX.json`.
5. **Analysis**: `statistical_tests.py` and `sensitivity_analysis.py` read `SimulationRun` records → Generate summary statistics and plots.
6. **Validation**: `theoretical_lower_bound.py` calculates the independent ground truth → Compares against simulation results.

## Data Hygiene

- **Checksums**: All files in `data/` are checksummed (SHA-256) and recorded in `state/`.
- **Immutability**: Raw data is never modified; transformations create new files.
- **Versioning**: Each artifact has a content hash; changes invalidate stale results.