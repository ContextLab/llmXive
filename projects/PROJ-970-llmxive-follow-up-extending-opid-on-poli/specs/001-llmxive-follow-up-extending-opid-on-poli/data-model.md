# Data Model: OPID Critical-First Routing Complexity Analysis

## Overview

This document defines the data structures for the synthetic environment generation, episode execution, and statistical analysis. All data is persisted in `data/` as CSV or Parquet files to ensure reproducibility and checksum verification.

## Entities

### 1. StateGraph (Environment)

Represents the synthetic environment for a specific run.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `graph_id` | str | Unique identifier (e.g., `tier1_seed_123`) | PK |
| `tier` | int | Complexity tier (1, 2, or 3) | 1, 2, 3 |
| `num_nodes` | int | Total nodes in the graph | Tier 1: 5-10; Tier 2: 20-50; Tier 3: 100+ |
| `num_edges` | int | Total edges | > 0 |
| `is_stochastic` | bool | Whether transitions have probabilistic outcomes | Tier 1: False; Tier 2/3: True |
| `reward_sparsity` | float | Fraction of nodes with non-zero rewards | 0.0 to 1.0 |
| `seed` | int | Random seed used for generation | |
| `start_node` | str | ID of start node | |
| `goal_node` | str | ID of goal node | |
| `path_length` | int | Length of ground-truth path | > 0 |

### 2. EpisodeResult

Record of a single simulation run.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `episode_id` | str | Unique ID (`graph_id_threshold_episode_num`) | PK |
| `graph_id` | str | FK to StateGraph | |
| `tier` | int | Complexity tier | 1, 2, 3 |
| `threshold` | float | Routing threshold used (0.0 to 1.0) | 0.0, 0.1, ..., 1.0 |
| `success` | bool | Did the agent reach the goal? | |
| `steps_taken` | int | Number of steps to reach goal or max | > 0 |
| `action_entropy_mean` | float | Mean action entropy over the episode | >= 0 |
| `action_entropy_variance` | float | **Raw variance** of action entropy over the episode | >= 0 |
| `log_prob_shift` | float | Average log-probability shift from skill injection | |
| `timestamp` | str | ISO 8601 timestamp | |

### 3. SummaryStats

Aggregated statistics per (Tier, Threshold) combination.

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `tier` | int | Complexity tier | 1, 2, 3 |
| `threshold` | float | Routing threshold | 0.0 to 1.0 |
| `n_episodes` | int | Count of episodes | [deferred] |
| `success_rate` | float | Mean success rate | 0.0 to 1.0 |
| `mean_entropy` | float | Mean action entropy | |
| `entropy_variance` | float | Mean **raw variance** of action entropy (rigidity) | |
| `log_prob_shift_mean` | float | Mean log-probability shift | |
| `quadratic_fit_r2` | float | R-squared of quadratic fit (if applicable) | |
| `quadratic_fit_p` | float | P-value of quadratic term (if applicable) | |

## Data Flow

1.  **Generation**: `graph_generator.py` creates `StateGraph` objects based on `tier` and `seed`.
2. **Execution**: `runner.py` executes [deferred] episodes, generating `EpisodeResult` records.
3.  **Aggregation**: `analyzer.py` computes `SummaryStats` and fits regression models.
4.  **Storage**:
    -   `data/processed/episode_results.csv`: All raw episode data.
    -   `data/processed/summary_stats.csv`: Aggregated results.
    -   `data/raw/graph_seeds.json`: Metadata for reproducibility.

## Constraints & Validation

-   **Threshold Range**: Must be in [0.0, 1.0] with step 0.1.
-   **Tier Consistency**: `num_nodes` must match the tier definition (5-10, 20-50, 100+).
-   **Success Rate**: Must be in [0.0, 1.0].
-   **Entropy**: Must be non-negative.
-   **Completeness**: `n_episodes` must equal 1,000 for each (Tier, Threshold) pair.
