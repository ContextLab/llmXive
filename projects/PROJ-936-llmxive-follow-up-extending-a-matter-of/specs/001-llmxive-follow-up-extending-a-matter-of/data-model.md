# Data Model: LLM Agent Efficiency vs. Reasoning Trade-off Analysis

## Overview
All data artifacts live under `data/` with explicit versioning and checksum tracking. Primary schemas are validated against the contract files in `contracts/`.

### 1. Execution Log (`execution_log.schema.yaml`)
| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Unique identifier from the τⁿ‑Bench dataset. |
| `run_id` | string | UUID for this specific agent run (allows multiple runs per task). |
| `success` | boolean | `true` if the agent produced a correct final answer; otherwise `false`. |
| `total_calls` | integer | Number of tool calls made during the run. |
| `total_tokens` | integer | Total number of LLM tokens consumed (prompt + completion). |
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
| `task` | object | Full task definition (nested Task object, see `task.schema.yaml`). |
| `generation_timestamp` | string (ISO‑8601) | When the evolution script generated this entry. |

### 4. Penalty Metrics (Primary & Sensitivity)
- **Primary Metric**: `penalty_primary = total_calls / tool_diversity_k`. This directly implements the spec’s definition of optimal path as the minimum distinct tool types.  
- **Sensitivity Metric**: `penalty_alt = total_calls / tool_diversity_k` (identical to primary when `optimal_path_length` is unavailable). If a true *minimum step count* (`minimum_step_count`) is present in the dataset, an additional alternative metric `penalty_step = total_calls / minimum_step_count` can be computed; the analysis will compare coefficients across metrics (SC‑010).

Both metrics are stored in derived CSV files for side‑by‑side comparison.

## Versioning & Checksums
- Each artifact is accompanied by a SHA‑256 checksum stored in `state/projects/PROJ-936-...yaml` under `artifact_hashes`.  
- Transformations always write a **new** file (e.g., `baseline_execution_v1.csv` → `baseline_execution_v2.csv`) and update the checksum map.

## Storage Layout
```
data/
├── raw/                # τⁿ‑Bench raw download (or abort if unavailable)
│   └── tasks.json
├── derived/
│   ├── baseline_execution.csv                # conforms to execution_log.schema.yaml
│   ├── filtered_tasks.csv                    # tasks with penalty>2.0 (primary metric)
│   ├── correlation_results.json              # point‑biserial correlation output
│   ├── difficulty_model.pkl                  # sklearn pickle (binary)
│   ├── evolved_tasks.csv                     # conforms to evolved_task.schema.yaml
│   ├── evolved_execution.csv                 # execution logs for evolved set
│   ├── sensitivity_filtered_tasks.csv        # filtered using penalty_alt
│   ├── sensitivity_evolved_tasks.csv         # evolved tasks for sensitivity analysis
│   └── sensitivity_evolved_execution.csv     # logs for sensitivity‑evolved set
└── outputs/
    ├── summary.csv
    └── figures/
        ├── regression_coefficients.png
        └── cost_performance_frontier.png
```

---

