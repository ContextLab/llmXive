# Data Model: Reproduce & Validate: Scaling the Horizon, Not the Parameters

## Overview

This document defines the data structures used for the reproduction pipeline, including input configurations, raw generation artifacts, and the final validation report.

## Entities

### 1. BenchmarkConfig
Configuration for a single benchmark run.
- `benchmark_name`: String (e.g., "IFBench", "SciCode")
- `sample_count`: Integer (Number of samples to run, e.g., 5)
- `max_tokens`: Integer (Max tokens per trajectory, e.g., 4000 for automated runs)
- `timeout_seconds`: Integer (Max wall-clock time for the job, e.g., 21600)

### 2. Trajectory
A single generation attempt for a benchmark task.
- `task_id`: String (Unique identifier from the dataset)
- `input_prompt`: String (The prompt sent to the model)
- `generated_text`: String (The model's output)
- `token_count`: Integer (Total tokens generated)
- `status`: Enum (`COMPLETED`, `TIMEOUT_EXCEEDED`, `OOM_ERROR`, `ERROR`)
- `error_message`: String (Optional, if status is not COMPLETED)

### 3. BenchmarkResult
The evaluated result for a single task.
- `task_id`: String
- `score`: Float (0.0 to 1.0 or raw score)
- `pass`: Boolean (Whether the task passed the judger)
- `judger_log`: String (Raw output from the judger script)

### 4. ValidationReport
The aggregate report comparing results to the paper.
- `benchmark_name`: String
- `paper_claim`: Float (The score claimed in the paper)
- `reproduced_score`: Float or Null (The average score of the sample, or null if no samples completed)
- `difference`: Float or Null (`reproduced_score - paper_claim`, or null if score is null)
- `pass_status`: Enum (`PASS`, `FAIL`, `INCONCLUSIVE`, `N/A`)
- `sample_size`: Integer
- `resource_log_path`: String (Path to the resource telemetry file)
- `feasibility_status`: Enum (`FEASIBLE`, `INFEASIBLE`, `ABORTED`)

## Data Flow

1.  **Input**: `BenchmarkConfig` + Dataset (from Verified URLs) -> **Pipeline**
2.  **Processing**: Model Inference -> `Trajectory` (Raw JSON)
3.  **Evaluation**: `Trajectory` + `Judger Logic` -> `BenchmarkResult`
4.  **Aggregation**: 
    - If `BenchmarkResult` exists: `BenchmarkResult` (all samples) + Paper Claims -> `ValidationReport` with scores.
    - If `BenchmarkResult` is missing (e.g., SEAL-0 excluded or OOM): `ValidationReport` is generated with `reproduced_score: null`, `difference: null`, and `pass_status: N/A`.
