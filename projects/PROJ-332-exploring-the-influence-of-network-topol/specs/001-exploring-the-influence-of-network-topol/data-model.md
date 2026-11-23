# Data Model: Influence of Network Topology on Thermal Conductivity in Nanomaterials

## Overview

This document defines the data structures used for simulation input, intermediate processing, and final output. All data is stored in CSV or JSON format to ensure reproducibility and ease of inspection.

## Input Parameters

| Parameter | Type | Description | Default | Source |
| :--- | :--- | :--- | :--- | :--- |
| `N` | int | Number of nodes | 1000 | FR-001 |
| `target_degree` | float | Target average degree | 4.0 | CLI |
| `material` | str | Material name (Si, CNT, Ag, Au) | "Si" | CLI |
| `diameter_nm` | float | Wire diameter in nm | 50.0 | CLI |
| `length_um` | float | Wire length in µm | 1.0 | CLI |
| `seed` | int | Random seed | Auto | CLI |
| `scaling_factor` | float | Resistance multiplier | 1.0 | Sensitivity |

## Intermediate Data: Graph Metrics

Stored per simulation run.

| Field | Type | Description |
| :--- | :--- | :--- |
| `run_id` | str | Unique identifier (seed + timestamp) |
| `avg_degree` | float | Measured average degree |
| `path_length` | float | Average shortest path (NaN if disconnected) |
| `clustering` | float | Clustering coefficient |
| `giant_component_ratio` | float | Fraction of nodes in largest component |
| `is_connected` | bool | True if graph is fully connected |
| `k_eff_iso` | float | Isotropic effective conductivity (avg of 4 directions) |

## Output Data: Simulation Results

Stored in `data/processed/simulation_results.csv` (FR-009).

| Column | Type | Description |
| :--- | :--- | :--- |
| `seed` | int | Random seed |
| `N` | int | Node count |
| `p` | float | Connection probability |
| `avg_degree` | float | Measured average degree |
| `percolation_threshold` | float | **Batch-level** estimated threshold ($k_c$) for the current connectivity level group |
| `connectivity_probability` | float | Fraction of connected graphs in the batch ($P_{\infty}$) |
| `convergence_rate` | float | Solver convergence status (1.0=success) |
| `total_runtime` | float | Execution time in seconds |
| `k_eff` | float | Effective thermal conductivity (W/mK) (Isotropic average) |
| `scaling_exponent_t` | float | Fitted exponent (only for batch analysis) |
| `p_value` | float | P-value for regression (only for batch analysis) |
| `k_eff_adj` | float | Adjusted conductivity ($k_{eff} \times P_{\infty}$) |

## Derived Aggregates

Stored in `data/processed/regression_summary.json`.

-   `exponent_t`: Best fit value.
-   `ci_lower`: 95% CI lower bound.
-   `ci_upper`: 95% CI upper bound.
-   `r_squared`: Goodness of fit.
-   `percolation_threshold_estimated`: Value used.
-   `sensitivity_range`: {min_k, max_k} for scaling factors {0.9, 1.1}.
-   `theoretical_deviation`: $|t_{fitted} - 1.3|$.