import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import cdsapi

from config import get_path_env_override
from setup_logging import setup_logging, get_data_quality_logger

def ensure_directories():
    """Ensure required output directories exist."""
    output_dir = Path(get_path_env_override("DATA_RAW_DIR", "data/raw"))
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def fetch_year_data(year: int, client: cdsapi.Client, output_dir: Path) -> Path:
    """
    Fetch ERA5 2m temperature data for a specific year.
    Parameters:
      year: The year to fetch (e.g., 2016)
      client: Initialized cdsapi client
      output_dir: Directory to save the temporary yearly file
    Returns:
      Path to the saved yearly file.
    """
    output_file = output_dir / f"era5_{year}.h5"
    
    request_params = {
        "product_type": "reanalysis",
        "format": "hdf5",
        "variable": "2m_temperature",
        "year": str(year),
        "month": [
            "01", "02", "03", "04", "05", "06",
            "07", "08", "09", "10", "11", "12"
        ],
        "day": [
            "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
            "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
            "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31"
        ],
        "time": [
            "00:00", "01:00", "02:00", "03:00", "04:00", "05:00",
            "06:00", "07:00", "08:00", "09:00", "10:00", "11:00",
            "12:00", "13:00", "14:00", "15:00", "16:00", "17:00",
            "18:00", "19:00", "20:00", "21:00", "22:00", "23:00"
        ],
        "area": [90, -180, -90, 180], # North, West, South, East (Global)
        "grid": [2.0, 2.0], # 2 degree grid for manageable size, adjust if needed
    }

    logging.info(f"Fetching data for year {year}...")
    try:
        client.retrieve(
            'reanalysis-era5-single-levels',
            request_params,
            str(output_file)
        )
        logging.info(f"Successfully fetched data for {year} -> {output_file}")
        return output_file
    except Exception as e:
        logging.error(f"Failed to fetch data for year {year}: {e}")
        raise

def merge_yearly_files(yearly_files: list, final_output_path: Path):
    """
    Merge multiple yearly HDF5 files into a single final file.
    Since CDS API returns full grid per request, and we are fetching year by year,
    we need to concatenate along the time dimension.
    We assume h5py or xarray is available for merging.
    """
    import h5py
    import numpy as np

    if not yearly_files:
        raise ValueError("No yearly files to merge.")

    # Open first file to get structure
    with h5py.File(yearly_files[0], 'r') as f:
        # Assuming standard ERA5 structure: 'data', 'latitude', 'longitude', 'time'
        # We need to determine the shape and chunks
        data_shape = f['data'].shape
        lat = f['latitude'][:]
        lon = f['longitude'][:]
        time_shape = data_shape[0] # Assuming time is the first dimension
        
        # Calculate total time steps
        total_time_steps = time_shape * len(yearly_files)
        
        # Create final file
        with h5py.File(final_output_path, 'w') as f_out:
            # Create datasets with correct size
            f_out.create_dataset('data', (total_time_steps, data_shape[1], data_shape[2]), 
                                 dtype=f['data'].dtype, chunks=(1, data_shape[1], data_shape[2]))
            f_out.create_dataset('latitude', data=lat)
            f_out.create_dataset('longitude', data=lon)
            
            # Copy time dimension logic if time is stored separately, 
            # but usually ERA5 single level time is implicit or stored in a separate attribute.
            # For simplicity, we assume we just concatenate the data arrays.
            # If 'time' coordinate exists:
            if 'time' in f:
                total_time = np.concatenate([h5py.File(f, 'r')['time'][:] for f in yearly_files])
                f_out.create_dataset('time', data=total_time)

            current_idx = 0
            for i, year_file in enumerate(yearly_files):
                with h5py.File(year_file, 'r') as f_in:
                    data_chunk = f_in['data'][:]
                    f_out['data'][current_idx:current_idx+data_chunk.shape[0], :, :] = data_chunk
                    current_idx += data_chunk.shape[0]
                    logging.info(f"Merged chunk {i+1}/{len(yearly_files)}")
            
            # Copy attributes
            for key, value in f.attrs.items():
                f_out.attrs[key] = value

    logging.info(f"Merged all yearly files into {final_output_path}")

def main():
    """
    Main execution function for T002c.
    Fetches ERA5 data for 2016-2019 by year, merges, and saves to data/raw/era5_full.h5.
    Logs success/fail to results/logs/data_validation_log.txt.
    """
    logger = setup_logging()
    data_logger = get_data_quality_logger()
    
    output_dir = ensure_directories()
    final_output_path = output_dir / "era5_full.h5"
    log_path = Path("results/logs/data_validation_log.txt")
    
    # Ensure log directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Initialize CDS client
        # Assumes CDSAPI_KEY and CDSAPI_URL are set in environment or .cdsapirc
        client = cdsapi.Client()
        
        years = [2016, 2017, 2018, 2019]
        yearly_files = []

        for year in years:
            year_file = fetch_year_data(year, client, output_dir)
            yearly_files.append(year_file)

        # Merge files
        logging.info("Starting merge of yearly files...")
        merge_yearly_files(yearly_files, final_output_path)

        # Cleanup temporary yearly files
        for f in yearly_files:
            if f.exists():
                f.unlink()
                logging.info(f"Removed temporary file: {f}")

        # Log success
        timestamp = datetime.now().isoformat()
        with open(log_path, 'a') as log_file:
            log_file.write(f"[{timestamp}] T002c: SUCCESS - Full ERA5 dataset fetched and merged to {final_output_path}\n")
        
        logger.info("T002c completed successfully.")
        data_logger.info("T002c: Full dataset fetched and saved.")

    except Exception as e:
        error_msg = f"Task T002c failed: {str(e)}"
        logging.error(error_msg)
        with open(log_path, 'a') as log_file:
            log_file.write(f"[{datetime.now().isoformat()}] T002c: FAILED - {error_msg}\n")
        raise

if __name__ == "__main__":
    main()
