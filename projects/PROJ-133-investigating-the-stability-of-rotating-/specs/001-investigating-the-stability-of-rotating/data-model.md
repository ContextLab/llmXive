# Data Model: Investigating the Stability of Rotating Bose-Einstein Condensates with Dipolar Interactions

## Overview

This document defines the data structures used for simulation inputs, raw outputs, processed metrics, and statistical aggregations. All data is stored in the `data/` directory with strict immutability rules for raw data.

## Entities

### 1. SimulationRun (Raw Output)
Represents the state of the wavefunction at a specific time step for a single simulation run.

- **Attributes**:
  - `run_id`: Unique identifier (e.g., `N1e4_O0.5_dd0.5_seed1`).
  - `timestamp`: ISO 8601 timestamp of generation.
  - `parameters`: JSON object containing `N`, `Omega`, `epsilon_dd`, `seed`, `grid_size`.
  - `time_step`: Current simulation time (float).
  - `density`: 2D numpy array (float32) of $|\psi|^2$.
  - `phase`: 2D numpy array (float32) of $\arg(\psi)$.
  - `vortex_count`: Integer count of detected vortices at this step.
  - `vortex_positions`: List of (x, y) tuples.
- **Storage Format**: `.npy` (NumPy binary) for arrays, `.json` for metadata.

### 2. StabilityMetric (Processed)
Aggregated metrics derived from a single simulation run.

- **Attributes**:
  - `run_id`: Foreign key to SimulationRun.
  - `initial_vortex_count`: Count at $t=0$.
  - `final_vortex_count`: Count at $t=end$.
  - `vortex_density`: Float (vortices per unit area).
  - `radial_variance`: Variance of vortex radial positions.
  - `structure_factor_sharpness`: Normalized peak height.
  - `instability_classified`: Boolean (True if density < 0.70 * theoretical_equilibrium_density).
  - `crash_time`: Float (if simulation crashed, else null).
- **Storage Format**: `.csv` (one row per run).

### 3. StatisticalAggregation (Final Results)
Aggregated results across the 5 repeats for a single parameter configuration.

- **Attributes**:
  - `config_id`: Unique identifier for the (N, Omega, epsilon_dd) set.
  - `mean_vortex_density`: Average density.
  - `std_vortex_density`: Standard deviation.
  - `p_value_anova_interaction`: P-value for Ω × ε_dd interaction.
  - `p_value_dunnett`: P-value vs baseline.
  - `threshold_sweep_results`: JSON object mapping threshold values (0.65, 0.70, 0.75) to false-positive/negative rates.
  - `non_parametric_flag`: Boolean (True if Kruskal-Wallis was used).
- **Storage Format**: `.json`.

## Data Flow

1.  **Input**: `ParameterGrid` (defined in `code/simulation/runner.py`) -> Generates `SimulationRun` files.
2.  **Processing**: `code/analysis/vortex_detector.py` & `metrics.py` -> Reads `SimulationRun` -> Writes `StabilityMetric` CSV.
3.  **Aggregation**: `code/statistics/aggregators.py` -> Reads `StabilityMetric` CSV -> Writes `StatisticalAggregation` JSON.
4.  **Visualization**: `code/viz/plotter.py` -> Reads `StatisticalAggregation` JSON -> Generates Figures.