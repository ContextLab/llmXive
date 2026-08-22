# Data Model: llmXive follow-up: extending "Geometric Action Model for Robot Policy Learning"

## Overview

This document defines the data structures for the `llmXive` follow-up project. The primary data artifact is the `trial_log`, which records the outcome of each execution of the symbolic-latent planner and the baseline GAM. The data model is designed to be schema-validated via `contracts/trial_log.schema.yaml` to ensure consistency across runs and reproducibility.

## Entities

### 1. Trial Log

The `trial_log` is the central record for each experimental run. It captures the configuration, execution metrics, and outcome for a single trial.

**Key Fields**:
- `trial_id`: Unique identifier for the trial.
- `topology_config`: JSON object describing the kinematic chain or deformable material used.
- `method`: "symbolic" or "baseline".
- `task_success`: Boolean indicating **external** task completion (PyBullet target check).
- `solver_feasibility`: Boolean indicating if the solver's internal constraints were met (distinct from `task_success`).
- `decoder_reconstruction_error`: MSE of the decoder output vs ground truth (for SC-003).
- `baseline_decoder_error`: MSE of the baseline decoder output vs ground truth (for SC-003 comparison).
- `latency_ms`: Inference time in milliseconds.
- `latent_drift`: Mahalanobis distance of the latent vector from the training distribution.
- `ci_time_limit_exceeded`: Boolean flag if the cumulative time exceeded 6 hours (SC-005).
- `error`: Error message if the trial failed (e.g., "timeout", "infeasible").

### 2. Topology Manifest

A JSON file (`training-topology-manifest.json`) containing hashes of all topology parameters from the original GAM training distribution. Used to verify zero overlap with the generated test set.

### 3. GFM Weights

Pre-trained weights for the Geometric Foundation Model encoder and decoder. Stored in `data/raw/` and loaded as frozen parameters.

## Schema Definition

The `trial_log` schema is defined in `contracts/trial_log.schema.yaml`. This schema is the Single Source of Truth for data validation.

### Validation Rules

- **Data Types**: All numeric fields must be floats or integers. Boolean fields must be true/false.
- **Constraints**: `latency_ms` must be ≥ 0. `task_success` must be a boolean.
- **Required Fields**: `trial_id`, `method`, `task_success`, `solver_feasibility`, `latency_ms`, `topology_config`.
- **Enum Values**: `method` must be one of ["symbolic", "baseline"].

## Data Flow

1. **Generation**: `data/generator.py` creates the synthetic test set and writes it to `data/generated/test_set.json`.
2. **Execution**: `evaluation/runner.py` runs the symbolic and baseline methods, generating a `trial_log` entry for each trial.
3. **Storage**: `trial_log` entries are appended to `data/results/trial_logs.jsonl`.
4. **Analysis**: `evaluation/stats.py` reads `trial_logs.jsonl`, validates against the schema, and computes statistics.

## Assumptions

- The `topology_config` is a JSON-serializable object.
- The `latent_drift` is calculated using the mean and covariance of the training distribution (stored in `data/raw/gfm_stats.json`).
- All data files are stored in UTF-8 encoding.
- **Format**: All logs are JSONL; all configs are JSON. No Parquet is used.

## SC-003 Metric Calculation

To satisfy SC-003, the system must calculate the ratio of `decoder_reconstruction_error` (symbolic) to `baseline_decoder_error` (baseline). The success criterion is that this ratio is ≤ 1.5. This calculation will be performed in the analysis phase and recorded in the final report.