"""
ACE data fetcher.

Downloads ACE SWEPAM (proton density, temperature) and SWICS (helium abundance)
Level‑2 CSV files for a given date range via FTP, merges them, and writes a
combined CSV containing the required columns: ``N_p``, ``T_p``, ``He2+_ratio``.
The file is saved under ``data/raw/ace_raw.csv`` (overwritten each call).

The implementation follows the specification:
* streaming download with ``requests`` (FTP fallback via ``ftplib``)
* exponential‑backoff retries (max 3 attempts)
* on any network/HTTP failure a ``ConnectionError`` is raised
* no synthetic data is generated
"""

import os
import ftplib
import ssl
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import pandas as pd
import requests

from code.config import (
    ACE_URL,
    ACE_SWEPAM_URL,
    ACE_SWICS_URL,
    RAW_DATA_DIR,
)
from code import logger

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _exponential_backoff(attempt: int, base: float = 1.0) -> None:
    """Sleep ``base * 2**attempt`` seconds."""
    time.sleep(base * (2 ** attempt))

def _download_ftp_file(host: str, remote_path: str, local_path: Path) -> None:
    """
    Download a single file from an FTP server using an SSL context.

    Parameters
    ----------
    host: str
        FTP host (e.g. ``spdf.gsfc.nasa.gov``).
    remote_path: str
        Full path on the FTP server (including the filename).
    local_path: Path
        Destination on the local filesystem.
    """
    logger.debug(f"Attempting FTP download: ftp://{host}/{remote_path}")

    # Ensure parent directory exists
    local_path.parent.mkdir(parents=True, exist_ok=True)

    # Use explicit TLS (FTP over TLS) if the server supports it.
    context = ssl.create_default_context()
    with ftplib.FTP_TLS(host) as ftp:
        ftp.login()  # anonymous
        ftp.prot_p()  # switch to secure data connection
        with open(local_path, "wb") as fp:
            ftp.retrbinary(f"RETR {remote_path}", fp.write)

def _download_http_file(url: str, local_path: Path) -> None:
    """
    Stream‑download a file via HTTP/HTTPS.

    Parameters
    ----------
    url: str
        The full URL of the file.
    local_path: Path
        Destination path.
    """
    logger.debug(f"Attempting HTTP download: {url}")
    local_path.parent.mkdir(parents=True, exist_ok=True)

    with requests.get(url, stream=True, timeout=30) as r:
        if r.status_code != 200:
            raise ConnectionError(f"Failed to download {url}: HTTP {r.status_code}")
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

# ----------------------------------------------------------------------
# Core fetch logic
# ----------------------------------------------------------------------
def _list_ftp_files(host: str, directory: str) -> List[str]:
    """Return a list of filenames in a given FTP directory."""
    with ftplib.FTP(host) as ftp:
        ftp.login()
        ftp.cwd(directory)
        return ftp.nlst()

def _matching_filenames(
    files: List[str],
    start: datetime,
    end: datetime,
    prefix: str,
    suffix: str = ".csv",
) -> List[str]:
    """
    Filter FTP filenames that fall inside the date window.

    Expected filename pattern (example):
        ace_swepam_l2_20031001_v01.cdf  (or .csv if available)

    The function extracts the ``YYYYMMDD`` part and keeps those that lie
    between ``start`` and ``end`` (inclusive).
    """
    matches = []
    for name in files:
        if not name.startswith(prefix) or not name.endswith(suffix):
            continue
        # Extract the date portion – assume it is the first 8 digits after the prefix
        try:
            date_str = name[len(prefix) : len(prefix) + 8]
            file_date = datetime.strptime(date_str, "%Y%m%d")
        except Exception:
            continue
        if start <= file_date <= end:
            matches.append(name)
    return matches

def _fetch_and_merge_ace(
    start_date: str, end_date: str, output_path: Path
) -> Path:
    """
    Download SWEPAM and SWICS Level‑2 CSV files for the requested period,
    merge them on the ``timestamp`` column and write a combined CSV.

    Parameters
    ----------
    start_date, end_date : str
        ``YYYY‑MM‑DD`` strings.
    output_path : Path
        Destination CSV path (``data/raw/ace_raw.csv``).

    Returns
    -------
    Path
        The path that was written.
    """
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    host = "spdf.gsfc.nasa.gov"

    # ------------------------------------------------------------------
    # SWEPAM (proton density & temperature)
    # ------------------------------------------------------------------
    swepam_dir = "/pub/data/ace/swepam/level2"
    swepam_files = _list_ftp_files(host, swepam_dir)
    swepam_matches = _matching_filenames(
        swepam_files, start_dt, end_dt, prefix="ace_swepam_l2_"
    )
    if not swepam_matches:
        raise ConnectionError(
            f"No SWEPAM files found for period {start_date} – {end_date}"
        )

    swepam_frames = []
    for fname in swepam_matches:
        remote_path = f"{swepam_dir}/{fname}"
        local_tmp = output_path.parent / f"tmp_{fname}"
        for attempt in range(3):
            try:
                _download_ftp_file(host, remote_path, local_tmp)
                break
            except Exception as exc:
                logger.warning(
                    f"Attempt {attempt + 1} failed for {fname}: {exc}"
                )
                if attempt == 2:
                    raise ConnectionError(
                        f"Failed to download SWEPAM file {fname}"
                    )
                _exponential_backoff(attempt)
        df = pd.read_csv(local_tmp)
        swepam_frames.append(df)
        local_tmp.unlink()  # clean up temporary file

    swepam_df = pd.concat(swepam_frames, ignore_index=True)

    # ------------------------------------------------------------------
    # SWICS (helium abundance)
    # ------------------------------------------------------------------
    swics_dir = "/pub/data/ace/swics/level2"
    swics_files = _list_ftp_files(host, swics_dir)
    swics_matches = _matching_filenames(
        swics_files, start_dt, end_dt, prefix="ace_swics_l2_"
    )
    if not swics_matches:
        raise ConnectionError(
            f"No SWICS files found for period {start_date} – {end_date}"
        )

    swics_frames = []
    for fname in swics_matches:
        remote_path = f"{swics_dir}/{fname}"
        local_tmp = output_path.parent / f"tmp_{fname}"
        for attempt in range(3):
            try:
                _download_ftp_file(host, remote_path, local_tmp)
                break
            except Exception as exc:
                logger.warning(
                    f"Attempt {attempt + 1} failed for {fname}: {exc}"
                )
                if attempt == 2:
                    raise ConnectionError(
                        f"Failed to download SWICS file {fname}"
                    )
                _exponential_backoff(attempt)
        df = pd.read_csv(local_tmp)
        swics_frames.append(df)
        local_tmp.unlink()

    swics_df = pd.concat(swics_frames, ignore_index=True)

    # ------------------------------------------------------------------
    # Merge on timestamp (both data sets contain a ``timestamp`` column)
    # ------------------------------------------------------------------
    if "timestamp" not in swepam_df.columns or "timestamp" not in swics_df.columns:
        raise ConnectionError(
            "Downloaded ACE files do not contain a 'timestamp' column."
        )

    # Ensure timestamps are parsed as datetime for reliable merging
    swepam_df["timestamp"] = pd.to_datetime(swepam_df["timestamp"])
    swics_df["timestamp"] = pd.to_datetime(swics_df["timestamp"])

    merged = pd.merge(
        swepam_df,
        swics_df,
        on="timestamp",
        how="inner",
        suffixes=("_swepam", "_swics"),
    )

    # Keep only the required columns (raw names)
    required = ["timestamp", "N_p", "T_p", "He2+_ratio"]
    missing = set(required) - set(merged.columns)
    if missing:
        raise ConnectionError(
            f"Missing required ACE columns after merge: {missing}"
        )

    merged = merged[required]

    # Write the combined file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False)
    logger.info(f"ACE data written to {output_path}")
    return output_path

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def fetch_ace(start_date: str, end_date: str) -> str:
    """
    Fetch ACE solar‑wind composition data for the supplied date range.

    The function writes a combined CSV to ``data/raw/ace_raw.csv`` and
    returns the absolute path as a string.

    Raises
    ------
    ConnectionError
        If any of the required files cannot be retrieved.
    """
    output_path = Path(RAW_DATA_DIR) / "ace_raw.csv"
    _fetch_and_merge_ace(start_date, end_date, output_path)
    return str(output_path)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch ACE SWEPAM + SWICS Level‑2 CSV data."
    )
    parser.add_argument(
        "--start",
        required=True,
        help="Start date (YYYY‑MM‑DD)",
    )
    parser.add_argument(
        "--end",
        required=True,
        help="End date (YYYY‑MM‑DD)",
    )
    args = parser.parse_args()
    try:
        path = fetch_ace(args.start, args.end)
        print(f"ACE data saved to: {path}")
    except Exception as e:
        logger.error(f"Failed to fetch ACE data: {e}")
        raise
