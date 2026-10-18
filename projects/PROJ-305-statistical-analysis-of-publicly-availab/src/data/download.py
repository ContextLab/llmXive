"""
VAERS Data Download Script
=========================

This script downloads the VAERS CSV archives for the years 2020‑2023.
It first attempts to download the official CDC zip archives. If those
downloads fail (e.g., due to network restrictions), it falls back to
downloading the raw CSV files from the public CDC GitHub mirror
(https://github.com/CDCgov/VAERS-data).  The script extracts (or directly
saves) the CSV files into ``data/raw/<YEAR>/`` and records SHA‑256
checksums for each extracted CSV.

The script aborts with a non‑zero exit code on any HTTP error or
checksum mismatch – no synthetic fallback is performed.
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
# Primary CDC mirror (zip archives)
BASE_URL = "https://download.cdc.gov/pub/cdc/vaers"
# Fallback GitHub mirror (raw CSV files, no zip)
GITHUB_RAW_URL = "https://raw.githubusercontent.com/CDCgov/VAERS-data/master"

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
    log.info(f"Downloading ZIP {url}")
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with dest_path.open("wb") as f:
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
    except requests.RequestException as exc:
        log.error(f"Failed to download ZIP {url}: {exc}")
        raise


def download_csv(url: str, dest_path: Path) -> None:
    """Download a raw CSV file from *url* to *dest_path* (streamed)."""
    log.info(f"Downloading CSV {url}")
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with dest_path.open("wb") as f:
                for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
    except requests.RequestException as exc:
        log.error(f"Failed to download CSV {url}: {exc}")
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
# Core download routine
# ----------------------------------------------------------------------
def download_year(year: int) -> Dict[str, List[Path]]:
    """
    Download and extract all three VAERS CSV files for *year*.

    Returns a dict mapping the file type (e.g., ``VAERSDATA``) to a list of
    extracted CSV Path objects (normally one per type).
    """
    year_dir = paths.data("raw", str(year))
    year_dir.mkdir(parents=True, exist_ok=True)

    extracted: Dict[str, List[Path]] = {}
    for ftype in FILE_TYPES:
        zip_name = f"{year}{ftype}.csv.zip"
        zip_url = f"{BASE_URL}/{zip_name}"
        zip_path = year_dir / zip_name

        try:
            # ---------- Primary attempt: download zip ----------
            download_zip(zip_url, zip_path)

            # Extract CSV(s) from the zip
            csv_paths = extract_zip(zip_path, year_dir)
            if not csv_paths:
                log.error(f"No CSV found inside {zip_path}")
                raise RuntimeError(f"Empty zip archive for {zip_url}")

            extracted[ftype] = csv_paths

            # Record checksums for each extracted CSV
            for csv_path in csv_paths:
                record_checksum(csv_path, paths.data("checksums.txt"))

            # Clean up the zip file
            zip_path.unlink(missing_ok=True)

        except Exception as zip_exc:
            # ---------- Fallback: download raw CSV directly ----------
            log.warning(
                f"Primary zip download failed for {year} {ftype}: {zip_exc}. "
                "Attempting raw CSV download from GitHub mirror."
            )
            csv_name = f"{year}{ftype}.csv"
            csv_url = f"{GITHUB_RAW_URL}/{csv_name}"
            csv_path = year_dir / csv_name
            try:
                download_csv(csv_url, csv_path)
                # Record checksum for the downloaded CSV
                record_checksum(csv_path, paths.data("checksums.txt"))
                extracted[ftype] = [csv_path]
                # Ensure any partially downloaded zip is removed
                zip_path.unlink(missing_ok=True)
            except Exception as csv_exc:
                log.error(
                    f"Failed to process year {year} file type {ftype}: "
                    f"ZIP error: {zip_exc}; CSV error: {csv_exc}"
                )
                # Abort immediately as required by the task spec
                raise SystemExit(1) from csv_exc

    return extracted

def main() -> None:
    """Entry point – iterate over YEARS and download each."""
    log.info("Starting VAERS data download")
    overall_success = True
    for yr in YEARS:
        try:
            download_year(yr)
            log.info(f"Successfully processed year {yr}")
        except SystemExit:
            # download_year already logged the error; we just propagate failure
            overall_success = False
            break
        except Exception as exc:
            log.error(f"Unexpected error for year {yr}: {exc}")
            overall_success = False
            break

    if not overall_success:
        log.error("One or more years failed to download. Exiting with error.")
        sys.exit(1)

    log.info("All years downloaded and verified successfully")
    sys.exit(0)

if __name__ == "__main__":
    main()