# Data Model: Neural Oscillations as a Biomarker for Predicting Response to Transcranial Direct Current Stimulation

## Overview

This document defines the data structures used throughout the pipeline, ensuring compatibility between ingestion, preprocessing, feature extraction, and modeling stages. The model supports both **Primary Mode** (real paired data) and **Fallback Mode** (synthetic targets).

## Core Entities

### 1. Raw EEG Recordings
Represents the raw input data from PhysioNet.
-   **Format**: Parquet (converted to MNE `Raw` objects in memory).
-   **Schema**:
    -   `subject_id`: String (Unique identifier).
    -   `channel`: String (e.g., "C3", "C4", "Cz").
    -   `time`: Float64 (Timestamp in seconds).
    -   `voltage`: Float64 (Microvolts).
    -   `condition`: String (e.g., "rest", "move", "imagery").

### 2. Preprocessed EEG Epochs
Derived data after filtering and re-referencing.
-   **Format**: MNE `Epochs` object (serialized to `.fif` or kept in memory for small batches).
-   **Schema**:
    -   `subject_id`: String.
    -   `epoch_id`: Integer.
    -   `time`: Float64 (Relative to event onset, e.g., -1.0 to 1.0s).
    -   `channel`: String.
    -   `voltage`: Float64 (Filtered, re-referenced).
    -   `bad_channel_flag`: Boolean (True if channel was rejected).

### 3. Feature Vector
Aggregated metrics per subject.
-   **Format**: Pandas DataFrame (Row = Subject, Columns = Features).
-   **Schema**:
    -   `subject_id`: String.
    -   `mode`: Enum (`primary`, `fallback`).
    -   `power_delta`: Float64.
    -   `power_theta`: Float64.
    -   `power_alpha`: Float64.
    -   `power_beta`: Float64.
    -   `power_gamma`: Float64.
    -   `plv_alpha`: Float64 (Average PLV across selected channels).
    -   `wpli_beta`: Float64 (Average wPLI across selected channels).
    -   `tDCS_response`: Float64 (Percentage change in motor score).
        -   *Primary Mode*: Real value from dataset.
        -   *Fallback Mode*: Synthetic value (mean=0, noise=0.5, decoupled).

### 4. Model Output
Results from the regression and validation steps.
-   **Format**: JSON / YAML.
-   **Schema**:
    -   `run_id`: String (UUID).
    -   `mode`: Enum (`primary`, `fallback`).
    -   `adjusted_r2`: Float64.
    -   `permutation_p_value`: Float64.
    -   `coefficients`: Dictionary (Feature name -> Weight).
    -   `fdr_corrected_p_values`: Dictionary (Feature name -> Adjusted p-value).
    -   `sensitivity_sweep`: List of objects (threshold, stability_metric).
    -   `flags`: List of Strings (e.g., "fallback_mode_active", "primary_question_abandoned").

## Data Flow

1.  **Ingestion**: Raw Parquet -> `subject_id`, `channel`, `time`, `voltage`.
2.  **Preprocessing**: Raw -> Filtered (1-45Hz) -> Re-referenced (CAR) -> Epochs.
3.  **Feature Extraction**: Epochs -> Spectral Power (Welch) + Connectivity (PLV/wPLI) -> Feature Vector.
4.  **Modeling**: Feature Vector -> Ridge Regression -> Model Output.
5.  **Validation**: Model Output -> Permutation Test + FDR + Sensitivity Analysis -> Final Report.

## Memory Management Strategy

-   **Subsampling**: If the number of epochs per subject exceeds a threshold (configurable, default 50), random epochs are dropped to fit within 7 GB RAM.
-   **Batching**: Permutation testing is executed in batches to avoid memory spikes.
-   **Garbage Collection**: Explicit `del` and `gc.collect()` calls after each major stage (Preprocessing, Feature Extraction).
