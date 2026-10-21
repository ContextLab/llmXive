import os
import sys
import csv
import hashlib
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests
from urllib.parse import urlparse

# Import from utils to avoid circular imports and ensure consistent logging
from code.utils.logging_config import setup_pipeline_logger
from code.utils.schema_definitions import get_datasets_headers, get_checksums_headers

# Constants
OPENML_DOMAIN = "openml.org"
UCI_DOMAIN = "archive.ics.uci.edu"
VERIFIED_SOURCES = [OPENML_DOMAIN, UCI_DOMAIN]

logger = setup_pipeline_logger("download_datasets")

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

def download_file(url: str, dest_path: str) -> bool:
    """Download a file from URL to dest_path."""
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def get_dataset_info_from_openml(dataset_id: int) -> Optional[Dict[str, Any]]:
    """Fetch dataset metadata from OpenML API."""
    api_url = f"https://www.openml.org/api/v1/json/data/{dataset_id}"
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "data" in data and "oml:data" in data["data"]:
            info = data["data"]["oml:data"]
            return {
                "dataset_id": str(dataset_id),
                "name": info.get("name"),
                "url": info.get("url"),
                "source": OPENML_DOMAIN,
                "format": "arff"
            }
    except Exception as e:
        logger.error(f"Error fetching OpenML dataset {dataset_id}: {e}")
        return None
    return None

def fetch_openml_datasets(min_rows: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch a list of datasets from OpenML that meet basic criteria.
    Returns a list of dataset metadata dictionaries.
    """
    search_url = "https://www.openml.org/api/v1/json/data/list/"
    params = {
        "limit": limit,
        "status": "active",
    }
    datasets: List[Dict[str, Any]] = []
    try:
        response = requests.get(search_url, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        if "data" in data and "oml:data" in data["data"]:
            for item in data["data"]["oml:data"]:
                did = item.get("did")
                url = item.get("url")
                if did and url and is_source_verified(url):
                    datasets.append({
                        "dataset_id": str(did),
                        "name": item.get("name", f"dataset_{did}"),
                        "url": url,
                        "source": OPENML_DOMAIN,
                        "format": "arff"
                    })
    except Exception as e:
        logger.error(f"Failed to fetch OpenML dataset list: {e}")
        raise ConnectionError(f"Dataset fetch failed: {e}")

    if len(datasets) < 50:
        logger.warning(f"Only fetched {len(datasets)} datasets; attempting to fetch more.")
        # Simple pagination loop (up to a reasonable bound)
        offset = limit
        while len(datasets) < 50 and offset < 2000:
            params["offset"] = offset
            try:
                resp = requests.get(search_url, params=params, timeout=60)
                resp.raise_for_status()
                more = resp.json()
                if "data" in more and "oml:data" in more["data"]:
                    for item in more["data"]["oml:data"]:
                        did = item.get("did")
                        url = item.get("url")
                        if did and url and is_source_verified(url):
                            if not any(d["dataset_id"] == str(did) for d in datasets):
                                datasets.append({
                                    "dataset_id": str(did),
                                    "name": item.get("name", f"dataset_{did}"),
                                    "url": url,
                                    "source": OPENML_DOMAIN,
                                    "format": "arff"
                                })
                offset += limit
            except Exception:
                break
    if len(datasets) < 50:
        raise ConnectionError("Failed to retrieve at least 50 public datasets from OpenML.")
    return datasets[:100]  # Return up to 100 candidates

def process_uci_dataset(dataset_info: Dict[str, Any], raw_dir: Path) -> Optional[Path]:
    """Download a UCI dataset (currently expects a direct URL to a file)."""
    url = dataset_info["url"]
    filename = f"uci_{dataset_info['dataset_id']}.arff"
    dest = raw_dir / filename
    if download_file(url, str(dest)):
        return dest
    return None

def process_openml_dataset(dataset_info: Dict[str, Any], raw_dir: Path) -> Optional[Path]:
    """Download an OpenML dataset using its standard download endpoint."""
    did = dataset_info["dataset_id"]
    url = f"https://www.openml.org/data/download/{did}"
    filename = f"openml_{did}.arff"
    dest = raw_dir / filename
    if download_file(url, str(dest)):
        return dest
    return None

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
        "source_url": dataset_info["url"],
        "sample_size": "",          # To be filled later in filtering stage
        "num_variables": "",        # To be filled later
        "continuous_variables": "",# To be filled later
        "checksum": checksum,
        "skewness": "",
        "kurtosis": "",
        "included": ""              # Will be set after filtering
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

def main():
    """Entry point for downloading and registering datasets."""
    base_dir = Path.cwd()
    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"

    raw_dir.mkdir(parents=True, exist_ok=True)
    initialize_metadata_files(data_dir)

    logger.info("Starting OpenML dataset discovery.")
    try:
        candidate_datasets = fetch_openml_datasets()
    except ConnectionError as e:
        logger.critical(str(e))
        sys.exit(1)

    processed = 0
    verified = 0
    for ds in candidate_datasets:
        if not is_source_verified(ds["url"]):
            logger.warning(f"Skipping unverified source for dataset {ds['dataset_id']}")
            continue

        logger.info(f"Downloading dataset {ds['dataset_id']} ({ds['name']})")
        dest_path = None
        if ds["source"] == OPENML_DOMAIN:
            dest_path = process_openml_dataset(ds, raw_dir)
        elif ds["source"] == UCI_DOMAIN:
            dest_path = process_uci_dataset(ds, raw_dir)

        if dest_path and dest_path.exists():
            checksum = compute_sha256(str(dest_path))
            append_to_datasets_csv(data_dir, ds, checksum)
            append_to_checksums_csv(data_dir, ds["dataset_id"], checksum)
            verified += 1
            processed += 1
        else:
            logger.error(f"Failed to retrieve dataset {ds['dataset_id']}")

    logger.info(f"Download phase completed: {processed} processed, {verified} verified.")
    if verified < 50:
        logger.error(f"Only {verified} datasets verified; need at least 50.")
        sys.exit(1)

if __name__ == "__main__":
    main()
