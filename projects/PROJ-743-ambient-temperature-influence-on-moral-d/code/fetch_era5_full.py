"""
Implementation of the full ERA5 dataset fetch (Task T002b logic, executed by T002c).

This module implements the logic to fetch the full 2014-2018 ERA5 2m temperature
dataset using the CDS API. It processes the data in 10x10 degree tiles to avoid
memory overflow and API timeouts, implements retry logic for rate limits, and
merges the results into a single HDF5 file.

Key Functions:
- fetch_tile: Downloads a single 10x10 degree tile for a specific year.
- merge_netcdf_to_hdf5: Combines downloaded NetCDF files into a single HDF5 store.
- main: Orchestrates the loop over years and tiles.
"""
import os
import sys
import logging
import time
import math
from datetime import datetime
from pathlib import Path
import cdsapi
import xarray as xr
import h5py
import tempfile
import shutil

# Import config for paths
from config import get_path_env_override

# Constants
OUTPUT_FILE = "data/raw/era5_full.h5"
LOG_FILE = "results/logs/data_validation_log.txt"
START_YEAR = 2014
END_YEAR = 2018
VARIABLE = "2t" # 2 metre temperature
PRODUCT = "reanalysis-era5-single-levels"
FORMAT = "netcdf"

# Geographic Bounding Box for Moral Machine Data (Approximate Global Coverage)
# Moral Machine data is global, so we iterate the full grid but filter by valid data later if needed.
# However, to optimize, we can restrict to land masses or known data regions if specified.
# For now, we implement the full 10x10 grid as requested, filtering tiles that have no data.
MIN_LAT = -89.0
MAX_LAT = 89.0
MIN_LON = -180.0
MAX_LON = 180.0
TILE_SIZE = 10.0

def ensure_directories():
    """Ensures output directories exist."""
    Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

def get_logger():
    """Configures and returns the data quality logger."""
    logger = logging.getLogger("data_quality")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        # File handler for the specific log file
        fh = logging.FileHandler(LOG_FILE, mode='a')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger

def append_log(message):
    """Appends a message to the validation log."""
    logger = get_logger()
    logger.info(message)

def get_cds_client():
    """Initializes and returns the CDS API client."""
    return cdsapi.Client()

def fetch_tile(client, year, lat_min, lat_max, lon_min, lon_max, output_path):
    """
    Fetches a single 10x10 degree tile for a specific year.

    Args:
        client: CDS API client instance.
        year: Target year (int).
        lat_min, lat_max: Latitude bounds.
        lon_min, lon_max: Longitude bounds.
        output_path: Path to save the NetCDF file.

    Returns:
        bool: True if successful, False otherwise.
    """
    logger = get_logger()
    # CDS API expects latitudes from North to South
    # CDS API expects longitudes from West to East
    request = {
        'product_type': PRODUCT,
        'format': FORMAT,
        'variable': VARIABLE,
        'year': str(year),
        'month': [f'{i:02d}' for i in range(1, 13)],
        'day': [f'{i:02d}' for i in range(1, 32)], # CDS handles invalid days automatically
        'time': [
            '00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00', '07:00',
            '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00',
            '16:00', '17:00', '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'
        ],
        'area': [lat_max, lon_min, lat_min, lon_max], # North, West, South, East
    }

    max_retries = 5
    retry_delay = 2
    attempt = 0

    while attempt < max_retries:
        try:
            logger.info(f"Fetching tile [{year}] Lat: {lat_min:.1f}-{lat_max:.1f}, Lon: {lon_min:.1f}-{lon_max:.1f}")
            client.retrieve(
                'reanalysis-era5-single-levels',
                request,
                output_path
            )
            return True
        except Exception as e:
            attempt += 1
            if attempt < max_retries:
                logger.warning(f"Retry {attempt}/{max_retries} for tile [{year}] Lat: {lat_min:.1f}-{lat_max:.1f} due to: {e}")
                time.sleep(retry_delay)
                retry_delay *= 2 # Exponential backoff
            else:
                logger.error(f"Failed to fetch tile [{year}] Lat: {lat_min:.1f}-{lat_max:.1f} after {max_retries} attempts: {e}")
                return False

def merge_netcdf_to_hdf5(netcdf_files, output_hdf5_path):
    """
    Merges a list of NetCDF files into a single HDF5 file.
    Uses xarray to open, combine, and save.

    Args:
        netcdf_files: List of paths to NetCDF files.
        output_hdf5_path: Path for the output HDF5 file.
    """
    logger = get_logger()
    if not netcdf_files:
        logger.warning("No NetCDF files to merge.")
        return

    logger.info(f"Merging {len(netcdf_files)} NetCDF files into {output_hdf5_path}")

    try:
        # Open all datasets
        datasets = [xr.open_dataset(f) for f in netcdf_files]
        
        # Combine along the time dimension (or whatever dimension xarray infers)
        # ERA5 data usually has 'time', 'latitude', 'longitude'
        combined = xr.combine_by_coords(datasets)
        
        # Save to HDF5
        combined.to_netcdf(output_hdf5_path, engine='netcdf4') # xarray saves as netcdf4/hdf5 by default
        
        # Close all open datasets to free memory
        for ds in datasets:
            ds.close()
        
        logger.info("Merge completed successfully.")
    except Exception as e:
        logger.error(f"Error merging NetCDF files: {e}", exc_info=True)
        raise

def tile_overlaps_bbox(lat_min, lat_max, lon_min, lon_max):
    """
    Checks if a tile overlaps with the Moral Machine data bounding box.
    Since Moral Machine is global, we assume all tiles are relevant unless
    specific filters are applied later. This function is a placeholder for
    future optimization if a specific region is required.
    """
    return True

def main():
    """
    Main execution function for T002c.
    Iterates over years and tiles, fetches data, and merges.
    """
    ensure_directories()
    logger = get_logger()
    append_log(f"Starting full ERA5 fetch for years {START_YEAR}-{END_YEAR}")

    client = get_cds_client()
    netcdf_files = []
    temp_dir = tempfile.mkdtemp(prefix="era5_fetch_")

    try:
        for year in range(START_YEAR, END_YEAR + 1):
            logger.info(f"Processing year: {year}")
            year_files = []
            
            # Iterate latitude from South to North (or North to South, CDS handles it)
            # We iterate from MIN_LAT to MAX_LAT in steps of TILE_SIZE
            lat = MIN_LAT
            while lat < MAX_LAT:
                lat_next = min(lat + TILE_SIZE, MAX_LAT)
                
                # Iterate longitude from West to East
                lon = MIN_LON
                while lon < MAX_LON:
                    lon_next = min(lon + TILE_SIZE, MAX_LON)
                    
                    # Filter tiles that do not overlap (if any filter logic is added)
                    if not tile_overlaps_bbox(lat, lat_next, lon, lon_next):
                        lon += TILE_SIZE
                        continue

                    # Create a unique filename for this tile and year
                    tile_filename = f"era5_{year}_lat{lat:.0f}_{lat_next:.0f}_lon{lon:.0f}_{lon_next:.0f}.nc"
                    tile_path = os.path.join(temp_dir, tile_filename)
                    
                    # Fetch the tile
                    success = fetch_tile(client, year, lat, lat_next, lon, lon_next, tile_path)
                    
                    if success and os.path.exists(tile_path):
                        year_files.append(tile_path)
                    
                    lon += TILE_SIZE
                lat += TILE_SIZE

            if year_files:
                logger.info(f"Found {len(year_files)} files for year {year}. Merging...")
                # We can merge year by year to save memory, or accumulate all.
                # To save memory, let's merge year by year into intermediate files if needed,
                # but for simplicity and given the constraint of one final file,
                # we will accumulate all netcdf files and merge at the end.
                # However, if the list gets too huge, we might need a chunked merge.
                # Given the 10x10 grid over 5 years: ~36 lat * 36 lon * 5 years = 6480 files.
                # This is manageable in a list, but merging 6000 files at once might be heavy.
                # Strategy: Merge year by year into intermediate HDF5, then merge those?
                # Or just collect and merge. Let's collect for now, but if memory is an issue,
                # we would need to change this to merge in batches.
                netcdf_files.extend(year_files)
            else:
                logger.warning(f"No data found for year {year}")

        if netcdf_files:
            logger.info("All tiles fetched. Starting final merge...")
            # Sort files to ensure consistent time ordering
            netcdf_files.sort()
            merge_netcdf_to_hdf5(netcdf_files, OUTPUT_FILE)
            append_log(f"SUCCESS: Full dataset merged to {OUTPUT_FILE}")
        else:
            logger.error("No data was fetched. Aborting merge.")
            append_log("FAILURE: No data fetched for full dataset.")
            raise RuntimeError("No data fetched.")

    except Exception as e:
        logger.error(f"Full fetch process failed: {e}", exc_info=True)
        append_log(f"FAILURE: {e}")
        raise
    finally:
        # Cleanup temp directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temp directory: {temp_dir}")

if __name__ == "__main__":
    main()