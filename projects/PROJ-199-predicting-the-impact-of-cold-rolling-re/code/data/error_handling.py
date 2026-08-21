"""
Error handling utilities for EBSD data processing pipeline.

This module provides functions to validate reduction levels, check file integrity,
and handle missing or corrupted data gracefully while logging appropriate warnings.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

from config import get_reductions, ConfigurationError
from utils.logging import get_logger


logger = get_logger(__name__)


def validate_reduction_levels(
    file_reduction: str,
    required_reductions: Optional[List[float]] = None
) -> Tuple[bool, str]:
    """
    Validate that a file's reduction level is in the allowed list.

    Args:
        file_reduction: The reduction level extracted from the filename or metadata.
        required_reductions: List of allowed reduction levels. If None, reads from config.

    Returns:
        Tuple of (is_valid, message)
    """
    if required_reductions is None:
        try:
            required_reductions = get_reductions()
        except ConfigurationError as e:
            logger.error(f"Failed to load reduction levels from config: {e}")
            return False, str(e)

    if not required_reductions:
        error_msg = "No valid reduction levels found in configuration."
        logger.error(error_msg)
        return False, error_msg

    try:
        reduction_value = float(file_reduction)
    except (ValueError, TypeError):
        error_msg = f"Invalid reduction level format: '{file_reduction}'. Expected numeric value."
        logger.warning(error_msg)
        return False, error_msg

    if reduction_value not in required_reductions:
        warning_msg = (
            f"Reduction level {reduction_value} not in allowed list: {required_reductions}. "
            "This file will be skipped."
        )
        logger.warning(warning_msg)
        return False, warning_msg

    logger.debug(f"Reduction level {reduction_value} validated successfully.")
    return True, "Valid reduction level"


def check_file_integrity(file_path: Path) -> Tuple[bool, str]:
    """
    Check if a file exists and is readable.

    Args:
        file_path: Path to the file to check.

    Returns:
        Tuple of (is_valid, message)
    """
    if not file_path.exists():
        error_msg = f"File not found: {file_path}"
        logger.error(error_msg)
        return False, error_msg

    if not file_path.is_file():
        error_msg = f"Path is not a file: {file_path}"
        logger.error(error_msg)
        return False, error_msg

    try:
        # Attempt to open the file to verify readability
        if file_path.suffix.lower() == '.csv':
            pd.read_csv(file_path, nrows=1)
        elif file_path.suffix.lower() in ['.parquet', '.pq']:
            pd.read_parquet(file_path)
        else:
            # Generic read attempt for other formats
            with open(file_path, 'r') as f:
                f.read(1)

        logger.debug(f"File integrity check passed: {file_path}")
        return True, "File is valid and readable"
    except Exception as e:
        error_msg = f"File corruption or read error: {file_path}. Error: {str(e)}"
        logger.warning(error_msg)
        return False, error_msg


def handle_corrupted_file(file_path: Path, error: Exception) -> Dict[str, Any]:
    """
    Handle a corrupted file by logging the error and returning a skip status.

    Args:
        file_path: Path to the corrupted file.
        error: The exception raised during processing.

    Returns:
        Dict with status and details about the skipped file.
    """
    warning_msg = (
        f"Skipping corrupted file {file_path.name}: {str(error)}"
    )
    logger.warning(warning_msg)

    return {
        "status": "skipped",
        "file": str(file_path),
        "reason": f"Corrupted: {str(error)}",
        "action": "File excluded from processing"
    }


def handle_missing_reduction(file_path: Path, file_reduction: str) -> Dict[str, Any]:
    """
    Handle a file with a missing or invalid reduction level.

    Args:
        file_path: Path to the file.
        file_reduction: The invalid or missing reduction value.

    Returns:
        Dict with status and details about the skipped file.
    """
    warning_msg = (
        f"Skipping file {file_path.name}: Missing or invalid reduction level '{file_reduction}'. "
        "Ensure reduction levels are defined in code/config.py."
    )
    logger.warning(warning_msg)

    return {
        "status": "skipped",
        "file": str(file_path),
        "reason": f"Missing/Invalid reduction: {file_reduction}",
        "action": "File excluded from processing"
    }


def process_with_error_handling(
    file_paths: List[Path],
    processor_func,
    **processor_kwargs
) -> Tuple[List[pd.DataFrame], List[Dict[str, Any]]]:
    """
    Process a list of files with robust error handling.

    This function iterates through file paths, validates reduction levels,
    checks file integrity, and processes valid files. It logs warnings for
    skipped files and returns both successful results and error logs.

    Args:
        file_paths: List of file paths to process.
        processor_func: Function to call for each valid file. Should accept
                        the file path and any additional kwargs.
        **processor_kwargs: Additional arguments to pass to processor_func.

    Returns:
        Tuple of (list of successful DataFrames, list of error logs)
    """
    results = []
    errors = []

    for file_path in file_paths:
        logger.info(f"Processing: {file_path.name}")

        # Step 1: Check file integrity
        is_valid, msg = check_file_integrity(file_path)
        if not is_valid:
            error_log = handle_corrupted_file(file_path, Exception(msg))
            errors.append(error_log)
            continue

        # Step 2: Extract and validate reduction level
        # Assuming reduction is part of filename or metadata; adjust logic as needed
        file_reduction = file_path.stem.split('_')[-1] if '_' in file_path.stem else None

        if file_reduction is None:
            error_log = handle_missing_reduction(file_path, "Unknown")
            errors.append(error_log)
            continue

        is_valid, msg = validate_reduction_levels(file_reduction)
        if not is_valid:
            error_log = handle_missing_reduction(file_path, file_reduction)
            errors.append(error_log)
            continue

        # Step 3: Process the file
        try:
            result = processor_func(file_path, **processor_kwargs)
            if result is not None:
                results.append(result)
                logger.info(f"Successfully processed: {file_path.name}")
        except Exception as e:
            error_log = handle_corrupted_file(file_path, e)
            errors.append(error_log)
            logger.exception(f"Unexpected error processing {file_path.name}")

    return results, errors


def main():
    """
    Main entry point for error handling module demonstration.
    """
    setup_logging()
    logger.info("Starting error handling module demonstration.")

    # Example usage
    sample_paths = [
        Path("data/raw/sample_10.csv"),
        Path("data/raw/sample_20.csv"),
        Path("data/raw/missing_reduction.csv"),
        Path("data/raw/corrupted.csv"),
    ]

    def dummy_processor(path, **kwargs):
        logger.info(f"Dummy processing {path.name}")
        return pd.DataFrame({"dummy": [1, 2, 3]})

    results, errors = process_with_error_handling(
        sample_paths,
        dummy_processor
    )

    logger.info(f"Processed {len(results)} files successfully.")
    logger.info(f"Skipped {len(errors)} files due to errors.")

    for err in errors:
        logger.warning(f"Skipped: {err['file']} - {err['reason']}")


if __name__ == "__main__":
    main()