import json
import logging
import os
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import requests
from tqdm import tqdm

from config.env_config import get_zenodo_url, get_data_dir, get_processed_dir, get_config
from validation_utils import compute_file_checksum, verify_file_integrity
from logging_config import get_logger

logger = get_logger(__name__)

# Zenodo record ID for Amorphous Silicon MD trajectories (Example: 1000000 -> replace with real ID if known,
# but per constraints we use a verified real source pattern.
# Using a real, public Zenodo record for a-Si MD data if available, otherwise a generic fetcher.
# NOTE: In a real deployment, `ZENODO_RECORD_ID` would be set in env.
# For this implementation, we attempt to fetch from a known public dataset or fail loudly.
# We will use a generic Zenodo API call pattern.

ZENODO_API_BASE = "https://zenodo.org/api/records"

def download_file(url: str, dest_path: Path, expected_checksum: Optional[str] = None) -> bool:
    """
    Downloads a file from a URL with progress bar and optional checksum verification.
    Returns True if successful and checksum matches (if provided), False otherwise.
    Raises an exception if download fails or checksum mismatch (fail loudly).
    """
    logger.info(f"Downloading {url} to {dest_path}")
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 1024  # 1 MB
        
        with open(dest_path, 'wb') as f, tqdm(total=total_size, unit='B', unit_scale=True, desc=dest_path.name) as pbar:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        
        if expected_checksum:
            actual_checksum = compute_file_checksum(dest_path)
            if actual_checksum.lower() != expected_checksum.lower():
                logger.error(f"Checksum mismatch for {dest_path}. Expected: {expected_checksum}, Got: {actual_checksum}")
                raise RuntimeError(f"Checksum mismatch for {dest_path}")
            logger.info(f"Checksum verified for {dest_path}")
        
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Download failed for {url}: {e}")
        raise RuntimeError(f"Download failed: {e}")
    except IOError as e:
        logger.error(f"IO error writing {dest_path}: {e}")
        raise RuntimeError(f"IO error: {e}")

def load_zenodo_metadata(record_id: str) -> Dict[str, Any]:
    """
    Fetches metadata from Zenodo API for a given record ID.
    Returns the metadata dictionary.
    """
    url = f"{ZENODO_API_BASE}/{record_id}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch metadata from Zenodo {record_id}: {e}")
        raise RuntimeError(f"Failed to fetch metadata: {e}")

def download_configs() -> List[str]:
    """
    Main entry point for downloading configurations.
    Reads configuration from env (ZENODO_RECORD_ID) or defaults to a known dataset.
    Fetches files listed in metadata, verifies checksums, and saves to data/raw/.
    Returns list of downloaded file paths.
    """
    config = get_config()
    record_id = config.get('zenodo_record_id')
    
    if not record_id:
        # Fallback to a known public dataset if env not set, but strictly speaking
        # we should fail if not configured. However, to make the script runnable
        # for the pipeline, we assume a standard record ID if not provided.
        # For this specific project (a-Si), let's assume a standard record ID is required.
        # If none is found, we raise an error to prevent silent failure.
        raise RuntimeError("ZENODO_RECORD_ID not found in environment/config. Cannot proceed.")

    logger.info(f"Fetching metadata for Zenodo record {record_id}")
    metadata = load_zenodo_metadata(record_id)
    
    files_metadata = metadata.get('files', [])
    if not files_metadata:
        logger.warning(f"No files found in Zenodo record {record_id}")
        # Check if files are in 'versions' or other structure if needed
        # For standard Zenodo, 'files' is the key.
        raise RuntimeError(f"No files found in record {record_id}")

    raw_dir = get_data_dir()
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded_files = []
    
    for file_info in files_metadata:
        file_name = file_info.get('key')
        file_url = file_info.get('links', {}).get('self')
        expected_checksum = file_info.get('checksum', '').split(':')[-1] if file_info.get('checksum') else None
        
        if not file_url:
            logger.warning(f"Skipping {file_name}: No download URL found in metadata")
            continue
        
        dest_path = raw_dir / file_name
        
        try:
            if dest_path.exists():
                logger.info(f"File {dest_path} already exists. Verifying checksum...")
                if expected_checksum:
                    actual = compute_file_checksum(dest_path)
                    if actual.lower() == expected_checksum.lower():
                        logger.info(f"Existing file {dest_path} verified.")
                        downloaded_files.append(str(dest_path))
                        continue
                    else:
                        logger.warning(f"Existing file {dest_path} checksum mismatch. Redownloading.")
                        dest_path.unlink()
            
            download_file(file_url, dest_path, expected_checksum)
            downloaded_files.append(str(dest_path))
            
        except Exception as e:
            logger.error(f"Failed to process {file_name}: {e}")
            raise e # Fail loudly as per constraint
    
    return downloaded_files

def load_configurations_from_raw(raw_dir: Optional[Path] = None) -> List[Path]:
    """
    Scans the raw directory for downloaded trajectory files (e.g., .xyz, .traj, .cfg).
    Returns a list of Path objects for valid configuration files.
    """
    if raw_dir is None:
        raw_dir = get_data_dir()
    
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory {raw_dir} does not exist.")
    
    valid_extensions = {'.xyz', '.traj', '.cfg', '.extxyz', '.dat'}
    config_files = []
    
    for file_path in raw_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in valid_extensions:
            config_files.append(file_path)
    
    if not config_files:
        logger.warning(f"No valid configuration files found in {raw_dir}")
    
    return config_files

def main():
    """
    CLI entry point for download task.
    """
    setup_logging()
    logger.info("Starting download process...")
    try:
        files = download_configs()
        logger.info(f"Successfully downloaded {len(files)} files.")
        for f in files:
            logger.info(f"  - {f}")
    except Exception as e:
        logger.error(f"Download process failed: {e}")
        raise

if __name__ == "__main__":
    main()
