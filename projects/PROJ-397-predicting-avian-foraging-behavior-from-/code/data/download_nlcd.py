"""
Download NLCD 2019 Land Cover data from USGS.

This script fetches the NLCD 2019 land cover data for the contiguous United States
(conus_2019) from the USGS EarthExplorer API / S3 mirror and saves it to the
project's raw data directory. It records the download metadata (checksum, version,
date) in data/metadata.yaml.

The script fails loudly with FileNotFoundError if the download fails.
"""
import os
import sys
import hashlib
import yaml
import logging
import requests
from pathlib import Path
from datetime import datetime

# Import project utilities
from utils.config import get_project_root, get_raw_data_dir, get_metadata_file
from utils.provenance import record_source_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
# NLCD 2019 Conus data is available as a single zip file from USGS S3 mirror
# Source: https://www.mrlc.gov/data/legacies/national-land-cover-database-nlcd-2019
# Direct S3 link to the conus_2019 land cover data (LC2019)
NLCD_URL = "https://s3-us-west-2.amazonaws.com/mrlc/USGS_NLCD_RELEASES/2019_REL/NLCD_Land_Cover/nlcd_2019_land_cover_20190618.zip"
EXPECTED_FILENAME = "nlcd_2019.zip"
CHUNK_SIZE = 1024 * 1024  # 1MB chunks

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, output_path: Path) -> None:
    """Download a file from URL with progress logging."""
    logger.info(f"Downloading {url} to {output_path}")
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Download complete: {output_path}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Download failed: {e}")
        raise FileNotFoundError(f"Failed to download NLCD data from {url}") from e

def save_metadata(metadata_path: Path, version: str, download_date: str, checksum: str) -> None:
    """Update metadata.yaml with NLCD dataset information."""
    # Load existing metadata
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = yaml.safe_load(f) or {}
    else:
        metadata = {}
    
    # Ensure datasets key exists
    if 'datasets' not in metadata:
        metadata['datasets'] = {}
    
    # Record NLCD dataset info
    metadata['datasets']['nlcd_2019'] = {
        'source_url': NLCD_URL,
        'version': version,
        'download_date': download_date,
        'checksum': checksum,
        'local_path': str(output_path)
    }
    
    # Save updated metadata
    with open(metadata_path, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False)
    
    logger.info(f"Metadata updated: {metadata_path}")

def main():
    """Main entry point for NLCD download."""
    project_root = get_project_root()
    raw_data_dir = get_raw_data_dir()
    metadata_path = get_metadata_file()
    
    # Ensure directories exist
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = raw_data_dir / EXPECTED_FILENAME
    version = "nlcd_2019_land_cover_20190618"
    download_date = datetime.utcnow().isoformat()
    
    try:
        # Download the file
        download_file(NLCD_URL, output_path)
        
        # Compute checksum
        checksum = compute_sha256(output_path)
        logger.info(f"Checksum computed: {checksum}")
        
        # Save metadata
        save_metadata(metadata_path, version, download_date, checksum)
        
        # Record provenance
        record_source_info(
            dataset_name="nlcd_2019",
            source_url=NLCD_URL,
            version=version,
            download_date=download_date,
            checksum=checksum,
            local_path=str(output_path)
        )
        
        logger.info("NLCD 2019 download and metadata recording completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"NLCD download failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during NLCD download: {e}")
        raise FileNotFoundError(f"Failed to process NLCD data: {e}") from e

if __name__ == "__main__":
    main()
