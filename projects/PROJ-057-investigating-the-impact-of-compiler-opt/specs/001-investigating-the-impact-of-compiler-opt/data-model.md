# Data Model: Investigating the Impact of Compiler Optimizations on LLM Inference Latency

## Overview

This document defines the data structures, file formats, and schemas used throughout the project. All data is stored in `data/` and processed in `code/`.

## Entity Definitions

### 1. Kernel Configuration
Represents a unique compilation environment.
-   `config_id`: Unique string (e.g., `gcc-O3-ffast-math-matmul`).
-   `compiler`: String ("gcc" or "clang").
-   `version`: String (e.g., "11.4.0").
-   `optimization_level`: String ("-O0", "-O1", etc.).
-   `flags`: List of strings (e.g., `["-ffast-math", "-march=native"]`).
-   `kernel_type`: String ("matmul", "softmax", "layernorm").
-   `tensor_shape`: List of integers (e.g., `[512, 512]`).
-   `seed`: Integer (42-46, indicating which of the 5 data sets was used).

### 2. Benchmark Run
Represents a single execution of a compiled kernel.
-   `run_id`: UUID.
-   `config_id`: Foreign key to Kernel Configuration.
- `iteration`: Integer (1 to [deferred]).
-   `latency_ns`: Integer (nanoseconds).
-   `status`: String ("success", "nan", "timeout").
-   `seed`: Integer (42-46).

### 3. Stability Result
Represents the comparison between an optimized run and the reference.
-   `result_id`: UUID.
-   `config_id`: Foreign key to Kernel Configuration.
-   `seed`: Integer (42-46).
-   `l2_relative_error`: Float.
-   `max_absolute_diff`: Float.
-   `is_stable`: Boolean (True if error < 1e-5).
-   `reference_checksum`: String (SHA256 of reference output).

### 4. Aggregated Result
Summarized statistics for a configuration (aggregated across seeds and iterations).
-   `config_id`: Foreign key.
-   `median_latency_ns`: Float.
-   `p95_latency_ns`: Float.
-   `cv`: Float (Coefficient of Variation).
-   `mean_l2_error`: Float (Mean across 5 seeds).
-   `max_l2_error`: Float (Maximum across 5 seeds).
-   `max_absolute_diff`: Float (Maximum across 5 seeds).
- `n_iterations`: Integer ([deferred]).
-   `n_blocks`: Integer (100).
-   `stability_pass`: Boolean (True if max_l2_error < 1e-5).
-   `is_frontier`: Boolean (True if this configuration is on the Pareto frontier, calculated on ALL points).

## File Formats

### Raw Logs (JSONL)
Located in `data/intermediates/raw_logs/`.
-   One JSON object per line.
-   Contains `run_id`, `config_id`, `latency_ns`, `status`, `seed`, `iteration`.
-   **Immutability**: This file is hashed as a final snapshot after the experiment completes to ensure reproducibility.

### Aggregated Results (CSV)
Located in `data/results/aggregated.csv`.
-   Columns: `config_id`, `median_latency_ns`, `p95_latency_ns`, `cv`, `mean_l2_error`, `max_l2_error`, `max_absolute_diff`, `stability_pass`, `is_frontier`.

### Pareto Data (JSON)
Located in `data/results/pareto_frontier.json`.
-   List of objects representing points on the frontier (including unstable ones).
-   Includes `config_id`, `latency`, `error`, `is_frontier`, `is_stable`.

### Versioning Manifest
Located in `data/manifest.json`.
-   JSON object mapping file paths to SHA-256 hashes.
-   Keys: `binaries`, `raw_logs` (final snapshot), `aggregated_csv`, `plots`.
-   **Generation**: Hashes are generated **after** the experiment completes on the final run to ensure reproducibility.

## Data Flow

1.  **Generation**: `code/benchmarks/reference.py` generates `reference_output.npy` (high precision) for seeds 42-46.
2.  **Compilation**: `code/benchmarks/compile_runner.py` generates binaries in `data/intermediates/binaries/`.
3. **Execution**: `code/benchmarks/executor.py` runs binaries [deferred] times per config (across 5 seeds), logs `latency` and `output.npy` to `data/intermediates/raw_logs/` and `data/intermediates/outputs/`.
4.  **Stability Check**: `code/analysis/stability_check.py` compares `output.npy` vs `reference_output.npy` for each seed, writes `stability_results.csv`.
5.  **Aggregation**: `code/analysis/stats.py` aggregates logs and stability results into `aggregated.csv`.
6.  **Visualization**: `code/analysis/viz.py` reads `aggregated.csv` to generate plots (including unstable points).
7.  **Hashing**: A script generates `manifest.json` with hashes for all critical artifacts **after the experiment completes**.
