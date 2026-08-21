"""
Fetch a specific sample subset of ERA5 data for validation.

Target: Jan 1, 2016 to Jan 7, 2016 in London (51.5N, -0.1W).
Output: data/raw/era_sample.h5
Log: results/logs/data_validation_log.txt
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Ensure we can import sibling modules
sys.path.insert(0, str(Path(__file__).parent))

import cdsapi

from setup_logging import setup_logging, get_data_quality_logger
from config import get_path_env_override

# Constants for the sample fetch
SAMPLE_START_DATE = "2016-01-01"
SAMPLE_END_DATE = "2016-01-07"
SAMPLE_LATITUDE = 51.5
SAMPLE_LONGITUDE = -0.1
SAMPLE_OUTPUT_PATH = "data/raw/era_sample.h5"
LOG_FILE_PATH = "results/logs/data_validation_log.txt"

def ensure_directories():
    """Ensure output directories exist."""
    output_dir = Path(SAMPLE_OUTPUT_PATH).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir = Path(LOG_FILE_PATH).parent
    log_dir.mkdir(parents=True, exist_ok=True)

def fetch_era5_sample():
    """
    Fetch ERA5 hourly data for London, Jan 1-7, 2016.
    Uses the CDS API to retrieve 2-meter temperature.
    """
    ensure_directories()
    
    logger = get_data_quality_logger()
    logger.info(f"Starting ERA5 sample fetch for {SAMPLE_START_DATE} to {SAMPLE_END_DATE} at ({SAMPLE_LATITUDE}, {SAMPLE_LONGITUDE})")

    try:
        client = cdsapi.Client()
        
        # Request parameters
        request_params = {
            'variable': '2m_temperature',
            'product_type': 'reanalysis',
            'format': 'grib', # CDS API typically returns grib; we will convert or save as is. 
                             # Note: The task asks for .h5. CDS API returns grib. 
                             # We will fetch as grib and save as .h5 (netcdf4/h5) if possible, 
                             # or save the grib file with .h5 extension if conversion is not 
                             # strictly enforced by the pipeline to be HDF5 internally. 
                             # However, standard practice is to fetch NetCDF if available.
                             # CDS API 'format' can be 'netcdf'. Let's use 'netcdf' to get HDF5 compatible file.
            'format': 'netcdf', 
            'year': '2016',
            'month': '01',
            'day': ['01', '02', '03', '04', '05', '06', '07'],
            'time': [
                '00:00', '01:00', '02:00', '03:00', '04:00', '05:00', 
                '06:00', '07:00', '08:00', '09:00', '10:00', '11:00', 
                '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', 
                '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'
            ],
            'area': [
                SAMPLE_LATITUDE + 0.05, # North
                SAMPLE_LONGITUDE - 0.05, # West
                SAMPLE_LATITUDE - 0.05, # South
                SAMPLE_LONGITUDE + 0.05  # East
            ],
        }

        output_path = Path(SAMPLE_OUTPUT_PATH)
        
        # Execute request
        client.retrieve(
            'reanalysis-era5-single-levels',
            request_params,
            str(output_path)
        )

        if output_path.exists() and output_path.stat().st_size > 0:
            logger.info(f"Successfully fetched sample data to {output_path}")
            return True
        else:
            logger.error(f"Fetch completed but output file is empty or missing: {output_path}")
            return False

    except Exception as e:
        logger.error(f"Failed to fetch ERA5 sample data: {str(e)}")
        raise

def append_log(message):
    """Append a message to the validation log file."""
    log_path = Path(LOG_FILE_PATH)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def main():
    """Main entry point."""
    setup_logging()
    logger = get_data_quality_logger()
    
    try:
        success = fetch_era5_sample()
        if success:
            append_log(f"SUCCESS: Fetched ERA5 sample (2016-01-01 to 2016-01-07, London) to {SAMPLE_OUTPUT_PATH}")
            logger.info("Task T002 completed successfully.")
        else:
            append_log(f"FAIL: Fetched ERA5 sample but output file invalid.")
            logger.error("Task T002 failed.")
            sys.exit(1)
    except Exception as e:
        append_log(f"FAIL: Exception during T002: {str(e)}")
        logger.error(f"Task T002 failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
