# Data Model: APPO: Agentic Procedural Policy Optimization

## 1. Overview
This document defines the data structures, schemas, and relationships for the APPO project. All data artifacts adhere to the **Data Hygiene** principle (checksummed, immutable raw data, derived processed data).

## 2. Core Entities

### 2.1 TrainingRun
Represents a single execution of the training loop.
*   **Attributes**:
    *   `run_id`: Unique identifier (UUID).
    *   `variant`: `No-Score`, `Score-Default`, or `Score-Ablation-{config_id}`.
    *   `seed`: Integer (random seed).
    *   `benchmark`: `MATH`, `ToolCalling`.
    *   `config`: JSON object containing hyperparameters (epsilon, epsilon_prime, beta_weight).
    *   `steps_to_threshold`: Integer (or `null` if not reached).
    *   `threshold_value`: Float (80% of pilot max).
    *   `final_success_rate`: Float.
    *   `mean_tool_calls`: Float.
    *   `status`: `completed`, `threshold-not-reached`, `oom`, `error`.
    *   `start_time`, `end_time`: ISO 8601 timestamps.

### 2.2 BranchingScoreConfig
Hyperparameters for the Branching Score.
*   **Attributes**:
    *   `epsilon`: Float (clipping threshold).
    *   `epsilon_prime`: Float (secondary clipping threshold).
    *   `beta_weight`: Float (weighting factor).

### 2.3 StepLog
Granular log of each training step.
*   **Attributes**:
    *   `run_id`: FK to `TrainingRun`.
    *   `step`: Integer.
    *   `entropy`: Float.
    *   `future_value`: Float.
    *   `branching_score`: Float.
    *   `reward`: Float.
    *   `success`: Boolean.

### 2.4 StatisticalResult
Outcome of hypothesis testing.
*   **Attributes**:
    *   `comparison_id`: Unique ID.
    *   `config_a`: Variant name.
    *   `config_b`: Variant name.
    *   `metric`: `steps_to_threshold`, `mean_tool_calls`.
    *   `test_type`: `wilcoxon`.
    *   `p_value`: Float.
    *   `confidence_interval`: [Float, Float].
    *   `effect_size`: Float (rank-biserial correlation).
    *   `significant`: Boolean (based on corrected alpha).

## 3. File Formats

*   **Raw Data**: Parquet/JSONL (downloaded from HuggingFace).
*   **Processed Data**: CSV (aggregated logs), JSON (config snapshots).
*   **Logs**: JSON Lines (`.jsonl`) for streaming, CSV for final aggregation.
*   **Results**: JSON (for programmatic access), Markdown (for human reading).

## 4. Data Flow

1.  **Ingestion**: `datasets.load_dataset` -> `data/raw/` (checksummed).
2.  **Preprocessing**: `code/data/prepare.py` -> `data/processed/` (filtered, tokenized).
3.  **Training**: `code/training/loop.py` reads `processed/`, writes `results/logs/{run_id}.jsonl`.
4.  **Aggregation**: `code/analysis/aggregate.py` reads `logs/`, writes `results/stats/summary.csv`.
5.  **Reporting**: `code/analysis/report_gen.py` reads `summary.csv`, writes `results/report.md`.