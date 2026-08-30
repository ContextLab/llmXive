# Data Model Specification: Urban Heat Island Analysis via OSM & Satellite Data

**Project**: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects
**Version**: 1.1 (Updated for FR-003 Implementation Details)
**Last Updated**: 2023-10-27

## 1. Overview

This document defines the data structures, schemas, and processing rules for the pipeline.
It serves as the contract between the ingestion phase (US1), exploratory analysis (US2),
and modeling phase (US3).

## 2. Core Entities

### 2.1 CityBoundary
Represents the administrative or study area boundary for a specific city.
- **Source**: Natural Earth Data or OpenStreetMap administrative boundaries.
- **Format**: GeoJSON or Shapefile.
- **Attributes**:
 - `city_id`: Unique identifier (e.g., "nyc", "lon", "par")
 - `name`: Human-readable name
 - `geometry`: Polygon or MultiPolygon (WKT)
 - `crs_epsg`: Integer EPSG code (e.g., 4326 for source, 3857 for processing)
 - `utm_zone`: String (e.g., "18N")

### 2.2 RasterCovariate
Represents a single-layer raster derived from vector data (OSM) or satellite data.
- **Source**: OSM (buildings, roads, landuse) or Satellite (MODIS/Landsat).
- **Format**: GeoTIFF (`.tif` or `.tiff`).
- **Attributes**:
 - `layer_name`: Identifier (e.g., `building_density`, `ndvi`, `lstd`)
 - `resolution_m`: Float (target: 30.0 meters)
 - `crs_epsg`: Integer (Target: Local UTM or EPSG:3857)
 - `nodata_value`: Float (e.g., -9999.0)
 - `data_type`: `continuous` (float32) or `categorical` (uint8)
 - `stats`: Dictionary containing `min`, `max`, `mean`, `std` (computed post-processing)

### 2.3 TemperatureRaster
A specialized RasterCovariate representing Land Surface Temperature (LST).
- **Source**: MODIS (Terra/Aqua) or Landsat 8/9 Thermal Bands.
- **Format**: GeoTIFF.
- **Attributes**:
 - Inherits all from `RasterCovariate`.
 - `temp_unit`: String ("Kelvin" or "Celsius").
 - `time_period`: String (ISO 8601 range, e.g., "2018-01-01/2023-01-01").
 - `cloud_mask_applied`: Boolean.

### 2.4 SocioeconomicProxy
Derived raster representing population density or building height proxies.
- **Source**: WorldPop, OSM building heights.
- **Format**: GeoTIFF.
- **Attributes**:
 - `proxy_type`: String ("population", "building_height", "roof_area").
 - `source_dataset`: String (e.g., "WorldPop", "OSM").

## 3. Processing & Reprojection Rules (FR-003 Implementation)

This section details the specific reprojection and resampling logic required by FR-003.
All data must be harmonized to a common spatial reference and resolution before analysis.

### 3.1 Common Coordinate Reference System (CRS)
- **Target CRS**: EPSG:3857 (Web Mercator) for global consistency, OR Local UTM zone for high-precision analysis.
 - *Decision*: The pipeline defaults to **Local UTM** for the specific city to minimize distortion in area-based calculations (e.g., building density).
 - *Configuration*: Defined in `config.py` via `get_city_utm_zone(city_id)`.
- **Reprojection Engine**: `rasterio.warp.reproject` (for rasters) and `geopandas.GeoDataFrame.to_crs` (for vectors).

### 3.2 Resampling Algorithms
Resampling is applied when converting between resolutions or reprojecting.
The algorithm is selected based on the `data_type` attribute of the source layer:

| Data Type | Source Example | Resampling Method | Rasterio Constant |
|:--- |:--- |:--- |:--- |
| **Continuous** | LST, Elevation, NDVI | **Bilinear** | `rasterio.enums.Resampling.bilinear` |
| **Continuous** | Temperature (Landsat) | **Cubic** (if >2x upscale) | `rasterio.enums.Resampling.cubic` |
| **Categorical** | Land Use, Building Type | **Nearest** | `rasterio.enums.Resampling.nearest` |
| **Count/Density** | Building Count | **Average** | `rasterio.enums.Resampling.average` |

**Implementation Note**:
- Continuous variables (LST, NDVI) use **bilinear interpolation** to preserve gradients.
- Categorical variables (Land Use, Road Type) use **nearest neighbor** to prevent the creation of invalid class values (e.g., "0.5" for a class ID).
- Upsampling error (difference between original vector area and rasterized area) must be validated against `config.MISSING_DATA_THRESHOLD`. If error > 0.1, the process exits with code 1 (see T014b).

### 3.3 Resolution Standardization
- **Target Resolution**: 30 meters.
- **Procedure**:
 1. Determine the native resolution of the input raster (e.g., MODIS ~1km, Landsat ~30m, Sentinel ~10m).
 2. If native > 30m: Upsample using the method defined in 3.2.
 3. If native < 30m: Downsample using the method defined in 3.2 (usually `average` for continuous, `mode` for categorical if available, else `nearest`).
- **Alignment**: All output rasters must share the exact same `transform` (affine) and `width`/`height` to ensure pixel-to-pixel alignment in the analysis stack.

### 3.4 No-Data Handling
- **Standard No-Data Value**: `-9999.0` for float rasters.
- **Propagation**: No-data values in source rasters must be preserved during reprojection.
- **Masking**: During analysis (US2/US3), pixels with value == No-Data are excluded from calculations (e.g., Moran's I, Regression).

## 4. Data Lineage & Metadata

All processed artifacts in `data/processed/` must be accompanied by a `metadata.json` file containing:
- `source_files`: List of input file paths.
- `processing_steps`: List of transformations applied (e.g., ["reproject_epsg:32618", "resample_bilinear_30m"]).
- `timestamp`: ISO 8601 timestamp of creation.
- `checksum`: SHA-256 hash of the output file.
- `crs`: EPSG code of the output.
- `resolution`: Float (meters).

## 5. Validation Constraints

- **Alignment**: `validate_raster_alignment` must confirm all rasters in a stack share identical bounds, dimensions, and CRS.
- **Non-Null Overlap**: The intersection of all valid (non-No-Data) pixels across the stack must be > 90% of the study area (configurable).
- **Memory Safety**: Raster dimensions must be checked against `config.MAX_BLOCKS` and available RAM before loading into memory (see `utils/memory.py`).

## 6. Changes in Version 1.1
- Added explicit **Resampling Algorithm** table (Section 3.2) to satisfy FR-003.
- Clarified **Target CRS** selection logic (Local UTM vs Web Mercator).
- Defined **No-Data** standard and propagation rules.
- Added **Validation Constraints** section to link with T014b/T016 tasks.