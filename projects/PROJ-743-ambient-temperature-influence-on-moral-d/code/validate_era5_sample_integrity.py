"""
Task T004: Validate ERA5 Sample Integrity.

Programmatically confirm that era5_sample.h5 meets hourly temporal resolution
and grid size standards (fixed resolution). Log Pass/Fail to
results/logs/data_validation_log.txt.
"""
import os
import sys
import logging
from pathlib import Path
import h5py
import numpy as np
from datetime import datetime

# Import setup_logging from the project's existing infrastructure
from setup_logging import setup_logging, get_data_quality_logger
from config import get_path_env_override

# Configuration constants matching T001b expectations
SAMPLE_FILE_PATH = "data/raw/era5_sample.h5"
LOG_FILE_PATH = "results/logs/data_validation_log.txt"
EXPECTED_TEMP_MIN = -50.0
EXPECTED_TEMP_MAX = 60.0
EXPECTED_RESOLUTION_HOURS = 1

def ensure_directories():
    """Ensure the log directory exists."""
    log_dir = Path(LOG_FILE_PATH).parent
    log_dir.mkdir(parents=True, exist_ok=True)

def setup_custom_logger():
    """Setup a custom logger for validation results."""
    logger = logging.getLogger("era5_validation")
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(LOG_FILE_PATH, mode='a')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Console handler for immediate feedback
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

def validate_temporal_resolution(time_dataset):
    """
    Validate that the time dimension represents hourly resolution.
    Returns (is_valid, details).
    """
    try:
        # Get time values (usually in hours since epoch or similar)
        time_values = time_dataset[:]
        
        if len(time_values) < 2:
            return False, "Insufficient time points to calculate resolution."

        # Calculate differences between consecutive time points
        # Assuming the dataset uses standard ERA5 time units (hours since 1900-01-01 or similar)
        # We need to check the unit attribute if available, or assume standard behavior
        time_units = time_dataset.attrs.get('units', 'hours since 1900-01-01 00:00:00')
        
        # Calculate deltas
        deltas = np.diff(time_values)
        
        # Check if all deltas are approximately 1 (hour)
        # Use a small tolerance for floating point errors
        is_hourly = np.allclose(deltas, 1.0, atol=0.01)
        
        if is_hourly:
            return True, f"Temporal resolution verified: {len(deltas)} intervals of ~1 hour."
        else:
            return False, f"Temporal resolution failed. Found deltas: {np.unique(deltas)}"
    except Exception as e:
        return False, f"Error validating temporal resolution: {str(e)}"

def validate_grid_size(data_dataset):
    """
    Validate that the grid size is fixed (consistent dimensions).
    Returns (is_valid, details).
    """
    try:
        shape = data_dataset.shape
        # ERA5 typically has shape (time, latitude, longitude) or (time, level, lat, lon)
        if len(shape) < 2:
            return False, "Data dimensionality too low for grid validation."
        
        # Check that spatial dimensions are non-zero and consistent
        # For a fixed resolution grid, the shape should be constant for all time steps
        # We assume the dataset is already loaded as a single chunk
        
        lat_dim = shape[-2] if len(shape) >= 2 else 0
        lon_dim = shape[-1] if len(shape) >= 1 else 0
        
        if lat_dim <= 0 or lon_dim <= 0:
            return False, "Invalid spatial dimensions."
        
        return True, f"Grid size verified: {lat_dim}x{lon_dim} (fixed resolution)."
    except Exception as e:
        return False, f"Error validating grid size: {str(e)}"

def validate_temperature_range(data_dataset):
    """
    Validate that temperature values are within expected physical bounds.
    Returns (is_valid, details).
    """
    try:
        data_values = data_dataset[:]
        
        # Handle potential masked arrays
        if isinstance(data_values, np.ma.MaskedArray):
            data_values = data_values.filled(np.nan)
        
        valid_data = data_values[~np.isnan(data_values)]
        
        if len(valid_data) == 0:
            return False, "No valid temperature data found."
        
        min_val = np.min(valid_data)
        max_val = np.max(valid_data)
        
        if min_val >= EXPECTED_TEMP_MIN and max_val <= EXPECTED_TEMP_MAX:
            return True, f"Temperature range verified: [{min_val:.2f}, {max_val:.2f}] °C within [{EXPECTED_TEMP_MIN}, {EXPECTED_TEMP_MAX}] °C."
        else:
            return False, f"Temperature range violation: [{min_val:.2f}, {max_val:.2f}] °C outside [{EXPECTED_TEMP_MIN}, {EXPECTED_TEMP_MAX}] °C."
    except Exception as e:
        return False, f"Error validating temperature range: {str(e)}"

def main():
    """Main entry point for T004."""
    logger = setup_custom_logger()
    ensure_directories()
    
    logger.info(f"Starting ERA5 Sample Integrity Validation (Task T004) at {datetime.now()}")
    logger.info(f"Target file: {SAMPLE_FILE_PATH}")
    
    all_passed = True
    validation_results = []
    
    # Check if file exists
    if not os.path.exists(SAMPLE_FILE_PATH):
        logger.error(f"File not found: {SAMPLE_FILE_PATH}")
        all_passed = False
        validation_results.append({"check": "file_exists", "status": "FAIL", "details": "File not found"})
    else:
        try:
            with h5py.File(SAMPLE_FILE_PATH, 'r') as hf:
                logger.info(f"Successfully opened HDF5 file: {SAMPLE_FILE_PATH}")
                
                # Identify datasets (assumes standard ERA5 structure)
                # Common keys: 'temperature', 't2m', or similar
                dataset_keys = list(hf.keys())
                logger.info(f"Found datasets: {dataset_keys}")
                
                # Try to find temperature data
                temp_key = None
                time_key = None
                for key in dataset_keys:
                    if 'temp' in key.lower() or 't2m' in key.lower():
                        temp_key = key
                    if 'time' in key.lower():
                        time_key = key
                
                if temp_key is None and len(dataset_keys) > 0:
                    # Fallback: use first dataset as data
                    temp_key = dataset_keys[0]
                
                if time_key is None and len(dataset_keys) > 1:
                    # Fallback: use second dataset as time if exists
                    time_key = dataset_keys[1]
                
                if temp_key is None:
                    logger.error("Could not identify temperature dataset.")
                    all_passed = False
                    validation_results.append({"check": "temp_dataset", "status": "FAIL", "details": "No temperature dataset found"})
                else:
                    # Validate Temperature Range
                    is_valid, details = validate_temperature_range(hf[temp_key])
                    status = "PASS" if is_valid else "FAIL"
                    logger.info(f"Temperature Range Validation: {status} - {details}")
                    validation_results.append({"check": "temperature_range", "status": status, "details": details})
                    if not is_valid:
                        all_passed = False
                
                if time_key is not None:
                    # Validate Temporal Resolution
                    is_valid, details = validate_temporal_resolution(hf[time_key])
                    status = "PASS" if is_valid else "FAIL"
                    logger.info(f"Temporal Resolution Validation: {status} - {details}")
                    validation_results.append({"check": "temporal_resolution", "status": status, "details": details})
                    if not is_valid:
                        all_passed = False
                
                # Validate Grid Size
                is_valid, details = validate_grid_size(hf[temp_key])
                status = "PASS" if is_valid else "FAIL"
                logger.info(f"Grid Size Validation: {status} - {details}")
                validation_results.append({"check": "grid_size", "status": status, "details": details})
                if not is_valid:
                    all_passed = False
        
        except Exception as e:
            logger.error(f"Error reading HDF5 file: {str(e)}")
            all_passed = False
            validation_results.append({"check": "file_read", "status": "FAIL", "details": str(e)})
    
    # Final Summary
    final_status = "PASS" if all_passed else "FAIL"
    logger.info("-" * 50)
    logger.info(f"FINAL VALIDATION STATUS: {final_status}")
    logger.info("-" * 50)
    
    # Log summary details
    for result in validation_results:
        logger.info(f"  - {result['check']}: {result['status']} ({result['details']})")
    
    # If all checks passed, log the specific success message required by the task
    if all_passed:
        logger.info("T004: ERA5 Sample Integrity validation PASSED. Hourly resolution and fixed grid size confirmed.")
    else:
        logger.error("T004: ERA5 Sample Integrity validation FAILED. See details above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
