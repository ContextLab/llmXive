# Data Model: State-Guided Curriculum for MobileGym

## Overview

This document defines the data structures, schemas, and flows required for the State-Guided Curriculum feature. All data is stored in the `data/` directory, with raw data preserved and derived data versioned.

## Core Entities

### 1. State Coverage Vector
A binary representation of the exploration status of tracked UI variables.
*   **Type**: `List[bool]` or `numpy.ndarray` (dtype=bool)
*   **Dimensions**: $N$ variables (e.g., 20 tracked proxies).
*   **Semantics**: `0` = Unexplored, `1` = Explored.
*   **Source**: `code/scheduler/state_coverage.py`
*   **Storage**: `data/processed/coverage_vectors/{run_id}/{step_id}.json`

### 2. Task Parameter
Configuration object defining a specific MobileGym task instance.
*   **Fields**: `task_id`, `app_name`, `initial_state`, `goal_description`, `difficulty_estimate`, `intrinsic_complexity` (static count of required transitions).
*   **Source**: `data/raw/mobilegym_tasks/`
*   **Storage**: `data/processed/task_params.json`

### 3. Training Log
Time-series record of training metrics.
*   **Fields**: `step_id`, `timestamp`, `mode` (static/state-guided), `batch_size`, `avg_success_rate`, `total_steps`, `coverage_entropy`, `ema_success_rate`.
*   **Source**: `code/training/runner.py`
*   **Storage**: `data/processed/training_logs/{run_id}.parquet`

### 4. Scheduler Trace
Audit log of the curriculum selection logic.
*   **Fields**: `step_id`, `selected_task_ids`, `reason` (e.g., "low_coverage", "sweet_spot", "fallback_entropy"), `metrics_triggered` (e.g., `{"dark_mode": 0.05}), `ema_estimates`.
*   **Source**: `code/scheduler/curriculum_scheduler.py`
*   **Storage**: `data/processed/scheduler_trace/{run_id}.json`

### 5. Evaluation Results
Final metrics for convergence and transfer.
*   **Fields**: `run_id`, `mode`, `steps_to_50pct`, `test_success_variance`, `proxy_correlation_r`, `proxy_correlation_method` (e.g., "point_biserial").
*   **Source**: `code/analysis/`
*   **Storage**: `data/processed/evaluation_results.json`

## Data Flow

1.  **Ingestion**: MobileGym tasks downloaded and checksummed (`data/raw/`).
2.  **Instrumentation**: During training, `state_coverage.py` updates the binary vector after each rollout.
3.  **Scheduling**: `curriculum_scheduler.py` reads the current coverage vector and selects the next batch of tasks.
4.  **Training**: `runner.py` executes the selected tasks, logs metrics, and updates the coverage vector.
5.  **Analysis**: `analysis/` scripts read the logs to compute convergence, variance, and correlation metrics.
6.  **Validation**: Results are checksummed and stored in `data/processed/`.

## Data Integrity & Hygiene

*   **Checksums**: All files in `data/` are checksummed (SHA-256) upon creation. Checksums are recorded in `state/projects/PROJ-858-llmxive-follow-up-extending-mobilegym-a.yaml`.
*   **Immutability**: Raw data (`data/raw/`) is never modified. Derived data (`data/processed/`) is written to new files with versioned names (e.g., `coverage_v1.json`).
*   **PII**: No Personally Identifiable Information is included in task definitions or logs.
*   **Reproducibility**: Random seeds are set in `code/utils/constants.py` and logged in the training logs.