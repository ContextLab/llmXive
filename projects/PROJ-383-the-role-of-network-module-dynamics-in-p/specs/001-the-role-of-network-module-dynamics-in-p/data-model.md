# Data Model: Network Module Dynamics in Predicting Working Memory

## Overview

This document defines the data structures, schemas, and transformations used in the project. It ensures consistency between ingestion, processing, analysis, and reporting.

## Entities

### Subject
- **ID**: Unique identifier (string, e.g., "100106").
- **RestingStateTimeSeries**: 2D array (Time x Regions), shape (T, R).
- **MotionParameters**: 2D array (Time x 6), shape (T, 6).
- **FramewiseDisplacement**: 1D array (Time,), shape (T,).
- **WorkingMemoryScore**: Scalar (float), 2-back accuracy.
- **MeanFD**: Scalar (float), average FD across time.
- **FlexibilityScore**: Scalar (float), [0, 1].
- **MotionPCs**: 2D array (Time x 5), top 5 principal components of motion parameters.

### WindowedConnectivity (Supra-Graph)
- **WindowID**: Integer index of the window.
- **StartTime**: Float, start time in seconds.
- **EndTime**: Float, end time in seconds.
- **ConnectivityMatrix**: 2D array (Regions x Regions).
- **CommunityAssignments**: 1D array (Regions,), community label per node (from MMO).

### AnalysisResult
- **SubjectID**: String.
- **WindowLength**: Integer (30, 60, 90).
- **FlexibilityScore**: Float.
- **MeanFD**: Float.
- **WorkingMemoryScore**: Float.
- **PartialCorrelation**: Float (rho).
- **PermutationPValue**: Float.
- **Significant**: Boolean (p < 0.0167).
- **MotionStratum**: String ("Low" or "High").

## File Formats

### Input: Raw fMRI (NIfTI/Parquet)
- Stored in `data/raw_fmri/`.
- Format: NIfTI or Parquet (if HCP provides).
- **Constraint**: Must be checksummed.

### Input: Behavioral Logs (CSV/JSON)
- Stored in `data/raw_behavior/`.
- Format: CSV with columns: `subject_id`, `task`, `accuracy`, `reaction_time`.

### Intermediate: Cleaned Time Series (Parquet)
- Path: `data/processed/cleaned_timeseries.parquet`.
- Columns: `subject_id`, `time_series` (list of lists or array), `motion_params`, `fd`, `mean_fd`, `motion_pcs`.
- **Constraint**: Excluded subjects (mean FD > 0.2) are not present.

### Intermediate: Flexibility Scores (Parquet)
- Path: `data/processed/flexibility_scores.parquet`.
- Columns: `subject_id`, `window_length`, `flexibility_score`, `num_windows`, `num_nodes`.

### Output: Results (Parquet/CSV)
- Path: `data/results/correlation_results.parquet`.
- Columns: `window_length`, `rho`, `p_value_raw`, `p_value_perm`, `significant`, `sensitivity_stable`, `motion_stratum`.

## Transformations

1. **Raw to Cleaned**:
   - Input: Raw fMRI + Motion Params.
   - Process: Scrub high-FD volumes, OLS regression.
   - Output: Cleaned time series, residual motion params, motion PCs.
2. **Cleaned to Flexibility**:
   - Input: Cleaned time series.
   - Process: Construct supra-graph, Multilayer Modularity Optimization (MMO), Flexibility calculation.
   - Output: Flexibility score per subject per window length.
3. **Flexibility to Results**:
   - Input: Flexibility scores + WM scores + Motion PCs.
   - Process: Partial Spearman (controlling for Motion PCs), Permutation, Sensitivity, Motion Stratification.
   - Output: Correlation statistics.
