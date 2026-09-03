"""
Validate ERA5 Sample Data Ingestion.

This script fetches a specific sample subset of ERA5 data (Jan 1-7, 2016)
for London using the CDS API, converts it to HDF5, and validates the
resulting file for resolution, data type, and physical plausibility.
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import cdsapi
import xarray as xr
import h5py
import numpy as np

# Ensure project root is in path for relative imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_path_env_override
from setup_logging import setup_logging, get_data_quality_logger

# Configuration for the sample
SAMPLE_LAT = 51.5074
SAMPLE_LON = -0.1278
START_DATE = "2016-01-01"
END_DATE = "2016-01-07"
VARIABLE = "2m_temperature"
PRODUCT_TYPE = "reanalysis"
GRID_RESOLUTION = "0.25"
OUTPUT_FILE = "data/raw/era5_sample.h5"
LOG_FILE = "results/logs/data_validation_log.txt"

# Physical limits for validation
TEMP_MIN = -50.0
TEMP_MAX = 60.0

def ensure_directories():
    """Create necessary directories for output and logs."""
    output_dir = Path(OUTPUT_FILE).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir = Path(LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)

def setup_logging_custom():
    """Setup custom logging for this script."""
    ensure_directories()
    logger = logging.getLogger("era5_validation")
    logger.setLevel(logging.INFO)

    # File handler
    fh = logging.FileHandler(LOG_FILE, mode='a')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)

    # Avoid duplicate handlers
    if not logger.handlers:
        logger.addHandler(fh)

    return logger

def log_validation_status(logger, status, message):
    """Log a validation status message."""
    if status == "PASS":
        logger.info(f"[VALIDATION PASS] {message}")
    elif status == "FAIL":
        logger.error(f"[VALIDATION FAIL] {message}")
    else:
        logger.info(message)

def fetch_era5_sample(logger):
    """Fetch ERA5 sample data using CDS API."""
    logger.info(f"Fetching ERA5 sample for {SAMPLE_LAT}, {SAMPLE_LON} from {START_DATE} to {END_DATE}")
    
    try:
        client = cdsapi.Client()
        request_data = {
            'product_type': PRODUCT_TYPE,
            'format': 'netcdf',
            'variable': VARIABLE,
            'year': '2016',
            'month': '01',
            'day': [
                '01', '02', '03', '04', '05', '06', '07'
            ],
            'time': [
                '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
                '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
                '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
                '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'
            ],
            'area': [
                SAMPLE_LAT + 0.1,
                SAMPLE_LON - 0.1,
                SAMPLE_LAT - 0.1,
                SAMPLE_LON + 0.1
            ],
            'grid': [0.25, 0.25],
            'data_format': 'netcdf'
        }
        
        # Temporary file for netcdf
        temp_netcdf = Path(OUTPUT_FILE).with_suffix('.nc')
        
        logger.info("Sending request to CDS API...")
        client.retrieve(
            'reanalysis-era5-single-levels',
            request_data,
            str(temp_netcdf)
        )
        
        if not temp_netcdf.exists():
            raise FileNotFoundError(f"Failed to download netCDF file to {temp_netcdf}")
        
        logger.info(f"Successfully downloaded netCDF to {temp_netcdf}")
        return str(temp_netcdf)
        
    except Exception as e:
        logger.error(f"Failed to fetch ERA5 data: {str(e)}")
        raise

def convert_netcdf_to_hdf5(netcdf_path, hdf5_path, logger):
    """Convert downloaded netCDF to HDF5 with compression."""
    logger.info(f"Converting {netcdf_path} to HDF5 at {hdf5_path}")
    
    try:
        # Load with xarray
        ds = xr.open_dataset(netcdf_path)
        
        # Ensure we have the right variable
        if VARIABLE not in ds.data_vars:
            raise KeyError(f"Variable '{VARIABLE}' not found in dataset. Available: {list(ds.data_vars)}")
        
        # Select the variable
        temp_data = ds[VARIABLE]
        
        # Create HDF5 file with compression
        with h5py.File(hdf5_path, 'w') as f:
            # Create dataset with compression
            dset = f.create_dataset(
                'temperature',
                data=temp_data.values,
                dtype='f4', # float32
                compression='gzip',
                compression_opts=4
            )
            
            # Store metadata as attributes
            dset.attrs['variable'] = VARIABLE
            dset.attrs['product_type'] = PRODUCT_TYPE
            dset.attrs['resolution'] = GRID_RESOLUTION
            dset.attrs['start_date'] = START_DATE
            dset.attrs['end_date'] = END_DATE
            dset.attrs['latitude'] = SAMPLE_LAT
            dset.attrs['longitude'] = SAMPLE_LON
            
            # Store coordinate info if available
            if 'time' in ds.coords:
                dset.attrs['time_coord'] = str(ds['time'].values)
            if 'latitude' in ds.coords:
                dset.attrs['lat_coord'] = str(ds['latitude'].values)
            if 'longitude' in ds.coords:
                dset.attrs['lon_coord'] = str(ds['longitude'].values)
        
        logger.info(f"Successfully converted to HDF5: {hdf5_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to convert to HDF5: {str(e)}")
        raise

def validate_hdf5_sample(hdf5_path, logger):
    """Validate the HDF5 file for resolution, dtype, and temperature range."""
    logger.info(f"Validating HDF5 file: {hdf5_path}")
    
    errors = []
    
    if not os.path.exists(hdf5_path):
        errors.append("File does not exist")
        for err in errors:
            log_validation_status(logger, "FAIL", err)
        return False
    
    try:
        with h5py.File(hdf5_path, 'r') as f:
            # Check dataset exists
            if 'temperature' not in f:
                errors.append("Dataset 'temperature' not found in HDF5 file")
            else:
                dset = f['temperature']
                
                # 1. Validate Data Type (Floating Point)
                dtype_str = str(dset.dtype)
                if not dtype_str.startswith('float'):
                    errors.append(f"Data type is {dtype_str}, expected floating-point")
                else:
                    log_validation_status(logger, "PASS", f"Data type is floating-point: {dtype_str}")
                
                # 2. Validate Hourly Resolution (Shape check)
                # ERA5 single level daily data usually has shape (time, lat, lon)
                # For 7 days * 24 hours = 168 time steps
                shape = dset.shape
                logger.info(f"Data shape: {shape}")
                
                if len(shape) < 3:
                    errors.append(f"Unexpected shape dimensions: {shape}. Expected at least 3 (time, lat, lon).")
                else:
                    time_dim = shape[0]
                    # Check if we have approximately 168 hours (7 days * 24)
                    # Allow some tolerance for grid selection
                    if time_dim < 100: # Rough check for hourly data over a week
                        errors.append(f"Time dimension {time_dim} is too small for hourly data over 7 days (expected ~168).")
                    else:
                        log_validation_status(logger, "PASS", f"Temporal resolution appears hourly (time dim: {time_dim})")
                
                # 3. Validate Temperature Range
                data = dset[:]
                min_val = np.nanmin(data)
                max_val = np.nanmax(data)
                
                logger.info(f"Temperature range: {min_val:.2f}°C to {max_val:.2f}°C")
                
                if min_val < TEMP_MIN:
                    errors.append(f"Minimum temperature {min_val:.2f}°C is below physical limit {TEMP_MIN}°C")
                if max_val > TEMP_MAX:
                    errors.append(f"Maximum temperature {max_val:.2f}°C is above physical limit {TEMP_MAX}°C")
                
                if not errors: # Only log pass if no range errors
                    log_validation_status(logger, "PASS", f"Temperature range [{min_val:.2f}, {max_val:.2f}] is within physical limits [{TEMP_MIN}, {TEMP_MAX}]")
                    
    except Exception as e:
        errors.append(f"Error reading HDF5 file: {str(e)}")
    
    if errors:
        for err in errors:
            log_validation_status(logger, "FAIL", err)
        return False
    
    log_validation_status(logger, "PASS", "All validation checks passed.")
    return True

def main():
    """Main entry point."""
    logger = setup_logging_custom()
    logger.info("="*50)
    logger.info("Starting ERA5 Sample Validation")
    logger.info("="*50)
    
    try:
        # 1. Fetch
        netcdf_path = fetch_era5_sample(logger)
        
        # 2. Convert
        convert_netcdf_to_hdf5(netcdf_path, OUTPUT_FILE, logger)
        
        # 3. Validate
        is_valid = validate_hdf5_sample(OUTPUT_FILE, logger)
        
        if is_valid:
            logger.info("Validation successful. File ready for use.")
            return 0
        else:
            logger.error("Validation failed. Check logs for details.")
            return 1
            
    except Exception as e:
        logger.error(f"Fatal error during execution: {str(e)}")
        log_validation_status(logger, "FAIL", f"Execution failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
