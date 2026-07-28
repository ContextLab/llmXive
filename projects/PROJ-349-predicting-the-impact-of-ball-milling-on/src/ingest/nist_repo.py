"""
NIST Repository Downloader for Ball Milling Data.

This module implements the data ingestion from the NIST Search API
using the specific query string required by the project specification.
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

from src.config.settings import get_settings
from src.exceptions import DataIngestionError, InsufficientDataError
from src.utils.logger import get_module_logger

# Configure logger
logger = get_module_logger(__name__)

# Constants
NIST_API_BASE_URL = "https://data.nist.gov/api/v1/sds"
NIST_SEARCH_URL = f"{NIST_API_BASE_URL}/search"
NIST_DOWNLOAD_URL_TEMPLATE = "https://data.nist.gov/api/v1/sds/{id}/content"
OUTPUT_PATH = Path("data/raw/nist_raw.csv")
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30
QUERY_STRING = "q=ball+milling AND datasetType:csv"


def _fetch_search_results(query: str, page: int = 1, page_size: int = 10) -> Optional[Dict[str, Any]]:
    """
    Fetch search results from NIST API.

    Args:
        query: The search query string.
        page: Page number for pagination.
        page_size: Number of results per page.

    Returns:
        JSON response dict or None if failed.
    """
    params = {
        "q": query,
        "page": page,
        "page_size": page_size,
        "format": "json"
    }

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(NIST_SEARCH_URL, params=params, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1} failed for NIST search: {e}")
            if attempt == MAX_RETRIES - 1:
                return None
            time.sleep(2 ** attempt)  # Exponential backoff

    return None


def _get_download_url(dataset_id: str) -> str:
    """
    Construct the download URL for a specific dataset.

    Args:
        dataset_id: The NIST dataset ID.

    Returns:
        The download URL string.
    """
    return NIST_DOWNLOAD_URL_TEMPLATE.format(id=dataset_id)


def _download_dataset(url: str) -> Optional[pd.DataFrame]:
    """
    Download a dataset from the given URL.

    Args:
        url: The download URL.

    Returns:
        DataFrame if successful, None otherwise.
    """
    try:
        response = requests.get(url, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()

        # Try to parse as CSV
        try:
            df = pd.read_csv(pd.io.common.StringIO(response.text))
            return df
        except Exception as csv_error:
            logger.warning(f"Failed to parse as CSV: {csv_error}")
            return None

    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to download dataset from {url}: {e}")
        return None


def _normalize_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize the downloaded DataFrame to match the project schema.

    This function performs basic cleaning and column renaming if necessary.
    It does NOT validate against the full schema (that is handled by T007b).

    Args:
        df: The raw DataFrame.

    Returns:
        A normalized DataFrame.
    """
    if df.empty:
        return df

    # Basic normalization: strip whitespace from column names
    df.columns = df.columns.str.strip()

    # Log column info for debugging
    logger.info(f"Downloaded dataset has {len(df.columns)} columns: {list(df.columns)}")

    return df


def download_data() -> Optional[pd.DataFrame]:
    """
    Main function to download data from NIST repository.

    Returns:
        DataFrame with downloaded data, or None if no valid data found.
    """
    logger.info("Starting NIST data ingestion...")

    # Fetch search results
    search_response = _fetch_search_results(QUERY_STRING, page=1, page_size=10)

    if not search_response:
        logger.warning("Source skipped: NIST (no rows or error)")
        return None

    # Check if results exist
    results = search_response.get("results", [])
    if not results:
        logger.warning("Source skipped: NIST (no rows or error)")
        return None

    logger.info(f"NIST search returned {len(results)} results. Attempting to download the first valid one.")

    # Iterate through results to find a valid dataset
    for result in results:
        dataset_id = result.get("sdsId") or result.get("id")
        if not dataset_id:
            logger.warning(f"Skipping result without ID: {result}")
            continue

        download_url = _get_download_url(dataset_id)
        logger.info(f"Attempting to download dataset: {dataset_id}")

        df = _download_dataset(download_url)

        if df is not None and not df.empty:
            logger.info(f"Successfully downloaded dataset with {len(df)} rows from {dataset_id}")
            return _normalize_schema(df)

        logger.warning(f"Failed to download or parse dataset: {dataset_id}")

    logger.warning("Source skipped: NIST (no valid datasets found)")
    return None


def process_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process the downloaded data (placeholder for future processing).

    Currently, this function just returns the normalized DataFrame.
    Future versions might add type conversions, filtering, etc.

    Args:
        df: The raw DataFrame.

    Returns:
        Processed DataFrame.
    """
    # For now, just return the normalized data
    # Future: Add specific processing logic here
    return df


def save_to_csv(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the DataFrame to a CSV file.

    Args:
        df: The DataFrame to save.
        output_path: The path to save the file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")


def run_nist_ingestion() -> bool:
    """
    Run the full NIST ingestion pipeline.

    Returns:
        True if successful, False otherwise.
    """
    try:
        # Download data
        df = download_data()

        if df is None:
            logger.warning("NIST ingestion skipped: No data downloaded")
            return False

        # Process data
        df_processed = process_data(df)

        if df_processed.empty:
            logger.warning("NIST ingestion skipped: Processed data is empty")
            return False

        # Save to CSV
        save_to_csv(df_processed, OUTPUT_PATH)

        logger.info("NIST ingestion completed successfully")
        return True

    except Exception as e:
        logger.error(f"NIST ingestion failed with error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = run_nist_ingestion()
    exit(0 if success else 1)
