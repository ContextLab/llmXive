"""
Data download module for Federated Learning experiments.

This module handles the retrieval of real-world datasets (FEMNIST) from
verified sources. It strictly enforces the exclusion of unverified datasets
(e.g., Shakespeare) and fails loudly if data cannot be retrieved.

No synthetic fallbacks are implemented.
"""
import time
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from datasets import load_dataset

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom exception for data fetching errors
class DataFetchError(Exception):
    """Raised when data fetching fails after retries."""
    pass

def _verify_source(dataset_name: str) -> None:
    """
    Verify that the requested dataset is a supported, verified source.
    
    Args:
        dataset_name: Name of the dataset to verify.
        
    Raises:
        ValueError: If the dataset is not supported or is excluded per plan.md.
    """
    supported_datasets = {"femnist"}
    
    if dataset_name not in supported_datasets:
        if dataset_name == "shakespeare":
            raise ValueError(
                f"Dataset '{dataset_name}' is excluded per plan.md Gap Analysis "
                "(no verified source available). Only 'femnist' is supported."
            )
        else:
            raise ValueError(
                f"Dataset '{dataset_name}' is not supported. "
                f"Supported datasets: {supported_datasets}. "
                f"Refer to plan.md for verified sources."
            )

def _compute_sha256(file_path: Path) -> str:
    """
    Compute SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hex digest of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def _generate_checksum_file(file_path: Path, checksum: str, output_path: Path) -> None:
    """
    Generate a checksum file.
    
    Args:
        file_path: Path to the original file.
        checksum: SHA256 checksum string.
        output_path: Path to write the checksum file.
    """
    output_path.write_text(f"{checksum}  {file_path.name}\n")
    logger.info(f"Checksum file generated: {output_path}")

def download_femnist(output_dir: Optional[Path] = None, max_retries: int = 3) -> Path:
    """
    Download the FEMNIST dataset from Hugging Face datasets.
    
    This function downloads the LEAF FEMNIST dataset, converts it to a
    Parquet file, and generates a SHA256 checksum. It implements retry
    logic with exponential backoff but fails loudly if the download
    ultimately fails.
    
    Args:
        output_dir: Directory to save the downloaded data. Defaults to 'data/raw'.
        max_retries: Maximum number of retry attempts.
        
    Returns:
        Path to the downloaded parquet file.
        
    Raises:
        DataFetchError: If the download fails after all retries.
        ValueError: If the dataset is invalid (checked in _verify_source).
    """
    if output_dir is None:
        output_dir = Path("data/raw")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    parquet_path = output_dir / "femnist.parquet"
    checksum_path = output_dir / "femnist.sha256"
    
    # Verify source before attempting download
    _verify_source("femnist")
    
    logger.info(f"Attempting to download FEMNIST dataset to {parquet_path}...")
    
    last_exception = None
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Download attempt {attempt}/{max_retries}")
            
            # Load dataset from Hugging Face
            # Using the 'leaf/femnist' dataset as per plan.md verified source
            dataset = load_dataset("leaf/femnist", "images", split="train")
            
            # Convert to Pandas DataFrame and save as Parquet
            # The dataset contains 'pixels', 'label', 'user_id', 'segment_id'
            df = dataset.to_pandas()
            df.to_parquet(parquet_path, index=False)
            
            # Generate checksum
            checksum = _compute_sha256(parquet_path)
            _generate_checksum_file(parquet_path, checksum, checksum_path)
            
            logger.info(f"FEMNIST dataset successfully downloaded and saved to {parquet_path}")
            logger.info(f"Checksum: {checksum}")
            
            return parquet_path
            
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt} failed: {e}")
            
            if attempt < max_retries:
                # Exponential backoff: 2^attempt seconds
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} attempts failed.")
    
    # If we reach here, all retries failed
    raise DataFetchError(
        f"Failed to download FEMNIST dataset after {max_retries} attempts. "
        f"Last error: {last_exception}"
    ) from last_exception

def download_shakespeare(output_dir: Optional[Path] = None) -> Path:
    """
    Attempt to download Shakespeare dataset.
    
    This function is a stub that raises an error because Shakespeare
    is excluded per plan.md Gap Analysis (no verified source).
    
    Args:
        output_dir: Directory to save data (unused).
        
    Raises:
        ValueError: Always raised as Shakespeare is excluded.
    """
    _verify_source("shakespeare")
    # This line is unreachable due to _verify_source raising ValueError
    raise DataFetchError("Shakespeare dataset download is not implemented.")

def download_dataset(dataset_name: str, output_dir: Optional[Path] = None) -> Path:
    """
    Generic download function that routes to specific dataset downloaders.
    
    Args:
        dataset_name: Name of the dataset ('femnist' or 'shakespeare').
        output_dir: Directory to save the downloaded data.
        
    Returns:
        Path to the downloaded file.
        
    Raises:
        ValueError: If dataset is not supported.
        DataFetchError: If download fails.
    """
    if dataset_name.lower() == "femnist":
        return download_femnist(output_dir)
    elif dataset_name.lower() == "shakespeare":
        return download_shakespeare(output_dir)
    else:
        _verify_source(dataset_name)
        # Unreachable, but satisfies type checker
        raise ValueError(f"Unknown dataset: {dataset_name}")