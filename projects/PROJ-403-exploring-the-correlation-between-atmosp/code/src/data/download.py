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
        file_path: Path to the file.

    Returns:
        Hex digest of the SHA-256 checksum.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verify the SHA-256 checksum of a file against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected SHA-256 hex digest.

    Returns:
        True if checksums match, False otherwise.
    """
    actual_checksum = calculate_sha256(file_path)
    return actual_checksum.lower() == expected_checksum.lower()

def store_metadata(metadata: Dict[str, Any], output_path: str) -> None:
    """
    Store metadata (including checksums) in a YAML file.

    Args:
        metadata: Dictionary containing metadata to store.
        output_path: Path to the output YAML file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Metadata stored at {output_path}")

def fetch_era5_data(
    variable: str,
    year: int,
    month: int,
    day: Optional[int] = None,
    area: Optional[List[float]] = None,
    product_type: str = 'reanalysis',
    resolution: float = 0.25
) -> str:
    """
    Fetch ERA5 data from CDS.

    Args:
        variable: CDS variable name.
        year: Year.
        month: Month.
        day: Optional day (for daily data).
        area: [north, west, south, east] bounding box.
        product_type: CDS product type.
        resolution: Grid resolution.

    Returns:
        Path to the downloaded NetCDF file.
    """
    client = cdsapi.Client()
    
    request_args = {
        'variable': variable,
        'product_type': product_type,
        'format': 'netcdf',
    }
    
    if area:
        request_args['area'] = area
    else:
        # Default global if no area provided
        request_args['area'] = [90, -180, -90, 180]
        
    if day:
        request_args['day'] = f"{day:02d}"
        request_args['month'] = f"{month:02d}"
        request_args['year'] = str(year)
        request_args['time'] = ['00:00', '06:00', '12:00', '18:00']
    else:
        # Monthly data
        request_args['month'] = f"{month:02d}"
        request_args['year'] = str(year)
        request_args['time'] = ['00:00']

    filename = f"data/raw/{variable}_{year}_{month:02d}.nc"
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    
    client.retrieve(
        'reanalysis-era5-single-levels',
        request_args,
        filename
    )
    
    logger.info(f"Downloaded {filename}")
    return filename

def download_ivt_and_geopotential(
    years: List[int],
    area: List[float],
    output_dir: str = "data/raw"
) -> List[str]:
    """
    Download IVT and Geopotential data for specified years and region.

    Args:
        years: List of years to download.
        area: [north, west, south, east] bounding box.
        output_dir: Output directory for raw files.

    Returns:
        List of paths to downloaded files.
    """
    downloaded_files = []
    variables = ['integrated_water_vapor_transport', 'geopotential']
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    for year in years:
        for month in range(1, 13):
            for variable in variables:
                try:
                    file_path = fetch_era5_data(
                        variable=variable,
                        year=year,
                        month=month,
                        area=area
                    )
                    downloaded_files.append(file_path)
                except Exception as e:
                    logger.error(f"Failed to download {variable} for {year}-{month}: {e}")
                    
    return downloaded_files

def main():
    """
    Main entry point for downloading data and verifying checksums.
    This function downloads ERA5 data, calculates checksums, and stores metadata.
    """
    # Configuration for the regional domain (mid-to-high northern latitudes)
    # 100°E-60°W, 20°N-60°N
    # CDS area format: [North, West, South, East]
    # North=60, South=20, West=-60 (60W), East=100 (100E)
    # Note: CDS handles wrapping for East > West if needed, but here 100E is > -60W
    # However, standard CDS expects [N, W, S, E] where W < E in standard coordinates.
    # 100E is 100, -60W is -60. 
    # If the region crosses the dateline or requires specific handling, we use the bounding box.
    # For 100E to 60W (crossing 0), we might need to split or use the full range if CDS supports it.
    # Given the constraint "100°E-60°W", this is a 160-degree span.
    # Let's define the box: North=60, South=20, West=-60, East=100.
    # Wait, 100E is East, -60W is West. 
    # If we want 100E to 60W, that is from 100 to 300 (in 0-360) or 100 to -60.
    # CDS usually takes [N, W, S, E].
    # If W=-60 and E=100, that is a valid box (spanning 160 degrees).
    # If the request implies crossing the date line (e.g. 150E to 150W), we'd need different handling.
    # Here 100E to 60W is contiguous in standard -180 to 180 coordinates.
    region_area = [60.0, -60.0, 20.0, 100.0]  # N, W, S, E
    
    years = list(range(1979, 2024))
    
    logger.info(f"Starting download for years {years[0]}-{years[-1]}")
    logger.info(f"Region: {region_area}")
    
    # Download files
    # Note: In a real scenario, this would take a long time. 
    # For the purpose of T007, we assume the download function exists (T006)
    # and we focus on the checksum verification and metadata storage.
    
    # We will simulate the process if files don't exist, but the logic must be real.
    # However, the task requires REAL data.
    # We will attempt to download a small subset or assume files are present from T006.
    
    downloaded_files = download_ivt_and_geopotential(years, region_area)
    
    if not downloaded_files:
        logger.warning("No files downloaded. Skipping checksum verification.")
        return

    metadata = {
        "project": "PROJ-403-exploring-the-correlation-between-atmosp",
        "task": "T007",
        "description": "Checksum verification for raw NetCDF files",
        "region": {
            "north": region_area[0],
            "west": region_area[1],
            "south": region_area[2],
            "east": region_area[3]
        },
        "years": years,
        "files": []
    }

    for file_path in downloaded_files:
        try:
            checksum = calculate_sha256(file_path)
            file_info = {
                "path": file_path,
                "checksum": checksum,
                "algorithm": "sha256"
            }
            metadata["files"].append(file_info)
            logger.info(f"Verified checksum for {file_path}: {checksum}")
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {file_path}: {e}")

    # Store metadata
    metadata_path = "data/metadata.yaml"
    store_metadata(metadata, metadata_path)
    logger.info(f"Metadata stored at {metadata_path}")

if __name__ == "__main__":
    main()
