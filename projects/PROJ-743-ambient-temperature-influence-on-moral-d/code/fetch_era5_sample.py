"""
Fetch a specific sample subset of ERA5 data for validation.
Date Range: Jan 1, 2016 to Jan 7, 2016
Location: London (51.5N, -0.1W)
Output: data/raw/era5_sample.h5
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

import cdsapi

# Ensure logging is configured before importing local modules that depend on it
from setup_logging import setup_logging, get_data_quality_logger

# Configure the logger for this script
logger = get_data_quality_logger()

def ensure_directories():
    """Ensure the output directory exists."""
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def fetch_era5_sample():
    """
    Fetch ERA5 hourly data for London for Jan 1-7, 2016.
    Uses the CDS API to retrieve 2m temperature.
    """
    client = cdsapi.Client()
    
    output_path = ensure_directories() / "era5_sample.h5"
    
    # Request parameters based on task requirements
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
        'area': [51.5, -0.1, 51.5, -0.1],  # [North, West, South, East] for a single point
        'format': 'grib',
    }

    logger.info(f"Starting CDS API fetch for London sample (2016-01-01 to 2016-01-07)...")
    logger.info(f"Target file: {output_path}")

    try:
        # The CDS API returns GRIB format. We save it as .h5 as requested,
        # but technically it's a GRIB file. If the downstream expects HDF5,
        # we would need to convert using cfgrib or xarray. 
        # However, the task specifically asks for .h5. 
        # Standard CDS client saves as the requested format. 
        # To strictly follow "save to .h5" while using CDS which outputs GRIB,
        # we will request GRIB and save to .h5, noting that the content is GRIB data.
        # If strict HDF5 is required, we must convert. 
        # Given the constraint "never fabricate", we fetch real data.
        # We will change format to 'netcdf' which is more standard for .h5/.nc interchange
        # or just save the GRIB as .h5 if the user intends to read it with a GRIB reader.
        # Let's request NetCDF which is natively compatible with HDF5 structures often used in .h5.
        # Actually, CDS API 'format' options are 'grib' or 'netcdf'. 
        # Let's use 'netcdf' to ensure it's a valid scientific data file.
        
        request_params['format'] = 'netcdf'
        
        client.retrieve(
            'reanalysis-era5-single-levels',
            request_params,
            str(output_path)
        )
        
        logger.info(f"Successfully fetched ERA5 sample to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to fetch ERA5 sample: {str(e)}")
        raise

def main():
    """Main entry point for the script."""
    try:
        success = fetch_era5_sample()
        if success:
            # Log success to the validation log
            log_path = Path("results/logs/data_validation_log.txt")
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().isoformat()
            with open(log_path, 'a') as f:
                f.write(f"{timestamp} - T002 - SUCCESS - Fetched era5_sample.h5\n")
            print(f"Success: Data fetched and logged.")
        else:
            # This case shouldn't happen if fetch_era5_sample raises on error
            raise RuntimeError("Fetch reported failure without exception.")
    except Exception as e:
        # Log failure to the validation log
        log_path = Path("results/logs/data_validation_log.txt")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().isoformat()
        with open(log_path, 'a') as f:
            f.write(f"{timestamp} - T002 - FAILED - {str(e)}\n")
        print(f"Failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
