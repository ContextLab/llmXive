# Data Model: Reprojection and Resampling Methods

## Overview

This document specifies the reprojection and resampling methods used to align OpenStreetMap (OSM) vector data and satellite thermal imagery into a common raster grid for Urban Heat Island (UHI) analysis. The pipeline ensures all output rasters share identical dimensions, origin, and Coordinate Reference System (CRS) to enable valid pixel-wise statistical analysis.

## Coordinate Reference System (CRS) Strategy

### Target CRS
- **Primary CRS**: EPSG:3857 (Web Mercator) for global consistency and visualization compatibility.
- **Local CRS**: For high-precision local analysis, the pipeline supports dynamic transformation to Local UTM zones based on the city centroid.
- **Configuration**: Controlled via `code/config.py` (`TARGET_CRS` and `USE_LOCAL_UTM` flags).

### Reprojection Workflow
1. **Input Validation**: Verify input rasters and vector footprints have valid CRS definitions.
2. **Transformation**: Use `rasterio.warp.reproject` for rasters and `geopandas.GeoDataFrame.to_crs` for vectors.
3. **Resampling**: Apply method-specific resampling (see below) during transformation.
4. **Verification**: Assert output CRS matches `TARGET_CRS` and dimensions are within 0.1% tolerance of expected grid.

## Resampling Methods

The choice of resampling algorithm depends on the data type to preserve statistical properties and physical meaning.

### 1. Continuous Variables (Bilinear Interpolation)
- **Applies to**: Temperature rasters (LST), elevation models, and continuous covariates.
- **Method**: Bilinear interpolation (`rasterio.enums.Resampling.bilinear`).
- **Rationale**: Preserves smooth gradients and minimizes artificial edge effects in thermal data.
- **Error Handling**: Upsampling error (RMSE between original and reprojected sample points) must be < 0.1. If exceeded, the pipeline exits with code 1.

### 2. Categorical Variables (Nearest Neighbor)
- **Applies to**: Land-use/land-cover (LULC) classes, building density buckets, road networks (rasterized).
- **Method**: Nearest neighbor (`rasterio.enums.Resampling.nearest`).
- **Rationale**: Prevents the creation of non-existent intermediate classes (e.g., "0.5 water") and preserves integer class labels.

### 3. Binary/Boolean Variables (Nearest Neighbor)
- **Applies to**: Tree canopy masks, water bodies.
- **Method**: Nearest neighbor.

## Resolution Alignment

- **Target Resolution**: 30 meters (aligned with Landsat thermal band resolution).
- **Process**:
 1. All input rasters are resampled to 30m resolution in the target CRS.
 2. Vector data (OSM buildings, roads) is rasterized to 30m using the appropriate method (nearest for categorical counts, bilinear for density aggregates).
- **Implementation**: Handled in `code/ingest.py` via the `align_rasters` function.

## Missing Data Handling

- **Threshold**:
 - **≤ 10% missing**: Proceed without warning.
 - **> 10% missing**: Log a `WARNING` but continue processing.
 - **> 50% missing**: Log `ERROR` and skip the specific raster layer.
- **No-Data Value**: Standardized to `-9999` across all output GeoTIFFs.
- **Masking**: `numpy.ma.masked_invalid` is used during statistical computation to ignore no-data pixels.

## Output Specifications

All aligned rasters in the final stack (`data/processed/`) must satisfy:
1. **Identical Dimensions**: Same number of rows and columns.
2. **Identical Origin**: Top-left corner coordinates match exactly.
3. **Identical CRS**: All layers use the same EPSG code.
4. **Identical Resolution**: 30m x 30m pixel size.

These constraints are enforced by `code/stack_output.py` during the `create_aligned_stack` step.

## Compliance

- **SC-007**: This document serves as the formal specification for reprojection and resampling methods required by the project specification.
- **Validation**: The `validate_non_null_overlap` function in `code/ingest.py` verifies these constraints before final output generation.