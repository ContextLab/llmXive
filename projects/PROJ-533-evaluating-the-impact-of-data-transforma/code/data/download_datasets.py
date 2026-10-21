import os
import sys
import csv
import hashlib
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd
import requests
from urllib.parse import urlparse
from sklearn.datasets import fetch_openml

# Project utilities
from code.utils.logging_config import setup_pipeline_logger
from code.utils.schema_definitions import get_datasets_headers, get_checksums_headers

# Constants
OPENML_DOMAIN = "openml.org"
UCI_DOMAIN = "archive.ics.uci.edu"
VERIFIED_SOURCES = [OPENML_DOMAIN, UCI_DOMAIN]

logger = setup_pipeline_logger("download_datasets")

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def is_valid_url(url: str) -> bool:
    """Check if a URL is syntactically valid."""
    if not url or not isinstance(url, str):
        return False
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def is_source_verified(url: str) -> bool:
    """
    Verify that the dataset source URL belongs to a canonical public domain.
    Returns True if the domain matches UCI or OpenML patterns.
    """
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        for allowed in VERIFIED_SOURCES:
            if domain == allowed or domain.endswith('.' + allowed):
                return True
        logger.warning(f"Source URL '{url}' does not match verified domains.")
        return False
    except Exception as e:
        logger.error(f"Error verifying source URL '{url}': {e}")
        return False

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: Path) -> bool:
    """Download a file from URL to dest_path (streamed)."""
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

# ----------------------------------------------------------------------
# Metadata file handling
# ----------------------------------------------------------------------
def initialize_metadata_files(data_dir: Path):
    """Create empty CSV artifacts with proper headers if they do not exist."""
    datasets_csv = data_dir / "datasets.csv"
    checksums_csv = data_dir / "checksums.csv"

    if not datasets_csv.exists():
        with open(datasets_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=get_datasets_headers())
            writer.writeheader()

    if not checksums_csv.exists():
        with open(checksums_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=get_checksums_headers())
            writer.writeheader()

def append_to_datasets_csv(data_dir: Path, dataset_info: Dict[str, Any], checksum: str):
    """Append a row to datasets.csv with the minimal required fields."""
    csv_path = data_dir / "datasets.csv"
    row = {
        "dataset_id": dataset_info["dataset_id"],
        "source_url": dataset_info["source_url"],
        "sample_size": dataset_info.get("sample_size", ""),
        "num_variables": dataset_info.get("num_variables", ""),
        "continuous_variables": dataset_info.get("continuous_variables", ""),
        "checksum": checksum,
        "skewness": "",
        "kurtosis": "",
        "included": ""  # will be filled after filtering stage
    }
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=get_datasets_headers())
        writer.writerow(row)

def append_to_checksums_csv(data_dir: Path, dataset_id: str, checksum: str):
    """Append checksum information to checksums.csv."""
    csv_path = data_dir / "checksums.csv"
    row = {
        "dataset_id": dataset_id,
        "checksum": checksum
    }
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=get_checksums_headers())
        writer.writerow(row)

# ----------------------------------------------------------------------
# Download helpers for each source type
# ----------------------------------------------------------------------
def download_openml_dataset(dataset_id: str, raw_dir: Path) -> Optional[Path]:
    """
    Download an OpenML dataset using sklearn's fetch_openml.
    The data is saved as a parquet file named ``openml_<id>.parquet``.
    """
    try:
        logger.info(f"Fetching OpenML dataset {dataset_id}")
        # fetch_openml returns a Bunch; we request as_frame for convenience
        bunch = fetch_openml(data_id=int(dataset_id), as_frame=True, version=1)
        df = bunch.frame
        # Ensure we have a DataFrame (some OpenML returns only data)
        if not isinstance(df, pd.DataFrame):
            logger.error(f"OpenML dataset {dataset_id} did not return a DataFrame")
            return None
        out_path = raw_dir / f"openml_{dataset_id}.parquet"
        df.to_parquet(out_path, index=False)
        return out_path
    except Exception as e:
        logger.error(f"Error fetching OpenML dataset {dataset_id}: {e}")
        return None

def download_uci_dataset(url: str, raw_dir: Path, dataset_id: str) -> Optional[Path]:
    """
    Download a UCI dataset given its URL.
    The file is saved in its original format (CSV or ARFF) and then,
    if it can be read by pandas, also stored as a parquet copy for downstream use.
    """
    try:
        logger.info(f"Downloading UCI dataset {dataset_id} from {url}")
        dest = raw_dir / f"uci_{dataset_id}{Path(url).suffix}"
        if not download_file(url, dest):
            return None

        # Try to read with pandas; many UCI files are CSV-like.
        try:
            df = pd.read_csv(dest, header=None, na_values='?')
            parquet_path = raw_dir / f"uci_{dataset_id}.parquet"
            df.to_parquet(parquet_path, index=False)
            return parquet_path
        except Exception:
            # If pandas cannot parse, keep the original file as raw.
            logger.warning(f"Could not parse UCI file {dest} into DataFrame; kept raw.")
            return dest
    except Exception as e:
        logger.error(f"Failed to process UCI dataset {dataset_id}: {e}")
        return None

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------
def main():
    """
    Download ≥50 public datasets from OpenML (using IDs from openml_ids.txt)
    and UCI (using URLs from uci_dataset_urls.txt). For each successful download:
    - Store as parquet in ``data/raw/`` (or keep original if parsing fails)
    - Compute SHA‑256 checksum
    - Append a provisional row to ``data/datasets.csv``
    - Append checksum row to ``data/checksums.csv``
    The script aborts with exit code 1 if fewer than 50 datasets are verified.
    """
    base_dir = Path.cwd()
    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Ensure CSV placeholders exist
    initialize_metadata_files(data_dir)

    # ------------------------------------------------------------------
    # 1. Load OpenML IDs
    # ------------------------------------------------------------------
    openml_ids_path = data_dir / "openml_ids.txt"
    if not openml_ids_path.is_file():
        logger.critical(f"Missing OpenML IDs file at {openml_ids_path}")
        sys.exit(1)

    with open(openml_ids_path, "r", encoding="utf-8") as f:
        openml_ids = [line.strip() for line in f if line.strip().isdigit()]

    # ------------------------------------------------------------------
    # 2. Load UCI URLs
    # ------------------------------------------------------------------
    uci_urls_path = data_dir / "uci_dataset_urls.txt"
    if not uci_urls_path.is_file():
        logger.critical(f"Missing UCI URLs file at {uci_urls_path}")
        sys.exit(1)

    with open(uci_urls_path, "r", encoding="utf-8") as f:
        uci_urls = [line.strip() for line in f if line.strip()]

    verified_count = 0
    processed_count = 0

    # ------------------------------------------------------------------
    # 3. Process OpenML datasets
    # ------------------------------------------------------------------
    for dataset_id in openml_ids:
        # Build a synthetic source URL for verification purposes
        source_url = f"https://{OPENML_DOMAIN}/data/download/{dataset_id}"
        if not is_source_verified(source_url):
            logger.warning(f"Skipping unverified OpenML source {source_url}")
            continue

        dest_path = download_openml_dataset(dataset_id, raw_dir)
        if dest_path and dest_path.exists():
            checksum = compute_sha256(str(dest_path))
            dataset_info = {
                "dataset_id": dataset_id,
                "source_url": source_url,
                "sample_size": "",  # to be filled later in filtering
                "num_variables": "",  # to be filled later
                "continuous_variables": ""  # to be filled later
            }
            append_to_datasets_csv(data_dir, dataset_info, checksum)
            append_to_checksums_csv(data_dir, dataset_id, checksum)
            verified_count += 1
            processed_count += 1
            logger.info(f"OpenML dataset {dataset_id} processed.")
        else:
            logger.error(f"Failed to download OpenML dataset {dataset_id}")

        # Respect a modest pause to avoid hammering the OpenML server
        time.sleep(0.2)

    # ------------------------------------------------------------------
    # 4. Process UCI datasets
    # ------------------------------------------------------------------
    for idx, url in enumerate(uci_urls, start=1):
        if not is_valid_url(url):
            logger.warning(f"Invalid UCI URL skipped: {url}")
            continue
        if not is_source_verified(url):
            logger.warning(f"Unverified UCI source skipped: {url}")
            continue

        # Use the index as a simple ID for UCI entries
        dataset_id = f"uci_{idx}"
        dest_path = download_uci_dataset(url, raw_dir, dataset_id)
        if dest_path and dest_path.exists():
            checksum = compute_sha256(str(dest_path))
            dataset_info = {
                "dataset_id": dataset_id,
                "source_url": url,
                "sample_size": "",
                "num_variables": "",
                "continuous_variables": ""
            }
            append_to_datasets_csv(data_dir, dataset_info, checksum)
            append_to_checksums_csv(data_dir, dataset_id, checksum)
            verified_count += 1
            processed_count += 1
            logger.info(f"UCI dataset {dataset_id} processed.")
        else:
            logger.error(f"Failed to download UCI dataset from {url}")

        # Small pause to be polite to the UCI server
        time.sleep(0.2)

    logger.info(f"Download phase completed: {processed_count} processed, {verified_count} verified.")
    if verified_count < 50:
        logger.error(f"Only {verified_count} datasets verified; need at least 50.")
        sys.exit(1)

if __name__ == "__main__":
    main()
