"""
Fetches a sample subset of ERA5 hourly 2m temperature data for 2016-2019 using the CDS API.

This script authenticates with the Copernicus Climate Data Store (CDS), requests
a small geographic subset to validate connectivity and data format, and saves
the result to data/raw/era5_sample.h5. It also logs the outcome to 
results/logs/data_validation_log.txt.

Dependencies:
    - cdsapi
    - pandas
    - pathlib
    - logging
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

try:
    import cdsapi
except ImportError:
    print("ERROR: cdsapi library is not installed. Please run: pip install cdsapi")
    sys.exit(1)

# Project root relative to this script (assuming code/ is at root level)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
RESULTS_LOGS_DIR = PROJECT_ROOT / "results" / "logs"
LOG_FILE = RESULTS_LOGS_DIR / "data_validation_log.txt"
OUTPUT_FILE = DATA_RAW_DIR / "era5_sample.h5"

# Ensure directories exist
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging to file
logger = logging.getLogger("era5_fetch")
logger.setLevel(logging.INFO)

# Clear existing handlers to avoid duplicates if run multiple times in same session
if logger.handlers:
    logger.handlers.clear()

fh = logging.FileHandler(LOG_FILE, mode='a')
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# Also log to console for immediate feedback
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

def fetch_era5_sample():
    """
    Fetches a small sample of ERA5 hourly 2m temperature data.
    
    Sample parameters:
      - Year: 2016 (first year of the range)
      - Month: January (first month)
      - Days: 1-2 (minimal days to reduce download time)
      - Time: 00:00 to 23:00 (24 hourly steps)
      - Area: A small box (e.g., London area) to keep file size small.
      - Format: netcdf (standard for analysis), saved as .h5 extension per task spec.
    """
    logger.info("Starting ERA5 sample fetch for validation.")
    
    # Define request parameters for a minimal sample
    request_params = {
        'variable': '2m_temperature',
        'product_type': 'reanalysis',
        'format': 'netcdf',
        'date': '2016-01-01/to/2016-01-02',
        'time': [
            '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
            '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
            '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
            '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'
        ],
        'area': [
            51.6,  # North
            -0.2,  # West
            51.4,  # South
            0.1    # East
        ],
        'year': '2016',
        'month': '01',
        'day': ['01', '02'],
        'hour': [
            '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
            '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
            '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
            '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'
        ]
    }

    try:
        client = cdsapi.Client(
            quiet=False
        )
        
        logger.info(f"Requesting data from CDS: {request_params['variable']} for {request_params['year']}.")
        
        # Execute request. The client handles authentication via ~/.cdsapirc
        client.retrieve(
            'reanalysis-era5-single-levels',
            request_params,
            str(OUTPUT_FILE)
        )
        
        # Verify file exists and has size > 0
        if OUTPUT_FILE.exists() and OUTPUT_FILE.stat().st_size > 0:
            logger.info(f"SUCCESS: Data fetched and saved to {OUTPUT_FILE}")
            logger.info(f"File size: {OUTPUT_FILE.stat().st_size} bytes")
            return True
        else:
            logger.error("FAILED: File created but is empty.")
            return False

    except Exception as e:
        logger.error(f"FAILED: Error during CDS retrieval: {str(e)}")
        # If the file was partially created, remove it to avoid confusion
        if OUTPUT_FILE.exists():
            try:
                OUTPUT_FILE.unlink()
            except OSError:
                pass
        return False

if __name__ == "__main__":
    success = fetch_era5_sample()
    if not success:
        sys.exit(1)
    else:
        sys.exit(0)