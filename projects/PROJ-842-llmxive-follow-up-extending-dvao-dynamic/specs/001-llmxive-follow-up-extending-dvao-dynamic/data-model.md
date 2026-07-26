# Data Model: llmXive follow-up: extending "DVAO: Dynamic Variance-adaptive Advantage Optimization for Multi-reward"

## 1. Overview

This document defines the data structures used for the theoretical derivation, synthetic environment generation, and empirical results aggregation. All data is generated in-memory and persisted to JSON for reproducibility.

## 2. Core Entities

### 2.1 SyntheticMDP
Represents a tabular Multi-Objective MDP.
- **State Space**: Finite set $S$, size $|S|$.
- **Action Space**: Finite set $A$, size $|A|$.
- **Objectives**: Integer $N$.
- **Rewards**: A 3D array $R \in \mathbb{R}^{|S| \times |A| \times N}$.
- **Noise Parameters**:
  - `noise_std`: $\sigma$ (float).
  - `noise_distribution`: "gaussian", "heavy_tailed" (Student's t), "sparse", "non_convex".
  - `correlation`: $\rho$ (float, default 0).

### 2.2 VarianceEstimate
Result of the Moving-Window Heuristic (Step-level).
- **metric_id**: Unique identifier for the metric instance (string).
- **objective_index**: Index of the objective (0 to N-1) (integer).
- **timestamp**: Step index $t$.
- **window_size**: $k$.
- **estimated_variance**: $\hat{\sigma}^2_t$.
- **theoretical_variance**: $\sigma^2$ (ground truth).
- **ratio**: $\hat{\sigma}^2_t / \sigma^2$.
- **noise_distribution_type**: "gaussian", "laplace", etc.

### 2.3 ApproximateParetoOracle
Result of the Approximate Pareto Frontier calculation.
- **method**: "weighted_sum_sweep" (string).
- **num_vectors**: Number of weight vectors used (e.g., 1000).
- **frontier_points**: List of reward vectors approximating the frontier.

### 2.4 EmpiricalResult
Aggregated results for a single configuration ($N$, $k$, $\rho$, distribution).
- **config_id**: Unique identifier for the run.
- **N**: Number of objectives.
- **k**: Window size.
- **rho**: Correlation.
- **distribution**: Noise type.
- **sample_count**: Number of episodes to reach Pareto threshold.
- **distance_to_frontier**: Distance metric (FR-017).
- **heuristic_accuracy**: Ratio of heuristic variance to true variance (FR-015).
- **statistical_tests**:
  - `regression_slope`: Slope $\beta$ from log-log regression.
  - `slope_ci_lower`: Lower bound of 95% CI.
  - `slope_ci_upper`: Upper bound of 95% CI.
  - `t_test_p_value`: From one-sample t-test on bias (sanity check).
  - `fdr_q_value`: Adjusted p-value from Benjamini-Hochberg.
- **coincidence_delta**: Difference between failure point N and Pareto distance point.
- **false_positive_rate**: Rate of false positives (SC-004).
- **metadata**:
  - `seed`: Random seed used.
  - `state_space_size`: Effective $|S|$ (may be degraded).
  - `approximation_method`: "weighted_sum_sweep".

## 3. File Formats

### 3.1 `data/processed/empirical_results.json`
A JSON array of `EmpiricalResult` objects.

### 3.2 `data/processed/step_logs.json`
A JSON array of `VarianceEstimate` objects.

### 3.3 `docs/theoretical_derivation.md`
A Markdown file generated from `src/derivation/sample_complexity.py`, containing the closed-form equations and derivation steps.

## 4. Data Flow

1. **Generation**: `src/environment/synthetic_mdp.py` creates `SyntheticMDP` instances.
2. **Simulation**: `src/heuristic/moving_window.py` runs episodes, producing `VarianceEstimate` streams.
3. **Pareto Calculation**: `src/environment/pareto_oracle.py` computes `ApproximateParetoOracle`.
4. **Aggregation**: `src/analysis/stats.py` computes statistics and `EmpiricalResult` objects.
5. **Persistence**: Results are written to `data/processed/empirical_results.json`.

## 5. Validation Rules

- **N**: Integer $\ge 1$.
- **k**: Integer $> 0$, $k < \text{rollout\_size}$.
- **rho**: Float in $[-1, 1]$.
- **noise_std**: Float $> 0$.
- **distance_to_frontier**: Float $\ge 0$.
- **sample_count**: Integer $> 0$.
- **regression_slope**: Float.
- **coincidence_delta**: Integer $\ge 0$.
- **false_positive_rate**: Float in $[0, 1]$.