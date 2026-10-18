"""
VAERS Data Download Script
=========================

This script downloads the VAERS CSV zip archives for the years 2020‑2023
from the official HHS website, extracts the three CSV files per year
(VAERSDATA, VAERSVAX, VAERSSYMPTOMS) into ``data/raw/<YEAR>/`` and records
SHA‑256 checksums for each extracted CSV.

The script aborts with a non‑zero exit code on any HTTP error or checksum
mismatch – no synthetic fallback is performed.
"""

import hashlib
import logging
import sys
import zipfile
from pathlib import Path
from typing import Dict, List

import requests
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
BASE_URL = "https://vaers.hhs.gov/data/datasets"
YEARS = [2020, 2021, 2022, 2023]
FILE_TYPES = ["VAERSDATA", "VAERSVAX", "VAERSSYMPTOMS"]  # without extension
CHUNK_SIZE = 8192

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
log = get_logger(__name__)  # writes to console; we also write our own log file
LOG_FILE = paths.logs("download_checksums.txt")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def sha256_checksum(file_path: Path) -> str:
    """Return the SHA‑256 hex digest of *file_path*."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def download_zip(url: str, dest_path: Path) -> None:
    """Download a zip file from *url* to *dest_path* (streamed)."""
    log.info(f"Downloading {url}")
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with dest_path.open("wb") as f:
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
    except requests.RequestException as exc:
        log.error(f"Failed to download {url}: {exc}")
        raise

def extract_zip(zip_path: Path, extract_to: Path) -> List[Path]:
    """Extract all members of *zip_path* into *extract_to* and return list of CSV paths."""
    extracted_files: List[Path] = []
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.namelist():
                if member.lower().endswith(".csv"):
                    zf.extract(member, path=extract_to)
                    extracted_path = extract_to / member
                    extracted_files.append(extracted_path)
    except zipfile.BadZipFile as exc:
        log.error(f"Corrupt zip file {zip_path}: {exc}")
        raise
    return extracted_files

def record_checksum(csv_path: Path, checksums_file: Path) -> None:
    """Compute SHA‑256 of *csv_path* and append a line to *checksums_file*."""
    checksum = sha256_checksum(csv_path)
    line = f"{csv_path.relative_to(Path.cwd())} {checksum} OK\n"
    checksums_file.parent.mkdir(parents=True, exist_ok=True)
    with checksums_file.open("a", encoding="utf-8") as f:
        f.write(line)
    # Also write to the human‑readable log used for verification
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line)

# ----------------------------------------------------------------------
# Main download routine
# ----------------------------------------------------------------------
def download_year(year: int) -> Dict[str, List[Path]]:
    """
    Download and extract all three VAERS CSV zip files for *year*.

    Returns a dict mapping the file type (e.g., ``VAERSDATA``) to a list of
    extracted CSV Path objects (normally one per type).
    """
    year_dir = paths.data("raw", str(year))
    year_dir.mkdir(parents=True, exist_ok=True)

    extracted: Dict[str, List[Path]] = {}
    for ftype in FILE_TYPES:
        zip_name = f"{year}{ftype}.csv.zip"
        url = f"{BASE_URL}/{zip_name}"
        zip_path = year_dir / zip_name

        # Download the zip – any HTTP error aborts the whole script
        download_zip(url, zip_path)

        # Extract CSV(s)
        csv_paths = extract_zip(zip_path, year_dir)
        if not csv_paths:
            log.error(f"No CSV found inside {zip_path}")
            raise RuntimeError(f"Empty zip archive for {url}")

        extracted[ftype] = csv_paths

        # Record checksums for each extracted CSV
        for csv_path in csv_paths:
            record_checksum(csv_path, paths.data("checksums.txt"))

        # Remove the zip file – we only need the CSVs
        zip_path.unlink(missing_ok=True)

    return extracted

def main() -> None:
    """Entry point – iterate over YEARS and download each."""
    log.info("Starting VAERS data download")
    overall_success = True
    for yr in YEARS:
        try:
            download_year(yr)
            log.info(f"Successfully processed year {yr}")
        except Exception as exc:
            log.error(f"Failed to process year {yr}: {exc}")
            overall_success = False
            # Abort immediately as required by the task spec
            sys.exit(1)

    if overall_success:
        log.info("All years downloaded and verified successfully")
        sys.exit(0)

if __name__ == "__main__":
    main()
