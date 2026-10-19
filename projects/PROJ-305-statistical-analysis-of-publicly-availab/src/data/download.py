"""
VAERS Data Download Script
=========================

This script downloads the VAERS CSV files for the years 2020-2023 from the
official HHS/VAERS source. For each year Y in {2020, 2021, 2022, 2023}, 
it downloads three zip files:
  - {Y}VAERSDATA.csv.zip
  - {Y}VAERSVAX.csv.zip
  - {Y}VAERSSYMPTOMS.csv.zip

The files are extracted to `data/raw/{Y}/`. 
After each successful download and extraction, a SHA-256 checksum is computed 
and appended to `data/checksums.txt` and `logs/download_checksums.txt`.

Any non-200 HTTP response or extraction error raises an exception and 
exits with a non-zero status. No synthetic fallback is performed.
"""

import hashlib
import logging
import sys
import zipfile
from pathlib import Path
from typing import List

import requests
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Official VAERS data source
BASE_URL = "https://vaers.hhs.gov/data/datasets"
YEARS = [2020, 2021, 2022, 2023]
FILE_TYPES = ["VAERSDATA", "VAERSVAX", "VAERSSYMPTOMS"]
CHUNK_SIZE = 8192

# User-Agent is critical for government sites to avoid 403/404 blocks
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
log = get_logger(__name__)
LOG_FILE = paths.logs("download_checksums.txt")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def sha256_checksum(file_path: Path) -> str:
    """Return the SHA-256 hex digest of *file_path*."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def record_checksum(csv_path: Path, checksums_file: Path) -> None:
    """Compute SHA-256 of *csv_path* and append a line to *checksums_file*."""
    checksum = sha256_checksum(csv_path)
    rel_path = csv_path.relative_to(Path.cwd())
    line = f"{rel_path} {checksum} OK\n"
    checksums_file.parent.mkdir(parents=True, exist_ok=True)
    with checksums_file.open("a", encoding="utf-8") as f:
        f.write(line)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line)

def download_and_extract(year: int, file_type: str) -> None:
    """Download a specific VAERS zip and extract its content."""
    filename = f"{year}{file_type}.csv.zip"
    url = f"{BASE_URL}/{filename}"
    
    # Destination for the zip and the extracted CSV
    zip_dest = paths.data("raw", str(year), filename)
    zip_dest.parent.mkdir(parents=True, exist_ok=True)
    
    log.info(f"Downloading {url}")
    try:
        with requests.get(url, stream=True, timeout=60, headers=HEADERS) as r:
            r.raise_for_status()
            with zip_dest.open("wb") as f:
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
    except Exception as e:
        log.error(f"Failed to download {url}: {e}")
        raise SystemExit(1)

    # Extract the zip
    try:
        with zipfile.ZipFile(zip_dest, "r") as zf:
            # VAERS zips usually contain one CSV with the same name (minus .zip)
            for member in zf.namelist():
                if member.endswith(".csv"):
                    target_path = zip_dest.parent / member
                    log.info(f"Extracting {member} to {target_path}")
                    with zf.open(member) as src, target_path.open("wb") as dst:
                        while True:
                            chunk = src.read(CHUNK_SIZE)
                            if not chunk:
                                break
                            dst.write(chunk)
                    
                    # Record checksum for the extracted CSV
                    record_checksum(target_path, paths.data("checksums.txt"))
    except Exception as e:
        log.error(f"Failed to extract {filename}: {e}")
        raise SystemExit(1)
    finally:
        # Clean up zip file
        if zip_dest.exists():
            zip_dest.unlink()

def verify_downloads() -> None:
    """Verify that all 12 expected CSVs are present and non-empty."""
    missing = []
    for year in YEARS:
        for ftype in FILE_TYPES:
            expected_name = f"{year}{ftype}.csv"
            p = paths.data("raw", str(year), expected_name)
            if not p.is_file() or p.stat().st_size == 0:
                missing.append(str(p))
    
    if missing:
        log.error(f"Missing or empty files: {missing}")
        raise SystemExit(1)
    log.info("All 12 VAERS files verified.")

def main() -> None:
    """Main entry point for VAERS data download."""
    log.info("Starting VAERS data download process")
    for year in YEARS:
        for ftype in FILE_TYPES:
            download_and_extract(year, ftype)
    
    verify_downloads()
    log.info("VAERS data download and verification completed successfully.")

if __name__ == "__main__":
    main()
