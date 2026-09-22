# Data Model: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-rewar"

## Overview

This document defines the data structures used for theoretical derivation, synthetic environment generation, and empirical results. All data is stored in JSON or CSV formats within the `data/processed/` directory.

## Core Entities

### 1. Theoretical Derivation Output
Represents the closed-form mathematical derivation results.
*   **Source**: `src/derivation/sample_complexity.py`
*   **Output**: `data/processed/theoretical_bound.json`

### 2. Synthetic MDP Configuration
Parameters used to generate a specific environment instance.
*   **Source**: `src/environment/synthetic_mdp.py`
*   **Output**: `data/processed/noise_properties.json`

### 3. Empirical Results
Aggregated results from training runs, including heuristic performance and statistical tests.
*   **Source**: `src/analysis/statistics.py`
*   **Output**: `data/processed/empirical_results.json`

### 4. Construct Validity Results
Results from testing different reward distributions.
*   **Source**: `scripts/validate_construct_validity.py`
*   **Output**: `data/processed/construct_validity_results.json`

### 5. Statistical Results
Aggregated statistical analysis including slope and bias tests.
*   **Source**: `src/analysis/statistics.py`
*   **Output**: `data/processed/statistical_results.json`

## Data Schemas

### `theoretical_bound.json`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  n_range:
    type: array
    items:
      type: integer
    description: "Range of N values tested"
  variance_equation:
    type: string
    description: "Closed-form equation string for variance as function of N and sigma"
  sample_complexity_bound:
    type: string
    description: "Closed-form equation string for sample complexity bound"
  assumptions:
    type: array
    items:
      type: string
    description: "List of assumptions (e.g., independent noise, i.i.d.)"
required:
  - n_range
  - variance_equation
  - sample_complexity_bound
  - assumptions
```

### `noise_properties.json`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  experiment_id:
    type: string
    description: "Unique identifier for the environment generation"
  n_objectives:
    type: integer
    description: "Number of objectives N"
  target_correlation:
    type: number
    description: "Target correlation coefficient rho"
  achieved_correlation_matrix:
    type: array
    items:
      type: array
      items:
        type: number
    description: "Actual correlation matrix achieved"
  noise_distribution_type:
    type: string
    description: "Type of noise distribution (Gaussian, Heavy-tailed, etc.)"
  effective_state_space_size:
    type: integer
    description: "Actual state space size used (may be reduced if N > 50)"
required:
  - experiment_id
  - n_objectives
  - achieved_correlation_matrix
  - noise_distribution_type
  - effective_state_space_size
```

### `empirical_results.json`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  experiment_id:
    type: string
    description: "Unique identifier"
  n_objectives:
    type: integer
    description: "Number of objectives N"
  window_size_k:
    type: number
    description: "Moving window size fraction"
  heuristic_variance_mean:
    type: number
    description: "Mean variance estimated by heuristic"
  theoretical_noise_variance:
    type: number
    description: "Known injected noise variance sigma^2"
  deviation_ratio:
    type: number
    description: "Ratio of heuristic variance to theoretical variance"
  sample_count_to_pareto:
    type: integer
    description: "Number of episodes to reach Pareto threshold"
  theoretical_sample_bound:
    type: number
    description: "Theoretical lower bound on sample count"
  pareto_frontier_distance:
    type: number
    description: "Distance of final policy to true Pareto frontier"
  scaling_slope_t_p_value:
    type: number
    description: "P-value from t-test on the regression slope (validating scaling law)"
  regression_slope:
    type: number
    description: "Slope beta from log-log regression of sample count vs N."
  r_squared:
    type: number
    description: "R-squared value of the regression fit."
  heuristic_bias_t_p_value:
    type: number
    description: "P-value from one-sample t-test on heuristic bias (validating estimator)"
required:
  - experiment_id
  - n_objectives
  - heuristic_variance_mean
  - theoretical_noise_variance
  - deviation_ratio
  - sample_count_to_pareto
  - theoretical_sample_bound
  - pareto_frontier_distance
  - scaling_slope_t_p_value
  - regression_slope
  - r_squared
  - heuristic_bias_t_p_value
```

### `construct_validity_results.json`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  distribution_type:
    type: string
    description: "Type of reward distribution (Linear, Sparse, Non-Convex)"
  n_objectives:
    type: integer
    description: "Number of objectives N"
  deviation_from_bound:
    type: number
    description: "Deviation of empirical sample complexity from theoretical bound"
  pass_criteria_met:
    type: boolean
    description: "True if deviation < 10%"
required:
  - distribution_type
  - n_objectives
  - deviation_from_bound
  - pass_criteria_met
```

### `statistical_results.json`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  config_id:
    type: string
    description: "Configuration ID"
  num_objectives:
    type: integer
    description: "Number of objectives (N)"
  window_ratio:
    type: number
    description: "The ratio k / rollout_size used."
  regression_slope:
    type: number
    description: "Slope beta from log-log regression of sample count vs N."
  r_squared:
    type: number
    description: "R-squared value of the regression fit."
  slope_ci_lower:
    type: number
    description: "Lower bound of 95% CI for slope."
  slope_ci_upper:
    type: number
    description: "Upper bound of 95% CI for slope."
  scaling_slope_t_p_value:
    type: number
    description: "P-value from t-test on the regression slope."
  heuristic_bias_t_p_value:
    type: number
    description: "P-value from one-sample t-test on heuristic bias."
  mean_bias:
    type: number
    description: "Mean difference (Heuristic - Known) variance."
  pareto_distance:
    type: number
    description: "Distance of the final policy from the theoretical Pareto frontier."
  convergence_status:
    type: string
    enum:
      - "stable"
      - "unstable"
      - "failed"
    description: "Status of the heuristic convergence."
  false_positive_rate:
    type: number
    description: "Rate of false positives in stability detection."
  noise_distribution_type:
    type: string
    enum:
      - "gaussian"
      - "heavy_tailed"
      - "sparse"
      - "non_convex"
    description: "Type of noise distribution used in the simulation."
  sample_complexity_ratio:
    type: number
    description: "Ratio of empirical samples used to theoretical lower bound K."
  coincidence_delta:
    type: integer
    description: "Difference between failure point N and Pareto distance point."
  timestamp:
    type: string
    format: date-time
    description: "ISO8601 timestamp of analysis."
required:
  - config_id
  - num_objectives
  - window_ratio
  - regression_slope
  - r_squared
  - slope_ci_lower
  - slope_ci_upper
  - scaling_slope_t_p_value
  - heuristic_bias_t_p_value
  - mean_bias
  - pareto_distance
  - convergence_status
  - false_positive_rate
  - noise_distribution_type
  - sample_complexity_ratio
  - coincidence_delta
  - timestamp
additionalProperties: false
```