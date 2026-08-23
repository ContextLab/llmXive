import os
import sys
import logging
import h5py
from pathlib import Path
from datetime import datetime

# Import logging setup from existing project module
from setup_logging import setup_logging, get_data_quality_logger

# Constants defined in FR-014 (derived from plan.md context)
# Temporal resolution: 1 hour
REQUIRED_TEMPORAL_RESOLUTION_HOURS = 1.0
# Grid size: 0.25 degrees
REQUIRED_GRID_SIZE_DEGREES = 0.25
# Plausible temperature range for 2m air temperature in Kelvin (approx -50C to +60C)
MIN_TEMP_K = 223.15
MAX_TEMP_K = 333.15

def validate_era5_sample(file_path: str) -> dict:
    """
    Validates the downloaded ERA5 sample file against FR-014 standards.
    
    Args:
        file_path: Path to the .h5 file (data/raw/era_sample.h5)
        
    Returns:
        dict: Validation results including status, resolution check, grid check, and temp validity.
    """
    result = {
        "file_path": file_path,
        "timestamp": datetime.now().isoformat(),
        "status": "FAIL",
        "temporal_resolution_ok": False,
        "grid_size_ok": False,
        "temperature_values_valid": False,
        "details": []
    }

    if not os.path.exists(file_path):
        result["details"].append(f"File not found: {file_path}")
        return result

    try:
        with h5py.File(file_path, 'r') as f:
            # Check for expected dataset structure
            # ERA5 data from CDS usually stores 't2m' (2m temperature)
            if 't2m' not in f:
                result["details"].append("Missing 't2m' dataset in HDF5 file.")
                return result
            
            t2m_dataset = f['t2m']
            
            # 1. Validate Temporal Resolution
            # Assuming time dimension is the first or a dedicated time group
            # We check the time coordinate if available, or infer from shape if time is implicit
            # Standard ERA5 HDF5 structure often has 'time' as a dimension or attribute
            time_dim = None
            if 'time' in f:
                time_dim = f['time']
            elif 'time' in t2m_dataset.attrs:
                # If time is an attribute (less common for time series)
                pass 
            
            # Heuristic: Check if we have a time dimension. 
            # In the sample fetch script (T001b), we requested Jan 1 to Jan 7 (7 days).
            # If hourly, we expect 7 * 24 = 168 time steps.
            # We verify the shape of the data to infer resolution if explicit time coords aren't in root.
            # Common structure: t2m(time, lat, lon) or similar.
            
            shape = t2m_dataset.shape
            ndim = len(shape)
            
            # Infer time dimension index (usually 0)
            if ndim >= 3:
                time_steps = shape[0]
                # Expected: 7 days * 24 hours = 168 steps
                # We verify if the count matches the expected duration for hourly data
                # Since we don't have the explicit time delta here without reading the time array,
                # we rely on the count matching the requested range (Jan 1-7 = 168 hours)
                # If the fetch script worked, shape[0] should be 168.
                if time_steps == 168:
                    result["temporal_resolution_ok"] = True
                    result["details"].append(f"Temporal resolution inferred as hourly (168 steps for 7-day range).")
                else:
                    result["details"].append(f"Unexpected time steps: {time_steps}. Expected 168 for hourly Jan 1-7.")
            else:
                result["details"].append(f"Insufficient dimensions in dataset: {shape}")
                return result

            # 2. Validate Geographic Grid Size
            # Check lat/lon dimensions. ERA5 0.25 deg grid.
            # If shape is (time, lat, lon), then shape[1] and shape[2] define the grid.
            if ndim >= 3:
                lat_size = shape[1]
                lon_size = shape[2]
                
                # Approximate check: For a global or large regional sample,
                # 0.25 deg resolution implies specific counts.
                # However, for a specific bounding box (London sample from T001b),
                # we check if the resolution *implies* the grid size.
                # A robust check is to verify the coordinate attributes if present.
                if 'lat' in f and 'lon' in f:
                    lat_coords = f['lat'][:]
                    lon_coords = f['lon'][:]
                    
                    if len(lat_coords) > 1 and len(lon_coords) > 1:
                        lat_step = lat_coords[1] - lat_coords[0]
                        lon_step = lon_coords[1] - lon_coords[0]
                        
                        if abs(lat_step - REQUIRED_GRID_SIZE_DEGREES) < 0.01:
                            result["grid_size_ok"] = True
                            result["details"].append(f"Latitude grid size verified: {lat_step} deg.")
                        else:
                            result["details"].append(f"Latitude grid size mismatch: {lat_step} deg (expected {REQUIRED_GRID_SIZE_DEGREES}).")
                        
                        if abs(lon_step - REQUIRED_GRID_SIZE_DEGREES) < 0.01:
                            result["grid_size_ok"] = True # Keep true if already true
                            result["details"].append(f"Longitude grid size verified: {lon_step} deg.")
                        else:
                            result["details"].append(f"Longitude grid size mismatch: {lon_step} deg (expected {REQUIRED_GRID_SIZE_DEGREES}).")
                    else:
                        result["details"].append("Insufficient coordinate data to verify grid size.")
                else:
                    # Fallback: Check dimension sizes against expected for a known region if coords missing
                    # London sample is small. If we can't verify coords, we assume the fetch logic (T001b) was correct
                    # but we flag it.
                    result["details"].append("Coordinate arrays 'lat'/'lon' not found in file root. Assuming fetch logic correct.")
                    # We cannot strictly verify grid size without coords, so we mark as False or warn?
                    # Strict validation: Fail if we can't check.
                    result["grid_size_ok"] = False 
                    result["details"].append("Grid size verification failed: Coordinate arrays missing.")
            else:
                result["details"].append("Cannot verify grid size: Dataset dimensions too low.")

            # 3. Validate Temperature Values
            # Read a sample of data to ensure values are within plausible range (Kelvin)
            # Read first time step, first lat/lon to check type and range
            sample_data = t2m_dataset[0, :, :]
            min_val = float(sample_data.min())
            max_val = float(sample_data.max())
            
            if min_val >= MIN_TEMP_K and max_val <= MAX_TEMP_K:
                result["temperature_values_valid"] = True
                result["details"].append(f"Temperature range valid: {min_val:.2f}K to {max_val:.2f}K.")
            else:
                result["details"].append(f"Temperature range invalid: {min_val:.2f}K to {max_val:.2f}K (expected {MIN_TEMP_K}-{MAX_TEMP_K}K).")

    except Exception as e:
        result["details"].append(f"Error reading file: {str(e)}")
        return result

    # Final Status
    if result["temporal_resolution_ok"] and result["grid_size_ok"] and result["temperature_values_valid"]:
        result["status"] = "PASS"
    else:
        result["status"] = "FAIL"

    return result

def main():
    logger = get_data_quality_logger()
    if not logger:
        # Fallback if logger setup fails
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)

    file_path = "data/raw/era_sample.h5"
    log_path = "results/logs/data_validation_log.txt"
    
    # Ensure log directory exists
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting validation for {file_path}")
    
    validation_result = validate_era5_sample(file_path)
    
    # Format log entry
    log_entry = (
        f"Task: T004 | File: {file_path} | Status: {validation_result['status']} | "
        f"Details: {'; '.join(validation_result['details'])}\n"
    )
    
    # Append to log file
    with open(log_path, 'a') as f:
        f.write(log_entry)
    
    logger.info(f"Validation complete. Status: {validation_result['status']}")
    logger.info(f"Details: {'; '.join(validation_result['details'])}")

    if validation_result['status'] == 'FAIL':
        logger.error("Validation FAILED. Check logs for details.")
        sys.exit(1)
    else:
        logger.info("Validation PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
