"""
Data acquisition module.
Fetches raw data tarballs from arXiv for specified IDs.
"""
import os
import sys
import tarfile
import logging
import glob
from pathlib import Path
import requests

from config import get_logger
from data.validator import validate_arxiv_id

logger = get_logger(__name__)

# Configuration
ARXIV_IDS = ["2106.08611", "2305.06325"]
DOWNLOAD_DIR = Path("data/raw")
# arXiv source download URL pattern
ARXIV_SOURCE_URL = "https://arxiv.org/e-print/{id}"

def download_arxiv_source(arxiv_id: str, output_dir: Path) -> Path:
    """
    Download the source tarball for a given arXiv ID.

    Args:
        arxiv_id: The arXiv ID (e.g., '2106.08611').
        output_dir: Directory to save the tarball.

    Returns:
        Path to the downloaded tarball.

    Raises:
        RuntimeError: If download fails.
    """
    clean_id = arxiv_id.replace("arXiv:", "").strip()
    url = ARXIV_SOURCE_URL.format(id=clean_id)
    tarball_path = output_dir / f"{clean_id}.tar.gz"

    logger.info(f"Downloading source for {clean_id} from {url}...")

    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        with open(tarball_path, 'wb') as f:
            f.write(response.content)

        logger.info(f"Downloaded {tarball_path} ({len(response.content)} bytes)")
        return tarball_path

    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Failed to download source for {clean_id}: {e}")

def extract_tarball(tarball_path: Path, extract_to: Path) -> list:
    """
    Extract a tarball and return list of extracted file paths.

    Args:
        tarball_path: Path to the tarball.
        extract_to: Directory to extract to.

    Returns:
        List of paths to extracted files.
    """
    logger.info(f"Extracting {tarball_path} to {extract_to}...")
    extracted_files = []

    with tarfile.open(tarball_path, 'r:*') as tar:
        tar.extractall(path=extract_to)
        for member in tar.getmembers():
            extracted_files.append(extract_to / member.name)

    logger.info(f"Extracted {len(extracted_files)} files.")
    return extracted_files

def count_independent_runs(extracted_files: list) -> int:
    """
    Count independent experimental runs by scanning for *_run*.csv files.

    Args:
        extracted_files: List of file paths from extraction.

    Returns:
        Count of runs.
    """
    run_files = []
    for f in extracted_files:
        if f.is_file() and "_run" in f.name.lower() and f.suffix.lower() == '.csv':
            run_files.append(f)
    
    # Also check for metadata if needed, but spec says scan files
    count = len(run_files)
    logger.info(f"Found {count} independent run files: {[f.name for f in run_files]}")
    return count

def main():
    """Main entry point for data acquisition."""
    # Ensure directory exists
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    EXTRACT_DIR = DOWNLOAD_DIR / "extracted"
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

    all_runs = 0

    for arxiv_id in ARXIV_IDS:
        logger.info(f"Processing {arxiv_id}...")
        
        # 1. Validate ID
        try:
            validate_arxiv_id(arxiv_id)
        except RuntimeError as e:
            logger.error(f"Validation failed for {arxiv_id}: {e}")
            raise e  # Fail loudly

        # 2. Download
        try:
            tarball = download_arxiv_source(arxiv_id, DOWNLOAD_DIR)
        except RuntimeError as e:
            logger.error(f"Download failed for {arxiv_id}: {e}")
            raise e

        # 3. Extract
        try:
            files = extract_tarball(tarball, EXTRACT_DIR)
        except Exception as e:
            logger.error(f"Extraction failed for {arxiv_id}: {e}")
            raise e

        # 4. Count runs
        runs = count_independent_runs(files)
        all_runs += runs

        if runs < 3:
            logger.warning(f"Insufficient runs ({runs} < 3) for leave-one-out cross-validation; "
                           f"bootstrap fallback (T013-BOOTSTRAP) will be triggered.")
        else:
            logger.info(f"Sufficient runs ({runs} >= 3) found.")

    logger.info(f"Total independent runs found: {all_runs}")
    return 0

if __name__ == "__main__":
    exit(main())
