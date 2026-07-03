# Data Model: Predicting Plant Phenology from Satellite Imagery and Climate Data

## Overview

This document defines the data structures for the plant phenology prediction pipeline. It covers the raw inputs, processed features, and model outputs.

**Key Change**: `gdd_cumulative` is **removed** from the raw `EnvironmentalTimeSeries` entity. GDD is now a **derived feature** calculated at training time from temperature variables to avoid multicollinearity.

## Entity Definitions

### StudySite
Represents a geographic location for analysis.
- `site_id` (str): Unique identifier (e.g., "SITE_001")
- `latitude` (float): Latitude in decimal degrees
- `longitude` (float): Longitude in decimal degrees
- `plant_functional_type` (str): e.g., "Deciduous Broadleaf", "Evergreen Needleleaf"
- `data_coverage_pct` (float): Percentage of valid 10-day intervals (2018-2023)

### PhenologicalEvent
Represents a ground-truth observation.
- `event_id` (str): Unique identifier from Nature's Notebook
- `site_id` (str): Foreign key to StudySite
- `species_code` (str): Plant species code
- `event_type` (str): "budburst", "flowering", "senescence"
- `observed_date` (date): Date of observation (YYYY-MM-DD)
- `year` (int): Year of observation

### EnvironmentalTimeSeries
Aligned time-series data for modeling.
- `site_id` (str): Foreign key to StudySite
- `date` (date): 10-day interval start date (YYYY-MM-DD)
- `ndvi` (float): Normalized Difference Vegetation Index
- `evi` (float): Enhanced Vegetation Index
- `temp_mean` (float): Mean temperature (°C)
- `temp_max` (float): Maximum temperature (°C)
- `precip_total` (float): Total precipitation (mm)
- `solar_rad` (float): Solar radiation (MJ/m²)
- `is_interpolated` (bool): True if value was interpolated
- `is_valid` (bool): True if data is valid (not excluded)
- **Note**: `gdd_cumulative` is **NOT** a field here. It is derived during feature engineering.

### ModelOutput
Prediction results and metrics.
- `site_id` (str): Foreign key to StudySite
- `event_type` (str): "budburst", "flowering", "senescence"
- `predicted_date` (date): Predicted date (YYYY-MM-DD)
- `actual_date` (date): Ground truth date (if available)
- `error_days` (float): Absolute difference in days
- `model_version` (str): Hash of model configuration

## Data Flow

1.  **Raw Ingestion**: Download Sentinel-2, NOAA, Nature's Notebook data → `data/raw/`
2.  **Preprocessing**: Align to 10-day intervals, interpolate, calculate GDD **at training time** → `data/processed/environmental_time_series.csv`
3.  **Feature Engineering**: Create lagged features (e.g., Jan-Mar data for April event), calculate GDD from `temp_mean`/`temp_max`, apply VIF filter → `data/processed/features.csv`
4.  **Model Training**: Train XGBoost/LightGBM → `artifacts/models/`
5.  **Evaluation**: Compute RMSE, MAE, R² → `artifacts/reports/metrics.json`

## Constraints & Validation

- **Temporal Consistency**: All dates must be within 2018-2023.
- **Geographic Bounds**: Latitude [-90, 90], Longitude [-180, 180].
- **Value Ranges**: NDVI/EVI in [-1, 1]; Temp in [-50, 60]; Precip ≥ 0.
- **Missing Data**: `is_valid=False` for excluded rows; `is_interpolated=True` for filled gaps.
- **Feature Independence**: Final feature set must not contain both GDD and raw temperature. GDD is calculated as `max(0, temp_mean - base_temp)` during training.
