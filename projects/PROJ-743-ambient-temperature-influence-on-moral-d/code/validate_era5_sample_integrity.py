import os
import sys
import logging
from pathlib import Path
import h5py
import numpy as np

# Import configuration for thresholds
from config import get_path_env_override

# Constants for validation
EXPECTED_HOURLY_RES_SECONDS = 3600
MIN_TEMP_C = -50.0
MAX_TEMP_C = 60.0
VALIDATION_LOG_PATH = "results/logs/data_validation_log.txt"
SAMPLE_FILE_PATH = "data/raw/era5_sample.h5"

def ensure_directories():
    """Ensure the results/logs directory exists."""
    log_dir = Path(VALIDATION_LOG_PATH).parent
    log_dir.mkdir(parents=True, exist_ok=True)

def setup_custom_logger(name):
    """Setup a custom logger that writes to the specific log file."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    fh = logging.FileHandler(VALIDATION_LOG_PATH, mode='a')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger

def validate_temporal_resolution(logger, file_path):
    """
    Validate that the HDF5 file has hourly temporal resolution.
    Returns (is_valid, message).
    """
    try:
        with h5py.File(file_path, 'r') as f:
            # Look for a time dimension or dataset
            time_key = None
            for key in f.keys():
                if 'time' in key.lower():
                    time_key = key
                    break
            
            if time_key is None:
                # Fallback: check for 'date' or 'valid_time'
                for key in f.keys():
                    if 'date' in key.lower() or 'valid' in key.lower():
                        time_key = key
                        break

            if time_key is None:
                return False, "No time dimension or dataset found in HDF5 file."

            time_data = f[time_key][:]
            
            # Calculate differences between consecutive time points
            if len(time_data) < 2:
                return False, "Insufficient time points to calculate resolution."

            # Assuming time is in seconds since epoch or similar linear scale
            # Convert to numpy array if not already
            time_array = np.array(time_data, dtype=float)
            diffs = np.diff(time_array)

            # Check if differences are approximately 3600 seconds (1 hour)
            # Allow a small tolerance for floating point or metadata adjustments
            avg_diff = np.mean(diffs)
            tolerance = 60.0 # 1 minute tolerance

            if abs(avg_diff - EXPECTED_HOURLY_RES_SECONDS) <= tolerance:
                return True, f"Temporal resolution validated: {avg_diff:.2f} seconds (expected ~3600s)."
            else:
                return False, f"Temporal resolution mismatch: {avg_diff:.2f} seconds found, expected ~3600s."

    except Exception as e:
        return False, f"Error reading time data: {str(e)}"

def validate_grid_size(logger, file_path):
    """
    Validate that the grid size is consistent and non-empty.
    Returns (is_valid, message).
    """
    try:
        with h5py.File(file_path, 'r') as f:
            # Look for spatial dimensions (lat, lon, grid, etc.)
            spatial_keys = []
            for key in f.keys():
                if 'lat' in key.lower() or 'lon' in key.lower() or 'grid' in key.lower():
                    spatial_keys.append(key)

            if not spatial_keys:
                return False, "No spatial dimensions (lat/lon) found in HDF5 file."

            # Check at least one spatial dimension has data
            valid_spatial = False
            for key in spatial_keys:
                if f[key].shape[0] > 0:
                    valid_spatial = True
                    break
            
            if not valid_spatial:
                return False, "Spatial dimensions are empty."

            return True, f"Spatial dimensions validated: Found keys {spatial_keys}."

    except Exception as e:
        return False, f"Error reading spatial data: {str(e)}"

def validate_temperature_range(logger, file_path):
    """
    Validate that temperature values are within physically plausible range.
    Returns (is_valid, message).
    """
    try:
        with h5py.File(file_path, 'r') as f:
            # Look for temperature data
            temp_key = None
            for key in f.keys():
                if 'temp' in key.lower() or 't2m' in key.lower() or 'temperature' in key.lower():
                    temp_key = key
                    break
            
            if temp_key is None:
                # Try to find any floating point dataset that might be temperature
                for key in f.keys():
                    if isinstance(f[key], h5py.Dataset) and f[key].dtype in [np.float32, np.float64]:
                        temp_key = key
                        break

            if temp_key is None:
                return False, "No temperature data found in HDF5 file."

            temp_data = f[temp_key][:]
            min_val = np.min(temp_data)
            max_val = np.max(temp_data)

            if min_val < MIN_TEMP_C or max_val > MAX_TEMP_C:
                return False, f"Temperature out of range: min={min_val:.2f}C, max={max_val:.2f}C (allowed: {MIN_TEMP_C}C to {MAX_TEMP_C}C)."
            
            return True, f"Temperature range validated: min={min_val:.2f}C, max={max_val:.2f}C."

    except Exception as e:
        return False, f"Error reading temperature data: {str(e)}"

def main():
    """Main execution function for T004."""
    ensure_directories()
    logger = setup_custom_logger("T004_ValidateERA5SampleIntegrity")
    
    logger.info("Starting ERA5 Sample Integrity Validation (T004).")
    
    if not os.path.exists(SAMPLE_FILE_PATH):
        error_msg = f"CRITICAL: Sample file not found at {SAMPLE_FILE_PATH}. Cannot validate."
        logger.error(error_msg)
        # Do not create a log entry saying PASS, just fail loudly
        sys.exit(1)

    all_passed = True

    # 1. Validate Temporal Resolution
    is_valid, msg = validate_temporal_resolution(logger, SAMPLE_FILE_PATH)
    logger.info(f"Temporal Resolution Check: {'PASS' if is_valid else 'FAIL'} - {msg}")
    if not is_valid:
        all_passed = False

    # 2. Validate Grid Size
    is_valid, msg = validate_grid_size(logger, SAMPLE_FILE_PATH)
    logger.info(f"Grid Size Check: {'PASS' if is_valid else 'FAIL'} - {msg}")
    if not is_valid:
        all_passed = False

    # 3. Validate Temperature Range
    is_valid, msg = validate_temperature_range(logger, SAMPLE_FILE_PATH)
    logger.info(f"Temperature Range Check: {'PASS' if is_valid else 'FAIL'} - {msg}")
    if not is_valid:
        all_passed = False

    # Final Result
    if all_passed:
        logger.info("ERA5 Sample Validation: PASS")
        # Ensure the specific string required by the gate is logged
        with open(VALIDATION_LOG_PATH, 'a') as f:
            f.write("ERA5 Validation: PASS\n")
    else:
        logger.error("ERA5 Sample Validation: FAIL")
        with open(VALIDATION_LOG_PATH, 'a') as f:
            f.write("ERA5 Validation: FAIL\n")
        sys.exit(1)

    logger.info("T004 Validation Complete.")

if __name__ == "__main__":
    main()
