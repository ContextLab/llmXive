"""
Base data processing utilities for loading chunked NetCDFs with Dask.

This module provides functions to load, slice, compute climatology,
calculate anomalies, detect Atmospheric River (AR) events, and save
processed datasets using xarray and Dask for memory-efficient operations.
"""
import os
import numpy as np
import xarray as xr
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Default regional domain constraints (mid-to-high northern latitudes)
DEFAULT_LAT_MIN = 20.0
DEFAULT_LAT_MAX = 60.0
DEFAULT_LON_MIN = 100.0  # 100°E
DEFAULT_LON_MAX = 300.0  # 60°W (converted to 0-360 or handled via wrap)

# AR Detection parameters (SWHAT-style defaults)
DEFAULT_AR_THRESHOLD = 250.0  # kg m^-1 s^-1
DEFAULT_MIN_DURATION = 1  # days (24h)
DEFAULT_MIN_AREA = 1  # grid cells

def load_chunked_netcdf(
    file_path: str | Path,
    chunks: Optional[Dict[str, int]] = None,
    engine: str = "netcdf4",
    decode_cf: bool = True
) -> xr.Dataset:
    """
    Load a NetCDF file into an xarray Dataset with Dask chunking for lazy evaluation.
    
    Args:
        file_path: Path to the NetCDF file.
        chunks: Dictionary specifying chunk sizes (e.g., {'time': 100, 'lat': 50}).
                If None, Dask will infer chunks or load into memory if small.
        engine: NetCDF engine to use ('netcdf4', 'h5netcdf', etc.).
        decode_cf: Whether to decode CF-compliant variables.
    
    Returns:
        xr.Dataset: Lazy-loaded dataset with Dask arrays.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be opened.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"NetCDF file not found: {file_path}")
    
    logger.info(f"Loading chunked NetCDF: {file_path} with engine={engine}")
    
    try:
        ds = xr.open_dataset(
            file_path,
            engine=engine,
            chunks=chunks,
            decode_cf=decode_cf,
            decode_times=True
        )
        logger.info(f"Successfully loaded dataset with variables: {list(ds.data_vars)}")
        return ds
    except Exception as e:
        logger.error(f"Failed to load NetCDF file {file_path}: {e}")
        raise

def slice_regional_domain(
    ds: xr.Dataset,
    lat_min: float = DEFAULT_LAT_MIN,
    lat_max: float = DEFAULT_LAT_MAX,
    lon_min: float = DEFAULT_LON_MIN,
    lon_max: float = DEFAULT_LON_MAX,
    lat_dim: str = "lat",
    lon_dim: str = "lon"
) -> xr.Dataset:
    """
    Slice the dataset to the specified regional domain.
    
    Handles longitude wrapping if the dataset uses 0-360 but inputs are -180-180,
    or vice versa.
    
    Args:
        ds: Input xarray Dataset.
        lat_min: Minimum latitude.
        lat_max: Maximum latitude.
        lon_min: Minimum longitude.
        lon_max: Maximum longitude.
        lat_dim: Name of latitude dimension.
        lon_dim: Name of longitude dimension.
    
    Returns:
        xr.Dataset: Sliced dataset.
    """
    logger.info(f"Slicing regional domain: Lat [{lat_min}, {lat_max}], Lon [{lon_min}, {lon_max}]")
    
    # Ensure coordinates are sorted for selection
    if lat_dim in ds.dims:
        ds = ds.sortby(lat_dim)
    if lon_dim in ds.dims:
        ds = ds.sortby(lon_dim)
    
    # Handle longitude wrapping if necessary
    lon_coords = ds[lon_dim].values
    if np.any(lon_coords < 0) and lon_min > 0:
        # Dataset is -180 to 180, but request is 100E to 60W (positive)
        # Convert dataset to 0-360
        ds = ds.assign_coords({lon_dim: (lon_coords + 360) % 360})
        ds = ds.sortby(lon_dim)
        # Adjust request if needed, but usually 100E-60W is 100-300 in 0-360
        if lon_max < lon_min: # e.g. 100 to 300
            pass 
        else:
            # Standard case: 100 to 300
            pass
    
    # Slice
    # Use sel with nearest or strict bounds. Strict bounds are safer for scientific analysis.
    sliced_ds = ds.sel(
        {lat_dim: slice(lat_min, lat_max)},
        {lon_dim: slice(lon_min, lon_max)},
        method=None # Exact match or nearest if needed, but strict is better for domains
    )
    
    # Fallback for wrap-around if region crosses dateline (not the case here, but good practice)
    # The request is 100E to 60W (100 to 300 degrees East). This is a continuous block in 0-360.
    
    if sliced_ds.sizes[lat_dim] == 0 or sliced_ds.sizes[lon_dim] == 0:
        logger.warning(f"Resulting slice is empty. Check coordinates. Original dims: {ds.sizes}")
    
    logger.info(f"Sliced dataset shape: {sliced_ds.sizes}")
    return sliced_ds

def compute_monthly_climatology(
    ds: xr.Dataset,
    var_name: str,
    time_dim: str = "time",
    lat_dim: str = "lat",
    lon_dim: str = "lon"
) -> xr.DataArray:
    """
    Compute monthly climatology (mean per month) for a specific variable.
    
    This groups by month-of-year and computes the mean across all years.
    
    Args:
        ds: Input dataset.
        var_name: Name of the variable to compute climatology for.
        time_dim: Name of the time dimension.
        lat_dim: Name of latitude dimension.
        lon_dim: Name of longitude dimension.
    
    Returns:
        xr.DataArray: Climatology array with dimensions (month, lat, lon).
    """
    if var_name not in ds.data_vars:
        raise ValueError(f"Variable '{var_name}' not found in dataset. Available: {list(ds.data_vars)}")
    
    logger.info(f"Computing monthly climatology for {var_name}")
    
    # Ensure time is a datetime index
    if not xr.core.common.contains_cftime_datetimes(ds[time_dim]):
        # Try to ensure it's parsed as datetime if not already
        pass 
    
    # Group by month
    climatology = ds[var_name].groupby(f"{time_dim}.month").mean(dim=time_dim)
    
    # Rename month dimension to 'month' for clarity if needed, but groupby usually handles it
    # climatology.coords['month'] = range(1, 13)
    
    logger.info(f"Climatology computed. Shape: {climatology.shape}")
    return climatology

def compute_anomalies(
    ds: xr.Dataset,
    var_name: str,
    climatology: xr.DataArray,
    time_dim: str = "time",
    lat_dim: str = "lat",
    lon_dim: str = "lon"
) -> xr.DataArray:
    """
    Compute anomalies by subtracting monthly climatology from raw data.
    
    IMPORTANT: This function does NOT apply linear detrending, per Spec FR-003.
    
    Args:
        ds: Input dataset.
        var_name: Name of the variable.
        climatology: Pre-computed monthly climatology.
        time_dim: Name of time dimension.
        lat_dim: Name of latitude dimension.
        lon_dim: Name of longitude dimension.
    
    Returns:
        xr.DataArray: Anomaly data.
    """
    if var_name not in ds.data_vars:
        raise ValueError(f"Variable '{var_name}' not found in dataset.")
    
    logger.info(f"Computing anomalies for {var_name} (climatology subtraction only)")
    
    # Align climatology with data time dimension
    # The climatology has 'month' dimension, data has 'time'
    # We need to map each time step to its corresponding month in climatology
    
    # Create a DataArray for the month of each time step
    time_coords = ds[time_dim]
    months = time_coords.dt.month
    
    # Select climatology based on month
    # This relies on xarray's alignment capabilities if dimensions match
    # climatology has dims (month, lat, lon)
    # We want to subtract climatology[month(t)] from data[t, lat, lon]
    
    # Method: Use groupby or direct indexing if we map months
    # Direct indexing is more efficient for this specific case
    
    # Ensure climatology has a 'month' coordinate
    if 'month' not in climatology.dims:
        # If groupby didn't create a 'month' coord, we might need to set it
        # xarray groupby usually creates a coordinate named 'month'
        pass
    
    # Subtract
    # We use isel or sel with the months array
    # climatology.sel(month=months) works if 'month' is a coordinate
    
    # To avoid alignment issues, we can reindex or use map_blocks, but simple sel works if coords align
    # Let's ensure the 'month' coordinate exists
    if 'month' not in climatology.coords:
        climatology = climatology.assign_coords(month=('month', range(1, 13)))
    
    # Align time steps to climatology months
    # This creates a new array where for each time t, we pick climatology[month(t)]
    anomaly = ds[var_name] - climatology.sel(month=months, method="nearest")
    
    logger.info(f"Anomalies computed. Shape: {anomaly.shape}")
    return anomaly

def detect_ar_events(
    ds: xr.Dataset,
    var_name: str = "integrated_water_vapor_transport",
    threshold: float = DEFAULT_AR_THRESHOLD,
    min_duration: int = DEFAULT_MIN_DURATION,
    time_dim: str = "time",
    lat_dim: str = "lat",
    lon_dim: str = "lon"
) -> xr.Dataset:
    """
    Detect Atmospheric River (AR) events using SWHAT-style logic.
    
    Logic:
    1. Apply threshold mask (IVT > threshold).
    2. Find contiguous regions (spatially and temporally).
    3. Filter by duration (>= min_duration days).
    4. Output binary mask and event metadata.
    
    Args:
        ds: Input dataset.
        var_name: Variable name for IVT.
        threshold: IVT threshold in kg m^-1 s^-1.
        min_duration: Minimum duration in days.
        time_dim: Time dimension name.
        lat_dim: Latitude dimension name.
        lon_dim: Longitude dimension name.
    
    Returns:
        xr.Dataset: Dataset with 'ar_mask' (binary) and 'ar_event_id'.
    """
    if var_name not in ds.data_vars:
        raise ValueError(f"Variable '{var_name}' not found in dataset.")
    
    logger.info(f"Detecting AR events with threshold={threshold}, min_duration={min_duration} days")
    
    ivt_data = ds[var_name].values
    mask = ivt_data > threshold
    
    # Convert to xarray for easier handling
    mask_da = xr.DataArray(
        mask,
        dims=ds[var_name].dims,
        coords=ds[var_name].coords
    )
    
    # Identify contiguous regions
    # We need to label connected components in 3D (time, lat, lon)
    # Since xarray doesn't have a direct connected_components, we use scipy or manual logic
    # For large datasets, scipy.ndimage.label is efficient
    
    from scipy.ndimage import label
    
    # Structure for connectivity: 3D connectivity (26 neighbors)
    # But typically ARs are defined as contiguous in space and time.
    # Let's use a structure that connects time steps if spatially connected.
    structure = np.ones((3, 3, 3), dtype=int) # 3D connectivity
    
    # Ensure time is the first dimension for label
    # mask_da is likely (time, lat, lon)
    labeled, num_features = label(mask_da.values, structure=structure)
    
    labeled_da = xr.DataArray(
        labeled,
        dims=mask_da.dims,
        coords=mask_da.coords
    )
    
    # Filter by duration
    # Count number of time steps per event ID
    # We need to map event_id -> count of time steps
    unique_ids = np.unique(labeled)
    unique_ids = unique_ids[unique_ids != 0] # Remove background
    
    valid_ids = []
    for event_id in unique_ids:
        # Count non-zero time steps for this event
        # Sum over lat/lon, count time steps where sum > 0
        event_mask = (labeled_da == event_id)
        # Count time steps with any spatial extent
        time_counts = event_mask.sum(dim=[lat_dim, lon_dim])
        if time_counts.max() >= min_duration:
            valid_ids.append(event_id)
    
    # Create final mask
    final_mask = np.isin(labeled, valid_ids)
    final_da = xr.DataArray(
        final_mask.astype(int),
        dims=mask_da.dims,
        coords=mask_da.coords,
        name="ar_mask"
    )
    
    # Create event ID mask (only valid events)
    final_event_id = xr.DataArray(
        np.where(final_mask, labeled, 0),
        dims=mask_da.dims,
        coords=mask_da.coords,
        name="ar_event_id"
    )
    
    result_ds = xr.Dataset({
        "ar_mask": final_da,
        "ar_event_id": final_event_id
    })
    
    logger.info(f"Detected {len(valid_ids)} AR events.")
    return result_ds

def aggregate_monthly_frequency(
    ds: xr.Dataset,
    event_id_var: str = "ar_event_id",
    time_dim: str = "time",
    lat_dim: str = "lat",
    lon_dim: str = "lon"
) -> xr.Dataset:
    """
    Aggregate AR events into monthly frequency counts.
    
    Args:
        ds: Dataset with 'ar_event_id' or 'ar_mask'.
        event_id_var: Name of the event ID variable.
        time_dim: Time dimension name.
        lat_dim: Latitude dimension name.
        lon_dim: Longitude dimension name.
    
    Returns:
        xr.Dataset: Monthly frequency counts per grid cell.
    """
    if event_id_var not in ds.data_vars:
        raise ValueError(f"Variable '{event_id_var}' not found in dataset.")
    
    logger.info("Aggregating monthly AR frequency")
    
    event_data = ds[event_id_var]
    
    # Group by year and month
    # We need to count unique events per month per grid cell?
    # Or just count days? The task says "monthly frequency counts".
    # Usually this means number of AR days or number of AR events.
    # Let's count number of days with AR presence (binary sum) per month.
    
    # Create a monthly groupby key
    months = event_data[time_dim].dt.to_period('M')
    
    # Sum the binary mask (if we had it) or count non-zero event IDs
    # Using the event_id, we can check if > 0
    binary = (event_data > 0).astype(int)
    
    monthly_freq = binary.groupby(months).sum(dim=time_dim)
    
    # Ensure dimensions are clean
    monthly_freq = monthly_freq.rename({"period": "time"})
    
    # Add metadata
    monthly_freq.attrs["long_name"] = "Monthly AR Frequency (days)"
    monthly_freq.attrs["units"] = "days/month"
    
    result_ds = xr.Dataset({
        "ar_frequency": monthly_freq
    })
    
    logger.info(f"Monthly frequency aggregated. Shape: {result_ds['ar_frequency'].shape}")
    return result_ds

def save_processed_dataset(
    ds: xr.Dataset,
    output_path: str | Path,
    compression: bool = True,
    encoding: Optional[Dict] = None
) -> None:
    """
    Save an xarray Dataset to NetCDF with optional compression.
    
    Args:
        ds: Dataset to save.
        output_path: Output file path.
        compression: Whether to enable compression.
        encoding: Custom encoding dictionary.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving processed dataset to {output_path}")
    
    if encoding is None:
        encoding = {}
        if compression:
            for var in ds.data_vars:
                encoding[var] = {
                    'zlib': True,
                    'complevel': 4,
                    'shuffle': True
                }
    
    ds.to_netcdf(
        output_path,
        encoding=encoding,
        engine="netcdf4"
    )
    
    logger.info(f"Successfully saved to {output_path}")
