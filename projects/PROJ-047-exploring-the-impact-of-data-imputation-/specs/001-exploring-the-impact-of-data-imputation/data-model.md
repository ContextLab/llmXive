# Data Model: Exploring the Impact of Data Imputation Methods on Causal Inference

## Overview

This document defines the data structures used in the simulation study. All data is stored in `data/` directory, with raw synthetic data in `data/raw/` and processed results in `data/processed/` and `data/results/`.

## Entities

### 1. SyntheticDataset
Represents a single generated instance of the SCM.

*   **Attributes**:
    *   `run_id` (str): Unique identifier (e.g., `seed_123_beta_0.5`).
    *   `seed` (int): Random seed used for generation.
    *   `n_samples` (int): Number of samples (default 1000).
    *   `tau_true` (float): Ground-truth ATE.
    *   `beta` (float): MNAR parameter ($\beta$).
    *   `alpha` (float): Intercept used in the MNAR logistic model (tuned to achieve target missingness rate).
    *   `data` (DataFrame): Columns: `T` (treatment), `Y` (outcome, partially missing), `X1`, `X2` (confounders), `M` (missingness indicator).
 * `missingness_rate` (float): Proportion of missing $Y$ (targeted to be [deferred]).
    *   `correlation_M_Y` (float): Spearman correlation between $M$ and unobserved $Y$ (computed before masking).
    *   `vif_max` (float): Maximum Variance Inflation Factor for confounders.

### 2. ImputationResult
Represents the output of an imputation method applied to a `SyntheticDataset`.

*   **Attributes**:
    *   `run_id` (str): Reference to parent `SyntheticDataset`.
    *   `method` (str): "mean", "knn", "mice".
    *   `imputed_data` (DataFrame): Complete dataset (no missing values).
    *   `convergence_status` (str): "success", "failed", "max_iter_reached".
    *   `iterations` (int): Number of iterations (for MICE).
    *   `runtime_ms` (float): Time taken for imputation.

### 3. CausalEstimate
Represents the final ATE calculation from an imputed dataset.

*   **Attributes**:
    *   `run_id` (str): Reference to parent.
    *   `method` (str): Imputation method.
    *   `estimator` (str): "ipw", "psm".
    *   `ate_est` (float): Estimated ATE.
    *   `se` (float): Standard error.
    *   `ci_lower` (float): 95% CI lower bound.
    *   `ci_upper` (float): 95% CI upper bound.
    *   `bias` (float): $|\hat{\tau} - \tau_{true}|$.
    *   `covered` (bool): True if $\tau_{true} \in [ci\_lower, ci\_upper]$.

## Aggregated Results

### SimulationSummary
Aggregated results across all runs for a specific $\beta$.

*   **Attributes**:
    *   `beta` (float): MNAR parameter.
    *   `method` (str): Imputation method.
    *   `estimator` (str): Causal estimator.
    *   `n_runs` (int): Number of successful runs (target 200).
    *   `mean_bias` (float): Mean absolute bias.
    *   `std_bias` (float): Std dev of bias.
    *   `coverage_rate` (float): Proportion of CIs covering $\tau_{true}$.
    *   `p_value` (float): P-value from Friedman test.

### SensitivityAnalysis
Results of the $\beta$ sweep.

*   **Attributes**:
    *   `beta` (float): Value in sweep.
    *   `method` (str): Imputation method.
    *   `mean_bias` (float): Mean bias at this $\beta$.
    *   `coverage_rate` (float): Coverage at this $\beta$.
    *   `trend_correlation` (float): Spearman $\rho$ of bias vs. $\beta$ (computed over the sweep).

## File Paths

*   `data/raw/synth_{seed}_{beta}.csv`: Raw synthetic data with missingness.
*   `data/processed/{method}_{seed}_{beta}.csv`: Imputed data.
*   `data/results/estimates_{seed}_{beta}.csv`: Causal estimates.
*   `data/results/summary_{beta}.csv`: Aggregated bias metrics.
*   `data/results/sensitivity_analysis.csv`: Final sweep results.