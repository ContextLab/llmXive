"""
Saver module for the solder hardness ingestion pipeline.
Handles saving raw and validated datasets with checksums.
"""
import os
import csv
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_data_raw_dir, get_data_processed_dir
from utils.logging_config import get_logger
from seed import init_reproducibility

logger = get_logger(__name__)


def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def save_raw_data_with_checksums(
    data: List[Dict[str, Any]],
    output_path: Path,
    checksums_path: Path
) -> None:
    """
    Save raw data to CSV and generate MD5 checksums.

    Args:
        data: List of dictionaries representing raw solder composition records.
        output_path: Path to save the raw CSV file.
        checksums_path: Path to save the checksums text file.
    """
    if not data:
        logger.warning("No data to save for raw dataset.")
        return

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    fieldnames = list(data[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    logger.info(f"Saved raw data to {output_path} ({len(data)} records)")

    # Calculate and save checksum
    checksum = calculate_md5(output_path)
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksums_path, 'w', encoding='utf-8') as f:
        f.write(f"{output_path.name}: {checksum}\n")
    
    logger.info(f"Saved checksum to {checksums_path}")


def save_validated_data(
    data: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Save validated dataset to CSV.

    Args:
        data: List of dictionaries representing validated solder composition records.
        output_path: Path to save the validated CSV file.
    """
    if not data:
        logger.warning("No data to save for validated dataset.")
        return

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    fieldnames = list(data[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    logger.info(f"Saved validated data to {output_path} ({len(data)} records)")


def main() -> None:
    """
    Main entry point for saving validated data.
    This script expects the validated data to be available from the ingestion pipeline.
    For T016, this function is called by the pipeline runner after validation.
    """
    init_reproducibility()
    
    # This is a stub for the direct execution context.
    # The actual saving logic is invoked by the pipeline_runner or unit tests.
    # If run directly, it assumes data has been processed and passed to save_validated_data.
    logger.info("Saver module initialized. Use save_validated_data() to persist results.")


if __name__ == "__main__":
    main()
