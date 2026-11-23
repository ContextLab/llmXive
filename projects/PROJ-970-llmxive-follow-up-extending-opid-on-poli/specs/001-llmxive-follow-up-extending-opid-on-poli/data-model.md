# Data Model: OPID Critical-First Routing Complexity Analysis

## Overview

This document defines the data structures, schemas, and storage formats for the OPID routing complexity analysis. All data is stored in CSV format for portability and analysis in `pandas`.

## Entities

### 1. Graph Configuration
Represents the parameters used to generate a specific synthetic environment.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `graph_id` | string | Unique identifier for the graph instance. | UUID format |
| `tier` | string | Complexity tier (Tier 1, Tier 2, Tier 3). | Enum: ["Tier 1", "Tier 2", "Tier 3"] |
| `num_nodes` | integer | Number of nodes in the graph. | Tier 1: 5-10; Tier 2: 20-50; Tier 3: 100+ |
| `num_edges` | integer | Number of edges in the graph. | > 0 |
| `stochasticity` | float | Probability of stochastic transition (0.0 for Tier 1). | 0.0 to 1.0 |
| `reward_sparsity` | float | Ratio of reward nodes to total nodes. | 0.0 to 1.0 |
| `path_exists` | boolean | Validation flag indicating a valid path exists. | True (if valid) |
| `split_set` | string | Whether the graph is in 'train' or 'validation' set. | Enum: ["train", "validation"] |

### 2. Episode Result
The primary output record for each simulation run.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `episode_id` | string | Unique identifier for the episode. | UUID format |
| `graph_id` | string | Reference to the graph used. | FK to Graph Config |
| `tier` | string | Complexity tier. | Enum: ["Tier 1", "Tier 2", "Tier 3"] |
| `threshold` | float | Routing threshold used (0.0 to 1.0). | 0.0, 0.1, ..., 1.0 |
| `success` | boolean | Whether the agent reached the goal. | True/False |
| `steps_taken` | integer | Number of steps to complete (or max steps). | > 0 |
| `action_entropy` | float | Mean action entropy for the episode. | >= 0.0 |
| `log_prob_shift` | float | Mean log-probability shift (advantage). | float |
| `timestamp` | string | ISO 8601 timestamp of completion. | ISO 8601 |

### 3. Aggregated Metrics
Derived metrics calculated per (Tier, Threshold) combination.

| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| `tier` | string | Complexity tier. | Enum |
| `threshold` | float | Routing threshold. | 0.0 to 1.0 |
| `n_episodes` | integer | Number of episodes in this bin. | > 0 |
| `success_rate` | float | Proportion of successful episodes. | 0.0 to 1.0 |
| `mean_entropy` | float | Mean action entropy. | >= 0.0 |
| `entropy_variance` | float | Variance of action entropy. | >= 0.0 |
| `residual_variance` | float | Policy rigidity (residual variance from quadratic fit). | >= 0.0 |
| `cost_benefit_ratio` | float | Distillation cost-benefit ratio (from validation set). | float (or NaN if denom=0) |
| `quadratic_beta2` | float | Quadratic coefficient from GLM. | float |
| `quadratic_p_value` | float | P-value for quadratic term. | float |
| `inflection_point` | float | Threshold where performance declines (if detected). | float |

## Storage Format

- **Raw Data**: `data/raw/synthetic_graphs/{graph_id}.json` (Graph topology in JSON)
- **Processed Data**: `data/processed/episode_results.csv` (Flat table of all episodes)
- **Aggregated Data**: `data/processed/aggregated_metrics.csv` (Summary statistics)

## Data Flow

1.  **Generation**: `graph_generator.py` creates graphs, assigns to 'train' or 'validation' sets, and saves to `data/raw/` (JSON).
2.  **Simulation**: `runner.py` loads a graph (from 'train' set), runs an episode, calculates metrics, and appends a row to `episode_results.csv` (streaming write).
3.  **Aggregation**: `aggregation.py` reads `episode_results.csv`, groups by (Tier, Threshold), performs **quadratic regression** for rigidity, and writes `aggregated_metrics.csv`.
4.  **Analysis**: `regression.py` reads `aggregated_metrics.csv` to fit GLM models and generate plots.