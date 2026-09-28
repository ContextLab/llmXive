# Project Architecture

## Overview

This project implements a modular pipeline for evaluating Differential Privacy (DP) in Federated Learning (FL). The architecture is designed to separate concerns between data handling, training orchestration, and statistical analysis.

## Core Components

### 1. Data Layer (`code/data/`)
- **`download.py`**: Handles fetching the FEMNIST dataset from Hugging Face. Supports streaming to manage memory constraints.
- **`partition.py`**: Implements Dirichlet-based partitioning to simulate client heterogeneity.
- **`checksum_utils.py`**: Ensures data integrity via SHA-256 verification.
- **`generate_partition_metadata.py`**: Creates JSON metadata files describing client label distributions.

### 2. Training Layer (`code/training/`)
- **`fedavg.py`**: Implements the FedAvg algorithm with optional DP noise injection via Opacus.
- **`dp_utils.py`**: Configures DP-SGD parameters (noise multiplier, clipping norm, moments accountant).
- **`logging.py`**: Handles CSV and JSON logging of training metrics (accuracy, loss, privacy budget).
- **`orchestrate_experiment.py`**: Manages the execution of multiple seeds and configurations.
- **`run_experiment_orchestrator.py`**: High-level entry point for the full experiment run.

### 3. Analysis Layer (`code/analysis/`)
- **`stats.py`**: Performs statistical tests (paired t-tests, Mann-Whitney U) and calculates summary statistics.
- **`aggregation.py`**: Consolidates raw logs into filtered datasets.
- **`plots.py`**: Generates visualizations for accuracy gaps and sensitivity analysis.
- **`sensitivity_analysis.py`**: Calculates slope ratios for heterogeneity sensitivity.
- **`generate_summary.py`**: Produces the final validation report and summary CSV.

### 4. Validation Layer (`code/validation/`)
- **`validate_quickstart.py`**: Automated script to verify project setup and reproducibility.

## Data Flow

1. **Ingestion**: `download.py` fetches FEMNIST -> `data/raw/femnist.parquet`.
2. **Partitioning**: `partition.py` splits data -> `data/partitions/partition_*.json`.
3. **Training**: `run_experiment_orchestrator.py` consumes partitions -> `results/raw_logs.csv`.
4. **Filtering**: `aggregation.py` filters logs -> `results/filtered_data.csv`.
5. **Analysis**: `stats.py` and `plots.py` consume filtered data -> `results/summary.csv`, `results/plots/*.png`.
6. **Reporting**: `generate_summary.py` produces `results/validation_report.md`.

## Constraints & Design Decisions

- **Dataset**: Only FEMNIST is supported. Shakespeare is excluded per T000.
- **Privacy**: Opacus is used for DP-SGD implementation.
- **Heterogeneity**: Controlled via Dirichlet $\alpha$ parameter.
- **Reproducibility**: All random seeds are explicitly logged and controlled.
- **Statistical Rigor**: Paired t-tests are prioritized; Mann-Whitney U is a fallback for low seed counts (flagged as `power_reduced`).

## Error Handling

- **Data Fetch Failures**: Retries up to 3 times, then fails loudly with `DataFetchError`.
- **Utility Collapse**: Results with extremely low accuracy or $\epsilon < 0.05$ are flagged and filtered.
- **Timeouts**: Runs exceeding time budgets are flagged as `is_time_limited` and excluded from final metrics.
- **Zero-Sample Clients**: Clients with no samples for a target class are skipped during gradient updates.

## Extensibility

To add a new dataset:
1. Update `code/config.py` to include the new dataset name.
2. Implement a new download function in `code/data/download.py`.
3. Ensure the partitioning logic in `code/data/partition.py` supports the new label structure.
4. Update `README.md` and `docs/CLI_REFERENCE.md`.

Note: Adding Shakespeare is currently blocked by the T000 exclusion constraint until a verified source is identified.
