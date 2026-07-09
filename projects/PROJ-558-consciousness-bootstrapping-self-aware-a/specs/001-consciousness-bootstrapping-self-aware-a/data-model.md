# Data Model: Consciousness Bootstrapping

## Overview

This document defines the data structures used for model checkpoints, evaluation results, and statistical reports. All data is stored in JSON/Parquet formats to ensure reproducibility and ease of analysis.

## Entities

### 1. ModelCheckpoint

Represents the saved state of a trained model.

| Field | Type | Description |
|-------|------|-------------|
| `checkpoint_id` | string | Unique identifier (e.g., `seed_001_recursive`). |
| `model_type` | string | `recursive` or `baseline`. |
| `seed` | integer | Random seed used for training. |
| `epoch` | integer | Number of epochs trained. |
| `loss_history` | list[float] | List of total loss values per step. |
| `config` | dict | Hyperparameters (lr, batch_size, etc.). |
| `path` | string | Filesystem path to the checkpoint file. |
| `teacher_label_source` | string | Path to the teacher labels used for training. |

### 2. EvaluationResult

A structured record for a single test item (question).

| Field | Type | Description |
|-------|------|-------------|
| `question_id` | string | Unique ID for the question. |
| `question_text` | string | The input prompt. |
| `ground_truth` | string | The correct answer. |
| `generated_paths` | list[string] | List of 10 generated answer strings. |
| `majority_vote` | string | The answer chosen by majority vote. |
| `is_correct` | boolean | Whether `majority_vote` matches `ground_truth`. |
| `confidence_scores` | list[float] | Confidence score for each of the 10 paths. |
| `avg_confidence` | float | Mean confidence across paths. |
| `consistency_score` | float | Proportion of paths matching the majority vote. |
| `metrics` | dict | Derived metrics: `brier_score`, `ece`, `roc_auc`, `correlation_coefficient`. |

### 3. StatisticalReport

A summary of the statistical analysis across seeds.

| Field | Type | Description |
|-------|------|-------------|
| `analysis_id` | string | Unique identifier for the run. |
| `seeds` | list[int] | List of seeds used (e.g., [1, 2, 3, 4, 5]). |
| `metrics_summary` | dict | Aggregated stats per metric: `mean_diff`, `p_value`, `cohen_d`, `adj_p_value`. |
| `sensitivity_analysis` | dict | Results for thresholds {0.4, 0.5, 0.6}. |
| `conclusion` | string | Text summary of findings. |

## Data Flow

1.  **Training**: `train.py` reads `data/processed/train.parquet` + `data/processed/teacher_labels.parquet` -> produces `artifacts/checkpoints/`.
2.  **Evaluation**: `run_benchmarks.py` reads checkpoints + `data/raw/gsm8k.parquet` -> produces `artifacts/results/seed_XX_eval.json`. *Validates against `contracts/evaluation-schema.schema.yaml`.*
3.  **Analysis**: `stats.py` reads all `seed_XX_eval.json` -> produces `artifacts/results/statistical_report.json`.

## Constraints

*   **Size**: `EvaluationResult` JSON files must be < 100MB each.
*   **Format**: All numeric values must be floats. All strings must be UTF-8.
*   **Versioning**: Checkpoints are versioned by `seed` and `model_type`.
*   **Data Hygiene**: All data files must be listed in `data/manifest.json` with SHA256 checksums.