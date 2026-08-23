"""
T001b: Ingest & Validate ERA5 Sample

Fetches a specific sample subset (Jan 1-7, 2016, London) from the CDS API,
converts it to HDF5, validates hourly resolution and temperature values,
and logs the result to results/logs/data_validation_log.txt.
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

import cdsapi
import h5py
import xarray as xr
import numpy as np

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
LOGS_DIR = PROJECT_ROOT / "results" / "logs"
LOG_FILE = LOGS_DIR / "data_validation_log.txt"
OUTPUT_FILE = DATA_RAW_DIR / "era_sample.h5"

# Configuration for the sample
SAMPLE_YEAR = 2016
SAMPLE_START = "01"  # Jan
SAMPLE_END = "07"    # Jan 7
LONDON_LAT = 51.50
LONDON_LON = -0.12
VARIABLE = "2m_temperature"
PRODUCT_TYPE = "reanalysis"
FORMAT = "netcdf"

def setup_logging():
    """Configure logging to append to the specific validation log file."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("validate_era5")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates if re-run in same process
    if logger.handlers:
        logger.handlers.clear()
    
    file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    return logger

def log_validation_status(logger, status, details):
    """Append a structured log entry."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] STATUS: {status} | DETAILS: {details}"
    logger.info(log_entry)

def fetch_era5_sample(client, logger):
    """
    Fetches the specific sample from CDS API.
    Returns the path to the downloaded NetCDF file or raises an exception on failure.
    """
    # Define request parameters
    request = {
        "variable": VARIABLE,
        "product_type": PRODUCT_TYPE,
        "date": f"{SAMPLE_YEAR}-{SAMPLE_START}-01/to/{SAMPLE_YEAR}-{SAMPLE_END}-07",
        "time": [
            "00:00", "01:00", "02:00", "03:00", "04:00", "05:00",
            "06:00", "07:00", "08:00", "09:00", "10:00", "11:00",
            "12:00", "13:00", "14:00", "15:00", "16:00", "17:00",
            "18:00", "19:00", "20:00", "21:00", "22:00", "23:00"
        ],
        "area": [
            LONDON_LAT + 0.5,  # North
            LONDON_LON - 0.5,  # West
            LONDON_LAT - 0.5,  # South
            LONDON_LON + 0.5   # East
        ],
        "format": FORMAT,
    }

    logger.info(f"Fetching ERA5 sample for {request['date']} around London...")
    
    # The CDS API returns the file path if successful
    try:
        output_path = client.retrieve(
            "reanalysis-era5-single-levels",
            request,
            str(OUTPUT_FILE.with_suffix('.nc')) # Download to .nc first
        )
        return output_path
    except Exception as e:
        logger.error(f"CDS API retrieval failed: {str(e)}")
        raise

def convert_netcdf_to_hdf5(nc_path, logger):
    """
    Converts the downloaded NetCDF file to HDF5 format for efficient storage.
    """
    logger.info(f"Converting {nc_path} to HDF5...")
    try:
        ds = xr.open_dataset(nc_path)
        # Save as HDF5 (xarray uses HDF5 backend for .h5)
        ds.to_netcdf(str(OUTPUT_FILE), engine='h5netcdf')
        ds.close()
        logger.info(f"Conversion successful: {OUTPUT_FILE}")
        return True
    except Exception as e:
        logger.error(f"Conversion to HDF5 failed: {str(e)}")
        raise

def validate_hdf5_sample(logger):
    """
    Validates the HDF5 file:
    1. Checks hourly resolution (time dimension size).
    2. Checks for valid temperature values (not NaN, reasonable range).
    """
    logger.info("Validating HDF5 sample content...")
    
    if not OUTPUT_FILE.exists():
        log_validation_status(logger, "FAIL", "Output file does not exist.")
        return False

    try:
        ds = xr.open_dataset(str(OUTPUT_FILE))
        
        # 1. Check Time Resolution
        # Expected: 7 days * 24 hours = 168 steps
        expected_steps = 7 * 24
        actual_steps = len(ds.time)
        
        if actual_steps != expected_steps:
            msg = f"Time resolution mismatch: Expected {expected_steps} hourly steps, found {actual_steps}."
            log_validation_status(logger, "FAIL", msg)
            ds.close()
            return False
        
        # 2. Check Temperature Values
        temp_var = "2t" # Standard ERA5 variable name for 2m temperature
        if temp_var not in ds.data_vars:
            # Try to find it by case or alternative name
            temp_var = next((k for k in ds.data_vars if "temperature" in k.lower()), None)
            if not temp_var:
                msg = "Temperature variable '2t' not found in dataset."
                log_validation_status(logger, "FAIL", msg)
                ds.close()
                return False

        temp_data = ds[temp_var].values
        
        # Check for NaNs
        nan_count = np.isnan(temp_data).sum()
        if nan_count > 0:
            msg = f"Found {nan_count} NaN values in temperature data."
            log_validation_status(logger, "FAIL", msg)
            ds.close()
            return False

        # Check physical range (Kelvin): 200K to 340K is a safe operational range for Earth
        min_temp = temp_data.min()
        max_temp = temp_data.max()
        
        if min_temp < 200 or max_temp > 340:
            msg = f"Temperature out of plausible range: Min={min_temp}K, Max={max_temp}K."
            log_validation_status(logger, "FAIL", msg)
            ds.close()
            return False

        log_msg = f"Validation Passed: {actual_steps} hourly steps. Temp range [{min_temp:.2f}K, {max_temp:.2f}K]. No NaNs."
        log_validation_status(logger, "SUCCESS", log_msg)
        
        ds.close()
        return True

    except Exception as e:
        log_validation_status(logger, "FAIL", f"Validation error: {str(e)}")
        return False

def main():
    """Main entry point for T001b."""
    logger = setup_logging()
    log_validation_status(logger, "START", "T001b: Ingest & Validate ERA5 Sample")

    try:
        # 1. Initialize CDS Client
        # The client reads configuration from CDSAPI_KEY or ~/.cdsapirc
        client = cdsapi.Client()

        # 2. Fetch Sample
        nc_path = fetch_era5_sample(client, logger)

        # 3. Convert to HDF5
        convert_netcdf_to_hdf5(nc_path, logger)

        # 4. Validate Content
        is_valid = validate_hdf5_sample(logger)

        if is_valid:
            log_validation_status(logger, "COMPLETE", "T001b finished successfully.")
            sys.exit(0)
        else:
            log_validation_status(logger, "COMPLETE", "T001b finished with validation errors.")
            sys.exit(1)

    except Exception as e:
        log_validation_status(logger, "ERROR", f"Fatal error during execution: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
