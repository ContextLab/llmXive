# System Architecture

## Overview

The `llmXive` pipeline for investigating neural correlates of predictive coding errors is designed as a modular, linear workflow. Each stage reads from the previous stage's output and writes to a new artifact, ensuring reproducibility and traceability.

## Component Interaction

```mermaid
graph TD
 A[Raw Data (OpenNeuro)] -->|download.py| B(data/raw)
 B -->|preprocess.py| C(data/processed/epo_clean.fif)
 C -->|extract.py| D(results/metrics.csv)
 D -->|stats.py| E(results/statistics.json)
 D -->|viz.py| F(results/plots)
 C -->|viz.py| F
```

### Module Responsibilities

1. **`download.py`**:
 - Handles network I/O.
 - Implements retry logic and checksum verification.
 - Does not depend on other code modules except `config_loader`.

2. **`preprocess.py`**:
 - Heavy computation (filtering, ICA).
 - Uses `mne` for EEG manipulation.
 - Outputs intermediate (epo_raw) and final (epo_clean) FIF files.
 - Generates rejection logs for quality control.

3. **`extract.py`**:
 - Reads FIF files.
 - Computes statistical aggregates (mean ERPs, difference waves).
 - Outputs a tabular CSV for downstream analysis.

4. **`stats.py`**:
 - Pure statistical logic.
 - Reads CSV, performs hypothesis testing.
 - Outputs JSON summary.

5. **`viz.py`**:
 - Reads CSV and FIF files.
 - Generates PNG images.
 - Stateless with respect to calculation.

## Data Flow

- **Raw Data**: BIDS-formatted EEG data from OpenNeuro.
- **Processed Data**: `.fif` files containing epochs.
- **Metrics**: `results/metrics.csv` (one row per participant).
- **Statistics**: `results/statistics.json` (aggregated results).
- **Visuals**: PNG files in `results/plots/`.

## Error Handling Strategy

- **Fail Loudly**: If data download fails, the script exits immediately.
- **No Synthetic Fallbacks**: The pipeline never generates fake data to bypass failures.
- **Logging**: All steps log to `code/logs/` with timestamps and severity levels.

## Configuration Management

- Centralized in `code/config.yaml`.
- Accessed via `config_loader.get_config()`.
- Environment variables (e.g., `OPENNEURO_API_KEY`) handled by `env_manager`.

## Scalability Considerations

- **Memory**: ICA and permutation tests are the most memory-intensive steps.
- **Parallelism**: Subject-level processing can be parallelized (not yet implemented in this MVP).
- **Streaming**: Large datasets are processed in chunks where possible.