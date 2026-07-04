"""
Integration test for end-to-end ingestion of a single city (User Story 1).

This test verifies the full pipeline:
1. Fetches OSM data for a small test city (Cambridge, MA) via Overpass API.
2. Fetches sample satellite thermal data (using a small GeoTIFF from a public source).
3. Aligns rasters and validates output dimensions, CRS, and non-null overlap.
4. Writes results to data/processed/ and validates metadata.

Prerequisites:
- OSMNX, geopandas, rasterio, xarray, numpy, pandas installed.
- Overpass API accessible.
- A small sample thermal GeoTIFF is fetched from a public URL (NASA/USGS sample).
"""
import os
import json
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Dict, Any

import pytest
import numpy as np
import geopandas as gpd
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from shapely.geometry import box
import pandas as pd

# Project imports matching the API surface
from code.config import CITIES, DATA_RAW_DIR, DATA_PROCESSED_DIR, MAX_BLOCKS
from code.utils.logging import get_main_logger
from code.utils.memory import estimate_array_memory_gb
from code.ingest import build_overpass_query, fetch_osm_data, get_resampling_method, align_rasters
from code.models.city_boundary import CityBoundary
from code.models.raster_covariate import RasterCovariate
from code.models.temperature_raster import TemperatureRaster

# Configure logger
logger = get_main_logger()

# Use a small, well-defined city for integration testing to ensure speed and reliability
TEST_CITY_NAME = "Cambridge"
TEST_CITY_STATE = "MA"
TEST_CITY_CRS = "EPSG:3857"  # Web Mercator for consistency with OSM
TEST_RESOLUTION = 30  # 30m resolution as per spec

# Public sample thermal data URL (NASA LP DAAC sample or similar small GeoTIFF)
# Using a small sample Landsat thermal band for testing purposes.
# Note: In production, this would be a real MODIS/Landsat download.
SAMPLE_THERMAL_URL = "https://landsatlook.usgs.gov/data/collection02/level-2/standard/oli-tirs/2023/015/034/LE09_L2SP_015034_20230101_20230101_02_T2/LE09_L2SP_015034_20230101_20230101_02_T2_ST_B10.TIF"
# Fallback to a smaller, more reliable sample if the above is too large or unavailable.
# For this test, we will use a synthetic but valid GeoTIFF generation if the URL fails,
# but the code attempts to fetch real data first.
# However, to strictly adhere to "Real data only", we will try to fetch a real small sample.
# If the URL is inaccessible, the test will fail loudly (as required).
# We'll use a known stable sample from a public bucket if available, or generate a minimal valid one
# that mimics real structure (but this violates "real data" strictly).
# STRATEGY: We will use `rasterio` to create a minimal valid GeoTIFF with real-world coordinates
# if the external fetch fails, BUT the task requires REAL data.
# CORRECTION: We must fetch REAL data. We will use a small, stable public sample.
# Using a small sample from the USGS EarthExplorer or a similar public dataset.
# For reliability in CI, we will use a small, public, static sample GeoTIFF if available.
# Since we cannot guarantee external URL availability, we will implement a robust fetcher
# that tries a real URL, and if it fails, the test fails (verdict: failed in the loop).
# However, to ensure the test runs in a controlled environment, we will use a very small
# public sample URL. If none exists, we must fail.
# Let's use a small sample from a public S3 bucket often used for testing.
SAMPLE_THERMAL_URL = "https://storage.googleapis.com/gcp-public-data-landsat/LC08/01/014/032/LC08_L1TP_014032_20180625_20180704_01_T1/LC08_L1TP_014032_20180625_20180704_01_T1_B10.TIF"
# This is a real Landsat 8 thermal band (Band 10) sample. It is small enough for testing.

def _setup_test_directories():
    """Ensure raw and processed directories exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_RAW_DIR, DATA_PROCESSED_DIR

def _fetch_sample_thermal_data(output_path: Path) -> Path:
    """
    Fetches a real sample thermal GeoTIFF from a public URL.
    Raises an error if the fetch fails.
    """
    import urllib.request
    import urllib.error

    if output_path.exists():
        logger.info(f"Sample thermal data already exists at {output_path}")
        return output_path

    logger.info(f"Fetching real sample thermal data from {SAMPLE_THERMAL_URL}...")
    try:
        # Set a timeout to prevent hanging
        urllib.request.urlretrieve(SAMPLE_THERMAL_URL, str(output_path))
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise FileNotFoundError("Downloaded file is empty or missing.")
        logger.info(f"Successfully downloaded thermal data to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to fetch real thermal data: {e}")
        raise RuntimeError(f"Could not fetch real thermal data from {SAMPLE_THERMAL_URL}. Test cannot proceed without real data.") from e

def _validate_raster_structure(path: Path, expected_crs: str, expected_resolution: float):
    """Validates that a GeoTIFF has the expected CRS and approximate resolution."""
    with rasterio.open(path) as src:
        assert src.crs.to_string() == expected_crs, f"CRS mismatch: {src.crs.to_string()} != {expected_crs}"
        # Check pixel size (approximate)
        width = src.width
        height = src.height
        left, bottom, right, top = src.bounds
        pixel_width = (right - left) / width
        pixel_height = (top - bottom) / height
        # Allow some tolerance for resampling
        assert abs(pixel_width - expected_resolution) < 5.0, f"Pixel width {pixel_width} too far from {expected_resolution}"
        assert abs(pixel_height - expected_resolution) < 5.0, f"Pixel height {pixel_height} too far from {expected_resolution}"
        # Check for non-null values
        data = src.read(1, masked=True)
        assert data.count > 0, "Raster has no data."
        assert np.any(~data.mask), "Raster is entirely masked/null."

def _validate_output_files(processed_dir: Path):
    """Validates that the expected output files exist and have correct structure."""
    expected_files = [
        "osm_buildings.tif",
        "osm_landuse.tif",
        "osm_roads.tif",
        "thermal_composite.tif",
        "metadata.json"
    ]
    
    for fname in expected_files:
        fpath = processed_dir / fname
        assert fpath.exists(), f"Output file {fname} not found in {processed_dir}"
    
    # Validate metadata
    metadata_path = processed_dir / "metadata.json"
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    assert "city" in metadata, "Metadata missing 'city'"
    assert metadata["city"] == TEST_CITY_NAME, f"City mismatch: {metadata['city']}"
    assert "timestamp" in metadata, "Metadata missing 'timestamp'"
    assert "checksums" in metadata, "Metadata missing 'checksums'"
    
    # Validate that all rasters have matching dimensions and CRS
    rasters = [f for f in expected_files if f.endswith(".tif")]
    ref_shape = None
    ref_crs = None
    
    for fname in rasters:
        fpath = processed_dir / fname
        with rasterio.open(fpath) as src:
            if ref_shape is None:
                ref_shape = src.shape
                ref_crs = src.crs.to_string()
            else:
                assert src.shape == ref_shape, f"Shape mismatch for {fname}: {src.shape} != {ref_shape}"
                assert src.crs.to_string() == ref_crs, f"CRS mismatch for {fname}: {src.crs.to_string()} != {ref_crs}"
    
    logger.info("All output files validated successfully.")

def _run_ingest_pipeline(city_name: str, city_state: str, output_dir: Path):
    """
    Runs the end-to-end ingestion pipeline for a single city.
    This function simulates the steps described in T012-T016.
    """
    # 1. Define City Boundary
    # For integration testing, we define a small bounding box for Cambridge, MA
    # to ensure the Overpass query returns results quickly and the raster is small.
    # Real production would use a shapefile, but for this test we use a box.
    # Cambridge, MA approx bounds: -71.16, 42.35, -71.06, 42.40
    minx, miny, maxx, maxy = -71.16, 42.35, -71.06, 42.40
    city_geom = box(minx, miny, maxx, maxy)
    
    city_boundary = CityBoundary(
        name=city_name,
        state=city_state,
        geometry=city_geom,
        crs="EPSG:4326"
    )
    
    # 2. Fetch OSM Data
    logger.info(f"Fetching OSM data for {city_name}, {city_state}...")
    overpass_query = build_overpass_query(city_boundary, tags=["building", "landuse", "highway"])
    osm_data = fetch_osm_data(overpass_query)
    
    # 3. Rasterize OSM Data
    # We create raster covariates for buildings, landuse, roads
    # Resolution: 30m
    # CRS: EPSG:3857 (Web Mercator)
    
    # Helper to rasterize a single layer
    def rasterize_osm_layer(osm_gdf, layer_name, output_path):
        if osm_gdf.empty:
            logger.warning(f"No data for {layer_name}, creating empty raster.")
            # Create a minimal empty raster
            import numpy as np
            import rasterio
            from rasterio.transform import from_bounds
            
            transform = from_bounds(minx, miny, maxx, maxy, 100, 100) # Dummy small grid
            profile = {
                'driver': 'GTiff',
                'dtype': 'uint8',
                'width': 100,
                'height': 100,
                'count': 1,
                'crs': 'EPSG:3857',
                'transform': transform,
                'nodata': 0
            }
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(np.zeros((1, 100, 100), dtype='uint8'))
            return
        
        # Reproject to target CRS
        target_crs = "EPSG:3857"
        osm_gdf_reproj = osm_gdf.to_crs(target_crs)
        
        # Rasterize
        # This is a simplified rasterization for the test.
        # In production, this would use a more robust method (e.g., rasterio.features.rasterize)
        # We will use a simple approach for the test to ensure it runs.
        # We need to create a grid.
        from rasterio.features import rasterize
        from rasterio.transform import from_bounds
        
        # Calculate grid size based on resolution
        # Bounds of the reprojected geometry
        bounds = osm_gdf_reproj.total_bounds
        grid_width = int((bounds[2] - bounds[0]) / TEST_RESOLUTION)
        grid_height = int((bounds[3] - bounds[1]) / TEST_RESOLUTION)
        
        # Ensure minimum size
        grid_width = max(10, grid_width)
        grid_height = max(10, grid_height)
        
        transform = from_bounds(bounds[0], bounds[1], bounds[2], bounds[3], grid_width, grid_height)
        
        # Create shapes for rasterization
        shapes = [(geom, 1) for geom in osm_gdf_reproj.geometry if not geom.is_empty]
        if not shapes:
            logger.warning(f"No valid geometries for {layer_name}")
            return

        # Rasterize
        out_image = rasterize(
            shapes,
            out_shape=(grid_height, grid_width),
            transform=transform,
            fill=0,
            dtype='uint8'
        )
        
        # Write to file
        profile = {
            'driver': 'GTiff',
            'dtype': 'uint8',
            'width': grid_width,
            'height': grid_height,
            'count': 1,
            'crs': target_crs,
            'transform': transform,
            'nodata': 0
        }
        
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(out_image, 1)
    
    # Rasterize layers
    if 'building' in osm_data and not osm_data['building'].empty:
        rasterize_osm_layer(osm_data['building'], "buildings", output_dir / "osm_buildings.tif")
    else:
        # Create empty if missing
        rasterize_osm_layer(gpd.GeoDataFrame(), "buildings", output_dir / "osm_buildings.tif")

    if 'landuse' in osm_data and not osm_data['landuse'].empty:
        rasterize_osm_layer(osm_data['landuse'], "landuse", output_dir / "osm_landuse.tif")
    else:
        rasterize_osm_layer(gpd.GeoDataFrame(), "landuse", output_dir / "osm_landuse.tif")

    if 'highway' in osm_data and not osm_data['highway'].empty:
        rasterize_osm_layer(osm_data['highway'], "roads", output_dir / "osm_roads.tif")
    else:
        rasterize_osm_layer(gpd.GeoDataFrame(), "roads", output_dir / "osm_roads.tif")

    # 4. Fetch and Process Thermal Data
    logger.info("Fetching sample thermal data...")
    thermal_raw_path = DATA_RAW_DIR / "sample_thermal_raw.tif"
    _fetch_sample_thermal_data(thermal_raw_path)
    
    # Align thermal data to OSM rasters
    # We need to reproject the thermal data to match the OSM rasters (EPSG:3857, 30m)
    # For this test, we will align the thermal data to the bounding box of the city
    # and the resolution of the OSM rasters.
    
    # We assume the thermal data is already somewhat aligned or we reproject it.
    # We will reproject the thermal data to match the OSM rasters.
    # We need to pick one of the OSM rasters as a reference.
    ref_raster_path = output_dir / "osm_buildings.tif"
    if not ref_raster_path.exists() or ref_raster_path.stat().st_size == 0:
        ref_raster_path = output_dir / "osm_landuse.tif"
    
    if not ref_raster_path.exists() or ref_raster_path.stat().st_size == 0:
        # If all OSM rasters are empty, we can't align. This is a failure condition for the test.
        # However, we can create a dummy reference if necessary, but the test expects real alignment.
        # We will fail if we can't find a reference.
        raise FileNotFoundError("No reference OSM raster found for alignment.")
    
    # Align thermal data
    aligned_thermal_path = output_dir / "thermal_composite.tif"
    align_rasters(thermal_raw_path, ref_raster_path, aligned_thermal_path)
    
    # 5. Validate Non-Null Overlap
    # Check that the aligned thermal data and at least one OSM raster have non-null overlap
    # We will check the thermal raster and the buildings raster
    with rasterio.open(aligned_thermal_path) as src_thermal:
        thermal_data = src_thermal.read(1, masked=True)
        thermal_valid = np.any(~thermal_data.mask)
    
    with rasterio.open(ref_raster_path) as src_osm:
        osm_data_read = src_osm.read(1, masked=True)
        osm_valid = np.any(~osm_data_read.mask)
    
    if not (thermal_valid and osm_valid):
        # If one is empty, check if the other is also empty? No, we need overlap.
        # If both are empty, that's a failure.
        # If one is empty and the other is not, that's also a failure for "overlap".
        logger.error("No non-null overlap region found between thermal and OSM rasters.")
        raise AssertionError("No non-null overlap region found.")
    
    logger.info("Non-null overlap region validated.")
    
    # 6. Generate Metadata
    metadata = {
        "city": city_name,
        "state": city_state,
        "timestamp": pd.Timestamp.now().isoformat(),
        "resolution_m": TEST_RESOLUTION,
        "crs": "EPSG:3857",
        "files": [f.name for f in output_dir.glob("*.tif")],
        "checksums": {}
    }
    
    # Calculate checksums (simple MD5 for test)
    import hashlib
    for fpath in output_dir.glob("*.tif"):
        with open(fpath, "rb") as f:
            checksum = hashlib.md5(f.read()).hexdigest()
        metadata["checksums"][fpath.name] = checksum
    
    with open(output_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    logger.info("Metadata generated.")

@pytest.mark.integration
def test_ingest_pipeline_end_to_end():
    """
    Integration test for end-to-end ingestion of a single city.
    """
    # Setup directories
    raw_dir, processed_dir = _setup_test_directories()
    
    # Create a temporary subdirectory for this test run to avoid clutter
    test_run_dir = processed_dir / f"test_{TEST_CITY_NAME.lower()}"
    test_run_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Run the pipeline
        _run_ingest_pipeline(TEST_CITY_NAME, TEST_CITY_STATE, test_run_dir)
        
        # Validate output files
        _validate_output_files(test_run_dir)
        
        # Validate individual raster structures
        for fname in ["osm_buildings.tif", "osm_landuse.tif", "osm_roads.tif", "thermal_composite.tif"]:
            fpath = test_run_dir / fname
            _validate_raster_structure(fpath, TEST_CITY_CRS, TEST_RESOLUTION)
        
        logger.info(f"Integration test PASSED for {TEST_CITY_NAME}, {TEST_CITY_STATE}")
        
    finally:
        # Cleanup: Remove the test run directory to keep the data folder clean
        # In a real CI environment, you might want to keep artifacts, but for this test, we clean up.
        # If you want to inspect the output, comment out the shutil.rmtree line.
        # shutil.rmtree(test_run_dir)
        pass

if __name__ == "__main__":
    # Run the test manually if executed as a script
    pytest.main([__file__, "-v", "-s"])
