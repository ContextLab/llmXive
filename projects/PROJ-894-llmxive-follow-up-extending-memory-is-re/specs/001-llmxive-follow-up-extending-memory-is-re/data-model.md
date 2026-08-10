# Data Model: llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

## Overview

This document defines the data structures used for input (LoCoMo tasks, graphs), intermediate processing (noisy graphs), and output (results CSVs, statistical reports).

## Entities

### 1. Task (Input)
Represents a single reasoning query from the LoCoMo benchmark.
- `task_id`: Unique identifier (string).
- `question`: The query string.
- `context`: The text context from which the graph is derived.
- `ground_truth`: The expected answer (fixed label).
- `source_url`: Reference to the dataset source.

### 2. Memory Graph (Intermediate)
A directed graph representing the agent's knowledge.
- `nodes`: List of node objects (id, text, metadata).
- `edges`: List of edge objects (source_id, target_id, weight/confidence).
- `is_noisy`: Boolean flag indicating if noise was injected.
- `noise_seed`: Integer seed used for reproducibility.

### 3. Execution Log (Output)
Record of a single task execution.
- `task_id`: String.
- `strategy`: Enum ("Full", "Lazy", "Greedy").
- `accuracy`: Float (0.0 - 1.0).
- `nodes_visited`: Integer.
- `latency_ms`: Float.
- `token_count`: Integer (Primary metric per Constitution VI).
- `status`: Enum ("completed", "timeout", "degenerate", "unresolved", "error").
- `evidence_threshold`: Float (only for Lazy, e.g., 0.7).
- `noise_applied`: Boolean.

### 4. Statistical Report (Output)
Summary of the analysis.
- `comparison_type`: String (e.g., "Lazy vs Full").
- `test_statistic`: Float (t, W, or McNemar's chi-square).
- `p_value`: Float.
- `correlation_coefficient`: Float (Point-Biserial).
- `inflection_point`: Integer (nodes_visited count where accuracy drops) or null.
- `sample_size`: Integer.
- `covariates`: List of strings (e.g., "critical_path_length").

## Data Flow

1. **Download**: `data_loader.py` fetches LoCoMo JSONL -> `data/raw/locomo.jsonl`.
2. **Graph Construction**: `graph_utils.py` parses context -> `data/processed/graphs/graph_clean.json`.
3. **Noise Injection**: `graph_utils.py` **replaces** edges -> `data/processed/graphs/graph_noise_42.json`.
4. **Execution**: `runner.py` processes tasks -> `data/processed/results/baseline_results.csv`, `lazy_results.csv`, etc.
5. **Analysis**: `stats.py` ingests CSVs -> `data/processed/results/statistical_report.json`.

## Constraints

- **Seeds**: All random operations (noise injection, sampling) must use a fixed seed (default 42) defined in `code/utils.py`.
- **Immutability**: Raw data is never modified. Derived data is written to new files.
- **Validation**: All JSON/CSV outputs must conform to the schemas in `contracts/`.
