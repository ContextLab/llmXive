import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
import cdsapi
import logging
from src.utils.logger import get_logger

logger = get_logger(__name__)

def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verify the SHA-256 checksum of a file against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected SHA-256 hex string.

    Returns:
        True if checksum matches, False otherwise.
    """
    actual_checksum = calculate_sha256(file_path)
    if actual_checksum.lower() != expected_checksum.lower():
        logger.error(
            f"Checksum mismatch for {file_path}. "
            f"Expected: {expected_checksum}, Got: {actual_checksum}"
        )
        return False
    logger.info(f"Checksum verified for {file_path}")
    return True

def store_metadata(metadata: Dict[str, Any], metadata_path: str) -> None:
    """
    Store metadata (including checksums) to a YAML file.
    If the file exists, it updates the specific entry; otherwise, it creates the file.

    Args:
        metadata: Dictionary containing file metadata (path, checksum, timestamp, etc.).
        metadata_path: Path to the metadata.yaml file.
    """
    metadata_path_obj = Path(metadata_path)
    metadata_path_obj.parent.mkdir(parents=True, exist_ok=True)

    existing_metadata = {}
    if metadata_path_obj.exists():
        try:
            with open(metadata_path_obj, 'r') as f:
                existing_metadata = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logger.warning(f"Could not parse existing metadata file: {e}. Overwriting.")

    # Ensure we have a list of entries if it doesn't exist yet
    if 'files' not in existing_metadata:
        existing_metadata['files'] = []

    # Check if file already exists in the list to update, else append
    file_entry = None
    for entry in existing_metadata['files']:
        if entry.get('path') == metadata.get('path'):
            file_entry = entry
            break

    if file_entry:
        file_entry.update(metadata)
    else:
        existing_metadata['files'].append(metadata)

    with open(metadata_path_obj, 'w') as f:
        yaml.dump(existing_metadata, f, default_flow_style=False)

def fetch_era5_data(
    variable: str,
    year: int,
    month: int,
    day: Optional[int] = None,
    level: str = '500',
    product_type: str = 'reanalysis',
    resolution: str = '0.25',
    area: Optional[List[float]] = None,
    output_dir: str = 'data/raw'
) -> str:
    """
    Fetch ERA5 data from CDS.

    Args:
        variable: Variable name (e.g., 'integrated_water_vapor_transport', 'z').
        year: Year of data.
        month: Month of data.
        day: Specific day (optional, usually for daily data).
        level: Pressure level (e.g., '500').
        product_type: 'reanalysis' or 'ensemble_members'.
        resolution: Grid resolution (e.g., '0.25').
        area: [north, west, south, east]. If None, defaults to global.
        output_dir: Directory to save the file.

    Returns:
        Path to the downloaded NetCDF file.
    """
    client = cdsapi.Client()

    if area is None:
        # Global grid: 90N, 180W, 90S, 180E
        area = [90, -180, -90, 180]

    output_path = Path(output_dir) / f"{variable}_{year}_{month}.nc"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    request_kwargs = {
        'product_type': product_type,
        'format': 'netcdf',
        'variable': variable,
        'pressure_level': level,
        'year': str(year),
        'month': f"{month:02d}",
        'time': ['00:00', '06:00', '12:00', '18:00'], # Default to standard times
        'grid': [float(resolution), float(resolution)],
        'area': area,
    }

    if day:
        request_kwargs['day'] = f"{day:02d}"
        # For daily requests, usually specific time handling might differ,
        # but keeping standard for consistency unless specified.

    logger.info(f"Fetching {variable} for {year}-{month} from CDS...")
    try:
        client.retrieve(
            'reanalysis-era5-single-levels',
            request_kwargs,
            str(output_path)
        )
    except Exception as e:
        logger.error(f"Failed to fetch data from CDS: {e}")
        raise

    return str(output_path)

def download_ivt_and_geopotential(
    years: List[int],
    output_dir: str = 'data/raw',
    metadata_path: str = 'data/metadata.yaml'
) -> List[Dict[str, Any]]:
    """
    Download IVT and Geopotential Height (Z) for a range of years.
    Computes checksums and stores them in metadata.yaml immediately after download.

    Args:
        years: List of years to download.
        output_dir: Directory to save files.
        metadata_path: Path to store metadata.

    Returns:
        List of metadata entries for downloaded files.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    downloaded_files = []

    # Global bounding box
    area = [90, -180, -90, 180]

    variables = [
        {'name': 'integrated_water_vapor_transport', 'level': '0'}, # IVT is surface
        {'name': 'z', 'level': '500'} # Geopotential at 500 hPa
    ]

    for year in years:
        for var in variables:
            # Download for each month (1-12)
            for month in range(1, 13):
                file_path = fetch_era5_data(
                    variable=var['name'],
                    year=year,
                    month=month,
                    level=var['level'],
                    area=area,
                    output_dir=output_dir
                )

                # Calculate checksum
                checksum = calculate_sha256(file_path)

                metadata_entry = {
                    'path': file_path,
                    'variable': var['name'],
                    'level': var['level'],
                    'year': year,
                    'month': month,
                    'checksum': checksum,
                    'checksum_algorithm': 'sha256'
                }

                # Store immediately in metadata
                store_metadata(metadata_entry, metadata_path)
                downloaded_files.append(metadata_entry)

                logger.info(f"Downloaded and verified {var['name']} ({year}-{month}): {checksum[:16]}...")

    return downloaded_files

def convert_geopotential_to_height(file_path: str, output_path: Optional[str] = None) -> str:
    """
    Convert geopotential (z, m²/s²) to geopotential height (Z, meters).
    Z = z / g0.
    In-place or new file creation.

    Args:
        file_path: Path to the NetCDF file.
        output_path: Path for the output file. If None, overwrites input.

    Returns:
        Path to the processed file.
    """
    import xarray as xr
    import numpy as np

    if output_path is None:
        output_path = file_path

    logger.info(f"Converting geopotential to height in {file_path}")
    ds = xr.open_dataset(file_path)

    # Standard gravity
    g0 = 9.80665

    if 'z' in ds:
        ds['z'] = ds['z'] / g0
        ds['z'].attrs['units'] = 'm'
        ds['z'].attrs['long_name'] = 'Geopotential Height'
    else:
        raise ValueError(f"Variable 'z' not found in {file_path}")

    ds.to_netcdf(output_path)
    ds.close()

    # Update checksum if file was modified in place
    if file_path == output_path:
        checksum = calculate_sha256(output_path)
        store_metadata({
            'path': output_path,
            'variable': 'z_height',
            'checksum': checksum,
            'checksum_algorithm': 'sha256',
            'note': 'Converted from geopotential'
        }, 'data/metadata.yaml')

    return output_path

def main():
    """
    Main entry point for downloading data and verifying checksums.
    """
    # Example: Download for 2020-2021 (for testing purposes, adjust as needed)
    # In a real scenario, this would be driven by CLI arguments or config
    years_to_download = [2020, 2021]
    metadata_file = 'data/metadata.yaml'

    logger.info(f"Starting download for years: {years_to_download}")
    try:
        results = download_ivt_and_geopotential(years_to_download, metadata_path=metadata_file)
        logger.info(f"Successfully downloaded and verified {len(results)} files.")
        logger.info(f"Metadata stored in {metadata_file}")
    except Exception as e:
        logger.error(f"Download process failed: {e}")
        raise

if __name__ == '__main__':
    main()
