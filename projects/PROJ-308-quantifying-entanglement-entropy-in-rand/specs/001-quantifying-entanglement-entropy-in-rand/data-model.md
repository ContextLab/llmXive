# Data Model: Quantifying Entanglement Entropy

## Overview

This document defines the data structures, file formats, and schemas used in the project. All data is stored in CSV or text formats for portability and ease of parsing.

## Entity Definitions

### 1. ParameterSet
Represents the configuration for a single simulation run.
- `chain_length` (int): $L$, number of spins.
- `disorder_strength` (float): $\delta$, coupling variance.
- `num_realizations` (int): $N_{\text{real}}$, number of disorder samples.
- `seed` (int): Random seed for reproducibility.
- `timestamp` (str): ISO 8601 execution time.

### 2. DisorderRealization
Represents a single instance of the random Hamiltonian.
- `realization_id` (int): Unique ID within a run.
- `couplings` (list[float]): The sequence of $J_i$.
- `ground_state_energy` (float): Converged energy value.
- `convergence_iterations` (int): Steps taken in TEBD.
- `chi_max_used` (int): Maximum bond dimension used in TEBD.
- `convergence_status` (str): "converged" or "numerically_unresolved".

### 3. EntropyRecord
The core measurement data.
- `realization_id` (int): Links to the disorder realization.
- `subsystem_size` (int): $l$, the bipartition point.
- `entropy` (float): $S(l)$, von Neumann entropy.
- `edge_left` (float): Entropy at $l=1$ (cached for speed).
- `edge_right` (float): Entropy at $l=L-1$ (cached for speed).

### 4. FitResult
Aggregated statistical results.
- `disorder_strength` (float): $\delta$.
- `scaling_exponent` (float): $\alpha$ (log-log fit).
- `thermal_slope` (float): $\beta$ (linear fit, if applicable).
- `ci_lower` (float): Lower bound of 95% CI for $\alpha$.
- `ci_upper` (float): Upper bound of 95% CI for $\alpha$.
- `p_value` (float): Two-sided p-value.
- `r_squared_log` (float): $R^2$ for log-log fit.
- `r_squared_linear` (float): $R^2$ for linear fit.
- `r_squared_constant` (float): $R^2$ for constant fit (area law).
- `aic_log` (float): AIC for log model.
- `aic_linear` (float): AIC for linear model.
- `aic_constant` (float): AIC for constant model.
- `phase_classification` (str): "critical", "mbl", "thermal", or "unknown".

### 5. Metadata (Single Source of Truth for Statistics)
- `file`: `data/raw/metadata.json`
- **Purpose**: This file is the **Single Source of Truth (SSoT)** for statistical robustness verification per Constitution Principle VII.
- `fields`:
  - `run_id` (str): Unique run identifier.
  - `parameters`: JSON object of `ParameterSet`.
  - `realizations_summary`: List of `DisorderRealization` summaries (ID, status, chi_max).
  - `pilot_variance`: Float (CV of alpha from pilot study).
  - `final_N_real`: Int (actual number of realizations used, recorded here as SSoT).
  - `bootstrap_resamples`: Int.

## File Formats

### `entropy_data.csv`
Raw entropy measurements per realization.
- **Columns**: `realization_id`, `subsystem_size`, `entropy`, `edge_left`, `edge_right`
- **Format**: CSV, UTF-8, comma-delimited.
- **Constraints**: `entropy` $\ge 0$; `subsystem_size` $\in [1, L-1]$.

### `scaling_fit.txt`
Human-readable summary of the regression analysis.
- **Format**: Text key-value pairs.
- **Example**:
  ```text
  disorder_strength: 0.2
  scaling_exponent: 0.31
  ci_lower: 0.29
  ci_upper: 0.33
  p_value: 0.001
  r_squared_log: 0.98
  aic_log: 120.5
  aic_constant: 150.2
  phase_classification: critical
  ```

### `bootstrap_summary.txt`
Details of the bootstrap resampling.
- **Columns/Keys**: `num_resamples`, `standard_error`, `p_value`, `mean_exponent`.

### `delta_vs_exponent.csv`
Summary of the grid scan (if applicable).
- **Columns**: `delta`, `alpha`, `ci_lower`, `ci_upper`, `ci_width`, `p_value`

### `boundary_entropy.csv`
Edge entropy profiles.
- **Columns**: `realization_id`, `delta`, `edge_left`, `edge_right`

### `metadata.json`
- **Format**: JSON.
- **Purpose**: Records the number of realizations, pilot variance, and convergence status for every run, satisfying Constitution Principle VII (Statistical Sampling Robustness). This file is the SSoT for $N_{\text{real}}$.

## Data Flow

1. **Input**: `config.yaml` (parameters) -> `cli.py`
2. **Pilot Study**: Run $N=20$ realizations -> Calculate variance -> Adjust $N_{\text{real}}$.
3. **Generation**: `hamiltonian.py` creates $J_i$.
4. **Simulation**: `ground_state.py` computes $|\psi_0\rangle$ (adaptive chi).
5. **Measurement**: `entropy.py` computes $S(l)$ -> Appends to `entropy_data.csv`.
6. **Analysis**: `analysis.py` reads `entropy_data.csv` -> Fits Log, Linear, Constant models -> Selects best via AIC -> Writes `scaling_fit.txt`, `bootstrap_summary.txt`, `delta_vs_exponent.csv`.
7. **Metadata**: `cli.py` writes `data/raw/metadata.json` with run details (including final $N_{\text{real}}$).
8. **Output**: All files stored in `data/raw/` and `data/processed/`.
