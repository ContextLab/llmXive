# Data Model: Dendritic Computation in Transformers

## Overview

This document defines the data structures, schemas, and file formats used in the project. All data artifacts are checksummed and traceable to the code that generated them.

## Directory Structure

```text
data/
├── raw/
│   └── glue_sst2/
│       ├── train.jsonl          # Raw train split (checksummed)
│       └── dev.jsonl            # Raw dev split (checksummed)
├── processed/
│   └── sst2_tokenized/
│       ├── train.pt             # Tokenized tensors
│       └── dev.pt               # Tokenized tensors
└── experiments/
    ├── seed_001/
    │   ├── model_baseline.pt    # Checkpoint
    │   ├── model_dendritic.pt   # Checkpoint
    │   ├── logs.jsonl           # Training logs (loss, accuracy)
    │   ├── dendritic_params.json # Dendritic configuration
    │   └── probing_results.json # Probing accuracies per layer
    └── seed_002/
        ...
```

## Data Schemas

### 1. Training Logs (`logs.jsonl`)

Each line is a JSON object recording metrics at a training step.

```yaml
# contracts/experiment_log.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  step:
    type: integer
    description: "Global training step number"
  seed:
    type: integer
    description: "Random seed for this run"
  model_type:
    type: string
    enum: ["baseline", "dendritic"]
    description: "Architecture variant"
  loss:
    type: number
    description: "Training loss at this step"
  accuracy:
    type: number
    minimum: 0.0
    maximum: 1.0
    description: "Validation accuracy at this step"
  elapsed_time_seconds:
    type: number
    description: "Wall-clock time elapsed since start"
  gradient_clipped:
    type: boolean
    description: "True if gradient clipping was applied"
required:
  - step
  - seed
  - model_type
  - loss
  - accuracy
  - elapsed_time_seconds
additionalProperties: false
```

### 2. Dendritic Parameters (`dendritic_params.json`)

Configuration and logged values for the dendritic mechanism, required by Constitution Principle VI.

```yaml
# contracts/dendritic_params.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  experiment_id:
    type: string
    description: "Unique identifier for the experiment run"
  seed:
    type: integer
    description: "Random seed used"
  model_type:
    type: string
    const: "dendritic"
  local_nonlinearity_type:
    type: string
    description: "Activation function used in dendritic branches (e.g., 'tanh', 'sigmoid')"
  plateau_potential_gate:
    type: boolean
    description: "Whether plateau potential gating is enabled"
  calcium_modulation_active:
    type: boolean
    description: "Whether calcium modulation influences the forward pass (and gradients)"
  dendritic_threshold:
    type: number
    minimum: 0.0
    maximum: 1.0
    description: "Threshold for local nonlinearity in dendritic units (sensitivity)"
  num_branches:
    type: integer
    minimum: 1
    description: "Number of dendritic branches per unit"
required:
  - experiment_id
  - seed
  - model_type
  - local_nonlinearity_type
  - plateau_potential_gate
  - calcium_modulation_active
  - dendritic_threshold
  - num_branches
additionalProperties: false
```

### 3. Probing Results (`probing_results.json`)

Aggregated results for linear probes on intermediate layers.

```yaml
# contracts/probing_results.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  experiment_id:
    type: string
    description: "Unique identifier for the experiment run"
  seed:
    type: integer
    description: "Random seed used"
  model_type:
    type: string
    enum: ["baseline", "dendritic"]
    description: "Architecture variant"
  layer_results:
    type: array
    items:
      type: object
      properties:
        layer_index:
          type: integer
          description: "Index of the transformer layer (0 to N-1)"
        probing_accuracy:
          type: number
          minimum: 0.0
          maximum: 1.0
          description: "Accuracy of the linear probe on this layer"
        task:
          type: string
          description: "Probing task name (e.g., 'sentiment', 'syntax')"
      required:
        - layer_index
        - probing_accuracy
        - task
  summary:
    type: object
    properties:
      auc_depth:
        type: number
        description: "Area under accuracy-vs-depth curve"
      sample_efficiency_steps:
        type: integer
        description: "Steps to reach fixed accuracy threshold (e.g., 85%)"
      fixed_threshold_accuracy:
        type: number
        description: "The fixed accuracy threshold used for sample efficiency (e.g., 0.85)"
    required:
      - auc_depth
      - sample_efficiency_steps
      - fixed_threshold_accuracy
required:
  - experiment_id
  - seed
  - model_type
  - layer_results
  - summary
additionalProperties: false
```

### 4. Configuration (`config.yaml`)

Hyperparameters and architectural settings.

```yaml
# contracts/config.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
type: object
properties:
  model:
    type: object
    properties:
      type:
        type: string
        enum: ["baseline", "dendritic"]
      hidden_size:
        type: integer
      num_layers:
        type: integer
      dendritic_threshold:
        type: number
        description: "Threshold for local nonlinearity in dendritic units"
      plateau_potential_gate:
        type: boolean
    required:
      - type
      - hidden_size
      - num_layers
  training:
    type: object
    properties:
      max_steps:
        type: integer
      max_wall_clock_hours:
        type: number
        const: 6.0
      learning_rate:
        type: number
      batch_size:
        type: integer
      gradient_clip:
        type: number
        maximum: 1.0
      fixed_target_accuracy:
        type: number
        description: "Fixed accuracy threshold for sample efficiency (e.g., 0.85)"
        minimum: 0.0
        maximum: 1.0
    required:
      - max_steps
      - max_wall_clock_hours
      - learning_rate
      - batch_size
      - fixed_target_accuracy
  seeds:
    type: array
    items:
      type: integer
    minItems: 3
    maxItems: 5
required:
  - model
  - training
  - seeds
additionalProperties: false
```

## Data Hygiene Rules

1. **Checksums**: Every file in `data/raw/` and `data/processed/` is checksummed (SHA-256) and recorded in `state/...yaml`.
2. **Immutability**: Raw files are never modified. Derivations create new files.
3. **PII**: No personally identifiable information is stored. The SST-2 dataset is public and anonymized.
4. **Traceability**: Every result in `data/experiments/` links to a specific `config.yaml` and code commit hash.