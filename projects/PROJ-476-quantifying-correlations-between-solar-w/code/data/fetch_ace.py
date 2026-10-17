"""
ACE data fetcher.

Downloads ACE SWEPAM (proton density, temperature) and SWICS (helium abundance)
Level‑2 data for a given date range from the NOAA SWPC public ACE product service,
merges them, and writes a combined CSV containing the required columns:
``N_p``, ``T_p``, ``He2+_ratio``.
The file is saved under ``data/raw/ace_raw.csv`` (overwritten each call).

Implementation details:
* Streaming HTTP download with ``requests`` and exponential‑backoff retries
  (max 3 attempts).
* No synthetic data generation – on any network or parsing failure a
  ``ConnectionError`` is raised.
* The function returns the absolute path to the written CSV.
"""

import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd
import requests

from code.config import RAW_DATA_DIR
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
    # Should never be reached
    raise ConnectionError(f"Failed to download {url}")

def _parse_ace_file(txt: str, required_cols: List[str]) -> pd.DataFrame:
    """
    Parse an ACE text file (SWEPAM or SWICS) returned by the NOAA SWPC service.

    The files are space‑separated with a header line starting with ``#``.
    Column names are taken from the first non‑comment line.  The function
    extracts a ``timestamp`` column (combined from year, month, day, hour,
    minute) and retains only the columns listed in ``required_cols``.
    """
    # Split into lines and drop comment lines
    lines = [ln for ln in txt.splitlines() if not ln.lstrip().startswith("#")]
    if not lines:
        raise ConnectionError("ACE data file is empty or contains only comments.")

    # The first line after comments contains column headers
    header_line = lines[0]
    col_names = header_line.split()
    data_lines = lines[1:]

    # Load into DataFrame
    df = pd.read_csv(
        pd.compat.StringIO("\n".join(data_lines)),
        delim_whitespace=True,
        names=col_names,
        comment="#",
    )

    # Build a timestamp column.
    # ACE files usually contain the columns: year, month, day, hour, minute.
    # If they provide a 'day_of_year' instead of month/day we convert it.
    if {"year", "month", "day", "hour", "minute"}.issubset(df.columns):
        df["timestamp"] = pd.to_datetime(
            df[["year", "month", "day", "hour", "minute"]]
        )
    elif {"year", "day_of_year", "hour", "minute"}.issubset(df.columns):
        # Convert day_of_year to month/day
        df["date"] = pd.to_datetime(df["year"], format="%Y") + pd.to_timedelta(
            df["day_of_year"] - 1, unit="D"
        )
        df["timestamp"] = pd.to_datetime(
            df["date"].dt.strftime("%Y-%m-%d")
            + " "
            + df["hour"].astype(str).str.zfill(2)
            + ":"
            + df["minute"].astype(str).str.zfill(2)
        )
        df.drop(columns=["date"], inplace=True)
    else:
        raise ConnectionError(
            "Unable to construct timestamp from ACE file columns."
        )

    # Keep only required columns plus timestamp
    needed = ["timestamp"] + required_cols
    missing = set(needed) - set(df.columns)
    if missing:
        raise ConnectionError(
            f"Missing required columns in ACE file: {missing}"
        )
    return df[needed]

# ----------------------------------------------------------------------
# Core fetch logic
# ----------------------------------------------------------------------
def _fetch_and_merge_ace(start_date: str, end_date: str, output_path: Path) -> Path:
    """
    Download SWEPAM (proton density & temperature) and SWICS (helium abundance)
    data for the requested period, merge them on the ``timestamp`` column and
    write a combined CSV.

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
    # Parse date range
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")

    # URLs provided by NOAA SWPC for 1‑minute ACE products
    swepam_url = "https://services.swpc.noaa.gov/products/ace/ace_swepam_1m.txt"
    swics_url = "https://services.swpc.noaa.gov/products/ace/ace_swics_1m.txt"

    logger.debug(f"Downloading ACE SWEPAM data from {swepam_url}")
    swepam_txt = _download_text(swepam_url)

    logger.debug(f"Downloading ACE SWICS data from {swics_url}")
    swics_txt = _download_text(swics_url)

    # Parse the raw text files
    swepam_df = _parse_ace_file(swepam_txt, required_cols=["N_p", "T_p"])
    swics_df = _parse_ace_file(swics_txt, required_cols=["He2+_ratio"])

    # Filter to the requested date window (inclusive)
    mask_swepam = (swepam_df["timestamp"] >= pd.Timestamp(start_dt)) & (
        swepam_df["timestamp"] <= pd.Timestamp(end_dt) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    )
    mask_swics = (swics_df["timestamp"] >= pd.Timestamp(start_dt)) & (
        swics_df["timestamp"] <= pd.Timestamp(end_dt) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    )
    swepam_df = swepam_df.loc[mask_swepam]
    swics_df = swics_df.loc[mask_swics]

    if swepam_df.empty:
        raise ConnectionError(f"No SWEPAM data found for period {start_date} – {end_date}")
    if swics_df.empty:
        raise ConnectionError(f"No SWICS data found for period {start_date} – {end_date}")

    # Merge on timestamp (inner join ensures both measurements are present)
    merged = pd.merge(
        swepam_df,
        swics_df,
        on="timestamp",
        how="inner",
    )

    # Verify required columns are present after merge
    required = ["timestamp", "N_p", "T_p", "He2+_ratio"]
    missing = set(required) - set(merged.columns)
    if missing:
        raise ConnectionError(
            f"Missing required ACE columns after merge: {missing}"
        )

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
        If any of the required files cannot be retrieved or parsed.
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
        description="Fetch ACE SWEPAM + SWICS Level‑2 data via NOAA SWPC service."
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
