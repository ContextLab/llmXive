import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
from datasets import load_dataset

from utils import setup_logging, init_random_seed, get_logger

def calculate_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """Calculate the checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """Verify the checksum of a file against an expected value."""
    actual_checksum = calculate_checksum(file_path, algorithm)
    return actual_checksum == expected_checksum

def fetch_tox21_dataset(
    output_dir: str,
    dataset_name: str = "deepchem/tox21",
) -> Tuple[pd.DataFrame, str]:
    """
    Fetch the Tox21 dataset from HuggingFace and save it locally.

    Args:
        output_dir: Directory to save the dataset.
        dataset_name: Name of the dataset on HuggingFace.

    Returns:
        Tuple of (DataFrame with dataset, path to saved file).
    """
    logger = get_logger(__name__)
    output_path = Path(output_dir) / "tox21_raw.csv"

    if output_path.exists():
        logger.info(f"Dataset already exists at {output_path}. Skipping download.")
        return pd.read_csv(output_path), str(output_path)

    logger.info(f"Downloading dataset: {dataset_name}")
    try:
        dataset = load_dataset(dataset_name, split="train")
        df = dataset.to_pandas()
        df.to_csv(output_path, index=False)
        logger.info(f"Dataset saved to {output_path}")
        return df, str(output_path)
    except Exception as e:
        logger.error(f"Failed to download dataset: {e}")
        raise

def main():
    """Main entry point for downloading the dataset."""
    setup_logging()
    init_random_seed()
    logger = get_logger(__name__)

    # Define paths
    data_dir = Path("data/raw")
    data_dir.mkdir(parents=True, exist_ok=True)
    output_file = data_dir / "tox21_raw.csv"

    logger.info("Starting dataset download...")

    # Fetch dataset
    df, _ = fetch_tox21_dataset(str(data_dir))

    # Log download size
    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    logger.info(f"Download size: {file_size_mb:.2f} MB")

    # Log initial row count
    logger.info(f"Initial dataset size: {len(df)} rows")
    logger.info(f"Columns: {list(df.columns)}")

    # Log endpoint distribution (count of non-null values per toxicity endpoint)
    # Assuming toxicity endpoints are columns that are not 'smiles' or 'mol'
    endpoint_cols = [col for col in df.columns if col not in ['smiles', 'mol']]
    endpoint_counts = df[endpoint_cols].notna().sum()
    logger.info("Endpoint distribution (non-null counts):")
    for col, count in endpoint_counts.items():
        logger.info(f"  {col}: {count}")

    logger.info("Dataset download and logging complete.")

if __name__ == "__main__":
    main()
