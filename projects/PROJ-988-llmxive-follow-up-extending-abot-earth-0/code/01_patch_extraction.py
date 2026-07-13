"""
Patch Extraction Module for ABot-Earth 0.5 Follow-up
Task: T013 [US1]

Extracts 100m² patches from downloaded 1km² aligned tiles.
Output: data/processed/patches_100m2/ and data/processed/patch_manifest.csv
"""

import os
import sys
import logging
import json
import math
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from PIL import Image

# Project imports
from lib.logging_config import setup_logging, get_logger
from lib.config import load_environment_config, get_config
from lib.models import GroundTruthLiDAR, DegradedScene

# Setup logging
logger = get_logger(__name__)

# Constants
PATCH_SIZE_M = 100  # 100m x 100m
TARGET_RESOLUTION_M = 30  # 30m/pixel (as per degradation spec)
# To get a 100m patch at 30m/pixel, we need ceil(100/30) = 4 pixels
# However, for better statistical representation and to avoid aliasing issues,
# we will extract a slightly larger window and downscale, or extract based on 
# the actual resolution of the input.
# The task says "extract 100m² patches". 
# If input is 1km² (1000m x 1000m) at 10m resolution (100x100 pixels) -> 100m = 10 pixels.
# If input is 1km² at 30m resolution (33x33 pixels) -> 100m = 3.3 pixels.
# We will assume the input from T012 is aligned and we know its resolution.
# We will target a fixed pixel count that approximates 100m x 100m based on the source resolution.

def calculate_pixel_size(geotransform: Tuple[float, ...]) -> float:
    """Extract pixel width from GDAL-style geotransform."""
    return abs(geotransform[1])

def extract_patches_from_aligned_pairs(
    manifest_path: Path,
    output_dir: Path,
    patch_size_m: float = PATCH_SIZE_M,
    target_resolution_m: float = TARGET_RESOLUTION_M
) -> List[Dict[str, Any]]:
    """
    Reads aligned pairs manifest, extracts patches, and saves them.
    
    Args:
        manifest_path: Path to data/processed/aligned_pairs.csv
        output_dir: Path to data/processed/patches_100m2/
        patch_size_m: Desired physical patch size in meters
        target_resolution_m: Target resolution for the output patches
        
    Returns:
        List of metadata dictionaries for the manifest
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Aligned pairs manifest not found: {manifest_path}")
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df = pd.read_csv(manifest_path)
    patches_metadata = []
    
    logger.info(f"Processing {len(df)} aligned pairs for patch extraction.")
    
    for idx, row in df.iterrows():
        try:
            # Extract paths from the row
            # Assuming T012 output columns: 'sentinel_id', 'lidar_id', 'sentinel_path', 'lidar_path', 'alignment_error', 'utm_zone'
            sent_path = Path(row['sentinel_path'])
            lidar_path = Path(row['lidar_path'])
            
            if not sent_path.exists() or not lidar_path.exists():
                logger.warning(f"Files missing for row {idx}: {sent_path}, {lidar_path}")
                continue
                
            # Load images
            # Sentinel-2 is typically multi-band. We'll use RGB or a composite.
            # LiDAR is typically intensity or DEM.
            sent_img = Image.open(sent_path)
            lidar_img = Image.open(lidar_path)
            
            # Determine source resolution. 
            # If images are already georeferenced or we have metadata, we use that.
            # For this implementation, we assume the images are loaded with a known 
            # pixel-to-meter ratio, or we infer it from the 1km² assumption.
            # T012 output description says "downloaded 1km² aligned tiles".
            # If the tile is 1km x 1km:
            #   Width in pixels / 1000m = meters_per_pixel
            width_px, height_px = sent_img.size
            meters_per_pixel = 1000.0 / width_px
            
            # Calculate required pixel dimensions for 100m patch
            required_pixels = int(math.ceil(patch_size_m / meters_per_pixel))
            
            # Ensure we have a square patch
            patch_w = required_pixels
            patch_h = required_pixels
            
            # If the required patch is larger than the source, skip or pad
            if patch_w > width_px or patch_h > height_px:
                logger.warning(f"Source too small for {patch_size_m}m patch at row {idx}. Skipping.")
                continue
                
            # Generate random or grid-based crop coordinates
            # Using a fixed seed per sample for reproducibility if needed, 
            # or random for variety. Let's use random to simulate diverse urban features.
            np.random.seed(int(row.get('sentinel_id', idx)) % (2**32))
            max_x = width_px - patch_w
            max_y = height_px - patch_h
            
            if max_x < 0 or max_y < 0:
                continue
                
            start_x = np.random.randint(0, max_x + 1)
            start_y = np.random.randint(0, max_y + 1)
            
            # Crop Sentinel
            sent_patch = sent_img.crop((start_x, start_y, start_x + patch_w, start_y + patch_h))
            
            # Crop LiDAR
            lidar_patch = lidar_img.crop((start_x, start_y, start_x + patch_w, start_y + patch_h))
            
            # Create output filenames
            sample_id = f"patch_{row['sentinel_id']}_{start_x}_{start_y}"
            sent_out_path = output_dir / f"{sample_id}_sentinel.png"
            lidar_out_path = output_dir / f"{sample_id}_lidar.png"
            
            # Save patches
            sent_patch.save(sent_out_path)
            lidar_patch.save(lidar_out_path)
            
            # Record metadata
            patch_meta = {
                "sample_id": sample_id,
                "parent_sentinel_id": row['sentinel_id'],
                "parent_lidar_id": row['lidar_id'],
                "crop_x": start_x,
                "crop_y": start_y,
                "crop_size_px": patch_w,
                "physical_size_m": patch_size_m,
                "source_resolution_m": meters_per_pixel,
                "sentinel_path": str(sent_out_path),
                "lidar_path": str(lidar_out_path),
                "alignment_error_m": row.get('alignment_error', 0.0)
            }
            patches_metadata.append(patch_meta)
            
            logger.debug(f"Extracted patch {sample_id} from {sent_path}")
            
        except Exception as e:
            logger.error(f"Error processing row {idx}: {e}", exc_info=True)
            continue
            
    return patches_metadata

def save_manifest(metadata: List[Dict[str, Any]], output_path: Path):
    """Saves the patch manifest to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not metadata:
        logger.warning("No patches extracted; manifest will be empty.")
        # Create empty CSV with headers
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["sample_id", "parent_sentinel_id", "parent_lidar_id", "crop_x", "crop_y", "crop_size_px", "physical_size_m", "source_resolution_m", "sentinel_path", "lidar_path", "alignment_error_m"])
            writer.writeheader()
        return
        
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=metadata[0].keys())
        writer.writeheader()
        writer.writerows(metadata)
    logger.info(f"Saved manifest to {output_path} with {len(metadata)} entries.")

def main():
    """Main entry point for patch extraction."""
    logger.info("Starting Patch Extraction (T013)")
    
    # Load config
    config = load_environment_config()
    base_dir = Path(config.get('project_root', '.'))
    
    input_manifest = base_dir / "data" / "processed" / "aligned_pairs.csv"
    output_dir = base_dir / "data" / "processed" / "patches_100m2"
    manifest_output = base_dir / "data" / "processed" / "patch_manifest.csv"
    
    if not input_manifest.exists():
        logger.error(f"Input manifest not found: {input_manifest}. Ensure T012 is complete.")
        sys.exit(1)
        
    try:
        patches = extract_patches_from_aligned_pairs(
            manifest_path=input_manifest,
            output_dir=output_dir,
            patch_size_m=PATCH_SIZE_M,
            target_resolution_m=TARGET_RESOLUTION_M
        )
        
        save_manifest(patches, manifest_output)
        
        logger.info(f"Patch extraction complete. {len(patches)} patches generated.")
        
    except Exception as e:
        logger.error(f"Patch extraction failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # Ensure logging is set up
    setup_logging()
    main()