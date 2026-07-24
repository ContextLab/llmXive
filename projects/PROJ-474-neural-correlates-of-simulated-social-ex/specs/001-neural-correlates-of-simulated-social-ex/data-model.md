# Data Model: Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

## Overview

This document defines the data structures and schemas used to represent subjects, time-series, connectivity matrices, and statistical results. The model ensures traceability from raw data to final report, adhering to the "Single Source of Truth" principle. All metrics are computed from real data streams; no placeholder or simulated values are permitted.

## Entities

### Subject
Represents a single participant in the study.
- `subject_id`: Unique identifier (string).
- `motion_max`: Maximum displacement in mm (float).
- `qc_status`: "passed" or "failed".
- `conditions`: List of available conditions (e.g., ["Inclusion", "Exclusion"]).

### TimeSeries
Represents the BOLD signal extracted from a specific ROI for a condition.
- `subject_id`: Link to Subject.
- `roi`: Region name (e.g., "PCC", "mPFC", "AngularGyrus").
- `condition`: "Inclusion" or "Exclusion".
- `data`: Array of BOLD signal values (list of floats).
- `tr`: Repetition time (float).

### ConnectivityMatrix
Represents the correlation matrix for a subject and condition.
- `subject_id`: Link to Subject.
- `condition`: "Inclusion" or "Exclusion".
- `nodes`: List of ROI names (ordered).
- `matrix`: 2D array of correlation coefficients.
- `strength_signed`: Mean **signed** correlation across edges (float).
- `strength_absolute`: Mean absolute correlation across edges (float, descriptive only).
- `edges`: Dictionary of individual edge correlation values (e.g., `{"PCC-mPFC": 0.45, ...}).

### Result
Represents the outcome of the statistical test.
- `test_type`: "paired_permutation".
- `metric`: "connectivity_strength_signed".
- `p_value`: Float.
- `effect_size`: Float (e.g., Cohen's d or mean difference).
- `confidence_interval`: [lower, upper] (list of floats).
- `framing`: "associational" or "causal".
- `edge_p_values`: Dictionary of p-values for each edge.
- `edge_p_values_fdr`: Dictionary of FDR-corrected p-values for each edge.
- `sensitivity_curve`: List of {threshold, p_value} objects.

## Data Flow

1.  **Raw**: NIfTI files (OpenNeuro) -> `data/raw/`.
2.  **Processed**: Time-series matrices (Numpy/Parquet) -> `data/processed/timeseries.parquet`.
3.  **Derived**: Connectivity matrices and strength metrics -> `data/processed/connectivity.parquet`.
4.  **Results**: Statistical outputs (JSON/CSV) -> `results/stats.json`.

## Schema Definitions

The following schemas are used for validation in the `contracts/` directory.
