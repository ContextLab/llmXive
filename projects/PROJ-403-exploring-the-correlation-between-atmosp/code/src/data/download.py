import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
import cdsapi
import requests
import time
from src.utils.logger import get_logger

logger = get_logger(__name__)

def calculate_sha256(file_path: str) -> str:
    """
    Calculate SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verify the SHA-256 checksum of a file against an expected value.
    
    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected SHA-256 hex string.
        
    Returns:
        True if checksum matches, False otherwise.
        
    Raises:
        FileNotFoundError: If the file does not exist.
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

def store_metadata(metadata: Dict[str, Any], output_path: str) -> None:
    """
    Store metadata (including checksums) to a YAML file.
    
    Args:
        metadata: Dictionary containing metadata to store.
        output_path: Path to the output YAML file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Metadata stored to {output_path}")

def fetch_era5_data(
    variable: str,
    year: int,
    month: int,
    day: Optional[int] = None,
    area: Optional[List[float]] = None,
    download_path: Optional[str] = None
) -> str:
    """
    Fetch ERA5 data from CDS API.
    
    Args:
        variable: The variable name (e.g., 'integrated_water_vapor_transport', 'geopotential').
        year: Year to fetch data for.
        month: Month to fetch data for.
        day: Optional specific day.
        area: Optional [north, west, south, east] bounding box.
        download_path: Optional path to save the file.
        
    Returns:
        Path to the downloaded file.
    """
    client = cdsapi.Client()
    
    request_params = {
        'product_type': 'reanalysis',
        'format': 'netcdf',
        'variable': variable,
        'year': str(year),
        'month': f"{month:02d}",
    }
    
    if day:
        request_params['day'] = f"{day:02d}"
        
    if area:
        request_params['area'] = area
        
    if not download_path:
        download_path = f"data/raw/{variable}_{year}_{month:02d}.nc"
        
    Path(download_path).parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Fetching {variable} for {year}-{month:02d}...")
    client.retrieve(
        'reanalysis-era5-single-levels',
        request_params,
        download_path
    )
    
    return download_path

def download_ivt_and_geopotential(
    years: List[int],
    area: List[float],
    output_dir: str = "data/raw"
) -> List[Dict[str, Any]]:
    """
    Download IVT and Geopotential data for specified years and region.
    
    Args:
        years: List of years to download.
        area: [north, west, south, east] bounding box.
        output_dir: Directory to save downloaded files.
        
    Returns:
        List of metadata dictionaries for downloaded files.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    metadata_list = []
    
    variables = [
        ('integrated_water_vapor_transport', 'ivt'),
        ('geopotential', 'z')
    ]
    
    for year in years:
        for var_name, var_short in variables:
            for month in range(1, 13):
                file_path = f"{output_dir}/{var_short}_{year}_{month:02d}.nc"
                
                if os.path.exists(file_path):
                    logger.info(f"File exists, skipping download: {file_path}")
                else:
                    file_path = fetch_era5_data(
                        variable=var_name,
                        year=year,
                        month=month,
                        area=area,
                        download_path=file_path
                    )
                
                checksum = calculate_sha256(file_path)
                
                file_metadata = {
                    "file": file_path,
                    "variable": var_name,
                    "year": year,
                    "month": month,
                    "checksum": checksum,
                    "checksum_algorithm": "sha256",
                    "downloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "region": {
                        "north": area[0],
                        "west": area[1],
                        "south": area[2],
                        "east": area[3]
                    }
                }
                metadata_list.append(file_metadata)
                
    return metadata_list

def main():
    """
    Main entry point for downloading data and generating checksums.
    """
    # Define regional domain: 20°N-60°N, 100°E-60°W
    # CDS format: [North, West, South, East]
    # 100°E = 100, 60°W = -60
    region = [60.0, 100.0, 20.0, -60.0]
    years = list(range(1979, 2024))
    
    logger.info(f"Starting download for years {years[0]}-{years[-1]} in region {region}")
    
    metadata = download_ivt_and_geopotential(years, region)
    
    # Store all metadata in a single file
    output_metadata_path = "data/metadata.yaml"
    store_metadata({"files": metadata}, output_metadata_path)
    
    # Verify checksums immediately after download
    verification_results = []
    for meta in metadata:
        is_valid = verify_checksum(meta["file"], meta["checksum"])
        verification_results.append({
            "file": meta["file"],
            "valid": is_valid
        })
        
    # Update metadata with verification status
    for meta, res in zip(metadata, verification_results):
        meta["verification_status"] = "valid" if res["valid"] else "invalid"
        
    store_metadata({"files": metadata, "verification_summary": verification_results}, output_metadata_path)
    
    logger.info("Download and verification complete.")
    return metadata

if __name__ == "__main__":
    main()
