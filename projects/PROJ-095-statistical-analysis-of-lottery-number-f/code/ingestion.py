"""
Data ingestion module for lottery draw data (Pre-CI Data Fetch, T008).

Reads the verified source URL from config/data_sources.json, verifies
reachability, downloads the historical draws CSV to
data/raw/lottery_draws.csv, computes and logs its SHA256 checksum
(also persisted to data/checksums.json), and processes the draws
while handling missing 'total_sales' (warning + retention).
"""
import json
import os
import sys
import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import pandas as pd
import numpy as np
import requests

# Ensure sibling modules are importable when run from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_utils import calculate_checksum, load_draws_csv
from exceptions import DataSourceUnavailableError, LotteryDataError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw', 'lottery_draws.csv')
PROCESSED_PATH = os.path.join(PROJECT_ROOT, 'data', 'processed', 'lottery_draws_processed.csv')
CHECKSUMS_PATH = os.path.join(PROJECT_ROOT, 'data', 'checksums.json')

# Some real endpoints reject HEAD requests; these status codes mean
# "method not supported / forbidden for HEAD" and we fall back to GET.
HEAD_FALLBACK_STATUSES = {403, 405, 501}

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


def load_config() -> Dict[str, Any]:
    """Load data source configuration from config/data_sources.json."""
    config_path = os.path.join(PROJECT_ROOT, 'config', 'data_sources.json')
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def fetch_lottery_data(url: str, output_path: str) -> str:
    """
    Fetch lottery data from a URL and save to disk.

    Steps:
    1. Verify URL reachability via HEAD request (falling back to GET
       only if the server rejects the HEAD method itself).
    2. Download the file via streaming GET and save to output_path.

    Raises:
        DataSourceUnavailableError: If the URL is unreachable or the
            download fails. Never falls back to synthetic data.
    """
    logger.info(f"Fetching data from {url}")
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    try:
        head = session.head(url, timeout=60, allow_redirects=True)
        if head.status_code in HEAD_FALLBACK_STATUSES:
            logger.warning(
                "HEAD request rejected with status %s; verifying via GET.",
                head.status_code,
            )
        else:
            head.raise_for_status()
            logger.info(
                "URL verified (HEAD request successful). Status: %s",
                head.status_code,
            )
    except requests.RequestException as e:
        logger.error(f"HEAD request failed for {url}: {e}")
        raise DataSourceUnavailableError(f"Data source unavailable: {url}") from e

    try:
        response = session.get(url, timeout=120, stream=True)
        response.raise_for_status()
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1 << 16):
                if chunk:
                    f.write(chunk)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch data from {url}: {e}")
        raise DataSourceUnavailableError(f"Data source unavailable: {url}") from e

    size = os.path.getsize(output_path)
    if size == 0:
        raise LotteryDataError(f"Downloaded file is empty: {output_path}")
    logger.info(f"Data saved to {output_path} ({size} bytes)")
    return output_path


COLUMN_ALIASES = {
    'draw date': 'draw_date',
    'drawdate': 'draw_date',
    'date': 'draw_date',
    'top prize': 'jackpot_amount',
    'jackpot': 'jackpot_amount',
    'jackpot_amount': 'jackpot_amount',
    'total sales': 'total_sales',
    'total_sales': 'total_sales',
    'sales': 'total_sales',
    'ball 1': 'ball_1',
    'ball 2': 'ball_2',
    'ball 3': 'ball_3',
    'ball 4': 'ball_4',
    'ball 5': 'ball_5',
    'ball 6': 'ball_6',
    'bonus ball': 'bonus_ball',
    'draw number': 'draw_number',
}


def _standardize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename known column aliases to the internal schema."""
    rename = {}
    for col in df.columns:
        key = str(col).strip().lower()
        if key in COLUMN_ALIASES:
            rename[col] = COLUMN_ALIASES[key]
    if rename:
        df = df.rename(columns=rename)

    # Build a 'numbers' list column from ball columns if available
    ball_cols = [f'ball_{i}' for i in range(1, 7) if f'ball_{i}' in df.columns]
    if ball_cols and 'numbers' not in df.columns:
        def to_numbers(row):
            vals = []
            for c in ball_cols:
                v = row[c]
                try:
                    iv = int(float(v))
                    vals.append(iv)
                except (TypeError, ValueError):
                    return np.nan
            return vals if len(vals) == len(ball_cols) else np.nan
        df['numbers'] = df.apply(to_numbers, axis=1)

    if 'jackpot_amount' in df.columns:
        df['jackpot_amount'] = pd.to_numeric(
            df['jackpot_amount'].astype(str)
            .str.replace(r'[^0-9.]', '', regex=True)
            .replace('', np.nan),
            errors='coerce',
        )
    return df


def process_draws(raw_path: str, processed_path: str) -> pd.DataFrame:
    """
    Process raw lottery data, handling missing 'total_sales' values.

    Edge case handling:
    - Logs a warning when 'total_sales' is missing (column or values)
    - Rows with missing sales are excluded from sales-dependent checks
      (flagged via 'has_sales') but retained for frequency analysis.
    """
    logger.info(f"Processing raw data from {raw_path}")
    df, _ = load_draws_csv(raw_path)
    if df.empty:
        raise LotteryDataError("Loaded data is empty")

    df = _standardize_columns(df)

    if 'total_sales' not in df.columns:
        logger.warning(
            "Column 'total_sales' not found in dataset. All rows will be "
            "retained for frequency analysis but excluded from "
            "sales-dependent checks."
        )
        df['total_sales'] = np.nan
    else:
        df['total_sales'] = pd.to_numeric(df['total_sales'], errors='coerce')
        missing = int(df['total_sales'].isna().sum())
        if missing > 0:
            logger.warning(
                f"Found {missing} rows ({missing/len(df):.1%}) with missing "
                "'total_sales'. These rows will be excluded from "
                "sales-dependent checks but retained for frequency analysis."
            )

    df['has_sales'] = df['total_sales'].notna()

    os.makedirs(os.path.dirname(processed_path), exist_ok=True)
    df.to_csv(processed_path, index=False)
    logger.info(f"Processed data saved to {processed_path}")
    return df


def _persist_checksum(file_path: str, checksum: str) -> None:
    """Write the real checksum of the raw file to data/checksums.json."""
    entry = {
        "sha256": checksum,
        "size_bytes": os.path.getsize(file_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    data: Dict[str, Any] = {"files": {}}
    if os.path.exists(CHECKSUMS_PATH):
        try:
            with open(CHECKSUMS_PATH, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
            if isinstance(loaded, dict) and isinstance(loaded.get('files'), dict):
                data = loaded
        except (json.JSONDecodeError, OSError):
            logger.warning("Existing checksums file unreadable; rewriting it.")
    data["files"]["lottery_draws.csv"] = entry
    os.makedirs(os.path.dirname(CHECKSUMS_PATH), exist_ok=True)
    with open(CHECKSUMS_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Checksum persisted to {CHECKSUMS_PATH}")


def main():
    """Main entry point for the ingestion script (T008)."""
    config = load_config()
    url = config.get('url')
    source_name = config.get('source_name', 'Unknown Source')
    if not url:
        raise ValueError("URL not found in config")

    logger.info(f"Starting data ingestion from {source_name}")

    if not os.path.exists(RAW_PATH):
        fetch_lottery_data(url, RAW_PATH)
    else:
        logger.info(f"Raw data already exists at {RAW_PATH}. Skipping download.")

    # Step 3: generate SHA checksum and log it
    checksum = calculate_checksum(RAW_PATH, algorithm='sha256')
    logger.info(f"SHA256 Checksum for {RAW_PATH}: {checksum}")
    _persist_checksum(RAW_PATH, checksum)

    # Step 4: process draws (handles missing total_sales)
    df = process_draws(RAW_PATH, PROCESSED_PATH)

    logger.info(f"Processing complete. Total rows: {len(df)}")
    logger.info(f"Columns: {list(df.columns)}")
    logger.info(f"Raw CSV available at: {RAW_PATH}")


if __name__ == '__main__':
    main()