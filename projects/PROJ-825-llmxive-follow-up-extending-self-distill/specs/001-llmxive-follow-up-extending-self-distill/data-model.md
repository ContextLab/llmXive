# Data Model: llmXive follow-up: extending "Self-Distilled Agentic Reinforcement Learning"

## Overview

This document defines the data structures used to represent training runs, gating signals, and metrics. All data is persisted in JSONL format for streaming efficiency and compatibility with statistical analysis tools.

## Entities

### 1. TrainingRun

Represents a single execution of the RL loop.

**Attributes**:
- `run_id`: Unique identifier (UUID).
- `variant`: "grpo", "baseline", or "student-only".
- `environment`: "alfworld" or "webshop".
- `seed`: Random seed used.
- `start_time`, `end_time`: ISO 8601 timestamps.
- `total_steps`: Number of training steps.
- `final_success_rate`: Average success rate over the run.
- `avg_cpu_time_per_step`: Mean CPU time in seconds.
- `peak_memory_mb`: Peak RSS memory in MB.
- `convergence_steps`: Steps to reach reward threshold 0.8 (or null).
- `early_stopped`: Boolean (True if run terminated due to threshold or step cap).

### 2. GatingSignal

Represents the computed gate value for a specific token.

**Attributes**:
- `step_id`: Integer step index.
- `token_id`: Integer token index.
- `token_text`: The actual token string.
- `entropy`: Float ($H_t$).
- `stability`: Float ($S_t$).
- `final_gate`: Float ($g_t$).
- `is_valid`: Boolean (True if no NaN/Inf).
- `paired_trajectory_id`: UUID (Links to the baseline trajectory if this is a replay).

### 3. EpisodeMetrics

Aggregated metrics per episode (for bootstrapping).

**Attributes**:
- `episode_id`: Integer.
- `cumulative_reward`: Float.
- `success`: Boolean (0 or 1).
- `steps`: Integer.
- `avg_gate`: Float (average $g_t$ for the episode).
- `avg_entropy`: Float.
- `avg_stability`: Float.
- `trajectory_id`: UUID (Unique ID for the trajectory, used for pairing).

### 4. ComparisonReport

Aggregated results for statistical analysis.

**Attributes**:
- `variant_grpo`: List of cumulative rewards (all episodes).
- `variant_baseline`: List of cumulative rewards (all episodes).
- `variant_student_only`: List of cumulative rewards (all episodes).
- `p_value`: Float from bootstrapping test.
- `effect_size`: Float (Cohen's d).
- `cost_reduction_pct`: Float (percentage reduction in CPU time).
- `performance_retention_pct`: Float (percentage of baseline performance retained).
- `correlation_coefficient`: Float (Pearson r between student heuristic and teacher gap on paired data).

## Data Flow

1.  **Input**: Configuration (JSON) + Environment State.
2.  **Processing**:
    - `student_only_agent.py` computes $H_t$ and $S_t$.
    - `cost_profiler.py` captures CPU/Memory.
    - Metrics are written to `data/processed/<run_id>.jsonl`.
    - **Paired Replay**: Baseline trajectories are saved. Student-Only agent replays them to generate paired gating signals.
3.  **Output**:
    - `data/processed/summary.json` (ComparisonReport).
    - `data/processed/correlation_analysis.csv` (Pearson correlation of heuristics).
    - `data/processed/episode_metrics.parquet` (For bootstrapping).

## Data Hygiene

- **Checksums**: All generated files in `data/processed/` are checksummed (SHA-256).
- **Immutability**: Raw logs are never modified. Derived statistics are written to new files.
- **PII**: No PII is expected. Token texts are from synthetic environments.