"""
Strict Data Loader for the NIST AM‑Bench dataset.

This script downloads the raw dataset from Zenodo (via API search and fallbacks),
validates its schema, checks for source independence between predictors and
targets, and writes a SHA‑256 checksum file.

Execution:
    python -m code.data_loader
"""
import hashlib
import logging
import time
import zipfile
from pathlib import Path
from typing import List
from urllib.parse import urlparse

import pandas as pd
import requests
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Zenodo API endpoints
ZENODO_SEARCH_URL = "https://zenodo.org/api/records/"
ZENODO_QUERY = "NIST AM Bench"
MAX_SEARCH_RESULTS = 5

# Required columns (normalized names: lowercase, spaces to underscores)
REQUIRED_PREDICTORS = [
    "laser_power",
    "scan_speed",
    "layer_thickness",
]
REQUIRED_TARGETS = ["yield_strength", "ductility"]
MIN_SAMPLES = 50

# Retry configuration
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # exponential back‑off multiplier (seconds)

# Acceptable file extensions
ACCEPTED_EXTENSIONS = (".csv", ".zip", ".xlsx", ".xls", ".txt", ".json")

# Fallback URLs: Using the API-based download pattern which is more stable than direct links
# Record ID 10428042 is the NIST AM-Bench record.
FALLBACK_DOWNLOAD_URLS = [
    "https://zenodo.org/api/records/10428042/files/NIST_AM_Bench.csv/download",
    "https://zenodo.org/record/10428042/files/NIST_AM_Bench.csv?download=1",
]

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
    try:
        response = requests.get(ZENODO_SEARCH_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            log.warning("No Zenodo records found for query.")
            return []
        log.info("Found %d candidate record(s).", len(hits))
        return hits
    except Exception as e:
        log.error("Zenodo API search failed: %s", e)
        return []

def _choose_download_url(records: List[dict]) -> str:
    """
    Pick the first acceptable file URL from search results or use fallbacks.
    """
    for rec in records:
        files = rec.get("files", [])
        for f in files:
            filename = f.get("key", "")
            lower_name = filename.lower()
            if any(lower_name.endswith(ext) for ext in ACCEPTED_EXTENSIONS):
                download_url = f.get("links", {}).get("download")
                if download_url:
                    log.info("Selected file '%s' from Zenodo record.", filename)
                    return download_url
    
    log.warning("No acceptable file found in search results; trying fallbacks.")
    return FALLBACK_DOWNLOAD_URLS[0]

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
            if attempt == MAX_RETRIES:
                raise FileNotFoundError(f"Failed to download after {MAX_RETRIES} attempts: {url}. Error: {e}")
            wait = BACKOFF_FACTOR ** attempt
            log.warning("Download failed (%s). Retrying in %s seconds...", e, wait)
            time.sleep(wait)

def _extract_zip_if_needed(zip_path: Path, target_csv_path: Path) -> None:
    """
    Extract the first CSV from a ZIP archive.
    """
    if zip_path.suffix.lower() != ".zip":
        return

    log.info("Extracting ZIP archive %s", zip_path)
    with zipfile.ZipFile(zip_path, "r") as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise FileNotFoundError(f"No CSV files found inside ZIP archive {zip_path}")
        first_csv = csv_names[0]
        extracted_path = zf.extract(first_csv, path=zip_path.parent)
        Path(extracted_path).rename(target_csv_path)
    zip_path.unlink(missing_ok=True)

def _convert_format_to_csv(file_path: Path, target_csv_path: Path) -> None:
    """
    Convert Excel, JSON, or TXT to CSV.
    """
    suffix = file_path.suffix.lower()
    log.info("Converting %s file %s to CSV", suffix, file_path)
    if suffix in (".xlsx", ".xls"):
        df = pd.read_excel(file_path, engine="openpyxl")
    elif suffix == ".json":
        df = pd.read_json(file_path)
    elif suffix == ".txt":
        df = pd.read_csv(file_path, sep=",")
    else:
        raise ValueError(f"Unsupported conversion format: {suffix}")
    
    df.to_csv(target_csv_path, index=False)
    file_path.unlink(missing_ok=True)

def _normalize_column_name(col: str) -> str:
    """
    Make column name comparison case‑insensitive and tolerant of spaces vs. underscores.
    """
    return col.lower().strip().replace(" ", "_")

def _validate_dataframe(df: pd.DataFrame) -> None:
    """
    Validate that the dataframe meets all strict requirements.
    """
    # 1. Sample count
    if len(df) < MIN_SAMPLES:
        raise ValueError(f"Insufficient samples: {len(df)} found, minimum required is {MIN_SAMPLES}.")
    log.info("Sample count validation passed (%d rows).", len(df))

    # 2. Column presence
    cols_normalized = [_normalize_column_name(c) for c in df.columns]
    
    missing_predictors = [p for p in REQUIRED_PREDICTORS if p not in cols_normalized]
    missing_targets = [t for t in REQUIRED_TARGETS if t not in cols_normalized]

    if missing_predictors or missing_targets:
        raise ValueError(
            f"Missing required columns. Predictors missing: {missing_predictors}; "
            f"Targets missing: {missing_targets}."
        )
    log.info("Required column validation passed.")

    # 3. Source‑independence check
    name_map = { _normalize_column_name(c): c for c in df.columns }
    predictor_cols = [name_map[p] for p in REQUIRED_PREDICTORS]
    target_cols = [name_map[t] for t in REQUIRED_TARGETS]

    for t in target_cols:
        t_series = pd.to_numeric(df[t], errors='coerce')
        for p in predictor_cols:
            p_series = pd.to_numeric(df[p], errors='coerce')
            if p_series.nunique() <= 1:
                continue
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
    raw_csv_path: Path = paths.data("raw", "am_raw_data.csv")
    checksum_path: Path = paths.data("checksums", "am_raw_data.sha256")
    raw_csv_path.parent.mkdir(parents=True, exist_ok=True)

    # Step 1: Locate dataset
    records = _search_zenodo()
    download_url = _choose_download_url(records)

    # Determine file extension
    parsed = urlparse(download_url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix == "" or suffix not in ACCEPTED_EXTENSIONS:
        # Handle cases where suffix is missing in URL (e.g., /download endpoint)
        # Default to .csv for the fallback NIST AM-Bench
        suffix = ".csv"

    temp_download_path = raw_csv_path.with_suffix(suffix)

    # Step 2: Download
    _download_with_retries(download_url, temp_download_path)

    # Step 3: Handle format
    if suffix == ".zip":
        _extract_zip_if_needed(temp_download_path, raw_csv_path)
    elif suffix in (".xlsx", ".xls", ".txt", ".json"):
        _convert_format_to_csv(temp_download_path, raw_csv_path)
    else:
        # Assume CSV
        temp_download_path.rename(raw_csv_path)

    # Step 4: Load and validate
    try:
        df = pd.read_csv(raw_csv_path)
    except Exception as e:
        raise ValueError(f"Failed to read downloaded CSV: {e}")

    _validate_dataframe(df)

    # Step 5: Write checksum
    _write_sha256(raw_csv_path, checksum_path)

    log.info("Data loader completed successfully.")

if __name__ == "__main__":
    main()