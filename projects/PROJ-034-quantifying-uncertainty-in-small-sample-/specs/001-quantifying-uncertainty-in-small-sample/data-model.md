# Data Model: Quantifying Uncertainty in Small Sample Regression Models

## Overview

This document defines the data structures used for simulation configuration, data generation, model outputs, and aggregated metrics. All data is stored in JSON/Parquet formats for reproducibility.

## Entities

### 1. SimulationConfig
Defines the parameters for a single simulation batch.

```yaml
type: object
properties:
  n_samples:
    type: integer
    minimum: 3
    maximum: 49
    description: "Sample size (N)"
  n_predictors:
    type: integer
    minimum: 2
    description: "Number of predictors (p)"
  target_correlation:
    type: number
    minimum: 0.0
    maximum: 1.0
    description: "Target correlation between predictors (rho)"
  noise_scale:
    type: number
    minimum: 0.0
    description: "Standard deviation of the error term"
  true_coefficients:
    type: array
    items:
      type: number
    description: "True beta values for each predictor"
  seed:
    type: integer
    description: "Random seed for reproducibility"
  prior_scale_factor:
    type: number
    description: "Multiplier for prior scale (e.g., 1.0 for Normal(0,10), 0.5 for Normal(0,5))"
  backend_engine:
    type: string
    enum: ["cmdstanpy"]
    description: "Stan backend engine (CPU-optimized)"
```

### 2. DatasetInstance
A single realization of synthetic data.

```yaml
type: object
properties:
  instance_id:
    type: string
    description: "Unique identifier for this dataset instance"
  x_matrix:
    type: array
    items:
      type: array
      items:
        type: number
    description: "Predictor matrix (N x p)"
  y_vector:
    type: array
    items:
      type: number
    description: "Outcome vector (N)"
  true_coefficients:
    type: array
    items:
      type: number
    description: "Ground truth beta values"
  target_correlation:
    type: number
    description: "Target correlation parameter used for generation"
  realized_correlation:
    type: number
    description: "Actual sample correlation of the generated predictors"
  realized_vif:
    type: object
    description: "Variance Inflation Factor for each predictor (realized)"
  collinearity_flag:
    type: boolean
    description: "True if any realized VIF > 10"
  rank_deficient:
    type: boolean
    description: "True if the matrix is rank deficient"
```

### 3. IntervalResult
Outputs from a single model fit on a single dataset.

```yaml
type: object
properties:
  instance_id:
    type: string
    description: "Reference to the dataset instance"
  method:
    type: string
    enum: ["ols", "bootstrap_bca", "bayesian"]
    description: "Method used"
  coefficient_estimates:
    type: array
    items:
      type: number
    description: "Estimated beta values"
  interval_lower:
    type: array
    items:
      type: number
    description: "Lower bounds of 95% intervals"
  interval_upper:
    type: array
    items:
      type: number
    description: "Upper bounds of 95% intervals"
  covered:
    type: array
    items:
      type: boolean
    description: "Binary flag: true if true beta is in interval"
  diagnostics:
    type: object
    description: "Method-specific diagnostics (e.g., R-hat, run time)"
```

### 4. CoverageMetric
Aggregated statistics across Monte Carlo replications.

```yaml
type: object
properties:
  method:
    type: string
    enum: ["ols", "bootstrap_bca", "bayesian"]
    description: "Method name"
  n_replications:
    type: integer
    description: "Total number of simulations"
  coverage_rate:
    type: number
    minimum: 0.0
    maximum: 1.0
    description: "Empirical coverage probability"
  average_interval_width:
    type: number
    description: "Mean width of intervals"
  standard_error:
    type: number
    description: "Monte Carlo standard error of coverage"
  convergence_rate:
    type: number
    minimum: 0.0
    maximum: 1.0
    description: "Percentage of valid runs (e.g., R-hat < 1.05)"
  cae_score:
    type: number
    description: "Coverage-Adjusted Efficiency score (penalizes width if coverage deviates)"
```

## Storage Strategy

*   **Raw Data**: `data/simulated/{config_hash}.parquet` (DatasetInstance).
*   **Results**: `data/results/{method}_{config_hash}.parquet` (IntervalResult).
*   **Aggregates**: `data/results/coverage_summary.json` (CoverageMetric).
*   **Validation**: `data/validation/uci_results.json` (IntervalResult for real data).