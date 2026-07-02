# Data Model: Investigating the Relationship Between Brain Network Dynamics and Subjective Time Perception

## Overview

This document defines the data structures, schemas, and flow for the project. All data is stored in `data/` and validated against the schemas in `contracts/`.

## Entity Definitions

### 1. Subject
Represents a single participant.
- **Attributes**: `subject_id` (str), `dsst_score` (float or null), `qc_motion` (float), `excluded` (bool).
- **Source**: `data/raw/behavioral.csv` (from verified HCP sources).

### 2. PreprocessedFmri
Represents the cleaned fMRI time-series for a subject.
- **Attributes**: `subject_id` (str), `file_path` (str or null), `n_timepoints` (int or null), `n_parcels` (int or null), `qc_passed` (bool).
- **Source**: `data/processed/preprocessed/` (or null if preprocessing skipped due to missing data).
- **Note**: `file_path` is **optional** (can be null) if the subject was excluded due to missing raw data or preprocessing failure. If real fMRI data is missing, this entity is not created or is marked as null.

### 3. ConnectivityMatrix
A time-varying functional connectivity matrix.
- **Attributes**: `subject_id` (str), `window_start` (int), `window_end` (int), `matrix` (list of lists of float).
- **Source**: `code/metrics.py` (Sliding window).

### 4. ReconfigurabilityMetric
The primary predictor variable.
- **Attributes**: `subject_id` (str), `transition_count` (int), `community_labels` (list of int), `algorithm_seed` (int).
- **Source**: `code/metrics.py` (Louvain community detection).

### 5. CorrelationResult
The output of the statistical analysis.
- **Attributes**: `metric_name` (str), `behavior_name` (str), `rho` (float), `p_value` (float), `p_adjusted` (float), `effect_size` (float), `significant` (bool).
- **Source**: `code/analysis.py`.

## Data Flow

1.  **Ingest**: `download.py` fetches data from verified URLs -> `data/raw/`. **Verification Step**: Check if files contain required data types. If not, log "Data Gap" and halt.
2.  **Preprocess**: `preprocess.py` (fMRIPrep) -> `data/processed/fmri/`. **Constraint**: Skipped if real data is missing.
3.  **Metric Computation**: `metrics.py` reads preprocessed data -> `data/processed/metrics/`. **Constraint**: Skipped if preprocessing failed.
4.  **Analysis**: `analysis.py` reads metrics and behavioral data -> `data/results/`. **Constraint**: Skipped if metrics are missing.
5.  **Visualization**: `viz.py` reads results -> `data/results/plots/`.

## Storage Constraints

- **Max RAM**: 7 GB. Data subsets (a limited number of subjects) used for testing.
- **Max Disk**: 14 GB. Raw data not committed; only checksums and small derived files.
- **Format**: Parquet/CSV for tabular data; NIfTI for fMRI (if available); JSON for metrics; **TSV** for analysis results (per Constitution VII).

## Output File Standardization
- **Analysis Results**: `data/analysis_results.tsv` (Tab-Separated Values) to align with Constitution Principle VII (Single Source of Truth).
- **Plots**: `data/results/plots/` (PNG).
- **Logs**: `data/preprocess_log.txt`.