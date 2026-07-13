"""
Saver: Handles saving data with checksums.
"""
import os
import csv
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from seed import init_reproducibility
from config import get_data_raw_dir, get_data_processed_dir
from utils.logging_config import get_logger

logger = get_logger(__name__)


def calculate_md5(file_path: Path) -> str:
    """
    Calculates the MD5 checksum of a file.
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def save_raw_data_with_checksums(df: pd.DataFrame, output_path: Path, checksum_path: Path):
    """
    Saves raw data and its checksum.
    """
    df.to_csv(output_path, index=False)
    checksum = calculate_md5(output_path)
    with open(checksum_path, 'w') as f:
        f.write(f"{checksum}  {output_path.name}\n")
    logger.info(f"Saved raw data to {output_path} with checksum {checksum}")


def save_validated_data(df: pd.DataFrame, output_path: Path):
    """
    Saves validated data.
    """
    df.to_csv(output_path, index=False)
    logger.info(f"Saved validated data to {output_path}")


def main():
    """
    Entry point for the saver.
    """
    logger.info("Starting Saver...")
    # This module is typically called by the pipeline_runner or individual scripts
    # after data has been processed.
    logger.info("Saver module loaded.")

if __name__ == "__main__":
    main()
