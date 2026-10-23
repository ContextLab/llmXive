"""Download daily OHLCV data for Bitcoin and Ethereum from CoinGecko.

This script:
  * Retrieves the last 5 years of daily price and volume data for BTC and ETH.
  * Aggregates raw timestamps into daily OHLCV records.
  * Stores the results as Parquet files under ``data/raw/``.
  * Computes SHA‑256 checksums for the generated files and writes them to
    ``data/checksums.json``.
  * Sets a fixed random seed (42) for reproducibility and logs the seed
    value together with progress information to ``analysis.log``.
"""

import json
import hashlib
import time
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from pycoingecko import CoinGeckoAPI

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
ASSETS = {
    "btc": {"id": "bitcoin", "filename": "btc_ohlcv.parquet"},
    "eth": {"id": "ethereum", "filename": "eth_ohlcv.parquet"},
}
# Number of years to request – 5 years.
YEARS = 5
VS_CURRENCY = "usd"
# Chunk size for range requests (days). CoinGecko returns up to ~90‑day
# intervals reliably; we use 365‑day chunks to minimise calls while staying
# within API limits.
CHUNK_DAYS = 365
# Maximum retry attempts for each API call.
MAX_RETRIES = 3
# Base back‑off seconds.
BACKOFF_BASE = 1

# ----------------------------------------------------------------------
# Initialise logger and reproducibility seed
# ----------------------------------------------------------------------
log = get_logger(__name__, log_file=str(paths.root / "analysis.log"))
SEED = 42
np.random.seed(SEED)
log.info(f"Reproducibility seed set to {SEED}")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _fetch_market_chart_range(coin_id: str, from_ts: int, to_ts: int) -> dict:
    """Fetch ``prices`` and ``total_volumes`` for a time range using CoinGecko.

    Parameters
    ----------
    coin_id: str
        CoinGecko identifier (e.g. ``bitcoin``).
    from_ts: int
        Unix timestamp (seconds) for the start of the range (inclusive).
    to_ts: int
        Unix timestamp (seconds) for the end of the range (exclusive).

    Returns
    -------
    dict
        JSON payload containing ``prices`` and ``total_volumes`` lists.

    Raises
    ------
    RuntimeError
        If the HTTP request fails or the response does not contain the
        expected keys after all retry attempts.
    """
    cg = CoinGeckoAPI()
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            log.info(
                f"Requesting market chart range for {coin_id}: "
                f"{datetime.utcfromtimestamp(from_ts).date()} → "
                f"{datetime.utcfromtimestamp(to_ts).date()} (attempt {attempt+1})"
            )
            data = cg.get_coin_market_chart_range_by_id(
                id=coin_id,
                vs_currency=VS_CURRENCY,
                from_timestamp=from_ts,
                to_timestamp=to_ts,
            )
            if not {"prices", "total_volumes"} <= data.keys():
                raise ValueError("Missing expected keys in response")
            return data
        except Exception as exc:  # pragma: no cover – exercised in CI when API fails
            attempt += 1
            wait = BACKOFF_BASE * (2 ** (attempt - 1))
            log.warning(
                f"CoinGecko request failed for {coin_id} (attempt {attempt}): {exc}. "
                f"Retrying in {wait}s..."
            )
            time.sleep(wait)
    raise RuntimeError(
        f"CoinGecko API request failed for {coin_id} after {MAX_RETRIES} attempts."
    )

def _aggregate_daily(df_price: pd.DataFrame, df_vol: pd.DataFrame) -> pd.DataFrame:
    """Convert timestamped price/volume data into daily OHLCV."""
    # Convert timestamps (ms) → datetime (UTC) → date.
    df_price["datetime"] = pd.to_datetime(df_price["timestamp"], unit="ms", utc=True)
    df_price["date"] = df_price["datetime"].dt.date

    df_vol["datetime"] = pd.to_datetime(df_vol["timestamp"], unit="ms", utc=True)
    df_vol["date"] = df_vol["datetime"].dt.date

    # Aggregate price data.
    price_agg = (
        df_price.groupby("date")
        .agg(
            open=("price", "first"),
            high=("price", "max"),
            low=("price", "min"),
            close=("price", "last"),
        )
        .reset_index()
    )

    # Aggregate volume data (sum per day).
    vol_agg = (
        df_vol.groupby("date")["volume"]
        .sum()
        .reset_index()
        .rename(columns={"volume": "volume"})
    )

    # Merge price and volume aggregates.
    daily = pd.merge(price_agg, vol_agg, on="date", how="inner")
    daily["date"] = daily["date"].astype(str)  # ISO‑8601 string
    return daily

def _write_parquet(df: pd.DataFrame, out_path: Path) -> None:
    """Write a DataFrame to Parquet, ensuring the parent directory exists."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False, engine="pyarrow")
    log.info(f"Wrote parquet file to {out_path}")

def _compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 checksum of a file."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

# ----------------------------------------------------------------------
# Main workflow
# ----------------------------------------------------------------------
def main() -> None:
    """Download data, write Parquet files, and record checksums."""
    checksums = {}

    # Define the overall date range: today back to (today - YEARS years)
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=YEARS * 365)

    for symbol, meta in ASSETS.items():
        coin_id = meta["id"]
        filename = meta["filename"]
        out_path = paths.data("raw", filename)

        # Collect price and volume records across the full range.
        all_prices = []
        all_volumes = []

        # Iterate in CHUNK_DAYS‑sized windows.
        chunk_start = datetime.combine(start_date, datetime.min.time())
        while chunk_start.date() < end_date:
            chunk_end = min(
                chunk_start + timedelta(days=CHUNK_DAYS), datetime.combine(end_date, datetime.min.time())
            )
            from_ts = int(chunk_start.timestamp())
            to_ts = int(chunk_end.timestamp())

            data = _fetch_market_chart_range(coin_id, from_ts, to_ts)

            # Extend the master lists.
            all_prices.extend(data["prices"])
            all_volumes.extend(data["total_volumes"])

            log.info(
                f"Fetched {len(data['prices'])} price points and "
                f"{len(data['total_volumes'])} volume points for {coin_id} "
                f"({chunk_start.date()} → {chunk_end.date()})"
            )

            # Move to next chunk.
            chunk_start = chunk_end

        if not all_prices or not all_volumes:
            raise RuntimeError(f"No OHLCV data retrieved for {coin_id}")

        # Build DataFrames.
        df_price = pd.DataFrame(all_prices, columns=["timestamp", "price"])
        df_vol = pd.DataFrame(all_volumes, columns=["timestamp", "volume"])

        # Aggregate to daily OHLCV.
        daily_ohlcv = _aggregate_daily(df_price, df_vol)

        # Persist to Parquet.
        _write_parquet(daily_ohlcv, out_path)

        # Compute checksum.
        checksum = _compute_sha256(out_path)
        checksums[filename] = checksum
        log.info(f"SHA‑256({filename}) = {checksum}")

    # Write checksums.json.
    checksums_path = paths.data("checksums.json")
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    with checksums_path.open("w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)
    log.info(f"Checksums written to {checksums_path}")

if __name__ == "__main__":
    start = time.time()
    try:
        main()
    finally:
        elapsed = time.time() - start
        log.info(f"download_raw_data.py completed in {elapsed:.2f} seconds")