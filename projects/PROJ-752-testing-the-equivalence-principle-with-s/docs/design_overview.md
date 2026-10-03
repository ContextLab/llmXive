# Design Overview

## Architecture

The pipeline is designed as a modular, sequential data processing workflow with explicit separation of concerns:

1. **Ingestion Layer (`code/data/ingestion`)**: Handles external I/O (ILRS API), raw parsing, and initial validation.
2. **Preprocessing Layer (`code/data/preprocessing`)**: Cleans data, handles missing values, and aligns time series.
3. **Dynamics Layer (`code/dynamics`)**: Provides the physical models (forces) required for orbit determination.
4. **Estimation Layer (`code/models/estimator`)**: Implements the mathematical solvers (Least Squares) to fit the models to data.
5. **Analysis Layer (`code/analysis`)**: Computes derived metrics ($\eta$, statistical tests) and generates reports.
6. **CLI Layer (`code/cli`)**: Orchestrates the workflow and enforces resource constraints.

## Methodology

### Primary Approach: Separate Fits
The project prioritizes the "Separate Fits" methodology (T024a) over the Joint Fit.
1. Fit Satellite A independently to get $a_{obs, A}$ and covariance.
2. Fit Satellite B independently to get $a_{obs, B}$ and covariance.
3. Compute anomalous differential acceleration:
 $$ a_{c} = (a_{obs, A} - a_{obs, B}) - (a_{expected, A} - a_{expected, B}) $$
 where $a_{expected}$ are the non-gravitational forces calculated by `force_calculator` (T023e).
4. Derive $\eta$ from $a_c$.

### Secondary Approach: Joint Fit
A joint estimator (T024) is implemented for comparison. It minimizes the stacked residuals of both satellites simultaneously, estimating a shared differential acceleration parameter $a_c$.

## Data Flow

1. **Raw**: `data/raw/*.slr` (Downloaded from ILRS).
2. **Processed**: `data/processed/cleaned_slr_data.csv` (Filtered, aligned).
3. **Results**: `data/results/` (JSON/CSV/PNG artifacts).
4. **Logs**: `data/logs/` (Resource monitoring, step durations).

## Configuration

The system relies on a single source of truth: `config.yaml`.
- **Paths**: Absolute or relative paths for data directories.
- **Hyperparameters**: Cutoffs for residuals, arc lengths, etc.
- **Benchmarks**: `benchmark_values.etvos_limit` is critical for the SC-002 validation (T049).

## Error Handling

- **Data Feasibility**: If a satellite's data is missing or insufficient (<30 days), the system logs a warning, records the exclusion in `excluded_satellites.json`, and proceeds with available data (T018, T009).
- **Convergence**: If the solver fails to converge, the best-fit solution is retained with a warning flag (T027).
- **Resources**: Hard exits on memory/time limits (T038).
