"""
NOAA geomagnetic index ingestion module: attempts real fetch.
"""

import argparse
from pathlib import Path
from datetime import datetime
import logging

import pandas as pd
import requests

from utils.logging import DataIngestionError, get_logger, log_duration
from utils.io import save_parquet
from config import RAW_DIR

logger = get_logger(__name__)

def _download_raw(url: str, raw_path: Path) -> bytes:
    """
    Download raw bytes from the given URL and write them unchanged to raw_path.
    Returns the raw content.
    Raises ConnectionError on network failure or non‑200 status.
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
        raise ConnectionError(f"Failed to download NOAA data: {e}") from e


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
    Fetch real Kp index from NOAA (JSON endpoint).
    Raises ConnectionError on failure.
    """
    url = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        json_data = response.json()
    except requests.RequestException as e:
        raise ConnectionError(f"Failed to download NOAA Kp data: {e}") from e

    df = pd.DataFrame(json_data)
    if "time_tag" not in df.columns:
        raise DataIngestionError("NOAA Kp JSON missing 'time_tag' field")
    df = df.rename(columns={"time_tag": "timestamp", "kp": "Kp"})
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    mask = (df["timestamp"] >= pd.Timestamp(start_date)) & (df["timestamp"] <= pd.Timestamp(end_date))
    return df.loc[mask, ["timestamp", "Kp"]]


def fetch_noaa_dst(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Fetch real Dst index from NOAA (text file).
    Raises ConnectionError on failure.
    """
    url = "https://services.swpc.noaa.gov/text/dst.txt"
    raw_path = RAW_DIR / f"noaa_dst_{start_date:%Y%m%d}_{end_date:%Y%m%d}.txt"
    raw_bytes = _download_raw(url, raw_path)

    try:
        from io import StringIO

        text = raw_bytes.decode("utf-8", errors="ignore")
        lines = [ln for ln in text.splitlines() if not ln.startswith("#")]
        df = pd.read_fwf(StringIO("\n".join(lines)), colspecs=[(0, 8), (9, 14)], names=["timestamp", "Dst"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="%Y%m%d")
    except Exception as e:
        raise DataIngestionError(f"Failed to parse NOAA Dst data: {e}") from e

    mask = (df["timestamp"] >= pd.Timestamp(start_date)) & (df["timestamp"] <= pd.Timestamp(end_date))
    return df.loc[mask, ["timestamp", "Dst"]]


@log_duration
def run_ingestion(start_date: datetime, end_date: datetime, output_path: Path) -> None:
    """
    Run NOAA ingestion. Writes merged DataFrame to output_path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Fetching NOAA data from {start_date} to {end_date}...")
    kp_df = fetch_noaa_kp(start_date, end_date)
    dst_df = fetch_noaa_dst(start_date, end_date)
    df = pd.merge(kp_df, dst_df, on="timestamp", how="outer")
    df["source"] = "real"

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
