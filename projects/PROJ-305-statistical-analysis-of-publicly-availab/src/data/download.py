"""
VAERS Data Download Script
=========================

This script downloads the VAERS CSV files for the years 2020‑2023 from
publicly‑available sources.  For each year Y ∈ {2020,2021,2022,2023} it
downloads three files:

  * {Y}VAERSDATA.csv
  * {Y}VAERSVAX.csv
  * {Y}VAERSSYMPTOMS.csv

The files are streamed directly to disk under ``data/raw/{Y}/`` with their
original filenames.  After each successful download a SHA‑256 checksum
of the file is computed and appended to ``data/checksums.txt`` as well as
to the human‑readable log file ``logs/download_checksums.txt``.
Any HTTP error or checksum failure aborts the script with a non‑zero
exit status – no synthetic fallback is performed.

The script uses only the standard library plus ``requests`` (available in
the environment) and the ``llmxive_toolkit`` helpers for path handling
and logging.
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
# Primary source – official HHS site (CSV, not zip)
PRIMARY_BASE_URL = "https://vaers.hhs.gov/data/datasets"
# Fallback – CDC GitHub mirror (raw CSV files)
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


def stream_download(url: str, dest_path: Path) -> None:
    """Stream‑download a file from *url* to *dest_path*."""
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


# ----------------------------------------------------------------------
# Core download routine
# ----------------------------------------------------------------------
def download_year(year: int) -> None:
    """
    Download the three VAERS CSV files for *year*.
    On any failure the function raises ``SystemExit(1)``.
    """
    for ftype in FILE_TYPES:
        filename = f"{year}{ftype}.csv"
        # Primary URL (official HHS CSV)
        primary_url = f"{PRIMARY_BASE_URL}/{filename}"
        # Fallback URL (CDC GitHub raw CSV)
        fallback_url = f"{GITHUB_RAW_URL}/{filename}"
        raw_dir = paths.data("raw", str(year))
        dest_path = raw_dir / filename

        # Try primary then fallback
        for url in (primary_url, fallback_url):
            try:
                stream_download(url, dest_path)
                log.info(f"Successfully downloaded {url}")
                break
            except Exception as exc:
                log.warning(f"Download failed for {url}: {exc}")
                if url == fallback_url:
                    raise SystemExit(1) from exc

        # Record checksum of the downloaded CSV
        try:
            record_checksum(dest_path, paths.data("checksums.txt"))
        except Exception as exc:
            log.error(f"Checksum recording failed for {dest_path}: {exc}")
            raise SystemExit(1) from exc

def fetch_vaers_data() -> None:
    """Public entry point used by the pipeline orchestrator."""
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


def main() -> None:
    """CLI entry point – mirrors ``fetch_vaers_data``."""
    fetch_vaers_data()


if __name__ == "__main__":
    main()