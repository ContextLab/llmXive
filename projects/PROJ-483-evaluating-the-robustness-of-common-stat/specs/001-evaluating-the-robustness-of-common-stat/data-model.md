# Data Model: Evaluating the Robustness of Common Statistical Tests to Non-Independence in Public Datasets

## Overview
This document defines the data structures used to load, process, and store simulation results. The model is designed for efficiency (CSV/Parquet) and traceability (checksums).

## Entities

### 1. DatasetMetadata
Stores information about the source dataset.
- `dataset_id`: Unique identifier (e.g., `uci_har_test`)
- `source_url`: Verified URL from the input block.
- `file_path`: Relative path in `data/raw/`.
- `checksum`: SHA-256 hash of the raw file.
- `sample_size`: Number of rows after initial cleaning/sampling.
- `variable_types`: Dictionary mapping variable names to types (`continuous`, `categorical`).

### 2. DependencyConfiguration
Defines the specific non-independence structure injected.
- `config_id`: Unique identifier (e.g., `ar1_r0.3`)
- `structure_type`: Enum (`temporal`, `hierarchical`, `spatial`)
- `strength`: Float (e.g., `0.3`)
- `method_params`: Dictionary of method-specific parameters (e.g., `{"block_size": 5}` for hierarchical).

### 3. SimulationRun
Tracks a single execution of the Monte Carlo loop.
- `run_id`: UUID
- `dataset_id`: FK to `DatasetMetadata`
- `test_type`: Enum (`t_test`, `anova`, `chi_squared`)
- `dependency_config_id`: FK to `DependencyConfiguration`
- `null_hypothesis`: Boolean (True for Type I error, False for Power)
- `replications`: Integer (Target [deferred])
- `seed`: Integer (Random seed used)
- `start_time`, `end_time`: Timestamps.
- `generation_method`: Enum (`synthetic`, `real`) - Indicates if data was generated from scratch (for Type I error) or sampled from real data (for Power).

### 4. SimulationResult
Aggregated metrics for a `SimulationRun`.
- `result_id`: UUID
- `run_id`: FK to `SimulationRun`
- `observed_alpha`: Float (Observed Type I error rate or Power).
- `lower_ci_95`: Float (Clopper-Pearson lower bound).
- `upper_ci_95`: Float (Clopper-Pearson upper bound).
- `logistic_model_coeffs`: JSON (Coefficients from logistic regression of p-value ~ dependency strength).
- `raw_p_values_path`: Path to the file containing individual p-values for this run (optional, for debugging).

## Data Flow

1.  **Ingestion**: Raw data downloaded from verified URLs → `data/raw/` → Checksummed → `DatasetMetadata` created.
2.  **Preprocessing**: Data cleaned, sampled if necessary, split into features/labels → `data/processed/`.
3.  **Generation**: For Type I error, synthetic independent data is generated (`generation_method=synthetic`). For Power, real data is used (`generation_method=real`).
4.  **Injection**: `DependencyConfiguration` applied to generated or real data → New files created (no overwrite).
5.  **Simulation**: `SimulationRun` executes on injected data → Individual p-values generated.
6.  **Aggregation**: P-values aggregated into `SimulationResult` → Saved to `results/aggregated.csv` and `results/` directory.
7.  **Visualization**: `SimulationResult` used to generate plots in `results/plots/`.

## Constraints & Validation

-   **No PII**: All datasets are public; no personal identifiers expected, but a PII scan is run on ingestion.
-   **Immutability**: Once a file is written to `data/raw/` or `data/processed/`, it is never modified. New versions are written with new filenames.
-   **Schema Enforcement**: All output files must match the schemas defined in `contracts/`.