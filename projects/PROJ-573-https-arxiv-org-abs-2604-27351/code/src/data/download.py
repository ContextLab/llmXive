"""
Dataset download and verification utilities.
Implements retry logic and checksum verification for benchmark datasets.
"""
import hashlib
import os
import time
import logging
from pathlib import Path
from typing import Tuple, Optional, Any, Dict, List
import requests
from datasets import load_dataset

# Configure logging
logger = logging.getLogger(__name__)

def ensure_data_dirs() -> Path:
    """Ensure data directories exist."""
    data_dir = Path("data")
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    return data_dir

def compute_dataset_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_dataset_integrity(file_path: Path, expected_checksum: Optional[str] = None) -> bool:
    """Verify dataset integrity via checksum."""
    if not file_path.exists():
        logger.error(f"Dataset file not found: {file_path}")
        return False
    
    actual_checksum = compute_dataset_checksum(file_path)
    logger.info(f"Computed checksum for {file_path.name}: {actual_checksum[:16]}...")
    
    if expected_checksum:
        if actual_checksum == expected_checksum:
            logger.info("Checksum verification passed.")
            return True
        else:
            logger.error(f"Checksum mismatch! Expected: {expected_checksum[:16]}..., Got: {actual_checksum[:16]}...")
            return False
    
    return True

def download_dataset(url: str, max_retries: int = 3, timeout: int = 300) -> Tuple[Path, str]:
    """
    Download a dataset with retry logic.
    
    Args:
        url: Dataset URL or HuggingFace dataset identifier
        max_retries: Maximum number of retry attempts
        timeout: Timeout in seconds for the download
        
    Returns:
        Tuple of (local_path, checksum)
        
    Raises:
        Exception: If download fails after all retries
    """
    ensure_data_dirs()
    data_dir = Path("data") / "raw"
    
    # Handle HuggingFace datasets
    if url in ['UCI_HAR', 'drop', 'must']:
        return _download_huggingface_dataset(url, data_dir, timeout)
    
    # Handle direct URL downloads
    attempt = 0
    last_error = None
    
    while attempt < max_retries:
        try:
            logger.info(f"Download attempt {attempt + 1}/{max_retries} for {url}")
            
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            
            # Extract filename from URL
            filename = url.split('/')[-1]
            if not filename:
                filename = f"dataset_{int(time.time())}"
            local_path = data_dir / filename
            
            # Download file
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            checksum = compute_dataset_checksum(local_path)
            logger.info(f"Successfully downloaded {url} to {local_path}")
            logger.info(f"Checksum: {checksum[:16]}...")
            
            return local_path, checksum
            
        except Exception as e:
            last_error = e
            attempt += 1
            if attempt < max_retries:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Download failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Download failed after {max_retries} attempts: {e}")
                raise Exception(f"Failed to download {url} after {max_retries} attempts: {last_error}")
    
    raise Exception(f"Download failed after {max_retries} attempts: {last_error}")

def _download_huggingface_dataset(dataset_name: str, data_dir: Path, timeout: int) -> Tuple[Path, str]:
    """
    Download a dataset from HuggingFace datasets.
    
    Args:
        dataset_name: Name of the dataset (e.g., 'UCI_HAR', 'drop')
        data_dir: Directory to save the dataset
        timeout: Timeout for the download
        
    Returns:
        Tuple of (local_path, checksum)
    """
    logger.info(f"Loading dataset '{dataset_name}' from HuggingFace...")
    
    try:
        # Load dataset (this will cache it automatically)
        dataset = load_dataset(dataset_name)
        
        # Save to local directory for checksum computation
        local_dir = data_dir / dataset_name
        local_dir.mkdir(parents=True, exist_ok=True)
        
        # Save dataset to parquet for easy checksumming
        output_path = local_dir / "dataset.parquet"
        dataset.save_to_disk(str(local_dir))
        
        # Compute checksum of the directory (hash of all files)
        combined_hash = hashlib.sha256()
        for file_path in local_dir.rglob("*"):
            if file_path.is_file() and file_path.name != ".gitkeep":
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        combined_hash.update(chunk)
        
        checksum = combined_hash.hexdigest()
        logger.info(f"Successfully downloaded dataset '{dataset_name}' to {local_dir}")
        logger.info(f"Checksum: {checksum[:16]}...")
        
        return local_dir, checksum
        
    except Exception as e:
        logger.error(f"Failed to download dataset '{dataset_name}': {e}")
        raise

def main():
    """Main function to demonstrate dataset download."""
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Example: Download UCI_HAR dataset
    try:
        path, checksum = download_dataset('UCI_HAR', max_retries=3, timeout=600)
        print(f"Dataset downloaded to: {path}")
        print(f"Checksum: {checksum}")
    except Exception as e:
        print(f"Failed to download dataset: {e}")

if __name__ == "__main__":
    main()
