"""
NOAA geomagnetic index fetcher.

Downloads hourly Kp and Dst indices from the official NOAA service, 
filters them for the date range, and writes a CSV containing 
the required columns `Kp` and `Dst`.

The file is saved as `data/raw/noaa_<YYYYMM>.csv`.
"""

import time
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

from code.config import RAW_DATA_DIR
from code import logger

def _exponential_backoff(attempt: int, base: float = 1.0) -> None:
    """Sleep base * 2**attempt seconds."""
    time.sleep(base * (2 ** attempt))

def _download_text(url: str) -> str:
    """Download a text file via HTTP/HTTPS and return its content."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; llmXive/1.0)"}
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=60, stream=True, headers=headers)
            response.raise_for_status()
            return response.text
        except Exception as exc:
            logger.warning(f"Attempt {attempt + 1} failed for {url}: {exc}")
            if attempt == 2:
                raise ConnectionError(f"Unable to download {url}") from exc
            _exponential_backoff(attempt)
    raise ConnectionError(f"Failed to download {url}")

def _parse_index(txt: str, col_name: str) -> pd.DataFrame:
    """Parse NOAA index text files (Kp or Dst).
    Expected format: YYYY MM DD HH Value
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

def fetch_noaa(start_date: str, end_date: str) -> str:
    """
    Fetch NOAA Kp and Dst geomagnetic indices.
    Writes to data/raw/noaa_<YYYYMM>.csv.
    """
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    yyyymm = start_dt.strftime("%Y%m")
    output_path = Path(RAW_DATA_DIR) / f"noaa_{yyyymm}.csv"
    
    # SWPC endpoints for current/recent indices
    kp_url = "https://services.swpc.noaa.gov/products/geomagnetic/kp.txt"
    dst_url = "https://services.swpc.noaa.gov/products/geomagnetic/dst.txt"
    
    logger.debug(f"Downloading Kp from {kp_url}")
    kp_text = _download_text(kp_url)
    logger.debug(f"Downloading Dst from {dst_url}")
    dst_text = _download_text(dst_url)
    
    kp_df = _parse_index(kp_text, "Kp")
    dst_df = _parse_index(dst_text, "Dst")
    
    if kp_df.empty or dst_df.empty:
        raise ConnectionError("Downloaded NOAA files are empty or malformed.")
    
    # Merge on timestamp
    merged = pd.merge(kp_df, dst_df, on="timestamp", how="inner")
    
    # Filter to requested window
    mask = (merged["timestamp"] >= pd.Timestamp(start_dt)) & \
           (merged["timestamp"] <= pd.Timestamp(end_dt) + pd.Timedelta(days=1))
    merged = merged.loc[mask]
    
    if merged.empty:
        # If the SWPC files (which are short-term) don't cover the historical range,
        # we raise a ConnectionError as the data is effectively unavailable at this endpoint.
        raise ConnectionError(f"No NOAA data found for period {start_date} to {end_date} at SWPC endpoint.")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False)
    logger.info(f"NOAA data written to {output_path}")
    
    return str(output_path)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    args = parser.parse_args()
    try:
        path = fetch_noaa(args.start, args.end)
        print(f"NOAA data saved to: {path}")
    except Exception as e:
        logger.error(f"Failed to fetch NOAA data: {e}")
        raise