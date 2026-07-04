# Data Model: Dendritic Computation in Transformers

## Overview

This document defines the data schemas for inputs, intermediate artifacts, and final outputs. All data is stored in JSON/CSV/Parquet formats to ensure reproducibility and machine-readability.

## Entity Relationships

1.  **ExperimentRun**: A single training instance defined by a model type, seed, and hyperparameters.
2.  **Checkpoint**: A snapshot of model weights and optimizer state at a specific step.
3.  **ProbeResult**: The accuracy of a linear classifier trained on a specific layer's representation.
4.  **StatisticalTest**: The result of a paired test (p-value, effect size) comparing models.

## Schemas

### 1. Experiment Configuration (`config.yaml`)

```yaml
# Schema: Experiment Configuration
experiment_name: string
model_type: enum["baseline", "dendritic"]
seed: integer
dendritic_params:
  num_branches: integer
  nonlinearity_threshold: float  # Sensitivity sweep parameter
  plateau_gating: boolean
training_params:
  batch_size: integer
  learning_rate: float
  max_steps: integer
  timeout_hours: float
dataset:
  name: string
  split: string
  checksum: string
```

### 2. Training Log (`logs/train_run_{id}.jsonl`)

```json
# Schema: Training Log Entry
{
  "step": integer,
  "timestamp": "ISO8601",
  "loss": float,
  "accuracy": float,
  "lr": float,
  "gradient_norm": float,
  "clipped_gradients": integer,
  "elapsed_time_seconds": float
}
```

### 3. Probing Results (`results/probe_{model}_{seed}.csv`)

```csv
# Schema: Probing Results
layer_id,model_type,seed,probe_accuracy,probe_loss,probe_f1
0,baseline,42,0.85,0.42,0.84
0,dendritic,42,0.88,0.38,0.87
...
```

### 4. Statistical Analysis (`results/stat_test.json`)

```json
# Schema: Statistical Test Results
{
  "test_type": "wilcoxon_signed_rank",
  "correction_method": "bonferroni",
  "alpha": 0.05,
  "layers": [
    {
      "layer_id": 0,
      "p_value_raw": 0.04,
      "p_value_corrected": 0.20,
      "effect_size_d": 0.65,
      "significant": false
    }
  ],
  "summary": {
    "best_layer": 2,
    "overall_improvement": "significant"
  }
}
```

## Data Flow

1.  **Input**: Raw SST-2 data loaded from HuggingFace.
2.  **Processing**: Tokenized and batched.
3.  **Training**: Logs written to `logs/`. Checkpoints saved to `checkpoints/`.
4.  **Probing**: Intermediate representations extracted, linear classifiers trained, results written to `results/probe_*.csv`.
5.  **Analysis**: Aggregated results processed into `results/stat_test.json`.
