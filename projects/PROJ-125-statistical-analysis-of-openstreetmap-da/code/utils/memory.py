"""
Memory safety utilities for the OSM Urban Heat Island analysis pipeline.

Provides functions for:
- Estimating memory footprint of numpy arrays and GeoDataFrames.
- Generating spatial blocks for sampling.
- Sampling spatial blocks deterministically.
- Checking memory constraints against a global limit.
"""

import math
import random
from typing import List, Optional, Tuple, Union, Dict, Any
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box

# Import config for default MAX_BLOCKS if needed, though we accept it as arg
# from ..config import MAX_BLOCKS  # Avoid circular import if possible, pass as arg

def estimate_array_memory_gb(arr: np.ndarray) -> float:
    """
    Estimate the memory usage of a numpy array in Gigabytes.

    Args:
        arr: The numpy array to estimate.

    Returns:
        float: Estimated memory in GB.
    """
    if arr is None:
        return 0.0
    # nbytes gives size in bytes
    size_bytes = arr.nbytes
    return size_bytes / (1024 ** 3)


def estimate_geodataframe_memory_gb(gdf: gpd.GeoDataFrame) -> float:
    """
    Estimate the memory usage of a GeoDataFrame in Gigabytes.

    This includes the geometry column and all attribute columns.

    Args:
        gdf: The GeoDataFrame to estimate.

    Returns:
        float: Estimated memory in GB.
    """
    if gdf is None:
        return 0.0
    # memory_usage(deep=True) returns memory in bytes for each column
    total_bytes = gdf.memory_usage(deep=True).sum()
    return total_bytes / (1024 ** 3)


def generate_spatial_blocks(
    gdf: gpd.GeoDataFrame,
    block_size_meters: float = 1000.0,
    crs: Optional[str] = None
) -> List[gpd.GeoDataFrame]:
    """
    Generate a list of spatial blocks (GeoDataFrames) covering the extent of the input.

    The function projects the input to a local metric CRS if one is not provided
    or if the input CRS is lat/lon, to ensure block_size_meters is accurate.
    It then creates a grid of boxes and clips them to the input geometry.

    Args:
        gdf: Input GeoDataFrame defining the area of interest.
        block_size_meters: Size of the square blocks in meters.
        crs: Target CRS (EPSG string or dict) for metric calculations.
             If None, attempts to infer a local UTM or use EPSG:3857.

    Returns:
        List[gpd.GeoDataFrame]: List of GeoDataFrames, each representing a valid block
                                 intersecting the input geometry.
    """
    if gdf.empty:
        return []

    # Determine target CRS
    if crs is None:
        # If input is lat/lon (e.g., EPSG:4326), project to a local UTM zone
        # For simplicity, we'll use a generic projection logic or default to 3857
        # if the geometry is small enough, but ideally we calculate UTM zone.
        # Here we assume the caller handles CRS or we default to a safe metric one.
        # A robust implementation would calculate UTM zone based on centroid.
        centroid = gdf.geometry.unary_union.centroid
        if abs(centroid.y) < 80: # Avoid polar regions for simple UTM
            zone = int((centroid.x + 180) / 6) + 1
            hemisphere = "N" if centroid.y >= 0 else "S"
            crs = f"EPSG:{32600 + zone if hemisphere == 'N' else 32700 + zone}"
        else:
            crs = "EPSG:3857" # Fallback

    # Project to metric CRS
    if gdf.crs is None or gdf.crs != crs:
        gdf_metric = gdf.to_crs(crs)
    else:
        gdf_metric = gdf

    # Calculate bounds
    minx, miny, maxx, maxy = gdf_metric.total_bounds

    # Calculate grid dimensions
    cols = int(math.ceil((maxx - minx) / block_size_meters))
    rows = int(math.ceil((maxy - miny) / block_size_meters))

    blocks = []
    block_id = 0

    # Generate grid
    for i in range(cols):
        for j in range(rows):
            x0 = minx + i * block_size_meters
            y0 = miny + j * block_size_meters
            x1 = x0 + block_size_meters
            y1 = y0 + block_size_meters

            # Create box
            grid_box = box(x0, y0, x1, y1)

            # Clip to input geometry (unary union of all input geometries)
            # Optimization: Use a spatial index if gdf is huge, but for now unary_union
            # is acceptable for typical city-scale OSM data.
            union_geom = gdf_metric.geometry.unary_union
            intersection = grid_box.intersection(union_geom)

            if not intersection.is_empty:
                # Create a GeoDataFrame for this block
                # We store the intersection geometry and a unique ID
                block_gdf = gpd.GeoDataFrame(
                    {'block_id': [block_id], 'geometry': [intersection]},
                    crs=crs
                )
                blocks.append(block_gdf)
                block_id += 1

    # Return to original CRS if needed? Usually we keep them in the metric CRS for analysis
    # or convert back to original. Let's return in the metric CRS used for generation.
    return blocks


def sample_spatial_blocks(
    blocks: List[gpd.GeoDataFrame],
    max_blocks: int,
    seed: Optional[int] = None
) -> List[gpd.GeoDataFrame]:
    """
    Sample a subset of spatial blocks deterministically.

    Args:
        blocks: List of all generated spatial blocks.
        max_blocks: Maximum number of blocks to return.
        seed: Random seed for reproducibility. If None, no sampling (returns all).

    Returns:
        List[gpd.GeoDataFrame]: A subset of the input blocks.
    """
    if not blocks:
        return []

    if seed is not None:
        random.seed(seed)

    n_blocks = len(blocks)

    if n_blocks <= max_blocks:
        return blocks

    # Shuffle indices deterministically
    indices = list(range(n_blocks))
    random.shuffle(indices)

    selected_indices = indices[:max_blocks]

    return [blocks[i] for i in selected_indices]


def check_memory_constraint(
    estimated_gb: float,
    limit_gb: float = 6.0,
    safety_margin: float = 0.8
) -> Tuple[bool, str]:
    """
    Check if an estimated memory usage fits within the constraint.

    Args:
        estimated_gb: Estimated memory usage in GB.
        limit_gb: Hard memory limit in GB (default 6.0).
        safety_margin: Fraction of limit to target (e.g., 0.8 means target 80% of limit).

    Returns:
        Tuple[bool, str]: (is_safe, message)
    """
    target = limit_gb * safety_margin
    if estimated_gb <= target:
        return True, f"Memory OK: {estimated_gb:.2f}GB <= {target:.2f}GB (target)"
    else:
        return False, f"Memory EXCEEDED: {estimated_gb:.2f}GB > {target:.2f}GB (target). Limit: {limit_gb}GB"


def estimate_matrix_size(
    n_samples: int,
    n_features: int,
    dtype: np.dtype = np.float64
) -> float:
    """
    Estimate the memory size of a dense matrix in GB.

    Args:
        n_samples: Number of rows.
        n_features: Number of columns.
        dtype: Data type of the matrix elements.

    Returns:
        float: Estimated memory in GB.
    """
    item_size = np.dtype(dtype).itemsize
    total_bytes = n_samples * n_features * item_size
    return total_bytes / (1024 ** 3)