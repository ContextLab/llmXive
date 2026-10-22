# Data Model: llmXive follow-up: extending "Multi-Turn Reflective Masking Elicits Reasoning in Mask Diffusion Mode"

## Overview
Defines the data structures for the synthetic logical puzzle dataset, execution logs, and aggregated analysis results. All files are JSONL or CSV for streaming friendliness.

## Entities

### 1. LogicalPuzzle (Synthetic Dataset)
**File**: `data/raw/synthetic_puzzles.jsonl`

| Field | Type | Description |
|-------|------|-------------|
| `instance_id` | `string` | Unique identifier (e.g., `"puzzle_001"`). |
| `text` | `string` | Deterministic natural‑language representation of the puzzle. |
| `ground_truth` | `string` | Correct solution path (textual). |
| `ground_truth_path` | `array[string]` | Ordered list of node IDs comprising the valid logical path. |
| `nesting_depth` | `integer` | Length of the longest path in the DAG. |
| `branching_factor` | `number` | Average in‑degree of non‑root nodes. |
| `graph_structure` | `object` | JSON representation of the DAG (`nodes`, `edges`). |
| `target_path_id` | `string` | Identifier of the selected ground‑truth path (perturbation). |
| `seed` | `integer` | Random seed used for generation (reproducibility). |
| `is_acyclic` | `boolean` | Must be `true`. |
| `is_solvable` | `boolean` | Must be `true`. |
| `text_generation_method` | `string` | `"template_based"` (ensures deterministic mapping). |
| `is_orthogonal` | `boolean` | Indicates whether the (depth, branch) pair satisfied the orthogonality constraint (|r| < 0.2). |

### 2. ExecutionLog (Results)
**File**: `data/processed/execution_log.csv`

| Field | Type | Description |
|-------|------|-------------|
| `instance_id` | `string` | FK to `LogicalPuzzle.instance_id`. |
| `turns_to_converge` | `integer` or `null` | Number of turns taken; `null` if censored (failure). |
| `convergence_status` | `string` | `"success"` or `"failure"`. |
| `is_censored` | `boolean` | `true` if the run hit the max‑turn limit. |
| `final_token_sequence` | `string` or `null` | Model’s final output (truncated if long). |
| `path_coverage` | `number` | Fraction of model steps that match DAG edges (0 – 1). |
| `limit_hit` | `boolean` | `true` if the turn limit was reached. |
| `runtime_seconds` | `number` | Wall‑clock time for the run. |
| `error_message` | `string` or `null` | Error details if execution failed. |

### 3. AnalysisResult (Aggregated Statistics)
**File**: `results/statistical_report.json`

| Field | Type | Description |
|-------|------|-------------|
| `cox_depth_hazard_ratio` | `number` | Hazard ratio for `nesting_depth`. |
| `cox_depth_p_value` | `number` | P‑value for the hazard ratio. |
| `tipping_point_depth` | `integer` | Depth where the degradation slope changes. |
| `tipping_point_slope_change` | `number` | Magnitude of slope change at the breakpoint. |
| `failure_rates` | `object` | Mapping `{threshold_turns: failure_rate}` (e.g., `"40": 0.12`). |
| `budget_exhaustion_rate` | `number` | Fraction of 50‑turn failures that converge by 1000 turns. |
| `collinearity_vif` | `number` | Variance Inflation Factor for predictors (optional). |
| `orthogonality_check` | `object` | `{ "correlation_coefficient": <float>, "threshold": 0.2 }`. |
| `spearman_correlation` | `number` | Descriptive Spearman ρ (not used for inference). |

## Constraints & Validation
- `is_acyclic` = `true` for every puzzle.
- `nesting_depth` ∈ [1, 10]; `branching_factor` ∈ [1, 5].
- Correlation between depth and branching must be |r| < 0.2 (checked during generation).
- `turns_to_converge` ≤ `max_turns` (50 primary, 1000 extended) or `null` if censored.
- `instance_id` must be unique across all files.
- `path_coverage` ≥ 0.95 required for a `"success"` status.

---
