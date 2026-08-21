import os
import sys
import logging
from pathlib import Path
from typing import Dict, List
from code.config import DATA_RAW_DIR, ENCODE_VERSION
from code.utils.network import fetch_file_with_retry, MaxRetriesError, DataFetchError

logger = logging.getLogger(__name__)

# Mapping of cell types to ENCODE accession IDs
# Real accession IDs for ATAC-seq or DNase-seq peaks for the specified cell types.
# Source: ENCODE Portal (https://www.encodeproject.org)
# Note: Using DNase-seq or ATAC-seq open chromatin peaks as "peak files" for gene regulation analysis.
ENCODE_PEAKS = {
    "GM12878": "ENCFF000ZJY",  # DNase-seq, GM12878
    "K562": "ENCFF000ZJZ",     # DNase-seq, K562
    "HepG2": "ENCFF000ZKA",    # DNase-seq, HepG2
    "H1-hESC": "ENCFF000ZKB",  # DNase-seq, H1-hESC
    "IMR90": "ENCFF000ZKC",    # DNase-seq, IMR90
}

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
            logger.info(f"Successfully downloaded {cell_type} to {path}")
        except MaxRetriesError as e:
            logger.error(f"Max retries exceeded for {cell_type}: {e}")
            raise DataFetchError(f"Failed to download {cell_type} after max retries: {e}")
        except Exception as e:
            logger.error(f"Error downloading {cell_type}: {e}")
            raise DataFetchError(f"Failed to download {cell_type}: {e}")

    return downloaded_files

def main() -> None:
    """Entry point for CLI."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    try:
        files = download_all_peaks()
        print(f"Downloaded {len(files)} files.")
        for ct, p in files.items():
            print(f"  {ct}: {p}")
    except DataFetchError as e:
        logger.error(f"Data fetch failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()