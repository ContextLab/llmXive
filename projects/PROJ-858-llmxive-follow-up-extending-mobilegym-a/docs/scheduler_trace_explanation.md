# Scheduler Trace Explanation

This document explains the structure, purpose, and usage of the `data/processed/scheduler_trace.json` file, which records the decision-making process of the State-Guided Curriculum Scheduler.

## Overview

The scheduler trace is a JSON Lines (or JSON array) file that logs every decision made by the `CurriculumScheduler` during training runs. It is essential for:
- **Reproducibility**: Understanding exactly why a specific task batch was selected.
- **Debugging**: Identifying why the scheduler might be stuck or selecting suboptimal tasks.
- **Analysis**: Post-hoc analysis of curriculum progression and coverage expansion.

## File Location

- **Path**: `data/processed/scheduler_trace.json`
- **Format**: JSON Array of objects (or JSONL depending on configuration).
- **Initialization**: The schema is initialized by `code/setup_scheduler_trace.py` (Task T011).

## Schema Definition

Each entry in the trace file corresponds to a single scheduler invocation and contains the following fields:

| Field Name | Type | Description |
|------------|------|-------------|
| `timestamp` | `string` (ISO 8601) | UTC time when the decision was made. |
| `run_id` | `string` | Unique identifier for the training run. |
| `phase` | `string` | The current curriculum phase (e.g., `low_coverage`, `moderate_success`, `entropy_fallback`). |
| `trigger_metrics` | `object` | The specific state variables and their values that triggered the selection logic. |
| `current_coverage_ratio` | `float` | The global state coverage ratio at the time of selection (0.0 - 1.0). |
| `target_range` | `object` | The target success rate range for the current phase (e.g., `{min: 0.1, max: 0.9}`). |
| `selected_tasks` | `array` | List of task parameters selected for the next batch. |
| `fallback_reason` | `string` (optional) | If a fallback was used, explains why (e.g., "No tasks in sweet spot"). |
| `entropy_score` | `float` (optional) | The calculated entropy of the current state distribution if entropy-based selection was used. |

### Example Entry

```json
{
 "timestamp": "2023-10-27T10:00:00Z",
 "run_id": "exp-001-state-guided",
 "phase": "moderate_success",
 "trigger_metrics": {
 "dark_mode": 0.45,
 "unread_count": 0.12,
 "scroll_depth": 0.60
 },
 "current_coverage_ratio": 0.35,
 "target_range": {
 "min": 0.3,
 "max": 0.7
 },
 "selected_tasks": [
 {"task_id": "mobilegym-task-102", "difficulty": "medium"},
 {"task_id": "mobilegym-task-105", "difficulty": "medium"}
 ],
 "fallback_reason": null,
 "entropy_score": 0.82
}
```

## Metrics Triggered

The `trigger_metrics` field is critical for the **State-Guided** aspect of the curriculum. It records the specific **Semantic State Proxies** (defined in `code/utils/constants.py` and read from `contracts/coverage.schema.yaml`) that influenced the scheduler.

- **Semantic Proxies**: Variables like `dark_mode`, `unread_count`, `scroll_depth`, etc.
- **Transition Values**: The value represents the proportion of the training population that has experienced this state (0.0 to 1.0).
- **Usage**: If `dark_mode` coverage is low, the scheduler might prioritize tasks that force dark mode interactions.

## Phase Logic

The trace records which phase logic was active:

1. **`low_coverage`**:
 - **Goal**: Target coverage < 5%.
 - **Logic**: Prioritize tasks that flip the most uncovered bits in the state vector.
 - **Trace Indicator**: `phase: "low_coverage"`, `target_range` may be null or irrelevant.

2. **`moderate_success`**:
 - **Goal**: Target success rate between 10% and 90% (dynamic expansion).
 - **Logic**: Select tasks where the agent's historical success rate falls within the "sweet spot".
 - **Trace Indicator**: `phase: "moderate_success"`, `target_range` shows current bounds.

3. **`entropy_fallback`**:
 - **Goal**: Maximize entropy when no tasks meet the specific phase criteria.
 - **Logic**: Random selection or maximum entropy sampling.
 - **Trace Indicator**: `phase: "entropy_fallback"`, `fallback_reason` is populated.

## How to Read the Trace

1. **Open the file**: `data/processed/scheduler_trace.json`
2. **Filter by `run_id`**: If multiple experiments were run, isolate the specific run.
3. **Check `phase` progression**: Verify that the scheduler moved from `low_coverage` to `moderate_success` as expected.
4. **Inspect `trigger_metrics`**: Correlate specific state variables with task selection. Did the scheduler correctly identify that `unread_count` was low and select a task to address it?
5. **Review `fallback_reason`**: If the scheduler frequently falls back, the curriculum might be too aggressive or the task pool insufficient.

## Implementation Details

- **Writer**: The trace is written by `code/scheduler/trace_logger.py` (Task T018).
- **Function**: `log_metrics_triggered` is called within the scheduler loop to append entries.
- **Atomicity**: Entries are appended atomically to prevent corruption in multi-process environments.

## References

- **Task**: T018 (Add logging for `metrics_triggered` to `data/processed/scheduler_trace.json`)
- **Schema**: `contracts/coverage.schema.yaml` (Source of semantic proxies)
- **Constants**: `code/utils/constants.py` (Definition of state variables)
- **Scheduler**: `code/scheduler/curriculum_scheduler.py`