# Data Model: Reprojection and Resampling Methods

**Project**: Statistical Analysis of OpenStreetMap Data for Urban Heat Island Effects
**Spec Reference**: SC-007
**Status**: Implemented in `code/ingest.py`

## Overview

This document defines the data model and algorithms used for aligning heterogeneous geospatial data sources (vector OSM data and satellite thermal rasters) into a unified, analysis-ready raster stack. The primary goal is to ensure all covariates and target variables share identical spatial extent, resolution, coordinate reference system (CRS), and pixel alignment.

## Target Specifications

- **Target CRS**: Local UTM zone for the city (EPSG:XXXX) or EPSG:3857 if UTM is undefined. Configurable via `config.py`.
- **Target Resolution**: 30 meters (coarse resolution for computational efficiency and memory safety).
- **Target Extent**: Intersection of all input layers within the city boundary.
- **Alignment**: Strict pixel alignment (origin and dimensions must match exactly across all layers).

## Input Data Sources

1. **OSM Vector Data** (Buildings, Land-use, Trees, Roads)
 - Source: Overpass API
 - Format: GeoJSON / Geometry objects
 - Initial CRS: EPSG:4326 (WGS84)
2. **Satellite Thermal Data** (MODIS/Landsat)
 - Source: NASA Earthdata / USGS EarthExplorer
 - Format: GeoTIFF
 - Initial CRS: Varies (often EPSG:4326 or native projection)

## Reprojection Methodology

### Coordinate Reference System Transformation

All data is transformed to the target CRS defined in `config.get_city_crs(city_name)`.

**Algorithm**:
1. Determine target UTM zone based on city centroid longitude.
2. If target is EPSG:3857, use standard Web Mercator projection.
3. Apply `pyproj.Transformer` or `geopandas.to_crs()` for vector data.
4. Apply `rasterio.warp.reproject()` for raster data.

**Code Reference**: `code/ingest.py::create_aligned_raster_stack()`

```python
# Pseudocode representation of the actual implementation
from rasterio.warp import reproject, Resampling
import rasterio

def reproject_raster(src_path, dst_path, target_crs, target_res):
 with rasterio.open(src_path) as src:
 transform, width, height = calculate_default_transform(
 src.crs, target_crs, src.width, src.height, *src.bounds,
 resolution=target_res
)
 kwargs = src.meta.copy()
 kwargs.update({
 'crs': target_crs,
 'transform': transform,
 'width': width,
 'height': height
 })

 with rasterio.open(dst_path, 'w', **kwargs) as dst:
 for i in range(1, src.count + 1):
 reproject(
 source=rasterio.band(src, i),
 destination=rasterio.band(dst, i),
 src_transform=src.transform,
 src_crs=src.crs,
 dst_transform=transform,
 dst_crs=target_crs,
 resampling=Resampling.bilinear if src.meta['dtype'] in ['float32', 'float64'] else Resampling.nearest
)
```

## Resampling Methods

The choice of resampling algorithm depends on the data type to preserve physical meaning and avoid artifacts.

### 1. Continuous Variables (Temperature, Elevation)
- **Method**: Bilinear Interpolation
- **Rationale**: Preserves smooth gradients and minimizes high-frequency noise while maintaining statistical properties of the surface.
- **Implementation**: `rasterio.warp.Resampling.bilinear`

### 2. Categorical Variables (Land-use, Building Density Classes)
- **Method**: Nearest Neighbor
- **Rationale**: Prevents creation of non-existent intermediate categories (e.g., "0.4 residential" is invalid). Ensures class integrity.
- **Implementation**: `rasterio.warp.Resampling.nearest`

### 3. Upsampling Validation (SC-007)
- **Constraint**: When upsampling from a coarser source (e.g., MODIS 1km) to the target 30m, the error must be monitored.
- **Validation**: The system calculates the variance of the resampled block against the original mean.
- **Threshold**: If upsampling error > 0.1 (normalized), the process exits with code 1.
- **Logic**:
 ```python
 if upsampling_error > 0.1:
 logger.error("Upsampling error exceeds threshold (0.1). Exiting.")
 sys.exit(1)
 ```

## Missing Data Handling

The pipeline handles missing data (NoData values) according to the following policy:

1. **Threshold Check**: Calculate the percentage of NoData pixels in the overlap region.
2. **Policy**:
 - **≤ 10% Missing**: Proceed silently. NoData is preserved as `-9999` or `NaN`.
 - **> 10% Missing**: Log a `WARNING` but proceed. The data is still usable for analysis, though with reduced coverage.
 - **> 50% Missing**: (Future enhancement) Could trigger an automatic exclusion of the layer.
3. **Output**: The final aligned stack preserves the NoData flag.

## Output Data Model

The final output is a stack of GeoTIFFs located in `data/processed/`.

**Schema**:
- **File Naming**: `{city}_{variable}_{date}.tif`
- **Dimensions**: Identical `(width, height)` for all layers.
- **Origin**: Identical `(x_min, y_max)` for all layers.
- **CRS**: Identical EPSG code.
- **Transform**: Identical affine transformation matrix.
- **Data Types**:
 - Temperature: `float32`
 - Covariates (Count/Class): `uint8` or `uint16`

## Validation Logic

The function `validate_raster_alignment()` in `code/ingest.py` performs the following checks before finalizing the stack:

1. **Dimension Match**: `raster.width == reference.width` and `raster.height == reference.height`.
2. **Transform Match**: `raster.transform == reference.transform` (within float tolerance).
3. **CRS Match**: `raster.crs == reference.crs`.
4. **Non-Null Overlap**: Verify that the intersection of valid data (non-NoData) is not empty.

## Metadata Generation

A `metadata.json` file is generated alongside the raster stack (Task T015) containing:
- Fetch timestamps
- Source URLs/IDs
- Checksums (SHA256) of input and output files
- Resampling parameters used
- CRS definition

## References

- `code/ingest.py`: Implementation of `create_aligned_raster_stack` and `validate_raster_alignment`.
- `config.py`: Definition of `MAX_BLOCKS` and city-specific CRS settings.
- `rasterio` Documentation: https://rasterio.readthedocs.io/en/latest/topics/reproject.html