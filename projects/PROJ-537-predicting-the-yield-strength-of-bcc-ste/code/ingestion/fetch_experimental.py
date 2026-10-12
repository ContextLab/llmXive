"""
Fetch experimental yield strength data for BCC Fe-alloys.

This module downloads real experimental data from a public source
(MatNavi/NIST or similar) as configured in code/config.py.
It now robustly handles both CSV and JSON responses, converting JSON
payloads to a CSV file so downstream steps can operate uniformly.
"""
import os
import sys
import logging
from pathlib import Path
import requests
import pandas as pd
from typing import Optional, Union

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import CONFIG, ERR_INSUFFICIENT_DATA
from utils.logging import get_logger, log_provenance_event

logger = get_logger(__name__)

def _save_dataframe(df: pd.DataFrame, output_path: Path) -> None:
    """Write DataFrame to CSV, ensuring parent directories exist."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved experimental data to {output_path}")

def download_experimental_data(url: str, output_path: Path) -> Optional[pd.DataFrame]:
    """
    Download experimental BCC Fe-alloy data from a URL.

    Supports CSV and JSON responses. The function writes a CSV file to
    ``output_path`` and returns the loaded DataFrame.

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
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download data from {url}: {e}")
        return None

    # Determine content type
    content_type = response.headers.get("Content-Type", "").lower()
    try:
        if "text/csv" in content_type or url.lower().endswith(".csv"):
            # Direct CSV
            df = pd.read_csv(pd.compat.StringIO(response.text))
        elif "application/json" in content_type or url.lower().endswith(".json"):
            # JSON payload
            json_content = response.json()
            # Assume list of records or dict with 'data' key
            if isinstance(json_content, dict) and "data" in json_content:
                records = json_content["data"]
            else:
                records = json_content
            df = pd.DataFrame(records)
        else:
            # Try to infer based on content
            try:
                df = pd.read_csv(pd.compat.StringIO(response.text))
            except Exception:
                # Fallback to JSON parsing
                json_content = response.json()
                if isinstance(json_content, dict) and "data" in json_content:
                    records = json_content["data"]
                else:
                    records = json_content
                df = pd.DataFrame(records)

        if df.empty:
            logger.error("Downloaded data is empty after parsing.")
            return None

        # Write standardized CSV
        _save_dataframe(df, output_path)
        return df

    except Exception as e:
        logger.error(f"Error processing downloaded data: {e}")
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
