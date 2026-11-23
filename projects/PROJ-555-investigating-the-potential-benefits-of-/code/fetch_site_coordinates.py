"""
fetch_site_coordinates.py
-------------------------

Implements Task T003: download the World Database of Protected Areas (WDPA),
extract the CSV, filter for candidate sites, and write
``data/processed/site_metadata.csv``.  The script also appends a log entry
to ``data/raw/query_log.json`` (using the helper from ``code.data_acquisition``)
and records any fatal errors in ``data/raw/fetch_error.log``.
"""

import logging
import json
import sys
import zipfile
from pathlib import Path
from datetime import datetime
from typing import List

import pandas as pd
import requests

# Local imports
from config import ensure_directories
from data_acquisition import log_api_query

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
WDPA_DOWNLOAD_URL = (
    "https://dopa.jrc.ec.europa.eu/download.php?file=WDPA_WDOECM_csv.zip"
)
# The expected CSV name inside the zip (observed from the official archive)
WDPA_CSV_NAME = "WDPA_WDOECM_csv.csv"

# ----------------------------------------------------------------------
# Logging helpers
# ----------------------------------------------------------------------
LOG = logging.getLogger(__name__)


def setup_logger(name: str = __name__) -> logging.Logger:
    """Configure a module‑level logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


# ----------------------------------------------------------------------
# Core functions
# ----------------------------------------------------------------------
def download_wdpa_release(output_dir: Path) -> Path:
    """
    Download the latest WDPA CSV zip file from the official source.
    Returns the path to the downloaded zip file.

    Raises
    ------
    RuntimeError
        If the HTTP request fails or the response is not a zip file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / "WDPA_WDOECM_csv.zip"

    LOG.info(f"Downloading WDPA release from {WDPA_DOWNLOAD_URL}")
    response = requests.get(WDPA_DOWNLOAD_URL, stream=True, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to download WDPA archive: HTTP {response.status_code}"
        )

    # Write the zip file to disk
    with zip_path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    LOG.info(f"WDPA archive saved to {zip_path}")
    return zip_path


def extract_and_load_wdpa(zip_path: Path) -> pd.DataFrame:
    """
    Extract the CSV from the WDPA zip archive and load it into a DataFrame.

    Raises
    ------
    RuntimeError
        If extraction fails or the expected CSV is not present.
    """
    LOG.info(f"Extracting WDPA CSV from {zip_path}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        # Find the first CSV file (the archive typically contains only one)
        csv_candidates = [name for name in zf.namelist() if name.lower().endswith(".csv")]
        if not csv_candidates:
            raise RuntimeError("No CSV file found inside the WDPA zip archive.")
        csv_name = csv_candidates[0]
        with zf.open(csv_name) as csv_file:
            df = pd.read_csv(csv_file, low_memory=False)

    LOG.info(f"Loaded WDPA data with {len(df)} rows")
    return df


def filter_and_sample_sites(df: pd.DataFrame, target_count: int = 30) -> pd.DataFrame:
    """
    Filter the WDPA DataFrame for rows that contain the required metadata
    and sample up to ``target_count`` sites.

    Required columns (case‑insensitive):
        - WDPAID
        - DESIG_TYPE
        - LATITUDE
        - LONGITUDE
        - BIOME
        - DESIG_STATUS

    The returned DataFrame contains the columns required by downstream
    tasks and is written to ``data/processed/site_metadata.csv``.
    """
    required_cols = {
        "WDPAID": "site_id",
        "DESIG_TYPE": "site_type",
        "LATITUDE": "latitude",
        "LONGITUDE": "longitude",
        "BIOME": "biome",
        "DESIG_STATUS": "protection_status",
    }

    # Normalise column names to upper case for case‑insensitive matching
    df_cols_upper = {c.upper(): c for c in df.columns}
    missing = [c for c in required_cols if c not in df_cols_upper]
    if missing:
        raise RuntimeError(f"WDPA CSV missing required columns: {missing}")

    # Select and rename columns
    selected = df[[df_cols_upper[c] for c in required_cols]]
    selected = selected.rename(columns={df_cols_upper[k]: v for k, v in required_cols.items()})

    # Drop rows with any missing critical information
    selected = selected.dropna(subset=list(required_cols.values()))

    # Sample without replacement (shuffle first for randomness)
    sampled = selected.sample(
        n=min(target_count, len(selected)), replace=False, random_state=42
    ).reset_index(drop=True)

    # Add an empty ``pairing_id`` column – it will be filled later in the pipeline
    sampled["pairing_id"] = pd.NA

    LOG.info(
        f"Filtered WDPA to {len(sampled)} candidate sites (target {target_count})"
    )
    return sampled


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Orchestrates the download, extraction, filtering and writing of site
    metadata.  All side‑effects are written to project‑owned directories.
    """
    try:
        ensure_directories()
        raw_dir = Path("data") / "raw"
        processed_dir = Path("data") / "processed"

        # 1. Download the WDPA zip
        zip_path = download_wdpa_release(raw_dir)

        # 2. Log the API request (required by T014 later)
        log_api_query(
            query_params={"url": WDPA_DOWNLOAD_URL, "downloaded_file": str(zip_path.name)},
            version="1.0.0",
        )

        # 3. Extract CSV and load into a DataFrame
        wdpa_df = extract_and_load_wdpa(zip_path)

        # 4. Filter, rename, and sample sites
        site_df = filter_and_sample_sites(wdpa_df, target_count=30)

        # 5. Write the output CSV
        output_csv = processed_dir / "site_metadata.csv"
        site_df.to_csv(output_csv, index=False)

        LOG.info(f"Site metadata written to {output_csv}")

    except Exception as exc:
        # Record the error details for debugging (platform‑owned logs are not allowed)
        error_log_path = Path("data") / "raw" / "fetch_error.log"
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(exc),
            "stage": "fetch_site_coordinates",
        }
        # Append JSON line (one per error)
        with error_log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(error_entry) + "\n")
        raise RuntimeError(f"Failed to fetch site coordinates: {exc}") from exc


if __name__ == "__main__":
    # When executed directly (e.g., via ``python code/fetch_site_coordinates.py``)
    # we run the pipeline and let any raised exception terminate the process
    # with a non‑zero exit code.
    main()
