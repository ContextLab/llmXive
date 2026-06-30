# Data Model: GateMem Benchmarking Memory Governance

## Overview

This document defines the data schemas for the GateMem benchmarking system. All data is stored in JSON/Parquet formats to ensure reproducibility and type safety. The model supports synthetic generation, execution logs, and aggregated metrics.

## Entities

### 1. Principal
A simulated user entity.
- `id`: Unique string identifier (e.g., "P1", "P2").
- `name`: Human-readable name (optional, for logging).

### 2. Memory Item
A discrete unit of information associated with a Principal.
- `id`: Unique string (e.g., "M_P1_001").
- `principal_id`: Reference to Principal.
- `content`: The text of the fact.
- `template_type`: Category of the fact (e.g., "profile", "preference").
- `position_seed`: Integer indicating the position rotation seed used.

### 3. Context Window
The aggregated sequence of memory items presented to the model.
- `run_id`: Unique identifier for the experimental run.
- `n_principals`: Number of principals ($N$).
- `seed`: Random seed used for generation.
- `items`: List of Memory Items (interleaved).
- `overflow_flag`: Boolean indicating if context limit was exceeded.

### 4. Task Log
The record of a single query-response interaction.
- `task_id`: Unique identifier.
- `run_id`: Reference to Context Window.
- `task_type`: Enum {`utility`, `access_control`, `suppression`}.
- `target_principal`: Principal ID the task targets.
- `target_fact_id`: The specific Fact ID involved.
- `prompt`: The exact prompt sent to the model.
- `response`: The model's raw response.
- `eval_pass`: Boolean (Pass/Fail) from rule-based evaluator.
- `eval_semantic_score`: Float (0.0 - 1.0) from semantic verification.
- `oracle_exists`: Boolean (True if fact exists in context).
- `oracle_leak`: Boolean (True if model revealed existing fact inappropriately).

### 5. Metrics Summary
Aggregated results for a specific $N$ and seed.
- `run_id`: Reference.
- `n_principals`: $N$.
- `utility_rate`: Float.
- `leak_rate`: Float.
- `suppression_rate`: Float.
- `governance_score`: Float.
- `lmm_p_value`: Float (from Linear Mixed-Effects Model).
- `lmm_effect_size`: Float (Cohen's d or similar).

## Data Flow

1. **Generation**: `data_gen.py` creates `generated/memories_N{N}_seed{S}.json`.
2. **Execution**: `runner.py` consumes memories, generates `results/logs_N{N}_seed{S}.jsonl`.
3. **Analysis**: `metrics.py` aggregates logs into `results/metrics_summary.csv`.

## Validation Rules

- **Uniqueness**: All `id` fields must be unique within their scope.
- **Referential Integrity**: `principal_id` in Memory Item must exist in Principal list.
- **Range**: `eval_semantic_score` must be in [0.0, 1.0].
- **Enum**: `task_type` must be one of {`utility`, `access_control`, `suppression`}.