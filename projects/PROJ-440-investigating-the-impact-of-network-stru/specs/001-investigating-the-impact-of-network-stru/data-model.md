# Data Model: Investigating the Impact of Network Structure on Energy Dissipation in Driven Oscillators

## Overview

This document defines the data structures, schemas, and relationships for the project. All data is generated synthetically and stored in `data/` with checksums for reproducibility.

## Entities

### 1. NetworkTopology
Represents a generated graph structure and its static metrics.

| Field | Type | Description |
|-------|------|-------------|
| `graph_id` | str | Unique identifier (e.g., "random_001") |
| `topology_class` | str | "random", "scale_free", "small_world", "lattice", "star" |
| `node_count` | int | Number of nodes (100-200) |
| `avg_degree` | float | Average degree of the graph |
| `clustering_coeff` | float | Global clustering coefficient (0-1) |
| `avg_path_length` | float | Average shortest path length |
| `degree_distribution` | dict | Histogram of degrees (for KS-test validation) |
| `seed` | int | Random seed used for generation |

### 2. EnergyTimeSeries
Represents the time-ordered sequence of total system energy.

| Field | Type | Description |
|-------|------|-------------|
| `simulation_id` | str | Unique identifier (links to graph_id) |
| `time` | list[float] | Time points (0 to 200) |
| `energy` | list[float] | Total system energy at each time point |
| `driving_active` | bool | True for t ≤ 100, False for t > 100 |
| `convergence_status` | str | "converged", "failed", "resonant" |

### 3. DecayRate
Extracted decay rate from the energy time-series.

| Field | Type | Description |
|-------|------|-------------|
| `simulation_id` | str | Unique identifier |
| `decay_rate` | float | Fitted λ from $E(t) = A e^{-\lambda t} \cos(\omega t + \phi) + C$ |
| `r_squared` | float | Goodness-of-fit (R²) for the exponential fit |
| `frequency` | float | Fitted oscillation frequency ω |
| `phase` | float | Fitted phase φ |
| `amplitude` | float | Fitted amplitude A |
| `offset` | float | Fitted offset C |

### 4. RegressionResult
Statistical output from PLS analysis.

| Field | Type | Description |
|-------|------|-------------|
| `vip_scores` | dict | Variable Importance in Projection (VIP) scores for each metric |
| `pls_coefficients` | dict | PLS regression coefficients for each metric |
| `p_values` | dict | Raw p-values for each metric |
| `p_values_corrected` | dict | Bonferroni-corrected p-values for each metric |
| `significant_predictors` | list[str] | List of metrics with corrected p < 0.05 |
| `vif_scores` | dict | VIF for each original metric (diagnostic) |
| `null_model_p_value` | float | p-value from permutation test (observed vs null distribution) |
| `observed_r_squared` | float | R² of the observed model |
| `null_r_squared_mean` | float | Mean R² of the null distribution |
| `null_r_squared_95th` | float | 95th percentile of the null distribution R² |

## Data Flow

1. **Generation**: `generate_networks.py` → `data/raw/networks.csv` (NetworkTopology)
2. **Simulation**: `simulate_oscillators.py` → `data/processed/energy_decay.csv` (EnergyTimeSeries, DecayRate)
3. **Analysis**: `analyze_regression.py` → `data/analysis/regression_results.json` (RegressionResult)

## Checksums

- `data/raw/networks.csv`: SHA-256 checksum recorded in `state/projects/PROJ-440-investigating-the-impact-of-network-stru.yaml`
- `data/processed/energy_decay.csv`: SHA-256 checksum recorded
- `data/analysis/regression_results.json`: SHA-256 checksum recorded