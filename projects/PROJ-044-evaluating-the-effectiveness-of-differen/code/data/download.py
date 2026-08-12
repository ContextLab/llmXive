"""
Data download module for FEMNIST dataset.

Implements robust downloading, conversion to Parquet, and checksum generation
for the FEMNIST dataset from Hugging Face.
"""

import time
import hashlib
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

import pandas as pd
from datasets import load_dataset

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Custom exception for data fetching failures."""
    pass

def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA256 checksum of a file.

    Args:
        file_path: Path to the file to checksum.

    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def generate_checksum_file(file_path: Path, checksum_path: Path) -> None:
    """
    Generate a checksum file for a given file.

    Args:
        file_path: Path to the file to checksum.
        checksum_path: Path where the checksum file will be written.
    """
    checksum = compute_sha256(file_path)
    with open(checksum_path, "w") as f:
        f.write(f"{checksum}  {file_path.name}\n")
    logger.info(f"Generated checksum file: {checksum_path}")

def download_femnist(output_dir: Path, max_retries: int = 3) -> Path:
    """
    Download FEMNIST dataset from Hugging Face, convert to Parquet, and generate checksum.

    Args:
        output_dir: Directory where the parquet file and checksum will be saved.
        max_retries: Maximum number of retry attempts.

    Returns:
        Path to the downloaded Parquet file.

    Raises:
        DataFetchError: If download fails after max retries or dataset is unavailable.
        ValueError: If an unsupported dataset is requested.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = output_dir / "femnist.parquet"
    checksum_path = output_dir / "femnist.sha256"

    # If file already exists and checksum is valid, skip download
    if parquet_path.exists() and checksum_path.exists():
        logger.info(f"File {parquet_path} already exists. Verifying checksum...")
        current_checksum = compute_sha256(parquet_path)
        with open(checksum_path, "r") as f:
            stored_checksum = f.read().split()[0]
        
        if current_checksum == stored_checksum:
            logger.info("Checksum verified. Using existing file.")
            return parquet_path
        else:
            logger.warning("Checksum mismatch. Re-downloading...")

    dataset_name = "leaf/femnist"
    logger.info(f"Attempting to download dataset: {dataset_name}")

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Download attempt {attempt}/{max_retries}")
            
            # Load the dataset from Hugging Face
            # Using streaming to handle large datasets efficiently
            dataset = load_dataset(dataset_name, split="train", streaming=True)
            
            # Convert to pandas DataFrame
            # We need to materialize a batch or the whole dataset if it fits in memory
            # For FEMNIST, we'll iterate and build chunks to avoid OOM
            chunks: List[pd.DataFrame] = []
            batch_size = 10000  # Process in batches
            batch = []
            
            logger.info("Converting dataset to pandas DataFrame...")
            for idx, sample in enumerate(dataset):
                batch.append(sample)
                if len(batch) >= batch_size:
                    chunks.append(pd.DataFrame(batch))
                    batch = []
                
                if (idx + 1) % 50000 == 0:
                    logger.info(f"Processed {idx + 1} samples...")
            
            # Add remaining samples
            if batch:
                chunks.append(pd.DataFrame(batch))
            
            if not chunks:
                raise DataFetchError("No data retrieved from dataset.")
            
            # Concatenate all chunks
            df = pd.concat(chunks, ignore_index=True)
            logger.info(f"Total samples loaded: {len(df)}")
            
            # Save to Parquet
            logger.info(f"Saving to Parquet: {parquet_path}")
            df.to_parquet(parquet_path, index=False)
            
            # Generate checksum
            generate_checksum_file(parquet_path, checksum_path)
            
            logger.info(f"Successfully downloaded and saved FEMNIST to {parquet_path}")
            return parquet_path

        except Exception as e:
            logger.warning(f"Attempt {attempt} failed: {str(e)}")
            if attempt < max_retries:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                raise DataFetchError(
                    f"Failed to download FEMNIST dataset after {max_retries} attempts. "
                    f"Last error: {str(e)}. Please check your internet connection and "
                    f"ensure the dataset 'leaf/femnist' is available on Hugging Face."
                ) from e

    raise DataFetchError("Download failed after all retry attempts.")

def download_shakespeare(output_dir: Path, max_retries: int = 3) -> Path:
    """
    Attempt to download Shakespeare dataset.
    
    Note: This dataset is excluded per plan.md Gap Analysis (no verified source).
    
    Args:
        output_dir: Directory for output.
        max_retries: Maximum retry attempts.
    
    Raises:
        ValueError: Always raised as Shakespeare is excluded.
    """
    raise ValueError(
        "Shakespeare dataset is excluded per plan.md Gap Analysis (no verified source). "
        "Only FEMNIST is supported for this project."
    )

def download_dataset(dataset_name: str, output_dir: Path, max_retries: int = 3) -> Path:
    """
    Generic download function that routes to specific dataset handlers.
    
    Args:
        dataset_name: Name of the dataset ("femnist" or "shakespeare").
        output_dir: Directory for output.
        max_retries: Maximum retry attempts.
    
    Returns:
        Path to the downloaded file.
    
    Raises:
        ValueError: If dataset_name is not supported.
        DataFetchError: If download fails.
    """
    if dataset_name.lower() == "femnist":
        return download_femnist(output_dir, max_retries)
    elif dataset_name.lower() == "shakespeare":
        return download_shakespeare(output_dir, max_retries)
    else:
        raise ValueError(
            f"Unsupported dataset: {dataset_name}. "
            f"Supported datasets: 'femnist'. "
            f"Shakespeare is excluded per plan.md."
        )

def main():
    """Main entry point for downloading FEMNIST."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download FEMNIST dataset")
    parser.add_argument(
        "--output-dir", 
        type=Path, 
        default="data/raw",
        help="Output directory for downloaded data"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="femnist",
        help="Dataset name (default: femnist)"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retry attempts (default: 3)"
    )
    
    args = parser.parse_args()
    
    try:
        output_path = download_dataset(
            dataset_name=args.dataset,
            output_dir=args.output_dir,
            max_retries=args.max_retries
        )
        print(f"Success! Data saved to: {output_path}")
        return 0
    except (DataFetchError, ValueError) as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())