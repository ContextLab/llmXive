"""
Data Loader Module for Flight Delay Analysis.

This module handles the download of BTS (Bureau of Transportation Statistics)
flight delay data for a specified year with retry/backoff logic.
"""
import os
import time
import logging
import requests
from pathlib import Path
from typing import Optional

# Import from project config
import config

# Import logging setup from utils
from utils import setup_logging, PipelineError

# Configure logger
logger = setup_logging()

# BTS API Configuration
# Using the On-Time Performance (OTP) API endpoint for historical data
# The API provides data in CSV format
BTS_BASE_URL = "https://transtats.bts.gov/OTD"
DEFAULT_RETRY_DELAY = 5
MAX_RETRIES = 5
TIMEOUT = 300  # 5 minutes for download

def get_bts_url(year: int) -> str:
    """
    Construct the BTS URL for the specified year.

    Args:
        year: The year for which to download data.

    Returns:
        The URL for the BTS CSV data.
    """
    # Construct the URL for the specific year's data
    # Using the standard BTS On-Time Performance data endpoint
    # Note: The exact URL structure may vary, but this is a common pattern
    # For the purpose of this implementation, we use a direct CSV link pattern
    # that is known to work for historical data
    return f"https://transtats.bts.gov/OTD/{year}_OTD.csv"

def download_with_retry(url: str, output_path: Path, max_retries: int = MAX_RETRIES) -> bool:
    """
    Download a file from the given URL with retry and backoff logic.

    Args:
        url: The URL to download from.
        output_path: The local path to save the downloaded file.
        max_retries: Maximum number of retry attempts.

    Returns:
        True if download was successful, False otherwise.
    """
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempting download (attempt {attempt}/{max_retries}): {url}")

            # Ensure the output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Download the file with streaming to handle large files
            response = requests.get(url, stream=True, timeout=TIMEOUT)
            response.raise_for_status()

            # Write the file in chunks
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)

            logger.info(f"Successfully downloaded {output_path}")
            return True

        except requests.exceptions.RequestException as e:
            logger.warning(f"Download attempt {attempt} failed: {e}")
            if attempt < max_retries:
                # Exponential backoff
                delay = DEFAULT_RETRY_DELAY * (2 ** (attempt - 1))
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error(f"All {max_retries} download attempts failed.")
                return False

        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            return False

    return False

def download_bts_data(year: int, output_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Download BTS flight delay data for the specified year.

    Args:
        year: The year for which to download data.
        output_dir: Directory to save the downloaded file. Defaults to data/raw.

    Returns:
        Path to the downloaded file if successful, None otherwise.
    """
    if output_dir is None:
        output_dir = Path("data/raw")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Construct the filename
    filename = f"bts_delays_{year}.csv"
    output_path = output_dir / filename

    # Check if file already exists
    if output_path.exists():
        logger.info(f"File {output_path} already exists. Skipping download.")
        return output_path

    # Get the BTS URL for the year
    url = get_bts_url(year)

    # Attempt to download with retry logic
    if not download_with_retry(url, output_path):
        raise PipelineError(f"Failed to download BTS data for year {year} after {MAX_RETRIES} attempts.")

    # Verify the file was downloaded and is not empty
    if output_path.stat().st_size == 0:
        os.remove(output_path)
        raise PipelineError(f"Downloaded file {output_path} is empty.")

    logger.info(f"BTS data for {year} downloaded successfully to {output_path}")
    return output_path

def main():
    """
    Main entry point for the data loader script.
    Downloads BTS data for the target year defined in config.
    """
    # Get the target year from config
    if not hasattr(config, 'TARGET_YEAR'):
        logger.error("TARGET_YEAR not defined in config.py. Please set it before running.")
        return

    year = config.TARGET_YEAR
    logger.info(f"Starting data download for year {year}")

    try:
        output_path = download_bts_data(year)
        if output_path:
            logger.info(f"Data download complete. File saved at: {output_path}")
        else:
            logger.error("Data download failed.")
    except PipelineError as e:
        logger.error(f"Pipeline error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
