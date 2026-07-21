import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
import cdsapi
import time
import logging

from src.utils.logger import get_logger

# Constants for the regional domain (mid-to-high northern latitudes)
# Task T006 specifies: 100°E to 60°W.
# CDS API expects min_lon, max_lon.
# 100°E = 100.0
# 60°W = 360.0 - 60.0 = 300.0
REGIONAL_DOMAIN = {
    "lat": (20.0, 60.0),  # 20°N to 60°N
    "lon": (100.0, 300.0) # 100°E to 60°W
}

# CDS Configuration
CDS_VARIABLES = {
    "ivt": {
        "variable": "integrated_water_vapor_transport",
        "product_type": "reanalysis",
        "format": "netcdf",
        "stream": "operational",
        "levelist": "surface",
        "date": [], # To be populated
        "time": [], # To be populated
        "area": [], # To be populated
        "grid": [], # To be populated
    },
    "z": {
        "variable": "geopotential",
        "product_type": "reanalysis",
        "format": "netcdf",
        "stream": "operational",
        "levelist": "500", # Z500
        "date": [],
        "time": [],
        "area": [],
        "grid": [],
    }
}

# Time range: 1979–2023
START_YEAR = 1979
END_YEAR = 2023

logger = get_logger(__name__)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """Verify the SHA256 checksum of a file against an expected value."""
    actual_checksum = calculate_sha256(file_path)
    return actual_checksum == expected_checksum

def store_metadata(metadata: Dict[str, Any], output_path: str) -> None:
    """Store metadata in a YAML file."""
    with open(output_path, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False)

def fetch_era5_data(
    variable_config: Dict[str, Any],
    output_file: str,
    years: List[int],
    months: List[int],
    days: List[int],
    times: List[str],
    lat_range: Tuple[float, float],
    lon_range: Tuple[float, float],
    resolution: float = 0.25
) -> None:
    """
    Fetch ERA5 data from CDS.
    
    Args:
        variable_config: Configuration dict for the variable (name, level, etc.)
        output_file: Path to save the downloaded NetCDF file.
        years: List of years to fetch.
        months: List of months to fetch.
        days: List of days to fetch.
        times: List of times to fetch (e.g., '00:00', '12:00').
        lat_range: (min_lat, max_lat)
        lon_range: (min_lon, max_lon)
        resolution: Grid resolution in degrees.
    """
    client = cdsapi.Client()
    
    # Format date list as YYYY-MM-DD
    date_list = []
    for y in years:
        for m in months:
            for d in days:
                date_list.append(f"{y:04d}-{m:02d}-{d:02d}")
    
    # Format area as [max_lat, min_lon, min_lat, max_lon] for CDS
    # CDS expects: [north, west, south, east]
    north, south = lat_range
    west, east = lon_range
    area = [north, west, south, east]

    request_params = {
        "variable": variable_config["variable"],
        "product_type": variable_config["product_type"],
        "format": variable_config["format"],
        "stream": variable_config.get("stream", "operational"),
        "levelist": variable_config.get("levelist", "surface"),
        "date": date_list,
        "time": times,
        "area": area,
        "grid": [resolution, resolution],
        "target": output_file
    }

    logger.info(f"Fetching {variable_config['variable']} for {len(date_list)} dates...")
    
    try:
        client.retrieve(
            "reanalysis-era5-single-levels", # Assuming single level for IVT and Z500
            request_params,
            output_file
        )
        logger.info(f"Successfully downloaded {output_file}")
    except Exception as e:
        logger.error(f"Failed to download {variable_config['variable']}: {e}")
        raise

def download_ivt_and_geopotential(
    data_dir: str,
    years: List[int],
    months: List[int],
    days: List[int],
    times: List[str],
    lat_range: Tuple[float, float],
    lon_range: Tuple[float, float]
) -> List[str]:
    """
    Main function to download IVT and Geopotential data for the specified domain.
    
    Args:
        data_dir: Directory to save the downloaded files.
        years: List of years.
        months: List of months.
        days: List of days.
        times: List of times.
        lat_range: (min_lat, max_lat)
        lon_range: (min_lon, max_lon)
        
    Returns:
        List of paths to downloaded files.
    """
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    downloaded_files = []

    for var_key, config in CDS_VARIABLES.items():
        filename = f"{var_key}_{config['levelist']}_1979_2023.nc"
        output_path = str(Path(data_dir) / filename)
        
        # Check if already downloaded
        if os.path.exists(output_path):
            logger.warning(f"File {output_path} already exists. Skipping download.")
            downloaded_files.append(output_path)
            continue

        try:
            fetch_era5_data(
                variable_config=config,
                output_file=output_path,
                years=years,
                months=months,
                days=days,
                times=times,
                lat_range=lat_range,
                lon_range=lon_range
            )
            downloaded_files.append(output_path)
        except Exception as e:
            logger.error(f"Error downloading {var_key}: {e}")
            # Do not return partial list if a critical download fails? 
            # For now, we let the exception propagate or handle gracefully.
            # Given the "fail loudly" constraint, we might want to raise here.
            raise e

    return downloaded_files

def main():
    """Entry point for downloading data."""
    logger.info("Starting data download for T006.")
    
    # Define the regional domain as per T006
    # 20°N-60°N, 100°E-60°W
    lat_range = (20.0, 60.0)
    lon_range = (100.0, 300.0) # 60W is 300E in 0-360 convention

    years = list(range(START_YEAR, END_YEAR + 1))
    months = list(range(1, 13))
    days = list(range(1, 32)) # Will be filtered by CDS to valid days
    times = ["00:00"] # Daily mean or specific time? ERA5 usually has hourly, but for monthly climatology, daily mean might be sufficient. 
                      # However, IVT and Z500 are often analyzed at specific times. 
                      # The task doesn't specify time of day, so we assume 00:00 or daily mean.
                      # Let's fetch 00:00 UTC.
    
    data_dir = "data/raw"
    
    try:
        files = download_ivt_and_geopotential(
            data_dir=data_dir,
            years=years,
            months=months,
            days=days,
            times=times,
            lat_range=lat_range,
            lon_range=lon_range
        )
        logger.info(f"Download completed. Files: {files}")
        
        # Generate metadata
        metadata = {
            "download_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "variables": list(CDS_VARIABLES.keys()),
            "domain": {
                "lat": lat_range,
                "lon": lon_range
            },
            "time_range": {
                "start": f"{START_YEAR}-01-01",
                "end": f"{END_YEAR}-12-31"
            },
            "files": [
                {
                    "path": f,
                    "checksum": calculate_sha256(f)
                } for f in files
            ]
        }
        
        metadata_path = str(Path(data_dir) / "metadata.yaml")
        store_metadata(metadata, metadata_path)
        logger.info(f"Metadata saved to {metadata_path}")
        
    except Exception as e:
        logger.error(f"Data download failed: {e}")
        raise

if __name__ == "__main__":
    main()
