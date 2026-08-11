# Data Model: llmXive follow-up: extending "LoopCoder-v2"

## Overview

This document defines the data structures, schemas, and transformation pipelines required for the project. All data is stored in `data/` (raw) and `data/processed/` (derivations).

## Entity Definitions

### InputProblem
Represents a code generation problem.
- `problem_id`: Unique identifier (e.g., "HumanEval/0").
- `prompt`: The problem description string.
- `reference_solution`: The ground truth code string.
- `difficulty_stratum`: Categorical label (e.g., "easy", "medium", "hard") based on baseline pass rates.
- `dataset`: Source dataset name ("HumanEval" or "MBPP").

### ConvergenceTrajectory
Represents the model's performance over loop counts.
- `problem_id`: Link to `InputProblem`.
- `loop_count`: Integer ($k$).
- `output`: Generated code string.
- `is_correct`: Boolean (1 if matches reference, 0 otherwise).
- `converged`: Boolean (True if `is_correct` is True at this $k$ and previous were False).
- `censored`: Boolean (True if $k=k_{max}$ and not converged).

### EntropyProxy
Represents the semantic uncertainty metric.
- `problem_id`: Link to `InputProblem`.
- `num_samples`: Integer ($N$).
- `cluster_ids`: List of integers (cluster assignment for each sample).
- `entropy_value`: Float (Shannon entropy).
- `exclusion_reason`: String (if excluded, e.g., "deterministic").

### RuntimeMetrics
Represents computational resource usage (SC-005).
- `task_name`: String (e.g., "entropy_extraction", "convergence_tracking").
- `duration_ms`: Integer (execution time in milliseconds).
- `peak_memory_mb`: Float (peak RAM/VRAM usage in MB).
- `device`: String ("cpu" or "cuda").

## Data Pipeline

1. **Ingestion**: Download HumanEval/MBPP from verified URLs. Parse into `InputProblem` objects.
2. **Entropy Generation**: Run `code/src/entropy.py` -> `data/processed/entropy_results.csv`.
3. **Convergence Generation**: Run `code/src/inference.py` -> `data/processed/convergence_results_core.csv` and `convergence_results_sensitivity.csv`.
4. **Router Training**: Run `code/src/router.py` -> `data/processed/router_model.pkl`, `router_metrics.json`.
5. **Robustness**: Run `code/src/robustness.py` -> `data/processed/sensitivity_sweep.json`.
6. **Metrics Logging**: Run `code/src/utils.py` (logging) -> `data/processed/runtime_metrics.json`.

## Data Hygiene & Checksums

- **Raw Data**: `data/raw/humaneval.parquet`, `data/raw/mbpp.jsonl`. Checksums recorded in `state/...yaml`.
- **Processed Data**: All derived files are checksummed. No in-place modifications.
- **PII**: None expected (code datasets are synthetic).

## File Formats

- **CSV**: Comma-separated, UTF-8, header row.
- **Parquet**: Apache Parquet (for raw dataset).
- **JSON**: Standard JSON for metrics and configuration.
- **Pickle**: Python pickle (for model artifacts, versioned).

## Configuration

- `max_mbpp_samples`: Integer. Maximum number of MBPP samples to process. Default: 500.
- `max_samples`: Integer. Maximum total samples (HumanEval + MBPP subset).
- `k_max`: Integer. Maximum loop count for convergence (default 3).