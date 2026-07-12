import os
import csv
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_data_processed_dir, get_data_raw_dir
from utils.logging_config import get_logger
from utils.error_handlers import DataValidationError

logger = get_logger(__name__)


def calculate_md5(file_path: str) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def save_raw_data_with_checksums(
    data: List[Dict[str, Any]],
    output_filename: str = "solder_hardness_raw.csv",
    checksum_filename: str = "checksums.txt"
) -> str:
    """
    Save raw data to CSV and generate checksums.
    Returns the path to the saved CSV file.
    """
    raw_dir = get_data_raw_dir()
    raw_dir.mkdir(parents=True, exist_ok=True)

    output_path = raw_dir / output_filename
    checksum_path = raw_dir / checksum_filename

    logger.info(f"Saving raw data to {output_path}")

    if not data:
        raise DataValidationError("Cannot save empty dataset.")

    # Determine headers from the first row
    headers = list(data[0].keys())

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

    # Calculate and save checksum
    checksum = calculate_md5(str(output_path))
    with open(checksum_path, 'w', encoding='utf-8') as f:
        f.write(f"{checksum}  {output_filename}\n")

    logger.info(f"Saved {len(data)} rows to {output_path}")
    logger.info(f"Checksum: {checksum}")

    return str(output_path)


def save_validated_data(
    data: List[Dict[str, Any]],
    output_filename: str = "solder_hardness_validated.csv"
) -> str:
    """
    Save validated data to the processed directory.
    This function implements T016: Save validated dataset.
    """
    processed_dir = get_data_processed_dir()
    processed_dir.mkdir(parents=True, exist_ok=True)

    output_path = processed_dir / output_filename

    logger.info(f"Saving validated data to {output_path}")

    if not data:
        raise DataValidationError("Cannot save empty validated dataset.")

    # Determine headers from the first row
    headers = list(data[0].keys())

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

    logger.info(f"Saved {len(data)} validated rows to {output_path}")

    return str(output_path)


def main():
    """
    Entry point for the saver module.
    This function is intended to be called by the pipeline orchestrator.
    For T016, it ensures the validated data saving capability is ready.
    """
    logger.info("Saver module initialized.")
    # In a real pipeline, this would receive data from the validator
    # and call save_validated_data().
    # For now, we log the capability.
    processed_dir = get_data_processed_dir()
    logger.info(f"Output directory for validated data: {processed_dir}")


if __name__ == "__main__":
    main()
