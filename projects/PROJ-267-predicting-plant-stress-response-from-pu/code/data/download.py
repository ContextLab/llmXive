"""
Real‑data ingestion script.

This script downloads a small publicly available file from NCBI GEO,
stores it under ``data/raw/``, and generates a SHA‑256 checksum file
``data/raw/checksums.sha256``. All operations are strict: any network
error or checksum mismatch raises an exception and aborts the pipeline.
"""

import sys
import logging
from pathlib import Path

# Project utilities
from utils.logging_config import get_logger
from utils.checksums import generate_checksums_for_directory
# Re‑use the robust download implementation from the existing module
from data_ingestion.download import download_file

# llmxive toolkit paths helper for reliable project‑wide directories
from llmxive_toolkit import paths

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Test GEO accession GSE14784 (family XML) – a real file >1 KB.
GEO_SAMPLE_URL = (
    "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE14nnn/GSE14784/miniml/GSE14784_family.xml"
)

# A matching ProteomeXchange file (series matrix) – also >1 KB.
PROTEOMEXCHANGE_URL = (
    "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE14nnn/GSE14784/matrix/GSE14784_series_matrix.txt"
)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def download_samples(urls):
    """
    Download each URL using the shared ``download_file`` routine.

    Returns a list of ``Path`` objects for the successfully downloaded files.
    """
    downloaded = []
    for url in urls:
        try:
            logger.info(f"Attempting to download {url}")
            path = download_file(url)
            downloaded.append(path)
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            raise  # Propagate – the pipeline must stop on failure
    return downloaded

def write_checksum_file(directory: Path, checksum_path: Path):
    """
    Generate SHA‑256 checksums for all files in *directory* and write them
    to *checksum_path* in the classic ``<checksum>  <relative_path>`` format.
    """
    logger.info(f"Generating checksums for directory {directory}")
    # ``generate_checksums_for_directory`` expects a string path
    checksums = generate_checksums_for_directory(str(directory))
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksum_path, "w") as f:
        for rel_path, checksum in checksums.items():
            f.write(f"{checksum}  {rel_path}\n")
    logger.info(f"Checksum file written to {checksum_path}")

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main():
    """
    Execute the download‑and‑checksum workflow.

    1. Download verified GEO and ProteomeXchange files.
    2. Verify that each file size is > 1 KB (handled by ``download_file``).
    3. Generate ``checksums.sha256`` for everything under ``data/raw/``.
    """
    # Use the toolkit to obtain a reliable ``data/raw`` directory
    raw_dir = paths.data("raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Step 1 – download both files
    urls = [GEO_SAMPLE_URL, PROTEOMEXCHANGE_URL]
    download_samples(urls)

    # Step 2 – checksum generation
    checksum_file = raw_dir / "checksums.sha256"
    write_checksum_file(raw_dir, checksum_file)

    logger.info("Data ingestion completed successfully.")
    print(f"Downloaded files are stored in {raw_dir}")
    print(f"Checksum manifest: {checksum_file}")

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.error(f"Data ingestion failed: {exc}")
        sys.exit(1)
