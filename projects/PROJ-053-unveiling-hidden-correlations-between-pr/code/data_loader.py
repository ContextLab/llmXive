"""
Strict Data Loader for the NIST AM‑Bench dataset.

This script downloads the raw dataset from Zenodo, validates its schema,
checks for source independence between predictors and targets, and writes
a SHA‑256 checksum file.

Execution:
    python -m code.data_loader
"""
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import List

import pandas as pd
import requests
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Search term used to locate the dataset on Zenodo.
ZENODO_SEARCH_URL = "https://zenodo.org/api/records/"
ZENODO_QUERY = "NIST AM Bench"
MAX_SEARCH_RESULTS = 5

# Required columns (case‑insensitive)
REQUIRED_PREDICTORS = ["laser power", "scan speed", "layer thickness"]
REQUIRED_TARGETS = ["yield strength", "ductility"]
MIN_SAMPLES = 50

# Retry configuration
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # exponential back‑off multiplier (seconds)

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
log: logging.Logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _search_zenodo() -> List[dict]:
    """
    Perform a Zenodo API search and return a list of record dicts.
    """
    params = {
        "q": ZENODO_QUERY,
        "size": MAX_SEARCH_RESULTS,
        "sort": "mostviewed",
    }
    log.info("Searching Zenodo for dataset: %s", ZENODO_QUERY)
    response = requests.get(ZENODO_SEARCH_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    hits = data.get("hits", {}).get("hits", [])
    if not hits:
        raise FileNotFoundError("No Zenodo records found for query.")
    log.info("Found %d candidate record(s).", len(hits))
    return hits

def _choose_download_url(records: List[dict]) -> str:
    """
    From the list of Zenodo records, pick the first CSV file URL.
    """
    for rec in records:
        files = rec.get("files", [])
        for f in files:
            filename = f.get("key", "")
            if filename.lower().endswith(".csv"):
                download_url = f.get("links", {}).get("download")
                if download_url:
                    log.info("Selected file '%s' from record %s.", filename, rec.get("id"))
                    return download_url
    raise FileNotFoundError("No CSV file found in the searched Zenodo records.")

def _download_with_retries(url: str, dest_path: Path) -> None:
    """
    Download a file with exponential back‑off retry logic.
    """
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            log.info("Downloading %s (attempt %d).", url, attempt + 1)
            with requests.get(url, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(dest_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            log.info("Download completed: %s", dest_path)
            return
        except Exception as e:
            attempt += 1
            wait = BACKOFF_FACTOR ** attempt
            log.warning("Download failed (%s). Retrying in %s seconds...", e, wait)
            time.sleep(wait)
    raise FileNotFoundError(f"Failed to download after {MAX_RETRIES} attempts: {url}")

def _validate_dataframe(df: pd.DataFrame) -> None:
    """
    Validate that the dataframe meets all strict requirements.
    """
    # Sample count
    if len(df) < MIN_SAMPLES:
        raise ValueError(
            f"Insufficient samples: {len(df)} found, minimum required is {MIN_SAMPLES}."
        )
    log.info("Sample count validation passed (%d rows).", len(df))

    # Column presence (case‑insensitive)
    cols_lower = [c.lower().strip() for c in df.columns]
    missing_predictors = [
        col for col in REQUIRED_PREDICTORS if col not in cols_lower
    ]
    missing_targets = [col for col in REQUIRED_TARGETS if col not in cols_lower]

    if missing_predictors or missing_targets:
        raise ValueError(
            f"Missing required columns. Predictors missing: {missing_predictors}; "
            f"Targets missing: {missing_targets}."
        )
    log.info("Required column validation passed.")

    # Source‑independence check: ensure no target is a near‑perfect linear
    # function of any predictor (|corr| >= 0.9999)
    predictor_cols = [
        df.columns[cols_lower.index(col)] for col in REQUIRED_PREDICTORS
    ]
    target_cols = [
        df.columns[cols_lower.index(col)] for col in REQUIRED_TARGETS
    ]

    for t in target_cols:
        t_series = df[t].astype(float)
        for p in predictor_cols:
            p_series = df[p].astype(float)
            if p_series.nunique() <= 1:
                continue  # zero variance predictor cannot be used for correlation
            corr = t_series.corr(p_series)
            if abs(corr) >= 0.9999:
                raise ValueError(
                    f"Source‑independence violation: target '{t}' is "
                    f"almost perfectly correlated (corr={corr:.5f}) with predictor '{p}'."
                )
    log.info("Source‑independence validation passed.")

def _write_sha256(file_path: Path, checksum_path: Path) -> None:
    """
    Compute SHA‑256 of the given file and write it to checksum_path.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    checksum = sha256.hexdigest()
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    checksum_path.write_text(checksum + "\n")
    log.info("SHA‑256 checksum written to %s", checksum_path)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Orchestrates the strict data loading process.
    """
    # Resolve output paths using llmxive_toolkit helpers
    raw_csv_path: Path = paths.data("raw", "am_raw_data.csv")
    checksum_path: Path = paths.data("checksums", "am_raw_data.sha256")

    # Ensure parent directories exist
    raw_csv_path.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: Locate dataset on Zenodo
    records = _search_zenodo()
    download_url = _choose_download_url(records)

    # Step 2: Download with retry logic
    _download_with_retries(download_url, raw_csv_path)

    # Step 3: Load and validate
    try:
        df = pd.read_csv(raw_csv_path)
    except Exception as e:
        raise ValueError(f"Failed to read downloaded CSV: {e}")

    _validate_dataframe(df)

    # Step 4: Write checksum
    _write_sha256(raw_csv_path, checksum_path)

    log.info("Data loader completed successfully.")


if __name__ == "__main__":
    main()
