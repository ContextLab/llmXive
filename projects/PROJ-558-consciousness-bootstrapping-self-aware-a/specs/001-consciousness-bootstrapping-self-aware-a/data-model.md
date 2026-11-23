# Data Model: Consciousness Bootstrapping: Self-Aware AI Through Recursive Introspection

## Overview

This document defines the data structures used for model checkpoints, evaluation results, and statistical reports. All data is serialized to JSON/Parquet for reproducibility and checksumming.

## Entity Definitions

### ModelCheckpoint
Represents the saved state of a trained model. Defined in `code/models/checkpoint.py`.

```yaml
type: object
properties:
  model_id:
    type: string
    description: "Unique identifier for the run (e.g., seed_1_recursive)"
  architecture:
    type: string
    enum: ["recursive", "baseline"]
    description: "Type of model architecture"
  seed:
    type: integer
    description: "Random seed used for initialization"
  hyperparameters:
    type: object
    properties:
      batch_size:
        type: integer
      epochs:
        type: integer
      recursion_depth:
        type: integer
      learning_rate:
        type: number
  weights_path:
    type: string
    description: "Relative path to the .bin or .safetensors file"
  checksum:
    type: string
    description: "SHA-256 hash of the weights file"
  created_at:
    type: string
    format: date-time
```

### EvaluationResult
A structured record for a single test item (question) and its generation paths. Defined in `code/evaluation/results.py`.

```yaml
type: object
properties:
  question_id:
    type: string
    description: "Unique ID for the question"
  dataset_source:
    type: string
    enum: ["gsm8k", "mmlu"]
  ground_truth:
    type: string
    description: "The correct answer"
  generated_paths:
    type: array
    items:
      type: object
      properties:
        path_id:
          type: integer
        text:
          type: string
        confidence_score:
          type: number
          format: float
          description: "Average confidence of tokens in the path"
        is_correct:
          type: boolean
    minItems: 5
    maxItems: 5
  majority_vote:
    type: string
    description: "The answer chosen by majority vote"
  is_consistent:
    type: boolean
    description: "Whether majority_vote matches ground_truth"
  metrics:
    type: object
    properties:
      self_consistency:
        type: boolean
      error_detection_score:
        type: number
        format: float
      calibration_brier:
        type: number
        format: float
      calibration_ece:
        type: number
        format: float
  timestamp:
    type: string
    format: date-time
```

### StatisticalReport
Aggregated results from multiple seeds.

```yaml
type: object
properties:
  experiment_id:
    type: string
  seeds:
    type: array
    items:
      type: integer
  metrics_summary:
    type: object
    properties:
      self_consistency:
        type: object
        properties:
          mean_recursive:
            type: number
          mean_baseline:
            type: number
          percentage_difference:
            type: number
            description: "Percentage difference in self-consistency scores"
          p_value:
            type: number
          effect_size_cohen_d:
            type: number
          bonferroni_adjusted_p:
            type: number
      error_detection:
        type: object
        properties:
          mean_recursive:
            type: number
          mean_baseline:
            type: number
          percentage_difference:
            type: number
          p_value:
            type: number
          effect_size_cohen_d:
            type: number
          bonferroni_adjusted_p:
            type: number
      calibration:
        type: object
        properties:
          mean_recursive:
            type: number
          mean_baseline:
            type: number
          percentage_difference:
            type: number
          p_value:
            type: number
          effect_size_cohen_d:
            type: number
          bonferroni_adjusted_p:
            type: number
  sensitivity_analysis:
    type: array
    items:
      type: object
      properties:
        threshold:
          type: number
        false_positive_rate:
          type: number
        false_negative_rate:
          type: number
  conclusion:
    type: string
    description: "Plain text summary of findings"
```

## Data Flow

1. **Training**: `train_loop.py` produces `ModelCheckpoint` files in `data/checkpoints/`.
2. **Evaluation**: `runner.py` loads checkpoints, runs inference on `GSM8K`/`MMLU`, and produces a list of `EvaluationResult` objects saved as `data/results/eval_results_<seed>.json`.
3. **Analysis**: `stats.py` aggregates `EvaluationResult` files, performs t-tests, and generates `StatisticalReport` saved as `data/results/statistical_report.json`.

## Serialization

- `ModelCheckpoint` and `EvaluationResult` classes are defined in `code/models/checkpoint.py` and `code/evaluation/results.py` respectively.
- Both classes implement `to_dict()` and `from_dict()` methods for JSON serialization.
- All numeric fields are stored as floats or integers as appropriate.
- All timestamps are in ISO 8601 format.