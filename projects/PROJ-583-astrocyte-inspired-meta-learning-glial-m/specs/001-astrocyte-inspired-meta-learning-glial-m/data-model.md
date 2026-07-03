# Data Model: Astrocyte-Inspired Meta-Learning

## 1. Overview

This document defines the data structures for the Astrocyte Meta-Learning project. It ensures that all metrics, parameters, and results are stored in a structured, reproducible format that aligns with the project's Constitution (Principle III: Data Hygiene, Principle IV: Single Source of Truth).

## 2. Data Entities

### 2.1 Configuration (YAML/JSON)
Stores all hyperparameters, seeds, and dataset paths.
-   **Entity**: `Config`
-   **Purpose**: Reproducible execution setup.
-   **Fields**:
    -   `seed`: Integer (Random seed).
    -   `dataset_seed`: Integer (Seed for dataset subsampling to ensure fairness between Baseline and Astrocyte).
    -   `dataset`: String ("omniglot" or "mini_imagenet").
    -   `task_shots`: Integer (e.g., 1, 5).
    -   `task_ways`: Integer (e.g., 5).
    -   `ode_params`: Object (decay, alpha, beta, history_buffer, tau_hist).
    -   `homeostatic_scale`: Float (sweep parameter).
    -   `inner_loop_steps`: Integer (15).
    -   `num_episodes`: Integer (Total training episodes).
    -   `stability_buffer_size`: Integer (Fixed at 5, per research design).

### 2.2 Episode Log (JSON/CSV)
Record of a single training episode.
-   **Entity**: `EpisodeLog`
-   **Purpose**: Time-series tracking of stability and plasticity.
-   **Fields**:
    -   `episode_id`: Integer.
    -   `seed`: Integer.
    -   `task_id`: String/Int.
    -   `plasticity_scores`: List[Float] (Accuracy at steps 1, 5, 10).
    -   `stability_scores`: List[Float] (Accuracy on buffer tasks, evaluated on pre-update parameters).
    -   `homeostatic_factor`: Float ($h_t$).
    -   `calcium_concentration`: Float ($Ca_t$).
    -   `loss`: Float (Meta-loss).
    -   `timestamp`: ISO8601 String.
    -   `buffer_tasks`: List[String/Int] (IDs of the 5 tasks used for stability evaluation).

### 2.3 Aggregated Results (JSON/CSV)
Summary of a full training run (all episodes for one seed).
-   **Entity**: `RunSummary`
-   **Purpose**: Statistical analysis input.
-   **Fields**:
    -   `run_id`: String.
    -   `seed`: Integer.
    -   `model_type`: String ("astrocyte" or "baseline").
    -   `mean_plasticity`: Float.
    -   `mean_stability`: Float.
    -   `std_plasticity`: Float.
    -   `std_stability`: Float.
    -   `total_episodes`: Integer.
    -   `avg_homeostatic_factor`: Float.

### 2.4 Statistical Test Output (JSON)
Result of the paired-sample t-test.
-   **Entity**: `StatisticalTestResult`
-   **Purpose**: Final hypothesis validation.
-   **Fields**:
    -   `test_name`: String ("Paired_T_Test").
    -   `metric`: String ("Stability" or "Plasticity").
    -   `t_statistic`: Float.
    -   `p_value`: Float.
    -   `significant`: Boolean (p < 0.025).
    -   `degrees_of_freedom`: Integer (n-1).
    -   `baseline_mean`: Float.
    -   `astrocyte_mean`: Float.
    -   `effect_size`: Float (Cohen's d).
    -   `power_note`: String (Optional, notes on low power if n=5).

## 3. File Naming Convention

-   **Config**: `config_{seed}_{dataset}.yaml`
-   **Logs**: `logs/episode_{seed}_{episode_id}.json`
-   **Summary**: `results/run_summary_{seed}_{model_type}.csv`
-   **Stats**: `results/stat_test_{dataset}_{metric}_{timestamp}.json`

## 4. Data Flow

1.  **Input**: `config.yaml` + `data/raw/` (datasets).
2.  **Process**: `train.py` reads config, loads data, executes ODE/MAML loop.
3.  **Output**: `logs/` (raw), `results/` (aggregated).
4.  **Analysis**: `evaluate.py` reads `results/` to compute `StatisticalTestResult`.
5.  **Storage**: All outputs checksummed and stored in `data/processed/`.
