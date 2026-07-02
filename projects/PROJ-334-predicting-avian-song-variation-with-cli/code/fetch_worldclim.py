"""
Fetch WorldClim v2.1 climate data (temperature, precipitation, elevation)
and record SHA256 checksums to data/checksums.txt.
"""
import os
import sys
import csv
import hashlib
import logging
import requests
from pathlib import Path

# Import shared utilities from existing modules
from config import Config
from utils import setup_logging

# Constants for WorldClim v2.1
# WorldClim provides 10-minute (approx 18km) resolution data.
# We will download the global bio1 (annual mean temp), bio12 (annual precip), and elev (elevation) variables.
# Note: Direct bulk download of all variables for all bioclim layers can be large.
# For this script, we download a representative set: bio1, bio12, and elev as a zip or individual tifs.
# To ensure a single downloadable file for checksumming as per task requirements,
# we will download the specific variable files for a representative region or the global set if feasible.
# However, WorldClim's API for direct file download via URL is straightforward for individual files.
# We will download a single representative file (e.g., bio1 global) to demonstrate the mechanism
# and ensure the checksum is recorded for a real artifact.
# Alternatively, we can download a specific region's data if the project scope implies a subset.
# Given T011 fetches global metadata, we aim for global coverage here.
# WorldClim v2.1 10min data URLs pattern:
# https://worldclim.org/data/v2.1/bioclim/bio1.tif (example)
# We will download bio1, bio12, and elev for the global set.
# To avoid multiple checksums for one task, we will download a specific "archive" if available,
# or download the three specific files and hash their concatenation or hash each and log all.
# The task says "record SHA256 checksum immediately to data/checksums.txt".
# We will download the three key variables (bio1, bio12, elev) as .tif files.

WORLDCLIM_BASE_URL = "https://worldclim.org/data/v2.1/bioclim"
ELEVATION_BASE_URL = "https://worldclim.org/data/v2.1/elevation"
VARIABLES = [
    ("bio1", WORLDCLIM_BASE_URL),
    ("bio12", WORLDCLIM_BASE_URL),
    ("elev", ELEVATION_BASE_URL),
]
OUTPUT_DIR = "data/raw"
CHECKSUM_FILE = "data/checksums.txt"

logger = logging.getLogger(__name__)


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def update_checksums_file(file_path: Path, checksum: str, source_url: str):
    """Append a record to the checksums file."""
    checksum_path = Path(CHECKSUM_FILE)
    # Ensure directory exists
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Format: filename, checksum, source_url
    record = f"{file_path.name},{checksum},{source_url}\n"
    
    with open(checksum_path, "a") as f:
        f.write(record)
    
    logger.info(f"Recorded checksum for {file_path.name}: {checksum}")


def download_file(url: str, output_path: Path) -> bool:
    """Download a file from URL to output_path."""
    logger.info(f"Downloading {url} to {output_path}")
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        if os.path.getsize(output_path) == 0:
            logger.error(f"Downloaded file is empty: {output_path}")
            return False
        
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        return False


def fetch_worldclim_data():
    """
    Download WorldClim v2.1 climate variables (bio1, bio12, elev).
    Records checksums to data/checksums.txt.
    Aborts if any download fails.
    """
    config = Config()
    output_dir = Path(config.data_raw_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    success = True
    
    for var_name, base_url in VARIABLES:
        filename = f"{var_name}.tif"
        file_path = output_dir / filename
        url = f"{base_url}/{filename}"
        
        # Check if already downloaded and valid? 
        # For strict reproducibility and checksum recording, we re-download or verify.
        # Let's assume we re-download to ensure fresh data unless file exists and matches.
        # But task says "download real... record checksum".
        # We will attempt download.
        
        if not download_file(url, file_path):
            logger.error(f"Aborting due to failure downloading {filename}")
            success = False
            break
        
        checksum = calculate_sha256(file_path)
        update_checksums_file(file_path, checksum, url)

    if not success:
        logger.error("WorldClim data fetch failed. Aborting.")
        sys.exit(1)
    
    logger.info("WorldClim data fetch completed successfully.")
    return True


def main():
    """Entry point for fetching WorldClim data."""
    setup_logging()
    fetch_worldclim_data()


if __name__ == "__main__":
    main()