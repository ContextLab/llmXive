# Data Model: Consciousness Bootstrapping: Self-Aware AI Through Recursive Introspection

## 1. Overview

This document defines the data structures, schemas, and flow for the project. All data is stored in `data/` and `artifacts/` directories. Raw data is streamed; processed data is checksummed.

## 2. Data Flow Diagram

```mermaid
graph TD
    A[Pile (arXiv) Stream] -->|100k tokens| B(Training Data)
    C[GSM8K Stream] -->|Test Set| D(Evaluation Data)
    E[MMLU Stream] -->|Dev Set| D
    B -->|Train| F[Recursive Model Checkpoint]
    B -->|Train| G[Baseline Model Checkpoint]
    F -->|Eval| H[Recursive Metrics JSON]
    G -->|Eval| I[Baseline Metrics JSON]
    H -->|Analysis| J[Statistical Report YAML]
    I -->|Analysis| J
```

## 3. Entity Definitions

### 3.1 ModelCheckpoint
Represents a trained model state.
- `id`: Unique string (e.g., `recursive_seed_001`).
- `model_type`: `recursive` or `baseline`.
- `seed`: Integer random seed.
- `path`: Relative path to checkpoint file.
- `hash`: SHA-256 checksum of the file.
- `training_params`: JSON object of hyperparameters.

### 3.2 EvaluationResult
Structured record for a single test item.
- `question_id`: Unique string.
- `dataset`: `gsm8k`, `mmlu`, etc.
- `input_text`: The prompt.
- `ground_truth`: Correct answer.
- `generated_paths`: List of strings (N=10).
- `majority_vote`: String (most frequent answer).
- `confidence_scores`: List of floats (one per path).
- `correct`: Boolean (majority vote == ground truth).
- `tie_breaker_used`: Boolean (True if tie-breaking rule was applied).
- `metrics`: JSON object with `consistency`, `calibration`, `error_detection` scores.
- **First Pass Output**: (For T043) The output of the first pass generation (before recursion).

### 3.3 StatisticalReport
Summary of the analysis.
- `experiment_id`: String.
- `seeds`: List of integers.
- `metrics_summary`: JSON object with mean, std, p-value, effect_size for each metric.
- `correction_method`: `bonferroni`.
- `conclusion`: String summary.

## 4. File Formats

### 4.1 Metrics JSON
Located in `artifacts/reports/metrics_seed_{seed}.json`.
```json
{
  "seed": 42,
  "model_type": "recursive",
  "results": [
    {
      "question_id": "gsm8k_001",
      "correct": true,
      "confidence": 0.85,
      "consistency_score": 0.9,
      "tie_breaker_used": false
    }
  ],
  "aggregate": {
    "self_consistency_mean": 0.75,
    "brier_score": 0.12,
    "roc_auc": 0.88
  }
}
```

### 4.2 Statistical Report YAML
Located in `artifacts/reports/statistical_report.yaml`.
```yaml
experiment_id: "exp_001"
seeds: [42, 123, 456, 789, 101]
metrics:
  self_consistency:
    mean_diff: 0.05
    p_value: 0.03
    effect_size: 0.45
    adjusted_p_value: 0.09
  brier_score:
    mean_diff: -0.02
    p_value: 0.15
    effect_size: 0.20
    adjusted_p_value: 0.45
  roc_auc:
    mean_diff: 0.03
    p_value: 0.04
    effect_size: 0.35
    adjusted_p_value: 0.12
correction_method: "bonferroni"
conclusion: "Recursive model shows significant improvement in self-consistency after correction."
```

## 5. Data Hygiene & Checksums

- **Raw Data**: Not stored. Streamed from HF.
- **Processed Data**: `artifacts/reports/*.json` and `*.yaml`.
- **Checksums**: Recorded in `state/projects/PROJ-558-consciousness-bootstrapping-self-aware-a.yaml` under `artifact_hashes`.
- **PII**: None expected in GSM8K/MMLU. Pile filtered for PII before training (via `datasets` preprocessing).

## 6. Tie-Breaking Rule
In the event of a majority vote tie (e.g., 5 correct vs. 5 incorrect), the system MUST select the path with the **highest average confidence score** as the tie-breaker. This rule is documented here and implemented in the evaluation script.