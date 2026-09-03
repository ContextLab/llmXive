# Data Model: llmXive follow-up

## Overview

This document defines the schema and relationships for the synthetic dataset and experiment results. All data is stored in JSON (raw) and CSV/JSON (results) formats to ensure portability and ease of processing in the CI environment.

## Entities

### 1. Task
A synthetic multi-step problem requiring a sequence of skills to solve.

| Field | Type | Description |
| :--- | :--- | :--- |
| `task_id` | `string` | Unique identifier (e.g., "task_001"). |
| `description` | `string` | Natural language description of the problem. |
| `ground_truth_skills` | `array[string]` | List of skill IDs required to solve the task (deterministic). |
| `complexity` | `integer` | Number of steps (3-5). |
| `embedding_vector` | `array[float]` | 384-dim vector (from `all-MiniLM-L6-v2`). |

### 2. Skill
A Python function capability with metadata.

| Field | Type | Description |
| :--- | :--- | :--- |
| `skill_id` | `string` | Unique identifier (e.g., "skill_001"). |
| `code_snippet` | `string` | The Python function source code. |
| `embedding_vector` | `array[float]` | 384-dim vector. |
| `usage_count` | `integer` | Runtime counter (reset per experiment run). |
| `last_used_index` | `integer` | Index of the task where it was last used. |

### 3. ExperimentLog
Record of a single agent execution.

| Field | Type | Description |
| :--- | :--- | :--- |
| `run_id` | `string` | Unique run identifier. |
| `library_size` | `integer` | Size of the active skill library (10, 20, ..., 100). |
| `overlap_level` | `string` | "low", "medium", or "high". |
| `pruning_enabled` | `boolean` | Whether pruning heuristic was active. |
| `task_id` | `string` | Reference to the task. |
| `success` | `boolean` | Whether the task was solved correctly. |
| `latency_ms` | `float` | Execution time. |
| `token_count` | `integer` | Tokens used. |
| `retrieval_precision` | `float` | Jaccard similarity (top-k vs ground truth). |
| `retrieval_diversity` | `float` | Inverse variance of similarity scores (against query). |
| `missing_skills` | `array[string]` | List of required skills not found (if failed). |

## Data Flow

1.  **Generation**: `generate_data.py` creates `tasks.json` and `skills.json` in `data/raw/`.
2.  **Execution**: `run_baseline.py` loads raw data, runs agent, appends to `experiment_log.csv` in `data/results/`.
3.  **Analysis**: `analyze.py` reads `experiment_log.csv`, computes aggregates, and writes `tipping_point.json` and `pruning_analysis.json`.