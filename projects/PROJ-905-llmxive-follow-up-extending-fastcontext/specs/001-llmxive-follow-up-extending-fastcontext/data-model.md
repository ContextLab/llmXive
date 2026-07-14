# Data Model: llmXive follow-up: extending "FastContext: Training Efficient Repository Explorer for Coding Agents"

## Overview
This document defines the data structures used to store, process, and analyze the results of the FastContext-Lite experiment. All data is stored in `data/` with strict versioning.

## Entities

### 1. Repository Metadata
Represents a single SWE-bench instance.
- `instance_id`: Unique identifier (string).
- `repo_name`: Repository path (string).
- `regularity_score`: Float (0.0–1.0).
- `stratum`: Enum {"Regular", "Irregular"}.
- `raw_data_path`: Relative path to the cloned repository.

### 2. Exploration Log
Record of a single run (Baseline or Lite) for a repository.
- `instance_id`: Foreign key to Repository Metadata.
- `engine_type`: Enum {"FastContext-Distilled-1.5B", "FastContext-Lite"}.
- `context_precision`: Float (0.0–1.0).
- `total_tokens`: Integer.
- `exploration_latency_ms`: Float.
- `run_timestamp`: ISO 8601 string.
- `seed`: Integer (for reproducibility).

### 3. Statistical Summary
Aggregated results per stratum.
- `stratum`: Enum {"Regular", "Irregular"}.
- `metric_name`: Enum {"precision", "tokens", "latency"}.
- `baseline_mean`: Float.
- `lite_mean`: Float.
- `delta_mean`: Float.
- `p_value`: Float.
- `significance`: Boolean.
- `test_method`: Enum {"t-test", "wilcoxon"} (indicates which test was used).

## File Formats

### `data/processed/regularity_scores.csv`
| instance_id | repo_name | regularity_score | stratum |
| :--- | :--- | :--- | :--- |
| `swe-bench-001` | `repo-A` | 0.85 | Regular |
| `swe-bench-002` | `repo-B` | 0.32 | Irregular |

### `data/results/exploration_logs.jsonl`
One JSON object per line.
```json
{
  "instance_id": "swe-bench-001",
  "engine_type": "FastContext-Lite",
  "context_precision": 0.92,
  "total_tokens": 1500,
  "exploration_latency_ms": 250.5,
  "run_timestamp": "2026-07-14T10:00:00Z",
  "seed": 42
}
```

### `data/results/statistical_summary.json`
```json
{
  "Regular": {
    "precision": { 
      "baseline_mean": 0.91, 
      "lite_mean": 0.90, 
      "delta": -0.01, 
      "p_value": 0.45, 
      "significance": false,
      "test_method": "t-test"
    }
  },
  "Irregular": {
    "precision": { 
      "baseline_mean": 0.88, 
      "lite_mean": 0.65, 
      "delta": -0.23, 
      "degradation_pct": 26.1 
    }
  }
}
```

## Data Flow
1.  **Ingestion**: SWE-bench Lite data downloaded to `data/raw/`.
2.  **Transformation**: `static_analysis.py` (using `networkx`) reads `data/raw/` and writes `data/processed/regularity_scores.csv`.
3.  **Execution**: `fastcontext_lite.py` and `baseline_runner.py` read `regularity_scores.csv` and write to `data/results/exploration_logs.jsonl`.
4.  **Analysis**: `analysis.py` reads `exploration_logs.jsonl` and writes `statistical_summary.json`.
5.  **Versioning**: `versioning.py` computes hashes and updates `state/`.