# Data Model: llmXive Follow-up: Extending Asynchronous RL Staleness Bounds for Low-Capacity Models

## Overview

This document defines the data structures, schemas, and flow for the `llmXive` staleness scaling experiment. The data model is designed to support reproducibility, deterministic execution, and statistical analysis.

## Entities

### 1. TrainingRun
Represents a single execution of the RL loop.
- **Attributes**:
  - `run_id`: Unique identifier (UUID).
  - `model_id`: String (e.g., "microsoft/phi-2", "Qwen/Qwen1.5-1.8B").
  - `staleness_level`: Integer (0, 10, or adaptive).
  - `seed`: Integer (1-5).
  - `convergence_status`: Enum (`STABLE`, `DIVERGED`, `INCOMPLETE`).
  - `divergence_point`: Integer (step number where divergence occurred, or `null`).
  - `final_reward`: Float.
  - `final_gradient_norm`: Float.
  - `start_time`: ISO 8601 timestamp.
  - `end_time`: ISO 8601 timestamp.
  - `memory_peak_mb`: Integer.

### 2. StalenessQueue
Internal buffer for delayed gradients.
- **Attributes**:
  - `max_size`: Integer (buffer capacity).
  - `current_delay`: Integer (current staleness value).
  - `queue_state`: List of gradient snapshots (internal, not persisted).

### 3. ConvergenceMetric
Derived value for stability analysis.
- **Attributes**:
  - `window_size`: Integer (50).
  - `reward_variance`: Float.
  - `gradient_norm_variance`: Float.
  - `is_stable`: Boolean.

### 4. BaselineManifest
Pre-computed artifact for benchmarking (not divergence definition).
- **Attributes**:
  - `model_id`: String.
  - `seed`: Integer.
  - `mean_reward_baseline`: Float (mean of first 50 steps of synchronous run).
  - `mean_gradient_norm_baseline`: Float.
  - `variance_reward_baseline`: Float.
  - `variance_gradient_norm_baseline`: Float.
  - `generated_at`: ISO 8601 timestamp.
  - `checksum`: String (SHA-256 of the run log used to generate it).
  - `stability_status`: String (`STABLE`, `UNSTABLE`) - **All statuses are recorded, none discarded.**

## Data Flow

1.  **Ingestion**: GSM8K dataset is downloaded from HuggingFace and cached in `data/raw/`.
2.  **Baseline Generation**:
    -   Run synchronous training (`staleness=0`) for each seed.
    -   Compute `BaselineManifest` for each seed.
    -   **Record stability status** (stable/unstable) but **do not discard** unstable seeds.
3.  **Experimental Runs**:
    -   Load `BaselineManifest` (for logging only).
    -   Run asynchronous training with specified `staleness_level`.
    -   Monitor metrics against **intrinsic thresholds**.
    -   Log `TrainingRun` data to `data/processed/run_logs/`.
4.  **Aggregation**:
    -   Collect all `TrainingRun` records.
    -   Compute summary statistics (mean, variance) per regime.
    -   Perform **Survival Analysis (Kaplan-Meier)** and **Log-Rank test**.
    -   Perform **Levene's test** and **t-test** (secondary).
    -   Generate `data/processed/summary_results.json`.
5.  **Figure Generation**:
    -   Run `generate_plots.py` to programmatically create all figures from `data/processed/` logs. **This ensures the Single Source of Truth principle.**

## Storage Layout

```text
data/
├── raw/
│   ├── gsm8k_test.parquet          # Downloaded dataset (checksummed)
│   └── checksums.txt               # SHA-256 hashes
├── processed/
│   ├── manifests/
│   │   ├── phi2_seed_1_manifest.json
│   │   ├── phi2_seed_2_manifest.json
│   │   └── ...
│   ├── run_logs/
│   │   ├── run_001_phi2_staleness_10_seed_1.json
│   │   └── ...
│   └── summary_results.json        # Aggregated stats, t-test results, survival analysis
└── artifacts/
    ├── convergence_plots.png
    ├── survival_curves.png
    └── staleness_threshold_map.csv
```

## Schema Constraints

-   **Seeds**: Must be unique per model/regime combination.
-   **Manifests**: Must be generated *before* any asynchronous run for the same seed.
-   **Logs**: Must be append-only; no modification of existing logs.
-   **Checksums**: All raw data files must have a corresponding entry in `checksums.txt`.
-   **Figures**: Must be generated programmatically from `data/processed/` logs.

## Versioning

-   **Data Version**: 1.0.0 (Initial schema definition).
-   **Manifest Version**: 1.0.0.
-   **Log Version**: 1.0.0.

Any change to the schema requires a new version number and a migration script in `code/utils/migrate_data.py`.