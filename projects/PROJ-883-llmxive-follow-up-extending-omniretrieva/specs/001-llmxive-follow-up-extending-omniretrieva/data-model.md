# Data Model: llmXive Follow-up: Structural Mismatch Cost in Heterogeneous Retrieval

## Overview

This document defines the data structures used for synthetic query generation, execution logging, and statistical analysis. All data is stored in `data/` (raw/processed) and `data/results/`. Artifact hashes for these files are tracked in `state/state.yaml` (Constitution Principle V).

## Entity Definitions

### 1. Query Instance
Represents a single synthetic retrieval request.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `query_id` | `str` | Unique UUID for the query. | Generated |
| `source_type` | `str` | One of: `text`, `relational`, `graph`. | Generated |
| `complexity_level` | `int` | Exact plan depth (1, 2, 3, 4+). | Generated |
| `logical_plan` | `list[str]` | Sequence of operations (e.g., `["join", "filter"]`). | Generated |
| `ground_truth_plan` | `list[str]` | Optimal plan from CBO (full lookahead). | Generated |
| `sut_plan` | `list[str]` | Plan from SUT (limited lookahead heuristic). | Generated |
| `parameters` | `dict` | Query-specific args (e.g., `{"tables": ["A", "B"]}`). | Generated |

### 2. Execution Metric
Represents the outcome of a single query run.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `query_id` | `str` | FK to Query Instance. | From Query |
| `latency_ms` | `float` | Wall-clock time in milliseconds. | Measured |
| `mismatch_flag` | `bool` | `True` if SUT selected a wrong source type. | Computed |
| `delta_latency` | `float` | `Latency_Mismatched - Latency_Optimal` (if mismatch). | Computed |
| `translation_error` | `bool` | `True` if `sut_plan` != `ground_truth_plan`. | Computed |
| `timeout_flag` | `bool` | `True` if execution > 60s. | Measured |
| `success_flag` | `bool` | `True` if `not timeout_flag` and no exception. | Computed |
| `timestamp` | `str` | ISO 8601 timestamp. | System |

### 3. Statistical Summary
Aggregated results for ANOVA and visualization.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `source_type` | `str` | Grouping variable. | Aggregated |
| `complexity_level` | `int` | Grouping variable. | Aggregated |
| `mean_delta_latency` | `float` | Average mismatch cost for group. | Calculated |
| `std_delta_latency` | `float` | Standard deviation. | Calculated |
| `n_samples` | `int` | Count of queries in group. | Calculated |
| `knee_point` | `float` | Identified complexity level of spike (from Segmented Regression). | Calculated |

## File Formats

### Raw Logs (JSONL)
Stored in `data/results/raw_logs.jsonl`.
```json
{"query_id": "uuid-1", "source_type": "graph", "complexity_level": 3, "latency_ms": 120.5, "mismatch_flag": true, "delta_latency": 45.2, "translation_error": true, "timeout_flag": false, "success_flag": true}
```

### Statistical Output (CSV)
Stored in `data/results/analysis_summary.csv`.
```csv
source_type,complexity_level,mean_delta_latency,std_delta_latency,n_samples,knee_point
graph,1,5.2,1.1,100,3.0
graph,2,12.4,2.5,100,3.0
graph,3,55.1,8.2,100,3.0
graph,4,120.5,15.0,100,3.0
```

## Data Flow

1. **Generation**: `synthetic_queries.py` creates `QueryInstance` objects -> Saved to `data/processed/queries.jsonl`.
2. **Execution**: `main.py` loops through queries -> Measures latency -> Saves `ExecutionMetric` to `data/results/raw_logs.jsonl`.
3. **Analysis**: `latency_analyzer.py` reads logs -> Computes aggregates and Segmented Regression -> Saves `StatisticalSummary` to `data/results/analysis_summary.csv`.
4. **State Tracking**: `state/state.yaml` is updated with checksums of all generated files (Constitution Principle V).
5. **Visualization**: `visualizer.py` reads CSV -> Generates `figures/latency_interaction.png`.

## State Tracking (Constitution Principle V)

The `state/state.yaml` file tracks artifact hashes to ensure reproducibility.
```yaml
artifacts:
  data/processed/queries.jsonl: <sha256_hash>
  data/results/raw_logs.jsonl: <sha256_hash>
  data/results/analysis_summary.csv: <sha256_hash>
  code/generators/synthetic_queries.py: <sha256_hash>
updated_at: "2026-07-10T12:00:00Z"
```