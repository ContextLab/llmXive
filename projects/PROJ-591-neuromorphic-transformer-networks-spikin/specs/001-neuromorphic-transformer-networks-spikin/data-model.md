# Data Model: Neuromorphic Transformer Networks

## Overview

This document defines the data structures, schemas, and storage formats for the project. All data artifacts are versioned and checksummed.

## Entity Definitions

### 1. TrainingRun
Represents a single execution of a model (baseline or spiking) with a specific seed.
- **Fields**:
  - `run_id`: Unique identifier (e.g., `baseline_seed_01`).
  - `model_type`: Enum (`baseline`, `spiking`).
  - `seed`: Integer.
  - `start_time`: ISO 8601 timestamp.
  - `end_time`: ISO 8601 timestamp.
  - `status`: Enum (`completed`, `failed`, `early_stopped`).
  - `config_hash`: SHA-256 of the hyperparameter configuration.

### 2. MetricRecord
Contains metrics for a single epoch of a training run.
- **Fields**:
  - `run_id`: FK to `TrainingRun`.
  - `epoch`: Integer (1-based).
  - `train_loss`: Float.
  - `val_loss`: Float.
  - `val_perplexity`: Float.
  - `energy_kWh`: Float (or null if estimated).
  - `energy_per_token_kWh`: Float.
  - `wall_clock_time_seconds`: Float.
  - `is_estimated_energy`: Boolean (True if codecarbon failed or fallback used).
  - `spike_metrics`: JSON (for spiking models only).
    - `isi_variance`: Float.
    - `bits_per_spike`: Float.
    - `synchrony_score`: Float.

### 3. StatisticalComparison
Aggregates results across seeds for hypothesis testing.
- **Fields**:
  - `comparison_id`: Unique identifier.
  - `metric_name`: Enum (`perplexity`, `energy_per_token`).
  - `baseline_mean`: Float.
  - `spiking_mean`: Float.
  - `t_statistic`: Float.
  - `p_value_raw`: Float.
  - `p_value_corrected`: Float (Bonferroni/Holm).
  - `confidence_interval_lower`: Float.
  - `confidence_interval_upper`: Float.
  - `threshold_stability`: JSON (thresholds vs significance status).
    - `thresholds`: List of floats (e.g., [0.20, 0.25, 0.30, 0.35]).
    - `results`: List of objects with `threshold`, `is_significant` (boolean), and `p_value`.

## File Formats

### CSV: `data/energy_logs/training_metrics.csv`
Columns: `run_id, model_type, seed, epoch, val_perplexity, energy_per_token_kWh, wall_clock_time_seconds, is_estimated_energy, isi_variance, bits_per_spike, synchrony_score`
*Note: `is_estimated_energy` is explicitly included to flag fallback to wall-clock time.*

### CSV: `data/energy_logs/statistical_results.csv`
Columns: `comparison_id, metric_name, baseline_mean, spiking_mean, t_statistic, p_value_raw, p_value_corrected, ci_lower, ci_upper`

### JSON: `data/energy_logs/sensitivity_analysis.json`
Structure:
```json
{
  "thresholds": [0.20, 0.25, 0.30, 0.35],
  "results": [
    { "threshold": 0.20, "is_significant": true, "p_value": 0.04 },
    { "threshold": 0.25, "is_significant": false, "p_value": 0.12 },
    ...
  ]
}
```
*Note: This structure replaces the previous FPR/FNR model with a Threshold Stability model.*

## Data Hygiene Rules

1. **Checksums**: Every file in `data/` must have a corresponding `.sha256` checksum file.
2. **Immutability**: Raw data (downloaded WikiText) is never modified. Processed data is written to new files (e.g., `wiki_tokenized_v1.parquet`).
3. **PII**: No personally identifiable information is allowed in `data/`.
4. **Versioning**: All artifacts in `state/` must reference the content hash of the corresponding data files.