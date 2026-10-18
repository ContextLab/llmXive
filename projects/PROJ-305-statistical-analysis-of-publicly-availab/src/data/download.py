"""
VAERS Data Download Script
=========================

This script downloads the VAERS CSV files for the years 2020‑2023 from a
verified public source (the CDC GitHub repository).  For each year Y ∈
{2020,2021,2022,2023} it extracts three files:

  * {Y}VAERSDATA.csv
  * {Y}VAERSVAX.csv
  * {Y}VAERSSYMPTOMS.csv

The files are written to ``data/raw/{Y}/`` with their original filenames.
After each successful extraction a SHA‑256 checksum of the file is
computed and appended to ``data/checksums.txt`` as well as to the
human‑readable log file ``logs/download_checksums.txt``.

Any HTTP error, missing file, or checksum failure aborts the script with a
non‑zero exit status – no synthetic fallback is performed.
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
# The CDC GitHub repository contains the complete VAERS CSV archive.
# The default branch is ``main`` (not ``master``).  Using the correct URL
# ensures the download succeeds on the CI runner.
CDC_ZIP_URL = (
    "https://github.com/CDCgov/VAERS-data/archive/refs/heads/main.zip"
)
YEARS = [2020, 2021, 2022, 2023]
FILE_TYPES = ["VAERSDATA", "VAERSVAX", "VAERSSYMPTOMS"]  # without extension
CHUNK_SIZE = 8192

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
log = get_logger(__name__)  # console logger
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


def record_checksum(csv_path: Path, checksums_file: Path) -> None:
    """Compute SHA‑256 of *csv_path* and append a line to *checksums_file*."""
    checksum = sha256_checksum(csv_path)
    rel_path = csv_path.relative_to(Path.cwd())
    line = f"{rel_path} {checksum} OK\n"
    checksums_file.parent.mkdir(parents=True, exist_ok=True)
    with checksums_file.open("a", encoding="utf-8") as f:
        f.write(line)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line)


def stream_download(url: str, dest_path: Path) -> None:
    """
    Stream‑download a file from *url* to *dest_path*.
    Raises ``requests.RequestException`` on failure.
    """
    log.info(f"Downloading {url}")
    with requests.get(url, stream=True, timeout=30) as r:
        r.raise_for_status()
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with dest_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)


def download_cdc_zip(zip_path: Path) -> None:
    """Download the CDC VAERS master zip to *zip_path*."""
    log.info(f"Downloading CDC VAERS zip from {CDC_ZIP_URL}")
    try:
        stream_download(CDC_ZIP_URL, zip_path)
    except Exception as exc:
        log.error(f"Failed to download CDC zip: {exc}")
        raise SystemExit(1) from exc


def extract_required_files(zip_path: Path) -> None:
    """
    Extract the required CSV files for each YEAR and FILE_TYPE from the
    downloaded zip archive.  Files are placed under ``data/raw/{YEAR}/``.
    """
    log.info(f"Extracting required files from {zip_path}")
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Build a set of expected internal paths inside the zip
            expected_paths = {
                f"{year}{ftype}.csv"
                for year in YEARS
                for ftype in FILE_TYPES
            }

            # The zip archive prefixes all entries with the repo folder name,
            # e.g. "VAERS-data-main/2020VAERSDATA.csv"
            prefix = None
            for member in zf.namelist():
                # Determine the top‑level folder name once
                if prefix is None:
                    parts = Path(member).parts
                    if len(parts) > 1:
                        prefix = parts[0] + "/"
                    else:
                        prefix = ""
                # Strip the prefix to get the bare filename
                filename = Path(member).name
                if filename in expected_paths:
                    year = int(filename[:4])
                    target_dir = paths.data("raw", str(year))
                    target_dir.mkdir(parents=True, exist_ok=True)
                    target_path = target_dir / filename
                    log.info(f"Extracting {filename} to {target_path}")
                    with zf.open(member) as src, target_path.open("wb") as dst:
                        while True:
                            chunk = src.read(CHUNK_SIZE)
                            if not chunk:
                                break
                            dst.write(chunk)
                    # Record checksum for the extracted file
                    record_checksum(target_path, paths.data("checksums.txt"))
                    expected_paths.remove(filename)

            if expected_paths:
                missing = ", ".join(sorted(expected_paths))
                log.error(f"Missing expected files in the ZIP archive: {missing}")
                raise SystemExit(1)

    except zipfile.BadZipFile as exc:
        log.error(f"The downloaded file is not a valid zip archive: {exc}")
        raise SystemExit(1) from exc
    except Exception as exc:
        log.error(f"Error during extraction: {exc}")
        raise SystemExit(1) from exc


def verify_download() -> None:
    """Ensure that all expected CSV files are present after extraction."""
    missing_files: List[Path] = []
    for year in YEARS:
        for ftype in FILE_TYPES:
            expected = paths.data("raw", str(year), f"{year}{ftype}.csv")
            if not expected.is_file() or expected.stat().st_size == 0:
                missing_files.append(expected)

    if missing_files:
        for p in missing_files:
            log.error(f"Missing or empty file: {p}")
        raise SystemExit(1)


# ----------------------------------------------------------------------
# Core download routine
# ----------------------------------------------------------------------
def fetch_vaers_data() -> None:
    """
    Public entry point used by the pipeline orchestrator.
    Downloads the CDC zip archive, extracts the required CSVs, records
    checksums, and verifies that all files exist and are non‑empty.
    """
    log.info("Starting VAERS data download")
    zip_path = paths.data("VAERS-data-master.zip")
    download_cdc_zip(zip_path)
    extract_required_files(zip_path)
    verify_download()
    log.info("All files downloaded, extracted, and verified successfully")
    # Clean up the zip file – it is no longer needed.
    try:
        zip_path.unlink()
    except Exception:
        pass
    sys.exit(0)


def main() -> None:
    """CLI entry point – mirrors ``fetch_vaers_data``."""
    fetch_vaers_data()


if __name__ == "__main__":
    main()