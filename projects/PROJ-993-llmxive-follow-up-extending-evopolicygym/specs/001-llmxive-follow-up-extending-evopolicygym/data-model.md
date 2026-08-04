# Data Model: llmXive follow-up: extending "EvoPolicyGym: Evaluating Autonomous Policy Evolution in Interactive En"

## 1. Overview

This document defines the data artifacts produced and consumed by the `001-llmxive-counterfactual-extension` feature. All data is stored in `projects/PROJ-993-llmxive-follow-up-extending-evopolicygym/data/` and is checksummed.

## 2. Data Entities

### 2.1 DynamicShiftEnvironment Config
Defines the parameters for the environment shift.
*   **Purpose**: Configuration for the 16 extended environments.
*   **Format**: JSON/YAML.
* **Key Fields**: `env_id`, `shift_step` (default [deferred]), `shift_type` (reward/transition), `shift_params`.

### 2.2 Trajectory Log
Records of agent-environment interactions.
*   **Purpose**: Input for counterfactual generation and performance analysis.
*   **Format**: CSV (one row per step).
*   **Key Fields**: `run_id`, `step`, `state`, `action`, `reward`, `shifted` (bool), `rule_violated` (optional).

### 2.3 Counterfactual Explanation
Generated feedback for agent failures.
*   **Purpose**: Training signal for the counterfactual condition.
*   **Format**: JSON (one entry per failure).
*   **Key Fields**: `run_id`, `trajectory_id`, `explanation_text`, `rule_id`, `corrective_action`, `generation_time_ms`, `fallback_used` (bool).

### 2.4 Evolved Policy
The Python source code of the evolved agent.
*   **Purpose**: Artifact for complexity analysis and final evaluation.
*   **Format**: `.py` file.
*   **Metadata**: Stored in a manifest CSV (see 2.5).

### 2.5 Evolution Metrics
Aggregated results for each evolutionary run.
*   **Purpose**: Input for statistical analysis.
*   **Format**: CSV (one row per run).
*   **Key Fields**: `run_id`, `seed`, `condition`, `env_id`, `pre_shift_score`, `post_shift_score`, `generalization_score`, `complexity_cyclomatic`, `complexity_branches`, `explanation_success_rate`.

## 3. Data Flow

1.  **Config Generation**: `code/utils/config.py` generates `dynamic_shift_config.json`.
2.  **Simulation**: `code/agents/evolutionary_harness.py` runs the loop:
    *   Generates `trajectory_logs/run_<id>.csv`.
    *   Calls `code/explanation/generator.py` -> `explanation_logs/run_<id>.json`.
    *   Saves `policies/run_<id>.py`.
3.  **Analysis**: `code/analysis/stats.py` reads logs and policies:
    *   Computes complexity via `radon`.
    *   Aggregates metrics into `metrics/evolution_summary.csv`.
    *   Outputs `results/statistical_test_results.json`.

## 4. Data Hygiene & Reproducibility

*   **Checksums**: Every file in `data/` is checksummed (SHA-256) and recorded in `state/...yaml`.
*   **Immutability**: Raw logs are never modified. Derived metrics are written to new files.
*   **Seeding**: All random seeds are logged in the `run_id` and `seed` columns.
*   **Versioning**: The `requirements.txt` used for generation is recorded in the metadata.
