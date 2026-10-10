"""
NOAA geomagnetic index ingestion module: attempts real fetch, falls back to synthetic.
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
        logger.info(f"Downloading NOAA data from {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        raw_content = response.content
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        with open(raw_path, "wb") as f:
            f.write(raw_content)
        logger.info(f"Raw NOAA data written to {raw_path}")
        return raw_content
    except requests.RequestException as e:
        raise DataIngestionError(f"Failed to download NOAA data: {e}") from e


def _parse_noaa_csv(raw_bytes: bytes) -> pd.DataFrame:
    """
    Parse the downloaded NOAA CSV content into a DataFrame.
    Expected columns include 'Kp' and 'Dst' along with a timestamp.
    """
    from io import BytesIO

    try:
        df = pd.read_csv(BytesIO(raw_bytes))
    except Exception as e:
        raise DataIngestionError(f"Failed to parse NOAA CSV data: {e}") from e

    required_cols = {"Kp", "Dst"}
    missing = required_cols - set(df.columns)
    if missing:
        raise DataIngestionError(f"NOAA data missing required columns: {missing}")

    if "timestamp" not in df.columns:
        raise DataIngestionError("NOAA data missing 'timestamp' column")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def fetch_noaa_kp(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Attempt to fetch real Kp index from NOAA.
    Raises DataIngestionError if fetch fails.
    """
    # NOAA provides Kp in a simple CSV archive; this URL is illustrative.
    base_url = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
    # For the purpose of this implementation we fetch the JSON and convert to DataFrame.
    try:
        response = requests.get(base_url, timeout=30)
        response.raise_for_status()
        json_data = response.json()
    except requests.RequestException as e:
        raise DataIngestionError(f"Failed to download NOAA Kp data: {e}") from e

    # Convert JSON list of dicts to DataFrame
    df = pd.DataFrame(json_data)
    if "time_tag" not in df.columns:
        raise DataIngestionError("NOAA Kp JSON missing 'time_tag' field")
    df = df.rename(columns={"time_tag": "timestamp", "kp": "Kp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    # Filter date range
    mask = (df["timestamp"] >= pd.Timestamp(start_date)) & (df["timestamp"] <= pd.Timestamp(end_date))
    return df.loc[mask, ["timestamp", "Kp"]]


def fetch_noaa_dst(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Attempt to fetch real Dst index from NOAA.
    Raises DataIngestionError if fetch fails.
    """
    # NOAA provides Dst as a CSV; illustrative URL.
    base_url = "https://services.swpc.noaa.gov/text/dst.txt"
    raw_path = RAW_DIR / f"noaa_dst_{start_date:%Y%m%d}_{end_date:%Y%m%d}.txt"
    raw_bytes = _download_raw(base_url, raw_path)

    # The Dst text file has a header; we parse it with pandas.read_fwf
    try:
        from io import StringIO

        text = raw_bytes.decode("utf-8", errors="ignore")
        # Skip comment lines starting with #
        lines = [ln for ln in text.splitlines() if not ln.startswith("#")]
        df = pd.read_fwf(StringIO("\n".join(lines)), colspecs=[(0, 8), (9, 14)], names=["timestamp", "Dst"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y%m%d")
    except Exception as e:
        raise DataIngestionError(f"Failed to parse NOAA Dst data: {e}") from e

    mask = (df["timestamp"] >= pd.Timestamp(start_date)) & (df["timestamp"] <= pd.Timestamp(end_date))
    return df.loc[mask, ["timestamp", "Dst"]]


def load_synthetic_noaa(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Generate synthetic NOAA data as a fallback."""
    logger.warning("Falling back to synthetic NOAA data generation.")
    # Generate synthetic data for Kp and Dst
    df = generate_synthetic_dataset(start_date, end_date, source="NOAA")
    return df


@log_duration
def run_ingestion(start_date: datetime, end_date: datetime, output_path: Path) -> None:
    """Run NOAA ingestion with fallback logic."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        logger.info(f"Attempting to fetch real NOAA data from {start_date} to {end_date}...")
        # Try to fetch Kp and Dst
        kp_df = fetch_noaa_kp(start_date, end_date)
        dst_df = fetch_noaa_dst(start_date, end_date)
        # Merge on timestamp (outer join to keep all rows)
        df = pd.merge(kp_df, dst_df, on="timestamp", how="outer")
        df["source"] = "real"
    except DataIngestionError as e:
        logger.error(f"Real data fetch failed: {e}")
        logger.info("Generating synthetic fallback data...")
        df = load_synthetic_noaa(start_date, end_date)
        df["source"] = "synthetic"

    save_parquet(df, output_path)
    logger.info(f"NOAA data saved to {output_path}")


def main():
    """Entry point for NOAA ingestion script."""
    parser = argparse.ArgumentParser(description="Ingest NOAA geomagnetic index data.")
    parser.add_argument("--start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/noaa.parquet",
        help="Output path for processed Parquet file",
    )

    args = parser.parse_args()
    start_date = datetime.strptime(args.start, "%Y-%m-%d")
    end_date = datetime.strptime(args.end, "%Y-%m-%d")
    output_path = Path(args.output)

    run_ingestion(start_date, end_date, output_path)


if __name__ == "__main__":
    main()
