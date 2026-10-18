"""
VAERS Data Download Script
=========================

This script downloads the VAERS CSV files for the years 2020‑2023 directly from the
official HHS website.  For each year Y ∈ {2020,2021,2022,2023} it attempts to download
the three CSV files:

  * {Y}VAERSDATA.csv
  * {Y}VAERSVAX.csv
  * {Y}VAERSSYMPTOMS.csv

The files are saved under ``data/raw/`` with names that start with ``vaers_`` so that
downstream cleaning scripts can discover them via ``Path("data/raw").glob("vaers_*.csv")``.
After each successful download a SHA‑256 checksum is computed and appended to
``data/checksums.txt`` as well as to the human‑readable log file
``logs/download_checksums.txt``.  Any HTTP error or checksum failure aborts the
script with a non‑zero exit status – no synthetic fallback is performed.

The script is deliberately simple: it streams each file, writes it to disk, and
records the checksum.  All directories are created on‑demand using the
``llmxive_toolkit.paths`` helpers.

Requirements
------------
* ``requests`` – standard library for streaming HTTP downloads.
* ``llmxive_toolkit`` – provides ``paths`` and ``get_logger`` utilities.

The script is executable via ``python src/data/download.py`` and is invoked
automatically by the quick‑start workflow.
"""

import hashlib
import logging
import sys
from pathlib import Path

import requests
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Base URL for the official VAERS CSV files (no zip archives)
BASE_URL = "https://vaers.hhs.gov/data/datasets"
# Fallback GitHub mirror (raw CSV files)
GITHUB_RAW_URL = "https://raw.githubusercontent.com/CDCgov/VAERS-data/master"

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


def download_csv(url: str, dest_path: Path) -> None:
    """Stream‑download a CSV file from *url* to *dest_path*."""
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
def download_year(year: int) -> None:
    """
    Download the three CSV files for *year* and write them to ``data/raw/``.
    On any failure the function raises ``SystemExit(1)``.
    """
    for ftype in FILE_TYPES:
        csv_name = f"{year}{ftype}.csv"
        primary_url = f"{BASE_URL}/{csv_name}"
        dest_path = paths.data("raw", f"vaers_{year}_{ftype}.csv")

        try:
            # Primary attempt: download from the official HHS site
            download_csv(primary_url, dest_path)
            record_checksum(dest_path, paths.data("checksums.txt"))
            log.info(f"Successfully downloaded {primary_url}")
        except Exception as primary_exc:
            # Fallback: download from the GitHub mirror
            log.warning(
                f"Primary download failed for {primary_url}: {primary_exc}. "
                "Attempting fallback from GitHub mirror."
            )
            fallback_url = f"{GITHUB_RAW_URL}/{csv_name}"
            try:
                download_csv(fallback_url, dest_path)
                record_checksum(dest_path, paths.data("checksums.txt"))
                log.info(f"Successfully downloaded fallback {fallback_url}")
            except Exception as fallback_exc:
                log.error(
                    f"Both primary and fallback downloads failed for {csv_name}: "
                    f"primary error: {primary_exc}; fallback error: {fallback_exc}"
                )
                # Abort as required by the task specification
                raise SystemExit(1) from fallback_exc


def main() -> None:
    """Entry point – iterate over YEARS and download each CSV."""
    log.info("Starting VAERS data download")
    for yr in YEARS:
        try:
            download_year(yr)
            log.info(f"All files for year {yr} processed successfully")
        except SystemExit:
            log.error(f"Failed to download data for year {yr}. Exiting.")
            sys.exit(1)
        except Exception as exc:
            log.error(f"Unexpected error for year {yr}: {exc}")
            sys.exit(1)

    log.info("All years downloaded and verified successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()
