# Data Model: llmXive follow-up: extending "AdaPlanBench: Evaluating Adaptive Planning in Large Language Model Age"

## 1. Overview

This document defines the data schemas for the project. All data artifacts are stored in `data/processed/` and must conform to these schemas. The data model supports the Dual-Track architecture, logging, and statistical analysis.

## 2. Entity Definitions

### 2.1 Task Instance
A single household task from the filtered AdaPlanBench dataset.
- **ID**: Unique identifier (string).
- **Prompt**: The initial task description.
- **Constraints**: List of constraints (strings) revealed progressively (time-ordered).
- **Constraint Count**: Integer (≥5).
- **Ground Truth**: The reference solution.

### 2.2 Execution Trace
A record of the agent's attempt to solve a task.
- **Task ID**: Reference to Task Instance.
- **Architecture**: "dual_track" or "monolithic".
- **Seed ID**: The random seed used for generation.
- **Steps**: List of generated steps.
- **Initial Violation**: Binary (0/1) indicating if the *raw* output violated a constraint (evaluated by Independent Oracle).
- **Final Adherence**: Binary (0/1) indicating if the *final* output (post-correction) adhered to constraints.
- **Resolution Status**: "passed", "failed", "unverified", "implicit_unverified", "parsing_failure".
- **Resource Logs**: CPU/RAM usage during execution.

### 2.3 Human Annotation
Manual validation of a subset of execution traces.
- **Task ID**: Reference to Task Instance.
- **Annotation ID**: Unique ID.
- **Human Verdict**: "violation", "no_violation", "ambiguous".
- **Notes**: Free text explanation.

## 3. File Schemas

### 3.1 `data/processed/filtered_tasks.csv`
The filtered subset of AdaPlanBench tasks (≥5 constraints).

| Column | Type | Description |
| :--- | :--- | :--- |
| `task_id` | string | Unique task identifier. |
| `prompt` | string | The initial task prompt. |
| `constraints` | string | JSON-encoded list of constraints (time-ordered). |
| `constraint_count` | int | Number of constraints (≥5). |
| `ground_truth` | string | Reference solution. |

### 3.2 `data/processed/execution_logs.csv`
The primary output of the agent execution.

| Column | Type | Description |
| :--- | :--- | :--- |
| `log_id` | string | Unique log identifier. |
| `task_id` | string | Reference to `filtered_tasks`. |
| `architecture` | string | "dual_track" or "monolithic". |
| `seed_id` | int | Random seed used for generation. |
| `step_index` | int | Step number in the plan. |
| `action` | string | The generated action. |
| `initial_violation` | bool | True if Independent Oracle detected a violation in raw output. |
| `final_adherence` | bool | True if final output (post-correction) adhered to constraints. |
| `resolution_type` | string | "none", "forced_revision", "accepted". |
| `status` | string | "passed", "failed", "implicit_unverified", "parsing_failure". |
| `cpu_usage` | float | CPU usage % during step. |
| `memory_mb` | float | Memory usage in MB during step. |

### 3.3 `data/processed/human_annotations.csv`
Human validation data.

| Column | Type | Description |
| :--- | :--- | :--- |
| `annotation_id` | string | Unique annotation ID. |
| `log_id` | string | Reference to `execution_logs`. |
| `human_verdict` | string | "violation", "no_violation", "ambiguous". |
| `notes` | string | Optional notes. |

### 3.4 `data/processed/distribution_summary.json`
Descriptive statistics for the filtered dataset.

| Field | Type | Description |
| :--- | :--- | :--- |
| `total_tasks` | int | Total number of tasks in the filtered subset. |
| `constraint_count_distribution` | object | Map of constraint counts to task frequencies. |
| `min_count` | int | Minimum constraint count. |
| `max_count` | int | Maximum constraint count. |

## 4. Data Flow

1. **Ingestion**: `code/dataset/loader.py` fetches raw data -> filters for `constraint_count >= 5` -> writes `filtered_tasks.csv` and `distribution_summary.json`.
2. **Execution**: `code/main.py` runs agents -> writes `execution_logs.csv`.
3. **Annotation**: `code/dataset/annotator.py` (stratified sampling) -> writes `human_annotations.csv`.
4. **Analysis**: `code/analysis/glmm.py` reads `execution_logs.csv` -> outputs statistical results.