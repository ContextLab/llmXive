# Data Model: llmXive follow-up: extending "Achieving Gold-Medal-Level Olympiad Reasoning via Simple and Unified S"

## Overview

This document defines the data structures used throughout the pipeline, ensuring type safety and traceability from raw input to final statistical output.

## Entity Definitions

### 1. Prompt
Represents a single problem statement.
- `prompt_id`: Unique string identifier.
- `source`: Dataset name (e.g., "IMO", "OpenSci").
- `text`: The raw text of the problem.
- `ground_truth`: Optional string (for Olympiad). Null for OpenSci.
- `type`: "deterministic" or "ill-structured".

### 2. Response
Represents a model's output.
- `response_id`: Unique string identifier.
- `prompt_id`: Foreign key to Prompt.
- `model_name`: Name of the model (e.g., "SU-01", "Baseline").
- `text`: Generated text.
- `token_count`: Number of tokens generated.
- `truncated`: Boolean (True if `max_tokens` reached).
- `seed`: Random seed used.
- `temperature`: Temperature used.

### 3. Score
Represents the evaluation of a Response.
- `score_id`: Unique string identifier.
- `response_id`: Foreign key to Response.
- `novelty`: Integer 1-5.
- `feasibility`: Integer 1-5.
- `consistency`: Integer 1-5.
- `rationale`: String (raw text from proxy model).
- `confidence`: Float (1.0 - 0.0).
- `is_low_confidence`: Boolean (True if variance > 1.5 or entropy > 2.0).

### 4. BenchmarkResult
Aggregated metrics per model.
- `model_name`: String.
- `dataset`: String.
- `metric_name`: String (e.g., "accuracy", "mean_novelty").
- `value`: Float.
- `n_samples`: Integer.
- `p_value`: Float (optional).
- `confidence_interval`: Tuple (lower, upper).

## File Formats

### Input: `data/raw/imo.parquet`
Standard HuggingFace parquet format.

### Intermediate: `data/processed/inference_results.jsonl`
One JSON object per line.
```json
{
  "prompt_id": "IMO-001",
  "model_name": "SU-01",
  "response_id": "resp-001-su",
  "text": "...",
  "token_count": 512,
  "truncated": false
}
```

### Output: `data/processed/scores.jsonl`
```json
{
  "response_id": "resp-001-su",
  "novelty": 3,
  "feasibility": 4,
  "consistency": 5,
  "rationale": "The approach is standard but feasible.",
  "is_low_confidence": false
}
```

### Final: `data/processed/stats.json`
```json
{
  "correlation": {
    "coefficient": -0.45,
    "p_value": 0.001,
    "method": "point_biserial"
  },
  "t_test": {
    "t_stat": -2.34,
    "p_value": 0.02,
    "method": "paired_t"
  },
  "power_analysis": {
    "n": 100,
    "effect_size": 0.5,
    "power": 0.72
  }
}
```

## Validation Rules

- All `prompt_id`s must be unique across the dataset.
- `novelty`, `feasibility`, `consistency` must be integers in [1, 5].
- `truncated` must be boolean.
- `is_low_confidence` must be boolean.
- All timestamps in logs must be ISO 8601.
