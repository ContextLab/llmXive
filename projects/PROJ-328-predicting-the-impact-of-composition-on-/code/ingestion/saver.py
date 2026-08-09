"""
Saver module for ingestion pipeline.
Handles saving raw and validated datasets with checksums.
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
from utils.error_handlers import DataValidationError

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
    output_filename: str = "solder_hardness_raw.csv"
) -> Path:
    """
    Save raw data to CSV and generate checksum.

    Args:
        data: List of dictionaries representing raw records
        output_filename: Name of the output file

    Returns:
        Path to the saved file
    """
    if not data:
        raise DataValidationError("Cannot save empty raw dataset")

    init_reproducibility()
    output_dir = get_data_raw_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_filename

    logger.info(f"Saving {len(data)} raw records to {output_path}")

    # Write CSV
    if data:
        fieldnames = list(data[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    # Calculate checksum
    checksum = calculate_md5(output_path)
    checksum_path = output_dir.parent / "checksums.txt"
    
    with open(checksum_path, 'a', encoding='utf-8') as f:
        f.write(f"{output_filename}:{checksum}\n")

    logger.info(f"Raw data saved with checksum: {checksum}")
    return output_path


def save_validated_data(
    data: List[Dict[str, Any]],
    status_info: Optional[Dict[str, Any]] = None,
    output_filename: str = "solder_hardness_validated.csv"
) -> Path:
    """
    Save validated data to CSV.
    Also updates the ingestion status file if provided.

    Args:
        data: List of dictionaries representing validated records
        status_info: Optional dictionary containing ingestion status
        output_filename: Name of the output file

    Returns:
        Path to the saved file
    """
    if not data:
        raise DataValidationError("Cannot save empty validated dataset")

    init_reproducibility()
    output_dir = get_data_processed_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_filename

    logger.info(f"Saving {len(data)} validated records to {output_path}")

    # Write CSV
    if data:
        fieldnames = list(data[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

    # Update status file if provided
    if status_info:
        status_path = output_dir / ".ingestion_status.json"
        import json
        with open(status_path, 'w', encoding='utf-8') as f:
            json.dump(status_info, f, indent=2)
        logger.info(f"Updated ingestion status at {status_path}")

    logger.info(f"Validated data saved successfully")
    return output_path


def main():
    """
    Main entry point for the saver module.
    This is a utility module; actual saving is done by the pipeline runner.
    """
    logger.info("Saver module loaded. Use save_raw_data_with_checksums or save_validated_data.")
    return 0
