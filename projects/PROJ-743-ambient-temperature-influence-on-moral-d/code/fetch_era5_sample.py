"""
Script to fetch a specific sample subset of ERA5 data for validation.
Parameters: Jan 1, 2016 to Jan 7, 2016 in London (51.5N, -0.1W).
Output: data/raw/era5_sample.h5 (NetCDF format, compatible with .h5 expectations for HDF5-based tools)
Log: results/logs/data_validation_log.txt
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

try:
    import cdsapi
except ImportError:
    print("Error: cdsapi library is not installed. Please install it via 'pip install cdsapi'.")
    sys.exit(1)

# Import logging setup from existing project module
# We use the project's logging infrastructure if available, otherwise fallback to basic config
try:
    from setup_logging import setup_logging, get_data_quality_logger
except ImportError:
    # Fallback if setup_logging isn't ready yet
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    def get_data_quality_logger(name):
        return logging.getLogger(name)

def ensure_directories():
    """Ensure output directories exist."""
    output_dir = Path("data/raw")
    log_dir = Path("results/logs")
    output_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

def fetch_era5_sample():
    """Fetch ERA5 2m temperature sample for London, Jan 1-7, 2016."""
    logger = get_data_quality_logger("fetch_era5_sample")
    logger.info("Starting ERA5 sample fetch for validation.")

    ensure_directories()

    output_path = Path("data/raw/era5_sample.h5")
    log_path = Path("results/logs/data_validation_log.txt")

    # Parameters for the sample fetch
    # Variable: 2m temperature (2t)
    # Date range: 2016-01-01 to 2016-01-07
    # Area: London (51.5N, -0.1W) - defined as [North, West, South, East]
    # Note: CDS API expects [North, West, South, East]
    # London approx: 51.5074, -0.1278
    # We use a small box around London
    area = [51.6, -0.2, 51.4, 0.0]

    request_params = {
        'variable': '2m_temperature',
        'product_type': 'reanalysis',
        'date': '2016-01-01/to/2016-01-07',
        'time': [
            '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
            '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
            '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
            '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'
        ],
        'format': 'netcdf',  # Request NetCDF directly to avoid GRIB conversion issues
        'area': area,
        # CDS API requires 'grid' for area requests to define resolution
        'grid': [0.25, 0.25] 
    }

    logger.info(f"Requesting data for area: {area}, dates: 2016-01-01 to 2016-01-07")

    try:
        client = cdsapi.Client()
        logger.info("Fetching data from CDS API...")
        
        # The CDS API returns the file in the requested format (NetCDF).
        # We save it with the .h5 extension as requested by the task, 
        # as NetCDF4 files are HDF5-based and widely compatible with .h5 loaders.
        client.retrieve(
            'reanalysis-era5-single-levels',
            request_params,
            str(output_path)
        )
        
        # Verify the file exists and is not empty
        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError(f"Downloaded file {output_path} is missing or empty.")
        
        logger.info(f"Successfully fetched sample data to {output_path}")
        
        # Log success to the validation log file
        with open(log_path, 'a') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] SUCCESS: Fetched ERA5 sample for London (Jan 1-7, 2016) to {output_path}\n")
        
        return True

    except Exception as e:
        logger.error(f"Failed to fetch ERA5 sample: {str(e)}")
        with open(log_path, 'a') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] FAIL: Fetch ERA5 sample failed - {str(e)}\n")
        raise  # Fail loudly as per constraints

def main():
    try:
        success = fetch_era5_sample()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Critical error during execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()