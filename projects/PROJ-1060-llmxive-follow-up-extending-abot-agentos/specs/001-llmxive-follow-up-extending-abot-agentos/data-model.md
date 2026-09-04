# Data Model: llmXive follow-up: extending "ABot-AgentOS" with Symbolic Memory

## Overview

This document defines the data structures used for the symbolic memory system, the task traces, and the experimental results. All data is serialized in JSON/CSV formats for portability and reproducibility.

## Entity Definitions

### 1. Task Trace
Represents a single navigation task from the ALFWorld benchmark.
- **Fields**:
  - `trace_id`: Unique identifier (string).
  - `dialogue`: List of dialogue turns (list of strings).
  - `spatial_coords`: List of (x, y, z) tuples (list of lists of floats). **[OPTIONAL]**
  - `temporal_seq`: List of timestamps or step indices (list of integers). **[OPTIONAL]**
  - `outcome`: Binary success flag (0 or 1).
  - `ground_truth_path`: List of nodes representing the correct path (list of strings).

> **Note**: `spatial_coords` and `temporal_seq` are marked as **optional** to support the "Dynamic Design Pruning" protocol. If these fields are missing, the study proceeds with the 'spatial-only' condition, and the schema validation will not fail.

### 2. Semantic Token
A discrete identifier for a visual or spatial state.
- **Fields**:
  - `token_id`: Unique string (e.g., "red_cup_kitchen_counter").
  - `taxonomy_level`: "coarse" or "fine".
  - `confidence`: Float (0.0-1.0) from the frozen VLM mapping.
  - `raw_observation`: Hash of the original visual data (string).

### 3. Symbolic Graph (DAG)
The core memory structure.
- **Nodes**: `SemanticToken` objects.
- **Edges**: Logical predicates connecting nodes.
  - `source_node`: ID of the source token.
  - `target_node`: ID of the target token.
  - `predicate`: String (e.g., `on_top_of`, `near`, `before`).
  - `timestamp`: Time of the relationship (optional).

### 4. Query Result
Output of the depth-first traversal.
- **Fields**:
  - `query_id`: Unique identifier.
  - `query_string`: Original user query.
  - `path_found`: Boolean.
  - `result_path`: List of nodes if found (list of strings).
  - `latency_ms`: Execution time.
  - `memory_peak_mb`: Peak RAM usage during execution.

### 5. Experiment Metric
Aggregated results for a specific configuration.
- **Fields**:
  - `config_id`: Unique identifier for the sweep (granularity, predicates).
  - `success_rate`: Float (0.0-1.0).
  - `latency_mean_ms`: Float.
  - `latency_std_ms`: Float.
  - `memory_peak_mb`: Float.
  - `glmm_fixed_effects`: Dictionary of fixed effect coefficients (e.g., `architecture_symbolic`, `granularity_fine`).
  - `glmm_random_effects_variance`: Variance of the task-level random effect.
  - `p_value_architecture`: P-value for the architecture effect.
  - `error_counts`: Dictionary {"discretization_ambiguity": int, "logical_inference": int}.

## Data Flow

1.  **Ingestion**: `Task Trace` (Raw) → `Data Loader` → `Processed Trace` (JSON).
2.  **Construction**: `Processed Trace` + `Frozen VLM` → `Semantic Token` → `Symbolic Graph` (GraphML/JSON).
3.  **Execution**: `Symbolic Graph` + `Query` → `Query Result`.
4.  **Analysis**: `Query Result` + `Baseline Result` → `Experiment Metric`.

## Storage Strategy

-   **Raw Data**: `data/raw/` (ALFWorld or versioned fallback).
-   **Processed Graphs**: `data/processed/graphs/{config_id}/graph.json`.
-   **Results**: `data/results/metrics.csv`, `data/results/errors.json`, `data/results/run_config.json`.
-   **Logs**: `logs/construction.log`, `logs/query.log`.