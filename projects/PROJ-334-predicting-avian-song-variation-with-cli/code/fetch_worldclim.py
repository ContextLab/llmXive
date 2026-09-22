import os
import sys
import csv
import hashlib
import logging
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import from local project modules based on API surface
from config import Config
from utils import setup_logging

# Constants for WorldClim v2.1
# WorldClim v2.1 provides 30s resolution data.
# We will download the global file for mean annual temperature (bio1),
# annual precipitation (bio12), and elevation.
# Since 30s global files are large, we rely on the 5-minute resolution
# for initial ingestion to keep bandwidth reasonable for the pipeline,
# or stream specific tiles if coordinates are known.
# However, the task requires downloading "real climate variables".
# WorldClim 5-min (0.0083 deg) global files are ~100MB each.
# We will download the global 5-min layers for the core variables.

WORLDCLIM_BASE_URL = "https://worldclim.org/data/worldclim21.html"
# Direct download links for WorldClim 5-min global layers (v2.1)
# These are the standard global files.
WORLDCLIM_DOWNLOADS = {
    "bio1": "https://biogeo.ucdavis.edu/data/worldclim/v2.1/5m/bio/wc2.1_5m_bio_1.tif",
    "bio12": "https://biogeo.ucdavis.edu/data/worldclim/v2.1/5m/bio/wc2.1_5m_bio_12.tif",
    "elev": "https://biogeo.ucdavis.edu/data/worldclim/v2.1/5m/alt/wc2.1_5m_alt.tif"
}

def calculate_sha256(filepath: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_checksums_file(filepath: str, checksum: str, dataset_name: str) -> None:
    """Append checksum to data/checksums.txt."""
    config = Config()
    checksum_file = Path(config.data_dir) / "checksums.txt"
    
    # Ensure directory exists
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(checksum_file, "a", encoding="utf-8") as f:
        f.write(f"{dataset_name}\t{checksum}\t{filepath}\n")

def download_file(url: str, output_path: str, logger: logging.Logger) -> bool:
    """Download a file from URL with progress logging."""
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 1024  # 1 MB
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        logger.info(f"Downloading: {percent:.1f}% complete")
        
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def fetch_worldclim_data(config: Config, logger: logging.Logger) -> bool:
    """
    Download WorldClim v2.1 climate variables (temp, precip, elev) as GeoTIFFs.
    Since the ingestion pipeline (T013/T014) expects CSVs for spatial joining,
    we must convert these GeoTIFFs to a CSV of sample points or a raster summary.
    
    However, the task specifically asks to "download real climate variables".
    The most robust way to align with the ingestion pipeline (which likely expects
    a CSV of locations with climate values) is to download the GeoTIFFs and then
    sample them at the bird locations (which will be done in ingestion.py).
    
    For this task, we download the raw GeoTIFFs and save them to data/raw/.
    We do NOT generate a CSV here because the coordinates are not known yet
    (they come from Xeno-Canto). We save the raster files which will be read
    by ingestion.py to extract values.
    """
    raw_dir = Path(config.data_dir) / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    success = True
    for var_name, url in WORLDCLIM_DOWNLOADS.items():
        filename = f"worldclim_{var_name}.tif"
        output_path = str(raw_dir / filename)
        
        logger.info(f"Downloading {var_name} from WorldClim v2.1...")
        if download_file(url, output_path, logger):
            checksum = calculate_sha256(output_path)
            update_checksums_file(output_path, checksum, f"worldclim_{var_name}")
            logger.info(f"Downloaded and checksummed: {filename} (SHA256: {checksum[:16]}...)")
        else:
            success = False
            logger.error(f"Aborting due to download failure for {var_name}")
            break
    
    return success

def main():
    """Main entry point for fetching WorldClim data."""
    logger = setup_logging("fetch_worldclim")
    logger.info("Starting WorldClim v2.1 data fetch...")
    
    try:
        config = Config()
        if fetch_worldclim_data(config, logger):
            logger.info("WorldClim data fetch completed successfully.")
            sys.exit(0)
        else:
            logger.error("WorldClim data fetch failed. Aborting.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
