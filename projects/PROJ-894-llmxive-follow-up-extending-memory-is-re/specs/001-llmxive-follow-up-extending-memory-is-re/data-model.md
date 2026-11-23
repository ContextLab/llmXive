# Data Model: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

## Overview

This document defines the data structures used for the benchmark execution, including the input graph representation, execution logs, and statistical outputs. All data is stored in JSON/CSV formats with strict schema validation.

## Entities

### 1. Task
A single reasoning query.
- `task_id`: Unique identifier (string).
- `question`: The multi-hop question (string).
- `context`: The text context from which the graph is derived (string).
- `ground_truth`: The expected answer (string).

### 2. Graph Node
A fact or sentence within the memory graph.
- `node_id`: Unique identifier (string).
- `content`: The text content of the fact (string).
- `vector_embedding`: Optional dense vector (array of floats) if semantic similarity is used.

### 3. Graph Edge
A relationship between nodes.
- `source_id`: Source node ID (string).
- `target_id`: Target node ID (string).
- `weight`: Confidence score or similarity metric (float).
- `type`: Relationship type (string, e.g., "logical", "semantic").

### 4. Execution Log
A record of a single task execution.
- `task_id`: ID of the task (string).
- `strategy`: "Full", "Lazy", or "Greedy" (string).
- `nodes_visited`: Count of nodes traversed (integer).
- `accuracy`: 1.0 if correct, 0.0 if incorrect (float).
- `latency_ms`: Total time in milliseconds (float).
- `status`: "completed", "timeout", "error", "invalid_graph" (string).
- `evidence_threshold`: Threshold used for Lazy strategy (float, nullable). **Must capture the exact value used in sensitivity sweeps.**
- `token_count`: Total tokens generated (integer). **Extracted from LLM response metadata.**
- `hard_cap_applied`: Boolean indicating if the hard cap on nodes visited was reached (boolean).
- `construction_model`: Name of the embedding model used for graph construction (string).
- `scoring_model`: Name of the embedding model used for edge scoring (string).
- `noise_applied`: Boolean indicating if noise was applied to the graph (boolean).

### 5. Statistical Summary
Aggregated results for a strategy.
- `strategy`: Strategy name (string).
- `n_tasks`: Number of tasks completed (integer).
- `mean_accuracy`: Average accuracy (float).
- `std_accuracy`: Standard deviation (float).
- `mean_nodes`: Average nodes visited (float).
- `p_value`: P-value from statistical test (float).
- `test_statistic`: T or W value (float).
- `correlation_coefficient`: Point-Biserial r (float).
- `inflection_point`: Nodes count where accuracy drops (integer, nullable).

## Data Flow

1. **Raw Data**: `data/raw/locomo.csv` (Downloaded).
2. **Intermediate**: `data/intermediate/graphs_raw.json` (Parsed graph structures - **Immutable**).
3. **Intermediate**: `data/intermediate/graph_validation_scores.json` (Edge coherence scores).
4. **Processed**:
   - `data/processed/baseline_results.csv` (Full strategy output).
   - `data/processed/lazy_results.csv` (Lazy strategy output).
   - `data/processed/greedy_results.csv` (Greedy strategy output).
   - `data/processed/noisy_graphs.json` (Synthetic noisy variants).
   - `data/processed/stats_clean.json` (Statistical analysis on clean data).
   - `data/processed/stats_noisy.json` (Statistical analysis on noisy data).

## Schema Validation

All generated CSVs and JSONs must conform to the schemas defined in `contracts/`, including `contracts/noisy_graphs.schema.yaml`.