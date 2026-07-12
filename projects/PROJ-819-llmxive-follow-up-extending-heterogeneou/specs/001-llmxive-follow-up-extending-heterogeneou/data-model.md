# Data Model: llmXive follow-up: extending "Heterogeneous Scientific Foundation Model Collaboration"

## Overview

This document defines the data structures and schemas used to represent the entities, cache state, and execution results for the semantic caching study. All data is stored in JSON/CSV formats within the `data/` directory to ensure reproducibility and portability.

## Core Entities

### 1. BenchmarkQuery
Represents a single iterative sub-task from the "Eywa" benchmark (or synthetic generator).

| Field | Type | Description |
|-------|------|-------------|
| `query_id` | string | Unique identifier (UUID). |
| `prompt` | string | The input text for the scientific hypothesis test. |
| `domain` | string | Scientific domain (e.g., "chemistry", "physics"). |
| `expected_output` | float | The ground-truth numerical outcome. |
| `metadata` | object | Additional context (e.g., step number in iteration). |

### 2. CacheEntry
Represents a stored result in the semantic cache.

| Field | Type | Description |
|-------|------|-------------|
| `prompt_embedding` | list[float] | A fixed-dimensional vector from `all-MiniLM-L6-v2`. |
| `output` | float | The cached result from EywaOrchestra. |
| `timestamp` | float | Unix timestamp of insertion. |
| `access_count` | int | Number of times this entry has been retrieved (for LRU). |

### 3. ExecutionRun
Aggregates metrics for a single execution of the pipeline (Baseline or Cached).

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | Unique identifier for the run. |
| `mode` | string | "baseline" or "cached". |
| `threshold` | float | The similarity threshold used (0.0 for baseline). |
| `total_queries` | int | Total number of queries processed. |
| `cache_hits` | int | Number of cache hits. |
| `cache_misses` | int | Number of cache misses. |
| `hit_rate` | float | `cache_hits / total_queries`. |
| `total_runtime_seconds` | float | Wall-clock time for the run. |
| `model_invocations` | int | Number of times EywaOrchestra was called. |
| `accuracy` | float | Percentage of correct predictions against ground truth. |
| `accuracy_deviation` | float | `abs(cached_accuracy - baseline_accuracy)`. |
| `similarity_scores` | list[float] | **Mandatory for cached runs**: List of cosine similarity scores for every query in the run (null/empty for baseline). This field is required to satisfy Constitution Principle VI (Semantic Cache Validity) by storing the exact score for audit. |

## File Formats

### `data/derived/queries.json`
A JSON array of `BenchmarkQuery` objects.
```json
[
  {
    "query_id": "uuid-1",
    "prompt": "Calculate the energy of a photon with wavelength 500nm.",
    "domain": "physics",
    "expected_output": 3.97e-19,
    "metadata": { "step": 1 }
  }
]
```

### `data/derived/results.csv`
A CSV file containing one row per `ExecutionRun` for the sensitivity analysis.
*Note: The `similarity_scores` field is stored as a JSON string within the CSV cell.*
```csv
run_id,mode,threshold,hit_rate,total_runtime_seconds,model_invocations,accuracy,accuracy_deviation,similarity_scores
run-baseline,0.00,0.00,120.5,500,98.2,0.0,"[]"
run-cached,0.95,0.60,48.1,200,98.0,0.2,"[0.91, 0.95, 0.96, ...]"
run-cached,0.99,0.30,90.5,350,98.2,0.0,"[0.91, 0.99, 0.88, ...]"
```

### `reports/statistical_significance.json`
A JSON file containing the results of the Permutation Test and Linear Regression.
*Schema defined in `contracts/statistical_significance.schema.yaml`.*

## Data Flow

1.  **Generation**: `code/data/generator.py` produces `data/derived/queries.json`.
2.  **Baseline Run**: `code/pipeline/runner.py` (mode=baseline) processes queries, logs metrics to `data/derived/results.csv`.
3.  **Cached Runs**: `code/pipeline/runner.py` (mode=cached, threshold=X) processes queries, logs metrics to `data/derived/results.csv`.
4.  **Analysis**: `code/analysis/metrics.py` reads `results.csv` to compute final statistics and generate plots.
5.  **Reporting**: `code/analysis/stats.py` generates `reports/statistical_significance.json`.