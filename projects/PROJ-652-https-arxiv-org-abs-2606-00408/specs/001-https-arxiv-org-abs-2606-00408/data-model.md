# Data Model: Reproduce & Validate Observation Masking Regime Map

## Overview

This document defines the data structures used for the evaluation pipeline, trajectory logging, and regime map analysis. These models are derived directly from the "Key Entities" section of the specification and are designed to be validated against the `contracts/` YAML schemas. The `TrajectoryLog` schema serves as the definitive contract for the `masking.py` and `retry_utils` modules.

## Module Interfaces

### `masking.py`
- **Input**: `TrajectoryLog` (steps), `context_window_limit` (int).
- **Output**: Modified `TrajectoryLog` (steps with `masked` flag set, `tokens_saved` calculated, `turns_added` calculated).
- **Logic**: Identifies "stale" observations (redundant tool calls) and masks them. Calculates `tokens_saved` as the difference between unmasked and masked token counts for the step. Calculates `turns_added` if masking forces the agent to re-attempt a step.

### `retry_utils.py`
- **Input**: `api_request` (function), `max_retries` (int=3).
- **Output**: `api_response` or `RateLimitError`.
- **Logic**: Implements exponential backoff. Logs `rate_limit_event` to `TrajectoryLog` if a retry occurs.

## Entity Definitions

### 1. EvaluationRun
Represents a single execution of the agent on a subset of tasks.
- **Purpose**: Aggregates configuration and summary results for a specific run (e.g., "Masked-Run-Phi-2").
- **Key Fields**:
  - `run_id`: Unique identifier (UUID).
  - `timestamp`: ISO 8601 string.
  - `config`: Nested object containing `masking_enabled`, `model_id`, `dataset_subset`, `sample_size`.
  - `summary`: Nested object containing `total_tasks`, `successful_tasks`, `accuracy`, `avg_tokens`, `avg_turns`.
  - `artifacts`: List of paths to generated logs and plots.
  - `rate_limit_events`: Count of rate limit events encountered during the run.
  - `truncation_events`: Count of context truncation events encountered during the run.

### 2. TrajectoryLog
A chronological record of a single agent's interaction history.
- **Purpose**: Provides granular data for mechanistic analysis (token-for-turn trade-off).
- **Key Fields**:
  - `task_id`: Reference to the specific task in the dataset.
  - `run_id`: Reference to the parent EvaluationRun.
  - `steps`: List of step objects.
    - `step_id`: Integer index.
    - `action`: String (e.g., "tool_call", "observation", "masking_event").
    - `content`: String (the text of the action/observation).
    - `masked`: Boolean (true if observation was masked).
    - `tokens_used`: Integer (cumulative or delta).
    - `rate_limit_event`: Boolean (true if a rate limit was hit at this step).
    - `truncation_event`: Boolean (true if context was truncated at this step).
  - `outcome`: String ("success", "failure", "timeout", "context_limit", "error").
  - `metrics`: Object with `total_tokens`, `total_turns`, `accuracy_score`, `tokens_saved`, `turns_added`.

### 3. RegimeDataPoint
Aggregates data for the regime map visualization.
- **Purpose**: Represents a single point on the "Model Capacity vs. Accuracy Gain" plot.
- **Key Fields**:
  - `model_capacity_proxy`: String (e.g., "TinyLlama-1.1B", "Phi-2-2.7B"). This is an independent variable (model ID), not derived from run parameters.
  - `model_parameter_count`: Float (e.g., 1.1, 2.7). Quantitative mapping of `model_capacity_proxy` for the x-axis.
  - `retriever_strength`: String (e.g., "strong", "weak").
  - `accuracy_baseline`: Float (0.0-1.0).
  - `accuracy_masked`: Float (0.0-1.0).
  - `accuracy_gain`: Float (calculated as `masked - baseline`).
  - `tokens_saved_avg`: Float.
  - `turns_added_avg`: Float.
- **Scope Note**: This entity is designed to capture the "Rising Limb" data points. It does not include a "Collapse" regime point, as that is outside the empirical scope of this study.

## Data Flow

1.  **Input**: `SWE-bench` dataset (parquet) -> `eval.py`.
2.  **Processing**: `eval.py` generates `TrajectoryLog` (JSON) for each task. The `masking.py` and `retry_utils` modules write to the `steps` array.
3.  **Aggregation**: `regime_analyzer.py` reads all `TrajectoryLog` files -> generates `EvaluationRun` summary -> computes `RegimeDataPoint`.
4.  **Output**: `EvaluationRun` JSON, `RegimeDataPoint` CSV/JSON, and visualization artifacts (PNG/PDF).

## Validation Strategy

All output artifacts must conform to the schemas defined in `contracts/`.
- `EvaluationRun` -> `evaluation-run.schema.yaml`
- `TrajectoryLog` -> `trajectory-log.schema.yaml`
- `RegimeDataPoint` -> `regime-data-point.schema.yaml`
