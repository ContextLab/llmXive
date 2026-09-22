"""
Download the eBird Basic Dataset (EBD) from S3.

This script attempts to download the latest EBD parquet file from the primary S3 bucket.
If that fails, it falls back to a verified subset.
It saves the file to data/raw/ebd_train.parquet and updates data/metadata.yaml with
the checksum and provenance information.
"""
import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from typing import Optional, Tuple

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from utils.config import get_data_dir, get_raw_data_dir, get_project_root
from utils.provenance import load_metadata_config, save_metadata_config, compute_file_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# S3 Configuration
PRIMARY_BUCKET = "ebird-data"
PRIMARY_PREFIX = "ebd_release/"
FALLBACK_BUCKET = "ebird-data"
FALLBACK_PREFIX = "ebd_subset/"
FALLBACK_FILE = "ebd_subset.parquet"

# Local paths
OUTPUT_FILE_NAME = "ebd_train.parquet"


def list_s3_bucket(bucket_name: str, prefix: str) -> list:
    """
    List objects in an S3 bucket with a given prefix.
    Uses s3fs if available, otherwise falls back to a mock check for local testing logic.
    """
    try:
        import s3fs
        fs = s3fs.S3FileSystem(anon=True)  # Assuming public read access
        files = fs.ls(f"{bucket_name}/{prefix}", detail=False)
        return files
    except ImportError:
        logger.warning("s3fs not installed. Cannot list S3 bucket. Check requirements.txt.")
        return []
    except Exception as e:
        logger.error(f"Error listing S3 bucket {bucket_name}/{prefix}: {e}")
        return []


def find_latest_parquet(bucket_name: str, prefix: str) -> Optional[str]:
    """
    Find the latest parquet file in the given S3 bucket/prefix.
    Returns the full S3 path or None.
    """
    files = list_s3_bucket(bucket_name, prefix)
    if not files:
        return None

    # Filter for parquet files
    parquet_files = [f for f in files if f.endswith('.parquet')]
    if not parquet_files:
        return None

    # Sort by filename (assuming naming convention like ebd_rel_YYYYMM.parquet)
    # If names are just generic, we might need metadata (LastModified), but for now sort by name
    parquet_files.sort(reverse=True)
    return parquet_files[0]


def download_file(s3_path: str, local_path: Path, bucket_name: str) -> bool:
    """
    Download a file from S3 to the local path.
    Returns True on success, False on failure.
    """
    try:
        import s3fs
        fs = s3fs.S3FileSystem(anon=True)
        
        # Ensure directory exists
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Download
        fs.download(s3_path, str(local_path))
        logger.info(f"Successfully downloaded {s3_path} to {local_path}")
        return True
    except ImportError:
        logger.error("s3fs not installed. Cannot download from S3.")
        return False
    except Exception as e:
        logger.error(f"Error downloading {s3_path}: {e}")
        return False


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def save_metadata(metadata: dict, local_path: Path, source_url: str, checksum: str):
    """Update metadata.yaml with the new dataset information."""
    # Load existing metadata
    meta_config = load_metadata_config()
    
    if 'datasets' not in meta_config:
        meta_config['datasets'] = {}
    
    # Update ebd_train entry
    meta_config['datasets']['ebd_train'] = {
        'source_url': source_url,
        'version': source_url.split('/')[-1],
        'download_date': None, # Will be updated by provenance if needed, or left for manual
        'checksum': checksum,
        'local_path': str(local_path.relative_to(get_project_root()))
    }
    
    save_metadata_config(meta_config)
    logger.info(f"Updated metadata.yaml for {local_path}")


def main():
    """Main entry point for downloading EBD data."""
    project_root = get_project_root()
    raw_data_dir = get_raw_data_dir()
    output_path = raw_data_dir / OUTPUT_FILE_NAME

    logger.info(f"Starting EBD download. Output: {output_path}")

    # 1. Attempt Primary Download
    logger.info(f"Attempting to find latest file in s3://{PRIMARY_BUCKET}/{PRIMARY_PREFIX}")
    latest_file = find_latest_parquet(PRIMARY_BUCKET, PRIMARY_PREFIX)
    
    if latest_file:
        logger.info(f"Found candidate: {latest_file}")
        if download_file(latest_file, output_path, PRIMARY_BUCKET):
            checksum = compute_sha256(output_path)
            save_metadata({}, output_path, f"s3://{PRIMARY_BUCKET}/{latest_file}", checksum)
            logger.info("Primary download successful.")
            return 0
        else:
            logger.warning("Primary download failed.")
    else:
        logger.warning("No files found in primary S3 location.")

    # 2. Attempt Fallback Download
    logger.info(f"Falling back to s3://{FALLBACK_BUCKET}/{FALLBACK_PREFIX}")
    fallback_path = f"{FALLBACK_BUCKET}/{FALLBACK_PREFIX}/{FALLBACK_FILE}"
    
    if download_file(fallback_path, output_path, FALLBACK_BUCKET):
        checksum = compute_sha256(output_path)
        save_metadata({}, output_path, f"s3://{fallback_path}", checksum)
        logger.info("Fallback download successful.")
        return 0
    else:
        logger.error("Fallback download also failed.")
        raise FileNotFoundError(
            "Failed to download EBD data from both primary and fallback S3 locations. "
            "Check network connectivity, S3 permissions, or if the data exists."
        )


if __name__ == "__main__":
    sys.exit(main())
