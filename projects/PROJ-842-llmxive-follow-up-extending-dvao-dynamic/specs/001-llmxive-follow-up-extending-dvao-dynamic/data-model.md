# Data Model: llmXive follow‑up: extending “DVAO: Dynamic Variance‑adaptive Advantage Optimization for Multi‑reward”

## Overview
All artifacts are stored as JSON files under `data/processed/`. Each file conforms to a strict JSON‑Schema (see `contracts/`), enabling automated validation in the CI pipeline.

## Core Entities & Files

| Entity | Produced By | File | Schema |
|--------|--------------|------|--------|
| **Theoretical Bound** | `src/derivation/sample_complexity.py` | `theoretical_bound.json` | `contracts/theoretical_bound.schema.yaml` |
| **Synthetic MDP Configuration** | `src/environment/synthetic_mdp.py` | `noise_properties.json` | `contracts/synthetic_mdp.schema.yaml` |
| **Empirical Run Results** | `src/analysis/statistics.py` (after full suite) | `empirical_results.json` | `contracts/empirical_results.schema.yaml` |
| **Construct‑Validity Summary** | `scripts/validate_construct_validity.py` | `construct_validity_results.json` | `contracts/construct_validity_results.schema.yaml` |
| **Statistical Summary** | `src/analysis/statistics.py` | `statistical_results.json` | `contracts/statistical_result.schema.yaml` |
| **Pareto Oracle Output** (optional debugging) | `src/analysis/pareto_oracle.py` | `pareto_oracle.json` | (internal, not exposed to paper) |

## Schema Highlights

### `theoretical_bound.json`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  n_range:
    type: array
    items: {type: integer}
  variance_equation:
    type: string
  sample_complexity_bound:
    type: string
  assumptions:
    type: array
    items: {type: string}
required: [n_range, variance_equation, sample_complexity_bound, assumptions]
```

### `noise_properties.json`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  experiment_id: {type: string}
  n_objectives: {type: integer}
  target_correlation: {type: number}
  achieved_correlation_matrix:
    type: array
    items:
      type: array
      items: {type: number}
  noise_distribution_type: {type: string}
  effective_state_space_size: {type: integer}
  seed: {type: integer}
required:
  - experiment_id
  - n_objectives
  - achieved_correlation_matrix
  - noise_distribution_type
  - effective_state_space_size
  - seed
additionalProperties: false
```

### `empirical_results.json` (excerpt)
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
    minimum: 0
    maximum: 1
  heuristic_variance_mean:
    type: number
    description: "Mean variance estimated by heuristic"
    minimum: 0
  theoretical_noise_variance:
    type: number
    description: "Known injected noise variance sigma^2"
    minimum: 0
  deviation_ratio:
    type: number
    description: "Ratio of heuristic variance to theoretical variance"
    minimum: 0
  sample_count_to_pareto:
    type: integer
    description: "Number of episodes to reach Pareto threshold"
    minimum: 1
  theoretical_sample_bound:
    type: number
    description: "Theoretical lower bound on sample count"
    minimum: 0
  pareto_frontier_distance:
    type: number
    description: "Distance of final policy to true Pareto frontier"
    minimum: 0
  scaling_slope_t_p_value:
    type: number
    description: "P-value from t-test on the regression slope (validating scaling law)"
    minimum: 0
    maximum: 1
  regression_slope:
    type: number
    description: "Slope beta from log-log regression of sample count vs N."
  r_squared:
    type: number
    description: "R-squared value of the regression fit."
    minimum: 0
    maximum: 1
  heuristic_bias_t_p_value:
    type: number
    description: "P-value from one-sample t-test on heuristic bias (validating estimator)"
    minimum: 0
    maximum: 1
  convergence_speed_episodes:
    type: integer
    description: "Number of episodes required to reach the predefined reward threshold (FR‑019)."
    minimum: 1
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
  - convergence_speed_episodes
additionalProperties: false
```

### `construct_validity_results.json`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  distribution_type: {type: string}
  n_objectives: {type: integer}
  deviation_from_bound: {type: number}
  pass_criteria_met: {type: boolean}
required: [distribution_type, n_objectives, deviation_from_bound, pass_criteria_met]
```

## Data Flow Diagram (conceptual)
```
Derivation → theoretical_bound.json
          ↘
Synthetic MDP → noise_properties.json → (used by) → heuristic.py / baseline_scalarization.py
          ↘
Full training runs → empirical_results.json → statistics.py → statistical_results.json
          ↘
Construct‑validity sweeps → construct_validity_results.json
```
All downstream artifacts (figures, tables) reference the JSON source that generated them, satisfying Principle IV (single source of truth).

---


