"""
ACE data ingestion module: attempts real fetch, falls back to synthetic if failed.
"""
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import logging

import pandas as pd
import numpy as np
import requests

from utils.logging import DataIngestionError, get_logger, log_duration
from utils.io import save_parquet
from ingestion.generate_synthetic_data import generate_synthetic_dataset
from config import RAW_DIR

logger = get_logger(__name__)


def _download_raw(url: str, raw_path: Path) -> bytes:
    """
    Download raw bytes from the given URL and write them unchanged to raw_path.
    Returns the raw content.
    Raises DataIngestionError on network failure or non‑200 status.
    """
    try:
        logger.info(f"Downloading ACE data from {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        raw_content = response.content
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        with open(raw_path, "wb") as f:
            f.write(raw_content)
        logger.info(f"Raw ACE data written to {raw_path}")
        return raw_content
    except requests.RequestException as e:
        raise DataIngestionError(f"Failed to download ACE data: {e}") from e


def _parse_ace_csv(raw_bytes: bytes) -> pd.DataFrame:
    """
    Parse the downloaded ACE CSV content into a DataFrame.
    Expected columns include O/Fe, He/H, C/O and basic bulk parameters.
    """
    from io import BytesIO

    try:
        df = pd.read_csv(BytesIO(raw_bytes))
    except Exception as e:
        raise DataIngestionError(f"Failed to parse ACE CSV data: {e}") from e

    required_cols = {"O/Fe", "He/H", "C/O"}
    missing = required_cols - set(df.columns)
    if missing:
        raise DataIngestionError(f"ACE data missing required columns: {missing}")

    # Ensure timestamp column exists and is datetime
    if "timestamp" not in df.columns:
        raise DataIngestionError("ACE data missing 'timestamp' column")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def fetch_ace_data(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Attempt to fetch real ACE data from CDAWeb.
    Raises DataIngestionError (or subclass) if fetch fails.
    """
    # Construct a simple URL for demonstration purposes.
    # CDAWeb provides data via the "sp_phys" service; we use a generic CSV endpoint.
    # This URL pattern is illustrative – in a real implementation it would be
    # constructed according to the CDAWeb API documentation.
    base_url = "https://cdaweb.gsfc.nasa.gov/sp_phys/data/ace_swics_1min/ace_swics_1min.csv"
    # Append query parameters for the date range
    url = (
        f"{base_url}?start_date={start_date:%Y-%m-%d}"
        f"&end_date={end_date:%Y-%m-%d}"
    )

    raw_path = RAW_DIR / f"ace_{start_date:%Y%m%d}_{end_date:%Y%m%d}.csv"

    # Download raw bytes and write them unchanged
    raw_bytes = _download_raw(url, raw_path)

    # Parse the content into a DataFrame
    df = _parse_ace_csv(raw_bytes)
    return df


def load_synthetic_ace(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Generate synthetic ACE data as a fallback."""
    logger.warning("Falling back to synthetic ACE data generation.")
    return generate_synthetic_dataset(start_date, end_date, source="ACE")


@log_duration
def run_ingestion(start_date: datetime, end_date: datetime, output_path: Path) -> None:
    """Run ACE ingestion with fallback logic."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"Attempting to fetch real ACE data from {start_date} to {end_date}...")
        df = fetch_ace_data(start_date, end_date)
        df["source"] = "real"
    except DataIngestionError as e:
        logger.error(f"Real data fetch failed: {e}")
        logger.info("Generating synthetic fallback data...")
        df = load_synthetic_ace(start_date, end_date)
        df["source"] = "synthetic"

    save_parquet(df, output_path)
    logger.info(f"ACE data saved to {output_path}")


def main():
    """Entry point for ACE ingestion script."""
    parser = argparse.ArgumentParser(description="Ingest ACE solar wind data.")
    parser.add_argument("--start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/ace.parquet",
        help="Output path for processed Parquet file",
    )

    args = parser.parse_args()
    start_date = datetime.strptime(args.start, "%Y-%m-%d")
    end_date = datetime.strptime(args.end, "%Y-%m-%d")
    output_path = Path(args.output)

    run_ingestion(start_date, end_date, output_path)


if __name__ == "__main__":
    main()
