"""
ACE data fetcher.

Downloads ACE SWEPAM (proton density, temperature) and SWICS (helium abundance)
Level-2 data for a given date range from the NASA CDAWeb public archive,
merges them, and writes a combined CSV containing the required columns:
`N_p`, `T_p`, `He2+_ratio`.

The file is saved as `data/raw/ace_<YYYYMM>.csv`.
"""

import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd
import requests
from io import StringIO

from code.config import RAW_DATA_DIR
from code import logger

def _exponential_backoff(attempt: int, base: float = 1.0) -> None:
    """Sleep base * 2**attempt seconds."""
    time.sleep(base * (2 ** attempt))

def _download_text(url: str) -> str:
    """Download a text file via HTTP/HTTPS and return its content.
    Uses streaming to handle potentially large archive files.
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; llmXive/1.0)"}
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=60, stream=True, headers=headers)
            response.raise_for_status()
            # For these specific archive files, we read the stream into a string
            # since pandas needs a buffer or string for read_csv.
            return response.text
        except Exception as exc:
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {exc}")
            if attempt == 2:
                raise ConnectionError(f"Unable to download {url}") from exc
            _exponential_backoff(attempt)
    raise ConnectionError(f"Failed to download {url}")

def _parse_ace_file(txt: str, required_cols: List[str]) -> pd.DataFrame:
    """
    Parse an ACE archive text file.
    Archive files typically have a header starting with '#' and use
    whitespace separation.
    """
    # Filter out comment lines
    lines = [ln for ln in txt.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    if not lines:
        raise ConnectionError("ACE data file is empty or contains only comments.")

    # The first non-comment line is the header
    header = lines[0].split()
    data = "\n".join(lines[1:])

    df = pd.read_csv(StringIO(data), sep=r'\s+', names=header)

    # CDAWeb ACE Level 2 files usually provide timestamp as a single column
    # or as year, month, day, hour, minute.
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    elif {"year", "month", "day", "hour", "minute"}.issubset(df.columns):
        df["timestamp"] = pd.to_datetime(df[["year", "month", "day", "hour", "minute"]])
    else:
        # Fallback: try to infer from the first column if it looks like a date
        try:
            df["timestamp"] = pd.to_datetime(df.iloc[:, 0])
        except Exception:
            raise ConnectionError("Unable to parse timestamp from ACE file.")

    # Keep only required columns plus timestamp
    needed = ["timestamp"] + required_cols
    missing = set(needed) - set(df.columns)
    if missing:
        # Some files use different naming (e.g., 'N_p' vs 'proton_density')
        # The spec explicitly mandates N_p, T_p, He2+_ratio
        raise ConnectionError(f"Missing required columns in ACE file: {missing}")
    
    return df[needed]

def fetch_ace(start_date: str, end_date: str) -> str:
    """
    Fetch ACE solar-wind composition data for the supplied date range.
    Writes to data/raw/ace_<YYYYMM>.csv.
    """
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Generate YYYYMM for the filename
    yyyymm = start_dt.strftime("%Y%m")
    output_path = Path(RAW_DATA_DIR) / f"ace_{yyyymm}.csv"
    
    # Determine years to fetch from archive
    years = range(start_dt.year, end_dt.year + 1)
    
    all_swepam = []
    all_swics = []
    
    for year in years:
        # CDAWeb Archive URLs for ACE Level 2
        swepam_url = f"https://cdaweb.gsfc.nasa.gov/pub/data/ace/swepam/level2/ace_swepam_l2_{year}.txt"
        swics_url = f"https://cdaweb.gsfc.nasa.gov/pub/data/ace/swics/level2/ace_swics_l2_{year}.txt"
        
        try:
            logger.debug(f"Fetching SWEPAM {year}...")
            txt_p = _download_text(swepam_url)
            all_swepam.append(_parse_ace_file(txt_p, ["N_p", "T_p"]))
        except ConnectionError as e:
            logger.error(f"Could not fetch SWEPAM for {year}: {e}")
            # If we can't get the data for the requested range, we must fail
            raise

        try:
            logger.debug(f"Fetching SWICS {year}...")
            txt_s = _download_text(swics_url)
            all_swics.append(_parse_ace_file(txt_s, ["He2+_ratio"]))
        except ConnectionError as e:
            logger.error(f"Could not fetch SWICS for {year}: {e}")
            raise

    # Merge yearly chunks
    swepam_df = pd.concat(all_swepam)
    swics_df = pd.concat(all_swics)
    
    # Filter to requested window
    mask_p = (swepam_df["timestamp"] >= pd.Timestamp(start_dt)) & \
             (swepam_df["timestamp"] <= pd.Timestamp(end_dt) + pd.Timedelta(days=1))
    swepam_df = swepam_df.loc[mask_p]
    
    mask_s = (swics_df["timestamp"] >= pd.Timestamp(start_dt)) & \
             (swics_df["timestamp"] <= pd.Timestamp(end_dt) + pd.Timedelta(days=1))
    swics_df = swics_df.loc[mask_s]
    
    if swepam_df.empty or swics_df.empty:
        raise ConnectionError(f"No ACE data found for period {start_date} to {end_date}")
    
    # Merge on timestamp
    merged = pd.merge(swepam_df, swics_df, on="timestamp", how="inner")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False)
    logger.info(f"ACE data written to {output_path}")
    
    return str(output_path)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    args = parser.parse_args()
    try:
        path = fetch_ace(args.start, args.end)
        print(f"ACE data saved to: {path}")
    except Exception as e:
        logger.error(f"Failed to fetch ACE data: {e}")
        raise
# ----------------------------------------------------------------------
