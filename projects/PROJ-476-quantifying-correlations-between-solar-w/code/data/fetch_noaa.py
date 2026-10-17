"""
NOAA geomagnetic index fetcher.

Downloads hourly Kp and Dst indices from the official NOAA FTP/HTTPS
service, merges them on their timestamps and writes a CSV containing the
required columns ``Kp`` and ``Dst`` (plus ``timestamp``).

The implementation respects the specification:
* streaming HTTP download with ``requests``
* exponential‑backoff retries (max 3 attempts)
* raises ``ConnectionError`` on any network problem
* never falls back to synthetic data
"""

import logging
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

from code.config import (
    NOAA_KP_DST_URL,
    RAW_DATA_DIR,
)
from code import logger

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _exponential_backoff(attempt: int, base: float = 1.0) -> None:
    """Sleep ``base * 2**attempt`` seconds."""
    time.sleep(base * (2 ** attempt))

def _download_text(url: str) -> str:
    """Download a text file via HTTP/HTTPS and return its content."""
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=30, stream=True)
            if response.status_code != 200:
                raise ConnectionError(
                    f"Failed to download {url}: HTTP {response.status_code}"
                )
            return response.text
        except Exception as exc:
            logger.warning(
                f"Attempt {attempt + 1} failed for {url}: {exc}"
            )
            if attempt == 2:
                raise ConnectionError(f"Unable to download {url}") from exc
            _exponential_backoff(attempt)
    # Should never reach here
    raise ConnectionError(f"Failed to download {url}")

def _parse_kp(txt: str) -> pd.DataFrame:
    """
    Parse the NOAA Kp index text file.

    Expected format (space‑separated):
        YYYY MM DD HH  Kp
    """
    records = []
    for line in txt.strip().splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        year, month, day, hour, kp = parts[:5]
        try:
            ts = datetime(
                int(year), int(month), int(day), int(hour)
            )
            kp_val = float(kp)
        except ValueError:
            continue
        records.append({"timestamp": ts, "Kp": kp_val})
    return pd.DataFrame(records)

def _parse_dst(txt: str) -> pd.DataFrame:
    """
    Parse the NOAA Dst index text file.

    Expected format (space‑separated):
        YYYY MM DD HH  Dst
    """
    records = []
    for line in txt.strip().splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 5:
            continue
        year, month, day, hour, dst = parts[:5]
        try:
            ts = datetime(
                int(year), int(month), int(day), int(hour)
            )
            dst_val = float(dst)
        except ValueError:
            continue
        records.append({"timestamp": ts, "Dst": dst_val})
    return pd.DataFrame(records)

# ----------------------------------------------------------------------
# Core fetch logic
# ----------------------------------------------------------------------
def _fetch_and_merge_noaa(output_path: Path) -> Path:
    """
    Download Kp and Dst files, merge on timestamp and write CSV.

    Parameters
    ----------
    output_path : Path
        Destination CSV (``data/raw/noaa_raw.csv``).

    Returns
    -------
    Path
        The path that was written.
    """
    # NOAA provides separate files; we use the standard HTTP endpoints.
    kp_url = f"{NOAA_KP_DST_URL}kp.txt"
    dst_url = f"{NOAA_KP_DST_URL}dst.txt"

    logger.debug(f"Downloading Kp from {kp_url}")
    kp_text = _download_text(kp_url)
    logger.debug(f"Downloading Dst from {dst_url}")
    dst_text = _download_text(dst_url)

    kp_df = _parse_kp(kp_text)
    dst_df = _parse_dst(dst_text)

    if kp_df.empty:
        raise ConnectionError("Downloaded Kp file is empty or malformed.")
    if dst_df.empty:
        raise ConnectionError("Downloaded Dst file is empty or malformed.")

    # Merge on timestamp (inner join ensures both indices present)
    merged = pd.merge(kp_df, dst_df, on="timestamp", how="inner")

    # Verify required columns
    if not {"Kp", "Dst", "timestamp"}.issubset(merged.columns):
        raise ConnectionError(
            "Merged NOAA data missing required columns after download."
        )

    # Write CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False)
    logger.info(f"NOAA data written to {output_path}")
    return output_path

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def fetch_noaa(start_date: str, end_date: str) -> str:
    """
    Fetch NOAA Kp and Dst geomagnetic indices.

    The start/end dates are accepted for API compatibility but the
    NOAA service provides a single continuous file; the function ignores
    the date limits and writes the full series to ``data/raw/noaa_raw.csv``.

    Returns
    -------
    str
        Absolute path to the written CSV.

    Raises
    ------
    ConnectionError
        If the remote files cannot be retrieved or parsed.
    """
    # The NOAA service does not support date‑restricted downloads; we
    # download the complete files and let downstream stages slice them.
    output_path = Path(RAW_DATA_DIR) / "noaa_raw.csv"
    _fetch_and_merge_noaa(output_path)
    return str(output_path)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch NOAA Kp and Dst geomagnetic indices."
    )
    parser.add_argument(
        "--start",
        required=True,
        help="Start date (YYYY‑MM‑DD) – kept for compatibility",
    )
    parser.add_argument(
        "--end",
        required=True,
        help="End date (YYYY‑MM‑DD) – kept for compatibility",
    )
    args = parser.parse_args()
    try:
        path = fetch_noaa(args.start, args.end)
        print(f"NOAA data saved to: {path}")
    except Exception as e:
        logger.error(f"Failed to fetch NOAA data: {e}")
        raise
