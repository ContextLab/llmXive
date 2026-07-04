"""
Task T015: Create aligned GeoTIFF stack output and metadata.

This module orchestrates the final assembly of aligned rasters into a
standardized stack in data/processed/ and generates a metadata.json file
containing fetch timestamps and file checksums.
"""
import os
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
import rasterio
from rasterio.transform import Affine
from rasterio.crs import CRS
from rasterio.warp import calculate_default_transform, reproject, Resampling
import xarray as xr

from config import DATA_PROCESSED_PATH, PROJECT_ROOT
from utils.logging import get_main_logger
from ingest import create_aligned_stack, validate_non_null_overlap

logger = get_main_logger()


def compute_file_checksum(filepath: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def generate_metadata(
    input_files: List[Path],
    output_stack_path: Path,
    stack_info: Dict[str, Any],
    fetch_timestamps: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Generate metadata dictionary for the aligned stack.

    Args:
        input_files: List of source raster paths.
        output_stack_path: Path to the output GeoTIFF stack.
        stack_info: Information about the output stack (dims, crs, etc.).
        fetch_timestamps: Optional dict mapping source filenames to fetch times.

    Returns:
        Metadata dictionary.
    """
    metadata = {
        "project": "PROJ-125-statistical-analysis-of-openstreetmap-da",
        "task": "T015",
        "output_file": str(output_stack_path.relative_to(PROJECT_ROOT)),
        "output_checksum": compute_file_checksum(output_stack_path),
        "stack_dimensions": stack_info.get("dimensions", {}),
        "crs": str(stack_info.get("crs", "")),
        "resolution": stack_info.get("resolution", {}),
        "source_files": [],
        "fetch_timestamps": fetch_timestamps or {},
        "validation": {
            "non_null_overlap": stack_info.get("non_null_overlap", False)
        }
    }

    for src_path in input_files:
        src_info = {
            "path": str(src_path.relative_to(PROJECT_ROOT)),
            "checksum": compute_file_checksum(src_path)
        }
        metadata["source_files"].append(src_info)

    return metadata


def write_metadata_json(metadata: Dict[str, Any], output_path: Path) -> None:
    """Write metadata dictionary to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, default=str)
    logger.info(f"Metadata written to {output_path}")


def create_and_save_aligned_stack(
    input_paths: List[Path],
    output_name: str = "aligned_stack.tif",
    target_resolution: float = 30.0,
    target_crs: str = "EPSG:3857"
) -> Path:
    """
    Align multiple rasters and save as a single GeoTIFF stack.

    Args:
        input_paths: List of input raster paths.
        output_name: Name for the output GeoTIFF.
        target_resolution: Target resolution in meters.
        target_crs: Target CRS string.

    Returns:
        Path to the created output file.
    """
    if not input_paths:
        raise ValueError("No input paths provided for stacking.")

    output_path = DATA_PROCESSED_PATH / output_name
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Creating aligned stack from {len(input_paths)} files...")
    
    # Use the existing ingest function to align rasters
    # This assumes align_rasters returns a list of aligned raster paths or handles the process
    # Since create_aligned_stack is the high-level function, we use it
    stack_info = create_aligned_stack(
        input_paths, 
        output_path, 
        target_resolution=target_resolution,
        target_crs=target_crs
    )

    # Validate non-null overlap
    is_valid = validate_non_null_overlap(output_path)
    stack_info["non_null_overlap"] = is_valid

    if not is_valid:
        logger.warning("Non-null overlap validation failed, but proceeding as per spec (≤10% missing allowed)")

    return output_path, stack_info


def main():
    """
    Main entry point for T015.
    Reads aligned rasters from data/raw (or intermediate), aligns them,
    writes to data/processed, and generates metadata.json.
    """
    logger.info("Starting T015: Create aligned GeoTIFF stack output")

    # Define input paths (assuming T014 produced aligned but unstacked files in data/raw or intermediate)
    # For this implementation, we look for .tif files in data/raw that were processed by T014
    # In a real pipeline, these would be the outputs of T014
    raw_dir = PROJECT_ROOT / "data" / "raw"
    if not raw_dir.exists():
        # Fallback to processed if raw doesn't exist (for testing)
        raw_dir = PROJECT_ROOT / "data" / "processed"
    
    if not raw_dir.exists():
        logger.error(f"Input directory {raw_dir} does not exist.")
        return

    input_files = list(raw_dir.glob("*.tif"))
    if not input_files:
        input_files = list(raw_dir.glob("*.tiff"))
    
    if not input_files:
        logger.warning("No input .tif files found in data/raw. Creating a placeholder stack for demonstration.")
        # In a real scenario, this would fail loudly. 
        # For the purpose of this task, we assume T014 produced files.
        # If no files exist, we cannot proceed with real data.
        raise FileNotFoundError("No input raster files found. Ensure T014 has populated data/raw/.")

    logger.info(f"Found {len(input_files)} input rasters: {[f.name for f in input_files]}")

    # Create the aligned stack
    output_path, stack_info = create_and_save_aligned_stack(
        input_files,
        output_name="nyc_aligned_stack.tif",
        target_resolution=30.0,
        target_crs="EPSG:3857"
    )

    logger.info(f"Aligned stack created at {output_path}")

    # Generate and write metadata
    # Note: In a full pipeline, fetch_timestamps would be passed from T013
    metadata = generate_metadata(
        input_files,
        output_path,
        stack_info
    )

    metadata_path = PROJECT_ROOT / "data" / "metadata.json"
    write_metadata_json(metadata, metadata_path)

    logger.info("T015 completed successfully.")


if __name__ == "__main__":
    main()
