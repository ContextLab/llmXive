"""
Download NIST Corrosion Database (NIST-IR-8200) records.

This script fetches real data from the NIST-IR-8200 repository.
It implements retry logic with exponential backoff and validates
the presence of a configured URL before attempting download.
"""

import os
import time
import requests
import zipfile
import io
from pathlib import Path
from typing import Optional, Dict, Any

# Import from project utilities
from utils.config import get_config, get_path, get_data_path
from utils.exceptions import DataInsufficientError
from utils.logging import get_logger

# Constants
MAX_RETRIES = 5
INITIAL_BACKOFF = 1.0  # seconds
MAX_BACKOFF = 60.0     # seconds
TIMEOUT = 30           # seconds

logger = get_logger(__name__)


def load_verified_dataset_config() -> Dict[str, Any]:
    """
    Load the verified-datasets registry configuration.
    Returns the config dict containing the NIST URL.
    """
    config_manager = get_config()
    # The config is expected to have a 'verified_datasets' section
    # or a specific 'nist_ir_8200' entry. We look for the URL key.
    return config_manager.get_config()


def get_nist_url(config: Dict[str, Any]) -> Optional[str]:
    """
    Extract the NIST-IR-8200 download URL from the configuration.
    """
    # Check for the URL in various expected locations in the config
    # based on standard project structure expectations
    url_keys = [
        'verified_datasets.nist_ir_8200.url',
        'data_sources.nist_ir_8200.url',
        'nist_ir_8200.url'
    ]

    for key in url_keys:
        try:
            parts = key.split('.')
            value = config
            for part in parts:
                value = value[part]
            if isinstance(value, str) and value.strip():
                return value.strip()
        except (KeyError, TypeError):
            continue

    # Fallback: check if a top-level key exists
    if 'nist_url' in config and isinstance(config['nist_url'], str):
        return config['nist_url']

    return None


def download_with_retry(url: str, output_path: Path) -> bool:
    """
    Download the file from URL with exponential backoff retry logic.

    Args:
        url: The download URL.
        output_path: Local path to save the file.

    Returns:
        True if download succeeded, False otherwise.

    Raises:
        DataInsufficientError: If the URL returns 404 or max retries exceeded.
    """
    attempt = 0
    backoff = INITIAL_BACKOFF

    while attempt < MAX_RETRIES:
        try:
            logger.info(f"Attempt {attempt + 1}/{MAX_RETRIES} to download from {url}")
            response = requests.get(url, timeout=TIMEOUT, stream=True)

            if response.status_code == 404:
                logger.error(f"Resource not found (404) at {url}")
                raise DataInsufficientError(
                    f"NIST-IR-8200 data not found at URL: {url}. "
                    "Data acquisition strategy must be updated."
                )

            response.raise_for_status()

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content to file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"Successfully downloaded to {output_path}")
            return True

        except requests.exceptions.RequestException as e:
            attempt += 1
            if attempt >= MAX_RETRIES:
                logger.error(f"Failed to download after {MAX_RETRIES} attempts: {e}")
                raise DataInsufficientError(
                    f"Failed to download NIST data after {MAX_RETRIES} retries. "
                    f"Last error: {e}"
                )
            logger.warning(f"Download attempt {attempt} failed: {e}. Retrying in {backoff:.1f}s...")
            time.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF)

    return False


def main():
    """
    Main entry point for the NIST data download script.
    """
    logger.info("Starting NIST-IR-8200 data download process.")

    # 1. Load configuration
    try:
        config = load_verified_dataset_config()
    except Exception as e:
        logger.error(f"Failed to load project configuration: {e}")
        raise DataInsufficientError("Project configuration is missing or invalid.")

    # 2. Pre-fetch: Check for URL
    nist_url = get_nist_url(config)
    if not nist_url:
        logger.error("NIST-IR-8200 URL is missing from verified-datasets registry.")
        raise DataInsufficientError(
            "NIST-IR-8200 URL is missing from configuration. "
            "Cannot proceed with data acquisition."
        )

    logger.info(f"Found NIST URL: {nist_url}")

    # 3. Define output path
    # Ensure data/raw directory exists
    data_raw_path = get_data_path() / "raw"
    output_file = data_raw_path / "nist_ir_8200_data.zip"

    # 4. Download with retry logic
    try:
        success = download_with_retry(nist_url, output_file)
        if success:
            logger.info("Download completed successfully.")
        else:
            logger.error("Download failed unexpectedly.")
            raise DataInsufficientError("Download process did not complete successfully.")
    except DataInsufficientError:
        logger.error("Data acquisition failed due to missing resource or unrecoverable error.")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        raise DataInsufficientError(f"Unexpected error during data acquisition: {e}")

    logger.info("NIST-IR-8200 data download task finished.")


if __name__ == "__main__":
    main()
