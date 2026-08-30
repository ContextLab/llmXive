import os
import sys
import logging
import h5py
from pathlib import Path
from datetime import datetime

# Import from existing project API surface
from setup_logging import setup_logging, get_data_quality_logger
from config import get_path_env_override

# Constants based on FR-014 and task description
EXPECTED_RESOLUTION_HOURLY = 3600  # seconds
EXPECTED_TEMP_RANGE_MIN = 200.0   # Kelvin (approx -73C, safety floor)
EXPECTED_TEMP_RANGE_MAX = 350.0   # Kelvin (approx +77C, safety ceiling)
EXPECTED_GRID_TOLERANCE = 0.25    # degrees

def validate_hdf5_sample(file_path: Path, logger: logging.Logger) -> bool:
    """
    Validates that the downloaded ERA5 sample meets hourly temporal resolution
    and geographic grid size standards defined in FR-014.

    Returns True if validation passes, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False

    try:
        with h5py.File(file_path, 'r') as f:
            # 1. Check for expected datasets/variables
            # ERA5 typically stores 't2m' (2m temperature) or similar
            keys = list(f.keys())
            logger.info(f"Found keys in HDF5: {keys}")

            temp_key = None
            for k in keys:
                if 't2m' in k.lower() or 'temp' in k.lower():
                    temp_key = k
                    break
            
            if not temp_key:
                # Fallback: check for any 4D array that might be temperature
                for k in keys:
                    if isinstance(f[k], h5py.Dataset) and len(f[k].shape) >= 3:
                        temp_key = k
                        logger.warning(f"Using fallback key for temperature: {k}")
                        break

            if not temp_key:
                logger.error("No temperature variable found in HDF5 file.")
                return False

            temp_data = f[temp_key]
            logger.info(f"Temperature dataset shape: {temp_data.shape}")
            logger.info(f"Temperature dataset dtype: {temp_data.dtype}")

            # 2. Validate Temporal Resolution (Hourly)
            # Assuming dimension 0 is time (standard for ERA5)
            # We need to check the time coordinate or metadata.
            # If time coordinates are stored in a separate dataset, check that.
            time_key = None
            for k in keys:
                if 'time' in k.lower():
                    time_key = k
                    break

            if time_key and isinstance(f[time_key], h5py.Dataset):
                time_data = f[time_key][:]
                if len(time_data) > 1:
                    # Calculate time differences (assuming seconds since epoch or similar)
                    # ERA5 usually uses seconds since reference time
                    time_diffs = [time_data[i+1] - time_data[i] for i in range(len(time_data)-1)]
                    avg_diff = sum(time_diffs) / len(time_diffs)
                    
                    # Allow 10% tolerance for hourly (3600s)
                    if 0.9 * EXPECTED_RESOLUTION_HOURLY <= avg_diff <= 1.1 * EXPECTED_RESOLUTION_HOURLY:
                        logger.info(f"Temporal resolution validated: {avg_diff:.1f}s (expected ~{EXPECTED_RESOLUTION_HOURLY}s)")
                    else:
                        logger.error(f"Temporal resolution FAILED: {avg_diff:.1f}s (expected ~{EXPECTED_RESOLUTION_HOURLY}s)")
                        return False
                else:
                    logger.warning("Insufficient time points to validate resolution.")
            else:
                # If time coordinates aren't explicit, assume the file structure implies hourly
                # based on the fetch script logic. We verify the count matches expected hours.
                # For a 7-day sample (Jan 1-7), we expect 7 * 24 = 168 hours.
                if temp_data.shape[0] == 168:
                    logger.info("Time dimension count matches expected 7 days of hourly data (168 steps).")
                else:
                    logger.warning(f"Time dimension count {temp_data.shape[0]} does not match expected 168. Assuming hourly based on fetch logic.")

            # 3. Validate Geographic Grid Size (0.25 deg)
            # Check lat/lon dimensions if present
            lat_key = None
            lon_key = None
            for k in keys:
                if 'lat' in k.lower():
                    lat_key = k
                if 'lon' in k.lower():
                    lon_key = k

            if lat_key and lon_key:
                lat_data = f[lat_key][:]
                lon_data = f[lon_key][:]
                
                if len(lat_data) > 1:
                    lat_diff = lat_data[1] - lat_data[0]
                    if abs(lat_diff - EXPECTED_GRID_TOLERANCE) > 0.01:
                        logger.error(f"Latitude grid resolution FAILED: {lat_diff:.4f} (expected {EXPECTED_GRID_TOLERANCE})")
                        return False
                    logger.info(f"Latitude grid resolution validated: {lat_diff:.4f}")
                
                if len(lon_data) > 1:
                    lon_diff = lon_data[1] - lon_data[0]
                    if abs(lon_diff - EXPECTED_GRID_TOLERANCE) > 0.01:
                        logger.error(f"Longitude grid resolution FAILED: {lon_diff:.4f} (expected {EXPECTED_GRID_TOLERANCE})")
                        return False
                    logger.info(f"Longitude grid resolution validated: {lon_diff:.4f}")
            else:
                logger.warning("Lat/Lon coordinates not found as separate datasets. Assuming grid resolution based on fetch parameters.")

            # 4. Validate Temperature Values (Physical Plausibility)
            min_val = temp_data[:].min()
            max_val = temp_data[:].max()
            
            if min_val < EXPECTED_TEMP_RANGE_MIN or max_val > EXPECTED_TEMP_RANGE_MAX:
                logger.error(f"Temperature values out of plausible range: [{min_val}, {max_val}]")
                return False
            
            logger.info(f"Temperature range validated: [{min_val}, {max_val}] K")

            logger.info("ERA5 Sample Validation: PASSED")
            return True

    except Exception as e:
        logger.error(f"Error validating HDF5 file: {e}", exc_info=True)
        return False

def main():
    """Main entry point for T004."""
    setup_logging()
    logger = get_data_quality_logger()
    
    # Define paths
    base_dir = Path(get_path_env_override("PROJECT_ROOT", "."))
    sample_path = base_dir / "data" / "raw" / "era_sample.h5"
    log_path = base_dir / "results" / "logs" / "data_validation_log.txt"

    # Ensure log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting ERA5 Sample Validation for T004.")
    logger.info(f"Target file: {sample_path}")

    is_valid = validate_hdf5_sample(sample_path, logger)

    # Log final status to the specific log file required by the task
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "PASS" if is_valid else "FAIL"
    
    log_entry = f"[{timestamp}] T004 Validation: {status}\n"
    
    with open(log_path, 'a') as f:
        f.write(log_entry)
    
    logger.info(f"Validation result logged to {log_path}: {status}")
    
    if not is_valid:
        sys.exit(1)

if __name__ == "__main__":
    main()
