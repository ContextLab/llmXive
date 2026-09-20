import os
import sys
import hashlib
import yaml
import logging
import requests
import zipfile
import time
from pathlib import Path
from datetime import datetime

# Import from project utils
from utils.config import get_project_root, get_raw_data_dir, get_metadata_file
from utils.provenance import record_source_info, save_metadata_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# NLCD 2019 specific constants
NLCD_2019_VERSION = "nlcd_2019_land_cover"
# USGS EarthExplorer API requires authentication, but we will use the direct S3/HTTP mirror
# provided by the Multi-Resolution Land Characteristics Consortium (MRLC) which is the
# authoritative source for NLCD data.
# The specific file for the conterminous US 2019 land cover is available here:
NLCD_2019_URL = "https://s3.amazonaws.com/mrlc/NLCD_2019_Land_Cover_L4.zip"
EXPECTED_FILENAME = "nlcd_2019.zip"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: Path, timeout: int = 300) -> bool:
    """
    Download a file from a URL to a destination path.
    Raises FileNotFoundError if the download fails.
    """
    logger.info(f"Starting download from {url} to {dest_path}")
    
    if dest_path.exists():
        logger.warning(f"File {dest_path} already exists. Overwriting.")
        dest_path.unlink()

    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        logger.info(f"Download progress: {progress:.2f}%")
        
        logger.info(f"Download completed: {dest_path}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download file: {e}")
        raise FileNotFoundError(f"Failed to download NLCD data from {url}: {e}")

def save_metadata(metadata: dict, metadata_path: Path):
    """Save metadata to YAML file."""
    with open(metadata_path, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Metadata saved to {metadata_path}")

def main():
    """
    Main function to download NLCD 2019 data and record provenance.
    """
    project_root = get_project_root()
    raw_data_dir = get_raw_data_dir()
    metadata_path = get_metadata_file()

    # Ensure directories exist
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = raw_data_dir / EXPECTED_FILENAME
    
    logger.info(f"Project root: {project_root}")
    logger.info(f"Raw data directory: {raw_data_dir}")
    logger.info(f"Output file: {output_file}")

    # Step 1: Download the file
    try:
        download_file(NLCD_2019_URL, output_file)
    except FileNotFoundError as e:
        logger.critical(str(e))
        raise  # Re-raise to ensure the pipeline fails loudly

    # Step 2: Compute checksum
    checksum = compute_sha256(output_file)
    logger.info(f"Checksum computed: {checksum}")

    # Step 3: Load existing metadata
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = yaml.safe_load(f) or {}
    else:
        metadata = {"datasets": {}, "artifacts": {}, "pipeline_runs": []}
    
    if "datasets" not in metadata:
        metadata["datasets"] = {}

    # Step 4: Update metadata with NLCD info
    nlcd_entry = {
        "source_url": NLCD_2019_URL,
        "version": NLCD_2019_VERSION,
        "download_date": datetime.utcnow().isoformat() + "Z",
        "checksum": checksum,
        "local_path": str(output_file.relative_to(project_root))
    }
    
    metadata["datasets"]["nlcd_2019"] = nlcd_entry

    # Step 5: Save updated metadata
    save_metadata(metadata, metadata_path)

    logger.info("NLCD 2019 download and metadata recording completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
