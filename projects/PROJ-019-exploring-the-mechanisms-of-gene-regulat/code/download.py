import os
import sys
import logging
from pathlib import Path
from typing import Dict, List
from code.config import DATA_RAW_DIR, ENCODE_VERSION
from code.utils.network import fetch_file_with_retry, MaxRetriesError

logger = logging.getLogger(__name__)

# Mapping of cell types to ENCODE accession IDs (Example mappings - to be updated with real IDs)
# These are placeholders for the actual ENCODE accession IDs for the 5 cell types.
# GM12878, K562, HepG2, H1-hESC, IMR90
ENCODE_PEAKS = {
    "GM12878": "ENCFF001XXX", # Replace with real accession
    "K562": "ENCFF002XXX",
    "HepG2": "ENCFF003XXX",
    "H1-hESC": "ENCFF004XXX",
    "IMR90": "ENCFF005XXX",
}

# Base URL for ENCODE downloads (Example - replace with actual API/URL)
ENCODE_BASE_URL = "https://www.encodeproject.org/files"

def get_download_url(accession: str) -> str:
    """Construct the download URL for an ENCODE file."""
    return f"{ENCODE_BASE_URL}/{accession}/download?file_format=bed"

def download_all_peaks() -> Dict[str, Path]:
    """
    Download peak files for all defined cell types.
    Returns a dictionary mapping cell type to the downloaded file path.
    """
    downloaded_files = {}
    for cell_type, accession in ENCODE_PEAKS.items():
        url = get_download_url(accession)
        output_path = DATA_RAW_DIR / f"{cell_type}_{accession}.bed"

        logger.info(f"Downloading {cell_type} peaks from {url}...")
        try:
            path = fetch_file_with_retry(url, output_path)
            downloaded_files[cell_type] = path
        except MaxRetriesError as e:
            logger.error(f"Failed to download {cell_type}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error downloading {cell_type}: {e}")
            raise

    return downloaded_files

def main() -> None:
    """Entry point for CLI."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    try:
        files = download_all_peaks()
        print(f"Downloaded {len(files)} files.")
        for ct, p in files.items():
            print(f"  {ct}: {p}")
    except Exception as e:
        logger.error(f"Download failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
