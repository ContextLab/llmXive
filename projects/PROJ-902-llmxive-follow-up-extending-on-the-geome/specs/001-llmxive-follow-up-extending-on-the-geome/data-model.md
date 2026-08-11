# Data Model: llmXive follow‑up – extending “On the Geometry of On‑Policy Distillation”

## 1. GSM8K Dataset Schema
| Field | Type | Description |
|-------|------|-------------|
| `question` | string | Natural‑language math problem statement. |
| `answer` | string | Ground‑truth solution (may contain LaTeX). |
| `category` *(optional)* | string | Difficulty tier supplied by the original dataset. |
| `id` | string | Unique identifier for the example. |

*The dataset is accessed via `datasets.load_dataset("openai/gsm8k", "main")`. The loader returns a `DatasetDict` with splits `train`, `test`.*

## 2. Subspace Mask Schema (`mask.json`)
```yaml
type: object
description: "Binary mask per model layer indicating which parameters are trainable."
properties:
  layer_name:
    type: array
    items:
      type: boolean
    description: "Boolean mask for the flattened weight matrix of the layer."
required:
  - layer_name
additionalProperties: false
```

## 3. Experiment Result Schema (`contracts/experiment_results.schema.yaml`)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: "ExperimentResults"
description: "Per‑run metrics for a single experimental condition."
type: object
properties:
  condition:
    type: string
    description: "One of: opd_full, frozen_opd, frozen_sft, random_sft."
  seed:
    type: integer
    description: "Random seed used for this run."
  accuracy:
    type: number
    description: "Test accuracy on the held‑out generalization subset (0‑1)."
  peak_ram_gb:
    type: number
    description: "Maximum resident memory (GiB) recorded during the run."
  wall_time_sec:
    type: number
    description: "Total wall‑clock time (seconds) for the run."
  loss_per_epoch:
    type: array
    items:
      type: number
    description: "List of loss values (one per epoch)."
  delta_loss:
    type: array
    items:
      type: number
    description: "ΔL = loss_i − loss_{i‑1} for each epoch i>0."
  plateau_epoch:
    type: [integer, "null"]
    description: "First epoch where ΔL < 0.001 for two consecutive epochs; null if never plateaued."
required:
  - condition
  - seed
  - accuracy
  - peak_ram_gb
  - wall_time_sec
  - loss_per_epoch
  - delta_loss
  - plateau_epoch
additionalProperties: false
```

## 4. Authority Artifact (`state.yaml`)
`state.yaml` aggregates all experiment results and analysis:

```yaml
metadata:
  generated_at: "2026-08-11T12:00:00Z"
  git_commit: "<SHA>"
  config_hash: "<hash>"
experiment_results:
  - condition: opd_full
    seed: 0
    accuracy: high
    peak_ram_gb: on the order of a few gigabytes
    wall_time_sec: appropriate duration for the planned experiments
    loss_per_epoch: [higher loss, moderate loss, 1.62]
    delta_loss: [a modest negative value]
    plateau_epoch: null
  # ... more entries for each seed & condition ...
analysis:
  power_opd: elevated (qualitative assessment)
  tost:
    p_lower: a qualitatively low probability threshold.
    p_upper: a modest upper bound
    decision: "equivalent"
    inconclusive: false
  sft_opd_mask:
    mean_drop: a modest reduction
    t_stat: a modest positive value
    p_value: indicative of a non‑significant result
    decision: "no significant drop"
    inconclusive: false
  sft_random_mask:
    mean_drop: a modest reduction.
    t_stat: significant (indicating a statistically notable effect)
    p_value: indicates statistical significance.
    decision: "significant drop"
    inconclusive: false
  sensitivity:
    variance_thresholds: [a lower variance capture level (qualitatively high), 0.99]
    tost_results:
      - threshold: 0.90
        p_lower: 0.07
        p_upper: 0.09
        decision: "non‑equivalent"
      - threshold: 0.95
        p_lower: 0.032
        p_upper: 0.041
        decision: "equivalent"
      - threshold: 0.99
        p_lower: 0.12
        p_upper: 0.15
        decision: "non‑equivalent"
resource_usage:
  max_peak_ram_gb: sufficient to accommodate the anticipated workload.
  max_wall_time_sec: a sufficiently large maximum wall‑time
```

*All fields are validated against the schemas above during CI (`jsonschema` library).*