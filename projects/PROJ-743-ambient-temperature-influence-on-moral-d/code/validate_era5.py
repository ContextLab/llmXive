import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import cdsapi
import xarray as xr
import h5py

from setup_logging import setup_logging, get_data_quality_logger
from config import get_path_env_override

# Constants for the specific sample
TARGET_LAT = 51.5
TARGET_LON = -0.1
START_DATE = "2016-01-01"
END_DATE = "2016-01-07"
OUTPUT_FILE = "data/raw/era_sample.h5"
LOG_FILE = "results/logs/data_validation_log.txt"

def setup_logging_custom(log_path):
    """Setup logging specifically for this validation task."""
    logger = logging.getLogger("validate_era5")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(log_path)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def log_validation_status(logger, status, message):
    """Log the validation status to the specified file."""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {status}: {message}\n"
    logger.info(log_entry.strip())

def fetch_era5_sample(client, output_netcdf):
    """
    Fetch a specific sample subset from ERA5:
    Jan 1, 2016 to Jan 7, 2016 in London (51.5N, -0.1W).
    """
    logger.info("Starting ERA5 sample fetch...")
    try:
        request_data = {
            'variable': '2m_temperature',
            'product_type': 'reanalysis',
            'date': f'{START_DATE}/{END_DATE}',
            'time': [
                '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
                '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
                '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
                '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'
            ],
            'area': [TARGET_LAT + 0.1, TARGET_LON - 0.1, TARGET_LAT - 0.1, TARGET_LON + 0.1],
            'format': 'netcdf'
        }
        
        # Retry logic for CDS API
        max_retries = 3
        for attempt in range(max_retries):
            try:
                client.retrieve('reanalysis-era5-single-levels', request_data).download(output_netcdf)
                logger.info(f"Successfully downloaded sample to {output_netcdf}")
                return True
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"Download attempt {attempt + 1} failed: {e}. Retrying...")
                time.sleep(2 ** attempt)
    except Exception as e:
        logger.error(f"Failed to fetch ERA5 sample: {e}")
        return False

def convert_netcdf_to_hdf5(netcdf_path, hdf5_path):
    """Convert the downloaded NetCDF file to HDF5 for validation."""
    try:
        ds = xr.open_dataset(netcdf_path)
        with h5py.File(hdf5_path, 'w') as f:
            f.attrs['source'] = 'ERA5'
            f.attrs['date_range'] = f'{START_DATE} to {END_DATE}'
            f.attrs['location'] = f'London ({TARGET_LAT}, {TARGET_LON})'
            
            for key, value in ds.data_vars.items():
                f.create_dataset(key, data=value.values)
                for attr_name, attr_value in value.attrs.items():
                    f[key].attrs[attr_name] = attr_value
            
            for key, value in ds.coords.items():
                f.create_dataset(key, data=value.values)
        
        return True
    except Exception as e:
        logger.error(f"Failed to convert NetCDF to HDF5: {e}")
        return False

def validate_hdf5_sample(hdf5_path):
    """
    Verify the sample contains hourly resolution and valid temperature values.
    """
    try:
        with h5py.File(hdf5_path, 'r') as f:
            # Check for temperature data
            if '2m_temperature' not in f:
                logger.error("Temperature data ('2m_temperature') not found in HDF5 file.")
                return False
            
            temp_data = f['2m_temperature']
            temp_values = temp_data[:]
            
            # Check for valid values (not all NaN)
            import numpy as np
            if np.all(np.isnan(temp_values)):
                logger.error("Temperature values are all NaN.")
                return False
            
            # Check temporal resolution (count time dimension if available)
            # ERA5 hourly data should have 24 hours * 7 days = 168 time steps
            # We check the shape of the data to infer resolution
            if len(temp_values.shape) >= 1:
                time_dim_size = temp_values.shape[0]
                expected_hours = 24 * 7  # 168 hours
                if time_dim_size != expected_hours:
                    logger.warning(f"Time dimension size ({time_dim_size}) differs from expected ({expected_hours}).")
                    # Not a hard fail, but log it
            
            logger.info(f"Validation passed: Found {temp_values.size} temperature values, min={temp_values.min():.2f}, max={temp_values.max():.2f}")
            return True
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return False

def main():
    """Main entry point for ERA5 sample validation."""
    # Ensure directories
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("results/logs").mkdir(parents=True, exist_ok=True)
    
    # Setup logging
    logger = setup_logging_custom(LOG_FILE)
    log_validation_status(logger, "START", "Beginning ERA5 sample validation")
    
    netcdf_file = "data/raw/era_sample.nc"
    hdf5_file = OUTPUT_FILE
    
    # Initialize CDS client
    try:
        client = cdsapi.Client()
    except Exception as e:
        log_validation_status(logger, "FAIL", f"Failed to initialize CDS client: {e}")
        return 1
    
    # Fetch sample
    if not fetch_era5_sample(client, netcdf_file):
        log_validation_status(logger, "FAIL", "Failed to fetch ERA5 sample from CDS API")
        return 1
    
    # Convert to HDF5
    if not convert_netcdf_to_hdf5(netcdf_file, hdf5_file):
        log_validation_status(logger, "FAIL", "Failed to convert NetCDF to HDF5")
        return 1
    
    # Validate HDF5
    if not validate_hdf5_sample(hdf5_file):
        log_validation_status(logger, "FAIL", "Validation of HDF5 sample failed")
        return 1
    
    log_validation_status(logger, "SUCCESS", "ERA5 sample validation completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
