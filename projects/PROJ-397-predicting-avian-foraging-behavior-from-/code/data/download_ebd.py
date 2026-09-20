"""
Download the eBird Basic Dataset (EBD) from S3.

This script attempts to download the latest EBD parquet file from the primary S3 bucket.
If that fails, it falls back to a verified subset. It saves the file to the raw data
directory and updates data/metadata.yaml with the checksum and provenance information.
"""

import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from typing import Optional, Tuple

# Add parent directory to path to allow imports from utils
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import s3fs
except ImportError:
    print("Error: s3fs is required. Install it via 'pip install s3fs'.")
    sys.exit(1)

from utils.config import get_project_root, get_raw_data_dir, get_metadata_file
from utils.provenance import record_source_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# S3 Configuration
PRIMARY_BUCKET = "ebird-data"
PRIMARY_PREFIX = "ebd_release/"
FALLBACK_BUCKET = "ebird-data"
FALLBACK_KEY = "ebd_subset/ebd_subset.parquet"

# Local paths
OUTPUT_FILENAME = "ebd_train.parquet"

def list_s3_bucket(fs: s3fs.S3FileSystem, bucket: str, prefix: str) -> list:
    """List objects in an S3 bucket with a given prefix."""
    try:
        files = fs.ls(f"{bucket}/{prefix}", detail=False)
        # Filter out directories if any
        return [f for f in files if f.endswith('.parquet')]
    except Exception as e:
        logger.warning(f"Error listing S3 bucket {bucket}/{prefix}: {e}")
        return []

def find_latest_parquet(files: list) -> Optional[str]:
    """
    Find the latest parquet file based on naming convention or modification time.
    Assumes files are full S3 paths (s3://bucket/key).
    """
    if not files:
        return None
    
    # Sort by key name descending to find latest (assuming versioning in name like ebd_rel_202301)
    # If names are not sortable by date, we might need to fetch metadata, but for now we assume naming convention.
    # Example: s3://ebird-data/ebd_release/ebd_rel_202301.parquet
    sorted_files = sorted(files, reverse=True)
    return sorted_files[0]

def download_file(fs: s3fs.S3FileSystem, s3_path: str, local_path: Path) -> bool:
    """Download a file from S3 to local path."""
    try:
        logger.info(f"Downloading {s3_path} to {local_path}...")
        # Ensure parent directory exists
        local_path.parent.mkdir(parents=True, exist_ok=True)
        fs.download(s3_path, str(local_path))
        logger.info(f"Download complete: {local_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to download {s3_path}: {e}")
        return False

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_metadata(metadata_path: Path, dataset_info: dict):
    """Update the metadata.yaml file with the new dataset information."""
    if not metadata_path.exists():
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata = {"datasets": {}, "artifacts": {}, "pipeline_runs": []}
    else:
        with open(metadata_path, 'r') as f:
            metadata = yaml.safe_load(f)
            if metadata is None:
                metadata = {"datasets": {}, "artifacts": {}, "pipeline_runs": []}

    # Update or add the ebd_train dataset entry
    metadata["datasets"]["ebd_train"] = dataset_info

    with open(metadata_path, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Updated metadata at {metadata_path}")

def main():
    """Main execution function."""
    project_root = get_project_root()
    raw_data_dir = get_raw_data_dir()
    metadata_path = get_metadata_file()
    output_path = raw_data_dir / OUTPUT_FILENAME

    # Ensure directories exist
    raw_data_dir.mkdir(parents=True, exist_ok=True)

    fs = s3fs.S3FileSystem(anon=True)  # Public bucket, no auth needed usually

    # Attempt 1: Primary Source
    logger.info("Attempting to download from primary S3 source...")
    primary_files = list_s3_bucket(fs, PRIMARY_BUCKET, PRIMARY_PREFIX)
    latest_primary = find_latest_parquet(primary_files)

    source_url = None
    version = None
    download_success = False

    if latest_primary:
        # Extract version from key (e.g., ebd_rel_202301.parquet)
        version = latest_primary.split('/')[-1]
        source_url = f"s3://{PRIMARY_BUCKET}/{latest_primary}"
        
        if download_file(fs, latest_primary, output_path):
            download_success = True
        else:
            logger.warning("Primary download failed.")
    else:
        logger.warning("No files found in primary S3 bucket.")

    # Attempt 2: Fallback Source
    if not download_success:
        logger.info("Falling back to verified subset...")
        fallback_source = f"s3://{FALLBACK_BUCKET}/{FALLBACK_KEY}"
        version = "ebd_subset.parquet"
        source_url = fallback_source

        if download_file(fs, fallback_source, output_path):
            download_success = True
        else:
            logger.error("Fallback download failed.")

    if not download_success:
        raise FileNotFoundError(
            "Failed to download EBD data from both primary and fallback S3 sources."
        )

    # Compute checksum
    checksum = compute_sha256(output_path)
    logger.info(f"Checksum computed: {checksum}")

    # Record metadata
    dataset_info = {
        "source_url": source_url,
        "version": version,
        "download_date": datetime.now().isoformat(),
        "checksum": checksum,
        "local_path": str(output_path.relative_to(project_root))
    }

    save_metadata(metadata_path, dataset_info)
    
    # Record provenance
    record_source_info(
        artifact_name="ebd_train",
        source_url=source_url,
        version=version,
        checksum=checksum
    )

    logger.info("EBD download and metadata update completed successfully.")

if __name__ == "__main__":
    from datetime import datetime
    main()
