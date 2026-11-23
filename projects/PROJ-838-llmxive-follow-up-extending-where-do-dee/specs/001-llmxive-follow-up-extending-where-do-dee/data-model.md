# Data Model: 001-gene-regulation

## Overview

This document defines the data structures used throughout the pipeline, from raw trajectory ingestion to final metric reporting. All data flows through the `code/` directory and is persisted in `data/processed/`.

## Raw Data Schema

### Source: TELBench Dataset
The raw data is a collection of JSON files (or a single large JSON/JSONL) containing agent trajectories.

| Field | Type | Description | Source |
| :--- | :--- | :--- | :--- |
| `trajectory_id` | string | Unique identifier for the trajectory. | TELBench |
| `spans` | list[object] | Ordered list of semantic spans in the trajectory. | TELBench |
| `spans[].text` | string | The text content of the span. | TELBench |
| `spans[].timestamp` | float | Timestamp of the span (optional). | TELBench |
| `spans[].type` | string | Type of span (e.g., "query", "response", "tool"). | TELBench |
| `label` | string | Final outcome: "success" or "failure". | TELBench |

## Intermediate Data: Graphs

### File: `data/processed/graphs/<trajectory_id>.json`
Serialized Claim-Dependency DAGs.

| Field | Type | Description |
| :--- | :--- | :--- |
| `trajectory_id` | string | Reference to the source trajectory. |
| `nodes` | list[object] | List of nodes in the DAG. |
| `nodes[].id` | string | Unique node ID (e.g., "span_0"). |
| `nodes[].text` | string | The text of the claim (first 100 chars). |
| `nodes[].index` | int | Original index in the trajectory spans list. |
| `edges` | list[tuple] | List of edges (source_id, target_id). |
| `metadata` | object | Cutoff depth used, node count, edge count. |

## Processed Data: Metrics

### File: `data/processed/metrics.csv`
Aggregated topological metrics for each trajectory.

| Column | Type | Description |
| :--- | :--- | :--- |
| `trajectory_id` | string | Unique ID. |
| `node_count` | int | Number of nodes in the early-stage graph. |
| `edge_count` | int | Number of edges in the early-stage graph. |
| `avg_branching_factor` | float | Sum of out-degrees / node_count. |
| `global_connectivity` | float | Edge_count / (node_count * (node_count - 1)). |
| `linear_reasoning_index` | float | Longest path length / node_count. |
| `label` | string | Ground truth label ("success"/"failure"). |
| `is_train` | bool | Whether this trajectory is in the training split. |

### File: `data/processed/train_metrics.csv`
Subset of `metrics.csv` where `is_train` is True.

### File: `data/processed/test_metrics.csv`
Subset of `metrics.csv` where `is_train` is False.

## Output Data: Evaluation

### File: `data/processed/evaluation_results.json`
Final performance metrics and threshold details.

| Field | Type | Description |
| :--- | :--- | :--- |
| `threshold_value` | float | The optimized threshold value used. |
| `threshold_percentile` | int | The percentile used (e.g., 10, 20, 30). |
| `precision` | float | Precision of the predictor. |
| `recall` | float | Recall of the predictor. |
| `f1_score` | float | F1-score of the predictor. |
| `confusion_matrix` | dict | `{"tp": int, "fp": int, "tn": int, "fn": int}` |
| `baseline_mean_connectivity_success` | float | Mean connectivity of the "success" class. |
| `correlation_coefficient` | float | Spearman/Pearson correlation between connectivity and collapse. |
| `p_value` | float | P-value for the correlation test. |
| `sensitivity_analysis` | list | Results for threshold sweeps (10, 20, 30 percentiles). |
| `linear_reasoning_analysis` | object | Results for linear reasoning index analysis. |

## Edge Cases

- **Short Trajectories**: If a trajectory has fewer spans than `int(len(spans) * config.cutoff_depth)`, the system uses the entire trajectory as the "early stage" rather than failing.
- **Zero-Edge Graphs**: If a graph has zero edges, `global_connectivity` and `avg_branching_factor` are defined as 0.0, not NaN.
- **Small Graphs**: If `node_count` < 5, the metric is flagged as 'unstable' in the `metrics.csv` (via a new `is_stable` column) and excluded from threshold derivation.
- **Malformed JSON**: If a trajectory file is malformed, the system logs a warning and skips that specific trajectory without crashing the entire batch process.

## Data Flow

1. **Download**: `downloader.py` fetches raw JSON to `data/raw/`.
2. **Parse**: `parser.py` reads raw JSON, extracts early spans, builds DAGs, saves to `data/processed/graphs/`.
3. **Metric**: `metrics.py` reads graphs, calculates metrics (including linear index), writes to `data/processed/metrics.csv`.
4. **Split**: `pipeline.py` splits `metrics.csv` into `train_metrics.csv` and `test_metrics.csv`.
5. **Evaluate**: `evaluator.py` reads train/test splits, calculates threshold (optimized), predicts, and writes `evaluation_results.json`.