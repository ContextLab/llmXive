# Data Model: Assessing the Impact of Data Ordering on Bootstrapping Results

## Overview
This document defines the data structures, schemas, and storage formats for the simulation and analysis pipeline. All data is stored in `data/` (raw/processed) and `results/` (aggregated metrics).

## Entity Definitions

### 1. TimeSeries (Synthetic)
Represents a generated AR(1) process.
- `id`: Unique string identifier (e.g., `syn_phi0.5_N100_trial001`).
- `phi`: Float, autoregressive coefficient.
- `n`: Integer, sample size.
- `values`: List of floats, the time series data.
- `theoretical_mean`: Float (always 0).
- `seed`: Integer, random seed used for generation.

### 2. BootstrapResult
Represents the outcome of a single bootstrap run.
- `series_id`: Reference to TimeSeries.
- `condition`: Enum (`ordered`, `shuffled`).
- `ci_lower`: Float, lower bound of 95% CI.
- `ci_upper`: Float, upper bound of 95% CI.
- `covered`: Boolean, true if `theoretical_mean` $\in$ [ci_lower, ci_upper].
- `ci_width`: Float, `ci_upper - ci_lower`.

### 3. SimulationBatch
Aggregated results for a specific configuration.
- `phi`: Float.
- `n`: Integer.
- `condition`: Enum (`ordered`, `shuffled`).
- `total_trials`: Integer ([deferred]).
- `covered_count`: Integer.
- `coverage_probability`: Float (ratio).
- `mcnemar_p_value`: Float (from McNemar's test, if applicable).
- `mcnemar_statistic`: Float (from McNemar's test).

### 4. DataSegment (Real-World - BLOCKED)
*This entity is defined for completeness but will not be populated.*
- `segment_id`: String.
- `start_index`: Integer.
- `end_index`: Integer.
- `phi_est`: Float, estimated AR(1) coefficient.
- `status`: Enum (`valid`, `skipped`).
- `skip_reason`: String (e.g., `insufficient_data`).

## Storage Formats

### Raw Data
- **Synthetic**: Generated in-memory, no persistent raw file.
- **UCI Power**: **BLOCKED** (No verified source).

### Processed Data
- **Segments**: **BLOCKED**.

### Results
- **Metrics**: `results/coverage_metrics.csv`.
  - Columns: `phi`, `n`, `condition`, `coverage_prob`, `mcnemar_p_value`, `mcnemar_statistic`, `ci_width_mean`.
- **Logs**: `results/simulation_logs.json`. Detailed per-trial logs for debugging.

## Data Flow
1.  **Generate**: `data_generation.py` creates `TimeSeries` objects.
2.  **Bootstrap**: `bootstrap_engine.py` consumes `TimeSeries` and produces `BootstrapResult`.
3.  **Aggregate**: `metrics.py` aggregates `BootstrapResult` into `SimulationBatch`.
4.  **Real-World**: **SKIPPED**.
5.  **Final Output**: `runner.py` writes `coverage_metrics.csv`.