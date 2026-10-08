# Data Model: llmXive Follow-up: Structural Mismatch Cost in Heterogeneous Retrieval

## Overview

This document defines the data structures for the benchmarking pipeline. All data is stored in local files under `data/`. The model ensures strict adherence to FR-002 (integer depth persistence) and FR-003 (JSON/CSV logging).

## Entities

### 1. Query Instance (Intermediate SSoT)
Represents a single synthetic query generated for the benchmark.
- `query_id`: UUID (unique identifier).
- `logical_plan`: List of steps (e.g., `[{"op": "lookup", "arg": "X"}, {"op": "join", "arg": "Y"}]`).
- `source_type`: Enum (`text`, `relational`, `graph`).
- `complexity_level`: Integer (1, 2, 3, 4+). **Critical**: Must be persisted as an integer.
- `ground_truth_plan`: JSON string of the optimal path (from `ground_truth_engine.py`).
- `synthetic_flag`: Boolean (True if generated from synthetic topology fallback).

### 2. Execution Metric (Final SSoT)
Represents the outcome of a single query execution.
- `query_id`: UUID (foreign key to Query Instance).
- `latency_ms`: Float (milliseconds). **Strictly real execution time.**
- `translation_error`: Boolean (True if generated plan != ground truth).
- `timeout_flag`: Boolean (True if >60s).
- `success_flag`: Boolean (1 if success, 0 otherwise).
- `timestamp`: ISO8601 string.
- `throttling_mode`: String (`cgroups`, `time_only`, `failed`).
- `synthetic_flag`: Boolean (inherited from Query Instance).

### 3. Statistical Result
Aggregated results from the analysis.
- `test_type`: String (`ancova`, `tukey`, `sensitivity`).
- `parameters`: JSON (e.g., `{"cutoff": 3}`).
- `statistics`: JSON (e.g., `{"F": 12.5, "p": 0.001}`).
- `interpretation`: String (e.g., "Interaction significant").

## File Formats

### `data/processed/generation_log.json` (Intermediate SSoT)
**Purpose**: Stores query definitions and ground truth plans before execution.
**Schema**: Validated by `contracts/generation_log.schema.yaml`.
**Structure**: Array of Query Instances.

### `data/processed/execution_logs.csv` (Final SSoT)
**Purpose**: Single source of truth for all latency and error metrics.
**Columns**:
- `query_id` (string)
- `source_type` (string)
- `complexity_level` (integer) **FR-002 Compliance**
- `latency_ms` (float)
- `translation_error` (integer 0/1)
- `success_flag` (integer 0/1)
- `synthetic_flag` (integer 0/1)
- `throttling_mode` (string)

*Note: `complexity_level` is explicitly typed as integer to satisfy FR-002. This file is written by `benchmark_runner.py` (T021).*

### `data/results/anova_results.json`
**Purpose**: Output of the ANCOVA test.
**Structure**:
```json
{
  "ancova": {
    "f_statistic": 12.34,
    "p_value": 0.0001,
    "interaction_p_value": 0.0045,
    "significant": true
  },
  "tukey": [
    {"group1": "graph_4", "group2": "text_4", "p_adj": 0.001},
    ...
  ]
}
```
*Written by `stats.py` (T018).*

### `data/results/sensitivity_analysis.json`
**Purpose**: Output of the threshold sweep (FR-007).
**Structure**:
```json
[
  {"cutoff": 2, "spike_point": 2.5, "slope_change": 15.2},
  {"cutoff": 3, "spike_point": 3.1, "slope_change": 18.4},
  {"cutoff": 4, "spike_point": 4.0, "slope_change": 22.1}
]
```
*Written by `stats.py` (T020).*

## Data Flow

1. **Generation**: `query_generator.py` creates Query Instances -> Writes `data/processed/generation_log.json`.
2. **Ground Truth**: `ground_truth_engine.py` reads generation log -> Writes `ground_truth_plan` to `generation_log.json`.
3. **Execution**: `benchmark_runner.py` reads `generation_log.json` -> Executes -> Writes `data/processed/execution_logs.csv` (T021).
4. **Analysis**: `stats.py` reads `execution_logs.csv` -> Computes stats -> Writes `data/results/anova_results.json` and `data/results/sensitivity_analysis.json` (T018, T020).

## Constraints

- No PII is stored.
- All files are checksummed.
- `complexity_level` must be an integer; any non-integer input is rejected by the generator.
- Synthetic fallbacks must be logged with `synthetic_flag=1`.
- **Primary Analysis**: Only queries with `synthetic_flag=0` are included in the ANCOVA.