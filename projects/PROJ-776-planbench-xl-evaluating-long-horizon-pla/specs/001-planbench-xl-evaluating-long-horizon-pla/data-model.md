# Data Model: PlanBench-XL Reproduction

## 1. Overview
This document defines the data structures for the reproduction pipeline, focusing on the input configurations, execution logs, and output metrics required to satisfy the Functional Requirements (FR-001 to FR-007).

## 2. Input Data

### 2.1 Task Configuration (YAML)
Used by `run_retail_batch.py` to define the run parameters.
- **Source**: `external/PlanBench-XL/configs/`
- **Schema**:
  - `model_id`: string (e.g., "gpt-5.4-mini"). **Note**: While the schema allows any string, the *plan* restricts usage to `gpt-5.4-mini` due to CI constraints. Models like `llama3.3-70b` are excluded.
  - `task_count`: integer (default: 5 for this plan)
  - `condition`: enum [default, blocker, noise]
  - `noise_ratio`: float (optional, for noise condition)
  - `timeout_per_tool`: integer (default: 60)
  - `timeout_per_task`: integer (default: 300)

### 2.2 Task Data (JSON)
- **Source**: `external/PlanBench-XL/data/tasks.json`
- **Structure**: Array of task objects.
  - `task_id`: string (unique identifier)
  - `goal`: string (natural language query)
  - `required_tools`: array of strings (tool names)

### 2.3 Tool Definitions (JSON)
- **Source**: `external/PlanBench-XL/data/database.json`
- **Structure**: Dictionary of tool definitions.
  - `tool_name`: string
  - `description`: string (modified by blocker/noise conditions)
  - `parameters`: object (schema for tool arguments)

## 3. Execution Logs

### 3.1 Execution Log (Per Task)
- **File**: `results/{run_id}/task_logs/{task_id}.json`
- **Schema**:
  - `task_id`: string
  - `model_id`: string
  - `condition`: string
  - `start_time`: ISO8601 timestamp
  - `end_time`: ISO8601 timestamp
  - `status`: enum [success, failed, timeout, error]
  - `steps`: array of step objects
    - `step_id`: integer
    - `action`: string (e.g., "call_tool")
    - `tool_name`: string
    - `args`: object
    - `response`: string (or error message)
    - `duration_ms`: integer
  - `error_message`: string (if failed)

## 4. Output Metrics

### 4.1 Evaluation Results (Aggregated)
- **File**: `results/{run_id}/eval_results.json`
- **Schema**:
  - `run_id`: string
  - `model_id`: string
  - `condition`: string
  - `total_tasks`: integer
  - `successful_tasks`: integer
  - `accuracy`: float (0.0 - 1.0)
  - `avg_duration_sec`: float
  - `timeout_rate`: float
  - `errors`: object (count of errors by type)

### 4.2 Reproduction Report (Markdown)
- **File**: `results/reproduction_report.md`
- **Content**:
  - Summary table of accuracy across models/conditions.
  - Discrepancy analysis section.
  - Methodological notes (including underpowered status).

## 5. Data Flow
1. **Config Load**: YAML config -> `run_retail_batch.py`.
2. **Task Load**: `tasks.json` -> Filtered by `task_count`.
3. **Execution**: Loop over tasks -> Call API/Tools -> Log to `task_logs/`.
4. **Aggregation**: `task_logs/` -> `eval_results.json`.
5. **Reporting**: `eval_results.json` + Paper Baselines -> `reproduction_report.md`.