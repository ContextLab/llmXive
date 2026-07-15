# Data Model: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

## Overview

This document defines the data structures used throughout the project, ensuring consistency between data loading, processing, and analysis. All data is stored in `data/` with raw data preserved and processed data derived.

## Input Data

### 1. Task
A single reasoning query from the LoCoMo benchmark.
- **Attributes**:
  - `task_id`: Unique identifier (string).
  - `question`: The query string.
  - `context`: The supporting text/context.
  - `ground_truth`: The expected answer.
  - `source`: "LoCoMo".

### 2. Graph
A directed graph representing the memory structure for a task.
- **Attributes**:
  - `task_id`: Foreign key to Task.
  - `nodes`: List of node objects (fact, id).
  - `edges`: List of edge objects (source_id, target_id, confidence).
  - `noise_level`: Float (0.0 to 1.0) indicating proportion of injected noise.
  - `seed`: Integer random seed used for generation.
  - `construction_method`: String (e.g., "NER+RuleBased").

### 3. Execution Log
Record of a single task execution under a specific strategy.
- **Attributes**:
  - `task_id`: Foreign key to Task.
  - `strategy`: Enum { "Full", "Lazy", "Greedy" }.
  - `accuracy`: Float (0.0–1.0).
  - `nodes_visited`: Integer.
  - `latency_seconds`: Float.
  - `status`: Enum { "success", "timeout", "unresolved", "error" }.
  - `evidence_threshold`: Float (only for "Lazy").
  - `top_k`: Integer (only for "Greedy").
  - `timestamp`: ISO8601 timestamp.

### 4. Statistical Result
Aggregated metrics and test statistics.
- **Attributes**:
  - `comparison`: String (e.g., "Lazy vs Full").
  - `p_value`: Float.
  - `test_statistic`: Float.
  - `correlation_coefficient`: Float (Point-Biserial).
  - `inflection_point`: Integer (nodes_visited) or null.
  - `threshold_found`: Boolean.
  - `m_des`: Float (Minimum Detectable Effect Size).

## File Formats

### Input Data
- **LoCoMo CSV**: `data/raw/locomo.csv`
  - Columns: `task_id`, `question`, `context`, `ground_truth`.

### Processed Data
- **Graphs**: `data/processed/graphs/{task_id}_{strategy}_{noise}.json`
  - JSON format containing nodes and edges.
- **Results**: `data/processed/results/{strategy}_results.csv`
  - CSV format with columns: `task_id`, `strategy`, `accuracy`, `nodes_visited`, `latency_seconds`, `status`, `evidence_threshold`, `top_k`, `timestamp`.
- **Analysis**: `data/processed/analysis/stats.json`
  - JSON format containing statistical test results.

## Data Flow

1. **Download**: `data_loader.py` fetches `locomo.csv` from HuggingFace.
2. **Graph Generation**: `graph_utils.py` generates synthetic graphs with noise injection (distractor edges), saving to `data/processed/graphs/`.
3. **Execution**: `runner.py` runs strategies, logging results to `data/processed/results/`.
4. **Analysis**: `analysis.py` reads results CSVs, computes statistics, and saves to `data/processed/analysis/`.

## Validation Rules

- **Task**: `question` and `ground_truth` must not be empty.
- **Graph**: Must be a valid directed graph (no self-loops unless specified).
- **Execution Log**: `accuracy` must be in [0.0, 1.0]. `nodes_visited` must be >= 0.
- **Timeout**: If `status` == "timeout", `accuracy` is recorded as 0.0 or null (depending on implementation), and `latency` is capped at 1800.