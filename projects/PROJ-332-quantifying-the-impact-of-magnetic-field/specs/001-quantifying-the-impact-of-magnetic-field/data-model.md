# Data Model: Quantifying the Impact of Magnetic Field Topology on Plasma Confinement

## Overview

This document defines the data structures used throughout the pipeline, from raw retrieval to final analysis. All data must conform to the schemas defined in `contracts/`.

## Entity Definitions

### Discharge
A single tokamak shot. Represents the atomic unit of analysis.
- **Attributes**:
  - `discharge_id`: Integer. Unique identifier for the shot (e.g., 154321).
  - `time`: Float. Time in seconds (optional, for time-series context, but analysis uses scalar aggregates).
  - `status`: String. "valid", "excluded_missing_island", "excluded_missing_tau", "excluded_outlier".

### TopologicalMetric
Derived scalar values describing the magnetic topology of a discharge.
- **Attributes**:
  - `island_width`: Float. Width of the primary magnetic island in meters. Derived or retrieved.
  - `resonant_surface_density`: Float. Count of rational surfaces ($q=m/n$) per unit normalized minor radius. **Note**: This is a descriptive statistic only, not an independent predictor.
  - `q_min`: Float. Minimum safety factor in the plasma.
  - `q_max`: Float. Maximum safety factor in the plasma.
  - `collinear_flag`: Boolean. True if `resonant_surface_density` is collinear with `q_max - q_min` (always true by definition, but included for schema completeness).

### ConfinementMetric
Derived scalar values describing plasma confinement.
- **Attributes**:
  - `tau_e`: Float. Energy confinement time in seconds.
  - `h98y2`: Float. Normalized confinement enhancement factor.
  - `mode`: String. "L-mode" (H98y2 < 0.85) or "H-mode" (H98y2 >= 0.85). **Derived from `h98y2`**.

### AnalysisResult
The output of the statistical analysis.
- **Attributes**:
  - `metric_name`: String. "island_width" (only).
  - `correlation`: Float. Spearman r.
  - `p_value`: Float. Two-tailed p-value.
  - `ci_lower`: Float. Lower bound of 95% CI.
  - `ci_upper`: Float. Upper bound of 95% CI.
  - `power`: Float. Estimated statistical power.
  - `hypothesis_status`: String. "supported", "inconclusive", "not_supported".
  - `stratification_warning`: String (nullable). Warning if stratification was skipped.

## Data Flow

1.  **Raw Ingestion**: MDSplus files (`.dat`, `.csv`, or binary) downloaded to `data/raw/`.
2.  **Unified Dataset**: `data/processed/discharge_metrics.csv` containing one row per valid discharge with columns: `discharge_id`, `island_width`, `resonant_surface_density`, `tau_e`, `mode`, `q_min`, `q_max`.
3.  **Analysis Output**: `outputs/summary_report.json` containing the `AnalysisResult` objects.

## Schema References

- **Input Schema**: `contracts/dataset.schema.yaml` (Validates `discharge_metrics.csv`).
- **Output Schema**: `contracts/output.schema.yaml` (Validates `summary_report.json`).