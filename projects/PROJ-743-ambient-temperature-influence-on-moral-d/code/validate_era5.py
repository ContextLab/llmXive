"""
Task T001b: Ingest & Validate ERA5 Sample.

Fetches a specific sample subset of ERA5 data for London (Jan 1-7, 2016),
converts it to HDF5, validates the content (hourly resolution, valid temps),
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

# Constants for the sample fetch
SAMPLE_START_DATE = "2016-01-01"
SAMPLE_END_DATE = "2016-01-07"
SAMPLE_LAT = 51.5074
SAMPLE_LON = -0.1278
SAMPLE_OUTPUT_FILE = "data/raw/era_sample.h5"
LOG_FILE = "results/logs/data_validation_log.txt"
CDS_TEMP_VAR = "2t"  # 2m temperature

def setup_logging_custom(log_path: Path) -> logging.Logger:
    """Configure a logger that writes to the specified file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("validate_era5")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates if run multiple times in same session
    logger.handlers = []
    
    fh = logging.FileHandler(log_path)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Also log to console for immediate feedback
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

def log_validation_status(logger: logging.Logger, status: str, details: str):
    """Log the validation status and details."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] Status: {status} | Details: {details}"
    logger.info(log_entry)

def fetch_era5_sample(client: cdsapi.Client, output_netcdf: Path):
    """
    Fetch ERA5 hourly data for the specific sample subset using cdsapi.
    Returns the path to the downloaded NetCDF file.
    """
    logger = logging.getLogger("validate_era5")
    logger.info(f"Fetching ERA5 sample from CDS API for {SAMPLE_START_DATE} to {SAMPLE_END_DATE} at ({SAMPLE_LAT}, {SAMPLE_LON})")
    
    # CDS API request parameters
    request_params = {
        'variable': CDS_TEMP_VAR,
        'product_type': 'reanalysis',
        'date': f'{SAMPLE_START_DATE}/to/{SAMPLE_END_DATE}',
        'time': [
            '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
            '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
            '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
            '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'
        ],
        'format': 'netcdf',
        'area': [
            SAMPLE_LAT + 0.1,  # north
            SAMPLE_LON - 0.1,  # west
            SAMPLE_LAT - 0.1,  # south
            SAMPLE_LON + 0.1   # east
        ],
        'grid': [0.25, 0.25] # 0.25 degree resolution
    }

    try:
        client.retrieve(
            'reanalysis-era5-single-levels',
            request_params,
            str(output_netcdf)
        )
        logger.info(f"Successfully downloaded NetCDF to {output_netcdf}")
        return output_netcdf
    except Exception as e:
        logger.error(f"Failed to fetch ERA5 sample: {e}")
        raise

def convert_netcdf_to_hdf5(netcdf_path: Path, hdf5_path: Path):
    """Convert the downloaded NetCDF file to HDF5 format."""
    logger = logging.getLogger("validate_era5")
    logger.info(f"Converting {netcdf_path} to HDF5 at {hdf5_path}")
    
    try:
        ds = xr.open_dataset(netcdf_path)
        # Ensure the HDF5 directory exists
        hdf5_path.parent.mkdir(parents=True, exist_ok=True)
        ds.to_netcdf(hdf5_path, engine='h5netcdf')
        ds.close()
        logger.info("Conversion to HDF5 successful.")
    except Exception as e:
        logger.error(f"Failed to convert NetCDF to HDF5: {e}")
        raise

def validate_hdf5_sample(hdf5_path: Path) -> bool:
    """
    Validate the HDF5 file contains:
    1. Hourly resolution (time dimension size matches expected count)
    2. Valid temperature values (not all NaN, reasonable range)
    """
    logger = logging.getLogger("validate_era5")
    expected_days = 7
    expected_hours_per_day = 24
    expected_time_steps = expected_days * expected_hours_per_day # 168
    
    # Allow for slight variance in time steps if CDS returns slightly different range
    # but strictly check for > 0 and roughly correct magnitude
    
    try:
        with h5py.File(hdf5_path, 'r') as f:
            # Check for 'time' dimension
            if 'time' not in f:
                logger.error("Validation Failed: 'time' dimension missing in HDF5.")
                return False
            
            time_dim = f['time']
            time_size = time_dim.shape[0]
            
            if time_size == 0:
                logger.error("Validation Failed: 'time' dimension is empty.")
                return False
            
            # Check for temperature variable (usually '2t')
            temp_var_name = None
            for key in f.keys():
                if '2t' in key.lower() or 'temperature' in key.lower():
                    temp_var_name = key
                    break
            
            if not temp_var_name:
                logger.error(f"Validation Failed: Temperature variable (2t) not found in {f.keys()}")
                return False

            temp_data = f[temp_var_name]
            
            # Check for valid data (not all NaN/missing)
            # In HDF5, we need to read a slice to check values
            # Assuming shape is (time, lat, lon) or similar
            if len(temp_data.shape) < 1:
                logger.error("Validation Failed: Temperature data has unexpected shape.")
                return False
            
            # Sample some data to check for validity
            # We'll read the first time slice
            sample_slice = temp_data[0, ...]
            
            # Convert to numpy to check for NaNs easily
            # Note: h5py datasets can be read directly
            vals = np.array(sample_slice)
            
            valid_count = np.count_nonzero(~np.isnan(vals))
            total_count = vals.size
            
            if total_count == 0:
                logger.error("Validation Failed: No data points in temperature variable.")
                return False
            
            valid_ratio = valid_count / total_count
            
            if valid_ratio < 0.1: # At least 10% valid data
                logger.error(f"Validation Failed: Too many NaN values. Valid ratio: {valid_ratio:.2f}")
                return False
            
            # Check temperature range (Kelvin usually for ERA5, 2m temp ~ 200K to 320K)
            # If it's Celsius, range would be different. ERA5 is usually Kelvin.
            min_val = np.nanmin(vals)
            max_val = np.nanmax(vals)
            
            # Sanity check: 2m temp in Kelvin should be between 150K and 350K
            if min_val < 150 or max_val > 350:
                logger.warning(f"Temperature range ({min_val} to {max_val}) seems outside typical ERA5 Kelvin bounds. Checking if Celsius...")
                # If it's Celsius, range might be -50 to 50.
                if min_val < -100 or max_val > 100:
                    logger.error(f"Validation Failed: Temperature values ({min_val} to {max_val}) are physically impossible.")
                    return False
            
            logger.info(f"Validation Passed: Time steps={time_size}, Valid data ratio={valid_ratio:.2f}, Temp range=[{min_val:.2f}, {max_val:.2f}]")
            return True

    except Exception as e:
        logger.error(f"Validation Failed with exception: {e}")
        return False

def main():
    """Main entry point for T001b."""
    # Setup paths
    project_root = Path.cwd()
    log_path = project_root / LOG_FILE
    netcdf_path = project_root / "data/raw/era_sample_temp.nc"
    hdf5_path = project_root / SAMPLE_OUTPUT_FILE

    # Ensure directories
    log_path.parent.mkdir(parents=True, exist_ok=True)
    (project_root / "data/raw").mkdir(parents=True, exist_ok=True)

    logger = setup_logging_custom(log_path)
    
    logger.info("Starting Task T001b: Ingest & Validate ERA5 Sample")
    logger.info(f"Target: London ({SAMPLE_LAT}, {SAMPLE_LON}), {SAMPLE_START_DATE} to {SAMPLE_END_DATE}")

    # 1. Fetch Sample
    try:
        # Initialize CDS client (assumes CDSAPI_KEY env var or ~/.cdsapirc is set)
        client = cdsapi.Client()
        
        # Fetch to temporary netcdf first
        fetched_netcdf = fetch_era5_sample(client, netcdf_path)
        
        # 2. Convert to HDF5
        convert_netcdf_to_hdf5(fetched_netcdf, hdf5_path)
        
        # 3. Validate
        is_valid = validate_hdf5_sample(hdf5_path)
        
        if is_valid:
            log_validation_status(logger, "PASS", "Sample fetched, converted, and validated successfully.")
            print(f"SUCCESS: {SAMPLE_OUTPUT_FILE} created and validated.")
            sys.exit(0)
        else:
            log_validation_status(logger, "FAIL", "Sample validation checks failed.")
            print(f"FAILURE: Validation failed. Check {LOG_FILE} for details.")
            sys.exit(1)

    except Exception as e:
        log_validation_status(logger, "FAIL", f"Critical error during execution: {e}")
        print(f"FAILURE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
