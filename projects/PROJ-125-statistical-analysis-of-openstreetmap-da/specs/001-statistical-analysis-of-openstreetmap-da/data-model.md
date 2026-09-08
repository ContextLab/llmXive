# Data Model: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## Overview

This document defines the data structures, schemas, and relationships used in the project. All data is stored in the `data/` directory with strict versioning and checksumming.

## Core Entities

### CityBoundary
Represents the administrative boundary of the study area.
- **Attributes**:
  - `name`: str (City name)
  - `bbox`: Tuple[float, float, float, float] (MinX, MinY, MaxX, MaxY)
  - `crs`: str (EPSG code, e.g., "EPSG:4326")

### RasterCovariate
Represents a rasterized urban feature (e.g., building density, tree cover).
- **Attributes**:
  - `path`: str (Relative path to GeoTIFF)
  - `resolution`: float (30.0)
  - `crs`: str (EPSG:3857 or Local UTM)
  - `variable_name`: str (e.g., "building_density")
  - `source`: str (e.g., "OSM")

### TemperatureRaster
Represents the Land Surface Temperature (LST) data.
- **Attributes**:
  - `path`: str (Relative path to GeoTIFF)
  - `resolution`: float (30.0)
  - `crs`: str (EPSG:3857 or Local UTM)
  - `time_range`: str (e.g., "2020-2025")
  - `source`: str (e.g., "MODIS")

### ModelResult
Stores the output of a regression model.
- **Attributes**:
  - `model_type`: str ("OLS", "SAR", "GWR")
  - `rmse`: float
  - `mae`: float
  - `r2`: float
  - `p_values`: Dict[str, float] (Variable -> p-value)
  - `correction_method`: str (e.g., "FDR_BH")
  - `memory_status`: str ("OK", "DEGRADED")
  - `city_name`: str

## File Formats

### Raw Data
- **OSM**: GeoJSON or GeoParquet (downloaded via `osmnx`).
- **Satellite**: HDF or GeoTIFF (downloaded via `earthengine-api` or `modis`).

### Processed Data
- **Rasterized Features**: GeoTIFF (30m, EPSG:3857).
- **Aligned Dataset**: CSV or GeoParquet (30m points with all variables).

### Results
- **Metrics**: CSV (`data/results/metrics.csv`).
- **Plots**: PNG/SVG (in `data/results/plots/`).
- **Reports**: Markdown/HTML (in `data/results/reports/`).

## Data Flow

1. **Ingest**: Download raw OSM and Satellite data to `data/raw/`.
2. **Preprocess**: Rasterize OSM features and align with LST to 30m resolution.
3. **Sample**: If N > 500k, apply spatial sampling to reduce size.
4. **Model**: Fit OLS, SAR, GWR (or pipeline halts if memory constraints are exceeded).
5. **Validate**: Spatial cross-validation and FDR correction.
6. **Export**: Save metrics and plots to `data/results/`.
