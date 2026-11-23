"""
Download dataset from Zenodo DOI.

Attempts to download the primary DOI (10.5281/zenodo.10043838).
On failure, attempts the fallback DOI (10.5281/zenodo.11023456).
If both fail, raises a clear RuntimeError.
"""
import sys
import logging
from pathlib import Path

from zenodo_client import download_csv_from_zenodo, DataUnavailableError

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def setup_logging():
    """Configure logging for download."""
    project_root = get_project_root()
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / "download.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def main():
    """Download dataset from Zenodo."""
    logger = setup_logging()
    project_root = get_project_root()
    
    primary_doi = "10.5281/zenodo.10043838"
    fallback_doi = "10.5281/zenodo.11023456"
    
    data_dir = project_root / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Try primary DOI
    raw_path = data_dir / "metallic_glass_raw.csv"
    try:
        logger.info(f"Attempting to download primary DOI: {primary_doi}")
        download_csv_from_zenodo(primary_doi, raw_path)
        logger.info(f"Successfully downloaded primary DOI to {raw_path}")
        return
    except DataUnavailableError as e:
        logger.warning(f"Primary DOI failed: {e}")
    
    # Try fallback DOI
    try:
        logger.info(f"Attempting to download fallback DOI: {fallback_doi}")
        download_csv_from_zenodo(fallback_doi, raw_path)
        logger.info(f"Successfully downloaded fallback DOI to {raw_path}")
        return
    except DataUnavailableError as e:
        logger.error(f"Fallback DOI also failed: {e}")
        raise RuntimeError("Both primary and fallback DOIs are unavailable.") from e

if __name__ == "__main__":
    main()
