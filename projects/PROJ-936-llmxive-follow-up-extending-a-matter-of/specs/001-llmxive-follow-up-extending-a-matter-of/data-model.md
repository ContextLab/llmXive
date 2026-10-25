# Data Model: LLM Agent Efficiency vs. Reasoning Trade‑off Analysis

## Overview
All artifacts reside under `data/` with explicit versioning, checksum tracking, and schema validation via the contract file `contracts/artifact.schema.yaml`.

### 1. Execution Log (`execution_log` schema)
| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Identifier from τⁿ‑Bench. |
| `run_id` | string | UUID for this specific agent run. |
| `success` | boolean | `true` if the final answer is correct. |
| `total_calls` | integer (≥ 0) | Number of tool calls issued. |
| `total_tokens` | integer (≥ 0) | Total LLM tokens consumed (prompt + completion). |
| `duration_seconds` | number (≥ 0) | Wall‑clock runtime. |
| `status` | string (enum) | `"completed"`, `"failed"` or `"timeout"`. |
| `warning_codes` | array[string] | Optional warnings (e.g., `["OPTIMAL_PATH_MISSING"]`). |
| `timestamp` | string (ISO‑8601) | UTC completion time. |

### 2. Task Definition (`task` schema)
| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Primary key matching execution logs. |
| `goal` | string | Natural‑language description of the objective. |
| `environment` | object | JSON‑serializable state representation. |
| `optimal_path_length` | integer | null | Provided optimal call count; may be missing. |
| `tool_diversity_k` | integer | Minimum number of distinct tool types required (heuristic). |
| `features` | object | Pre‑computed numeric features (e.g., `num_tools`, `desc_len`). **Note:** `tool_diversity_k` is **excluded** from the feature set used to train the difficulty model to avoid circularity. |
| `difficulty_score` | number | null | Model‑predicted difficulty; null before training. |

### 3. Evolved Task (`evolved_task` schema)
| Field | Type | Description |
|-------|------|-------------|
| `evolved_task_id` | string | Unique ID for the evolved variant. |
| `base_task_id` | string | ID of the source task. |
| `modifications` | array[string] | Human‑readable description of each change. |
| `predicted_penalty` | number | Penalty score predicted by the regression model for this evolved task. |
| `task` | object (nested `task` schema) | Full task definition of the evolved variant. |
| `generation_timestamp` | string (ISO‑8601) | When the evolution script generated the record. |

### 4. Penalty Metrics
- **Primary**: `penalty_primary = total_calls / optimal_path_length` when `optimal_path_length` is present; otherwise `penalty_primary = total_calls / tool_diversity_k`.  
- **Sensitivity**: `penalty_alt = total_calls / tool_diversity_k` (identical when `optimal_path_length` missing).  
- **Optional Step‑Count Metric** (if dataset provides `minimum_step_count`): `penalty_step = total_calls / minimum_step_count`.  

Both primary and sensitivity metrics are stored in derived CSV files for side‑by‑side comparison.

## Versioning & Checksums
- Every generated file is accompanied by a SHA‑256 checksum recorded in `state/projects/PROJ-936-...yaml` under `artifact_hashes`.  
- Transformations never overwrite existing files; they produce a new file (e.g., `baseline_execution_v1.csv` → `baseline_execution_v2.csv`) and update the checksum map.

## Storage Layout
```
data/
├── raw/
│   └── tau_c_bench/               # downloaded from HuggingFace (or abort)
├── derived/
│   ├── baseline_execution.csv                # execution_log records
│   ├── filtered_tasks.csv                    # tasks with penalty > 2.0
│   ├── correlation_results.json              # point‑biserial output
│   ├── difficulty_model.pkl                  # sklearn DecisionTreeRegressor
│   ├── evolved_tasks.csv                     # evolved_task records
│   ├── evolved_execution.csv                 # logs for evolved set
│   ├── sensitivity_filtered_tasks.csv        # filtered using penalty_alt
│   ├── sensitivity_evolved_tasks.csv         # evolved tasks for alt metric
│   └── sensitivity_evolved_execution.csv     # logs for alt‑metric evolved set
└── outputs/
    ├── summary.csv
    └── figures/
        ├── regression_coefficients.png
        └── cost_performance_frontier.png
```

---



