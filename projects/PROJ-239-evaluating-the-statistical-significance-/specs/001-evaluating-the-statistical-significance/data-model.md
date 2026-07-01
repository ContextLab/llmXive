# Data Model: Evaluating the Statistical Significance of A/B Test Results with Non-Independent Observations

## Overview

This document defines the data structures used for generating synthetic clustered data, running simulations, and aggregating results. All data is stored in CSV or Parquet formats for reproducibility and efficiency.

## Key Entities

### 1. Simulation Configuration
Defines the parameters for a single simulation run.
*   `icc_level` (float): The target intra-cluster correlation coefficient (e.g., 0.1).
*   `alpha` (float): The nominal significance threshold (e.g., 0.05).
*   `n_clusters` (int): Number of clusters. **Constraint: Must be >= 50** to ensure validity of cluster-robust variance estimators.
*   `cluster_size_mean` (float): Average number of observations per cluster.
*   `cluster_size_sd` (float): Standard deviation of cluster sizes (for unbalanced designs).
*   `seed` (int): Random seed for reproducibility.

### 2. Synthetic Observation
Represents a single data point in the generated dataset.
*   `cluster_id` (int): Unique identifier for the cluster.
*   `observation_id` (int): Unique identifier for the observation within the cluster.
*   `treatment` (int): 0 (Control) or 1 (Treatment). **Assigned at the cluster level** (constant for all observations in a cluster).
*   `outcome` (float): The simulated continuous outcome variable.
*   `true_effect` (float): Always 0.0 for this study (H0 is true).

### 3. Simulation Run Result
Aggregated results from a single iteration of the simulation.
*   `run_id` (int): Unique iteration ID.
*   `icc_level` (float): ICC used.
*   `alpha` (float): Alpha used.
*   `method` (string): "standard_t", "cluster_robust", "block_permutation".
*   `p_value` (float): Calculated p-value.
*   `reject_h0` (bool): True if $p < \alpha$.

### 4. Aggregated Metrics
Final summary statistics for a specific configuration.
*   `icc_level` (float)
*   `alpha` (float)
*   `method` (string)
*   `empirical_type1_error` (float): Proportion of `reject_h0` across all runs.
*   `ci_lower` (float): Lower bound of 95% CI for the error rate.
*   `ci_upper` (float): Upper bound of 95% CI for the error rate.
* `n_iterations` (int): Total iterations (should be [deferred]).

## File Structure

```text
data/
├── derived/
│   ├── simulation_results_raw.csv      # All individual run results (run_id, p_value, etc.)
│   ├── aggregated_metrics.csv          # Final summary (empirical error rates, CIs)
│   └── config_snapshot.json            # Full configuration used for the run
```

## Data Flow

1.  **Config Generation**: `config.py` generates parameter sets (ICC, Alpha, **n_clusters >= 50**).
2.  **Data Generation**: `data_generator.py` creates `synthetic_observation` rows with cluster-level treatment assignment.
3. **Simulation Loop**: `simulation_runner.py` iterates [deferred] times, calling `estimators.py`.
4.  **Result Aggregation**: `analysis.py` computes `aggregated_metrics` and writes to CSV.