import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from typing import Optional, Tuple

# Add parent directory to path to allow imports from utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import get_project_root, get_raw_data_dir, get_metadata_file
from utils.provenance import compute_file_hash, save_provenance_record

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# S3 configuration
EBD_RELEASE_BUCKET = "ebird-data"
EBD_RELEASE_PREFIX = "ebd_release"
EBD_SUBSET_BUCKET = "ebird-data"
EBD_SUBSET_PREFIX = "ebd_subset"
EBD_SUBSET_FILENAME = "ebd_subset.parquet"

def list_s3_bucket(bucket: str, prefix: str) -> list:
    """
    List objects in an S3 bucket with a given prefix.
    Uses s3fs to interact with S3.
    """
    try:
        import s3fs
        fs = s3fs.S3FileSystem()
        path = f"{bucket}/{prefix}"
        if not fs.exists(path):
            logger.warning(f"S3 path does not exist: {path}")
            return []
        
        files = fs.ls(path, detail=False)
        # Filter out directories if any
        files = [f for f in files if not f.endswith('/')]
        return files
    except Exception as e:
        logger.error(f"Error listing S3 bucket {bucket}/{prefix}: {e}")
        return []

def find_latest_parquet(bucket: str, prefix: str) -> Optional[str]:
    """
    Find the latest parquet file in the S3 bucket/prefix.
    Assumes filenames are sortable (e.g., ebd_rel_202301.parquet).
    """
    files = list_s3_bucket(bucket, prefix)
    if not files:
        return None
    
    # Filter for parquet files
    parquet_files = [f for f in files if f.endswith('.parquet')]
    if not parquet_files:
        return None
    
    # Sort and return the last one (assuming chronological naming)
    parquet_files.sort()
    return parquet_files[-1]

def download_file(s3_path: str, local_path: str) -> bool:
    """
    Download a file from S3 to local storage.
    """
    try:
        import s3fs
        fs = s3fs.S3FileSystem()
        
        # Ensure local directory exists
        local_dir = os.path.dirname(local_path)
        os.makedirs(local_dir, exist_ok=True)
        
        # Download
        fs.download(s3_path, local_path)
        logger.info(f"Successfully downloaded {s3_path} to {local_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to download {s3_path}: {e}")
        return False

def compute_sha256(file_path: str) -> str:
    """
    Compute SHA-256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_metadata(metadata_path: str, dataset_info: dict):
    """
    Update metadata.yaml with new dataset information.
    """
    metadata = {}
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = yaml.safe_load(f) or {}
    
    if 'datasets' not in metadata:
        metadata['datasets'] = {}
    
    metadata['datasets']['ebd_train'] = dataset_info
    
    with open(metadata_path, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False)
    
    logger.info(f"Updated metadata at {metadata_path}")

def main():
    """
    Main function to download EBD data.
    Attempts primary source first, then falls back to subset.
    """
    project_root = get_project_root()
    raw_data_dir = get_raw_data_dir()
    metadata_path = get_metadata_file()
    
    output_file = os.path.join(raw_data_dir, "ebd_train.parquet")
    
    # Ensure output directory exists
    os.makedirs(raw_data_dir, exist_ok=True)
    
    # Try primary source
    primary_file = find_latest_parquet(EBD_RELEASE_BUCKET, EBD_RELEASE_PREFIX)
    
    if primary_file:
        s3_path = f"{EBD_RELEASE_BUCKET}/{EBD_RELEASE_PREFIX}/{primary_file}"
        logger.info(f"Attempting download from primary source: {s3_path}")
        
        if download_file(s3_path, output_file):
            checksum = compute_sha256(output_file)
            file_size = os.path.getsize(output_file)
            
            dataset_info = {
                "source_url": s3_path,
                "version": primary_file,
                "download_date": datetime.now().isoformat(),
                "checksum": checksum,
                "local_path": output_file,
                "size_bytes": file_size
            }
            
            save_metadata(metadata_path, dataset_info)
            logger.info(f"Download completed successfully. Checksum: {checksum}")
            return True
        else:
            logger.warning("Primary source download failed. Trying fallback.")
    else:
        logger.warning("No primary source found. Trying fallback.")
    
    # Try fallback source
    fallback_file = EBD_SUBSET_FILENAME
    s3_fallback_path = f"{EBD_SUBSET_BUCKET}/{EBD_SUBSET_PREFIX}/{fallback_file}"
    logger.info(f"Attempting download from fallback source: {s3_fallback_path}")
    
    if download_file(s3_fallback_path, output_file):
        checksum = compute_sha256(output_file)
        file_size = os.path.getsize(output_file)
        
        dataset_info = {
            "source_url": s3_fallback_path,
            "version": fallback_file,
            "download_date": datetime.now().isoformat(),
            "checksum": checksum,
            "local_path": output_file,
            "size_bytes": file_size,
            "fallback_used": True
        }
        
        save_metadata(metadata_path, dataset_info)
        logger.info(f"Fallback download completed successfully. Checksum: {checksum}")
        return True
    else:
        logger.error("Both primary and fallback sources failed.")
        raise FileNotFoundError("Failed to download EBD data from both primary and fallback sources.")

if __name__ == "__main__":
    from datetime import datetime
    main()
