"""
Memory safety utilities for large spatial datasets.

This module provides functions to estimate memory usage of arrays, rasters,
and GeoDataFrames, and to enforce safety checks that prevent out-of-memory
failures during processing.
"""
import numpy as np
import geopandas as gpd
from shapely.geometry import box
from typing import List, Tuple, Optional, Union, Dict
import math
import logging
from config import MAX_BLOCKS, get_city_crs, get_path

# Configure logger
logger = logging.getLogger(__name__)

# Default safety threshold: 5 GB (5 * 1024 MB)
DEFAULT_MAX_MEMORY_MB = 5 * 1024

def estimate_array_memory_mb(arr: np.ndarray) -> float:
    """
    Estimate memory usage of a numpy array in MB.
    
    Args:
        arr: Numpy array to estimate
        
    Returns:
        Memory usage in MB
    """
    return arr.nbytes / (1024 * 1024)

def estimate_raster_memory_mb(width: int, height: int, bands: int, dtype: np.dtype) -> float:
    """
    Estimate memory usage of a raster in MB.
    
    Args:
        width: Raster width in pixels
        height: Raster height in pixels
        bands: Number of bands
        dtype: Data type
        
    Returns:
        Memory in MB
    """
    bytes_per_pixel = np.dtype(dtype).itemsize
    total_bytes = width * height * bands * bytes_per_pixel
    return total_bytes / (1024 * 1024)

def estimate_geodataframe_memory_mb(gdf: gpd.GeoDataFrame) -> float:
    """
    Estimate memory usage of a GeoDataFrame in MB.
    
    Args:
        gdf: GeoDataFrame to estimate
        
    Returns:
        Memory in MB
    """
    return gdf.memory_usage(deep=True).sum() / (1024 * 1024)

def check_memory_safety(
    estimated_mb: float,
    max_memory_mb: Optional[float] = None,
    context: str = "Data processing"
) -> None:
    """
    Check if estimated memory usage is within safe limits.
    
    If the estimated memory exceeds the limit, raises a MemoryError with
    a descriptive message to fail loudly as per spec requirements.
    
    Args:
        estimated_mb: Estimated memory usage in MB
        max_memory_mb: Maximum allowed memory in MB (defaults to DEFAULT_MAX_MEMORY_MB)
        context: Context description for the error message
        
    Raises:
        MemoryError: If estimated memory exceeds the limit
    """
    if max_memory_mb is None:
        max_memory_mb = DEFAULT_MAX_MEMORY_MB
        
    if estimated_mb > max_memory_mb:
        error_msg = (
            f"{context} requires {estimated_mb:.2f} MB of memory, "
            f"which exceeds the safety limit of {max_memory_mb:.2f} MB. "
            f"The dataset is too large for available RAM. "
            f"Please reduce the spatial extent or use a machine with more memory."
        )
        logger.error(error_msg)
        raise MemoryError(error_msg)
        
    logger.debug(f"{context} memory check passed: {estimated_mb:.2f} MB <= {max_memory_mb:.2f} MB")

def generate_spatial_blocks(
    bounds: Tuple[float, float, float, float],
    block_size_m: float = 1000.0,
    crs: Optional[str] = None
) -> gpd.GeoDataFrame:
    """
    Generate a grid of spatial blocks covering the given bounds.
    
    Args:
        bounds: (minx, miny, maxx, maxy) in projected coordinates (meters)
        block_size_m: Size of each block in meters
        crs: CRS for the blocks
        
    Returns:
        GeoDataFrame of blocks
    """
    minx, miny, maxx, maxy = bounds
    
    # Calculate grid dimensions
    width = maxx - minx
    height = maxy - miny
    
    n_cols = int(math.ceil(width / block_size_m))
    n_rows = int(math.ceil(height / block_size_m))
    
    blocks = []
    block_id = 0
    
    for i in range(n_cols):
        for j in range(n_rows):
            x0 = minx + i * block_size_m
            y0 = miny + j * block_size_m
            x1 = minx + (i + 1) * block_size_m
            y1 = miny + (j + 1) * block_size_m
            
            geom = box(x0, y0, x1, y1)
            blocks.append({
                'block_id': block_id,
                'geometry': geom
            })
            block_id += 1
    
    gdf = gpd.GeoDataFrame(blocks, crs=crs or get_city_crs())
    return gdf

def sample_blocks_by_intersection(
    gdf: gpd.GeoDataFrame,
    blocks: gpd.GeoDataFrame,
    max_blocks: Optional[int] = None
) -> List[int]:
    """
    Sample a subset of blocks that intersect with the data.
    
    Args:
        gdf: Data GeoDataFrame
        blocks: Grid of blocks
        max_blocks: Maximum number of blocks to return
        
    Returns:
        List of block IDs
    """
    # Join data with blocks
    joined = gpd.sjoin(gdf, blocks, how='inner', predicate='intersects')
    
    if joined.empty:
        return []
    
    unique_blocks = joined['block_id'].unique()
    
    if max_blocks and len(unique_blocks) > max_blocks:
        # Random sample
        import random
        random.seed(42) # Reproducibility
        return random.sample(list(unique_blocks), max_blocks)
    
    return list(unique_blocks)

def get_sampling_plan(
    data_gdf: gpd.GeoDataFrame,
    bounds: Tuple[float, float, float, float],
    block_size_m: float = 1000.0,
    max_blocks: Optional[int] = None
) -> List[int]:
    """
    Generate a sampling plan for spatial blocks.
    
    Args:
        data_gdf: Data GeoDataFrame
        bounds: City bounds
        block_size_m: Block size in meters
        max_blocks: Maximum blocks to sample
        
    Returns:
        List of block IDs to process
    """
    blocks = generate_spatial_blocks(bounds, block_size_m)
    return sample_blocks_by_intersection(data_gdf, blocks, max_blocks)

def validate_raster_dimensions_for_memory(
    width: int,
    height: int,
    bands: int,
    dtype: np.dtype,
    max_memory_mb: Optional[float] = None
) -> None:
    """
    Validate that a raster will fit in memory before loading.
    
    This is a safety check that should be called before attempting to load
    large rasters. If the raster exceeds memory limits, it raises a MemoryError.
    
    Args:
        width: Raster width in pixels
        height: Raster height in pixels
        bands: Number of bands
        dtype: Data type
        max_memory_mb: Maximum allowed memory in MB
        
    Raises:
        MemoryError: If raster exceeds memory limits
    """
    estimated_mb = estimate_raster_memory_mb(width, height, bands, dtype)
    check_memory_safety(estimated_mb, max_memory_mb, "Raster loading")

def validate_geodataframe_for_memory(
    gdf: gpd.GeoDataFrame,
    max_memory_mb: Optional[float] = None
) -> None:
    """
    Validate that a GeoDataFrame will fit in memory.
    
    Args:
        gdf: GeoDataFrame to validate
        max_memory_mb: Maximum allowed memory in MB
        
    Raises:
        MemoryError: If GeoDataFrame exceeds memory limits
    """
    estimated_mb = estimate_geodataframe_memory_mb(gdf)
    check_memory_safety(estimated_mb, max_memory_mb, "GeoDataFrame processing")
