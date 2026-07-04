# Data Model: Evaluating the Impact of Variable Selection on Statistical Power in Linear Regression

## Overview

This document defines the data structures used in the simulation and analysis pipeline. All data is stored in `data/processed/` as CSV or Parquet files, with raw OpenML data in `data/raw/`.

## Entities

### 1. RawDataset
Represents a dataset fetched from OpenML.
- `dataset_id`: Unique OpenML ID (int).
- `dataset_name`: Name of the dataset (str) - *Required for Constitution VI*.
- `n_rows`: Number of rows (int).
- `n_cols`: Number of predictors (int).
- `covariance_matrix`: Path to stored covariance matrix (str).
- `checksum`: SHA-256 hash of the raw file (str).
- `status`: "valid", "skipped" (due to collinearity), or "error".

### 2. SimulationRun
Represents a single simulation instance (one row in the results table).
- `simulation_id`: Unique ID (str or int).
- `dataset_id`: FK to RawDataset (int).
- `dataset_name`: Name of the dataset (str) - *Required for Constitution VI*.
- `snr_level`: Signal-to-Noise Ratio (float).
- `sparsity_level`: Proportion of non-zero coefficients (float).
- `alpha_threshold`: Significance threshold (float).
- `true_coefficients`: Array of true $\beta$ values (list of floats).
- `selected_variables`: List of indices selected by the method (list of int).
- `p_values`: Array of p-values for selected variables (list of float).
- `selection_recovery`: Binary indicator (1 if selected, 0 otherwise) - *Aggregated later*.
- `inference_power`: Binary indicator (1 if selected AND p < alpha, 0 otherwise) - *Aggregated later*.
- `method`: "Forward", "Backward", "LASSO" (str).
- `seed`: Random seed used (int).

### 3. PowerMetric
Aggregated power rate for a specific condition.
- `dataset_id`: FK to RawDataset (int).
- `dataset_name`: Name of the dataset (str).
- `snr_level`: (float).
- `sparsity_level`: (float).
- `alpha_threshold`: (float).
- `method`: (str).
- `empirical_power`: Mean Inference Power rate (float).
- `selection_recovery_rate`: Mean Selection Recovery rate (float).
- `ci_lower`: Lower bound of 95% CI (float).
- `ci_upper`: Upper bound of 95% CI (float).
- `n_sims`: Number of simulations (int).

### 4. DiagnosticRecord
Collinearity and other diagnostics.
- `dataset_id`: FK to RawDataset (int).
- `dataset_name`: Name of the dataset (str).
- `condition_number`: (float).
- `max_vif`: Maximum VIF among predictors (float).
- `timestamp`: Timestamp of calculation (datetime).

## File Structure

```text
data/
├── raw/
│   ├── dataset_<id>.csv           # Raw OpenML dump
│   └── dataset_<id>.cov.npy       # Covariance matrix
├── processed/
│   ├── simulation_results.csv     # All SimulationRun records (includes dataset_name)
│   ├── power_metrics.csv          # All PowerMetric records
│   └── diagnostics.csv            # All DiagnosticRecord records (mandatory for all datasets)
└── artifacts/
    └── checksums.json             # SHA-256 hashes for raw files
```

## Relationships

- `RawDataset` (1) ──< `SimulationRun` (Many)
- `SimulationRun` (Many) ──> `PowerMetric` (1) [Aggregated]
- `RawDataset` (1) ──> `DiagnosticRecord` (1)

## Constraints

- **RawDataset**: Must have ≥100 rows, ≥3 predictors.
- **SimulationRun**: `true_coefficients` must match `sparsity_level` in count of non-zeros.
- **PowerMetric**: `empirical_power` must be between 0 and 1.
- **Diagnostics**: `condition_number` must be < 10^10 for valid datasets. **Mandatory**: Every valid dataset must have a record in `diagnostics.csv`.
