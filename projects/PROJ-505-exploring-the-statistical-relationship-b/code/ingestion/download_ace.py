"""
ACE data ingestion module: attempts real fetch of ACE composition data.
This module provides:
- fetch_ace_data: download real ACE data from CDAWeb.
- run_ingestion: orchestrates ingestion using a configuration dict, returns
  the resulting DataFrame and a label indicating the data source ("real").

The public API matches the expectations of the unit tests
(tests/unit/test_download_ace.py). Synthetic fallback has been removed
to satisfy the project's "real data only" policy.
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
# Real data download utilities
# ----------------------------------------------------------------------
def _download_raw(url: str, raw_path: Path) -> bytes:
    """
    Download raw bytes from the given URL and write them unchanged to raw_path.
    Returns the raw content.
    Raises ConnectionError on network failure or non‑200 status.
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
        raise ConnectionError(f"Failed to download ACE data: {e}") from e


def _parse_ace_csv(raw_bytes: bytes) -> pd.DataFrame:
    """
    Parse the downloaded ACE CSV content into a DataFrame.
    Expected columns include O/Fe, He/H, C/O and a timestamp column.
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

    if "timestamp" not in df.columns:
        raise DataIngestionError("ACE data missing 'timestamp' column")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def fetch_ace_data(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Attempt to fetch real ACE data from CDAWeb.
    Raises ConnectionError if the request fails.
    """
    base_url = "https://cdaweb.gsfc.nasa.gov/sp_phys/data/ace_swics_1min/ace_swics_1min.csv"
    url = (
        f"{base_url}?start_date={start_date:%Y-%m-%d}"
        f"&end_date={end_date:%Y-%m-%d}"
    )

    raw_path = RAW_DIR / f"ace_{start_date:%Y%m%d}_{end_date:%Y%m%d}.csv"

    raw_bytes = _download_raw(url, raw_path)

    df = _parse_ace_csv(raw_bytes)
    return df


# ----------------------------------------------------------------------
# Public orchestration function (real data only)
# ----------------------------------------------------------------------
@log_duration
def run_ingestion(config: dict) -> tuple[pd.DataFrame, str]:
    """
    Orchestrate ACE ingestion using only real data.

    The function expects a configuration dictionary with at least the
    following keys:
        - ``start_date`` (datetime)
        - ``end_date``   (datetime)
        - ``output_path`` (Path or str, optional; defaults to
          ``data/processed/ace.parquet``)

    It raises ``ConnectionError`` if the remote fetch fails.
    The returned DataFrame includes a column ``data_source`` set to ``"real"``.
    """
    # Resolve configuration
    start_date = config["start_date"]
    end_date = config["end_date"]
    output_path = Path(config.get("output_path", "data/processed/ace.parquet"))

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Attempt real fetch; any failure propagates to the caller.
    df = fetch_ace_data(start_date, end_date)
    source_label = "real"

    # Annotate source and persist
    df["data_source"] = source_label
    save_parquet(df, output_path)
    logger.info(f"ACE data ({source_label}) saved to {output_path}")

    return df, source_label


# ----------------------------------------------------------------------
# Command‑line entry point
# ----------------------------------------------------------------------
def main() -> None:
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

    config = {
        "start_date": start_date,
        "end_date": end_date,
        "output_path": Path(args.output),
    }

    # run_ingestion will raise if the download fails; this is intentional
    # to avoid silently falling back to synthetic data.
    run_ingestion(config)


if __name__ == "__main__":
    main()
