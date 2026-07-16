"""
Validate the downloaded ERA5 sample file against FR-014 standards:
- Temporal resolution: Hourly (1 data point per hour)
- Geographic grid size: Consistent with ERA5 standard (approx 0.25 degree)

Logs validation status to results/logs/data_validation_log.txt.
"""
import os
import sys
import logging
import h5py
from pathlib import Path
from datetime import datetime

# Add project root to path for imports if necessary, though this script is standalone logic
project_root = Path(__file__).resolve().parent.parent
data_dir = project_root / "data" / "raw"
log_dir = project_root / "results" / "logs"

# Ensure log directory exists
log_dir.mkdir(parents=True, exist_ok=True)

# Setup logging to file
log_file = log_dir / "data_validation_log.txt"

# Configure logger
logger = logging.getLogger("era5_validation")
logger.setLevel(logging.INFO)

# Clear existing handlers to avoid duplicates if imported multiple times
if logger.hasHandlers():
    logger.handlers.clear()

# File handler
fh = logging.FileHandler(log_file)
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# Console handler for immediate feedback
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

FR_014_TEMPORAL_RESOLUTION_HOURS = 1
FR_014_GRID_SIZE_DEG = 0.25  # Standard ERA5 grid
TOLERANCE_GRID = 0.01        # Tolerance for grid size verification

def validate_era5_sample(file_path):
    """
    Validates the ERA5 sample file against FR-014 standards.
    Returns True if valid, False otherwise.
    """
    logger.info(f"Starting validation for: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False

    try:
        with h5py.File(file_path, 'r') as f:
            # Check for expected groups/datasets
            # ERA5 data in H5 usually has structure like:
            # /data/ (containing temperature, time, latitude, longitude)
            # or specific variable keys.
            
            keys = list(f.keys())
            logger.info(f"File keys found: {keys}")

            # Attempt to locate time, lat, lon, and temperature data
            # Heuristic: look for common keys or iterate
            time_key = None
            lat_key = None
            lon_key = None
            temp_key = None

            # Common naming conventions in CDS H5 exports
            candidate_time = ['time', 'valid_time', 'step', 'datetime']
            candidate_lat = ['latitude', 'lat', 'grib_latitude']
            candidate_lon = ['longitude', 'lon', 'grib_longitude']
            candidate_temp = ['temperature_2m', 't2m', 'temperature']

            def find_key(keys, candidates):
                for c in candidates:
                    for k in keys:
                        if c.lower() in k.lower():
                            return k
                return None

            # Check root level first
            time_key = find_key(keys, candidate_time)
            lat_key = find_key(keys, candidate_lat)
            lon_key = find_key(keys, candidate_lon)
            temp_key = find_key(keys, candidate_temp)

            # If not found at root, check inside 'data' or similar groups
            if not time_key and 'data' in keys:
                data_keys = list(f['data'].keys())
                time_key = find_key(data_keys, candidate_time)
                lat_key = find_key(data_keys, candidate_lat)
                lon_key = find_key(data_keys, candidate_lon)
                temp_key = find_key(data_keys, candidate_temp)
            
            # Fallback: try to find any time-like array if keys are ambiguous
            if not time_key:
                for k in keys:
                    if 'time' in k.lower():
                        time_key = k
                        break

            if not all([time_key, lat_key, lon_key]):
                logger.error(f"Could not locate required dimensions. Found keys: {keys}")
                return False

            # 1. Validate Temporal Resolution (Hourly)
            # We expect the time dimension to have steps of 1 hour.
            # In CDS H5, time is often encoded as seconds since epoch or a specific reference.
            # We check the difference between consecutive time points.
            
            time_data = f[time_key][:]
            if len(time_data) < 2:
                logger.warning("Insufficient time points to calculate resolution.")
                # If sample is tiny, we might not be able to validate strictly, but assume pass if structure exists
                # However, FR-014 requires hourly. We must verify.
                logger.error("Validation Failed: Insufficient time points to verify hourly resolution.")
                return False

            # Calculate differences (assuming seconds or similar linear scale)
            # CDS often uses 'valid_time' in seconds since reference.
            # We check the median difference.
            diffs = []
            for i in range(1, len(time_data)):
                diffs.append(time_data[i] - time_data[i-1])
            
            if not diffs:
                logger.error("Could not compute time differences.")
                return False

            median_diff_seconds = float(np.median(diffs))
            expected_diff_seconds = FR_014_TEMPORAL_RESOLUTION_HOURS * 3600
            
            # Allow 10% tolerance for time step verification
            if abs(median_diff_seconds - expected_diff_seconds) > (expected_diff_seconds * 0.1):
                logger.error(f"Validation Failed: Temporal resolution is {median_diff_seconds/3600:.2f} hours, expected {FR_014_TEMPORAL_RESOLUTION_HOURS} hours.")
                return False
            
            logger.info(f"Temporal Resolution Check: PASS ({median_diff_seconds/3600:.2f} hours)")

            # 2. Validate Geographic Grid Size
            # ERA5 standard is 0.25 degrees. We check the spacing of lat/lon arrays.
            lat_data = f[lat_key][:]
            lon_data = f[lon_key][:]

            # Calculate median spacing
            lat_diffs = [lat_data[i+1] - lat_data[i] for i in range(len(lat_data)-1) if lat_data[i+1] > lat_data[i]]
            lon_diffs = [lon_data[i+1] - lon_data[i] for i in range(len(lon_data)-1) if lon_data[i+1] > lon_data[i]]

            if not lat_diffs or not lon_diffs:
                logger.warning("Could not compute grid spacing (singular or unsorted coordinates).")
                # If we can't compute, we assume the file structure is correct but log a warning
                # However, strict FR-014 validation might require a pass. 
                # Given the sample nature, if we can't verify, we fail loudly to be safe.
                logger.error("Validation Failed: Could not verify geographic grid size.")
                return False

            median_lat_spacing = float(np.median(lat_diffs))
            median_lon_spacing = float(np.median(lon_diffs))

            # Check against 0.25 tolerance
            if abs(median_lat_spacing - FR_014_GRID_SIZE_DEG) > TOLERANCE_GRID:
                logger.error(f"Validation Failed: Lat grid spacing is {median_lat_spacing}, expected {FR_014_GRID_SIZE_DEG}.")
                return False
            
            if abs(median_lon_spacing - FR_014_GRID_SIZE_DEG) > TOLERANCE_GRID:
                logger.error(f"Validation Failed: Lon grid spacing is {median_lon_spacing}, expected {FR_014_GRID_SIZE_DEG}.")
                return False

            logger.info(f"Geographic Grid Size Check: PASS (Lat: {median_lat_spacing:.3f}, Lon: {median_lon_spacing:.3f})")
            
            return True

    except Exception as e:
        logger.error(f"Validation Error: {str(e)}")
        return False

def main():
    sample_file = data_dir / "era5_sample.h5"
    
    logger.info("="*50)
    logger.info("Starting FR-014 Validation Task (T004)")
    logger.info("="*50)
    
    is_valid = validate_era5_sample(sample_file)
    
    if is_valid:
        logger.info("RESULT: PASS - Sample meets FR-014 standards.")
    else:
        logger.info("RESULT: FAIL - Sample does not meet FR-014 standards.")
    
    logger.info("="*50)
    return 0 if is_valid else 1

if __name__ == "__main__":
    # Import numpy locally to avoid dependency issues if not installed globally, 
    # though it's in requirements.
    import numpy as np
    sys.exit(main())
