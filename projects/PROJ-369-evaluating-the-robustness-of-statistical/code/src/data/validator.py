"""
Data Validator Module for User Story 1 & 2.

This module implements the synchronization task between data ingestion (T014)
and preprocessing (T015). It verifies that all required raw datasets are present
and valid before any processing begins, ensuring data availability and preventing
partial pipeline execution per Constitution Principle I (Reproducibility).
"""

import os
import logging
from pathlib import Path
from typing import List, Optional

from src.data.sources import get_all_source_names, get_source_info
from src.utils.logging import log_info, log_error, log_critical
from src.utils.config import get_path


class DataValidationError(Exception):
    """Custom exception for data validation failures."""
    pass


def verify_raw_datasets(required_datasets: Optional[List[str]] = None) -> bool:
    """
    Verify that all required raw datasets are present in data/raw/ and have size > 0.

    This function acts as a synchronization barrier between T014 (Download) and
    T015 (Preprocessing). It ensures that the pipeline does not proceed with
    preprocessing if critical data is missing or invalid.

    Args:
        required_datasets: Optional list of specific dataset names to verify.
                           If None, verifies all datasets defined in sources.py.

    Returns:
        True if all datasets are present and valid.

    Raises:
        DataValidationError: If any required dataset is missing or invalid.
        FileNotFoundError: If the data/raw directory does not exist.
    """
    raw_dir = get_path("data_raw")
    if not raw_dir.exists():
        raise FileNotFoundError(
            f"Raw data directory does not exist: {raw_dir}. "
            "Run ingestion (T014) before preprocessing."
        )

    # Determine which datasets to verify
    if required_datasets is None:
        # Verify all datasets defined in sources.py
        all_sources = get_all_source_names()
        # Filter to only those that should be in raw/ (excluding yfinance which might be handled differently)
        # For this implementation, we assume all sources defined in sources.py are expected in raw/
        # unless they are specifically marked as 'streaming' or similar.
        datasets_to_check = all_sources
    else:
        datasets_to_check = required_datasets

    missing_files = []
    invalid_files = []

    log_info(f"Verifying {len(datasets_to_check)} raw datasets in {raw_dir}")

    for dataset_name in datasets_to_check:
        source_info = get_source_info(dataset_name)
        if not source_info:
            log_warning(f"Source info not found for {dataset_name}, skipping check.")
            continue

        # Determine expected file path based on source info
        # The ingestion module typically saves files with a specific naming convention
        # We check for the presence of the primary data file
        expected_filename = source_info.get("expected_filename")
        if not expected_filename:
            # Fallback: use dataset_name as filename (lowercase, no spaces)
            expected_filename = f"{dataset_name.lower().replace(' ', '_')}.csv"

        file_path = raw_dir / expected_filename

        if not file_path.exists():
            missing_files.append(f"{dataset_name}: {file_path}")
            continue

        # Check file size > 0
        if file_path.stat().st_size == 0:
            invalid_files.append(f"{dataset_name}: {file_path} (size=0)")
            continue

        log_info(f"Verified: {dataset_name} -> {file_path} ({file_path.stat().st_size} bytes)")

    if missing_files or invalid_files:
        error_msg = "Raw dataset validation failed:\n"
        if missing_files:
            error_msg += "\nMissing files:\n"
            for item in missing_files:
                error_msg += f"  - {item}\n"
        if invalid_files:
            error_msg += "\nInvalid files (size=0):\n"
            for item in invalid_files:
                error_msg += f"  - {item}\n"

        log_critical(error_msg)
        raise DataValidationError(error_msg)

    log_info("All raw datasets verified successfully.")
    return True


def main() -> int:
    """
    CLI entry point for the data validator.

    This function is invoked by the run-book script `code/scripts/verify_raw_datasets.py`.
    It performs the validation and exits with appropriate status codes.

    Returns:
        0 if validation passes, 1 if validation fails.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    try:
        log_info("Starting raw dataset verification...")
        verify_raw_datasets()
        log_info("Verification successful. Preprocessing can proceed.")
        return 0
    except DataValidationError as e:
        log_critical(f"Data validation failed: {e}")
        return 1
    except FileNotFoundError as e:
        log_critical(f"Directory not found: {e}")
        return 1
    except Exception as e:
        log_critical(f"Unexpected error during verification: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
