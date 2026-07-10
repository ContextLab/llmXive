# Data Model: Exploring the Impact of Data Imputation Methods on Causal Inference

## Overview

This document defines the data structures, schemas, and relationships for the simulation pipeline. All data is stored in CSV or Parquet format under `data/`.

## Entities

### 1. SyntheticDataset
Represents a single generated dataset with missingness.
- **Attributes**:
  - `seed`: Integer (Unique identifier for the replication).
  - `N`: Integer (Sample size, fixed at 1000).
  - `beta`: Float (MNAR strength parameter).
  - `alpha`: Float (Intercept parameter, solved for target missingness rate).
  - `target_missing_rate`: Float (Target proportion of missing data).
  - `tau_true`: Float (Ground truth ATE).
  - `treatment`: Binary (0/1).
  - `outcome`: Float (Continuous, may contain NaN).
  - `confounders`: Vector (Floats, e.g., `x1`, `x2`, `x3`).
  - `missingness_indicator`: Binary (1 if missing, 0 if observed).

### 2. ImputedDataset
Represents a dataset after imputation.
- **Attributes**:
  - `source_seed`: Integer (Links to `SyntheticDataset.seed`).
  - `method`: String (Mean, KNN, MICE).
  - `data`: Full dataset (Floats, no NaN).
  - `convergence_status`: Boolean (True if MICE converged, N/A for others).

### 3. CausalEstimate
Represents the result of an estimation step.
- **Attributes**:
  - `seed`: Integer.
  - `method`: String (Mean, KNN, MICE).
  - `estimator`: String (IPW, PSM).
  - `estimated_ate`: Float.
  - `standard_error`: Float.
  - `ci_lower`: Float (95% CI lower bound).
  - `ci_upper`: Float (95% CI upper bound).
  - `bias`: Float (Absolute difference from `tau_true`).
  - `rmse`: Float.
  - `beta`: Float (MNAR strength).
  - `alpha`: Float (Intercept).
  - `coverage_indicator`: Boolean (True if `tau_true` is within `[ci_lower, ci_upper]`).
  - `baseline_ate`: Float (ATE from Oracle/Complete Case baseline for this seed).
  - `imputation_bias`: Float (Difference between `estimated_ate` and `baseline_ate`).

## File Structure

```text
data/
├── raw/
│   ├── synthetic_seed_{seed}_beta_{beta}.csv   # Generated data with NaN
│   └── ...
├── processed/
│   ├── imputed_seed_{seed}_method_{method}.csv # Imputed data
│   └── ...
└── results/
    ├── estimates.csv                            # Aggregated CausalEstimate table
    ├── anova_results.json                       # Repeated-Measures ART ANOVA F-stat, p-value
    ├── coverage_results.json                    # CI coverage rates per method
    └── sensitivity_plot.png                     # Bias vs Beta chart
```

## Data Contracts

### Input/Output Schema

The `code/` scripts must adhere to the following schemas (detailed in `contracts/`).
- **Generation Output**: `SyntheticDataset` schema.
- **Imputation Input**: `SyntheticDataset` schema.
- **Imputation Output**: `ImputedDataset` schema.
- **Estimation Input**: `ImputedDataset` schema.
- **Estimation Output**: `CausalEstimate` schema.

## Versioning

- **v1.0**: Initial schema definition.
- **Hashing**: All files in `data/` will be checksummed (SHA-256) and recorded in `state/...yaml`.

