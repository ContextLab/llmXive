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
    Calculate the SHA256 checksum of a file.

    Args:
        file_path: Path to the file to checksum.

    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error calculating checksum for {file_path}: {e}")
        raise

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verify the SHA256 checksum of a file against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected SHA256 hex string.

    Returns:
        True if checksum matches, False otherwise.

    Raises:
        ValueError: If checksum mismatch occurs.
    """
    actual_checksum = calculate_sha256(file_path)
    if actual_checksum != expected_checksum:
        msg = (
            f"Checksum mismatch for {file_path}.\n"
            f"Expected: {expected_checksum}\n"
            f"Actual:   {actual_checksum}"
        )
        logger.error(msg)
        raise ValueError(msg)
    
    logger.info(f"Checksum verified successfully for {file_path}")
    return True

def store_metadata(metadata: Dict[str, Any], output_path: str) -> None:
    """
    Store metadata dictionary to a YAML file.

    Args:
        metadata: Dictionary containing file metadata (path, checksum, size, date).
        output_path: Path to the output YAML file.
    """
    path_obj = Path(output_path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path_obj, 'w', encoding='utf-8') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Metadata stored to {output_path}")

def fetch_era5_data(
    variable: str,
    year: int,
    month: int,
    day: Optional[int] = None,
    area: Optional[List[float]] = None,
    output_dir: str = "data/raw"
) -> str:
    """
    Fetch ERA5 data from CDS API.

    Args:
        variable: Variable name (e.g., 'geopotential', 'integrated_water_vapor_transport').
        year: Year of data.
        month: Month of data.
        day: Specific day (optional, for daily data).
        area: [north, west, south, east] bounding box.
        output_dir: Directory to save the downloaded file.

    Returns:
        Path to the downloaded NetCDF file.
    """
    client = cdsapi.Client()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    request_args = {
        'product_type': 'reanalysis',
        'format': 'netcdf',
        'variable': variable,
        'year': str(year),
        'month': f'{month:02d}',
        'time': ['00:00', '06:00', '12:00', '18:00'],
        'area': area if area else [90, -180, -90, 180], # Default global
    }
    
    if day:
        request_args['day'] = f'{day:02d}'
    
    filename = f"{variable}_{year}_{month:02d}.nc"
    file_path = output_dir / filename
    
    logger.info(f"Downloading {variable} for {year}-{month:02d}...")
    client.retrieve(
        'reanalysis-era5-single-levels',
        request_args,
        str(file_path)
    )
    
    logger.info(f"Downloaded to {file_path}")
    return str(file_path)

def download_ivt_and_geopotential(
    years: List[int],
    area: List[float],
    output_dir: str = "data/raw",
    metadata_file: str = "data/metadata.yaml"
) -> List[str]:
    """
    Download IVT and Geopotential data for a range of years.

    Args:
        years: List of years to download.
        area: [north, west, south, east] bounding box.
        output_dir: Directory to save files.
        metadata_file: Path to the metadata YAML file to update.

    Returns:
        List of paths to downloaded files.
    """
    downloaded_files = []
    
    # Load existing metadata if it exists
    existing_metadata = {}
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r') as f:
            existing_metadata = yaml.safe_load(f) or {}
    
    for year in years:
        for month in range(1, 13):
            for variable in ['geopotential', 'integrated_water_vapor_transport']:
                file_path = fetch_era5_data(
                    variable=variable,
                    year=year,
                    month=month,
                    area=area,
                    output_dir=output_dir
                )
                
                # Calculate checksum
                checksum = calculate_sha256(file_path)
                file_size = os.path.getsize(file_path)
                
                # Update metadata
                file_key = os.path.basename(file_path)
                existing_metadata[file_key] = {
                    'path': file_path,
                    'checksum': checksum,
                    'size_bytes': file_size,
                    'downloaded_at': str(year) + "-" + f"{month:02d}"
                }
                
                downloaded_files.append(file_path)
    
    # Store updated metadata
    store_metadata(existing_metadata, metadata_file)
    
    return downloaded_files

def main():
    """
    Main entry point for downloading and verifying data.
    """
    # Define regional domain: 20°N-60°N, 100°E-60°W
    # CDS area format: [North, West, South, East]
    # North: 60, West: -60 (60°W), South: 20, East: -100 (100°E is -100 in standard, but CDS uses 0-360 or -180-180? 
    # CDS standard is usually -180 to 180. 100°E is 100, 60°W is -60. 
    # Wait, 100°E is East, 60°W is West. 
    # Standard W/E: West is negative, East is positive.
    # 100°E = 100. 60°W = -60.
    # However, the task description says "100°E-60°W".
    # If West is -60 and East is 100, the box is valid.
    # Let's use [60, -60, 20, 100].
    # Note: CDS area is [north, west, south, east].
    # North: 60, West: -60, South: 20, East: 100.
    
    area = [60.0, -60.0, 20.0, 100.0]
    years = list(range(1979, 2024)) # 1979-2023 inclusive
    
    download_ivt_and_geopotential(
        years=years,
        area=area,
        output_dir="data/raw",
        metadata_file="data/metadata.yaml"
    )

if __name__ == "__main__":
    main()
