"""
T004: Validate ERA5 Sample Integrity.

Programmatically confirms that `data/raw/era5_sample.h5` meets:
1. Hourly temporal resolution.
2. Fixed grid size standards.
3. Physically plausible temperature range.

Logs Pass/Fail to `results/logs/data_validation_log.txt`.
"""
import os
import sys
import logging
from pathlib import Path
import h5py
import numpy as np

# Ensure we can import from the code directory if run from root
CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

LOG_FILE = Path("results/logs/data_validation_log.txt")
DATA_FILE = Path("data/raw/era5_sample.h5")

def ensure_directories():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def setup_custom_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(LOG_FILE)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def validate_temporal_resolution(logger, dataset):
    """
    Checks that the time dimension corresponds to hourly resolution.
    Assumes the dataset has a 'time' or 'timestamp' dimension/variable.
    """
    try:
        if 'time' in dataset:
            time_var = dataset['time']
            # Get time values
            time_vals = time_var[:]
            if len(time_vals) < 2:
                logger.error("Temporal validation failed: Less than 2 time points found.")
                return False

            # Calculate differences between consecutive time points
            # ERA5 usually stores time in hours since epoch or similar.
            # We check the difference in the raw unit first.
            diffs = np.diff(time_vals)
            
            # If the unit is hours (common for ERA5), diffs should be 1.0
            # If the unit is seconds, diffs should be 3600.0
            # We normalize by the median difference to check consistency
            median_diff = np.median(diffs)
            if median_diff == 0:
                logger.error("Temporal validation failed: Zero time difference detected.")
                return False
            
            # Check if all diffs are effectively equal to the median (within 1%)
            # This confirms fixed hourly steps regardless of the specific unit
            tolerance = 0.01 * median_diff
            is_consistent = np.allclose(diffs, median_diff, atol=tolerance)
            
            if not is_consistent:
                logger.error(f"Temporal validation failed: Time steps are inconsistent. Diffs: {diffs[:5]}...")
                return False

            # Check if the step size corresponds to an hour (either 1.0 or 3600.0)
            # ERA5 CDS API typically returns time in hours since 1900-01-01 or similar.
            # We check if the median diff is close to 1 (hour) or 3600 (seconds)
            is_hourly = (np.isclose(median_diff, 1.0, atol=0.1) or np.isclose(median_diff, 3600.0, atol=36.0))
            
            if not is_hourly:
                logger.warning(f"Temporal validation warning: Time step is {median_diff}, expected 1.0 (hours) or 3600.0 (seconds).")
                # We might still pass if the data is consistent, but log a warning
                # However, strict requirement says "hourly temporal resolution".
                # If it's not 1 or 3600, we fail.
                logger.error("Temporal validation failed: Time step does not correspond to 1 hour.")
                return False

            logger.info(f"Temporal validation passed: {len(time_vals)} points, step size {median_diff}.")
            return True
        else:
            logger.error("Temporal validation failed: 'time' variable not found in HDF5 dataset.")
            return False
    except Exception as e:
        logger.error(f"Temporal validation failed with exception: {e}")
        return False

def validate_grid_size(logger, dataset):
    """
    Checks that the spatial dimensions (lat/lon) are consistent and fixed.
    """
    try:
        # ERA5 usually has 'latitude' and 'longitude' or 'lat' and 'lon'
        lat_var = None
        lon_var = None

        if 'latitude' in dataset:
            lat_var = dataset['latitude']
        elif 'lat' in dataset:
            lat_var = dataset['lat']
        
        if 'longitude' in dataset:
            lon_var = dataset['longitude']
        elif 'lon' in dataset:
            lon_var = dataset['lon']

        if lat_var is None or lon_var is None:
            logger.error("Grid validation failed: Missing latitude or longitude variables.")
            return False

        lat_vals = lat_var[:]
        lon_vals = lon_var[:]

        # Check for fixed grid: no NaNs, consistent shape
        if np.any(np.isnan(lat_vals)) or np.any(np.isnan(lon_vals)):
            logger.error("Grid validation failed: NaN values found in coordinate arrays.")
            return False

        # Check resolution consistency (e.g., 0.25 degrees)
        # We check the difference between consecutive sorted values
        lat_sorted = np.sort(lat_vals)
        lon_sorted = np.sort(lon_vals)

        lat_diffs = np.diff(lat_sorted)
        lon_diffs = np.diff(lon_sorted)

        # Check if diffs are constant (fixed grid)
        if not np.allclose(lat_diffs, lat_diffs[0], atol=1e-4) or not np.allclose(lon_diffs, lon_diffs[0], atol=1e-4):
            logger.error("Grid validation failed: Spatial grid is not uniform.")
            return False

        # Log the resolution
        logger.info(f"Grid validation passed: Lat resolution {lat_diffs[0]:.4f}, Lon resolution {lon_diffs[0]:.4f}.")
        return True

    except Exception as e:
        logger.error(f"Grid validation failed with exception: {e}")
        return False

def validate_temperature_range(logger, dataset):
    """
    Validates that temperature values are within physically plausible range (-90C to +60C).
    """
    try:
        temp_var = None
        # Common names
        for key in ['temperature', 't2m', '2m_temperature', 'temp']:
            if key in dataset:
                temp_var = dataset[key]
                break
        
        if temp_var is None:
            logger.error("Temperature validation failed: Temperature variable not found.")
            return False

        temp_vals = temp_var[:]
        
        # Flatten to check all values
        temp_flat = temp_vals.flatten()
        
        min_val = np.nanmin(temp_flat)
        max_val = np.nanmax(temp_flat)

        # Plausible range for Earth surface air temperature
        if min_val < -90.0 or max_val > 60.0:
            logger.error(f"Temperature validation failed: Values out of plausible range. Min: {min_val}, Max: {max_val}")
            return False

        logger.info(f"Temperature validation passed: Range [{min_val:.2f}, {max_val:.2f}] °C.")
        return True

    except Exception as e:
        logger.error(f"Temperature validation failed with exception: {e}")
        return False

def main():
    ensure_directories()
    logger = setup_custom_logger("T004_Validation")
    
    if not DATA_FILE.exists():
        logger.error(f"Data file not found: {DATA_FILE}")
        logger.info("Status: FAIL - File missing")
        return 1

    try:
        with h5py.File(DATA_FILE, 'r') as hf:
            logger.info(f"Validating file: {DATA_FILE}")
            
            res_ok = validate_temporal_resolution(logger, hf)
            grid_ok = validate_grid_size(logger, hf)
            temp_ok = validate_temperature_range(logger, hf)

            if res_ok and grid_ok and temp_ok:
                logger.info("Status: PASS - All validations successful.")
                return 0
            else:
                logger.info("Status: FAIL - One or more validations failed.")
                return 1
    except Exception as e:
        logger.error(f"Critical error during validation: {e}")
        logger.info("Status: FAIL - Exception")
        return 1

if __name__ == "__main__":
    sys.exit(main())
