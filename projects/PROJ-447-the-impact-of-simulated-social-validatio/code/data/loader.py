"""
Real data loading module.

This module attempts to fetch real datasets from external sources.
It raises a DataLoadError on failure and does NOT fall back to synthetic data.
"""

import os
import logging
from typing import Optional, Dict, Any
import pandas as pd

from utils.exceptions import DataLoadError
from utils.logger import get_logger, log_data_load_start, log_data_load_success, log_data_load_error

logger = get_logger(__name__)


def load_real_data(
    source_url: Optional[str] = None,
    file_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Attempt to load real data from a specified source.

    Args:
        source_url: URL to fetch data from (if not using local file).
        file_path: Path to a local CSV file (if not fetching from URL).

    Returns:
        DataFrame containing the loaded data.

    Raises:
        DataLoadError: If data cannot be loaded from any source.
    """
    log_data_load_start()

    data = None

    # Priority 1: Try local file if provided
    if file_path and os.path.exists(file_path):
        try:
            logger.info(f"Loading data from local file: {file_path}")
            data = pd.read_csv(file_path)
            log_data_load_success(file_path)
            return data
        except Exception as e:
            log_data_load_error(f"Failed to read local file {file_path}: {e}")
            # Continue to try other sources

    # Priority 2: Try fetching from URL
    if source_url:
        try:
            logger.info(f"Attempting to fetch data from: {source_url}")
            # Attempt to fetch via pandas read_csv (supports HTTP)
            data = pd.read_csv(source_url)
            log_data_load_success(source_url)
            return data
        except Exception as e:
            error_msg = f"DataLoadError: Failed to fetch real dataset from {source_url}. Error: {e}"
            log_data_load_error(error_msg)
            raise DataLoadError(error_msg) from e

    # If neither source worked, raise error
    error_msg = "DataLoadError: No valid data source provided or accessible. " \
                "Neither local file nor URL fetch succeeded."
    log_data_load_error(error_msg)
    raise DataLoadError(error_msg)


def main() -> None:
    """
    Main entry point for data loading.
    Attempts to load real data and prints result or error.
    """
    logger.info("Executing main() for data loader")

    # Example: Try loading from a known public dataset URL or local file
    # Replace with actual project data source if available
    # For now, we demonstrate the failure mode as real data is not guaranteed
    try:
        # Attempt to load from a hypothetical real source
        # In a real scenario, this would be a verified URL or path
        df = load_real_data(
            source_url="https://raw.githubusercontent.com/your-repo/real-data.csv",
            file_path=None
        )
        print(f"Successfully loaded {len(df)} rows.")
    except DataLoadError as e:
        print(f"Data loading failed as expected: {e}")
        # This is the expected behavior when no real data is available


if __name__ == "__main__":
    main()
