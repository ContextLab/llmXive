# Data Model: Exploring the Impact of Data Imputation Methods on Causal Inference

## Overview

This document defines the data structures, schemas, and flow for the simulation study. All data is stored in `data/` with checksums. The primary artifact is `data/results/simulation_summary.csv`, which serves as the Single Source of Truth for all analysis and figures.

## Entity Definitions

### 1. SyntheticDataset
Represents a single generated instance of the SCM.
- **Attributes**:
  - `run_id`: Unique identifier (UUID or hash of seed).
  - `seed`: Random seed used for generation.
  - `sample_size`: Number of samples (default 1000).
  - `ground_truth_ate`: $\tau_{true}$ (float).
  - `mnar_beta`: $\beta$ parameter (float).
  - `missingness_rate`: Proportion of missing $Y$ (float).
  - `data_path`: Relative path to the generated CSV/Parquet file.

### 2. ImputationResult
Represents the output of an imputation method.
- **Attributes**:
  - `run_id`: FK to SyntheticDataset.
  - `method`: "Mean", "KNN", "MICE".
  - `convergence_status`: "success", "failed", "warning".
  - `imputed_data_path`: Path to imputed dataset.
  - `bias_estimate`: $|\hat{\tau} - \tau_{true}|$ (float).
  - `rmse`: Root Mean Squared Error (float).

### 3. CausalEstimate
Represents the final ATE calculation.
- **Attributes**:
  - `run_id`: FK to SyntheticDataset.
  - `method`: Imputation method.
  - `estimator`: "IPW" or "PSM".
  - `estimated_ate`: $\hat{\tau}$ (float).
  - `standard_error`: SE of the estimate (float).
  - `ci_lower`: Lower bound of 95% CI (float).
  - `ci_upper`: Upper bound of 95% CI (float).
  - `bias`: Absolute bias (float).
  - `coverage`: 1 if true ATE in CI, 0 otherwise (int).

## Data Flow

1.  **Generation**: `code/sim/generate.py` creates `SyntheticDataset` files in `data/raw/`.
2.  **Imputation**: `code/sim/impute.py` processes raw data, outputs `ImputationResult` files.
3.  **Estimation**: `code/sim/estimate.py` processes imputed data, outputs `CausalEstimate` files.
4.  **Aggregation**: `code/analysis/run_simulation.py` aggregates all results into `data/results/simulation_summary.csv`.
5.  **Analysis**: `code/analysis/sensitivity.py` and `visualization.py` read the summary CSV.

## Schema Constraints

- **Run ID**: Must be unique across all runs.
- **Ground Truth**: Must match the theoretical $\tau_{true}$ defined in the generation script for the given seed.
- **Missingness**: $M$ must correlate with $Y$ as specified by $\beta$.
- **Convergence**: If `convergence_status` is "failed", `estimated_ate` and `bias` must be `null`.
- **Coverage**: Calculated as binary (0/1) per run; aggregated coverage is the mean of this column.

## File Formats

- **Raw/Intermediate Data**: CSV or Parquet (Parquet preferred for efficiency).
- **Results Summary**: CSV (UTF-8).
- **Verification Logs**: JSON.
- **Figures**: PNG (300 DPI).
