# Data Model: The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress

## Overview

This document defines the data structures used throughout the pipeline. All data is stored in `data/` with checksums. Derived data is stored in `data/derived/`.

## Entity Definitions

### Subject
A unique participant in the dataset.
-   `subject_id`: String (e.g., "101", "S01").
-   `dataset_source`: String ("WESAD", "OpenNeuro").
-   `has_schandry`: Boolean (True if behavioral task data exists).
-   `has_stress_ecg`: Boolean (True if ECG/PPG during TSST exists).

### Phase
A temporal segment of the experiment.
-   `phase_id`: String ("baseline", "stress", "recovery").
-   `start_time`: Float (seconds from start of recording).
-   `end_time`: Float.
-   `duration_sec`: Float.

### Metric
A derived quantitative value.
-   `metric_id`: String ("RMSSD", "SDNN").
-   `value`: Float.
-   `unit`: String ("ms").
-   `phase`: String (reference to Phase).
-   `subject_id`: String (reference to Subject).

### AuditResult
The output of the data availability scan.
-   `dataset_name`: String.
-   `search_term`: String ("Schandry", "TSST", "heartbeat").
-   `found`: Boolean.
-   `evidence_path`: String (path to `events.tsv` or metadata file).

### FeasibilityMetric
The output of the MDES calculation.
-   `metric_type`: String ("MDES").
-   `outcome_variance`: Float (Total Variance of Stress HRV).
-   `sample_size`: Integer.
-   `assumed_r_squared`: Float (Hypothetical R², e.g., 0.10).
-   `detectable_effect`: Float (Effect size detectable at alpha=0.05, power=0.8).
-   `note`: String ("Calculated based on outcome variance + hypothetical R²; predictor missing").

## Data Flow

1.  **Raw Ingestion**:
    -   WESAD Parquet -> `data/raw/wesad.parquet`
    -   OpenNeuro Metadata (API) -> `data/raw/openneuro_index.json`
2.  **Audit**:
    -   `01_audit_data.py` scans metadata -> `data/audit/audit_results.json`
3.  **Preprocessing (Conditional)**:
    -   If `has_stress_ecg` is True: `02_preprocess_hrv.py` -> `data/derived/hrv_metrics.csv`
4.  **Analysis (Conditional)**:
    -   If `has_schandry` is True: `03_analyze_regression.py` -> `data/derived/regression_results.csv`
    -   If `has_schandry` is False: `03_analyze_regression.py` -> `data/audit/feasibility_report.md` (Contains MDES based on outcome variance + hypothetical R²)
5.  **Versioning**:
    -   `04_update_state.py` hashes all outputs (SHA-256) -> updates `state/projects/...yaml`

## Schema Constraints

-   **No NaNs**: HRV metric columns must be non-null for valid subjects.
-   **Uniqueness**: `subject_id` + `phase` + `metric_id` must be unique.
-   **Range**: RMSSD values must be > 0 and < 2000 ms (physiological sanity check).