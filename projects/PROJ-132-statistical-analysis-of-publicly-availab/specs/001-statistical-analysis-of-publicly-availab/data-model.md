# Data Model: Bird Migration and Climate Analysis

## Overview

This document defines the data structures used throughout the pipeline. All data is stored in CSV or Parquet format, with checksums recorded in the project state.

## Entity Definitions

### 1. MigrationRecord (Raw)
Represents a single bird observation.
- `species` (str): Scientific name (e.g., "Turdus migratorius").
- `latitude` (float): Decimal degrees (WGS84).
- `longitude` (float): Decimal degrees.
- `date` (date): YYYY-MM-DD.
- `count` (int): Number of individuals observed.
- `checklist_id` (str): Unique eBird checklist ID.
- `grid_cell` (str): "lat_lon" string (e.g., "45.5_-122.0").

### 2. ClimateVariable (Raw/Interim)
Represents climate measurements for a grid cell and week.
- `grid_cell` (str): "lat_lon" string.
- `week` (int): ISO week number (1-52).
- `year` (int): Year (2020-2024).
- `mean_temp` (float): Mean temperature (°C).
- `total_precip` (float): Total precipitation (mm).
- `extreme_idx` (float): Extreme weather index (0-1).
- `imputed` (bool): True if value was interpolated.

### 3. PhenologyMetric (Processed)
Computed metrics per species, grid cell, year.
- `species` (str).
- `grid_cell` (str).
- `year` (int).
- `first_arrival` (int): Day of year (1-365).
- `median_arrival` (int): Day of year.
- `stopover_duration` (float): Days between 10th and 90th percentile.
- `n_obs` (int): Number of observations used.
- `data_quality` (str): "sufficient" or "insufficient".

### 4. ModelOutput (Result)
Results from the Unified Spatial Model.
- `species` (str).
- `term` (str): "temp_smooth", "precip_smooth".
- `estimate` (float): Coefficient or smooth effect estimate.
- `p_value` (float): Permutation p-value.
- `fdr_q_value` (float): FDR corrected p-value.
- `converged` (bool).
- `spatial_smooth_k` (int): Complexity parameter used.

### 5. TrajectoryShift (Result)
Spatial route shift analysis.
- `species` (str).
- `year_start` (int).
- `year_end` (int).
- `shift_magnitude` (float): Distance in km.
- `shift_direction` (float): Degrees (0-360).
- `p_value` (float): Permutation p-value.
- `ci_lower` (float): 95% CI lower bound.
- `ci_upper` (float): 95% CI upper bound.

## Data Flow

1.  **Input**: `data/raw/synthetic_ebird.csv`, `data/raw/synthetic_climate.parquet` (or real data if available).
2.  **Preprocess**: `src/data/preprocess.py` -> `data/processed/phenology_metrics.csv`, `data/processed/climate_aligned.parquet`.
3.  **Model**: `src/models/gamm.py` -> `data/processed/model_results.parquet`.
4.  **Trajectory**: `src/models/trajectory.py` -> `data/processed/trajectory_shifts.parquet`.
5.  **Output**: `data/processed/final_analysis_report.csv`.

## Assumptions

- All coordinates are in WGS84.
- Dates are UTC.
- Missing climate data is imputed using spatial interpolation within 1° radius.
- "Insufficient data" threshold is < 5 observations per cell/year.
