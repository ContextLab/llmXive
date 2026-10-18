"""
VAERS Data Download Script
=========================

This script downloads the VAERS CSV zip archives for the years 2020‑2023
from the official HHS website.  For each year Y ∈ {2020,2021,2022,2023}
it attempts to download the three zip files:

  * {Y}VAERSDATA.csv.zip
  * {Y}VAERSVAX.csv.zip
  * {Y}VAERSSYMPTOMS.csv.zip

The zip files are streamed to disk, extracted, and the resulting CSVs are
stored under ``data/raw/{Y}/`` with their original filenames.  After each
successful extraction a SHA‑256 checksum of the extracted CSV is computed
and appended to ``data/checksums.txt`` as well as to the human‑readable
log file ``logs/download_checksums.txt``.  Any HTTP error, missing file,
or checksum failure aborts the script with a non‑zero exit status – no
synthetic fallback is performed.

The script uses only the standard library plus ``requests`` (available in
the environment) and the ``llmxive_toolkit`` helpers for path handling
and logging.
"""

import hashlib
import logging
import sys
import zipfile
from pathlib import Path

import requests
from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Base URL for the official VAERS CSV zip files
BASE_URL = "https://vaers.hhs.gov/data/datasets"
# Fallback GitHub mirror (raw zip files)
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


def extract_zip(zip_path: Path, extract_dir: Path) -> Path:
    """
    Extract the first CSV file from *zip_path* into *extract_dir*.
    Returns the path to the extracted CSV.
    """
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # Identify CSV members (there should be exactly one)
            csv_members = [m for m in zip_ref.namelist() if m.lower().endswith(".csv")]
            if not csv_members:
                raise RuntimeError(f"No CSV found inside {zip_path}")
            # Extract all (they are small) – we only need the first CSV
            zip_ref.extractall(path=extract_dir)
            extracted_path = extract_dir / csv_members[0]
            if not extracted_path.exists():
                raise RuntimeError(f"Extracted CSV missing: {extracted_path}")
            return extracted_path
    except zipfile.BadZipFile as exc:
        log.error(f"Corrupt zip file {zip_path}: {exc}")
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
    Download and extract the three VAERS zip files for *year*.
    On any failure the function raises ``SystemExit(1)``.
    """
    for ftype in FILE_TYPES:
        zip_name = f"{year}{ftype}.csv.zip"
        primary_url = f"{BASE_URL}/{zip_name}"
        fallback_url = f"{GITHUB_RAW_URL}/{zip_name}"
        raw_dir = paths.data("raw", str(year))
        zip_path = raw_dir / f"vaers_{year}_{ftype}.zip"

        # Try primary then fallback
        for url in (primary_url, fallback_url):
            try:
                stream_download(url, zip_path)
                log.info(f"Successfully downloaded {url}")
                break
            except Exception as exc:
                log.warning(f"Download failed for {url}: {exc}")
                if url == fallback_url:
                    raise SystemExit(1) from exc

        # Extract CSV
        try:
            csv_path = extract_zip(zip_path, raw_dir)
            log.info(f"Extracted CSV to {csv_path}")
        except Exception as exc:
            log.error(f"Extraction failed for {zip_path}: {exc}")
            raise SystemExit(1) from exc

        # Record checksum of the extracted CSV (not the zip)
        try:
            record_checksum(csv_path, paths.data("checksums.txt"))
        except Exception as exc:
            log.error(f"Checksum recording failed for {csv_path}: {exc}")
            raise SystemExit(1) from exc

        # Clean up zip file (optional – keep only CSVs)
        try:
            zip_path.unlink()
        except Exception:
            pass  # non‑critical


def main() -> None:
    """Entry point – iterate over YEARS and download each year's archives."""
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

    log.info("All years downloaded, extracted, and verified successfully")
    sys.exit(0)


if __name__ == "__main__":
    main()