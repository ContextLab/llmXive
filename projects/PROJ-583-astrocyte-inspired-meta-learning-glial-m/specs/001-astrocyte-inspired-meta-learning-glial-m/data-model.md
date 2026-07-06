# Data Model: Astrocyte-Inspired Meta-Learning

## 1. Overview

This document defines the data structures for the astrocyte meta-learning project. It covers the configuration, intermediate training states, and final output metrics. All data is stored in JSON or CSV formats for reproducibility and analysis.

## 2. Configuration Schema

The system is driven by a YAML configuration file (`config/default.yaml`).

### 2.1 Top-Level Configuration
```yaml
experiment:
  name: "astrocyte-maml-omniglot"
  seed: 42
  mode: "incremental" # or "baseline", "ablation"

model:
  backbone: "conv4" # Standard MAML backbone
  layers: 4
  hidden_dim: 32

astrocyte:
  enabled: true
  lambda_scale: 0.05
  ode_params:
    alpha: 0.1
    beta: 0.5
    gamma: 0.2
  history_buffer_size: 5

training:
  inner_lr: 0.01
  outer_lr: 0.001
  episodes_per_seed: 100 # Validation subset
  tasks_per_episode: 5
  way: 5
  shot: 1

datasets:
  name: "omniglot" # Primary dataset
  root: "./data"
  download: true

analysis:
  seeds: [42, 123, 456, 789, 101]
  ablation_params: [0.01, 0.05, 0.1]
```

## 3. Intermediate Data Structures

### 3.1 Task Episode
A single 5-way 1-shot task instance.
*   `task_id`: Unique identifier (e.g., `seed_42_task_12`).
*   `support_set`: List of `(image_tensor, label)` tuples.
*   `query_set`: List of `(image_tensor, label)` tuples.
*   `activation_signal`: The aggregated activation value from the support set used for ODE input.

### 3.2 Homeostatic State
Internal state maintained by the astrocyte module.
*   `calcium_concentration`: $Ca_t$ (scalar, clamped to [0, 1]).
*   `homeostatic_factor`: $h_t$ (scalar, derived from $Ca_t$).
*   `history_buffer`: List of past activation signals (EXCLUDES tasks N-1 and N to prevent circular validation).

### 3.3 Training Step Log
Logged after every episode update.
*   `timestamp`: ISO 8601.
*   `seed`: Random seed ID.
*   `task_id`: Current task ID.
*   `loss_support`: Loss on support set.
*   `loss_query`: Loss on query set (before update).
*   `plasticity_score_1`: Accuracy on current task query set (after 1 step).
*   `plasticity_score_5`: Accuracy on current task query set (after 5 steps).
*   `plasticity_score_10`: Accuracy on current task query set (after 10 steps).
*   `stability_score`: Mean accuracy on Meta-Test Buffer (tasks N-1, N-2, N-3) after current update.
*   `h_t`: Homeostatic factor value.
*   `Ca_t`: Calcium concentration value.

## 4. Output Schema

### 4.1 Results File (`results/metrics.csv`)
Aggregated metrics for the entire experiment.
*   `seed`: Random seed.
*   `model_type`: "astrocyte" or "baseline".
*   `lambda_scale`: Homeostatic scale parameter (for ablation).
*   `mean_plasticity`: Mean accuracy on current tasks (5-step plasticity).
*   `mean_stability`: Mean accuracy on Meta-Test Buffer (3-task average stability).
*   `std_plasticity`: Standard deviation.
*   `std_stability`: Standard deviation.
*   `total_episodes`: Total number of episodes run.

### 4.2 Statistical Test Result (`results/stat_test.json`)
Output of the Permutation Test (primary) and Hotelling's T-squared (secondary).

**Permutation Test Output**:
*   `test_name`: "Permutation Test".
*   `test_statistic`: Euclidean distance between mean vectors.
*   `p_value`: Float.
*   `verdict`: "significant", "not_significant", "inconclusive", or "undefined".
*   `reason`: If inconclusive, e.g., "insufficient_power".
*   `confidence_interval`: [lower, upper] or null.
*   `n_seeds`: 5.
*   `effect_size`: Euclidean distance.
*   `baseline_mean`: [Stability, Plasticity].
*   `astrocyte_mean`: [Stability, Plasticity].
*   `permutations`: 10,000.

**Hotelling's T-squared Output (Reference)**:
*   `test_name`: "Hotelling's T-squared".
*   `test_statistic`: T² value.
*   `p_value`: Float.
*   `verdict`: "significant", "not_significant", "inconclusive", "undefined", or "singular".
*   `reason`: If singular, "covariance_singular"; if inconclusive, "insufficient_power".
*   `confidence_interval`: [lower, upper] or null.
*   `n_seeds`: 5.
*   `effect_size`: Estimated Cohen's d or null.
*   `baseline_mean`: [Stability, Plasticity].
*   `astrocyte_mean`: [Stability, Plasticity].
*   `degrees_of_freedom`: 2.

## 5. Data Flow

1.  **Config** -> **Loader** -> **Task Generator** (deterministic sequence) -> **Episodes**.
2.  **Episodes** -> **Trainer** -> **ODE Module** (calcium history buffer excludes N-1, N) -> **Homeostatic State**.
3.  **Homeostatic State** -> **Metric Calculator** (plasticity at 1, 5, 10 steps; stability over 3-task buffer) -> **Step Log**.
4.  **Step Logs** -> **Aggregator** -> **Results CSV**.
5.  **Results CSV** -> **Statistical Analyzer** (Permutation Test primary, Hotelling's secondary) -> **Stat Test JSON**.
