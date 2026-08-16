# Data Model: llmXive follow-up: extending "EvoPolicyGym: Evaluating Autonomous Policy Evolution in Interactive En"

## Overview

This document defines the data structures, schemas, and storage formats used in the project. All data is stored in `data/` with raw, processed, and final subdirectories.

## Key Entities

### 1. DynamicShiftEnvironment Configuration
Defines the parameters for the dynamic shift in an environment.

| Field | Type | Description |
|-------|------|-------------|
| `env_id` | string | Unique identifier for the environment (e.g., "CartPole-v1"). |
| `shift_threshold` | float | Fraction of total steps at which the shift occurs (default 0.5). |
| `shift_config` | object | Configuration for the change (e.g., `{"reward_inversion": true}`). |
| `rules` | list[object] | List of ground-truth rules for this environment (masked for LLM). |

### 2. Trajectory Log
Record of a single agent-environment interaction episode.

| Field | Type | Description |
|-------|------|-------------|
| `episode_id` | string | Unique ID (UUID). |
| `seed` | int | Random seed used. |
| `condition` | string | "baseline" or "counterfactual". |
| `steps` | list[object] | List of steps: `{step, state, action, reward, is_shifted}`. |
| `total_reward` | float | Sum of rewards. |
| `pre_shift_reward` | float | Sum of rewards before shift. |
| `post_shift_reward` | float | Sum of rewards after shift. |
| `failed` | boolean | Whether the episode ended in failure. |

### 3. Counterfactual Explanation
Generated explanation for a failure.

| Field | Type | Description |
|-------|------|-------------|
| `episode_id` | string | Link to the trajectory. |
| `rule_id` | string | ID of the violated rule (selected by LLM). |
| `explanation_text` | string | Natural language explanation. |
| `suggested_action` | string | The action retrieved from ground-truth lookup. |
| `generation_method` | string | "llm" or "fallback". |
| `valid` | boolean | Whether the output passed schema validation. |

### 4. Evolved Policy Metrics
Static analysis results for a generated policy.

| Field | Type | Description |
|-------|------|-------------|
| `policy_id` | string | Unique ID for the policy. |
| `seed` | int | Seed used for evolution. |
| `condition` | string | "baseline" or "counterfactual". |
| `cyclomatic_complexity` | int | Result from `radon`. |
| `branch_count` | int | Number of if/else branches. |
| `code_length` | int | Lines of code. |
| `generalization_score` | float | Score on the dynamic shift test set. |

### 5. Statistical Results
Aggregated results from the mixed-effects model.

| Field | Type | Description |
|-------|------|-------------|
| `model_id` | string | Unique ID for the analysis run. |
| `p_value` | float | p-value from the mixed-effects model. |
| `effect_size` | float | Cohen's d or similar. |
| `significant` | boolean | True if p < 0.05 (one-tailed) and effect > 0. |
| `complexity_coefficient` | float | Coefficient for complexity covariate. |
| `random_effect_variance` | float | Variance attributed to seeds. |
| `explanation_success_rate` | float | Rate of successful explanation generations (valid text / total failures). |

## Storage Formats

*   **Raw Data**: JSONL (JSON Lines) for trajectory logs and explanations to support streaming writes.
*   **Processed Data**: CSV for `evolution_results.csv` and `complexity_metrics.csv`.
*   **Final Results**: JSON for `stats_results.json`.
*   **Schemas**: YAML (`contracts/*.schema.yaml`) for validation of counterfactual outputs.

## Data Flow

1.  **Generation**: `DynamicShiftEnvironment` produces trajectories -> `data/raw/trajectories/*.jsonl`.
2.  **Feedback**: `CounterfactualGenerator` reads trajectories -> writes `data/raw/explanations.jsonl`.
3.  **Evolution**: `EvolutionaryHarness` evolves policies -> writes `data/raw/policies/*.py`.
4.  **Analysis**: `ComplexityAnalyzer` reads policies -> `data/processed/complexity_metrics.csv`.
5.  **Aggregation**: `StatsRunner` reads metrics + scores -> `data/final/stats_results.json`.
6.  **Fallback Aggregation**: `AggregationRunner` parses `data/processed/fallbacks.log` -> updates `data/final/stats_results.json` with success rate.