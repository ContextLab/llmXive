"""
Dataset download and verification module.
Implements robust download logic with retries, checksum verification,
and support for HuggingFace datasets.
"""
import hashlib
import os
import time
import logging
import shutil
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

# Try to import datasets, but handle gracefully if not present
try:
    from datasets import load_dataset
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT = 300
BUFFER_SIZE = 8192

def ensure_data_dirs() -> Dict[str, Path]:
    """
    Ensure data directories exist.
    Returns a dictionary of path names to Path objects.
    """
    base = Path("data")
    raw = base / "raw"
    processed = base / "processed"
    
    raw.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)
    
    return {
        "base": base,
        "raw": raw,
        "processed": processed
    }

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm (default: sha256)
        
    Returns:
        Hexadecimal checksum string
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_obj = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        while chunk := f.read(BUFFER_SIZE):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()

def compute_directory_checksum(dir_path: Path, extensions: Optional[List[str]] = None) -> str:
    """
    Compute checksum of all files in a directory (sorted by name for determinism).
    
    Args:
        dir_path: Path to directory
        extensions: Optional list of file extensions to include
        
    Returns:
        Combined checksum string
    """
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    hash_obj = hashlib.sha256()
    files = sorted(dir_path.rglob("*"))
    
    for file_path in files:
        if file_path.is_file():
            if extensions:
                if file_path.suffix not in extensions:
                    continue
            # Include relative path in hash for structure awareness
            rel_path = file_path.relative_to(dir_path)
            hash_obj.update(str(rel_path).encode())
            
            with open(file_path, "rb") as f:
                while chunk := f.read(BUFFER_SIZE):
                    hash_obj.update(chunk)
    
    return hash_obj.hexdigest()

def compute_dataset_checksum(dataset_path: Path) -> str:
    """
    Compute checksum for a dataset directory.
    
    Args:
        dataset_path: Path to dataset directory
        
    Returns:
        Checksum string
    """
    return compute_directory_checksum(dataset_path)

def verify_dataset_integrity(dataset_path: Path, expected_checksum: Optional[str] = None) -> Tuple[bool, str]:
    """
    Verify dataset integrity via checksum.
    
    Args:
        dataset_path: Path to dataset
        expected_checksum: Optional expected checksum for verification
        
    Returns:
        Tuple of (is_valid, checksum_or_error)
    """
    try:
        actual_checksum = compute_dataset_checksum(dataset_path)
        
        if expected_checksum:
            if actual_checksum == expected_checksum:
                return True, actual_checksum
            else:
                return False, f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}"
        else:
            return True, actual_checksum
            
    except Exception as e:
        return False, str(e)

def download_file_with_retry(
    url: str, 
    dest_path: Path, 
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout: int = DEFAULT_TIMEOUT
) -> bool:
    """
    Download a file with retry logic.
    
    Args:
        url: Source URL
        dest_path: Destination path
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
        
    Returns:
        True if download successful, False otherwise
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Downloading {url} to {dest_path} (attempt {attempt + 1}/{max_retries})")
            
            response = requests.get(url, stream=True, timeout=timeout)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=BUFFER_SIZE):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            logger.debug(f"Download progress: {progress:.1f}%")
            
            logger.info(f"Successfully downloaded {dest_path} ({downloaded} bytes)")
            return True
            
        except (Timeout, ConnectionError, RequestException) as e:
            logger.warning(f"Download attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to download {url} after {max_retries} attempts")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error downloading {url}: {e}")
            return False
    
    return False

def download_huggingface_dataset(
    dataset_name: str, 
    config_name: Optional[str] = None,
    split: Optional[str] = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout: int = DEFAULT_TIMEOUT
) -> Tuple[Optional[Path], Optional[str]]:
    """
    Download a dataset from HuggingFace.
    
    Args:
        dataset_name: Name of the dataset (e.g., 'UCI_HAR', 'drop')
        config_name: Optional configuration name
        split: Optional split to download
        max_retries: Maximum retry attempts
        timeout: Timeout in seconds
        
    Returns:
        Tuple of (download_path, checksum) or (None, None) on failure
    """
    if not HF_AVAILABLE:
        logger.error("HuggingFace datasets library not installed. Install with: pip install datasets")
        return None, None
    
    try:
        logger.info(f"Loading HuggingFace dataset: {dataset_name}")
        
        kwargs = {}
        if config_name:
            kwargs['config_name'] = config_name
        if split:
            kwargs['split'] = split
            
        dataset = load_dataset(dataset_name, **kwargs)
        
        # Save dataset to disk
        data_dirs = ensure_data_dirs()
        dataset_dir = data_dirs["raw"] / dataset_name.replace("/", "_")
        dataset_dir.mkdir(parents=True, exist_ok=True)
        
        # Save dataset
        save_path = dataset_dir / "dataset.json"
        # For simplicity, we save a manifest. Real usage would save actual data.
        # In practice, datasets are cached by HF, but we create a local reference.
        
        manifest = {
            "dataset_name": dataset_name,
            "config_name": config_name,
            "split": split,
            "features": str(dataset.info.features) if hasattr(dataset, 'info') else "N/A",
            "num_rows": len(dataset[split]) if split and split in dataset else "N/A"
        }
        
        import json
        with open(save_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Dataset {dataset_name} loaded and manifest saved to {save_path}")
        
        # Compute checksum of the manifest
        checksum = compute_file_checksum(save_path)
        
        return dataset_dir, checksum
        
    except Exception as e:
        logger.error(f"Failed to load HuggingFace dataset {dataset_name}: {e}")
        return None, None

def download_dataset(
    url: str, 
    max_retries: int = DEFAULT_MAX_RETRIES, 
    timeout: int = DEFAULT_TIMEOUT
) -> Tuple[Optional[Path], Optional[str]]:
    """
    Download a dataset from a URL with retry logic.
    
    Args:
        url: URL to download from
        max_retries: Maximum number of retry attempts (default: 3)
        timeout: Timeout in seconds (default: 300)
        
    Returns:
        Tuple of (path, checksum) if successful, (None, None) otherwise
    """
    # Validate inputs
    if not url:
        logger.error("URL cannot be empty")
        return None, None
    
    if max_retries < 1:
        logger.warning("max_retries must be at least 1, setting to 1")
        max_retries = 1
    
    try:
        # Ensure data directories exist
        data_dirs = ensure_data_dirs()
        
        # Extract filename from URL
        filename = url.split('/')[-1].split('?')[0]
        if not filename:
            filename = "dataset.zip"
        
        dest_path = data_dirs["raw"] / filename
        
        # Check if already downloaded
        if dest_path.exists():
            logger.info(f"File already exists: {dest_path}")
            checksum = compute_file_checksum(dest_path)
            return dest_path, checksum
        
        # Download with retries
        success = download_file_with_retry(url, dest_path, max_retries, timeout)
        
        if not success:
            return None, None
        
        # Compute checksum
        checksum = compute_file_checksum(dest_path)
        
        logger.info(f"Dataset downloaded successfully: {dest_path}")
        logger.info(f"Checksum: {checksum}")
        
        return dest_path, checksum
        
    except Exception as e:
        logger.error(f"Error downloading dataset from {url}: {e}")
        return None, None

def main():
    """
    Main entry point for dataset download script.
    Demonstrates download functionality.
    """
    logger.info("Starting dataset download verification")
    
    # Ensure directories
    ensure_data_dirs()
    
    # Example: Download a small public dataset for verification
    # Note: In production, URLs would be configured in a YAML file
    test_urls = [
        # Example URL for a small test file
        "https://archive.ics.uci.edu/ml/machine-learning-databases/00244/UCI_HAR_Dataset.zip"
    ]
    
    for url in test_urls:
        logger.info(f"Attempting to download: {url}")
        path, checksum = download_dataset(url, max_retries=3, timeout=300)
        
        if path:
            logger.info(f"Download successful: {path}")
            logger.info(f"Checksum: {checksum}")
            
            # Verify integrity
            is_valid, msg = verify_dataset_integrity(path)
            logger.info(f"Integrity check: {msg}")
        else:
            logger.error(f"Download failed for: {url}")
    
    # Example: HuggingFace dataset verification
    if HF_AVAILABLE:
        logger.info("Testing HuggingFace dataset loading...")
        path, checksum = download_huggingface_dataset("UCI_HAR")
        if path:
            logger.info(f"HF Dataset path: {path}")
            logger.info(f"HF Dataset checksum: {checksum}")
        else:
            logger.warning("HF Dataset download failed or not available")
    else:
        logger.info("HuggingFace datasets not available, skipping HF test")
    
    logger.info("Dataset download verification complete")

if __name__ == "__main__":
    main()
