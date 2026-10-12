# Data Model: LLM Agent Efficiency vs. Reasoning Trade-off Analysis

## Overview
All data artifacts are stored under `data/` with explicit versioning and checksum tracking. Below are the primary schemas used for validation (see `contracts/`).

### 1. Execution Log (`execution_log.schema.yaml`)
| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Unique identifier from the τ^c‑Bench dataset. |
| `run_id` | string | UUID for this specific agent run (allows multiple runs per task). |
| `success` | boolean | `true` if the agent produced a correct final answer; otherwise `false`. |
| `total_calls` | integer | Number of tool calls made during the run. |
| `total_tokens` | integer | Total number of LLM tokens consumed (prompt + completion). |
| `duration_seconds` | number | Wall‑clock runtime of the run (seconds). |
| `status` | string (enum) | One of `["completed", "failed", "timeout"]`. |
| `warning_codes` | array[string] | Optional list of warning identifiers (e.g., `["OPTIMAL_PATH_MISSING"]`). |
| `timestamp` | string (ISO‑8601) | UTC time when the run finished. |

### 2. Task Definition (`task.schema.yaml`)
| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Primary key matching execution logs. |
| `goal` | string | Natural‑language description of the task objective. |
| `environment` | object | JSON‑serializable representation of the task state. |
| `optimal_path_length` | integer \| null | Provided optimal call count; `null` if missing. |
| `tool_diversity_k` | integer | Minimum number of distinct tool types required (heuristic). |
| `features` | object | Pre‑computed numeric features (e.g., `num_tools`, `desc_len`). |
| `difficulty_score` | number \| null | Model‑predicted difficulty (output of the regression tree); `null` if not yet computed. |

### 3. Evolved Task (`evolved_task.schema.yaml`)
| Field | Type | Description |
|-------|------|-------------|
| `evolved_task_id` | string | Identifier for the evolved task variant. |
| `base_task_id` | string | Original task identifier from which this variant was derived. |
| `modifications` | array[string] | Human‑readable description of each change applied during evolution. |
| `predicted_penalty` | number | Penalty score predicted by the regression model for this evolved task. |
| `task` | object | Full task definition (matches the Task schema) with all required fields: `task_id`, `goal`, `environment`, `optimal_path_length`, `tool_diversity_k`, `features`, and optionally `difficulty_score`. |
| `generation_timestamp` | string (ISO‑8601) | When the evolution script generated this entry. |

All CSV files (`*.csv`) must contain a header row matching the field names above and be UTF‑8 encoded.

### 4. Penalty Metrics (Primary and Sensitivity)
The plan computes efficiency penalties using two metrics:

- **Primary Metric (Tool Diversity Heuristic)**: `penalty_primary = total_calls / tool_diversity_k`. Used when `optimal_path_length` is null. Logged with warning `OPTIMAL_PATH_MISSING`.
- **Sensitivity Metric (Minimum Step Count)**: `penalty_sensitivity = total_calls / minimum_step_count`. Used when `minimum_step_count` is available in the dataset. Enables robustness validation.

Both metrics are computed for every task and recorded in the derived CSV files, allowing side-by-side comparison of trade-off results.

## Versioning & Checksums
- Each artifact is accompanied by a SHA‑256 checksum stored in `state/projects/PROJ-936-...yaml` under `artifact_hashes`.  
- Any transformation writes a **new** file (e.g., `baseline_execution_v1.csv` → `baseline_execution_v2.csv`) and updates the checksum map.

## Storage Layout
```
data/
├── raw/                # τ^c‑Bench raw download (or abort if unavailable)
│   └── tasks.json
├── derived/
│   ├── baseline_execution.csv                    # conforms to execution_log.schema.yaml
│   ├── filtered_tasks.csv                        # subset of tasks with penalty>2.0 (primary metric)
│   ├── difficulty_model.pkl                      # sklearn pickle (binary)
│   ├── evolved_tasks.csv                         # conforms to evolved_task.schema.yaml
│   ├── evolved_execution.csv                     # execution logs for evolved set
│   ├── sensitivity_filtered_tasks.csv            # subset with penalty>2.0 (sensitivity metric)
│   ├── sensitivity_evolved_tasks.csv             # evolved tasks for sensitivity analysis
│   └── sensitivity_evolved_execution.csv         # execution logs for sensitivity-evolved set
└── outputs/
    ├── summary.csv
    └── figures/
        └── regression_coefficients.png
```
