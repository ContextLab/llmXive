"""
T002b: Fetch ERA5 Subset (Targeted)

Reads the bounding box defined in data/external/bounding_box.json,
requests 2m_temperature reanalysis data for 2014-2018 via CDS API,
handles rate limits with exponential backoff, and saves raw chunks
to data/raw/era5_raw_chunks/.
"""
import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
import cdsapi

# Ensure project root is in path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path_env_override
from setup_logging import setup_logging, get_data_quality_logger

# Configuration
VARIABLE = "2m_temperature"
PRODUCT_TYPE = "reanalysis"
GRID = "0.25/0.25"
YEARS = ["2014", "2015", "2016", "2017", "2018"]
MONTHS = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
DAYS = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31"]
TIME = ["00:00", "01:00", "02:00", "03:00", "04:00", "05:00", "06:00", "07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00", "23:00"]

MAX_RETRIES = 5
BASE_DELAY = 2.0  # seconds

def ensure_directories():
    output_dir = project_root / "data" / "raw" / "era5_raw_chunks"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def get_cds_client():
    """Initialize CDS API client."""
    try:
        client = cdsapi.Client()
        return client
    except Exception as e:
        logger = get_data_quality_logger()
        logger.error(f"Failed to initialize CDS client: {e}")
        raise

def fetch_tile(client, year, month, day, time, bbox, output_dir):
    """
    Fetch a single ERA5 tile for a specific timestamp.
    Implements exponential backoff on rate limit errors.
    """
    # Format: "YYYY-MM-DDTHH:00"
    timestamp_str = f"{year}-{month}-{day}T{time}"
    
    # Construct filename
    filename = f"era5_{year}_{month}_{day}_{time.replace(':', '_')}.nc"
    output_path = output_dir / filename

    if output_path.exists():
        logging.info(f"Skipping {filename} (already exists)")
        return output_path

    attempt = 0
    delay = BASE_DELAY
    last_error = None

    while attempt < MAX_RETRIES:
        try:
            request_params = {
                "variable": VARIABLE,
                "product_type": PRODUCT_TYPE,
                "format": "netcdf",
                "year": year,
                "month": month,
                "day": day,
                "time": time,
                "area": [
                    bbox["north"],
                    bbox["west"],
                    bbox["south"],
                    bbox["east"]
                ],
                "grid": GRID.split("/"),
            }

            client.retrieve(
                "reanalysis-era5-single-levels",
                request_params,
                str(output_path)
            )
            logging.info(f"Successfully fetched {filename}")
            return output_path

        except Exception as e:
            last_error = e
            error_msg = str(e)
            
            # Check for rate limit errors (HTTP 429 or specific CDS messages)
            if "429" in error_msg or "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
                attempt += 1
                if attempt < MAX_RETRIES:
                    logging.warning(f"Rate limit hit for {filename}. Retrying in {delay:.1f}s (attempt {attempt}/{MAX_RETRIES})...")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                    continue
            
            # For other errors, log and fail immediately
            logging.error(f"Error fetching {filename}: {e}")
            raise

    # If we exhausted retries
    raise RuntimeError(f"Failed to fetch {filename} after {MAX_RETRIES} attempts. Last error: {last_error}")

def load_bounding_box():
    """Load the bounding box from the JSON file."""
    bbox_path = project_root / "data" / "external" / "bounding_box.json"
    if not bbox_path.exists():
        raise FileNotFoundError(f"Bounding box file not found: {bbox_path}")
    
    with open(bbox_path, "r") as f:
        return json.load(f)

def main():
    logger = setup_logging()
    data_logger = get_data_quality_logger()
    
    logger.info("Starting T002b: Fetch ERA5 Subset (Targeted)")
    data_logger.info("T002b: Starting ERA5 subset fetch")

    try:
        # 1. Read bounding box
        bbox = load_bounding_box()
        logger.info(f"Loaded bounding box: {bbox}")
        data_logger.info(f"Bounding box loaded: {bbox}")

        # 2. Ensure output directory
        output_dir = ensure_directories()
        logger.info(f"Output directory: {output_dir}")

        # 3. Initialize CDS client
        client = get_cds_client()
        logger.info("CDS client initialized")

        # 4. Fetch tiles for each timestamp in the range
        # Note: This is a potentially very large operation. 
        # The task asks for 2014-2018.
        # We will iterate through years, months, days, times.
        
        total_fetches = len(YEARS) * len(MONTHS) * len(DAYS) * len(TIME)
        logger.info(f"Total potential fetches: {total_fetches}")
        
        success_count = 0
        error_count = 0

        for year in YEARS:
            for month in MONTHS:
                # Skip invalid days for specific months (simple check)
                if int(month) in [4, 6, 9, 11]:
                    valid_days = DAYS[:30]
                elif int(month) == 2:
                    # Leap year check
                    is_leap = (int(year) % 4 == 0 and (int(year) % 100 != 0 or int(year) % 400 == 0))
                    valid_days = DAYS[:29] if is_leap else DAYS[:28]
                else:
                    valid_days = DAYS
                
                for day in valid_days:
                    for time_val in TIME:
                        try:
                            fetch_tile(client, year, month, day, time_val, bbox, output_dir)
                            success_count += 1
                        except Exception as e:
                            error_count += 1
                            logger.error(f"Failed to fetch {year}-{month}-{day} {time_val}: {e}")
                            # Do not abort on single tile failure, log and continue
                            # unless it's a critical configuration error
                            if "401" in str(e) or "403" in str(e):
                                logger.critical("Authentication error. Aborting.")
                                data_logger.critical("Authentication error. Aborting.")
                                sys.exit(1)

        logger.info(f"Fetch complete. Success: {success_count}, Errors: {error_count}")
        data_logger.info(f"T002b: Fetch complete. Success: {success_count}, Errors: {error_count}")

    except FileNotFoundError as e:
        logger.error(f"Configuration error: {e}")
        data_logger.error(f"T002b: Configuration error - {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Critical error during fetch: {e}")
        data_logger.error(f"T002b: Critical error - {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
