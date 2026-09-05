# Data Model: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects

## 1. Entities

### CityBoundary
- **Name**: `str` - Name of the city (e.g., "Boston").
- **BBox**: `tuple[float, float, float, float]` - (minx, miny, maxx, maxy) in EPSG:4326.
- **CRS**: `str` - Coordinate Reference System (default: EPSG:4326).

### RasterCovariate
- **Path**: `str` - File path to the rasterized covariate (e.g., `data/processed/buildings_30m.tif`).
- **Resolution**: `float` - Cell size in meters (30.0).
- **CRS**: `str` - Coordinate Reference System (EPSG:3857).
- **Variable Name**: `str` - Name of the variable (e.g., "building_density", "tree_coverage").

### TemperatureRaster
- **Path**: `str` - File path to the LST raster.
- **Resolution**: `float` - Cell size in meters (30.0).
- **CRS**: `str` - Coordinate Reference System (EPSG:3857).
- **Time Range**: `str` - Start and end dates (e.g., "2020-01-01 to 2025-01-01").

## 2. Data Flow

1. **Ingestion**:
   - `OSM Vector` (`.osm.pbf` or `.geojson`) -> `CityBoundary` (extracted).
   - `LST Raster` (`.tif`) -> `TemperatureRaster`.
   - **Note**: If OSM or LST data is missing, the pipeline will **halt** with a clear error. No metrics will be generated.
2. **Processing**:
   - `OSM Vector` + `CityBoundary` -> Rasterization -> `RasterCovariate` (per variable).
   - All rasters aligned to a common grid (30m, EPSG:3857).
3. **Analysis**:
   - `RasterCovariate` + `TemperatureRaster` -> Extracted values at each pixel -> `DataFrame` (N rows, M columns).
   - `DataFrame` -> `OLS/SAR/GWR` -> `ModelResults`.
4. **Output**:
   - `ModelResults` -> `metrics.csv` (RMSE, MAE, R², p-values).
   - `ModelResults` -> `plots/` (sensitivity, spatial maps).
   - **Note**: If data is missing, `metrics.csv` will **not** be generated. The pipeline will exit with an error.
5. **Versioning**:
   - After data ingestion and processing, the pipeline MUST update `state/projects/PROJ-125-statistical-analysis-of-openstreetmap-da.yaml` with content hashes for all data artifacts.

## 3. Constraints

- **Resolution**: All rasters must be 30m.
- **CRS**: All spatial operations must use EPSG:3857.
- **Memory**: The final `DataFrame` used for modeling must fit in < 6GB RAM. If not, **Stratified Spatial Block Sampling** is applied to reduce N < 200k. If sampling fails, the fallback to OLS is triggered.
- **Versioning**: All data artifacts will include content hashes in `state/projects/PROJ-125-statistical-analysis-of-openstreetmap-da.yaml` `artifact_hashes` map. The pipeline MUST update this file after processing.