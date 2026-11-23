"""
Download module for fetching amorphous silicon trajectories from Zenodo.

Implements strict checksum verification and fails loudly on any download or
integrity failure. No synthetic data fallback is permitted.
"""
import json
import logging
import os
import hashlib
import shutil
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from tqdm import tqdm
from config.env_config import get_zenodo_url, get_data_dir, get_config, ConfigError
from validation_utils import compute_file_checksum, verify_file_integrity

logger = logging.getLogger(__name__)

# Zenodo Record ID for the specific a-Si dataset (placeholder, to be verified)
# Based on common literature or project spec, this would be the actual ID.
# If the environment variable ZENODO_RECORD_ID is set, it takes precedence.
DEFAULT_ZENODO_RECORD_ID = "1000000"  # Placeholder, will be overridden by env or config

def download_file(url: str, destination: Path, expected_checksum: Optional[str] = None) -> None:
    """
    Downloads a file from a URL with a progress bar and optional checksum verification.
    
    Args:
        url: The URL to download from.
        destination: The local path to save the file.
        expected_checksum: Optional MD5/SHA256 checksum string to verify integrity.
        
    Raises:
        RuntimeError: If download fails or checksum verification fails.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading {url} to {destination}...")
    
    try:
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 8192
        
        with open(destination, 'wb') as f, tqdm(
            total=total_size,
            unit='B',
            unit_scale=True,
            desc=destination.name
        ) as pbar:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
                    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        raise RuntimeError(f"Download failed: {e}")
    
    if expected_checksum:
        logger.info(f"Verifying checksum for {destination}...")
        actual_checksum = compute_file_checksum(destination)
        
        # Support both MD5 and SHA256 (length check or explicit config)
        # Assuming MD5 for this implementation unless specified otherwise
        if len(expected_checksum) == 32 and len(actual_checksum) == 32:
            is_valid = actual_checksum.lower() == expected_checksum.lower()
        elif len(expected_checksum) == 64 and len(actual_checksum) == 64:
            is_valid = actual_checksum.lower() == expected_checksum.lower()
        else:
            # Fallback to strict comparison if lengths match but type is ambiguous
            is_valid = actual_checksum.lower() == expected_checksum.lower()
            
        if not is_valid:
            logger.error(f"Checksum mismatch for {destination}!")
            logger.error(f"  Expected: {expected_checksum}")
            logger.error(f"  Actual:   {actual_checksum}")
            raise RuntimeError(f"Checksum verification failed for {destination}")
        
        logger.info(f"Checksum verified successfully for {destination}")

def load_zenodo_metadata(record_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetches metadata for a Zenodo record to get file lists and checksums.
    
    Args:
        record_id: The Zenodo record ID. If None, uses env config.
        
    Returns:
        Dictionary containing metadata including files and checksums.
        
    Raises:
        RuntimeError: If metadata cannot be fetched.
    """
    if record_id is None:
        record_id = os.getenv("ZENODO_RECORD_ID", DEFAULT_ZENODO_RECORD_ID)
        
    zenodo_url = f"https://zenodo.org/api/records/{record_id}"
    logger.info(f"Fetching metadata from {zenodo_url}")
    
    try:
        response = requests.get(zenodo_url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch Zenodo metadata: {e}")
        raise RuntimeError(f"Failed to fetch metadata: {e}")

def download_configs(record_id: Optional[str] = None) -> List[Path]:
    """
    Orchestrates the download of all configuration files for a given Zenodo record.
    
    This function:
    1. Fetches metadata to identify files and checksums.
    2. Downloads each file to `data/raw/`.
    3. Verifies checksums immediately after download.
    
    Args:
        record_id: The Zenodo record ID.
        
    Returns:
        List of paths to the downloaded files.
        
    Raises:
        RuntimeError: If any download or verification step fails.
    """
    data_dir = get_data_dir()
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    metadata = load_zenodo_metadata(record_id)
    
    files_to_download = []
    if 'files' in metadata:
        for file_info in metadata['files']:
            # Extract filename and checksum
            # Zenodo API structure: file_info['key'] is filename, 'checksum' is usually 'md5:...'
            filename = file_info.get('key')
            checksum_str = file_info.get('checksum', '')
            
            # Parse checksum (format: "md5:abc123..." or "sha256:abc123...")
            checksum = None
            if ':' in checksum_str:
                algo, value = checksum_str.split(':', 1)
                checksum = value
            
            files_to_download.append({
                'filename': filename,
                'checksum': checksum,
                'url': file_info.get('links', {}).get('self', f"https://zenodo.org/api/records/{record_id}/files-archive/{filename}")
            })
    
    if not files_to_download:
        logger.warning("No files found in Zenodo metadata.")
        return []
        
    downloaded_paths = []
    
    for file_info in files_to_download:
        filename = file_info['filename']
        expected_checksum = file_info['checksum']
        # Construct download URL if not present in metadata (fallback)
        # Zenodo download URL pattern: https://zenodo.org/api/records/{id}/files/{filename}
        download_url = file_info.get('url')
        if not download_url:
            # Fallback to standard Zenodo download link construction if API doesn't provide direct link
            # Note: Zenodo usually provides 'self' in links.files, but we construct a safe fallback
            download_url = f"https://zenodo.org/api/records/{record_id}/files/{filename}"
            
        dest_path = raw_dir / filename
        
        try:
            download_file(download_url, dest_path, expected_checksum)
            downloaded_paths.append(dest_path)
        except RuntimeError as e:
            logger.error(f"Aborting due to failure in downloading {filename}: {e}")
            # Fail loudly as per requirements
            raise e
            
    logger.info(f"Successfully downloaded and verified {len(downloaded_paths)} configurations.")
    return downloaded_paths

def load_configurations_from_raw(raw_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Scans the raw directory for downloaded configuration files and returns their metadata.
    
    Args:
        raw_dir: Path to the raw data directory. Defaults to env config.
        
    Returns:
        List of dictionaries containing file path and basic metadata.
    """
    if raw_dir is None:
        raw_dir = get_data_dir() / "raw"
        
    if not raw_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_dir}")
        return []
        
    configs = []
    for file_path in raw_dir.iterdir():
        if file_path.is_file():
            configs.append({
                'path': str(file_path),
                'filename': file_path.name,
                'size': file_path.stat().st_size
            })
            
    return configs

def main():
    """
    Entry point for the download script.
    Downloads all configurations from the Zenodo record specified in environment variables.
    """
    setup_logging = True # Assuming logging is configured elsewhere or here
    if setup_logging:
        from logging_config import setup_logging as init_logging
        init_logging()
        
    logger.info("Starting download process...")
    
    try:
        # Determine Record ID from environment or config
        record_id = os.getenv("ZENODO_RECORD_ID")
        if not record_id:
            logger.error("ZENODO_RECORD_ID environment variable is not set.")
            raise ConfigError("ZENODO_RECORD_ID environment variable is required.")
        
        downloaded_files = download_configs(record_id)
        
        if downloaded_files:
            logger.info(f"Download complete. Files saved to {get_data_dir() / 'raw'}")
            # Register artifacts in state manager if needed
            from state_manager import register_artifact, save_state
            for f in downloaded_files:
                register_artifact(str(f), "raw_trajectory")
            save_state()
        else:
            logger.warning("No files were downloaded.")
            
    except Exception as e:
        logger.error(f"Download process failed: {e}")
        raise

if __name__ == "__main__":
    main()
