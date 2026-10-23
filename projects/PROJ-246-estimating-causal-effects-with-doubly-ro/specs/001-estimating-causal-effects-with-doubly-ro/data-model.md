# Data Model: Estimating Causal Effects with Doubly Robust Methods

## Overview
The pipeline stores three core artifact types on disk. Each artifact conforms to a JSON/YAML schema located in `contracts/`. Schemas are validated by the test suite before downstream analysis.

## Schemas

### 1. `SimulationConfig` (YAML)
Defines the DGP parameters, sample size, random seed, and model specifications for a single run.

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "SimulationConfig"
type: object
required:
  - seed
  - sample_size
  - dgp_params
  - outcome_model
  - propensity_model
properties:
  seed:
    type: integer
    description: "Fixed random seed for reproducibility."
  sample_size:
    type: integer
    minimum: 10
    description: "Number of observations (N)."
  dgp_params:
    type: object
    required: [beta, beta_interaction, sigma]
    properties:
      beta:
        type: array
        items:
          type: number
        description: "Coefficients for the propensity logistic function (excluding interaction)."
      beta_interaction:
        type: number
        description: "Coefficient for the X₁·X₂ interaction term in the propensity model."
      sigma:
        type: number
        description: "Standard deviation of outcome noise ε."
  outcome_model:
    type: string
    enum: [nonlinear_correct, quadratic_missing_sine, interaction_omitted]
    description: "Outcome model family to be fitted."
  propensity_model:
    type: string
    enum: [logistic_correct, logistic_misspecified, logistic_interaction_heavy]
    description: "Propensity model family to be fitted."
```

### 2. `EstimationResult` (YAML – contract)
Captures the result of a single Monte‑Carlo replication.

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "EstimationResult"
type: object
required:
  - replication_id
  - config_hash
  - ate_estimate
  - ate_std_error
  - ci_lower
  - ci_upper
  - bias
  - coverage
  - outcome_model
  - propensity_model
properties:
  replication_id:
    type: integer
    description: "Index of the Monte‑Carlo replication (1‑based)."
  config_hash:
    type: string
    description: "SHA‑256 hash of the SimulationConfig used."
  ate_estimate:
    type: number
    description: "AIPW estimated average treatment effect."
  ate_std_error:
    type: number
    description: "Standard error of the ATE estimate."
  ci_lower:
    type: number
    description: "Lower bound of the 95 % confidence interval."
  ci_upper:
    type: number
    description: "Upper bound of the 95 % confidence interval."
  bias:
    type: number
    description: "Difference (estimate – true ATE)."
  coverage:
    type: boolean
    description: "True ATE lies within the confidence interval?"
  outcome_model:
    type: string
    enum:
      - nonlinear_correct
      - quadratic_missing_sine
      - interaction_omitted
    description: "Outcome model family used in this replication."
  propensity_model:
    type: string
    enum:
      - logistic_correct
      - logistic_misspecified
      - logistic_interaction_heavy
    description: "Propensity model family used in this replication."
```

### 3. `AggregatedMetrics` (YAML)
Aggregates results across replications for a specific grid configuration.

```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "AggregatedMetrics"
type: object
required:
  - outcome_model
  - propensity_model
  - sample_size
  - mean_bias
  - se_bias
  - coverage_rate
  - interaction_term
properties:
  outcome_model:
    type: string
    enum: [nonlinear_correct, quadratic_missing_sine, interaction_omitted]
  propensity_model:
    type: string
    enum: [logistic_correct, logistic_misspecified, logistic_interaction_heavy]
  sample_size:
    type: integer
  mean_bias:
    type: number
  se_bias:
    type: number
    description: "Standard error of the mean bias across replications."
  coverage_rate:
    type: number
    description: "Proportion of replications where CI covered the true ATE."
  interaction_term:
    type: object
    description: "Meta‑regression coefficient for the outcome × propensity interaction."
    required: [estimate, p_value, std_error]
    properties:
      estimate:
        type: number
      p_value:
        type: number
      std_error:
        type: number
```

## Storage Conventions
- Raw synthetic draws → `data/raw/dgp_seed{seed}_N{sample_size}.csv`  
- Per‑replication results → `data/interim/estimation_results_{hash}.parquet` (validated against `contracts/estimation_result.schema.yaml`)  
- Aggregated metrics → `data/processed/aggregated_metrics.parquet` (conforms to `contracts/aggregated_metrics.schema.yaml`)  
- Checksums → `state/project_artifacts.yaml`

All files are version‑controlled via content hashes; the `state/...yaml` file records the hash and timestamp.

---

