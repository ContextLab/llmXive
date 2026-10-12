"""
NOAA geomagnetic index ingestion module: attempts real fetch of NOAA Kp and Dst data.
This module provides:
- fetch_noaa_kp: download real Kp index data.
- fetch_noaa_dst: download real Dst index data.
- run_ingestion: orchestrates ingestion using a configuration dict, returns
  the resulting DataFrame and a label indicating the data source ("real").

Synthetic fallback has been removed to comply with the project's policy
of using only real data.
"""

import argparse
from pathlib import Path
from datetime import datetime
import logging

import pandas as pd
import requests

# Updated imports to use the correct package path
from code.utils.logging import DataIngestionError, get_logger, log_duration
from code.utils.io import save_parquet
from code.config import RAW_DIR, SEED

logger = get_logger(__name__)


# ----------------------------------------------------------------------
# Real data download helpers
# ----------------------------------------------------------------------
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
    Expected columns include 'Kp' and 'Dst' and a timestamp column.
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


# ----------------------------------------------------------------------
# Public orchestration function (real data only)
# ----------------------------------------------------------------------
@log_duration
def run_ingestion(config: dict) -> tuple[pd.DataFrame, str]:
    """
    Orchestrate NOAA ingestion using only real data.

    Expected keys in ``config``:
        - ``start_date`` (datetime)
        - ``end_date``   (datetime)
        - ``output_path`` (optional Path/str; defaults to
          ``data/processed/noaa.parquet``)

    It raises ``ConnectionError`` if any remote fetch fails.
    The returned DataFrame includes a column ``data_source`` set to ``"real"``.
    """
    start_date = config["start_date"]
    end_date = config["end_date"]
    output_path = Path(config.get("output_path", "data/processed/noaa.parquet"))

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Attempt real fetch; any failure propagates.
    kp_df = fetch_noaa_kp(start_date, end_date)
    dst_df = fetch_noaa_dst(start_date, end_date)
    df = pd.merge(kp_df, dst_df, on="timestamp", how="outer")
    source_label = "real"

    # Annotate source and persist
    df["data_source"] = source_label
    save_parquet(df, output_path)
    logger.info(f"NOAA data ({source_label}) saved to {output_path}")

    return df, source_label


# ----------------------------------------------------------------------
# Command‑line entry point
# ----------------------------------------------------------------------
def main() -> None:
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

    config = {
        "start_date": start_date,
        "end_date": end_date,
        "output_path": Path(args.output),
    }

    # run_ingestion will raise on any download failure.
    run_ingestion(config)


if __name__ == "__main__":
    main()
