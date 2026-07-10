# Data Model: Exploring the Impact of Data Imputation Methods on Causal Inference

## 1. Overview

This document defines the data structures used for synthetic data generation, imputation results, and causal estimates. All data is stored in `data/synthetic/` with checksums.

## 2. Entity Definitions

### 2.1 SyntheticDataset
Represents a single generated instance of the SCM.

| Attribute | Type | Description |
|-----------|------|-------------|
| `run_id` | str | Unique identifier for the simulation run (e.g., `seed_123_beta_0.5`). |
| `seed` | int | Random seed used for generation. |
| `beta` | float | MNAR strength parameter ($\beta$). |
| `sample_size` | int | Number of samples ($N$). |
| `ground_truth_ate` | float | Known ATE ($\tau_{true}$) from the SCM. |
| `missingness_rate` | float | Proportion of missing values in $Y$. |
| `data_path` | str | Path to the generated dataset (Parquet/CSV). |
| `checksum` | str | SHA-256 hash of the data file. |

### 2.2 ImputationResult
Represents the output of an imputation method applied to a dataset.

| Attribute | Type | Description |
|-----------|------|-------------|
| `run_id` | str | Reference to the parent `SyntheticDataset`. |
| `method_name` | str | Name of the imputation method (e.g., "Mean", "KNN", "MICE"). |
| `imputed_data_path` | str | Path to the imputed dataset. |
| `convergence_status` | str | "success", "failed", or "timeout". |
| `iterations` | int | Number of iterations (for MICE). |
| `divergence_flag` | bool | **True** if the difference between IPW and PSM estimates > 0.1 OR if their 95% CIs do not overlap. |

### 2.3 CausalEstimate
Represents the final ATE calculation for a specific imputation method and estimator.

| Attribute | Type | Description |
|-----------|------|-------------|
| `run_id` | str | Reference to the parent `SyntheticDataset`. |
| `imputation_method` | str | Name of the imputation method. |
| `estimator_type` | str | "IPW" or "PSM". |
| `estimated_ate` | float | Calculated ATE ($\hat{\tau}$). |
| `standard_error` | float | Standard error of the estimate (derived via Rubin's Rules or Bootstrapping). |
| `ci_lower` | float | Lower bound of 95% CI. |
| `ci_upper` | float | Upper bound of 95% CI. |
| `bias` | float | Absolute bias $|\hat{\tau} - \tau_{true}|$. |
| `squared_error` | float | $(\hat{\tau} - \tau_{true})^2$. Used for RMSE aggregation later. |
| `coverage` | bool | True if $\tau_{true}$ is within CI. |

*Note: RMSE is NOT stored in the per-run `CausalEstimate` object. It is an aggregated metric calculated across runs in the summary phase.*

## 3. Data Flow

1.  **Generation**: `scm_generator.py` creates `SyntheticDataset` files.
2.  **Imputation**: `imputation.py` processes `SyntheticDataset` to create `ImputationResult` files.
3.  **Estimation**: `causal_estimation.py` processes `ImputationResult` to create `CausalEstimate` records.
4.  **Divergence Check**: `metrics.py` compares IPW and PSM estimates for each run. If `|IPW - PSM| > 0.1` or CIs do not overlap, `divergence_flag` is set to `True` in `ImputationResult`.
5.  **Aggregation**: `metrics.py` aggregates `CausalEstimate` records into summary statistics (bias, coverage, RMSE, p-values).

## 4. File Formats

-   **Raw Data**: Parquet (efficient storage, typed columns).
-   **Results**: JSON (structured metadata) or CSV (tabular metrics).
-   **Checksums**: Stored in `data/checksums.json`.
