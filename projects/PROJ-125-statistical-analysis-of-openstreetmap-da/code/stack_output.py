"""
stack_output.py

Implements T015: Create aligned GeoTIFF stack output in data/processed/

This module ensures all output rasters share identical dimensions, origin, and CRS.
It generates data/metadata.json with fetch timestamps and checksums.
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
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
from rasterio.merge import merge as merge_rasters
from shapely.geometry import mapping

from config import get_path, get_city_crs, get_city_bounds
from utils.logging import get_logger
from models.raster import RasterCovariate, TemperatureRaster

logger = get_logger(__name__)

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute a cryptographic checksum of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hex digest of the file checksum
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_obj = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def generate_metadata(
    input_files: List[Path],
    output_files: List[Path],
    city: str,
    crs: str,
    resolution: float,
    bounds: Dict[str, float],
    description: str = "Aligned OSM and Satellite Raster Stack"
) -> Dict[str, Any]:
    """
    Generate metadata dictionary for the aligned raster stack.
    
    Args:
        input_files: List of input file paths
        output_files: List of output file paths
        city: City name
        crs: Coordinate Reference System
        resolution: Resolution in meters
        bounds: Dictionary with 'minx', 'miny', 'maxx', 'maxy'
        description: Description of the dataset
        
    Returns:
        Metadata dictionary
    """
    metadata = {
        "created_at": datetime.utcnow().isoformat() + "Z",
        "project": "PROJ-125-statistical-analysis-of-openstreetmap-da",
        "task": "T015",
        "city": city,
        "crs": crs,
        "resolution_meters": resolution,
        "bounds": bounds,
        "description": description,
        "input_files": [],
        "output_files": [],
        "checksums": {}
    }
    
    # Process input files
    for f in input_files:
        if f.exists():
            metadata["input_files"].append({
                "path": str(f),
                "size_bytes": f.stat().st_size,
                "checksum": compute_file_checksum(f)
            })
        else:
            logger.warning(f"Input file not found: {f}")
    
    # Process output files
    for f in output_files:
        if f.exists():
          metadata["output_files"].append({
              "path": str(f),
              "size_bytes": f.stat().st_size,
              "checksum": compute_file_checksum(f)
          })
          # Add to top-level checksums for quick reference
          metadata["checksums"][f.name] = compute_file_checksum(f)
        else:
            logger.warning(f"Output file not found: {f}")
            
    return metadata

def write_metadata_json(metadata: Dict[str, Any], output_path: Path) -> None:
    """
    Write metadata dictionary to a JSON file.
    
    Args:
        metadata: Metadata dictionary
        output_path: Path to write the JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata written to {output_path}")

def create_aligned_raster_stack(
    input_rasters: List[Path],
    output_dir: Path,
    target_crs: Optional[str] = None,
    target_resolution: float = 30.0,
    city_name: str = "unknown"
) -> List[Path]:
    """
    Create an aligned stack of GeoTIFFs with identical dimensions, origin, and CRS.
    
    Args:
        input_rasters: List of input GeoTIFF paths
        output_dir: Directory to write aligned rasters
        target_crs: Target CRS (defaults to city CRS from config)
        target_resolution: Target resolution in meters (default 30m)
        city_name: Name of the city for metadata
        
    Returns:
        List of paths to the aligned output rasters
    """
    if not input_rasters:
        raise ValueError("No input rasters provided")
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if target_crs is None:
        target_crs = get_city_crs(city_name)
        
    logger.info(f"Aligning {len(input_rasters)} rasters to CRS {target_crs} at {target_resolution}m resolution")
    
    # Read the first raster to establish the target template
    # We will compute the union of all bounds
    all_bounds = []
    templates = []
    
    for i, r_path in enumerate(input_rasters):
        if not r_path.exists():
            raise FileNotFoundError(f"Input raster not found: {r_path}")
        with rasterio.open(r_path) as src:
            # Get bounds in source CRS
            bounds = src.bounds
            # Transform bounds to target CRS
            from rasterio.warp import transform_bounds
            target_bounds = transform_bounds(
                src.crs, target_crs,
                bounds.left, bounds.bottom, bounds.right, bounds.top
            )
            all_bounds.append(target_bounds)
            templates.append({
                "path": r_path,
                "src": src,
                "bounds": target_bounds
            })
            
    # Compute union of all bounds
    minx = min(b[0] for b in all_bounds)
    miny = min(b[1] for b in all_bounds)
    maxx = max(b[2] for b in all_bounds)
    maxy = max(b[3] for b in all_bounds)
    
    # Calculate output dimensions
    width = int(np.ceil((maxx - minx) / target_resolution))
    height = int(np.ceil((maxy - miny) / target_resolution))
    
    logger.info(f"Target extent: ({minx:.2f}, {miny:.2f}, {maxx:.2f}, {maxy:.2f})")
    logger.info(f"Target dimensions: {width}x{height}")
    
    output_paths = []
    
    for i, template in enumerate(templates):
        src = template["src"]
        r_path = template["path"]
        
        # Determine output filename
        stem = r_path.stem
        output_path = output_dir / f"{stem}_aligned.tif"
        
        # Create the output profile
        profile = src.profile.copy()
        profile.update({
            "crs": target_crs,
            "transform": rasterio.transform.from_bounds(minx, miny, maxx, maxy, width, height),
            "width": width,
            "height": height,
            "driver": "GTiff",
            "nodata": src.nodata if src.nodata is not None else -9999
        })
        
        # If the source is multi-band, we might want to keep that, 
        # but for this analysis we usually want single-band covariates/temps.
        # We'll keep the band count as is, but reproject.
        
        logger.info(f"Reprojecting {r_path} to aligned stack...")
        
        with rasterio.open(output_path, "w", **profile) as dst:
            for band_idx in range(src.count):
                reproject(
                    source=rasterio.band(src, band_idx + 1),
                    destination=rasterio.band(dst, band_idx + 1),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=dst.transform,
                    dst_crs=dst.crs,
                    resampling=Resampling.bilinear if src.dtypes[band_idx] in ['float32', 'float64'] else Resampling.nearest,
                    src_nodata=src.nodata,
                    dst_nodata=dst.nodata
                )
        
        output_paths.append(output_path)
        logger.info(f"Written: {output_path}")
        
    return output_paths

def main():
    """
    Main entry point for T015.
    
    Reads raw rasters from data/raw/, aligns them to a common grid,
    writes to data/processed/, and generates data/metadata.json.
    """
    logger.info("Starting T015: Create aligned GeoTIFF stack output")
    
    # Define paths
    raw_dir = get_path("data_raw")
    processed_dir = get_path("data_processed")
    metadata_path = get_path("data_metadata")
    
    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all GeoTIFFs in raw directory
    input_rasters = list(raw_dir.glob("*.tif")) + list(raw_dir.glob("*.tiff"))
    
    if not input_rasters:
        logger.error(f"No GeoTIFF files found in {raw_dir}. "
                     "Please run T012 (OSM ingestion) and T013 (Satellite ingestion) first.")
        return 1
        
    logger.info(f"Found {len(input_rasters)} input rasters: {[p.name for p in input_rasters]}")
    
    # Get city info
    # We assume the first raster or config tells us the city. 
    # For simplicity, we use the first city defined in config or a default.
    # In a real scenario, we might parse the filename or have a specific city config.
    city_name = "new_york" # Default, could be made configurable
    try:
        # Try to get city from config if available, otherwise default
        # This is a simplification; in practice, we'd pass city as an argument
        city_name = "new_york" 
    except Exception:
        pass
        
    target_crs = get_city_crs(city_name)
    target_resolution = 30.0 # 30m resolution as per spec
    
    # Create aligned stack
    try:
        output_paths = create_aligned_raster_stack(
            input_rasters=input_rasters,
            output_dir=processed_dir,
            target_crs=target_crs,
            target_resolution=target_resolution,
            city_name=city_name
        )
    except Exception as e:
        logger.error(f"Failed to create aligned stack: {e}")
        raise
        
    # Calculate bounds for metadata
    # We read the first output to get the bounds
    if output_paths:
        with rasterio.open(output_paths[0]) as src:
            bounds = src.bounds
            bounds_dict = {
                "minx": float(bounds.left),
                "miny": float(bounds.bottom),
                "maxx": float(bounds.right),
                "maxy": float(bounds.top)
            }
    else:
        bounds_dict = {}
        
    # Generate metadata
    metadata = generate_metadata(
        input_files=input_rasters,
        output_files=output_paths,
        city=city_name,
        crs=target_crs,
        resolution=target_resolution,
        bounds=bounds_dict,
        description=f"Aligned OSM and Satellite Raster Stack for {city_name.title()}"
    )
    
    # Write metadata
    write_metadata_json(metadata, metadata_path)
    
    logger.info("T015 completed successfully.")
    return 0

if __name__ == "__main__":
    exit(main())
