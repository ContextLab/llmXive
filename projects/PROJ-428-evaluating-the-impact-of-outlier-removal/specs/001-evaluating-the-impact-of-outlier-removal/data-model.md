# Data Model: Evaluating the Impact of Outlier Removal Methods on Variance Estimation

## Overview

This document defines the data structures used throughout the simulation pipeline. All data flows from `data_generator` to `outlier_removal`, then to `metrics`, and finally aggregates into `analysis` results.

## Entities

### 1. Dataset
Represents a source of data, either a real UCI dataset (loaded for properties) or a synthetic generation configuration.

-   **Attributes**:
    -   `dataset_id`: Unique identifier (e.g., `uci_har`, `synthetic_normal_01`).
    -   `source`: URL or `synthetic`.
    -   `distribution_type`: One of `normal`, `lognormal`, `exponential`, `beta`, `gamma`.
    -   `parameters`: Dictionary of generation parameters (mean, std, shape, etc.).
    -   `continuous_vars`: List of column names identified as continuous.

### 2. ContaminationProfile
Defines the specific experimental condition regarding outlier injection.

-   **Attributes**:
    -   `profile_id`: Unique identifier.
    -   `contamination_rate`: Float (0.0 to 1.0).
    -   `outlier_magnitude`: Float (multiplier for injected values).
    -   `seed`: Integer for reproducibility.

### 3. RemovalMethod
Defines the strategy applied to the contaminated data.

-   **Attributes**:
    -   `method_name`: One of `iqr`, `winsorize`, `trim`.
    -   `parameters`: Dictionary (e.g., `iqr_multiplier`, `winsorize_percentiles`, `trim_percent`).

### 4. EstimationResult
The output of a single Monte Carlo replicate.

-   **Attributes**:
    -   `run_id`: Unique integer.
    -   `dataset_id`: Reference to Dataset.
    -   `contamination_rate`: Float.
    -   `distribution_type`: String.
    -   `method_name`: String.
    -   `true_variance`: Float (Ground truth theoretical parameter of the underlying distribution).
    -   `estimated_variance`: Float (After removal).
    -   `bias`: Float.
    -   `mse`: Float.
    -   `n_original`: Integer.
    -   `n_remaining`: Integer.

## Data Flow

1.  **Generation**: `data_generator` creates a `Dataset` and applies a `ContaminationProfile` to produce a contaminated DataFrame.
2.  **Processing**: `outlier_removal` applies a `RemovalMethod` to the DataFrame.
3.  **Metrics**: `metrics` calculates `true_variance` (theoretical parameter), `estimated_variance`, `bias`, and `mse`, producing an `EstimationResult`.
4.  **Aggregation**: Results are appended to a master CSV/Parquet file for `analysis`.

## Constraints

-   All floating-point values must be finite (no NaN/Inf).
-   `contamination_rate` must be in $[0, 1]$.
-   `bias` and `mse` are derived fields, not stored in raw input files.
-   `true_variance` must be the theoretical variance of the distribution used for generation, not the sample variance of the pre-contamination data.