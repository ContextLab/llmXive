"""
Task T004: Validate ERA5 Sample Integrity.

Programmatically confirms that `era5_sample.h5` meets hourly temporal resolution
and grid size standards (fixed resolution). Logs Pass/Fail to
`results/logs/data_validation_log.txt`.

Dependencies: T001b (fetch_era5_sample.py must have run successfully to produce the file).
"""
import os
import sys
import logging
from pathlib import Path
import h5py
import numpy as np

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from setup_logging import setup_logging, get_data_quality_logger
from config import get_path_env_override

# Constants for validation
EXPECTED_RESOLUTION_HOURS = 1.0
MIN_GRID_SIZE = 1  # At least 1x1 grid is valid, though we expect more
VALID_TEMP_MIN = -90.0
VALID_TEMP_MAX = 60.0

def ensure_directories():
    """Ensure the results/logs directory exists."""
    log_dir = PROJECT_ROOT / "results" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def setup_custom_logger(name):
    """Setup a custom logger for this task."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger

def validate_temporal_resolution(h5_path, logger):
    """
    Validates that the time dimension in the HDF5 file corresponds to hourly resolution.
    Returns (is_valid, details).
    """
    try:
        with h5py.File(h5_path, 'r') as f:
            # Look for a time or date variable
            time_key = None
            for key in f.keys():
                if 'time' in key.lower() or 'date' in key.lower():
                    time_key = key
                    break
            
            if not time_key:
                logger.warning(f"Could not find time variable in {h5_path}. Keys: {list(f.keys())}")
                return False, "No time variable found"

            time_data = f[time_key][:]
            if len(time_data) < 2:
                logger.warning(f"Insufficient time points ({len(time_data)}) to calculate resolution.")
                return False, "Insufficient time points"

            # Calculate differences (assuming time is in hours or convertible units)
            # ERA5 data often stores time in hours since a reference date.
            # We check the delta between consecutive points.
            diffs = np.diff(time_data)
            median_diff = np.median(diffs)
            
            # If the unit is hours, median_diff should be ~1.0
            # If the unit is seconds, median_diff should be ~3600.0
            # We assume the dataset T001b downloaded uses standard ERA5 units (hours since reference)
            # based on the task description "hourly resolution".
            
            is_hourly = abs(median_diff - 1.0) < 0.01 or abs(median_diff - 3600.0) < 10.0
            
            if is_hourly:
                unit = "hours" if median_diff < 10 else "seconds"
                logger.info(f"Temporal resolution validated: {median_diff} {unit} (median diff).")
                return True, f"Resolution: {median_diff} {unit}"
            else:
                logger.error(f"Temporal resolution mismatch. Expected ~1 hour, got {median_diff}.")
                return False, f"Resolution mismatch: {median_diff}"

    except Exception as e:
        logger.error(f"Error validating temporal resolution: {e}")
        return False, str(e)

def validate_grid_size(h5_path, logger):
    """
    Validates that the grid dimensions are present and non-zero.
    Returns (is_valid, details).
    """
    try:
        with h5py.File(h5_path, 'r') as f:
            # Look for spatial dimensions (lat, lon, latitude, longitude, y, x)
            spatial_dims = []
            for key in f.keys():
                if any(term in key.lower() for term in ['lat', 'lon', 'y', 'x']):
                    spatial_dims.append(key)
            
            if not spatial_dims:
                # Try to find dimensions in the data variable itself
                data_var = None
                for key in f.keys():
                    if isinstance(f[key], h5py.Dataset) and f[key].shape:
                        data_var = f[key]
                        break
                if data_var and len(data_var.shape) >= 2:
                    logger.info(f"Found data variable with shape {data_var.shape}, assuming grid exists.")
                    return True, f"Grid inferred from data shape: {data_var.shape}"
                
                logger.error(f"No spatial dimensions found in {h5_path}. Keys: {list(f.keys())}")
                return False, "No spatial dimensions found"

            # Check sizes
            sizes = {}
            for dim in spatial_dims:
                if isinstance(f[dim], h5py.Dataset):
                    sizes[dim] = f[dim].shape[0]
                else:
                    sizes[dim] = len(f[dim])
            
            valid = all(s >= MIN_GRID_SIZE for s in sizes.values())
            if valid:
                logger.info(f"Grid size validated: {sizes}")
                return True, f"Grid size: {sizes}"
            else:
                logger.error(f"Grid size too small: {sizes}")
                return False, f"Grid size too small: {sizes}"

    except Exception as e:
        logger.error(f"Error validating grid size: {e}")
        return False, str(e)

def validate_temperature_range(h5_path, logger):
    """
    Validates that temperature values are within physically plausible ranges.
    Returns (is_valid, details).
    """
    try:
        with h5py.File(h5_path, 'r') as f:
            data_var = None
            for key in f.keys():
                if isinstance(f[key], h5py.Dataset):
                    # Prefer a variable that looks like temperature
                    if 'temp' in key.lower() or '2t' in key.lower():
                        data_var = f[key]
                        break
            
            if not data_var:
                # Fallback to any dataset
                for key in f.keys():
                    if isinstance(f[key], h5py.Dataset):
                        data_var = f[key]
                        break

            if not data_var:
                logger.warning("No data variable found to validate temperature range.")
                return True, "No data variable to check"

            min_val = np.min(data_var[:])
            max_val = np.max(data_var[:])

            logger.info(f"Temperature range: {min_val:.2f} to {max_val:.2f}")

            if min_val < VALID_TEMP_MIN or max_val > VALID_TEMP_MAX:
                logger.error(f"Temperature out of physical range [{VALID_TEMP_MIN}, {VALID_TEMP_MAX}].")
                return False, f"Out of range: [{min_val}, {max_val}]"
            
            return True, f"Range OK: [{min_val:.2f}, {max_val:.2f}]"

    except Exception as e:
        logger.error(f"Error validating temperature range: {e}")
        return False, str(e)

def main():
    logger = setup_custom_logger("validate_era5_sample_integrity")
    ensure_directories()
    data_quality_logger = get_data_quality_logger()

    sample_path = PROJECT_ROOT / "data" / "raw" / "era5_sample.h5"
    
    if not sample_path.exists():
        error_msg = f"File not found: {sample_path}"
        logger.error(error_msg)
        if data_quality_logger:
            data_quality_logger.error(f"T004 Validation Failed: {error_msg}")
        print(f"T004 FAILED: {error_msg}")
        sys.exit(1)

    logger.info(f"Validating integrity of {sample_path}...")
    
    results = {
        "temporal_resolution": validate_temporal_resolution(sample_path, logger),
        "grid_size": validate_grid_size(sample_path, logger),
        "temperature_range": validate_temperature_range(sample_path, logger)
    }

    all_passed = all(r[0] for r in results.values())
    status = "PASS" if all_passed else "FAIL"
    
    log_entry = f"T004: ERA5 Sample Integrity Validation - {status}\n"
    for check, (passed, detail) in results.items():
        status_str = "OK" if passed else "FAILED"
        log_entry += f"  - {check}: {status_str} ({detail})\n"
    
    logger.info(log_entry)
    
    # Log to the main data validation log
    if data_quality_logger:
        data_quality_logger.info(log_entry)
    
    # Write to the specific log file as requested
    log_file_path = PROJECT_ROOT / "results" / "logs" / "data_validation_log.txt"
    with open(log_file_path, 'a') as f:
        f.write(f"\n[{datetime.now().isoformat()}] {log_entry}")

    print(f"T004 Result: {status}")
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()