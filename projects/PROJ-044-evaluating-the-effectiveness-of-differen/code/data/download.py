"""
Data download module for FED-LEAF datasets.

Implements robust downloading of FEMNIST dataset from Hugging Face with
checksum verification and retry logic.
"""

import time
import hashlib
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from datasets import load_dataset
import pandas as pd

# Import checksum utilities from sibling module
from code.data.checksum_utils import compute_sha256, generate_checksum_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataFetchError(Exception):
    """Custom exception for data fetching failures."""
    pass


def download_femnist(output_dir: Path, max_retries: int = 3) -> Path:
    """
    Download FEMNIST dataset from Hugging Face and save as parquet.
    
    Args:
        output_dir: Directory to save the downloaded data
        max_retries: Maximum number of retry attempts with exponential backoff
    
    Returns:
        Path to the downloaded parquet file
    
    Raises:
        DataFetchError: If download fails after all retries
        ValueError: If dataset name is not "femnist"
    """
    dataset_name = "leaf/femnist"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    parquet_path = output_dir / "femnist.parquet"
    checksum_path = output_dir / "femnist.sha256"
    
    # Check if already downloaded and valid
    if parquet_path.exists() and checksum_path.exists():
        logger.info(f"Verifying existing FEMNIST download...")
        if compute_sha256(parquet_path) == Path(checksum_path).read_text().strip():
            logger.info("Existing download verified successfully.")
            return parquet_path
        else:
            logger.warning("Existing checksum mismatch, re-downloading...")
    
    attempt = 0
    last_exception = None
    
    while attempt < max_retries:
        try:
            logger.info(f"Downloading {dataset_name} (attempt {attempt + 1}/{max_retries})...")
            
            # Load dataset from Hugging Face with streaming to handle large size
            # FEMNIST is large (~7GB+), so we stream and process in chunks
            dataset = load_dataset(dataset_name, split="train", streaming=True)
            
            # Convert to pandas and save as parquet
            # Since FEMNIST is large, we process it in batches
            logger.info("Processing dataset chunks...")
            
            # FEMNIST structure: images are stored as 'pixels' (list of ints), labels as 'label'
            # We need to convert to a format suitable for parquet
            chunks = []
            batch_size = 1000  # Process in batches to manage memory
            
            batch_count = 0
            for batch in dataset.iter(batch_size=batch_size):
                # Convert batch to DataFrame
                # batch is a dict with 'pixels' (list of lists) and 'label' (list)
                df_batch = pd.DataFrame({
                    'pixels': batch['pixels'],
                    'label': batch['label']
                })
                chunks.append(df_batch)
                batch_count += 1
                
                if batch_count % 10 == 0:
                    logger.info(f"Processed {batch_count} batches ({batch_count * batch_size} samples)")
            
            # Concatenate all chunks
            logger.info(f"Concatenating {len(chunks)} chunks...")
            df = pd.concat(chunks, ignore_index=True)
            
            # Save to parquet
            logger.info(f"Saving to {parquet_path}...")
            df.to_parquet(parquet_path, index=False)
            
            # Generate checksum
            logger.info("Generating checksum...")
            checksum = compute_sha256(parquet_path)
            generate_checksum_file(parquet_path, checksum_path)
            
            logger.info(f"Successfully downloaded and saved FEMNIST ({len(df)} samples)")
            logger.info(f"Checksum: {checksum}")
            
            return parquet_path
            
        except Exception as e:
            last_exception = e
            attempt += 1
            if attempt < max_retries:
                wait_time = 2 ** attempt  # Exponential backoff: 2s, 4s, 8s
                logger.warning(f"Download failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Download failed after {max_retries} attempts: {e}")
    
    raise DataFetchError(f"Failed to download FEMNIST dataset after {max_retries} attempts. Last error: {last_exception}")


def download_shakespeare(output_dir: Path, max_retries: int = 3) -> Path:
    """
    Download Shakespeare dataset from Hugging Face.
    
    Note: This dataset is excluded per plan.md Gap Analysis (no verified source).
    This function raises ValueError if called.
    
    Args:
        output_dir: Directory to save the downloaded data
        max_retries: Maximum number of retry attempts (unused)
    
    Raises:
        ValueError: Always raises with message about exclusion
    """
    raise ValueError(
        "Shakespeare dataset is excluded per plan.md Gap Analysis (no verified source). "
        "Only FEMNIST is supported for this project."
    )


def download_dataset(dataset_name: str, output_dir: Path, max_retries: int = 3) -> Path:
    """
    Download dataset by name.
    
    Args:
        dataset_name: Name of dataset to download ("femnist" or "shakespeare")
        output_dir: Directory to save the downloaded data
        max_retries: Maximum number of retry attempts
    
    Returns:
        Path to the downloaded parquet file
    
    Raises:
        ValueError: If dataset_name is not "femnist"
        DataFetchError: If download fails
    """
    dataset_name_lower = dataset_name.lower()
    
    if dataset_name_lower == "femnist":
        return download_femnist(output_dir, max_retries)
    elif dataset_name_lower == "shakespeare":
        return download_shakespeare(output_dir, max_retries)
    else:
        raise ValueError(
            f"Unsupported dataset: {dataset_name}. "
            f"Only 'femnist' is supported for this project."
        )


def main():
    """Main entry point for downloading FEMNIST dataset."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download FEMNIST dataset")
    parser.add_argument(
        "--dataset",
        type=str,
        default="femnist",
        help="Dataset name (default: femnist)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Output directory (default: data/raw)"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retry attempts (default: 3)"
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    
    try:
        result_path = download_dataset(
            dataset_name=args.dataset,
            output_dir=output_dir,
            max_retries=args.max_retries
        )
        logger.info(f"Download complete: {result_path}")
    except (DataFetchError, ValueError) as e:
        logger.error(f"Download failed: {e}")
        raise


if __name__ == "__main__":
    main()
