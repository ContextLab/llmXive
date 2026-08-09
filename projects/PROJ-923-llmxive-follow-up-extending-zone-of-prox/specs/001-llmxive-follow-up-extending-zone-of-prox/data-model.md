# Data Model: llmXive Follow-up: Extending "Zone of Proximal Policy Optimization"

## Overview

This document defines the data structures used in the simulation, analysis, and reporting phases. All data is stored in `data/` and validated against YAML schemas in `contracts/`.

## Entities

### 1. Rollout Log (Synthetic)

The core input for the simulation. Contains the history of student model responses and confidence scores.

*   **Format**: JSONL (one JSON object per line)
*   **Location**: `data/synthetic/rollout_log_<seed>.jsonl`
*   **Fields**:
    *   `task_id`: String (Identifier for the task, e.g., "MMLU-History-01")
    *   `cycle`: Integer (1 to 50)
    *   `candidate_id`: String (Identifier for the negative candidate/error mode)
    *   `student_confidence`: Float (0.0 to 1.0)
    *   `expert_confidence`: Float (0.0 to 1.0, ground truth)
    *   `ground_truth`: Boolean (True if student response matches expert)
    *   `noise_applied`: Float (The Gaussian noise value applied to confidence)

### 2. Simulation Run Metadata

Describes the parameters and outcomes of a single simulation run.

*   **Format**: JSON
*   **Location**: `data/synthetic/run_metadata_<seed>.json`
*   **Fields**:
    *   `seed`: Integer
    *   `variant`: String ("static" or "cap")
    *   `task_id`: String
    *   `epsilon`: Float (Pruning threshold, default 0.1)
    *   `num_candidates`: Integer
    *   `num_cycles`: Integer
    *   `aucc`: Float (Area Under Convergence Curve)
    *   `final_accuracy`: Float (Accuracy on held-out test data)
    *   `avg_prompt_length_mid`: Float (Average number of candidates in prompt during cycles 20-40)
    *   `prompt_length_variance`: Float
    *   `edge_cases_triggered`: Integer (Count of times fallback was used)

### 3. Aggregated Metrics

The final output for statistical analysis.

*   **Format**: CSV
*   **Location**: `data/metrics/aggregated_results.csv`
*   **Fields**:
    *   `task_id`: String
    *   `seed`: Integer
    *   `variant`: String
    *   `aucc`: Float
    *   `final_accuracy`: Float
    *   `avg_prompt_length_mid`: Float

### 4. Held-Out Test Data

Subset of MMLU used for final accuracy evaluation.

*   **Format**: Parquet
*   **Location**: `data/raw/mmlu_heldout.parquet`
*   **Fields**:
    *   `question`: String
    *   `answer`: String
    *   `subject`: String
    *   `options`: List[String]

## Data Flow

1.  **Generation**: `code/data/generators.py` creates `rollout_log_<seed>.jsonl` and `run_metadata_<seed>.json`.
2.  **Processing**: `code/loops/base_zppo.py` and `code/loops/cap_zppo.py` read the log, simulate training, and write metrics to `run_metadata`.
3.  **Aggregation**: `code/analysis/metrics.py` reads all `run_metadata` files and writes `aggregated_results.csv`.
4.  **Analysis**: `code/analysis/stats.py` reads `aggregated_results.csv` to perform t-tests.

## Validation

All data files must pass schema validation before analysis. See `contracts/` for schema definitions.
