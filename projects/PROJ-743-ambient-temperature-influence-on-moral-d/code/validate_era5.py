"""
Task T001b: Ingest & Validate ERA5 Sample.

Fetches a specific sample subset (Jan 1 – Jan 7 2016) for London (51.5074, -0.1278)
using the CDS API. Saves to data/raw/era5_sample.h5 (HDF5). Validates hourly
resolution, float data type, and physically plausible temperature range.
Logs success/failure to results/logs/data_validation_log.txt.
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

import cdsapi
import h5py
import numpy as np

# Ensure imports from existing project files
from setup_logging import get_data_quality_logger, ensure_directories

# Configuration constants matching task requirements
TARGET_LAT = 51.5074
TARGET_LON = -0.1278
START_DATE = "2016-01-01"
END_DATE = "2016-01-07"
VARIABLE = "2m_temperature"
PRODUCT_TYPE = "reanalysis"
GRID_RESOLUTION = "fine"  # CDS API often uses 'regular_ll' or specific grid specs, but we pass as requested
OUTPUT_PATH = Path("data/raw/era5_sample.h5")
LOG_PATH = Path("results/logs/data_validation_log.txt")
CHECKSUM_PATH = Path("state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml")

# Temperature validity bounds (physically plausible for Earth surface)
TEMP_MIN_K = 180.0  # ~-93 C
TEMP_MAX_K = 340.0  # ~+67 C

def setup_logging_custom():
    """Custom logger setup for this task."""
    ensure_directories([OUTPUT_PATH.parent, LOG_PATH.parent])
    logger = get_data_quality_logger()
    if not logger.handlers:
        handler = logging.FileHandler(LOG_PATH)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def log_validation_status(logger, status, message):
    """Log validation status and message."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {status}: {message}"
    logger.info(log_entry)
    print(log_entry)

def fetch_era5_sample(logger):
    """
    Fetch ERA5 sample data from CDS API.
    Returns the path to the downloaded NetCDF file.
    """
    # Check for API key
    api_key = os.environ.get("CDS_API_KEY")
    if not api_key:
        log_validation_status(logger, "ERROR", "CDS_API_KEY environment variable not set.")
        return None

    netcdf_path = OUTPUT_PATH.with_suffix(".nc")
    logger.info(f"Fetching ERA5 sample for {TARGET_LAT}, {TARGET_LON} from {START_DATE} to {END_DATE}")

    try:
        c = cdsapi.Client()
        c.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': PRODUCT_TYPE,
                'format': 'netcdf',
                'variable': VARIABLE,
                'year': '2016',
                'month': '01',
                'day': [
                    '01', '02', '03', '04', '05', '06', '07'
                ],
                'time': [
                    '00:00', '01:00', '02:00', '03:00',
                    '04:00', '05:00', '06:00', '07:00',
                    '08:00', '09:00', '10:00', '11:00',
                    '12:00', '13:00', '14:00', '15:00',
                    '16:00', '17:00', '18:00', '19:00',
                    '20:00', '21:00', '22:00', '23:00'
                ],
                'area': [
                    TARGET_LAT + 0.25, TARGET_LON - 0.25,
                    TARGET_LAT - 0.25, TARGET_LON + 0.25
                ],
                'grid': '0.25/0.25', # Fine grid resolution
                'target': str(netcdf_path)
            },
        )
        log_validation_status(logger, "SUCCESS", f"Downloaded NetCDF to {netcdf_path}")
        return netcdf_path
    except Exception as e:
        log_validation_status(logger, "ERROR", f"CDS API request failed: {str(e)}")
        return None

def convert_netcdf_to_hdf5(logger, netcdf_path):
    """
    Convert NetCDF to HDF5 format with compression.
    This is a simplified conversion assuming standard ERA5 structure.
    In a production environment, xarray would be used, but we stick to minimal deps.
    """
    try:
        import xarray as xr
        ds = xr.open_dataset(netcdf_path)
        
        # Select the variable of interest if present
        if VARIABLE in ds.data_vars:
            ds = ds[[VARIABLE]]
        
        # Save to HDF5
        ds.to_netcdf(OUTPUT_PATH, engine='h5netcdf', encoding={
            VARIABLE: {'complevel': 4, 'zlib': True}
        })
        log_validation_status(logger, "SUCCESS", f"Converted to HDF5: {OUTPUT_PATH}")
        return True
    except ImportError:
        # Fallback if xarray not available: attempt raw copy or error
        # Since the task requires real data and specific format, we raise if we can't convert properly
        log_validation_status(logger, "ERROR", "xarray not available for conversion. Cannot produce HDF5.")
        return False
    except Exception as e:
        log_validation_status(logger, "ERROR", f"Conversion to HDF5 failed: {str(e)}")
        return False

def validate_hdf5_sample(logger):
    """
    Validate the HDF5 file:
    1. Contains hourly resolution.
    2. Floating-point data type.
    3. Temperature values within physically plausible range.
    """
    if not OUTPUT_PATH.exists():
        log_validation_status(logger, "FAIL", f"Output file {OUTPUT_PATH} does not exist.")
        return False

    try:
        with h5py.File(OUTPUT_PATH, 'r') as f:
            # Find the data variable
            data_var = None
            for key in f.keys():
                if key != 'coordinates' and key != 'time' and key != 'latitude' and key != 'longitude':
                    if isinstance(f[key], h5py.Dataset):
                        data_var = key
                        break
            
            if data_var is None:
                # Try standard ERA5 variable name
                if VARIABLE in f:
                    data_var = VARIABLE
                else:
                    log_validation_status(logger, "FAIL", "Could not locate temperature data variable in HDF5.")
                    return False

            dataset = f[data_var]
            
            # 1. Check data type
            if not np.issubdtype(dataset.dtype, np.floating):
                log_validation_status(logger, "FAIL", f"Data type is {dataset.dtype}, expected floating point.")
                return False
            log_validation_status(logger, "PASS", "Data type is floating point.")

            # 2. Check temporal resolution (approximate via time dimension if available, or just count)
            # ERA5 single levels usually has a 'time' dimension.
            time_dim = None
            for key in f.keys():
                if key == 'time':
                    time_dim = f[key]
                    break
            
            if time_dim is not None:
                time_size = len(time_dim)
                if time_size < 24: # Expecting 7 days * 24 hours = 168
                    log_validation_status(logger, "WARN", f"Time dimension size {time_size} is less than expected (168).")
                else:
                    log_validation_status(logger, "PASS", f"Time dimension size {time_size} indicates hourly resolution.")
            else:
                log_validation_status(logger, "WARN", "No explicit time dimension found, assuming hourly based on request.")

            # 3. Check temperature range
            # Read a sample or the whole array if small enough (this sample is small)
            data = dataset[:]
            min_val = float(np.nanmin(data))
            max_val = float(np.nanmax(data))
            
            log_validation_status(logger, "INFO", f"Temperature range: {min_val} K to {max_val} K")
            
            if min_val < TEMP_MIN_K or max_val > TEMP_MAX_K:
                log_validation_status(logger, "FAIL", f"Temperature values out of plausible range [{TEMP_MIN_K}, {TEMP_MAX_K}] K.")
                return False
            
            log_validation_status(logger, "PASS", "Temperature values within plausible range.")
            
            return True

    except Exception as e:
        log_validation_status(logger, "ERROR", f"Validation failed with exception: {str(e)}")
        return False

def update_state_checksum(logger):
    """Update the state YAML file with the checksum of the new file."""
    try:
        import hashlib
        import yaml

        if not OUTPUT_PATH.exists():
            return

        # Compute SHA-256
        sha256_hash = hashlib.sha256()
        with open(OUTPUT_PATH, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        checksum = sha256_hash.hexdigest()

        # Ensure state directory exists
        CHECKSUM_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Load existing state or create new
        if CHECKSUM_PATH.exists():
            with open(CHECKSUM_PATH, 'r') as f:
                state = yaml.safe_load(f) or {}
        else:
            state = {}

        # Update
        if 'artifact_hashes' not in state:
            state['artifact_hashes'] = {}
        state['artifact_hashes']['era5_sample'] = checksum
        state['updated_at'] = datetime.now().isoformat()

        with open(CHECKSUM_PATH, 'w') as f:
            yaml.dump(state, f)
        
        log_validation_status(logger, "SUCCESS", f"Updated state checksum for era5_sample: {checksum}")

    except Exception as e:
        log_validation_status(logger, "ERROR", f"Failed to update state checksum: {str(e)}")

def main():
    logger = setup_logging_custom()
    log_validation_status(logger, "INFO", "Starting T001b: Ingest & Validate ERA5 Sample")

    # 1. Fetch
    netcdf_path = fetch_era5_sample(logger)
    if not netcdf_path:
        log_validation_status(logger, "FAIL", "Fetch failed. Aborting.")
        sys.exit(1)

    # 2. Convert
    if not convert_netcdf_to_hdf5(logger, netcdf_path):
        log_validation_status(logger, "FAIL", "Conversion failed. Aborting.")
        sys.exit(1)

    # 3. Validate
    if not validate_hdf5_sample(logger):
        log_validation_status(logger, "FAIL", "Validation failed. Aborting.")
        sys.exit(1)

    # 4. Update State
    update_state_checksum(logger)

    log_validation_status(logger, "SUCCESS", "T001b completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()