"""
Zenodo API Client for fetching datasets.

This module provides a client to interact with the Zenodo API to fetch datasets
using DOIs. It handles authentication, rate limits, and raises specific errors
when data is unavailable.
"""
import os
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

import requests
from requests.exceptions import RequestException

from config.config import get_config

# Configure logging
logger = logging.getLogger(__name__)

# Zenodo API Base URL
ZENODO_API_URL = "https://zenodo.org/api/records"

# Rate limiting settings (Zenodo allows ~10 requests per second, we use 0.2s to be safe)
RATE_LIMIT_DELAY = 0.2

class DataUnavailableError(Exception):
    """
    Custom exception raised when data cannot be fetched from Zenodo.

    This error is raised when both the primary and fallback DOIs are unreachable
    or return errors.
    """
    pass

def _get_headers() -> Dict[str, str]:
    """
    Get headers for Zenodo API requests.

    Returns:
        Dict[str, str]: Headers including authentication token if available.
    """
    headers = {"Accept": "application/json"}
    token = os.getenv("ZENODO_API_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def _fetch_record(doi: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single record from Zenodo by DOI.

    Args:
        doi: The DOI of the record to fetch.

    Returns:
        Optional[Dict[str, Any]]: The record data if successful, None otherwise.
    """
    # Zenodo API uses the DOI in the path for direct record access
    # Format: https://zenodo.org/api/records?q doi:<DOI> or direct access via DOI
    # Direct access via DOI: https://zenodo.org/api/records/{doi} doesn't work directly
    # We need to search by DOI or use the DOI to construct the correct URL

    # Zenodo's API allows searching by DOI
    search_url = f"{ZENODO_API_URL}?q=doi:{doi}&size=1"

    logger.info(f"Fetching record for DOI: {doi}")

    try:
        response = requests.get(search_url, headers=_get_headers(), timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("hits", {}).get("total", 0) == 0:
            logger.warning(f"No records found for DOI: {doi}")
            return None

        record = data["hits"]["hits"][0]
        logger.info(f"Successfully fetched record for DOI: {doi}")
        return record

    except RequestException as e:
        logger.error(f"Failed to fetch record for DOI {doi}: {e}")
        return None

def _download_files(record: Dict[str, Any], output_dir: Path) -> Optional[str]:
    """
    Download files from a Zenodo record.

    Args:
        record: The Zenodo record data.
        output_dir: Directory to save downloaded files.

    Returns:
        Optional[str]: Path to the downloaded file if successful, None otherwise.
    """
    if not record.get("files"):
        logger.warning("No files found in the record")
        return None

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Zenodo records can have multiple files, we'll download the first one
    # or all files depending on the use case. For now, we download the first CSV.
    file_url = None
    file_name = None

    for file_info in record["files"]:
        if file_info.get("type") == "csv" or file_info.get("name", "").endswith(".csv"):
            file_url = file_info.get("links", {}).get("self")
            file_name = file_info.get("name")
            break

    if not file_url or not file_name:
        # If no CSV found, try the first file
        file_info = record["files"][0]
        file_url = file_info.get("links", {}).get("self")
        file_name = file_info.get("name")

    if not file_url:
        logger.warning("No file URL found in the record")
        return None

    file_path = output_dir / file_name
    logger.info(f"Downloading file: {file_name} to {file_path}")

    try:
        response = requests.get(file_url, stream=True, timeout=300)
        response.raise_for_status()

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Successfully downloaded: {file_name}")
        return str(file_path)

    except RequestException as e:
        logger.error(f"Failed to download file: {e}")
        return None

def fetch_dataset(doi: str, output_dir: Optional[Path] = None) -> str:
    """
    Fetch a dataset from Zenodo using a DOI.

    Args:
        doi: The DOI of the dataset to fetch.
        output_dir: Optional directory to save the downloaded files.
                   Defaults to 'data/raw' relative to project root.

    Returns:
        str: Path to the downloaded file.

    Raises:
        DataUnavailableError: If the dataset cannot be fetched.
    """
    if output_dir is None:
        config = get_config()
        output_dir = Path(config.get("data_dir", "data")) / "raw"

    # Rate limiting
    time.sleep(RATE_LIMIT_DELAY)

    record = _fetch_record(doi)
    if not record:
        raise DataUnavailableError(f"Failed to fetch record for DOI: {doi}")

    downloaded_path = _download_files(record, output_dir)
    if not downloaded_path:
        raise DataUnavailableError(f"Failed to download files for DOI: {doi}")

    return downloaded_path

def fetch_from_zenodo(primary_doi: str, fallback_doi: Optional[str] = None) -> str:
    """
    Fetch a dataset from Zenodo with fallback support.

    Args:
        primary_doi: The primary DOI to fetch.
        fallback_doi: Optional fallback DOI if the primary fails.

    Returns:
        str: Path to the downloaded file.

    Raises:
        DataUnavailableError: If both primary and fallback DOIs fail.
    """
    config = get_config()
    output_dir = Path(config.get("data_dir", "data")) / "raw"

    # Try primary DOI
    try:
        return fetch_dataset(primary_doi, output_dir)
    except DataUnavailableError as e:
        logger.warning(f"Primary DOI failed: {e}")
        if fallback_doi:
            logger.info(f"Attempting fallback DOI: {fallback_doi}")
            try:
                return fetch_dataset(fallback_doi, output_dir)
            except DataUnavailableError as e_fallback:
                logger.error(f"Fallback DOI also failed: {e_fallback}")
                raise DataUnavailableError(
                    f"Both primary ({primary_doi}) and fallback ({fallback_doi}) DOIs are unreachable."
                ) from e_fallback
        else:
            raise

def main():
    """
    Main function to demonstrate Zenodo client usage.
    """
    config = get_config()
    primary_doi = config.get("primary_doi", "10.5281/zenodo.10043838")
    fallback_doi = config.get("fallback_doi", "10.5281/zenodo.11023456")

    try:
        file_path = fetch_from_zenodo(primary_doi, fallback_doi)
        print(f"Successfully downloaded dataset: {file_path}")
    except DataUnavailableError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
