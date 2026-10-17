"""
NOAA geomagnetic index fetcher.

Downloads hourly Kp and Dst indices from the official NOAA service,
filters them for the requested date range, and writes a CSV containing the
required columns ``Kp`` and ``Dst`` (plus a ``timestamp`` column).

The file is saved as ``data/raw/noaa_<YYYYMM>.csv``.
"""

import time
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

from code.config import RAW_DATA_DIR
from code import logger

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _exponential_backoff(attempt: int, base: float = 1.0) -> None:
    """Sleep ``base * 2**attempt`` seconds."""
    time.sleep(base * (2 ** attempt))

def _download_text(url: str) -> str:
    """
    Download a text file via HTTP/HTTPS and return its content.

    The function retries three times with exponential back‑off.  If all
    attempts fail, a ``ConnectionError`` is raised – the caller must handle
    this to satisfy the specification (no silent synthetic fall‑back).
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; llmXive/1.0)"}
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=60, stream=True, headers=headers)
            response.raise_for_status()
            return response.text
        except Exception as exc:  # pragma: no cover – exercised by CI when network fails
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {exc}")
            if attempt == 2:
                raise ConnectionError(f"Unable to download {url}") from exc
            _exponential_backoff(attempt)
    raise ConnectionError(f"Failed to download {url}")

def _parse_index(txt: str, col_name: str) -> pd.DataFrame:
    """
    Parse NOAA index text files (Kp or Dst).

    Expected format (space‑separated):
    ``YYYY MM DD HH Value``

    Lines beginning with ``#`` are ignored.
    """
    records = []
    for line in txt.strip().splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        try:
            ts = datetime(int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3]))
            val = float(parts[4])
            records.append({"timestamp": ts, col_name: val})
        except (ValueError, IndexError):
            continue
    return pd.DataFrame(records)

# ----------------------------------------------------------------------
# Main public function
# ----------------------------------------------------------------------
def fetch_noaa(start_date: str, end_date: str) -> str:
    """
    Fetch NOAA Kp and Dst geomagnetic indices for the supplied date range.

    The function downloads the two index files from NOAA's public service,
    parses them, merges on the exact timestamps, filters to the requested
    window, and writes the result to ``data/raw/noaa_<YYYYMM>.csv`` where
    ``YYYYMM`` corresponds to the month of ``start_date`` (as required by the
    specification).

    Parameters
    ----------
    start_date : str
        Start date in ``YYYY‑MM‑DD`` format (inclusive).
    end_date : str
        End date in ``YYYY‑MM‑DD`` format (inclusive).

    Returns
    -------
    str
        Path to the written CSV file.
    """
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt   = datetime.strptime(end_date,   "%Y-%m-%d")

    yyyymm = start_dt.strftime("%Y%m")
    output_path = Path(RAW_DATA_DIR) / f"noaa_{yyyymm}.csv"

    # Corrected public endpoints – these URLs return plain text files with
    # space‑separated columns ``YYYY MM DD HH value``.
    kp_url = "https://services.swpc.noaa.gov/products/kp.txt"
    dst_url = "https://services.swpc.noaa.gov/products/dst.txt"

    logger.debug(f"Downloading Kp data from {kp_url}")
    kp_text = _download_text(kp_url)

    logger.debug(f"Downloading Dst data from {dst_url}")
    dst_text = _download_text(dst_url)

    kp_df = _parse_index(kp_text, "Kp")
    dst_df = _parse_index(dst_text, "Dst")

    if kp_df.empty or dst_df.empty:
        raise ConnectionError("Downloaded NOAA files are empty or malformed.")

    # Merge on exact timestamp (inner join keeps rows where both indices are present)
    merged = pd.merge(kp_df, dst_df, on="timestamp", how="inner")

    # Restrict to the requested window (inclusive of the end date)
    mask = (merged["timestamp"] >= pd.Timestamp(start_dt)) & (
        merged["timestamp"] <= pd.Timestamp(end_dt) + pd.Timedelta(days=1)
    )
    merged = merged.loc[mask]

    if merged.empty:
        raise ConnectionError(
            f"No NOAA data found for period {start_date} to {end_date} at the provided endpoints."
        )

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False)
    logger.info(f"NOAA data written to {output_path}")

    return str(output_path)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch NOAA Kp and Dst geomagnetic indices.")
    parser.add_argument("--start", required=True, help="Start date in YYYY‑MM‑DD")
    parser.add_argument("--end",   required=True, help="End date in YYYY‑MM‑DD")
    args = parser.parse_args()

    try:
        path = fetch_noaa(args.start, args.end)
        print(f"NOAA data saved to: {path}")
    except Exception as exc:  # pragma: no cover – exercised by CI when network fails
        logger.error(f"Failed to fetch NOAA data: {exc}")
        raise
