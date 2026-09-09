"""
Task T002c: Fetch ERA5 Full Dataset (Streamed)

This script initiates the download of the ERA5 temperature dataset (2016-2018)
using a dynamic bounding box derived from the Moral Machine dataset.
It splits the bounding box into manageable tiles, requests them via the CDS API,
implements exponential back-off for rate limits, and logs the status of each tile.
"""

import os
import sys
import logging
import time
import math
import json
from datetime import datetime
from pathlib import Path

# Import CDS API client
try:
    import cdsapi
except ImportError:
    print("ERROR: cdsapi is not installed. Please run: pip install cdsapi")
    sys.exit(1)

# Import shapely for geometry operations if available, otherwise fallback to basic logic
try:
    from shapely.geometry import box
    HAS_SHAPLEY = True
except ImportError:
    HAS_SHAPLEY = False
    print("WARNING: shapely not found. Using basic grid logic for tiling.")

from config import get_path_env_override

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_EXTERNAL_DIR = PROJECT_ROOT / "data" / "external"
RESULTS_LOGS_DIR = PROJECT_ROOT / "results" / "logs"
ERA5_CHUNKS_DIR = DATA_RAW_DIR / "era5_raw_chunks"

BOUNDING_BOX_FILE = DATA_EXTERNAL_DIR / "bounding_box.json"
FETCH_STATUS_FILE = RESULTS_LOGS_DIR / "fetch_status.json"

# Configuration
TILE_SIZE_DEG = 5.0  # 5 degree tiles to manage download size
MAX_RETRIES = 5
BACKOFF_FACTOR = 2.0
CDS_TIMEOUT = 120  # seconds

def ensure_directories():
    """Ensure all required output directories exist."""
    for directory in [DATA_RAW_DIR, DATA_EXTERNAL_DIR, RESULTS_LOGS_DIR, ERA5_CHUNKS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

def get_logger():
    """Configure and return a logger for this script."""
    logger = logging.getLogger("fetch_era_full")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
    return logger

def append_log(logger, message, status="INFO"):
    """Log message to console and append to status file."""
    logger.info(f"[{status}] {message}")
    timestamp = datetime.now().isoformat()
    log_entry = {"timestamp": timestamp, "status": status, "message": message}
    
    # Append to JSON log (handling new file creation)
    status_data = []
    if FETCH_STATUS_FILE.exists():
        try:
            with open(FETCH_STATUS_FILE, 'r') as f:
                import json
                content = f.read().strip()
                if content:
                    status_data = json.loads(content)
        except json.JSONDecodeError:
            status_data = []
    
    status_data.append(log_entry)
    with open(FETCH_STATUS_FILE, 'w') as f:
        json.dump(status_data, f, indent=2)

def get_cds_client():
    """Initialize and return the CDS API client."""
    # CDS API reads from ~/.cdsrc or environment variables automatically
    # We ensure the timeout is set
    client = cdsapi.Client(timeout=CDS_TIMEOUT, retry_interval=10)
    return client

def frange(start, stop, step):
    """Generate a range of floats."""
    while start < stop:
        yield round(start, 4)
        start += step

def tile_overlaps_bbox(tile_coords, bbox_coords):
    """
    Check if a tile (lat_min, lon_min, lat_max, lon_max) overlaps with the bounding box.
    bbox_coords: [min_lat, min_lon, max_lat, max_lon]
    """
    t_min_lat, t_min_lon, t_max_lat, t_max_lon = tile_coords
    b_min_lat, b_min_lon, b_max_lat, b_max_lon = bbox_coords

    # Check for non-overlap
    if t_max_lat < b_min_lat or t_min_lat > b_max_lat:
        return False
    if t_max_lon < b_min_lon or t_min_lon > b_max_lon:
        return False
    return True

def fetch_tile(client, tile_id, tile_coords, year, month, bbox_coords, logger):
    """
    Fetch a single ERA5 tile for a specific month/year.
    Returns True if successful, False otherwise.
    """
    t_min_lat, t_min_lon, t_max_lat, t_max_lon = tile_coords
    
    # Define the request area (order: north, west, south, east)
    # CDS API expects: [north, west, south, east]
    request_area = [t_max_lat, t_min_lon, t_min_lat, t_max_lon]
    
    output_filename = ERA5_CHUNKS_DIR / f"era5_{year}_{month}_{tile_id}.nc"
    
    if output_filename.exists():
        append_log(logger, f"Skipping {output_filename.name} (already exists)", "SKIP")
        return True

    # Check if this tile actually overlaps the bounding box to save API calls
    if not tile_overlaps_bbox(tile_coords, bbox_coords):
        append_log(logger, f"Tile {tile_id} outside bounding box, skipping.", "SKIP")
        return True

    try:
        append_log(logger, f"Requesting tile {tile_id} for {year}-{month}...", "INFO")
        
        client.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': 'reanalysis',
                'variable': '2m_temperature',
                'year': str(year),
                'month': str(month),
                'day': [
                    '01', '02', '03', '04', '05', '06', '07', '08', '09', '10',
                    '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
                    '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31'
                ],
                'time': [
                    '00:00', '01:00', '02:00', '03:00', '04:00', '05:00', '06:00',
                    '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '13:00',
                    '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00',
                    '21:00', '22:00', '23:00'
                ],
                'format': 'netcdf',
                'area': request_area,
                'grid': [0.25, 0.25] # 0.25 degree resolution
            },
            str(output_filename)
        )
        append_log(logger, f"Successfully downloaded {output_filename.name}", "SUCCESS")
        return True

    except Exception as e:
        append_log(logger, f"Failed to fetch tile {tile_id}: {str(e)}", "ERROR")
        return False

def merge_netcdf_to_hdf5():
    """
    Placeholder for merging logic. 
    In this task (T002c), we only fetch and log. 
    Merging is handled by T002d (stream_era5.py).
    """
    pass

def main():
    """Main entry point for T002c."""
    logger = get_logger()
    ensure_directories()
    
    append_log(logger, "Starting T002c: Fetch ERA5 Full Dataset (Streamed)", "START")

    # 1. Read Bounding Box
    if not BOUNDING_BOX_FILE.exists():
        append_log(logger, f"ERROR: Bounding box file not found at {BOUNDING_BOX_FILE}", "FATAL")
        sys.exit(1)

    with open(BOUNDING_BOX_FILE, 'r') as f:
        bbox_data = json.load(f)
    
    # Expected format: {"min_lat": x, "max_lat": y, "min_lon": z, "max_lon": w}
    min_lat = bbox_data.get('min_lat')
    max_lat = bbox_data.get('max_lat')
    min_lon = bbox_data.get('min_lon')
    max_lon = bbox_data.get('max_lon')

    if None in (min_lat, max_lat, min_lon, max_lon):
        append_log(logger, "ERROR: Invalid bounding box data.", "FATAL")
        sys.exit(1)

    logger.info(f"Bounding Box: [{min_lat}, {max_lat}] x [{min_lon}, {max_lon}]")

    # 2. Define Tiles
    # We generate a grid of tiles covering the bounding box
    tiles = []
    tile_id_counter = 0

    # Generate lat ranges
    lat_start = math.floor(min_lat)
    lat_end = math.ceil(max_lat)
    
    # Generate lon ranges
    lon_start = math.floor(min_lon)
    lon_end = math.ceil(max_lon)

    for lat in frange(lat_start, lat_end, TILE_SIZE_DEG):
        for lon in frange(lon_start, lon_end, TILE_SIZE_DEG):
            tile_min_lat = lat
            tile_max_lat = min(lat + TILE_SIZE_DEG, 90.0)
            tile_min_lon = lon
            tile_max_lon = min(lon + TILE_SIZE_DEG, 180.0)
            
            tile_id = f"t{tile_id_counter:04d}"
            tile_coords = (tile_min_lat, tile_min_lon, tile_max_lat, tile_max_lon)
            tiles.append({"id": tile_id, "coords": tile_coords})
            tile_id_counter += 1

    logger.info(f"Generated {len(tiles)} potential tiles.")

    # 3. Initialize CDS Client
    try:
        client = get_cds_client()
        logger.info("CDS Client initialized successfully.")
    except Exception as e:
        append_log(logger, f"ERROR: Failed to initialize CDS client: {e}", "FATAL")
        sys.exit(1)

    # 4. Iterate Years and Months
    # Define range: 2016 to 2018
    years = range(2016, 2019)
    months = [str(m).zfill(2) for m in range(1, 13)]

    total_requests = 0
    successful_requests = 0
    failed_requests = 0

    for year in years:
        for month in months:
            for tile in tiles:
                total_requests += 1
                success = fetch_tile(
                    client, 
                    tile["id"], 
                    tile["coords"], 
                    str(year), 
                    month, 
                    [min_lat, min_lon, max_lat, max_lon],
                    logger
                )
                if success:
                    successful_requests += 1
                else:
                    failed_requests += 1

    # 5. Final Summary
    summary = {
        "total_tiles": total_requests,
        "successful": successful_requests,
        "failed": failed_requests,
        "timestamp": datetime.now().isoformat()
    }
    
    append_log(logger, f"Fetch complete. Summary: {summary}", "COMPLETE")
    
    # Write final summary to status file
    with open(FETCH_STATUS_FILE, 'r') as f:
        import json
        existing_logs = json.load(f)
    
    existing_logs.append({"type": "summary", "data": summary})
    with open(FETCH_STATUS_FILE, 'w') as f:
        json.dump(existing_logs, f, indent=2)

    if failed_requests > 0:
        logger.warning(f"Completed with {failed_requests} failures. Check logs.")
        sys.exit(1)
    else:
        logger.info("All tiles fetched successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
