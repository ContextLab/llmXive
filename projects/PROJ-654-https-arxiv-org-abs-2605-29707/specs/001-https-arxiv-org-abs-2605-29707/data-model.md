# Data Model: Reproduce & Validate Domino Speculative Decoding Framework

## Overview

This document defines the data structures used for the benchmark execution, metrics collection, and validation reporting. The data model is designed to be serializable to JSON for CI integration and validation against the `contracts/benchmark_metrics.schema.yaml`.

## Core Entities

### 1. BenchmarkRun
Represents a single execution of the benchmark.

| Field | Type | Description |
|-------|------|-------------|
| `run_id` | string | Unique identifier (UUID) for the run. |
| `timestamp` | string (ISO8601) | Start time of the run. |
| `hardware` | object | Hardware configuration details. |
| `model_config` | object | Model and parameter configuration. |
| `status` | string | `success`, `timeout`, `oom`, `error`. |
| `metrics` | object | Performance metrics (see MetricsArtifact). |
| `logs_path` | string | Path to the raw log file. |

### 2. HardwareConfig
Details of the execution environment.

| Field | Type | Description |
|-------|------|-------------|
| `cpu_cores` | integer | Number of CPU cores (e.g., 2). |
| `ram_gb` | float | Total RAM in GB (e.g., 7.0). |
| `device_type` | string | `cpu` or `gpu`. |
| `cuda_available` | boolean | Always `false` for this project. |

### 3. ModelConfig
Details of the model used.

| Field | Type | Description |
|-------|------|-------------|
| `target_model_name` | string | HuggingFace model ID for the target (e.g., `Qwen/Qwen2-1.8B-Instruct`). **Allowed values**: `Qwen/Qwen2-1.8B-Instruct`, `Qwen/Qwen2-0.5B-Instruct`. |
| `draft_model_name` | string | HuggingFace model ID for the draft (e.g., `Qwen/Qwen2-0.5B-Instruct`). **Allowed values**: `Qwen/Qwen2-0.5B-Instruct`, `Qwen/Qwen2-1.8B-Instruct`. |
| `precision` | string | `float32`, `float16`, `int8`. |
| `device_map` | string | `cpu`, `auto`, `cuda:0`. |
| `prompt_count` | integer | Number of prompts processed per run. |
| `run_count` | integer | Total number of runs aggregated (n=10). |
| `max_new_tokens` | integer | Max tokens generated per prompt. |
| `substitution_log` | string | Log of any model substitution (e.g., "Qwen3 -> Qwen2-1.8B"). |

### 4. MetricsArtifact
The core performance data (matches `contracts/benchmark_metrics.schema.yaml`).

| Field | Type | Description |
|-------|------|-------------|
| `total_latency` | object | Aggregated latency stats: `mean`, `std`, `min`, `max` (ms). |
| `total_tokens` | object | Aggregated token counts: `mean`, `std`, `min`, `max`. |
| `tokens_per_second` | object | Aggregated throughput stats: `mean`, `std`, `min`, `max`. |
| `baseline_latency` | object | Baseline latency stats: `mean`, `std`, `min`, `max` (ms). |
| `domino_latency` | object | Domino latency stats: `mean`, `std`, `min`, `max` (ms). |
| `speedup_ratio` | object | Aggregated speedup stats: `mean`, `std`, `min`, `max`. |
| `acceptance_rate` | object | Aggregated acceptance rate stats: `mean`, `std`, `min`, `max`. |

### 5. ValidationReport
The final human-readable summary.

| Field | Type | Description |
|-------|------|-------------|
| `paper_claimed_speedup` | float | The value from the paper (5.49). |
| `reproduced_speedup_mean` | float | The calculated mean speedup. |
| `confidence_interval_95` | object | Lower and upper bounds of the 95% CI. |
| `pass_fail_status` | string | `PASS`, `FAIL`, `INCONCLUSIVE`. |
| `reasoning` | string | Explanation of the result. |
| `hardware_mismatch_flag` | boolean | True if hardware differs from paper (CPU vs GPU). |

## Data Flow

1. **Input**: `BenchmarkRun` configuration (hardcoded in `src/config/constraints.yaml`).
2. **Process**: `src/benchmark/runner.py` executes the benchmark 10 times, capturing `MetricsArtifact` for each run.
3. **Output**: `MetricsArtifact` is aggregated and serialized to `results_<run_id>.json`.
4. **Validation**: `src/benchmark/report.py` reads the artifact, calculates `speedup_ratio` and 95% CI, and generates `ValidationReport`.
5. **Storage**: Artifacts stored in `external/Domino/results/`.
