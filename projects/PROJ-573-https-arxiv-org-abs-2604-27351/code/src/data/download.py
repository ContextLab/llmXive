"""
Dataset download utilities for the Heterogeneous Scientific Foundation Model Collaboration Benchmark.

This module provides functions to download datasets from HuggingFace with retry logic,
checksum computation, and integrity verification.
"""

import hashlib
import os
import time
import logging
from pathlib import Path
from typing import Tuple, Optional, Any, Dict, List

try:
    from datasets import load_dataset
except ImportError:
    load_dataset = None
    raise ImportError(
        "The 'datasets' package is required. Install it via: pip install datasets"
    )

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Mapping of dataset identifiers to their HuggingFace repository IDs
DATASET_REGISTRY: Dict[str, str] = {
    "UCI_HAR": "uciml/uci-human-activity-recognition",
    "DROP": "drop",
    "MUST": "mustard",
}

# Maximum number of retries for download operations
DEFAULT_MAX_RETRIES = 3
# Timeout in seconds for each download attempt
DEFAULT_TIMEOUT = 300
# Base directory for downloaded datasets
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"

def ensure_data_dirs() -> Path:
    """Ensure the data directories exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    return PROCESSED_DIR

def compute_dataset_checksum(data_dir: Path, algorithm: str = "sha256") -> str:
    """
    Compute a checksum for a dataset directory by hashing all file contents.
    
    Args:
        data_dir: Path to the dataset directory.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal string of the checksum.
    """
    hasher = hashlib.new(algorithm)
    
    # Sort files to ensure deterministic ordering
    all_files = sorted([f for f in data_dir.rglob('*') if f.is_file()])
    
    if not all_files:
        logger.warning(f"No files found in {data_dir} to compute checksum.")
        return hasher.hexdigest()
    
    for file_path in all_files:
        try:
            with open(file_path, 'rb') as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)
        except (IOError, OSError) as e:
            logger.error(f"Error reading file {file_path} for checksum: {e}")
            # Continue with other files
    
    return hasher.hexdigest()

def verify_dataset_integrity(data_dir: Path, expected_checksum: Optional[str] = None) -> Tuple[bool, str]:
    """
    Verify the integrity of a downloaded dataset.
    
    Args:
        data_dir: Path to the dataset directory.
        expected_checksum: Optional expected checksum to verify against.
        
    Returns:
        Tuple of (is_valid, computed_checksum).
    """
    if not data_dir.exists():
        return False, ""
    
    computed = compute_dataset_checksum(data_dir)
    
    if expected_checksum:
        is_valid = computed == expected_checksum
        if not is_valid:
            logger.error(f"Checksum mismatch. Expected: {expected_checksum}, Got: {computed}")
        else:
            logger.info(f"Dataset integrity verified. Checksum: {computed}")
    else:
        logger.info(f"Dataset checksum computed (no expected value provided): {computed}")
        is_valid = True
        
    return is_valid, computed

def download_dataset(
    dataset_id: str,
    max_retries: int = DEFAULT_MAX_RETRIES,
    timeout: int = DEFAULT_TIMEOUT,
    output_dir: Optional[Path] = None
) -> Tuple[Path, str]:
    """
    Download a dataset from HuggingFace with retry logic.
    
    Args:
        dataset_id: Identifier for the dataset (e.g., 'UCI_HAR', 'DROP').
        max_retries: Maximum number of retry attempts (default: 3).
        timeout: Timeout in seconds for the download operation (default: 300).
        output_dir: Optional output directory. Defaults to data/processed/.
        
    Returns:
        Tuple of (path_to_dataset, checksum).
        
    Raises:
        ValueError: If dataset_id is not found in the registry.
        RuntimeError: If download fails after all retries.
        TimeoutError: If download times out.
    """
    if load_dataset is None:
        raise ImportError("The 'datasets' package is required for downloading datasets.")
        
    if dataset_id not in DATASET_REGISTRY:
        raise ValueError(
            f"Dataset '{dataset_id}' not found in registry. "
            f"Available: {list(DATASET_REGISTRY.keys())}"
        )
    
    hf_repo_id = DATASET_REGISTRY[dataset_id]
    output_path = output_dir or ensure_data_dirs()
    dataset_path = output_path / dataset_id
    
    # Check if already downloaded
    if dataset_path.exists():
        logger.info(f"Dataset '{dataset_id}' already exists at {dataset_path}. Skipping download.")
        is_valid, checksum = verify_dataset_integrity(dataset_path)
        if is_valid:
            return dataset_path, checksum
        else:
            logger.warning(f"Existing dataset '{dataset_id}' failed integrity check. Re-downloading...")
            # Remove corrupted data
            import shutil
            shutil.rmtree(dataset_path)
    
    attempt = 0
    last_error = None
    
    while attempt < max_retries:
        attempt += 1
        logger.info(f"Downloading dataset '{dataset_id}' (Attempt {attempt}/{max_retries})...")
        
        try:
            # Set a timeout for the download operation
            # Note: datasets.load_dataset doesn't have a native timeout arg for the whole operation,
            # so we rely on network stack timeouts and our retry logic.
            start_time = time.time()
            
            # Load the dataset (this downloads the data to the cache)
            # We use trust_remote_code=False for security unless explicitly needed
            dataset = load_dataset(hf_repo_id, trust_remote_code=False)
            
            # Save the dataset to our local directory
            # The 'save_to_disk' method writes the dataset to a local path
            dataset.save_to_disk(str(dataset_path))
            
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Download took {elapsed:.2f}s, exceeding timeout of {timeout}s")
            
            logger.info(f"Dataset '{dataset_id}' downloaded successfully in {elapsed:.2f}s.")
            
            # Compute checksum
            checksum = compute_dataset_checksum(dataset_path)
            logger.info(f"Dataset checksum: {checksum}")
            
            return dataset_path, checksum
            
        except TimeoutError:
            last_error = TimeoutError(f"Download timed out after {timeout}s")
            logger.error(f"Attempt {attempt} timed out: {last_error}")
            
        except Exception as e:
            last_error = e
            logger.error(f"Attempt {attempt} failed: {type(e).__name__}: {e}")
        
        if attempt < max_retries:
            wait_time = 2 ** (attempt - 1)  # Exponential backoff: 2s, 4s, 8s
            logger.info(f"Retrying in {wait_time}s...")
            time.sleep(wait_time)
    
    # All retries exhausted
    raise RuntimeError(
        f"Failed to download dataset '{dataset_id}' after {max_retries} attempts. "
        f"Last error: {type(last_error).__name__}: {last_error}"
    )

def main():
    """
    Main entry point for downloading datasets.
    Downloads all registered datasets and prints their checksums.
    """
    logger.info("Starting dataset download process...")
    results = []
    
    for dataset_id in DATASET_REGISTRY.keys():
        try:
            path, checksum = download_dataset(dataset_id)
            results.append({
                "dataset_id": dataset_id,
                "path": str(path),
                "checksum": checksum,
                "status": "success"
            })
            logger.info(f"✓ {dataset_id}: {path} (checksum: {checksum[:16]}...)")
        except Exception as e:
            results.append({
                "dataset_id": dataset_id,
                "path": None,
                "checksum": None,
                "status": "failed",
                "error": str(e)
            })
            logger.error(f"✗ {dataset_id}: Failed - {e}")
    
    # Print summary
    logger.info("\n--- Download Summary ---")
    for r in results:
        status = "SUCCESS" if r["status"] == "success" else "FAILED"
        logger.info(f"{r['dataset_id']}: {status}")
        if r["status"] == "failed":
            logger.info(f"  Error: {r.get('error', 'Unknown')}")
    
    return results

if __name__ == "__main__":
    main()
