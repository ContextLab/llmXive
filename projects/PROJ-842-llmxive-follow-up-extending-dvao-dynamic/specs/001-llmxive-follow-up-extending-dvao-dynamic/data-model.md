# Data Model: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-reward"

## Overview

This document defines the data structures used for the synthetic MDP generation, variance estimation, and statistical analysis. All data is generated programmatically and stored in `data/` with checksums.

## Entities

### 1. SyntheticMDP Configuration
Defines the parameters of a generated environment.
- **state_space_size**: Integer (e.g., 100).
- **action_space_size**: Integer (e.g., 4).
- **num_objectives**: Integer ($N \in \{5, 10, 20, 50\}$).
- **noise_std**: Float ($\sigma$).
- **noise_correlation**: Float ($\rho \in \{0, 0.2, 0.5\}$).
- **noise_distribution**: String ("gaussian", "laplace").
- **seed**: Integer (for reproducibility).

### 2. Trajectory
A single episode of interaction with the MDP.
- **trajectory_id**: String (UUID).
- **steps**: List of step objects.
- **total_rewards**: List of floats (one per objective).

### 3. Step
A single timestep in a trajectory.
- **state**: Integer (state index).
- **action**: Integer (action index).
- **rewards**: List of floats (one per objective).
- **advantages**: List of floats (estimated per objective).

### 4. VarianceEstimate
The result of variance estimation (Heuristic vs. Full-Batch vs. Theoretical).
- **metric_id**: String.
- **objective_index**: Integer.
- **heuristic_variance**: Float (from Moving-Window).
- **full_batch_variance**: Float (from Full-Batch calculation on same trajectory).
- **theoretical_variance**: Float (from analytical formula).
- **heuristic_to_full_batch_ratio**: Float (Heuristic / Full-Batch).
- **window_size**: Integer ($k$).
- **timestamp**: ISO8601.

### 5. StatisticalResult
Aggregated results for a specific configuration ($N, k, \rho$).
- **config_id**: String.
- **num_objectives**: Integer.
- **window_ratio**: Float.
- **p_value**: Float (from paired t-test: Heuristic vs. Full-Batch).
- **mean_bias**: Float (Mean difference: Heuristic - Full-Batch).
- **pareto_distance**: Float.
- **convergence_status**: String ("stable", "unstable", "failed").
- **false_positive_rate**: Float.
- **noise_distribution_type**: String.

## Data Flow

1.  **Generation**: `synthetic_mdp.py` creates `Trajectory` objects based on `SyntheticMDP Configuration`.
2.  **Estimation**: `heuristic.py` processes `Trajectory` to produce `VarianceEstimate` (calculating Heuristic, Full-Batch, and Theoretical values).
3.  **Analysis**: `stats.py` aggregates `VarianceEstimate` into `StatisticalResult` (performing paired t-tests).
4.  **Storage**: All artifacts saved to `data/processed/` as CSV/JSON.

## Storage Format
- **Raw Data**: `data/raw/trajectories_{config_id}.jsonl` (line-delimited JSON for streaming).
- **Processed Data**: `data/processed/stats_{config_id}.csv` (pandas-compatible).
- **Metadata**: `data/metadata.json` (checksums, seeds, git commit hash).