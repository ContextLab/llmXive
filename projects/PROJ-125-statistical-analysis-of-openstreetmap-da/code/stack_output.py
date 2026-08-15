"""
stack_output.py

Implements the logic to create aligned GeoTIFF stacks and generate metadata
for the Urban Heat Island analysis pipeline.

This module satisfies Task T015: Create aligned GeoTIFF stack output.
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, transform_bounds, reproject, Resampling
from rasterio.mask import mask
from shapely.geometry import mapping

# Local imports
from config import get_path, get_city_bounds, get_city_crs
from utils.logging import get_logger

logger = get_logger(__name__)

def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal checksum string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_metadata(
    input_files: List[Path],
    output_files: List[Path],
    city_name: str,
    crs: str,
    resolution: float = 30.0,
    align_params: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Generate metadata dictionary for the aligned raster stack.

    Args:
        input_files: List of source raster paths.
        output_files: List of aligned output raster paths.
        city_name: Name of the city processed.
        crs: Target CRS string (e.g., 'EPSG:32618').
        resolution: Target resolution in meters.
        align_params: Additional alignment parameters used.

    Returns:
        Metadata dictionary.
    """
    timestamp = datetime.utcnow().isoformat()
    
    files_meta = []
    for inp, out in zip(input_files, output_files):
        file_meta = {
            "source_path": str(inp),
            "output_path": str(out),
            "checksum": compute_file_checksum(out),
            "file_size_bytes": out.stat().st_size,
            "processed_at": timestamp
        }
        files_meta.append(file_meta)

    metadata = {
        "project": "PROJ-125-statistical-analysis-of-openstreetmap-da",
        "task": "T015",
        "city": city_name,
        "crs": crs,
        "resolution_meters": resolution,
        "generated_at": timestamp,
        "input_files": files_meta,
        "alignment_parameters": align_params or {}
    }
    return metadata

def write_metadata_json(metadata: Dict[str, Any], output_path: Path) -> None:
    """
    Write metadata dictionary to a JSON file.

    Args:
        metadata: Metadata dictionary.
        output_path: Path to write the JSON file.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata written to {output_path}")

def create_aligned_raster_stack(
    city_name: str,
    input_rasters: List[Dict[str, Any]],
    output_dir: Optional[Path] = None
) -> List[Path]:
    """
    Create an aligned stack of GeoTIFFs from input rasters.

    This function:
    1. Determines the target CRS and extent from the city boundary.
    2. Selects the first valid raster as the reference template (or creates one).
    3. Reprojects and resamples all rasters to match the reference grid.
    4. Writes aligned GeoTIFFs to the output directory.

    Args:
        city_name: Name of the city (used to fetch boundary).
        input_rasters: List of dicts with keys: 'path', 'type' (covariate/temp).
    output_dir: Directory to write aligned rasters. Defaults to data/processed.

    Returns:
        List of paths to the created aligned GeoTIFFs.
    """
    if not input_rasters:
        raise ValueError("No input rasters provided for alignment.")

    # 1. Setup paths and CRS
    if output_dir is None:
        output_dir = get_path("data_processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    city_bounds = get_city_bounds(city_name)
    target_crs = get_city_crs(city_name)
    logger.info(f"Target CRS for {city_name}: {target_crs}")

    # 2. Determine reference grid
    # We use the first raster as the initial reference, but we must ensure
    # the grid aligns with the city boundary extent and a fixed resolution.
    ref_raster_info = None
    ref_transform = None
    ref_width = None
    ref_height = None
    
    # Resolution in meters (standardized coarse resolution per T014)
    target_resolution = 30.0 

    # Calculate target extent from city boundary in target CRS
    # city_bounds is typically in lat/lon (EPSG:4326) from config
    # We need to transform it to target_crs
    from shapely.ops import transform
    from pyproj import Transformer
    
    transformer = Transformer.from_crs("EPSG:4326", target_crs, always_xy=True)
    transformed_bounds = transform(transformer.transform, city_bounds)
    
    minx, miny, maxx, maxy = transformed_bounds.bounds
    
    # Define a grid that covers the bounds with a slight padding if needed
    # For strict alignment, we snap to a grid start
    start_x = np.floor(minx / target_resolution) * target_resolution
    start_y = np.floor(miny / target_resolution) * target_resolution
    
    width = int(np.ceil((maxx - start_x) / target_resolution))
    height = int(np.ceil((maxy - start_y) / target_resolution))

    # Create a synthetic reference transform
    ref_transform = rasterio.transform.from_bounds(
        start_x, start_y, start_x + width * target_resolution, 
        start_y + height * target_resolution, width, height
    )
    ref_width = width
    ref_height = height

    logger.info(f"Reference grid: {width}x{height}, Resolution: {target_resolution}m")

    output_paths = []
    input_paths = [Path(r['path']) for r in input_rasters]

    # 3. Process each raster
    for i, raster_info in enumerate(input_rasters):
        src_path = Path(raster_info['path'])
        if not src_path.exists():
            raise FileNotFoundError(f"Input raster not found: {src_path}")

        # Determine output filename
        stem = src_path.stem
        output_filename = f"aligned_{stem}.tif"
        output_path = output_dir / output_filename

        logger.info(f"Processing {src_path} -> {output_path}")

        with rasterio.open(src_path) as src:
            # Determine resampling method based on data type
            # If it's a temperature layer (continuous) or categorical?
            # Assuming continuous for temp, nearest for categorical if specified
            resampling = Resampling.bilinear
            if raster_info.get('type') == 'categorical':
                resampling = Resampling.nearest

            # Reproject and align
            # We use the calculated reference transform and dimensions
            dst_crs = target_crs
            
            # Handle nodata
            nodata = src.nodata
            if nodata is None:
                nodata = -9999

            with rasterio.open(
                output_path,
                'w',
                driver='GTiff',
                height=ref_height,
                width=ref_width,
                count=src.count,
                dtype=src.dtypes[0],
                crs=dst_crs,
                transform=ref_transform,
                nodata=nodata
            ) as dst:
                for idx in range(1, src.count + 1):
                    reproject(
                        source=rasterio.band(src, idx),
                        destination=rasterio.band(dst, idx),
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=ref_transform,
                        dst_crs=dst_crs,
                        resampling=resampling,
                        src_nodata=nodata,
                        dst_nodata=nodata
                    )
            
            logger.info(f"Aligned raster written: {output_path}")
            output_paths.append(output_path)

    return output_paths

def main():
    """
    Main entry point for T015.
    Reads configuration to find input rasters (simulated here as a list for demo,
    but in a real pipeline, this would be populated by T012/T013 outputs).
    """
    # In a real pipeline, the list of input rasters would come from the previous
    # steps (T012/T013) or a manifest file.
    # For this task, we assume the existence of processed rasters in data/raw or similar
    # that need to be aligned.
    
    # Since T012/T013 are marked complete but we don't see their outputs in the
    # environment, we will attempt to find files that match expected patterns
    # or fail loudly if not found.
    
    city_name = "New York" # Default, can be overridden by env or args
    
    # Simulate finding input rasters
    # In a real scenario, T012/T013 would write to data/raw/
    raw_dir = get_path("data_raw")
    if not raw_dir.exists():
        logger.error(f"Raw data directory {raw_dir} does not exist. Cannot proceed.")
        return

    # Look for tifs
    input_candidates = list(raw_dir.glob("*.tif")) + list(raw_dir.glob("*.tiff"))
    
    if not input_candidates:
        logger.warning(f"No input rasters found in {raw_dir}. "
                       "This task requires real input data from T012/T013.")
        # In a strict pipeline, we would exit 1.
        # For the purpose of this implementation, we raise an error.
        raise FileNotFoundError("No input rasters found. Please run T012 and T013 first.")

    input_rasters = []
    for p in input_candidates:
        # Simple heuristic: if 'temp' in name, it's target, else covariate
        r_type = "temperature" if "temp" in p.name.lower() else "covariate"
        input_rasters.append({"path": str(p), "type": r_type})

    logger.info(f"Found {len(input_rasters)} input rasters to align.")

    try:
        output_paths = create_aligned_raster_stack(city_name, input_rasters)
        
        # Generate metadata
        metadata = generate_metadata(
            input_files=[Path(r['path']) for r in input_rasters],
            output_files=output_paths,
            city_name=city_name,
            crs=get_city_crs(city_name),
            resolution=30.0
        )
        
        metadata_path = get_path("data_processed") / "metadata.json"
        write_metadata_json(metadata, metadata_path)
        
        logger.info("T015 completed successfully.")
        
    except Exception as e:
        logger.error(f"Failed to create aligned stack: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
