# Data Model: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## Overview

This document defines the data structures for the UHI analysis pipeline. The model is designed to support the ingestion of vector and raster data, the alignment process, and the storage of statistical results.

## Entity Definitions

### 1. CityGrid
Represents the unified 30m raster grid for a specific city.
- **Attributes**:
  - `city_id`: String (e.g., "NYC", "CHI", "LA")
  - `crs`: String (EPSG code, e.g., "EPSG:3857")
  - `resolution`: Float (30.0)
  - `dimensions`: Tuple (rows, cols)
  - `bounds`: Tuple (min_x, min_y, max_x, max_y)
  - `data_array`: xarray DataArray (Temperature, Building_Density, Road_Density, Tree_Density)

### 2. ModelResult
Structured record for fitted model outputs.
- **Attributes**:
  - `model_type`: String ("OLS", "GWR", "SAR")
  - `city_id`: String
  - `coefficients`: Dict (feature_name -> float)
  - `standard_errors`: Dict (feature_name -> float)
  - `p_values`: Dict (feature_name -> float)
  - `metrics`: Dict ("rmse": float, "r2": float, "aic": float)
  - `cv_metrics`: Dict ("cv_rmse": float, "cv_r2": float)
  - `bandwidth`: Float (for GWR only, [deferred] range)

### 3. SpatialDiagnostic
Record for exploratory analysis results.
- **Attributes**:
  - `city_id`: String
  - `moran_i`: Float
  - `moran_p_value`: Float
  - `variogram_params`: Dict ("nugget": float, "sill": float, "range": float)
  - `vif_scores`: Dict (feature_name -> float)
  - `correlation_matrix`: Matrix (features vs temperature)

## Data Flow

1.  **Ingest**: Raw OSM vectors and Satellite rasters -> `CityGrid` (aligned).
2.  **EDA**: `CityGrid` -> `SpatialDiagnostic`.
3.  **Modeling**: `CityGrid` + `SpatialDiagnostic` -> `ModelResult`.
4.  **Validation**: `ModelResult` -> Aggregated Metrics (JSON).

## Constraints

- **Immutable Raw Data**: Raw files in `data/raw` are never modified.
- **Derived Data**: All processed rasters in `data/processed` are derived from raw data with a recorded checksum.
- **Missing Data**: Pixels with missing temperature or covariate data are masked (NaN) and excluded from model fitting.
- **Collinearity**: If VIF > 5, the feature is flagged in `SpatialDiagnostic` but may be excluded from the final model or reported with a warning.
