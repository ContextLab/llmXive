# Data Model: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## Overview

This document defines the data structures, transformations, and schemas used in the UHI analysis pipeline. The data flows from raw vector/raster ingestion to aligned covariates, and finally to statistical model outputs.

## Entity Definitions

### 1. CityBoundary
- **Type**: GeoJSON / Shapefile
- **Description**: The administrative boundary of the study city.
- **Attributes**:
  - `city_name` (string): e.g., "New York"
  - `geometry` (Polygon): WGS84 (EPSG:4326)
  - `crs` (string): "EPSG:4326"

### 2. RasterCovariate
- **Type**: GeoTIFF
- **Resolution**: 30m
- **CRS**: Projected (e.g., EPSG:3857 or local UTM)
- **Description**: OSM-derived features rasterized to a grid.
- **Attributes**:
  - `feature_type` (string): e.g., "building_density", "tree_canopy", "road_density"
  - `unit` (string): e.g., "count_per_pixel", "fraction"
  - `nodata_value` (float): -9999

### 3. TemperatureRaster
- **Type**: GeoTIFF
- **Resolution**: 30m
- **CRS**: Same as RasterCovariate
- **Description**: Land Surface Temperature (LST) derived from Landsat.
- **Attributes**:
  - `source` (string): "Landsat 8/9 TIRS"
  - `unit` (string): "Kelvin" or "Celsius"
  - `cloud_mask` (boolean): True if pixel is cloud-free.

### 4. SpatialModelOutput
- **Type**: JSON / CSV
- **Description**: Results from OLS, GWR, SAR models.
- **Attributes**:
  - `model_type` (string): "OLS", "GWR", "SAR", "OLS_DEGRADED"
  - `metric_rmse` (float)
  - `metric_r2` (float)
  - `coefficients` (dict): {predictor: value}
  - `p_values_adjusted` (dict): {predictor: value}
  - `spatial_autocorrelation_residuals` (float): Moran's I of residuals.

## Data Flow

1.  **Ingestion**:
    - `CityBoundary` + `Overpass Query` → `RawOSM_Vector`
    - `Landsat Scene ID` + `AWS` → `RawLandsat_TIF`
2.  **Processing**:
    - `RawOSM_Vector` → (Rasterize) → `RasterCovariate`
    - `RawLandsat_TIF` → (LST Retrieval + Cloud Mask) → `TemperatureRaster`
    - `RasterCovariate` + `TemperatureRaster` → (Align/Resample) → `StackedDataset`
3.  **Sampling (Critical Step)**:
    - `StackedDataset` → (Spatial Block Sampling: 1km x 1km grid) → `SampledDataset`
    - *Logic*: Generate a fixed grid of 1km x 1km blocks over the city extent. Randomly select a subset of blocks (max [deferred] of total) to ensure spatial autocorrelation structure is preserved while reducing $N$. **Random pixel sampling is explicitly forbidden.**
4.  **Analysis**:
    - `SampledDataset` → (EDA) → `CorrelationMatrix`, `MoranI_Report`
    - `SampledDataset` → (Modeling) → `SpatialModelOutput`

## Edge Case Handling

- **Missing Data**: If `nodata_value` > 10% of pixels in `TemperatureRaster`, log WARNING and proceed with mask.
- **Cloud Cover**: If `cloud_mask` > 20% of area, generate multi-date composite.
- **Resolution Mismatch**: If OSM vector area differs from raster area by > 0.1, log ERROR and exit.
- **Memory Overflow**: If $N_{samples} > 500,000$, degrade to OLS only.

## Block Generation Logic

To ensure reproducibility of spatial statistics:
- **Grid Size**: Fixed 1km x 1km blocks.
- **Origin**: Aligned to the UTM zone origin (or EPSG:3857 origin) for the city.
- **Selection**: A random seed is used to select which blocks are included in the final sample. The seed and block count are recorded in `metadata.json`.
- **Constraint**: This block-based approach is mandatory to preserve spatial autocorrelation structure for Moran's I and variogram estimation.