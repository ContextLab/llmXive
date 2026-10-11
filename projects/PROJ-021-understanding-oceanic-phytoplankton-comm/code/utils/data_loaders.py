import os
import gc
import logging
from typing import Generator, Optional, Dict, Any, Union, List, Tuple
from pathlib import Path
import numpy as np
import xarray as xr
import pandas as pd
import psutil

from utils.logging_config import get_logger
from utils.config import get_config

logger = get_logger(__name__)

def get_available_ram_gb() -> float:
    """Get available RAM in GB using psutil."""
    try:
        vm = psutil.virtual_memory()
        available_gb = vm.available / (1024 ** 3)
        logger.debug(f"Available RAM: {available_gb:.2f} GB")
        return available_gb
    except Exception as e:
        logger.warning(f"Could not determine available RAM: {e}. Defaulting to 7.0 GB")
        return 7.0

def stream_netcdf_by_chunk(path: str, chunk_size: int = 1000) -> Generator[xr.Dataset, None, None]:
    """
    Stream a NetCDF file by chunks to save memory.
    
    Yields xarray Datasets of size approximately chunk_size rows.
    This allows processing large files without loading them entirely into memory.
    
    Args:
        path: Path to the NetCDF file.
        chunk_size: Number of rows per chunk (default: 1000).
    
    Yields:
        xr.Dataset: Chunks of the NetCDF file.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        RuntimeError: If the file cannot be opened or read.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"NetCDF file not found: {path}")
    
    try:
        logger.info(f"Streaming NetCDF {path} in chunks of {chunk_size}")
        
        # Open dataset with chunks parameter to enable chunked reading
        ds = xr.open_dataset(path, chunks={'time': chunk_size})
        
        # Get the time dimension size
        if 'time' in ds.dims:
            time_size = ds.dims['time']
            
            # Iterate through chunks
            for start_idx in range(0, time_size, chunk_size):
                end_idx = min(start_idx + chunk_size, time_size)
                chunk = ds.isel(time=slice(start_idx, end_idx))
                yield chunk
                gc.collect()  # Force garbage collection between chunks
        else:
            # If no time dimension, yield the whole dataset as one chunk
            logger.warning("No 'time' dimension found. Yielding entire dataset as single chunk.")
            yield ds
            
    except Exception as e:
        logger.error(f"Error streaming NetCDF file {path}: {e}")
        raise RuntimeError(f"Failed to stream NetCDF file: {e}")

def sample_to_ram_limit(ds: xr.Dataset, limit_gb: float) -> xr.Dataset:
    """
    Sample a dataset to fit within RAM limit.
    
    Estimates the memory footprint of the dataset and samples rows if necessary
    to ensure it fits within the specified RAM limit.
    
    Args:
        ds: xarray Dataset to sample.
        limit_gb: RAM limit in GB.
    
    Returns:
        xr.Dataset: Sampled dataset that fits within the limit.
    
    Raises:
        ValueError: If even a single row exceeds the limit (data cannot be processed).
    """
    logger.info(f"Sampling dataset to fit within {limit_gb} GB RAM limit")
    
    # Estimate memory footprint
    # Each float64 variable is 8 bytes per value
    estimated_bytes = 0
    num_rows = 1
    
    # Get approximate dimensions
    for var in ds.data_vars:
        var_size = ds[var].nbytes
        estimated_bytes += var_size
    
    # Get number of time steps or primary dimension
    if 'time' in ds.dims:
        num_rows = ds.dims['time']
    elif len(ds.dims) > 0:
        num_rows = list(ds.dims.values())[0]
    
    estimated_gb = estimated_bytes / (1024 ** 3)
    logger.debug(f"Estimated dataset size: {estimated_gb:.2f} GB ({num_rows} rows)")
    
    if estimated_gb <= limit_gb:
        logger.info(f"Dataset fits within limit ({estimated_gb:.2f} GB <= {limit_gb} GB)")
        return ds
    
    # Calculate sampling ratio needed
    sampling_ratio = limit_gb / estimated_gb
    
    if sampling_ratio < 0.01:
        raise ValueError(
            f"Dataset is too large to fit in RAM even with aggressive sampling. "
            f"Required: {estimated_gb:.2f} GB, Available: {limit_gb} GB. "
            f"Sampling ratio would be {sampling_ratio:.4f}."
        )
    
    # Perform sampling
    if 'time' in ds.dims:
        sample_size = max(1, int(num_rows * sampling_ratio))
        logger.info(f"Sampling: {num_rows} -> {sample_size} rows ({sampling_ratio:.2%})")
        
        # Use deterministic sampling (first N rows for consistency)
        sampled = ds.isel(time=slice(0, sample_size))
    else:
        # For other dimensions, sample the first dimension
        first_dim = list(ds.dims.keys())[0]
        dim_size = ds.dims[first_dim]
        sample_size = max(1, int(dim_size * sampling_ratio))
        logger.info(f"Sampling: {dim_size} -> {sample_size} rows ({sampling_ratio:.2%})")
        sampled = ds.isel({first_dim: slice(0, sample_size)})
    
    return sampled

def load_and_sample_csv(path: str, ram_limit_gb: Optional[float] = None) -> pd.DataFrame:
    """
    Load a CSV and sample if too large to fit in RAM.
    
    Args:
        path: Path to the CSV file.
        ram_limit_gb: RAM limit in GB (uses config default if None).
    
    Returns:
        pd.DataFrame: Loaded (and possibly sampled) data.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        RuntimeError: If the file cannot be read or is too large even for minimal sampling.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV file not found: {path}")
    
    if ram_limit_gb is None:
        config = get_config()
        ram_limit_gb = config.get('memory_limit_gb', 7.0)
    
    logger.info(f"Loading CSV from {path} (RAM limit: {ram_limit_gb} GB)")
    
    try:
        # Read CSV with memory mapping to estimate size
        df = pd.read_csv(path)
        
        # Estimate memory footprint
        df_memory_gb = df.memory_usage(deep=True).sum() / (1024 ** 3)
        logger.debug(f"CSV memory footprint: {df_memory_gb:.2f} GB")
        
        if df_memory_gb <= ram_limit_gb:
            logger.info(f"CSV fits within limit ({df_memory_gb:.2f} GB <= {ram_limit_gb} GB)")
            return df
        
        # Sample if necessary
        sampling_ratio = ram_limit_gb / df_memory_gb
        
        if sampling_ratio < 0.01:
            raise RuntimeError(
                f"CSV is too large to fit in RAM even with aggressive sampling. "
                f"Required: {df_memory_gb:.2f} GB, Available: {ram_limit_gb} GB."
            )
        
        sample_size = max(1, int(len(df) * sampling_ratio))
        logger.info(f"Sampling CSV: {len(df)} -> {sample_size} rows ({sampling_ratio:.2%})")
        
        # Use deterministic sampling (first N rows)
        df_sampled = df.iloc[:sample_size].copy()
        
        return df_sampled
        
    except Exception as e:
        logger.error(f"Error loading CSV {path}: {e}")
        raise RuntimeError(f"Failed to load CSV: {e}")

def load_and_sample_nc(path: str, ram_limit_gb: Optional[float] = None) -> xr.Dataset:
    """
    Load a NetCDF and sample if too large to fit in RAM.
    
    Args:
        path: Path to the NetCDF file.
        ram_limit_gb: RAM limit in GB (uses config default if None).
    
    Returns:
        xr.Dataset: Loaded (and possibly sampled) data.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        RuntimeError: If the file cannot be read or is too large even for minimal sampling.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"NetCDF file not found: {path}")
    
    if ram_limit_gb is None:
        config = get_config()
        ram_limit_gb = config.get('memory_limit_gb', 7.0)
    
    logger.info(f"Loading NetCDF from {path} (RAM limit: {ram_limit_gb} GB)")
    
    try:
        # Open dataset
        ds = xr.open_dataset(path)
        
        # Estimate memory footprint
        ds_memory_gb = sum(var.nbytes for var in ds.data_vars.values()) / (1024 ** 3)
        logger.debug(f"NetCDF memory footprint: {ds_memory_gb:.2f} GB")
        
        if ds_memory_gb <= ram_limit_gb:
            logger.info(f"NetCDF fits within limit ({ds_memory_gb:.2f} GB <= {ram_limit_gb} GB)")
            return ds
        
        # Sample if necessary using sample_to_ram_limit
        ds_sampled = sample_to_ram_limit(ds, ram_limit_gb)
        return ds_sampled
        
    except Exception as e:
        logger.error(f"Error loading NetCDF {path}: {e}")
        raise RuntimeError(f"Failed to load NetCDF: {e}")

def main():
    """Entry point for data loaders module."""
    logger.info("Data loaders module initialized")
    logger.info(f"Available RAM: {get_available_ram_gb():.2f} GB")

if __name__ == "__main__":
    from utils.logging_config import setup_logging
    setup_logging()
    main()