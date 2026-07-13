# Data Model: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

## Overview

This document defines the data structures used throughout the pipeline. All data is stored in CSV or Parquet format for compatibility with `pandas` and `numpy`.

## Entities

### 1. Task
Represents a single reasoning query from the benchmark.
*   **Source**: LoCoMo CSV.
*   **Derivation**: Raw row mapped to `Task` object.

### 2. MemoryGraph
A directed graph representing the agent's reconstructed memory for a specific task.
*   **Source**: Constructed dynamically from Task Context.
*   **Derivation**: `graph_builder.py` extracts entities and relations.

### 3. ExecutionLog
The result of running a specific strategy on a specific task.
*   **Source**: `runner.py` output.
*   **Derivation**: Aggregated metrics from inference and traversal.

### 4. StatisticalReport
Aggregated results of hypothesis testing.
*   **Source**: `stats.py` output.
*   **Derivation**: Computed from `ExecutionLog` files.

## Schema Definitions

### Task Schema
| Field | Type | Description |
| :--- | :--- | :--- |
| `task_id` | string | Unique identifier from LoCoMo. |
| `question` | string | The multi-hop reasoning question. |
| `context` | string | The raw text context used to build the graph. |
| `ground_truth` | string | The correct answer (for accuracy calculation). |
| `split` | string | Train/Test split (if available). |

### ExecutionLog Schema
| Field | Type | Description |
| :--- | :--- | :--- |
| `task_id` | string | Reference to the task. |
| `strategy` | string | "Full", "Lazy", or "Greedy". |
| `accuracy` | float | 1.0 if answer matches ground truth, 0.0 otherwise. |
| `nodes_visited` | integer | Count of nodes traversed during reconstruction. |
| `edges_explored` | integer | Count of edges traversed. |
| `latency_seconds` | float | Total time taken for the task (inference + traversal). |
| `token_count` | integer | Total tokens generated/consumed. |
| `status` | string | "COMPLETED", "TIMEOUT", "ERROR", "DEGENERATE". |
| `error_message` | string | Optional error details if status != COMPLETED. |

### StatisticalReport Schema
| Field | Type | Description |
| :--- | :--- | :--- |
| `comparison` | string | e.g., "Lazy_vs_Full". |
| `test_type` | string | "t-test" or "wilcoxon". |
| `p_value` | float | Significance value. |
| `test_statistic` | float | t-statistic or W-statistic. |
| `correlation_coeff` | float | Pearson r for depth vs. accuracy. |
| `inflection_point` | integer | Nodes visited where accuracy < 95% baseline (or null). |
| `sample_size` | integer | Number of tasks in the comparison. |

## Data Flow

1.  **Ingestion**: `data_loader.py` reads LoCoMo CSV → `Task` objects.
2.  **Graph Construction**: `graph_builder.py` converts `Task` → `MemoryGraph`.
3.  **Execution**: `runner.py` iterates strategies → produces `ExecutionLog` rows (CSV).
4.  **Analysis**: `stats.py` reads `ExecutionLog` CSVs → produces `StatisticalReport` (JSON/CSV).
5.  **Reporting**: `report.py` aggregates `StatisticalReport` into final `results_summary.md`.
