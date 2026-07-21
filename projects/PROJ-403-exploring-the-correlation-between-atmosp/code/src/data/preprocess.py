"""
Data preprocessing utilities for Atmospheric River and Geopotential Height analysis.

This module handles loading, slicing, climatology computation, and anomaly calculation
for the regional domain (20°N-60°N, 100°E-60°W).
"""

import os
import numpy as np
import xarray as xr
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Regional domain constraints (FR-009)
REGIONAL_DOMAIN = {
    'lat_min': 20.0,
    'lat_max': 60.0,
    'lon_min': 100.0,  # 100°E
    'lon_max': 300.0   # 60°W (converted to 0-360 for xarray usually, or -180 to 180)
    # Note: CDS often returns -180 to 180. 60°W = -60.
    # If data is 0-360, 60°W = 300.
    # We will handle standard -180 to 180 convention in slicing.
}

# Adjusted for standard -180 to 180 convention often used in xarray after loading
# 100°E = 100, 60°W = -60
REGIONAL_DOMAIN_STD = {
    'lat_min': 20.0,
    'lat_max': 60.0,
    'lon_min': 100.0,
    'lon_max': -60.0
}

def load_chunked_netcdf(file_path: str, chunks: Optional[Dict[str, int]] = None) -> xr.Dataset:
    """
    Load a NetCDF file using Dask for chunked processing.

    Args:
        file_path: Path to the NetCDF file.
        chunks: Dictionary specifying chunk sizes (e.g., {'time': 10, 'lat': 50}).
                If None, Dask will choose optimal chunks or load fully if small.

    Returns:
        xarray.Dataset loaded with Dask backend.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"NetCDF file not found: {file_path}")

    logger.info(f"Loading {file_path} with chunks={chunks}")
    if chunks is None:
        # Default chunking for time to avoid loading all at once if large
        chunks = {'time': 30} 

    ds = xr.open_dataset(file_path, chunks=chunks)
    logger.info(f"Loaded dataset: {list(ds.data_vars)}")
    return ds

def slice_regional_domain(ds: xr.Dataset, domain: Optional[Dict[str, float]] = None) -> xr.Dataset:
    """
    Slice the dataset to the regional domain (20°N-60°N, 100°E-60°W).

    Handles both -180 to 180 and 0 to 360 longitude conventions.

    Args:
        ds: Input xarray.Dataset.
        domain: Optional dictionary with lat_min, lat_max, lon_min, lon_max.
                Defaults to REGIONAL_DOMAIN_STD.

    Returns:
        Sliced xarray.Dataset.
    """
    if domain is None:
        domain = REGIONAL_DOMAIN_STD

    logger.info(f"Slicing to domain: {domain}")

    # Handle longitude wrapping if necessary
    # If lon is 0-360, convert to -180-180 for consistent slicing logic
    if 'lon' in ds.coords:
        if ds.lon.max() > 180:
            logger.info("Detected 0-360 longitude, converting to -180 to 180")
            ds = ds.assign_coords(lon=((ds.lon + 180) % 360) - 180)
            ds = ds.sortby('lon')

    # Ensure coordinates are sorted for sel
    if 'lat' in ds.coords:
        ds = ds.sortby('lat')
    if 'lon' in ds.coords:
        ds = ds.sortby('lon')

    # Slice
    try:
        ds_sliced = ds.sel(
            lat=slice(domain['lat_min'], domain['lat_max']),
            lon=slice(domain['lon_min'], domain['lon_max'])
        )
    except Exception as e:
        logger.error(f"Failed to slice dataset: {e}")
        # Fallback: try swapping min/max if order is reversed
        ds_sliced = ds.sel(
            lat=slice(min(domain['lat_min'], domain['lat_max']), max(domain['lat_min'], domain['lat_max'])),
            lon=slice(min(domain['lon_min'], domain['lon_max']), max(domain['lon_min'], domain['lon_max']))
        )

    logger.info(f"Sliced dataset shape: {ds_sliced.sizes}")
    return ds_sliced

def compute_monthly_climatology(ds: xr.Dataset, var_name: str, dim: str = 'time') -> xr.DataArray:
    """
    Compute the monthly climatology for a specific variable.
    This calculates the mean for each month (Jan, Feb, ..., Dec) across all years.

    Args:
        ds: Input xarray.Dataset.
        var_name: Name of the variable in the dataset.
        dim: Name of the time dimension.

    Returns:
        xarray.DataArray of shape (12, lat, lon) representing monthly means.
    """
    if var_name not in ds.data_vars:
        raise ValueError(f"Variable '{var_name}' not found in dataset. Available: {list(ds.data_vars)}")

    logger.info(f"Computing monthly climatology for {var_name}")

    data = ds[var_name]
    
    # Ensure time is a DatetimeIndex
    if not isinstance(data.time.dt, xr.coding.times.CFDatetimeCoder):
        # Access time coordinates
        time_coords = data.time
        # Extract month
        month = time_coords.dt.month
        # Group by month
        climatology = data.groupby(f"{dim}.month").mean(dim=dim)
    
    # Rename 'month' coordinate to 1-12 for clarity if needed, 
    # but groupby('time.month') usually results in a 'month' coordinate 1..12
    
    logger.info(f"Climatology computed. Shape: {climatology.shape}")
    return climatology

def compute_anomalies(ds: xr.Dataset, climatology: xr.DataArray, var_name: str) -> xr.DataArray:
    """
    Calculate anomalies by subtracting the monthly climatology from the raw data.
    **IMPORTANT: No linear detrending is applied.** (Per Spec FR-003)

    Args:
        ds: Input xarray.Dataset with raw data.
        climatology: Pre-computed monthly climatology (12, lat, lon).
        var_name: Name of the variable to compute anomalies for.

    Returns:
        xarray.DataArray of anomalies.
    """
    if var_name not in ds.data_vars:
        raise ValueError(f"Variable '{var_name}' not found in dataset.")

    logger.info(f"Calculating anomalies for {var_name} (Climatology subtraction only)")

    raw_data = ds[var_name]
    
    # Align dimensions if necessary (climatology usually has 'month' coord)
    # xarray groupby subtraction usually handles alignment automatically if time is datetime
    # We subtract the climatology based on the month of the time coordinate.
    
    # Method: Use the month of the time coordinate to select the correct climatology value
    # and subtract.
    
    # If climatology was created via groupby('time.month'), it has a 'month' coordinate.
    # We can map the time coordinate to the month coordinate.
    
    # Efficient approach:
    # 1. Extract month from time
    # 2. Use that to index the climatology
    # 3. Subtract
    
    time_coords = raw_data.time
    month_indices = time_coords.dt.month.values - 1  # 0-indexed for numpy selection if needed, but xarray handles labels
    
    # If climatology has 'month' coordinate (1-12), we can use groupby logic again or direct alignment
    # The most robust way in xarray:
    # anomalies = raw_data.groupby('time.month') - climatology
    # But 'climatology' must be indexed by 'month'.
    
    # Let's assume climatology has a 'month' coordinate from compute_monthly_climatology
    # If not, we might need to add it.
    if 'month' not in climatology.coords:
         # Create a DataArray for climatology with 'month' coord if missing
         # This should not happen if compute_monthly_climatology returns groupby result
         pass

    # Perform subtraction
    # raw_data.groupby('time.month') returns a DataArrayGroupBy object
    # We subtract the climatology which is indexed by 'month'
    anomalies = raw_data.groupby('time.month') - climatology

    logger.info(f"Anomalies computed. Shape: {anomalies.shape}")
    return anomalies

def detect_ar_events(data: xr.DataArray, threshold: float, min_duration: int = 24) -> xr.DataArray:
    """
    Detect AR events based on IVT threshold and duration.
    (Placeholder for T018 implementation details, included for API completeness)
    """
    # Implementation deferred to T018
    raise NotImplementedError("AR detection logic to be implemented in T018")

def aggregate_monthly_frequency(ar_events: xr.DataArray) -> xr.DataArray:
    """
    Aggregate AR events into monthly frequency counts.
    (Placeholder for T018 implementation details)
    """
    raise NotImplementedError("AR frequency aggregation to be implemented in T018")

def save_processed_dataset(ds: xr.Dataset, output_path: str) -> None:
    """
    Save the processed dataset to a NetCDF file.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(output_path)
    logger.info(f"Saved processed dataset to {output_path}")