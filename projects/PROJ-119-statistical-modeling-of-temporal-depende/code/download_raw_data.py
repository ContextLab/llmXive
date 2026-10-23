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

import numpy as np
import pandas as pd
import yaml
import jsonschema
from pycoingecko import CoinGeckoAPI

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
ASSETS = {
    "btc": {"id": "bitcoin", "filename": "btc_ohlcv.parquet"},
    "eth": {"id": "ethereum", "filename": "eth_ohlcv.parquet"},
}
# Number of days to request – 5 years ≈ 5 * 365 = 1825 days.
DAYS = 1825
VS_CURRENCY = "usd"

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
def _fetch_market_chart(coin_id: str, days: int) -> dict:
    """Fetch ``prices`` and ``total_volumes`` from CoinGecko using pycoingecko.

    Parameters
    ----------
    coin_id: str
        CoinGecko identifier (e.g. ``bitcoin``).
    days: int
        Number of days of data to request.

    Returns
    -------
    dict
        JSON payload containing ``prices`` and ``total_volumes`` lists.

    Raises
    ------
    RuntimeError
        If the HTTP request fails or the response does not contain the
        expected keys.
    """
    cg = CoinGeckoAPI()
    log.info(f"Requesting market chart for {coin_id} ({days} days) …")
    try:
        data = cg.get_coin_market_chart_by_id(
            id=coin_id, vs_currency=VS_CURRENCY, days=days, interval="daily"
        )
    except Exception as exc:
        raise RuntimeError(
            f"CoinGecko API request failed for {coin_id}: {exc}"
        ) from exc

    if not {"prices", "total_volumes"} <= data.keys():
        raise RuntimeError(
            f"Unexpected response structure for {coin_id}: missing keys."
        )
    return data

def _aggregate_daily(df_price: pd.DataFrame, df_vol: pd.DataFrame) -> pd.DataFrame:
    """Convert timestamped price/volume data into daily OHLCV.

    Parameters
    ----------
    df_price: pd.DataFrame
        Columns ``timestamp`` (ms) and ``price``.
    df_vol: pd.DataFrame
        Columns ``timestamp`` (ms) and ``volume``.

    Returns
    -------
    pd.DataFrame
        Daily records with columns:
        ``date`` (ISO string), ``open``, ``high``, ``low``, ``close``,
        ``volume``.
    """
    # Convert timestamps to pandas datetime (UTC) and then to date.
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

    for symbol, meta in ASSETS.items():
        coin_id = meta["id"]
        filename = meta["filename"]
        out_path = paths.data("raw", filename)

        # 1. Download raw market chart data.
        raw = _fetch_market_chart(coin_id, DAYS)

        # 2. Build DataFrames for price and volume.
        df_price = pd.DataFrame(
            raw["prices"], columns=["timestamp", "price"]
        )
        df_vol = pd.DataFrame(
            raw["total_volumes"], columns=["timestamp", "volume"]
        )

        # 3. Aggregate to daily OHLCV.
        daily_ohlcv = _aggregate_daily(df_price, df_vol)

        # 4. Persist to Parquet.
        _write_parquet(daily_ohlcv, out_path)

        # 5. Compute checksum.
        checksum = _compute_sha256(out_path)
        checksums[filename] = checksum
        log.info(f"SHA‑256({filename}) = {checksum}")

    # 6. Write checksums.json.
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
