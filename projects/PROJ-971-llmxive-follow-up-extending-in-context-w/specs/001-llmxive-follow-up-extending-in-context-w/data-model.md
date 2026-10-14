# Data Model: llmXive follow‑up: extending "In-Context World Modeling for Robotic Control"

**Feature**: `001-auto-icwm-latent-dynamics`  
**Date**: 2026‑10‑13  

## Overview
The project manipulates three primary data artifacts:

1. **Interaction Clip** – raw simulation episode (`.npz` with `states`, `actions`, `observations`).  
2. **Latent Descriptor** – per‑clip statistical summary (variance, autocorr_lag1, spectral_density).  
3. **Hyperparameter Label** – optimal `(tau, k)` pair obtained from grid search (training only).  

Derived artifacts (task‑complexity, validation results) are also modeled.

## Schemas

### 1. `contracts/descriptor.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Latent Descriptor Record"
type: object
required:
  - clip_id
  - variance
  - autocorr_lag1
  - spectral_density
properties:
  clip_id:
    type: string
    description: "Unique identifier for the interaction clip (e.g., 'clip_00123')."
  variance:
    type: number
    description: "Sample variance of the latent token sequence."
  autocorr_lag1:
    type: number
    description: "Lag‑1 autocorrelation of the latent token sequence."
  spectral_density:
    type: number
    description: "Mean power spectral density (Welch estimate) across token dimensions."
```

### 2. `contracts/label.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Hyperparameter Label Record"
type: object
required:
  - clip_id
  - tau
  - k
  - success_rate
properties:
  clip_id:
    type: string
    description: "Identifier matching the descriptor record."
  tau:
    type: number
    minimum: 0.1
    maximum: 2.0
    description: "Optimal sampling temperature found by grid search."
  k:
    type: integer
    minimum: 1
    maximum: 64
    description: "Optimal context window length (tokens)."
  success_rate:
    type: number
    minimum: 0.0
    maximum: 1.0
    description: "Empirical success rate achieved with (tau, k)."
```

### 3. `contracts/complexity.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Task Complexity Record"
type: object
required:
  - config_id
  - subgoal_count
properties:
  config_id:
    type: string
    description: "Identifier for the robot configuration / simulation scene."
  subgoal_count:
    type: integer
    minimum: 1
    description: "Number of distinct sub‑goals defined in the environment."
```

### 4. `contracts/validation_results.schema.yaml`
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "Zero‑Shot Validation Results"
type: object
required:
  - clip_id
  - predicted_tau
  - predicted_k
  - auto_success
  - baseline_success
  - success_diff
properties:
  clip_id:
    type: string
  predicted_tau:
    type: number
  predicted_k:
    type: integer
  auto_success:
    type: boolean
    description: "Whether the Auto‑ICWM run succeeded on this clip."
  baseline_success:
    type: boolean
    description: "Whether the fixed‑baseline run succeeded on this clip."
  success_diff:
    type: integer
    description: "1 if auto succeeded and baseline failed, -1 if opposite, 0 if tie."
```

## Data Flow Diagram (conceptual)

```
generate_clips.py --> raw/.npz
extract_descriptors.py --> descriptors.csv (validated by descriptor.schema.yaml)
grid_search_labels.py --> labels.csv (validated by label.schema.yaml)
train_regressor.py --> model/regressor.pt
validate_autocwm.py --> validation_results.csv (validated by validation_results.schema.yaml)
```

All CSV files are UTF‑8, comma‑separated, with a header row matching the schema field names.

---



