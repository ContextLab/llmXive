"""
Download module for fetching datasets from OpenNeuro.
Implements retry logic with exponential backoff and checksum verification.
"""
import os
import subprocess
import time
import hashlib
import json
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import requests

# Configuration constants
INITIAL_BACKOFF = 10  # seconds
MAX_RETRIES = 3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_manifest_hash(manifest_path: Path, filename: str) -> Optional[str]:
    """Extract hash for a specific file from the OpenNeuro manifest."""
    if not manifest_path.exists():
        return None
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    for entry in manifest:
        if entry['filename'] == filename:
            return entry['sha256']
    return None


def download_file(url: str, dest_path: Path, retries: int = MAX_RETRIES) -> bool:
    """
    Download a file from URL with retry logic and exponential backoff.
    
    Args:
        url: The URL to download from
        dest_path: Local path to save the file
        retries: Number of retry attempts (default: MAX_RETRIES)
    
    Returns:
        True if download successful, False otherwise
    
    Raises:
        Exception if all retries fail
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    backoff_time = INITIAL_BACKOFF
    
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{retries}: Downloading from {url}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Successfully downloaded to {dest_path}")
            return True
            
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt} failed: {e}")
            if attempt < retries:
                logger.info(f"Retrying in {backoff_time} seconds...")
                time.sleep(backoff_time)
                backoff_time *= 2  # Exponential backoff
            else:
                logger.error(f"All {retries} attempts failed")
                raise
    
    return False


def verify_checksum(file_path: Path, expected_hash: Optional[str]) -> bool:
    """
    Verify the SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file to verify
        expected_hash: Expected SHA256 hash (if None, only checks file is non-empty)
    
    Returns:
        True if verification passes, False otherwise
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False
    
    if file_path.stat().st_size == 0:
        logger.error(f"File is empty: {file_path}")
        return False
    
    if expected_hash is None:
        logger.info("No expected hash provided, skipping checksum verification")
        return True
    
    actual_hash = calculate_sha256(file_path)
    
    if actual_hash.lower() == expected_hash.lower():
        logger.info(f"Checksum verified: {actual_hash}")
        return True
    else:
        logger.error(f"Checksum mismatch! Expected: {expected_hash}, Got: {actual_hash}")
        return False


def extract_tar_gz(tar_path: Path, dest_dir: Path) -> bool:
    """Extract a tar.gz file to destination directory."""
    try:
        shutil.unpack_archive(str(tar_path), str(dest_dir), format='gztar')
        logger.info(f"Successfully extracted {tar_path} to {dest_dir}")
        return True
    except Exception as e:
        logger.error(f"Failed to extract {tar_path}: {e}")
        return False


def run_download_pipeline(config: Dict[str, Any], output_dir: Path) -> bool:
    """
    Run the complete download pipeline for a dataset.
    
    Args:
        config: Configuration dictionary with dataset info
        output_dir: Directory to save downloaded data
    
    Returns:
        True if pipeline completes successfully, False otherwise
    """
    dataset_id = config.get('dataset_id')
    if not dataset_id:
        logger.error("Dataset ID not found in configuration")
        return False
    
    # Construct OpenNeuro download URL
    base_url = f"https://openneuro.org/datasets/{dataset_id}/downloads"
    
    # For simplicity, we'll download the main tarball
    # In a real implementation, this would parse the manifest
    download_url = f"https://s3.amazonaws.com/openneuro.org/datasets/{dataset_id}/attachments/{dataset_id}.tar.gz"
    
    tar_path = output_dir / f"{dataset_id}.tar.gz"
    
    if not download_file(download_url, tar_path):
        return False
    
    # Verify checksum if available
    manifest_path = output_dir / "manifest.json"
    expected_hash = get_manifest_hash(manifest_path, f"{dataset_id}.tar.gz")
    
    if expected_hash and not verify_checksum(tar_path, expected_hash):
        logger.error("Checksum verification failed")
        return False
    
    # Extract the archive
    if not extract_tar_gz(tar_path, output_dir):
        return False
    
    # Clean up tar file
    tar_path.unlink()
    
    return True
