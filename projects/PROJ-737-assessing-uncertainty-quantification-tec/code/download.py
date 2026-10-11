"""
Download module for fetching real materials datasets.

Fetches:
- OQMD Band Gap
- OQMD Formation Energy (substituted for Elastic Modulus)
- AFLOW Thermal Conductivity

Implements strict failure policy: any failure to fetch a dataset (including all fallbacks)
raises an exception, causing the whole download step to fail loudly.
Caps each dataset at 5,000 samples using a fixed random seed (42) and records
per‑dataset metadata (including the applied cap and checksum) in JSON files.
"""
import os
import hashlib
import time
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import requests
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
DATA_RAW_DIR = Path("data/raw")
CHECKSUMS_FILE = DATA_RAW_DIR / "checksums.txt"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
RATE_LIMIT_DELAY = 60  # seconds between requests to avoid 429
SAMPLE_CAP = 5000
RANDOM_SEED = 42

# Real data sources (public CSV mirrors)
DATASETS = {
    "oqmd_band_gap": {
        "url": "https://raw.githubusercontent.com/materialsproject/materials-database/master/oqmd_band_gap_sample.csv",
        "fallback": "https://raw.githubusercontent.com/hackingmaterials/automatminer/master/automatminer_demo/band_gap.csv",
        "filename": "oqmd_band_gap.csv",
        "description": "OQMD Band Gap (eV)"
    },
    "oqmd_formation_energy": {
        "url": "https://raw.githubusercontent.com/materialsproject/materials-database/master/oqmd_formation_energy_sample.csv",
        "fallback": "https://raw.githubusercontent.com/hackingmaterials/automatminer/master/automatminer_demo/formation_energy.csv",
        "filename": "oqmd_formation_energy.csv",
        "description": "OQMD Formation Energy (eV/atom) - Substituted for Elastic Modulus"
    },
    "aflow_thermal_conductivity": {
        "url": "https://raw.githubusercontent.com/materialsdata/aflow/master/examples/thermal_conductivity_sample.csv",
        "fallback": "https://raw.githubusercontent.com/materialsproject/materials-database/master/aflow_thermal_sample.csv",
        "filename": "aflow_thermal_conductivity.csv",
        "description": "AFLOW Thermal Conductivity (W/mK)"
    }
}

def compute_md5(filepath: Path) -> str:
    """Compute MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def fetch_with_retry(url: str, fallback_url: Optional[str] = None) -> pd.DataFrame:
    """
    Fetch data from URL with retry logic and rate‑limit handling.
    Falls back to an alternative URL if the primary fails.
    Returns a DataFrame on success; raises RuntimeError on total failure.
    """
    urls_to_try = [url]
    if fallback_url:
        urls_to_try.append(fallback_url)

    for current_url in urls_to_try:
        for attempt in range(MAX_RETRIES):
            try:
                logger.info(f"Attempting to fetch from {current_url} (Attempt {attempt+1}/{MAX_RETRIES})")
                response = requests.get(current_url, timeout=30)

                if response.status_code == 429:
                    logger.warning("Rate limit hit. Waiting before retry...")
                    time.sleep(RATE_LIMIT_DELAY * (attempt + 1))
                    continue

                response.raise_for_status()

                # Assume CSV content
                try:
                    df = pd.read_csv(pd.compat.StringIO(response.text))
                    logger.info(f"Successfully fetched CSV from {current_url}")
                    return df
                except Exception as parse_error:
                    logger.error(f"Failed to parse CSV from {current_url}: {parse_error}")
                    # Cannot parse, try next attempt / next URL
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error for {current_url}: {e}")

            if attempt < MAX_RETRIES - 1:
                sleep_time = RETRY_DELAY * (attempt + 1)
                logger.info(f"Retrying after {sleep_time}s...")
                time.sleep(sleep_time)

    raise RuntimeError(f"All attempts failed for URLs: {urls_to_try}")

def save_dataset(df: pd.DataFrame, filename: str, dataset_key: str) -> Path:
    """Save dataset to data/raw/ and compute its checksum. Returns the file path."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    filepath = DATA_RAW_DIR / filename
    df.to_csv(filepath, index=False)
    checksum = compute_md5(filepath)

    # Append checksum entry
    with open(CHECKSUMS_FILE, "a") as f:
        f.write(f"{dataset_key},{filename},{checksum}\n")

    logger.info(f"Saved {filename} ({filepath.stat().st_size} bytes) with MD5 {checksum}")
    return filepath

def write_metadata(dataset_key: str, filename: str, df: pd.DataFrame, checksum: str) -> None:
    """Write a JSON metadata file for a downloaded dataset."""
    metadata = {
        "dataset_key": dataset_key,
        "filename": filename,
        "num_samples": int(df.shape[0]),
        "cap_applied": SAMPLE_CAP,
        "checksum_md5": checksum,
        "download_timestamp": pd.Timestamp.utcnow().isoformat()
    }
    metadata_path = DATA_RAW_DIR / f"{dataset_key}_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Wrote metadata to {metadata_path}")

def cap_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Cap the dataframe to SAMPLE_CAP rows using a fixed random seed."""
    if len(df) > SAMPLE_CAP:
        logger.info(f"Dataset has {len(df)} rows; capping to {SAMPLE_CAP} with seed {RANDOM_SEED}")
        return df.sample(n=SAMPLE_CAP, random_state=RANDOM_SEED).reset_index(drop=True)
    else:
        logger.info(f"Dataset size ({len(df)}) <= cap ({SAMPLE_CAP}); no capping applied")
        return df

def download_all() -> None:
    """Download all required datasets, enforce caps, and write metadata."""
    logger.info("Starting dataset download process...")

    for key, cfg in DATASETS.items():
        logger.info(f"Processing dataset: {cfg['description']} (key={key})")

        # Attempt to fetch; will raise on total failure
        df = fetch_with_retry(cfg["url"], cfg.get("fallback"))
        df = cap_dataframe(df)

        # Save and compute checksum
        saved_path = save_dataset(df, cfg["filename"], key)
        checksum = compute_md5(saved_path)

        # Write per‑dataset metadata
        write_metadata(key, cfg["filename"], df, checksum)

    logger.info("All datasets downloaded and processed successfully.")

if __name__ == "__main__":
    download_all()
