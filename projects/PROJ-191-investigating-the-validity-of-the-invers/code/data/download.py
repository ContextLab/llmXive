"""
Data acquisition module.
Fetches raw data tarballs from arXiv for specified IDs,
extracts them, counts independent experimental runs, and writes
the total count to `data/processed/run_count.json`.
"""
import json
import logging
import tarfile
from pathlib import Path

import requests

from config import get_logger
from data.validator import validate_arxiv_id
from llmxive_toolkit import paths

logger = get_logger(__name__)

# Configuration
ARXIV_IDS = ["2106.08611", "2305.06325"]
# Directory where raw tarballs are stored
DOWNLOAD_DIR = Path("data/raw")
# URL pattern for downloading the source tarball of an arXiv paper
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

        with open(tarball_path, "wb") as f:
            f.write(response.content)

        logger.info(
            f"Downloaded {tarball_path} ({len(response.content)} bytes)"
        )
        return tarball_path

    except requests.exceptions.RequestException as e:
        raise RuntimeError(
            f"Failed to download source for {clean_id}: {e}"
        ) from e

def extract_tarball(tarball_path: Path, extract_to: Path) -> list[Path]:
    """
    Extract a tarball and return list of extracted file paths.

    Args:
        tarball_path: Path to the tarball.
        extract_to: Directory to extract to.

    Returns:
        List of paths to extracted files.
    """
    logger.info(f"Extracting {tarball_path} to {extract_to}...")
    extracted_files: list[Path] = []

    with tarfile.open(tarball_path, "r:*") as tar:
        tar.extractall(path=extract_to)
        for member in tar.getmembers():
            extracted_files.append(extract_to / member.name)

    logger.info(f"Extracted {len(extracted_files)} files.")
    return extracted_files

def count_independent_runs(extracted_files: list[Path]) -> int:
    """
    Count independent experimental runs by scanning for *_run*.csv files.

    Args:
        extracted_files: List of file paths from extraction.

    Returns:
        Count of runs.
    """
    run_files = [
        f
        for f in extracted_files
        if f.is_file()
        and "_run" in f.name.lower()
        and f.suffix.lower() == ".csv"
    ]

    count = len(run_files)
    logger.info(
        f"Found {count} independent run files: {[f.name for f in run_files]}"
    )
    return count

def main() -> int:
    """Main entry point for data acquisition."""
    # Ensure the raw download directory exists
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    # Directory where extracted files will be placed
    EXTRACT_DIR = DOWNLOAD_DIR / "extracted"
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)

    total_runs = 0

    for arxiv_id in ARXIV_IDS:
        logger.info(f"Processing arXiv ID {arxiv_id}...")

        # 1. Validate the ID using the validator module
        try:
            validate_arxiv_id(arxiv_id)
        except RuntimeError as e:
            logger.error(f"Validation failed for {arxiv_id}: {e}")
            raise e  # Fail loudly as required

        # 2. Download the source tarball
        try:
            tarball_path = download_arxiv_source(arxiv_id, DOWNLOAD_DIR)
        except RuntimeError as e:
            logger.error(f"Download failed for {arxiv_id}: {e}")
            raise e

        # 3. Extract the tarball
        try:
            extracted_files = extract_tarball(tarball_path, EXTRACT_DIR)
        except Exception as e:
            logger.error(f"Extraction failed for {arxiv_id}: {e}")
            raise e

        # 4. Count independent runs in this tarball
        runs = count_independent_runs(extracted_files)
        total_runs += runs

        if runs < 3:
            logger.warning(
                f"Insufficient runs ({runs} < 3) for leave-one-out cross-validation; "
                "bootstrap fallback may be required."
            )
        else:
            logger.info(f"Sufficient runs ({runs} >= 3) found.")

    logger.info(f"Total independent runs across all IDs: {total_runs}")

    # Write the run count to the processed data directory
    run_count_path = paths.data("processed", "run_count.json")
    run_count_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(run_count_path, "w", encoding="utf-8") as f:
            json.dump({"run_count": total_runs}, f, indent=2)
        logger.info(f"Wrote run count to {run_count_path}")
    except Exception as e:
        logger.error(f"Failed to write run count JSON: {e}")
        raise

    return 0

if __name__ == "__main__":
    exit(main())
