"""
Dataset download module with retry logic and checksum verification.

Implements FR-010: Dataset download with 3-retry logic.
"""
import hashlib
import os
import time
import logging
import shutil
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List, Union
import requests
from datasets import load_dataset

# Configure logger
logger = logging.getLogger(__name__)

# Constants
CHECKSUM_ALGORITHM = 'sha256'
DEFAULT_MAX_RETRIES = 3
DEFAULT_TIMEOUT = 300  # seconds

def ensure_data_dirs() -> Path:
    """Ensure data directories exist."""
    data_dir = Path("data")
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Data directories ensured: {data_dir}")
    return data_dir

def compute_file_checksum(file_path: Path, algorithm: str = CHECKSUM_ALGORITHM) -> str:
    """Compute SHA256 checksum of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_obj = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks for large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()

def compute_directory_checksum(dir_path: Path, algorithm: str = CHECKSUM_ALGORITHM) -> str:
    """Compute checksum of a directory by hashing all file contents in sorted order."""
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {dir_path}")
    
    hash_obj = hashlib.new(algorithm)
    files = sorted(dir_path.rglob('*'))
    
    for file_path in files:
        if file_path.is_file():
          # Include relative path in hash for structural integrity
          rel_path = file_path.relative_to(dir_path)
          hash_obj.update(str(rel_path).encode('utf-8'))
          # Include file content
          with open(file_path, 'rb') as f:
              for chunk in iter(lambda: f.read(8192), b""):
                  hash_obj.update(chunk)
    
    return hash_obj.hexdigest()

def download_file_with_retry(
    url: str,
    output_path: Path,
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout: int = DEFAULT_TIMEOUT
) -> Tuple[Path, str]:
    """
    Download a file from URL with retry logic.
    
    Args:
        url: URL to download from
        output_path: Local path to save the file
        max_retries: Maximum number of retry attempts (default: 3)
        timeout: Timeout in seconds for the request (default: 300)
        
    Returns:
        Tuple of (Path to saved file, SHA256 checksum)
        
    Raises:
        RuntimeError: If download fails after all retries
        TimeoutError: If request times out
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    attempt = 0
    last_exception = None
    
    while attempt < max_retries:
        try:
            logger.info(f"Downloading {url} to {output_path} (attempt {attempt + 1}/{max_retries})")
            
            response = requests.get(url, stream=True, timeout=timeout)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            checksum = compute_file_checksum(output_path)
            logger.info(f"Download successful: {output_path}, checksum: {checksum[:16]}...")
            return output_path, checksum
            
        except requests.exceptions.Timeout as e:
            last_exception = e
            logger.warning(f"Timeout on attempt {attempt + 1}: {e}")
        except requests.exceptions.RequestException as e:
            last_exception = e
            logger.warning(f"Request error on attempt {attempt + 1}: {e}")
        except Exception as e:
            last_exception = e
            logger.warning(f"Unexpected error on attempt {attempt + 1}: {e}")
        
        attempt += 1
        if attempt < max_retries:
            wait_time = 2 ** attempt  # Exponential backoff
            logger.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    
    raise RuntimeError(
        f"Failed to download {url} after {max_retries} attempts. "
        f"Last error: {last_exception}"
    )

def download_huggingface_dataset(
    dataset_name: str,
    config_name: Optional[str] = None,
    split: Optional[str] = None,
    output_dir: Optional[Path] = None,
    max_retries: int = DEFAULT_MAX_RETRIES
) -> Tuple[Path, str]:
    """
    Download a dataset from HuggingFace datasets.
    
    Args:
        dataset_name: Name of the dataset (e.g., 'UCI_HAR', 'drop')
        config_name: Configuration name if required
        split: Specific split to download (e.g., 'train', 'test')
        output_dir: Directory to save the dataset (default: data/raw/dataset_name)
        max_retries: Maximum retry attempts for loading issues
        
    Returns:
        Tuple of (Path to dataset directory, SHA256 checksum of directory)
        
    Raises:
        RuntimeError: If dataset cannot be loaded after retries
    """
    if output_dir is None:
        ensure_data_dirs()
        output_dir = Path("data") / "raw" / dataset_name
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    attempt = 0
    last_exception = None
    
    while attempt < max_retries:
        try:
            logger.info(f"Loading HuggingFace dataset: {dataset_name} (attempt {attempt + 1}/{max_retries})")
            
            # Load dataset
            load_kwargs = {}
            if config_name:
                load_kwargs['config_name'] = config_name
            if split:
                load_kwargs['split'] = split
                
            dataset = load_dataset(dataset_name, **load_kwargs)
            
            # Save dataset to disk in Arrow format (efficient)
            save_path = output_dir / "dataset"
            dataset.save_to_disk(str(save_path))
            
            # Compute checksum of the saved directory
            checksum = compute_directory_checksum(save_path)
            
            logger.info(f"Dataset saved to {save_path}, checksum: {checksum[:16]}...")
            return save_path, checksum
            
        except Exception as e:
            last_exception = e
            logger.warning(f"Error loading dataset on attempt {attempt + 1}: {e}")
            attempt += 1
            if attempt < max_retries:
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
    
    raise RuntimeError(
        f"Failed to load HuggingFace dataset '{dataset_name}' after {max_retries} attempts. "
        f"Last error: {last_exception}"
    )

def download_dataset(
    url: str,
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout: int = DEFAULT_TIMEOUT
) -> Tuple[Path, str]:
    """
    Download a dataset with 3-retry logic.
    
    Supports both direct URL downloads and HuggingFace datasets.
    For HuggingFace datasets, use the dataset name as the URL (e.g., 'UCI_HAR').
    
    Args:
        url: URL or HuggingFace dataset name
        max_retries: Maximum number of retry attempts (default: 3)
        timeout: Timeout in seconds (default: 300)
        
    Returns:
        Tuple of (Path to downloaded data, SHA256 checksum)
        
    Raises:
        RuntimeError: If download fails after all retries
    """
    # Check if this is a HuggingFace dataset name (no http/https)
    if not url.startswith(('http://', 'https://')):
        # Treat as HuggingFace dataset
        dataset_name = url
        return download_huggingface_dataset(
            dataset_name=dataset_name,
            max_retries=max_retries
        )
    
    # Otherwise, treat as direct URL download
    filename = url.split('/')[-1]
    if not filename:
        filename = "dataset"
    
    output_path = Path("data") / "raw" / filename
    return download_file_with_retry(
        url=url,
        output_path=output_path,
        max_retries=max_retries,
        timeout=timeout
    )

def verify_dataset_integrity(
    dataset_path: Path,
    expected_checksum: str
) -> bool:
    """
    Verify dataset integrity using checksum.
    
    Args:
        dataset_path: Path to dataset file or directory
        expected_checksum: Expected SHA256 checksum
        
    Returns:
        True if checksum matches, False otherwise
    """
    if not dataset_path.exists():
        logger.error(f"Dataset path does not exist: {dataset_path}")
        return False
    
    if dataset_path.is_file():
        actual_checksum = compute_file_checksum(dataset_path)
    else:
        actual_checksum = compute_directory_checksum(dataset_path)
    
    if actual_checksum != expected_checksum:
        logger.error(
            f"Checksum mismatch for {dataset_path}. "
            f"Expected: {expected_checksum[:16]}..., Got: {actual_checksum[:16]}..."
        )
        return False
    
    logger.info(f"Dataset integrity verified: {dataset_path}")
    return True

def main():
    """Main function for testing download functionality."""
    logging.basicConfig(level=logging.INFO)
    
    # Example: Download UCI_HAR dataset
    try:
        logger.info("Testing download_dataset with UCI_HAR...")
        path, checksum = download_dataset('UCI_HAR', max_retries=3)
        logger.info(f"Success: {path}, checksum: {checksum}")
    except Exception as e:
        logger.error(f"Failed to download UCI_HAR: {e}")
    
    # Example: Download a file from URL (if available)
    # try:
    #     url = "https://example.com/dataset.csv"
    #     path, checksum = download_dataset(url, max_retries=3)
    #     logger.info(f"Success: {path}, checksum: {checksum}")
    # except Exception as e:
    #     logger.error(f"Failed to download from URL: {e}")

if __name__ == "__main__":
    main()