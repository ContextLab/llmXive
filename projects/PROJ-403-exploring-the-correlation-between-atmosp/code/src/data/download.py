import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
import cdsapi
from tqdm import tqdm
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger("download")
config = get_config()

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify file checksum against expected value."""
    actual = calculate_sha256(file_path)
    return actual == expected_checksum

def store_metadata(metadata_list: List[Dict[str, Any]], output_path: Path) -> None:
    """Store download metadata in YAML file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        yaml.dump(metadata_list, f, default_flow_style=False)

def fetch_era5_data(variable: str, product_type: str, year: int, month: int, 
                    request_params: Dict[str, Any], output_dir: Path) -> Optional[Path]:
    """Fetch a single month of ERA5 data from CDS."""
    client = cdsapi.Client(
        key=f"{config.cds_api_key}",
        url=config.cds_url,
        quiet=False
    )
    
    filename = output_dir / f"{variable}_{year}_{month:02d}.nc"
    
    # Check if already exists
    if filename.exists():
        logger.info(f"Skipping {variable} {year}-{month:02d}: file exists")
        return filename

    logger.info(f"Downloading {variable} {year}-{month:02d}...")
    
    try:
        client.retrieve(
            'reanalysis-era5-single-levels',
            {
                'product_type': product_type,
                'variable': variable,
                'year': str(year),
                'month': f'{month:02d}',
                'day': [
                    '01', '02', '03', '04', '05', '06', '07', '08',
                    '09', '10', '11', '12', '13', '14', '15', '16',
                    '17', '18', '19', '20', '21', '22', '23', '24',
                    '25', '26', '27', '28', '29', '30', '31'
                ],
                'time': [
                    '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
                    '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
                    '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
                    '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'
                ],
                'format': 'netcdf',
                **request_params
            },
            str(filename)
        )
        return filename
    except Exception as e:
        logger.error(f"Failed to download {variable} {year}-{month:02d}: {e}")
        if filename.exists():
            filename.unlink()
        return None

def download_ivt_and_geopotential():
    """Main function to download IVT and Geopotential data for 1979-2023."""
    output_dir = config.data_dir / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    metadata_list = []
    
    # Define regional domain: 20N-60N, 100E-60W
    # CDS expects lat/lon in specific order. 
    # For 100E to 60W (crossing 180), we handle it as 100 to 300 (since 60W = 300E)
    # But CDS handles bounding boxes. 100E to 60W is a large span.
    # Standard CDS box: [north, west, south, east]
    # 60W is -60. 100E is 100.
    # If we request 100 to -60, CDS might interpret as crossing 180 or wrapping.
    # To be safe and explicit for the "mid-to-high northern latitudes" region:
    # We will request the bounding box [60, -60, 20, 100] -> [North, West, South, East]
    # Wait, CDS box is [North, West, South, East] in degrees.
    # North=60, South=20.
    # West=100E? No, West must be the westernmost longitude. 
    # The region is 100°E to 60°W. 
    # In standard -180 to 180, 100E is 100, 60W is -60.
    # The region spans from 100 to -60? That crosses the dateline (180).
    # Actually, 100E to 60W covers the Pacific and Americas? 
    # 100E is Asia/Australia. 60W is South America/Atlantic.
    # The region 100E -> 180 -> -180 -> -60 covers the Pacific.
    # CDS `area` parameter: [north, west, south, east].
    # If we want 100E to 60W, we are crossing the 180 meridian.
    # CDS usually handles this by splitting or requiring specific handling.
    # However, the task says "100E-60W".
    # Let's assume the standard interpretation: West=100 (if 100E is the start) is wrong.
    # West must be the minimum longitude. 
    # If the region is 100E to 60W, it covers the Pacific.
    # The longitude range is 100 -> 180 -> -180 -> -60.
    # CDS `area` expects [N, W, S, E].
    # If we set W=100 and E=-60, CDS might fail or wrap.
    # Correct approach for CDS: 
    # If the region crosses the dateline, we might need two requests or a specific format.
    # But let's try the standard box first: [60, 100, 20, -60] -> This implies 100 is West, -60 is East.
    # This would cover the region from 100E to 60W (crossing 180) ONLY if CDS interprets W > E as crossing 180.
    # Actually, CDS documentation says: "The area is defined by [north, west, south, east]."
    # If west > east, it assumes crossing the 180 meridian.
    # So: [60, 100, 20, -60] should work for 100E to 60W crossing the Pacific.
    
    request_params = {
        'area': [60.0, 100.0, 20.0, -60.0] # [North, West, South, East]
    }

    years = range(config.start_year, config.end_year + 1)
    months = range(1, 13)
    
    variables = [
        ('integrated_water_vapor_transport', 'integrated_water_vapor_transport'),
        ('geopotential', 'geopotential')
    ]

    for var_name, cds_var in variables:
        for year in years:
            for month in months:
                file_path = fetch_era5_data(
                    cds_var, 
                    'reanalysis', 
                    year, 
                    month, 
                    request_params, 
                    output_dir
                )
                if file_path:
                    checksum = calculate_sha256(file_path)
                    metadata_list.append({
                        "file": str(file_path),
                        "variable": cds_var,
                        "year": year,
                        "month": month,
                        "checksum": checksum,
                        "region": f"{config.lat_min}N-{config.lat_max}N, {config.lon_min}E-{config.lon_max}W"
                    })
    
    # Store metadata
    store_metadata(metadata_list, config.data_dir / "metadata.yaml")
    logger.info(f"Download complete. Metadata saved to {config.data_dir / 'metadata.yaml'}")

def main():
    """Entry point for the download script."""
    if not config.cds_api_key:
        logger.error("CDS API key not found. Set CDS_API_KEY environment variable.")
        return
    
    download_ivt_and_geopotential()

if __name__ == "__main__":
    main()
