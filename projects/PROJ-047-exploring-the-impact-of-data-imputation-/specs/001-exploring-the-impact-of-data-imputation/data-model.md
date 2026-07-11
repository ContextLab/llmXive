# Data Model: Exploring the Impact of Data Imputation Methods on Causal Inference

## Entities

### 1. SyntheticDataset
Represents a single generated instance of the SCM.
- **Attributes**:
  - `run_id` (str): Unique identifier for the simulation run.
  - `seed` (int): Random seed for reproducibility.
  - `n_samples` (int): Number of samples (default 1000).
  - `ground_truth_ate` (float): The true $\alpha$ parameter used in generation (regenerated via regenerate_ground_truth).
  - `mnar_beta` (float): The $\beta_{mnar}$ parameter used for missingness.
  - `mnar_alpha` (float): The $\alpha_{mnar}$ parameter used in logistic missingness model.
  - `missingness_rate` (float): Observed proportion of missing $Y$.
  - `data_path` (str): Relative path to the generated CSV/Parquet file.
  - `checksum` (str): SHA-256 hash of the file.

### 2. ImputationResult
Represents the output of an imputation method applied to a `SyntheticDataset`.
- **Attributes**:
  - `run_id` (str): Link to SyntheticDataset.
  - `method` (str): "mean", "knn", "mice".
  - `convergence_status` (str): "success", "failed", "timeout".
  - `imputed_data_path` (str): Path to the imputed file.
  - `imputation_time` (float): Time taken in seconds.

### 3. CausalEstimate
Represents the final ATE calculation for a specific imputation method and estimator.
- **Attributes**:
  - `run_id` (str): Link to ImputationResult.
  - `estimator` (str): "ipw", "psm".
  - `estimated_ate` (float): Calculated ATE.
  - `standard_error` (float): SE of the estimate.
  - `confidence_interval_lower` (float): 95% CI lower bound.
  - `confidence_interval_upper` (float): 95% CI upper bound.
  - `bias` (float): $|\hat{\tau} - \tau_{true}|$.
  - `rmse` (float): Root Mean Square Error.
  - `coverage` (bool): True if $\tau_{true} \in [CI_{low}, CI_{high}]$.

### 4. StatisticalTestResult
Aggregated results for a specific $\beta$ level.
- **Attributes**:
  - `mnar_beta` (float): The beta value for this group.
  - `test_type` (str): "anova", "friedman", "bootstrap".
  - `p_value` (float): Resulting p-value.
  - `test_statistic` (float): F-statistic or Chi-square.
  - `skewness` (float): Skewness of bias distribution.
  - `bootstrap_ci_diff` (list): [lower, upper] for median difference.
  - `interaction_flag` (bool): True if divergence between IPW and PSM > 0.1.

## File Schema

### `data/results/simulation_summary.csv` — Single Source of Truth
Aggregated results for all runs. **This is the canonical schema for all analysis and figures.**
- **Columns**:
  - `run_id`
  - `seed`
  - `sample_size`
  - `ground_truth_ate` (regenerated via regenerate_ground_truth)
  - `mnar_beta`
  - `mnar_alpha` (regenerated via regenerate_ground_truth)
  - `missingness_rate`
  - `imputation_method`
  - `estimator`
  - `estimated_ate`
  - `standard_error`
  - `ci_lower`
  - `ci_upper`
  - `bias`
  - `rmse`
  - `coverage` (bool: 1 if tau_true in [ci_lower, ci_upper], else 0)
  - `convergence_status`
  - `vif_max` (maximum Variance Inflation Factor for confounders)

### `data/results/statistical_tests.json`
Aggregated statistical test results by beta level.
- **Structure**:
  ```json
  {
    "beta_0.0": {
      "test_type": "anova",
      "p_value": 0.123,
      "test_statistic": 2.456,
      "skewness": 0.5,
      "bootstrap_ci_diff": [0.01, 0.05],
      "interaction_flag": false
    },
    "beta_0.2": { ... },
    ...
  }
  ```

### `data/results/sensitivity_analysis.json`
Trend verification results.
- **Structure**:
  ```json
  {
    "bias_trend": {
      "spearman_rho": 0.95,
      "p_value": 0.001,
      "monotonicity_confirmed": true
    },
    "coverage_trend": {
      "slope": -0.45,
      "p_value": 0.002,
      "negative_slope_confirmed": true
    }
  }
  ```
