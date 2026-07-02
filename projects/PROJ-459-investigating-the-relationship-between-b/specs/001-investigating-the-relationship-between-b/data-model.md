# Data Model: Investigating the Relationship Between Brain Network Dynamics and Musical Genre Preference

## 1. Overview

This document defines the data structures, schemas, and flow for the project. It ensures alignment between the ingestion, processing, and analysis phases, adhering to the "Single Source of Truth" principle.

## 2. Core Entities

### Subject
Represents a single participant.
- `subject_id`: Unique string (e.g., `sub-001`).
- `demographics`: Dict (Age, Sex, etc. - if available).
- `musical_preference`: Dict of genre scores (e.g., `{"classical": 5.0, "rock": 2.0}`).
- `stomp_r_score`: Float (if available, fallback).
- `exclusion_reason`: String (e.g., `FD > 0.5mm`, `Missing Data`, `Underpowered`, `None`).
- `mean_fd`: Float (mean Framewise Displacement, used as a covariate).

### TimeSeries
The BOLD signal for a specific ROI.
- `subject_id`: String.
- `roi_id`: Integer (1-400).
- `timepoints`: List of floats (BOLD signal values, motion-regressed).
- `metadata`: Dict (TR, acquisition parameters).

### NetworkMetric
Derived graph-theoretic measures.
- `subject_id`: String.
- `network_type`: String (e.g., `DMN`, `Auditory`, `Salience`, `Global`).
- `metric_name`: String (e.g., `global_efficiency`, `modularity_Q`, `dynamic_reconfiguration_rate`).
- `value`: Float.
- `window_size`: Integer (only for dynamic metrics).

### CorrelationResult
Statistical relationship between a metric and a genre.
- `metric_name`: String.
- `network_type`: String.
- `genre`: String.
- `spearman_r`: Float.
- `p_raw`: Float.
- `p_adjusted`: Float (BH corrected).
- `is_significant`: Boolean (True if `p_adjusted < 0.05`).

### SensitivityReport
Stability of dynamic metrics across window sizes.
- `metric_name`: String.
- `window_sizes`: List of Integers (e.g., `[20, 30, 40]`).
- `icc_value`: Float.
- `is_stable`: Boolean (True if `icc >= 0.7`).

## 3. File Formats & Paths

| Artifact | Path | Format | Description |
| :--- | :--- | :--- | :--- |
| Raw Data | `data/raw/openneuro/` | BIDS | Downloaded fMRI and metadata. |
| Preprocessed | `data/processed/fmriprep/` | NIfTI/TSV | fMRIPrep outputs. |
| Time Courses | `data/derived/timeseries/` | HDF5/Parquet | 400-ROI time series per subject (motion-regressed). |
| Metrics CSV | `data/derived/metrics.csv` | CSV | Aggregated static/dynamic metrics. |
| Results CSV | `data/derived/correlations.csv` | CSV | Correlation results with p-values. |
| Figures | `data/derived/figures/` | PNG/PDF | Heatmaps, network diagrams. |
| Checksums | `data/checksums.json` | JSON | SHA256 hashes of all data files. |

## 4. Data Flow

1.  **Ingestion**: `data/download.py` fetches data to `data/raw/`.
2.  **Validation**: `data/validate.py` checks for `musical_preference`/`STOMP-R` and N≥85. If missing, `ERR_DATA_MISSING` or `ERR_UNDERPOWERED`.
3.  **Preprocessing**: `data/preprocess.py` runs fMRIPrep, outputs to `data/processed/`.
4.  **Extraction**: `analysis/metrics.py` (part 1) extracts time courses to `data/derived/timeseries/`.
5.  **Motion Regression**: Time series are regressed for FD/DVARS before metric calculation.
6.  **Metric Calc**: `analysis/metrics.py` (part 2) computes static/dynamic metrics, writes `metrics.csv`.
7.  **Analysis**: `analysis/stats.py` computes correlations, writes `correlations.csv`.
8.  **Viz**: `analysis/viz.py` reads `correlations.csv` to generate figures.

## 5. Constraints & Rules

- **No In-Place Modification**: Raw data is never changed. All transformations create new files.
- **Schema Enforcement**: All CSVs must match the schemas defined in `contracts/`.
- **Missing Values**: If a subject has >10% missing data, they are excluded and logged.
- **Precision**: All floating-point metrics stored with 6 decimal places.
- **Motion Control**: All dynamic metrics must be calculated on motion-regressed time series.