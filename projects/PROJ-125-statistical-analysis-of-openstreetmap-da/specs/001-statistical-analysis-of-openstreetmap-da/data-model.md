# Data Model Specification: Urban Heat Island Analysis using OpenStreetMap

## Overview
This document defines the data structures, schemas, and processing rules for the
`PROJ-125-statistical-analysis-of-openstreetmap-da` project. It serves as the
contract between the ingestion (US1), analysis (US2), and modeling (US3) stages.

## 1. Core Entities

### 1.1 CityBoundary
Represents the administrative boundary of the study area.
- **Type**: GeoJSON / Shapefile
- **Fields**:
 - `city_name` (string): Canonical name (e.g., "New York City")
 - `country` (string): ISO 3166-1 alpha-3 code
 - `geometry` (Polygon/MultiPolygon): The boundary geometry
 - `source` (string): Origin (e.g., "OpenStreetMap Overpass", "GADM")
 - `epsg_code` (int): Source CRS code (usually 4326 or 3857)

### 1.2 RasterCovariate
Represents a single geospatial covariate layer derived from OSM or external sources.
- **Type**: GeoTIFF
- **Fields**:
 - `variable_name` (string): e.g., "building_density", "tree_coverage", "road_length"
 - `unit` (string): e.g., "m²/m²", "count", "m/m²"
 - `resolution_m` (float): Cell size in meters (target: 30m)
 - `nodata_value` (float): Value representing missing data (e.g., -9999)
 - `source` (string): e.g., "OSM Buildings", "WorldPop"

### 1.3 TemperatureRaster
Represents the target variable: Land Surface Temperature (LST).
- **Type**: GeoTIFF
- **Fields**:
 - `variable_name` (string): "LST"
 - `unit` (string): "Kelvin" or "Celsius" (specify in metadata)
 - `resolution_m` (float): Cell size in meters (target: 30m)
 - `acquisition_date` (datetime): Timestamp of satellite pass
 - `cloud_cover_pct` (float): Cloud coverage percentage
 - `source` (string): e.g., "MODIS LST", "Landsat 8 TIRS"

## 2. Reprojection and Resampling Specifications (FR-003)

To ensure spatial alignment for regression analysis, all layers must be transformed
to a common Coordinate Reference System (CRS) and resampled to a standard resolution.

### 2.1 Target CRS
- **Primary**: Local UTM Zone (EPSG:XXXX) appropriate for the city center.
- **Fallback**: Web Mercator (EPSG:3857) if UTM zone boundaries are ambiguous.
- **Transformation Method**: `rasterio.warp.reproject` with `resampling='bilinear'` for continuous
 variables (Temperature, Density) and `resampling='nearest'` for categorical variables
 (Land Use Classes).

### 2.2 Target Resolution
- **Standard**: 30 meters.
- **Rationale**: Matches the native resolution of Landsat thermal bands and provides
 sufficient granularity for urban block-level analysis without excessive memory overhead.

### 2.3 Resampling Rules
| Source Type | Target Variable | Resampling Method | Rationale |
|-------------|-----------------|-------------------|-----------|
| Vector (Polygons) | Building Density | `bilinear` (after rasterization) | Smooths area aggregation |
| Vector (Lines) | Road Length | `bilinear` (after rasterization) | Preserves line density |
| Vector (Points) | Tree Count | `bilinear` (after rasterization) | Smooths point density |
| Continuous Raster | Temperature | `bilinear` | Preserves continuous gradient |
| Categorical Raster | Land Cover | `nearest` | Prevents mixing of class labels |

### 2.4 Implementation Constraints
- **Validation**: After reprojection, the `validate_raster_alignment` function must verify:
 1. All rasters share the same `affine` transform (width, height, origin, rotation).
 2. All rasters share the same `crs`.
 3. No layer has been distorted beyond a 1% area change threshold.
- **Error Handling**: If the reprojection results in an area change > 1% or mismatched dimensions,
 the pipeline must **FAIL LOUDLY** (exit code 1) and log the specific misalignment details.
 Do not attempt to auto-correct or proceed with misaligned data.

## 3. Data Integrity and Quality Controls

### 3.1 Missing Data
- **Threshold**: Configurable via `config.MISSING_DATA_THRESHOLD`.
- **Action**: If a raster has > `threshold` % null pixels in the city boundary, log a WARNING
 but proceed. If the overlap between temperature and covariates is < 10%, fail.

### 3.2 Memory Safety
- **Check**: Before loading, estimate memory usage using `utils.memory.estimate_raster_memory_mb`.
- **Constraint**: If estimated usage > `config.MAX_MEMORY_MB` (default 5GB), raise a fatal error.
 Do not subsample or degrade resolution automatically.

## 4. File Naming Conventions
- **Raw**: `data/raw/{city}/{source}_{variable}_{date}.tif`
- **Processed**: `data/processed/{city}/{variable}_{resolution}m_{crs}.tif`
- **Metadata**: `data/metadata.json` (generated on successful pipeline completion)

## 5. Schema Validation
All entities must be instantiated via the classes in `code/models/`:
- `CityBoundary` (from `code/models/city.py`)
- `RasterCovariate` (from `code/models/raster.py`)
- `TemperatureRaster` (from `code/models/raster.py`)

These classes enforce type checking and required field validation upon initialization.