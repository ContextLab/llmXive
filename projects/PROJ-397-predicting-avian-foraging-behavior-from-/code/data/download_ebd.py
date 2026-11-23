"""
Download the eBird Basic Dataset (EBD) from S3.

This script attempts to download the latest EBD parquet file from the primary S3 bucket.
If that fails, it falls back to a verified subset.
It saves the file to data/raw/ebd_train.parquet and updates data/metadata.yaml with checksums.
"""
import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from typing import Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.config import get_data_dir, get_raw_data_dir, get_metadata_file
from utils.provenance import compute_file_hash, record_source_info

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# S3 Paths
PRIMARY_BUCKET = "s3://ebird-data/ebd_release/"
FALLBACK_BUCKET = "s3://ebird-data/ebd_subset/"
FALLBACK_FILE = "ebd_subset.parquet"

def list_s3_bucket(bucket_prefix: str) -> Optional[list]:
    """
    List objects in the S3 bucket prefix.
    Uses s3fs to interact with S3.
    """
    try:
        import s3fs
        fs = s3fs.S3FileSystem(anon=True)
        files = fs.ls(bucket_prefix)
        return files
    except Exception as e:
        logger.warning(f"Failed to list S3 bucket {bucket_prefix}: {e}")
        return None

def find_latest_parquet(files: list) -> Optional[str]:
    """
    Find the latest parquet file in the list based on naming convention or modification time.
    Assumes files are named like 'ebd_rel_YYYYMM.parquet' or similar.
    """
    if not files:
        return None
    
    # Filter for .parquet files
    parquet_files = [f for f in files if f.endswith('.parquet')]
    if not parquet_files:
        logger.error("No parquet files found in bucket.")
        return None

    # Simple sort by filename string (assuming YYYYMM format in name)
    # If filenames are standard, sorting alphabetically usually works for dates
    # e.g., ebd_rel_202301.parquet, ebd_rel_202302.parquet
    sorted_files = sorted(parquet_files, reverse=True)
    return sorted_files[0]

def download_file(s3_path: str, local_path: Path, bucket_prefix: str) -> bool:
    """
    Download a file from S3 to local path.
    """
    try:
        import s3fs
        fs = s3fs.S3FileSystem(anon=True)
        # Ensure local directory exists
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Downloading {s3_path} to {local_path}...")
        fs.download(s3_path, str(local_path))
        
        if not local_path.exists():
            logger.error("Download completed but file does not exist locally.")
            return False
        
        logger.info(f"Successfully downloaded {local_path.name}")
        return True
    except Exception as e:
        logger.error(f"Failed to download {s3_path}: {e}")
        return False

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_metadata(metadata_path: Path, source_url: str, checksum: str, download_date: str):
    """Update data/metadata.yaml with the new EBD info."""
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            try:
                metadata = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                metadata = {}
    else:
        metadata = {"datasets": {}}

    if "datasets" not in metadata:
        metadata["datasets"] = {}

    metadata["datasets"]["ebd_train"] = {
        "source_url": source_url,
        "version": os.path.basename(source_url),
        "download_date": download_date,
        "checksum": checksum,
        "local_path": str(metadata_path.parent / "raw" / "ebd_train.parquet")
    }

    with open(metadata_path, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False)
    
    logger.info(f"Updated metadata at {metadata_path}")

def main():
    """Main execution logic."""
    raw_data_dir = get_raw_data_dir()
    metadata_path = get_metadata_file()
    output_file = raw_data_dir / "ebd_train.parquet"
    
    # Ensure directory exists
    raw_data_dir.mkdir(parents=True, exist_ok=True)

    # 1. Attempt Primary Download
    logger.info(f"Attempting to download from primary source: {PRIMARY_BUCKET}")
    files = list_s3_bucket(PRIMARY_BUCKET)
    latest_file = find_latest_parquet(files)
    
    downloaded = False
    primary_url = ""

    if latest_file:
        primary_url = latest_file
        if download_file(latest_file, output_file, PRIMARY_BUCKET):
            downloaded = True
        else:
            logger.warning("Primary download failed.")

    # 2. Fallback to Subset if Primary Failed
    if not downloaded:
        logger.info(f"Attempting fallback download from: {FALLBACK_BUCKET}{FALLBACK_FILE}")
        fallback_path = f"{FALLBACK_BUCKET}{FALLBACK_FILE}"
        if download_file(fallback_path, output_file, FALLBACK_BUCKET):
            downloaded = True
            primary_url = fallback_path # Record the actual source used
        else:
            logger.error("Fallback download also failed.")

    if not downloaded:
        raise FileNotFoundError("Failed to download EBD from both primary and fallback sources.")

    # 3. Compute Checksum and Update Metadata
    checksum = compute_sha256(output_file)
    from datetime import datetime
    download_date = datetime.utcnow().isoformat() + "Z"
    
    save_metadata(metadata_path, primary_url, checksum, download_date)
    
    logger.info(f"EBD download complete. File: {output_file}, Checksum: {checksum}")

if __name__ == "__main__":
    main()
