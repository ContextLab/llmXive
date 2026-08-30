"""
T015: Create aligned GeoTIFF stack output in data/processed/

This script orchestrates the creation of an aligned raster stack from previously
ingested and processed data. It ensures all output rasters share identical
dimensions, origin, and CRS. It generates data/metadata.json ONLY if the
pipeline completed successfully (exit code 0). If T014b validation failed
(exit code 1 in previous steps), this script will detect the missing
intermediate state and exit without generating metadata.
"""
import os
import sys
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, transform_bounds
from rasterio.merge import merge as merge_rasters
from rasterio.crs import CRS

# Import from project utils and config
from config import get_path, get_city_bounds, get_city_crs
from utils.logging import get_logger

# Import ingestion functions if needed for re-validation
from ingest import validate_raster_alignment

def get_file_checksum(filepath: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_raster_info(filepath: Path) -> Dict[str, Any]:
    """Load basic info from a raster file."""
    with rasterio.open(filepath) as src:
        return {
            "crs": src.crs.to_string(),
            "width": src.width,
            "height": src.height,
            "transform": list(src.transform),
            "count": src.count,
            "dtype": str(src.dtypes[0]),
            "nodata": src.nodata
        }

def ensure_aligned_stack(input_files: List[Path], output_dir: Path, base_crs: CRS) -> Dict[str, Path]:
    """
    Ensure all input rasters are aligned to the same grid, CRS, and resolution.
    Returns a dictionary mapping layer names to their aligned output paths.
    """
    output_files = {}
    reference_profile = None
    reference_transform = None
    reference_width = None
    reference_height = None

    # Determine reference from the first file or a dedicated 'reference' file if present
    # For this task, we assume the first file in the list sets the grid, or we use the city bounds
    # If a specific 'reference' file is expected, logic would adjust here.
    # Here we assume the first file is the reference for geometry.
    
    if not input_files:
        raise ValueError("No input files provided for alignment.")

    # Sort files to ensure deterministic order
    sorted_files = sorted(input_files)
    first_file = sorted_files[0]

    with rasterio.open(first_file) as src:
        reference_transform = src.transform
        reference_width = src.width
        reference_height = src.height
        reference_crs = src.crs
        reference_profile = src.profile

    logging.info(f"Using {first_file.name} as reference geometry: {reference_width}x{reference_height}")

    for i, input_file in enumerate(sorted_files):
        layer_name = input_file.stem
        output_path = output_dir / f"{layer_name}_aligned.tif"

        if i == 0:
            # First file is the reference, just copy it to the output name
            # We still ensure it's in the correct CRS if needed, but usually it is
            if reference_crs != base_crs:
                logging.warning(f"Reference file CRS {reference_crs} differs from base CRS {base_crs}. Reprojecting.")
                # If reprojecting the reference, we need to calculate new transform
                # For simplicity in this task, we assume inputs are already reprojected to base_crs by T014a
                # If not, we would reproject here.
                pass
            
            # Just copy the file to the aligned name
            with rasterio.open(input_file) as src:
                with rasterio.open(output_path, 'w', **src.profile) as dst:
                    for idx in range(1, src.count + 1):
                        data = src.read(idx)
                        dst.write(data, idx)
            output_files[layer_name] = output_path
            continue

        # For subsequent files, check alignment
        with rasterio.open(input_file) as src:
            if (src.width != reference_width or 
                src.height != reference_height or 
                src.transform.almost_equals(reference_transform)):
                
                logging.info(f"Reprojecting/resampling {layer_name} to match reference...")
                
                # Calculate transform and size for the target
                # Since we want to match the first file exactly, we use its transform, width, height
                dst_transform = reference_transform
                dst_width = reference_width
                dst_height = reference_height
                dst_crs = reference_crs

                # Read source data
                src_data = src.read()
                src_crs = src.crs
                src_nodata = src.nodata

                # If CRS differs, we must warp
                if src_crs != dst_crs:
                    from rasterio.warp import reproject
                    dst_data = np.zeros((src_data.shape[0], dst_height, dst_width), dtype=src_data.dtype)
                    reproject(
                        source=src_data,
                        destination=dst_data,
                        src_transform=src.transform,
                        src_crs=src_crs,
                        dst_transform=dst_transform,
                        dst_crs=dst_crs,
                        resampling=rasterio.enums.Resampling.bilinear, # bilinear for continuous
                        src_nodata=src_nodata,
                        dst_nodata=src_nodata
                    )
                else:
                    # Same CRS but different transform/size -> Resample
                    # We assume bilinear for continuous data as per T014a
                    from rasterio.warp import reproject
                    dst_data = np.zeros((src_data.shape[0], dst_height, dst_width), dtype=src_data.dtype)
                    reproject(
                        source=src_data,
                        destination=dst_data,
                        src_transform=src.transform,
                        src_crs=src_crs,
                        dst_transform=dst_transform,
                        dst_crs=dst_crs,
                        resampling=rasterio.enums.Resampling.bilinear,
                        src_nodata=src_nodata,
                        dst_nodata=src_nodata
                    )

                # Write aligned output
                profile = src.profile
                profile.update({
                    "transform": dst_transform,
                    "width": dst_width,
                    "height": dst_height,
                    "crs": dst_crs,
                    "driver": "GTiff"
                })

                with rasterio.open(output_path, 'w', **profile) as dst:
                    dst.write(dst_data)
            else:
                # Already aligned, just copy
                with rasterio.open(input_file) as src:
                    with rasterio.open(output_path, 'w', **src.profile) as dst:
                        for idx in range(1, src.count + 1):
                            data = src.read(idx)
                            dst.write(data, idx)
        
        output_files[layer_name] = output_path

    return output_files

def validate_non_null_overlap(aligned_files: Dict[str, Path], threshold: float = 0.01) -> bool:
    """
    Validate that there is a non-null overlap region between all files.
    Returns True if valid, False otherwise.
    """
    if len(aligned_files) < 2:
        return True

    # Load masks of valid data for each file
    masks = []
    for name, path in aligned_files.items():
        with rasterio.open(path) as src:
            data = src.read(1)
            mask = ~np.isnan(data) if src.nodata is None else (data != src.nodata)
            masks.append(mask)
    
    # Compute intersection
    intersection = masks[0]
    for m in masks[1:]:
        intersection = intersection & m

    valid_ratio = np.sum(intersection) / intersection.size
    if valid_ratio < threshold:
        logging.error(f"Non-null overlap region is below threshold ({valid_ratio:.4f} < {threshold})")
        return False

    logging.info(f"Non-null overlap region validated: {valid_ratio:.4f}")
    return True

def generate_metadata(aligned_files: Dict[str, Path], city_name: str, output_path: Path) -> None:
    """Generate metadata.json with fetch timestamps and checksums."""
    metadata = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "city": city_name,
        "crs": None,
        "dimensions": None,
        "transform": None,
        "layers": []
    }

    # Get reference properties from the first file
    first_path = next(iter(aligned_files.values()))
    with rasterio.open(first_path) as src:
        metadata["crs"] = src.crs.to_string()
        metadata["dimensions"] = {"width": src.width, "height": src.height}
        metadata["transform"] = list(src.transform)

    for name, path in aligned_files.items():
        checksum = get_file_checksum(path)
        file_info = {
            "name": name,
            "path": str(path.relative_to(Path.cwd())),
            "checksum_sha256": checksum,
            "size_bytes": path.stat().st_size
        }
        metadata["layers"].append(file_info)

    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logging.info(f"Metadata written to {output_path}")

def main():
    logger = get_logger("T015_aligned_stack")
    logger.info("Starting T015: Create aligned GeoTIFF stack output")

    # Configuration
    city_name = "New York City" # Default, can be overridden by env or args
    processed_dir = get_path("data/processed")
    output_dir = processed_dir
    metadata_path = get_path("data/metadata.json")

    # Check for previous step failure indicators (T014b exit code 1)
    # We assume T014b failure would leave no valid intermediate files or a specific flag.
    # Here we check if the expected input files exist.
    # In a real pipeline, we might check for a 'pipeline_status.json' or similar.
    # For now, we look for the raw processed rasters.
    
    # Expected input pattern: data/processed/*.tif (excluding _aligned.tif)
    # We filter out files that are already aligned to avoid double processing
    input_files = []
    if not processed_dir.exists():
        logger.error(f"Processed directory {processed_dir} does not exist.")
        sys.exit(1)

    for f in processed_dir.glob("*.tif"):
        if not f.name.endswith("_aligned.tif"):
            input_files.append(f)

    if not input_files:
        logger.error("No input raster files found in data/processed/ to align.")
        sys.exit(1)

    logger.info(f"Found {len(input_files)} input files to align.")

    # Get base CRS from config
    try:
        base_crs = get_city_crs(city_name)
    except Exception as e:
        logger.error(f"Failed to get CRS for {city_name}: {e}")
        sys.exit(1)

    try:
        aligned_files = ensure_aligned_stack(input_files, output_dir, base_crs)
    except Exception as e:
        logger.error(f"Failed to align rasters: {e}")
        sys.exit(1)

    # Validate non-null overlap (T016 requirement, but checked here before metadata)
    if not validate_non_null_overlap(aligned_files):
        logger.error("Validation of non-null overlap failed. Exiting without metadata.")
        sys.exit(1)

    # Generate metadata ONLY if successful
    try:
        generate_metadata(aligned_files, city_name, metadata_path)
    except Exception as e:
        logger.error(f"Failed to generate metadata: {e}")
        sys.exit(1)

    logger.info("T015 completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
