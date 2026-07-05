"""
Fetch experimental yield strength data for BCC Fe-alloys.

This module downloads real experimental data from a public source
(MatNavi/NIST or similar) as configured in code/config.py.
"""
import os
import sys
import logging
from pathlib import Path
import requests
import pandas as pd
from typing import Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import CONFIG, ERR_INSUFFICIENT_DATA
from utils.logging import get_logger, log_provenance_event

logger = get_logger(__name__)


def download_experimental_data(url: str, output_path: Path) -> Optional[pd.DataFrame]:
    """
    Download experimental BCC Fe-alloy data from a URL.

    Args:
        url: The URL to download data from.
        output_path: Path where the CSV file will be saved.

    Returns:
        DataFrame with experimental data, or None if download fails.
    """
    logger.info(f"Downloading experimental data from: {url}")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Save raw file
        with open(output_path, 'wb') as f:
            f.write(response.content)

        logger.info(f"Downloaded raw data to: {output_path}")
        return pd.read_csv(output_path)

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download data from {url}: {e}")
        return None
    except pd.errors.EmptyDataError:
        logger.error(f"Downloaded file at {output_path} is empty.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing downloaded data: {e}")
        return None


def fetch_experimental_data() -> Optional[pd.DataFrame]:
    """
    Main entry point to fetch experimental data.

    Returns:
        DataFrame with experimental data, or None if the operation fails.
    """
    url = CONFIG.EXPERIMENTAL_DATA_URL
    output_path = CONFIG.RAW_EXPERIMENTAL_PATH

    if not url:
        logger.error("EXPERIMENTAL_DATA_URL not configured in config.py")
        return None

    df = download_experimental_data(url, output_path)

    if df is not None:
        log_provenance_event(
            event_type="data_download",
            source=url,
            destination=str(output_path),
            status="success",
            row_count=len(df)
        )
        logger.info(f"Successfully downloaded {len(df)} rows of experimental data")
    else:
        log_provenance_event(
            event_type="data_download",
            source=url,
            destination=str(output_path),
            status="failed",
            error="Download or parsing failed"
        )

    return df


def main():
    """
    Script entry point for fetching experimental data.
    """
    logger.info("Starting experimental data fetch (T013)")

    df = fetch_experimental_data()

    if df is None:
        logger.error("Failed to fetch experimental data. Exiting.")
        print(f"ERROR: {ERR_INSUFFICIENT_DATA}: Could not retrieve experimental data")
        sys.exit(1)

    logger.info("Experimental data fetch completed successfully")
    print(f"Success: Downloaded {len(df)} rows to {CONFIG.RAW_EXPERIMENTAL_PATH}")


if __name__ == "__main__":
    main()