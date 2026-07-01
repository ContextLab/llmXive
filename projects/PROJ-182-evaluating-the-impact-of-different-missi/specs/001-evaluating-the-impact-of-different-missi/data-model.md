# Data Model: Evaluating the Impact of Different Missing Data Mechanisms on Regression Discontinuity Designs

## Overview

This document defines the data structures for the simulation study. All data is generated synthetically and stored in memory or temporary CSV/Parquet files during execution. No persistent database is used.

## Key Entities

### 1. SimulationConfig
Defines the parameters for a single simulation run.
- **Fields**:
  - `seed`: Integer (random seed).
  - `n_samples`: Integer (sample size per replication).
  - `true_effect`: Float (ground truth $\tau$).
  - `missing_rate`: Float (0.0 to 1.0).
  - `mechanism`: Enum ["MCAR", "MAR", "MNAR"].
  - `covariate_dependent`: Boolean (for MAR).
  - `outcome_dependent`: Boolean (for MNAR).

### 2. MissingnessPattern
A binary mask indicating missingness for each observation.
- **Fields**:
  - `outcome_mask`: Array[bool] (True if missing).
  - `covariate_mask`: Array[bool] (True if missing).
  - `mechanism`: String (source mechanism).
  - `rate`: Float (actual missingness rate observed).

### 3. EstimationResult
Output of a single replication.
- **Fields**:
  - `replication_id`: Integer.
  - `config_hash`: String (hash of SimulationConfig).
  - `estimator`: Enum ["Naive", "MI", "IPW", "Selection"].
  - `estimate`: Float (point estimate $\hat{\tau}$).
  - `se`: Float (standard error).
  - `ci_lower`: Float.
  - `ci_upper`: Float.
  - `converged`: Boolean (for Selection model).
  - `error_code`: String (if failed).

### 4. AggregatedMetric
Summary statistics across multiple replications.
- **Fields**:
  - `mechanism`: String.
  - `missing_rate`: Float.
  - `estimator`: String.
  - `mean_bias`: Float.
  - `rmse`: Float.
  - `coverage_rate`: Float.
  - `convergence_rate`: Float (for Selection).

## Data Flow

1. **Input**: `config/simulation.yaml` and `config/missingness.yaml` loaded.
2. **Generation**: `rd_data.py` creates synthetic $X, Y, Z$. `missingness.py` applies mask.
3. **Estimation**: Each estimator processes the masked data, producing `EstimationResult`.
4. **Aggregation**: `aggregation.py` groups results by configuration, calculates `AggregatedMetric`.
5. **Output**: `results/metrics.csv` and `results/heatmaps/` generated.

## Storage Format

- **Intermediate Data**: CSV or Parquet (compressed) in `data/`.
- **Results**: CSV in `results/`.
- **Config**: YAML in `config/`.
