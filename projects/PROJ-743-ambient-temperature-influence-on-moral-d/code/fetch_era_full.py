"""
Fetch the full 2014-2018 ERA5 2m temperature dataset required for primary analysis.
Implements chunking by 10x10 degree tiles, streaming to disk, and retry logic.
"""
import os
import sys
import logging
import time
import math
import json
import cdsapi
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Configuration
CDS_TIMEOUT = 3600  # seconds
CDS_RETRY_COUNT = 5
CDS_RETRY_BACKOFF = 2.0  # exponential backoff multiplier
TILE_SIZE_DEG = 10.0
OUTPUT_FILE = PROJECT_ROOT / "data" / "raw" / "era5_full.h5"
BBOX_FILE = PROJECT_ROOT / "data" / "external" / "bounding_box.json"
LOG_FILE = PROJECT_ROOT / "results" / "logs" / "data_validation_log.txt"

def ensure_directories() -> None:
    """Create necessary output directories."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    Path(PROJECT_ROOT / "results" / "logs").mkdir(parents=True, exist_ok=True)

def get_logger() -> logging.Logger:
    """Configure and return the project logger."""
    logger = logging.getLogger("fetch_era5_full")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = logging.FileHandler(LOG_FILE)
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        # Also log to console for immediate feedback
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

def append_log(message: str, logger: logging.Logger) -> None:
    """Append a message to the log file via the logger."""
    logger.info(message)

def get_cds_client() -> cdsapi.Client:
    """Initialize and return a CDS API client with robust settings."""
    return cdsapi.Client(
        quiet=False,
        info_callback=logging.getLogger("cdsapi").debug,
        debug=logging.getLogger("cdsapi").debug,
        timeout=CDS_TIMEOUT,
        retries=CDS_RETRY_COUNT
    )

def tile_overlaps_bbox(tile_min_lat: float, tile_max_lat: float,
                       tile_min_lon: float, tile_max_lon: float,
                       bbox: Dict[str, float]) -> bool:
    """Check if a 10x10 tile overlaps with the provided bounding box."""
    # Bounding box from T002
    min_lat, max_lat = bbox['min_lat'], bbox['max_lat']
    min_lon, max_lon = bbox['min_lon'], bbox['max_lon']

    # Check for non-overlap
    if tile_max_lat < min_lat or tile_min_lat > max_lat:
        return False
    if tile_max_lon < min_lon or tile_min_lon > max_lon:
        return False
    return True

def fetch_tile(client: cdsapi.Client, year: int, tile_min_lat: float, tile_max_lat: float,
               tile_min_lon: float, tile_max_lon: float, tile_id: str,
               logger: logging.Logger) -> Optional[str]:
    """
    Fetch a single 10x10 degree tile for a specific year.
    Returns the path to the downloaded NetCDF file or None if failed.
    Implements exponential backoff retry logic.
    """
    output_path = PROJECT_ROOT / "data" / "raw" / f"era5_{year}_{tile_id}.nc"
    
    request_args = {
        'product_type': 'reanalysis',
        'format': 'netcdf',
        'variable': '2m_temperature',
        'year': str(year),
        'month': [f'{i:02d}' for i in range(1, 13)],
        'day': [f'{i:02d}' for i in range(1, 32)],
        'time': [f'{i:02d}:00' for i in range(0, 24)],
        'area': [tile_max_lat, tile_min_lon, tile_min_lat, tile_max_lon], # Note: CDS uses [north, west, south, east]
        'grid': [0.25, 0.25]
    }

    # Retry logic
    for attempt in range(CDS_RETRY_COUNT):
        try:
            append_log(f"Fetching tile {tile_id} for year {year} (Attempt {attempt + 1})...", logger)
            client.retrieve(
                'reanalysis-era5-single-levels',
                request_args,
                str(output_path)
            )
            append_log(f"Successfully fetched tile {tile_id} for year {year}.", logger)
            return str(output_path)
        except Exception as e:
            append_log(f"Error fetching tile {tile_id} for year {year}: {e}", logger)
            if attempt < CDS_RETRY_COUNT - 1:
                wait_time = CDS_RETRY_BACKOFF * (2 ** attempt)
                append_log(f"Retrying in {wait_time} seconds...", logger)
                time.sleep(wait_time)
            else:
                append_log(f"Failed to fetch tile {tile_id} for year {year} after {CDS_RETRY_COUNT} attempts.", logger)
                return None

def merge_netcdf_to_hdf5(nc_files: List[str], output_h5_path: str, logger: logging.Logger) -> bool:
    """
    Merge multiple NetCDF files into a single HDF5 file.
    Uses xarray and h5py for efficient I/O.
    """
    try:
        import xarray as xr
        import h5py
    except ImportError:
        append_log("ERROR: xarray or h5py not installed. Please install them.", logger)
        return False

    append_log(f"Merging {len(nc_files)} NetCDF files into {output_h5_path}...", logger)
    
    try:
        # Open all datasets
        datasets = [xr.open_dataset(f) for f in nc_files]
        
        # Concatenate along the time dimension
        # Ensure all datasets have the same variables and dimensions structure
        # ERA5 data usually has 'time', 'latitude', 'longitude'
        merged_ds = xr.concat(datasets, dim='time', combine_attrs="drop_conflicts")
        
        # Sort by time if necessary
        merged_ds = merged_ds.sortby('time')
        
        # Save to HDF5
        # Using engine='h5netcdf' or 'netcdf4' is standard, but explicit h5py can be used for control
        # xarray supports to_netcdf with engine='netcdf4' which writes HDF5 format
        merged_ds.to_netcdf(output_h5_path, engine='netcdf4')
        
        append_log(f"Successfully merged data to {output_h5_path}.", logger)
        
        # Close datasets to free memory
        for ds in datasets:
            ds.close()
        
        return True
    except Exception as e:
        append_log(f"Error merging NetCDF files: {e}", logger)
        # Clean up partial output if failed
        if os.path.exists(output_h5_path):
            os.remove(output_h5_path)
        return False

def main() -> int:
    """Main entry point for fetching the full ERA5 dataset."""
    ensure_directories()
    logger = get_logger()
    append_log("Starting full ERA5 data fetch process.", logger)

    # 1. Read Bounding Box
    if not BBOX_FILE.exists():
        append_log(f"ERROR: Bounding box file not found at {BBOX_FILE}. Run T002 first.", logger)
        return 1

    with open(BBOX_FILE, 'r') as f:
        bbox = json.load(f)
    
    min_lat, max_lat = bbox['min_lat'], bbox['max_lat']
    min_lon, max_lon = bbox['min_lon'], bbox['max_lon']
    append_log(f"Loaded bounding box: [{min_lat}, {max_lat}] x [{min_lon}, {max_lon}]", logger)

    # 2. Initialize CDS Client
    try:
        client = get_cds_client()
    except Exception as e:
        append_log(f"ERROR: Failed to initialize CDS client: {e}", logger)
        return 1

    # 3. Generate Tile Grid
    # Determine global tile range needed to cover the bounding box
    # We iterate 10-degree chunks
    start_lat = math.floor(min_lat / TILE_SIZE_DEG) * TILE_SIZE_DEG
    end_lat = math.ceil(max_lat / TILE_SIZE_DEG) * TILE_SIZE_DEG
    start_lon = math.floor(min_lon / TILE_SIZE_DEG) * TILE_SIZE_DEG
    end_lon = math.ceil(max_lon / TILE_SIZE_DEG) * TILE_SIZE_DEG

    tiles_to_fetch = []
    for lat in frange(start_lat, end_lat, TILE_SIZE_DEG):
        for lon in frange(start_lon, end_lon, TILE_SIZE_DEG):
            tile_min_lat, tile_max_lat = lat, lat + TILE_SIZE_DEG
            tile_min_lon, tile_max_lon = lon, lon + TILE_SIZE_DEG
            
            if tile_overlaps_bbox(tile_min_lat, tile_max_lat, tile_min_lon, tile_max_lon, bbox):
                tiles_to_fetch.append({
                    'min_lat': tile_min_lat,
                    'max_lat': tile_max_lat,
                    'min_lon': tile_min_lon,
                    'max_lon': tile_max_lon,
                    'tile_id': f"{int(tile_min_lat)}_{int(tile_min_lon)}"
                })

    append_log(f"Identified {len(tiles_to_fetch)} tiles to fetch.", logger)

    # 4. Fetch Data for Years 2014-2018
    all_nc_files = []
    years = range(2014, 2019)
    
    for year in years:
        append_log(f"Processing year {year}...", logger)
        year_nc_files = []
        for tile in tiles_to_fetch:
            nc_path = fetch_tile(
                client, year,
                tile['min_lat'], tile['max_lat'],
                tile['min_lon'], tile['max_lon'],
                tile['tile_id'], logger
            )
            if nc_path and os.path.exists(nc_path):
                year_nc_files.append(nc_path)
        
        if year_nc_files:
            append_log(f"Collected {len(year_nc_files)} files for year {year}.", logger)
            all_nc_files.extend(year_nc_files)
        else:
            append_log(f"WARNING: No files fetched for year {year}.", logger)

    if not all_nc_files:
        append_log("ERROR: No data files were successfully fetched.", logger)
        return 1

    # 5. Merge to HDF5
    success = merge_netcdf_to_hdf5(all_nc_files, str(OUTPUT_FILE), logger)
    
    if success:
        append_log("Full ERA5 dataset fetch and merge completed successfully.", logger)
        return 0
    else:
        append_log("ERROR: Failed to merge ERA5 dataset.", logger)
        return 1

def frange(start: float, stop: float, step: float) -> List[float]:
    """Float range generator to avoid floating point accumulation errors."""
    current = start
    while current < stop:
        yield current
        current += step
        # Small epsilon to handle float precision issues
        if current > stop:
            break

if __name__ == "__main__":
    sys.exit(main())
