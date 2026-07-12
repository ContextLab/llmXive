# Data Model: 001-tutorial-bias-analysis

## Overview

This document defines the data structures used in the benchmark generation, evaluation, and analysis phases. All data is stored in JSON/JSONL format within the `data/` directory.

## Entities

### 1. BenchmarkTask
Represents a single synthetic GUI task.
- **ID**: Unique string identifier.
- **Type**: `linear` or `non-linear`.
- **Goal**: String description of the target state.
- **InitialState**: JSON object describing the initial GUI state.
- **ErrorInjection**: (Optional) Object describing the error to inject (e.g., `{"type": "modal", "trigger": "submit"}`).
- **RecoveryPath**: List of actions required to recover from the error.
- **TaxonomyReference**: Link to the error taxonomy source (FR-008).

### 2. TrajectoryLog
Records the execution of an agent on a task.
- **TaskID**: Reference to `BenchmarkTask`.
- **AgentVariant**: `baseline`, `wildgui`, or `hybrid`.
- **Steps**: List of step objects (state, action, result).
- **Outcome**: `success`, `failure`, `timeout`, `simulation_error`.
- **StepCount**: Integer (max 50).
- **Timestamp**: ISO 8601 string.

### 3. AnalysisResult
Aggregated statistical results.
- **Metric**: Name of the metric (e.g., `success_rate_non_linear`).
- **Value**: Float.
- **Agent**: Agent variant.
- **ConfidenceInterval**: [lower, upper].
- **PValue**: Float (from McNemar's test).
- **DiscordantPairs**: Object `{b: int, c: int}`.
- **Power**: Float.

## Data Flow

1.  **Generation**: `benchmark_generator.py` reads `config.py` and outputs `data/benchmarks/tasks.jsonl` (500 lines).
2.  **Evaluation**: `runner.py` reads tasks and outputs `data/results/trajectories.jsonl` (one per agent-task pair).
3.  **Analysis**: `stats.py` reads trajectories and outputs `data/results/stats.json`.

## Schema References

Detailed schemas for `BenchmarkTask` and `TrajectoryLog` are defined in `contracts/`.
