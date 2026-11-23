"""
Data download and subsetting utilities for the Moral Machine dataset.

This module handles fetching the raw Moral Machine data, verifying checksums,
and creating a stratified subset for efficient processing.
"""
import os
import sys
import hashlib
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

# Configure logging
logger = logging.getLogger(__name__)

# Constants
MORAL_MACHINE_URL = "https://raw.githubusercontent.com/robinlovelace/moral-machine/master/moral_machine.csv"
CHECKSUM_URL = "https://raw.githubusercontent.com/robinlovelace/moral-machine/master/moral_machine.csv.sha256"
RAW_DATA_DIR = Path("data/raw")
OUTPUT_FILE = RAW_DATA_DIR / "moral_machine_subset.csv"
MAX_ROWS = 50000
RANDOM_SEED = 42
STRATIFY_COLUMNS = ["outcome", "species"]


def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """Verify the SHA256 checksum of a file."""
    computed = compute_file_sha256(file_path)
    return computed.lower() == expected_checksum.lower().strip()


def download_from_url(url: str, dest_path: Path, timeout: int = 300) -> Path:
    """
    Download a file from a URL to a local path.

    Args:
        url: The URL to download from.
        dest_path: The local path to save the file.
        timeout: Request timeout in seconds.

    Returns:
        The path to the downloaded file.

    Raises:
        RuntimeError: If the download fails or the file cannot be written.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Downloading {url} to {dest_path}...")

    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 Kibibyte

        with open(dest_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        logger.debug(f"Download progress: {progress:.2f}%")

        logger.info(f"Download complete: {dest_path} ({downloaded} bytes)")
        return dest_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download from {url}: {e}")
        raise RuntimeError(f"Download failed: {e}")


def download_moral_machine_data() -> Path:
    """
    Download the full Moral Machine dataset and verify its checksum.

    Returns:
        Path to the downloaded raw CSV file.
    """
    raw_file = RAW_DATA_DIR / "moral_machine_full.csv"

    if raw_file.exists():
        logger.info(f"Raw data already exists at {raw_file}. Skipping download.")
        # Verify checksum if possible, otherwise assume valid
        try:
            # Attempt to fetch checksum for verification
            checksum_resp = requests.get(CHECKSUM_URL, timeout=30)
            if checksum_resp.status_code == 200:
                expected_checksum = checksum_resp.text.strip()
                if verify_checksum(raw_file, expected_checksum):
                    logger.info("Checksum verification passed.")
                else:
                    logger.warning("Checksum mismatch. Re-downloading...")
                    raw_file.unlink()
                return raw_file
        except Exception as e:
            logger.warning(f"Could not verify checksum: {e}")

    download_from_url(MORAL_MACHINE_URL, raw_file)
    return raw_file


def subset_csv(
    input_path: Path,
    output_path: Path,
    max_rows: int = MAX_ROWS,
    seed: int = RANDOM_SEED,
    stratify_cols: list = None
) -> Path:
    """
    Load a CSV, perform stratified sampling, and save the subset.

    This function ensures the output contains exactly `max_rows` (or fewer if
    the dataset is smaller) rows, maintaining the distribution of the
    specified stratification columns.

    Args:
        input_path: Path to the input CSV.
        output_path: Path to save the subset CSV.
        max_rows: Maximum number of rows to keep.
        seed: Random seed for reproducibility.
        stratify_cols: List of column names to use for stratification.

    Returns:
        Path to the output subset CSV.
    """
    if stratify_cols is None:
        stratify_cols = STRATIFY_COLUMNS

    logger.info(f"Loading {input_path}...")
    df = pd.read_csv(input_path)
    total_rows = len(df)
    logger.info(f"Loaded {total_rows} rows.")

    if total_rows <= max_rows:
        logger.warning(f"Dataset ({total_rows} rows) is smaller than target ({max_rows}). Saving full dataset.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        return output_path

    # Check if stratification columns exist
    missing_cols = [col for col in stratify_cols if col not in df.columns]
    if missing_cols:
        logger.warning(f"Stratification columns {missing_cols} not found. Falling back to random sampling.")
        df_sample = df.sample(n=max_rows, random_state=seed)
    else:
        # Filter out rows with missing values in stratification columns to avoid errors
        df_clean = df.dropna(subset=stratify_cols)
        if len(df_clean) < max_rows:
            logger.warning(f"Cleaned dataset ({len(df_clean)} rows) is smaller than target. Saving all clean rows.")
            df_sample = df_clean
        else:
            # Stratified sample
            # We need to sample n=max_rows from the whole dataframe, preserving ratios
            # sklearn's train_test_split is perfect for this
            _, df_sample = train_test_split(
                df_clean,
                train_size=max_rows,
                random_state=seed,
                stratify=df_clean[stratify_cols]
            )
            logger.info(f"Stratified sampling completed. Selected {len(df_sample)} rows.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_sample.to_csv(output_path, index=False)
    logger.info(f"Subset saved to {output_path} ({len(df_sample)} rows).")
    return output_path


def main():
    """Main entry point for the download and subsetting pipeline."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Step 1: Download full data
        raw_path = download_moral_machine_data()

        # Step 2: Subset the data
        subset_path = subset_csv(
            input_path=raw_path,
            output_path=OUTPUT_FILE,
            max_rows=MAX_ROWS,
            seed=RANDOM_SEED,
            stratify_cols=STRATIFY_COLUMNS
        )

        logger.info(f"Pipeline complete. Output: {subset_path}")
        return 0

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
