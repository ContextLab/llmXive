"""
Stack Output Module (T015)

Creates aligned GeoTIFF stack output in data/processed/ and generates
data/metadata.json ONLY if the pipeline completed successfully.

This module implements T015: Create aligned GeoTIFF stack output.
It ensures all output rasters share identical dimensions, origin, and CRS.
It also generates metadata.json with fetch timestamps and checksums.
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
from rasterio.features import geometry_mask
from shapely.geometry import box, mapping
import geopandas as gpd

from config import get_path, get_city_bounds, get_city_crs
from utils.logging import get_logger

logger = get_logger(__name__)


def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA256 checksum of a file.

    Args:
        file_path: Path to the file

    Returns:
        SHA256 checksum as hex string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def generate_metadata(
    input_files: List[Path],
    output_files: List[Path],
    city: str,
    bounds: Dict[str, Any],
    crs: str,
    resolution: float = 30.0,
    timestamps: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Generate metadata dictionary for the aligned raster stack.

    Args:
        input_files: List of input file paths
        output_files: List of output file paths
        city: City name
        bounds: Bounding box dictionary
        crs: Coordinate reference system
        resolution: Target resolution in meters
        timestamps: Optional dictionary of fetch timestamps

    Returns:
        Metadata dictionary
    """
    metadata = {
        "project": "llmXive-statistical-analysis-of-openstreetmap-data",
        "task": "T015",
        "city": city,
        "crs": crs,
        "resolution_meters": resolution,
        "bounds": bounds,
        "output_files": [str(f) for f in output_files],
        "input_files": [str(f) for f in input_files],
        "checksums": {},
        "timestamp": timestamps.get("generation", None) if timestamps else None
    }

    # Compute checksums for output files
    for f in output_files:
        if f.exists():
            metadata["checksums"][f.name] = compute_file_checksum(f)

    return metadata


def write_metadata_json(metadata: Dict[str, Any], output_path: Path) -> None:
    """
    Write metadata dictionary to a JSON file.

    Args:
        metadata: Metadata dictionary
        output_path: Path to output JSON file
    """
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata written to {output_path}")


def create_aligned_raster_stack(
    input_rasters: List[Path],
    output_dir: Path,
    city: str,
    target_resolution: float = 30.0
) -> List[Path]:
    """
    Create an aligned stack of GeoTIFF rasters with identical dimensions,
    origin, and CRS.

    Args:
        input_rasters: List of input raster file paths
        output_dir: Directory to write aligned rasters
        city: City name for bounds retrieval
        target_resolution: Target resolution in meters

    Returns:
        List of output file paths
    """
    if not input_rasters:
        raise ValueError("No input rasters provided for alignment")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Get city bounds and CRS
    bounds = get_city_bounds(city)
    target_crs = get_city_crs(city)

    if not bounds:
        raise ValueError(f"No bounds found for city: {city}")

    # Convert bounds to WKT geometry for masking
    minx, miny, maxx, maxy = bounds['minx'], bounds['miny'], bounds['maxx'], bounds['maxy']
    bounds_geom = box(minx, miny, maxx, maxy)

    # Read first raster to establish reference grid
    ref_raster = rasterio.open(input_rasters[0])
    ref_transform = ref_raster.transform
    ref_crs = ref_raster.crs

    # Calculate target transform based on bounds and resolution
    target_transform, target_width, target_height = calculate_default_transform(
        ref_crs,
        target_crs,
        ref_raster.width,
        ref_raster.height,
        *ref_raster.bounds,
        resolution=target_resolution
    )

    # Adjust transform to align with bounds
    # Ensure the grid aligns with the bounding box
    target_minx, target_miny = target_transform * (0, target_height)
    target_maxx, target_maxy = target_transform * (target_width, 0)

    # Refine bounds to match grid
    final_minx = minx
    final_miny = miny
    final_maxx = maxx
    final_maxy = maxy

    # Recalculate grid based on final bounds
    final_transform = rasterio.transform.from_bounds(
        final_minx, final_miny, final_maxx, final_maxy,
        int((final_maxx - final_minx) / target_resolution),
        int((final_maxy - final_miny) / target_resolution)
    )
    final_width = int((final_maxx - final_minx) / target_resolution)
    final_height = int((final_maxy - final_miny) / target_resolution)

    output_paths = []

    for i, input_path in enumerate(input_rasters):
        logger.info(f"Processing raster {i+1}/{len(input_rasters)}: {input_path.name}")

        with rasterio.open(input_path) as src:
            # Determine output profile
            out_profile = src.profile.copy()
            out_profile.update({
                'crs': target_crs,
                'transform': final_transform,
                'width': final_width,
                'height': final_height,
                'driver': 'GTiff',
                'compress': 'lzw'
            })

            # Create output filename
            output_name = f"{input_path.stem}_aligned.tif"
            output_path = output_dir / output_name

            # Reproject and resample
            with rasterio.open(output_path, 'w', **out_profile) as dst:
                for idx in range(src.count):
                    reproject(
                        source=rasterio.band(src, idx),
                        destination=rasterio.band(dst, idx),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=final_transform,
                        dst_crs=target_crs,
                        resampling=Resampling.bilinear if src.meta['dtype'] in ['float32', 'float64'] else Resampling.nearest,
                        src_nodata=src.nodata,
                        dst_nodata=src.nodata
                    )

            output_paths.append(output_path)
            logger.info(f"  -> Wrote {output_path}")

    ref_raster.close()
    return output_paths


def validate_non_null_overlap(
    output_files: List[Path],
    bounds: Dict[str, Any],
    tolerance: float = 0.1
) -> bool:
    """
    Validate that all output rasters have non-null values in the overlap region.

    Args:
        output_files: List of output raster file paths
        bounds: Bounding box dictionary
        tolerance: Maximum allowed fraction of null values

    Returns:
        True if validation passes, False otherwise
    """
    if len(output_files) < 2:
        logger.warning("Less than 2 rasters provided; skipping overlap validation")
        return True

    minx, miny, maxx, maxy = bounds['minx'], bounds['miny'], bounds['maxx'], bounds['maxy']

    # Read all rasters
    rasters = [rasterio.open(f) for f in output_files]

    try:
        # Sample points in the overlap region
        sample_points = []
        step_x = (maxx - minx) / 10
        step_y = (maxy - miny) / 10

        for i in range(10):
            for j in range(10):
                x = minx + step_x * i + step_x / 2
                y = miny + step_y * j + step_y / 2
                sample_points.append((x, y))

        # Check each raster at sample points
        null_fractions = []
        for raster in rasters:
            null_count = 0
            for x, y in sample_points:
                try:
                    value = raster.sample([(x, y)], masked=True)
                    if value.mask[0] or np.isnan(value[0, 0]):
                        null_count += 1
                except Exception:
                    null_count += 1

            null_frac = null_count / len(sample_points)
            null_fractions.append(null_frac)

        # Check if any raster has too many nulls
        max_null_frac = max(null_fractions)
        if max_null_frac > tolerance:
            logger.error(f"Overlap validation failed: max null fraction {max_null_frac:.2f} > {tolerance}")
            return False

        logger.info(f"Overlap validation passed: max null fraction {max_null_frac:.2f}")
        return True

    finally:
        for r in rasters:
            r.close()


def main():
    """
    Main entry point for T015: Create aligned GeoTIFF stack output.

    This function:
    1. Reads input rasters from data/raw/
    2. Aligns them to a common CRS, origin, and resolution
    3. Writes aligned rasters to data/processed/
    4. Generates data/metadata.json with checksums and timestamps
    """
    logger.info("Starting T015: Create aligned GeoTIFF stack output")

    # Configuration
    city = "new_york"  # Default, can be overridden via args or config
    input_dir = get_path("data_raw")
    output_dir = get_path("data_processed")
    metadata_path = get_path("data_metadata")

    # Ensure directories exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find input rasters
    input_rasters = list(input_dir.glob("*.tif")) + list(input_dir.glob("*.tiff"))

    if not input_rasters:
        logger.error(f"No input rasters found in {input_dir}")
        logger.error("T015 cannot proceed without input data")
        return 1

    logger.info(f"Found {len(input_rasters)} input rasters")

    # Create aligned stack
    try:
        output_files = create_aligned_raster_stack(
            input_rasters=input_rasters,
            output_dir=output_dir,
            city=city,
            target_resolution=30.0
        )
    except Exception as e:
        logger.error(f"Failed to create aligned raster stack: {e}")
        return 1

    if not output_files:
        logger.error("No output files were created")
        return 1

    # Validate non-null overlap
    bounds = get_city_bounds(city)
    if not bounds:
        logger.warning(f"Could not retrieve bounds for {city}; skipping overlap validation")
    else:
        if not validate_non_null_overlap(output_files, bounds, tolerance=0.1):
            logger.error("Overlap validation failed; exiting without generating metadata")
            return 1

    # Generate metadata
    import datetime
    timestamps = {
        "generation": datetime.datetime.now().isoformat()
    }

    metadata = generate_metadata(
        input_files=input_rasters,
        output_files=output_files,
        city=city,
        bounds=bounds,
        crs=get_city_crs(city),
        resolution=30.0,
        timestamps=timestamps
    )

    write_metadata_json(metadata, metadata_path)

    logger.info("T015 completed successfully")
    return 0


if __name__ == "__main__":
    exit(main())
