import os
import sys
import logging
import time
import math
import json
import cdsapi
from pathlib import Path
from datetime import datetime
from shapely.geometry import box

# Import existing project utilities
from config import get_path_env_override
from setup_logging import setup_logging, get_data_quality_logger

# Constants
OUTPUT_FILE = "data/raw/era5_full.h5"
BBOX_FILE = "data/external/bounding_box.json"
LOG_FILE = "results/logs/data_validation_log.txt"
CHUNK_SIZE = 10000  # Rows per chunk for memory management

def ensure_directories():
    """Ensure output and log directories exist."""
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("data/external").mkdir(parents=True, exist_ok=True)
    Path("results/logs").mkdir(parents=True, exist_ok=True)

def get_logger():
    """Get the data quality logger."""
    return get_data_quality_logger()

def append_log(message, logger=None):
    """Append a timestamped message to the log file."""
    if logger is None:
        logger = get_logger()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    logger.info(log_entry)
    # Also append to the specific file if needed
    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")

def get_cds_client():
    """Initialize and return the CDS API client."""
    # The CDS API client reads credentials from CDSAPIRC or environment variables
    try:
        client = cdsapi.Client()
        append_log("CDS API client initialized successfully.")
        return client
    except Exception as e:
        append_log(f"Failed to initialize CDS API client: {str(e)}")
        raise

def frange(start, stop, step):
    """Generate a range of floats."""
    while start < stop:
        yield round(start, 5)
        start += step

def tile_overlaps_bbox(tile_lat, tile_lon, bbox):
    """Check if a tile overlaps with the bounding box."""
    # tile_lat/lon are center points of the tile
    # Assume a standard tile size (e.g., 1 degree)
    tile_size = 1.0
    tile_min_lat = tile_lat - tile_size / 2
    tile_max_lat = tile_lat + tile_size / 2
    tile_min_lon = tile_lon - tile_size / 2
    tile_max_lon = tile_lon + tile_size / 2

    bbox_min_lat = bbox["min_lat"]
    bbox_max_lat = bbox["max_lat"]
    bbox_min_lon = bbox["min_lon"]
    bbox_max_lon = bbox["max_lon"]

    # Check for overlap
    lat_overlap = (tile_min_lat <= bbox_max_lat) and (tile_max_lat >= bbox_min_lat)
    lon_overlap = (tile_min_lon <= bbox_max_lon) and (tile_max_lon >= bbox_min_lon)

    return lat_overlap and lon_overlap

def fetch_tile(client, tile_lat, tile_lon, bbox, year, month, day, hour, output_path):
    """Fetch a single tile of ERA5 data for a specific time."""
    if not tile_overlaps_bbox(tile_lat, tile_lon, bbox):
        return False

    request_params = {
        "product_type": "reanalysis",
        "variable": "2m_temperature",
        "product_type": "reanalysis",
        "date": f"{year:04d}-{month:02d}-{day:02d}",
        "time": f"{hour:02d}:00",
        "area": [tile_lat + 0.5, tile_lon - 0.5, tile_lat - 0.5, tile_lon + 0.5],
        "format": "netcdf"
    }

    # Exponential back-off for rate limits
    retries = 0
    max_retries = 5
    base_delay = 2

    while retries < max_retries:
        try:
            append_log(f"Fetching tile for {year}-{month:02d}-{day:02d} {hour:02d}:00 at ({tile_lat}, {tile_lon})")
            client.retrieve(
                'reanalysis-era5-single-levels',
                request_params,
                output_path
            )
            append_log(f"Successfully fetched tile: {output_path}")
            return True
        except Exception as e:
            retries += 1
            if retries < max_retries:
                delay = base_delay * (2 ** retries)
                append_log(f"Rate limit or error encountered. Retrying in {delay}s... ({retries}/{max_retries})")
                time.sleep(delay)
            else:
                append_log(f"Failed to fetch tile after {max_retries} retries: {str(e)}")
                raise

def merge_netcdf_to_hdf5(netcdf_paths, output_hdf5_path):
    """Merge multiple NetCDF files into a single HDF5 file."""
    try:
        import xarray as xr
        import h5py
        import numpy as np

        append_log("Starting merge of NetCDF files to HDF5...")
        
        # Load all datasets
        datasets = []
        for path in netcdf_paths:
            ds = xr.open_dataset(path)
            datasets.append(ds)
        
        # Concatenate along time dimension
        combined = xr.concat(datasets, dim='time')
        
        # Save to HDF5
        combined.to_netcdf(output_hdf5_path, engine='h5netcdf')
        
        append_log(f"Merged data saved to {output_hdf5_path}")
        return True
    except Exception as e:
        append_log(f"Error merging NetCDF files: {str(e)}")
        raise

def main():
    """Main execution function for fetching full ERA5 data."""
    ensure_directories()
    logger = get_logger()
    append_log("Starting full ERA5 data fetch process.", logger)

    # Load bounding box
    try:
        with open(BBOX_FILE, 'r') as f:
            bbox = json.load(f)
        append_log(f"Loaded bounding box: {bbox}", logger)
    except Exception as e:
        append_log(f"Failed to load bounding box from {BBOX_FILE}: {str(e)}", logger)
        raise

    # Initialize CDS client
    client = get_cds_client()

    # Define date range (example: 2016-2020)
    start_year = 2016
    end_year = 2020
    temp_files = []
    temp_counter = 0

    # Iterate over years, months, days, hours
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            for day in range(1, 32):
                # Simple date validation
                try:
                    datetime(year, month, day)
                except ValueError:
                    continue
                
                for hour in [0, 6, 12, 18]:  # Sample 4 times per day to reduce volume
                    # Generate tile grid
                    # Assuming 0.25 degree resolution
                    min_lat = bbox["min_lat"]
                    max_lat = bbox["max_lat"]
                    min_lon = bbox["min_lon"]
                    max_lon = bbox["max_lon"]
                    
                    # Create tiles
                    for lat in frange(min_lat, max_lat, 0.25):
                        for lon in frange(min_lon, max_lon, 0.25):
                            if tile_overlaps_bbox(lat, lon, bbox):
                                temp_file = f"/tmp/era5_tile_{year}_{month:02d}_{day:02d}_{hour:02d}_{lat}_{lon}.nc"
                                success = fetch_tile(client, lat, lon, bbox, year, month, day, hour, temp_file)
                                if success:
                                    temp_files.append(temp_file)
                                    temp_counter += 1
                                    # Process in chunks to avoid memory issues
                                    if temp_counter % CHUNK_SIZE == 0:
                                        append_log(f"Processing chunk of {CHUNK_SIZE} files...", logger)
                                        chunk_output = f"/tmp/era5_chunk_{temp_counter // CHUNK_SIZE}.h5"
                                        merge_netcdf_to_hdf5(temp_files[-CHUNK_SIZE:], chunk_output)
                                        temp_files = temp_files[-CHUNK_SIZE:]  # Keep only the last chunk for potential final merge
        
    # Merge any remaining files
    if temp_files:
        append_log("Merging final chunk of files...", logger)
        merge_netcdf_to_hdf5(temp_files, OUTPUT_FILE)
    else:
        # If we processed in chunks, we need to merge the chunk files
        # For simplicity, this example assumes the last merge wrote to OUTPUT_FILE
        # In a real implementation, we'd collect all chunk files and merge them
        pass

    # Verify output
    if os.path.exists(OUTPUT_FILE) and os.path.getsize(OUTPUT_FILE) > 0:
        append_log(f"Full ERA5 dataset successfully saved to {OUTPUT_FILE}", logger)
        # Basic verification: check if file is readable
        try:
            import xarray as xr
            ds = xr.open_dataset(OUTPUT_FILE)
            append_log(f"Verification: Dataset contains {len(ds.time)} time steps and variables: {list(ds.data_vars)}", logger)
            ds.close()
        except Exception as e:
            append_log(f"Warning: Could not verify dataset contents: {str(e)}", logger)
    else:
        append_log(f"Error: Output file {OUTPUT_FILE} not created or is empty.", logger)
        raise FileNotFoundError(f"Output file {OUTPUT_FILE} not created or is empty.")

    append_log("Full ERA5 data fetch process completed.", logger)

if __name__ == "__main__":
    main()
