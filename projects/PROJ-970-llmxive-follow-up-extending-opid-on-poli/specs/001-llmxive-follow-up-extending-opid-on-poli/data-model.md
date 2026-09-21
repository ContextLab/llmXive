# Data Model: OPID Critical-First Routing Complexity Analysis

## Overview
This document defines the data structures for the synthetic environment generation, episode execution, and aggregated results. All data is stored in local files (`data/raw/`, `data/processed/`) and validated against `contracts/`.

## Entities

### 1. StateGraph (Environment)
A directed graph representing the environment.
- **Nodes**: States (integers or strings). Attributes: `tier`, `is_start`, `is_goal`, `reward`.
- **Edges**: Transitions. Attributes: `probability`, `stochastic`.
- **Metadata**: `seed`, `tier_id`, `node_count`, `path_length`.

### 2. EpisodeResult
A record for a single simulation run.
- **Fields**:
  - `episode_id`: Unique identifier (UUID).
  - `tier`: 1, 2, or 3.
  - `threshold`: Float (0.0 to 1.0).
  - `success`: Boolean (True if goal reached via ground-truth path).
  - `steps`: Integer (total steps taken).
  - `action_entropy_variance`: Float (variance of action entropies during the episode).
  - `log_prob_shift`: Float (cumulative log-probability shift due to injection).
  - `injection_count`: Integer (number of times skill signal was injected).
  - `conditional_entropy_variance`: Float (Variance of action entropy *given* injection vs. *given* no injection).

### 3. AggregatedMetrics
Per ($\text{Tier}, \text{Threshold}$) summary.
- **Fields**:
  - `tier`: Integer.
  - `threshold`: Float.
  - `success_rate`: Float (0.0 to 1.0).
  - `success_rate_baseline`: Float (Success rate at $\tau=1.0$ for this tier).
  - `success_rate_improvement`: Float (success_rate - success_rate_baseline).
  - `mean_entropy_variance`: Float.
  - `policy_rigidity`: Float (Conditional variance reduction due to injection).
  - `distillation_cost_benefit`: Float (Mean log-prob shift / success_rate_improvement).
  - `n_episodes`: Integer.

## Data Flow

1.  **Generation**: `generator.py` creates `StateGraph` objects based on `tier` and `seed`.
    - Output: JSON files in `data/raw/synthetic_graphs/`.
2.  **Execution**: `runner.py` executes episodes sequentially.
    - Output: `EpisodeResult` records appended to `data/processed/results.csv` (or JSONL).
3.  **Aggregation**: `aggregation.py` groups by `tier` and `threshold`.
    - **CRITICAL**: Calculates `policy_rigidity` (conditional variance reduction) and `distillation_cost_benefit` (log-prob shift / success_rate_improvement) here.
    - **Baseline Logic**: For each tier, the success rate at $\tau=1.0$ is identified and applied as the baseline to all other thresholds in that tier.
    - Output: `data/processed/aggregated_metrics.csv`.
4.  **Analysis**: `stats.py` performs regression and ANOVA on aggregated data.

## Storage Strategy

- **Raw Data**: `data/raw/synthetic_graphs/` contains one JSON file per generated graph.
  - *Naming*: `tier_{tier}_seed_{seed}.json`.
  - *Checksum*: SHA-256 hash recorded in `data/checksums.json`.
- **Processed Data**: `data/processed/results.csv` (streamed append) and `data/processed/aggregated_metrics.csv`.
- **Logs**: `logs/simulation.log` contains runtime warnings (e.g., "deterministic policy observed").

## Constraints

- **Immutability**: Raw graph files are never modified.
- **Reproducibility**: Every graph and episode result is tied to a specific `seed` and `code_version`.
- **Memory**: Intermediate episode data is discarded after writing to CSV.