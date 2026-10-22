# Data Model: llmXive follow-up: extending "Foundation Protocol: A Coordination Layer for Agentic Society"

## Overview
All pipeline artifacts are stored as JSON (intermediate) or CSV (final) files. Schemas in `contracts/` enforce structural validity.

## Entities

### 1. Workflow
| Field | Type | Description |
|---|---|---|
| `workflow_id` | string (UUID) | Unique identifier |
| `delegation_depth` | integer (1‑10) | Length of agent delegation chain (consistent range across the project) |
| `policy_complexity` | integer (1‑20) | Number of policy constraints attached (consistent range across the project) |
| `nodes` | array of `PolicyNode` | Policy constraints |
| `edges` | array of `[source, target]` strings | Directed edges |
| `is_valid` | boolean | `true` if the workflow is solvable by the Oracle Policy Engine |

### 2. PolicyNode
| Field | Type | Description |
|---|---|---|
| `node_id` | string | Unique ID |
| `type` | string | e.g., `"budget"`, `"sovereignty"` |
| `content` | string | Text description |
| `dependencies` | array of strings | IDs of prerequisite nodes |

### 3. ExecutionLog (one per run)
| Field | Type | Description |
|---|---|---|
| `workflow_id` | string | Reference to Workflow |
| `mode` | `"full_context"` | `"compressed"` | Execution mode |
| `compression_depth` | integer | `0` for full context, otherwise BFS/DFS depth |
| `token_count` | integer | Tokens counted via `tiktoken` (`cl100k_base`) |
| `context_reduction_pct` | number 0‑100 **or** string `"[deferred]"` | % reduction vs full context |
| `violations` | array of `Violation` | Detected policy breaches |
| `error_rate` | number 0‑1 | `len(violations) / total_steps` (valid workflows only) |
| `timestamp` | ISO‑8601 string | Execution time |

### 4. Violation
| Field | Type | Description |
|---|---|---|
| `node_id` | string | Policy node that violated |
| `reason` | string | `"missing_context"`, `"deduction_failure"`, etc. |
| `step_index` | integer | Position in workflow execution |

### 5. StepOutcome (new)
| Field | Type | Description |
|---|---|---|
| `workflow_id` | string | Reference to the originating workflow |
| `step_id` | string | Unique identifier for the individual step |
| `outcome` | integer (0 | 1) | Binary indicator: `0` = no violation, `1` = violation |
| `context_reduction_pct` | number 0‑100 **or** string `"[deferred]"` | Same reduction value as in the parent `ExecutionLog` (numeric for regression, `[deferred]` for edge cases) |
| `policy_complexity` | integer | Copied from the workflow for modeling |
| `delegation_depth` | integer | Copied from the workflow for modeling |
| `timestamp` | ISO‑8601 string | When the step was processed |

### 6. TradeOffCurve (aggregated result)
| Field | Type | Description |
|---|---|---|
| `reduction_pct` | number | Context reduction percentage (rounded 2 dp) |
| `error_rate` | number (0‑1) | Mean policy‑violation error rate at this reduction |
| `std_dev` | number | Standard deviation of error rates |
| `n_samples` | integer | Number of execution logs contributing |
| `threshold_confidence_lower` | number | Lower bound of 95 % CI for safe‑zone threshold |
| `threshold_confidence_upper` | number | Upper bound of 95 % CI for safe‑zone threshold |

### 7. RunMetrics
| Field | Type | Description |
|---|---|---|
| `total_wall_clock_time_seconds` | number | End‑to‑end runtime |
| `start_timestamp` | ISO‑8601 string | Pipeline start |
| `end_timestamp` | ISO‑8601 string | Pipeline end |
| `total_workflows` | integer | Count of generated workflows |
| `total_executions` | integer | Full + Compressed runs |
| `invalid_workflow_ratio` | number (0‑1) | Proportion of generated workflows flagged `is_valid=False` |
| `estimated_power` | number | Power estimate from the simulation‑based analysis (0‑1) |

## Data Flow
1. `generator.py` → `data/raw/workflows.json` (conforms to `workflow.schema.yaml`).  
2. `executor.py` (full) → `data/processed/full_context_logs.json`.  
3. `executor.py` (compressed) → `data/processed/compressed_context_logs.json`.  
4. **T‑Prepare‑Step‑Level‑Data** expands logs into `data/processed/step_outcomes.json` (conforms to the new `StepOutcome` description).  
5. `analyzer.py` → `data/results/tradeoff_curve.csv` (SSoT) and `data/results/threshold_report.json`.  
6. `analyzer.py` → `data/results/run_metrics.json`.  
7. After each step, `utils.py` computes SHA‑256 checksums stored in `state/projects/...yaml`.

## Formatting Rules
- `context_reduction_pct` is a **numeric** value unless the workflow is a single node or `compression_depth=0`; in those cases the literal string `"[deferred]"` must be used.  
- All percentages in CSV are rounded to **two decimal places**.  
- `tradeoff_curve.csv` is the **single source of truth** for any figure or table in the eventual paper (Constitution IV).  
- `step_outcomes.json` is the source data for the GEE regression; it is **not** presented directly in the paper but is the SSoT for the statistical model.  
- Rows with `context_reduction_pct="[deferred]"` are **included in descriptive statistics** and a **sensitivity analysis**, but **excluded from the GEE regression** because they lack a numeric reduction value, thereby avoiding selection bias.
