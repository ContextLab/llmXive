# Data Model: llmXive follow-up: extending "KVarN: Variance-Normalized KV-Cache Quantization Mitigates Error Accum"

## Overview

This document defines the core data entities used in the synthetic data generation, model training, and simulation phases. All entities are serializable to JSON/CSV for reproducibility and checksumming.

## Entities

### 1. AttentionMatrix

Represents a single synthetic attention matrix and its derived statistics.

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | string | Unique identifier (UUID). |
| `dimensions` | object | `{"rows":, "cols": 128}`. |
| sparsity_level | float | Ratio of zero elements (ranging from minimal to maximal sparsity). |
| `outlier_magnitude` | float | Scaling factor for outlier values. |
| `mean` | float | Arithmetic mean of non-zero elements. |
| `variance` | float | Variance of non-zero elements. |
| `raw_data` | string | Base64 encoded flattened array (optional, for debugging). |

### 2. ScalingFactor

Represents the ground-truth optimal scaling factor derived from the Sinkhorn solver.

| Field | Type | Description |
| :--- | :--- | :--- |
| `matrix_id` | string | Reference to the source `AttentionMatrix`. |
| `optimal_value` | float | The scaling factor $s^*$ computed by Sinkhorn. |
| `convergence_status` | string | `converged` or `failed`. |
| `iterations` | int | Number of iterations taken to converge. |
| `computation_time_ms` | float | Wall-clock time for the solver. |

### 3. SimulationRun

Represents a single instance of the long-horizon autoregressive simulation.

| Field | Type | Description |
| :--- | :--- | :--- |
| `run_id` | string | Unique identifier. |
| `seed` | int | Random seed used for reproducibility. |
| `method` | string | `static_prior` or `kvarn_baseline`. |
| `steps` | int | Total steps (a predetermined number). |
| `accumulated_kl_divergence` | float | Sum of KL-divergence over all steps. |
| `avg_latency_per_token_ms` | float | Average wall-clock time per token. |
| `kl_history` | array | List of KL values per step (for plotting). |
| `fallback_count` | int | Number of times the system fell back to KVarN. |

### 4. ModelError

Records the prediction error for a specific matrix during evaluation.

| Field | Type | Description |
| :--- | :--- | :--- |
| `matrix_id` | string | Reference to `AttentionMatrix`. |
| `predicted_value` | float | MLP prediction. |
| `ground_truth_value` | float | Sinkhorn result. |
| `mse` | float | Squared error for this instance. |
| `baseline_error` | float | Error of the $1/\sigma^2$ baseline. |

## Data Flow

1. **Generation**: `synthetic_matrix_generator.py` creates `AttentionMatrix` instances.
2. **Labeling**: `sinkhorn_solver.py` computes `ScalingFactor` for each matrix.
3. **Training**: `train_and_eval.py` reads matrices and labels, outputs `ModelError` records.
4. **Simulation**: `autoregressive_loop.py` generates `SimulationRun` records.
5. **Analysis**: `statistical_tests.py` aggregates `SimulationRun` data for t-tests.