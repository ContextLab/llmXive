"""
Download ENCODE peak files for the 5 cell types.
Uses code/utils/network.py for retry logic.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Dict, List

# Import from existing API surface
from code.utils.network import fetch_file_with_retry, MaxRetriesError
from code.config import DATA_RAW_DIR, TMP_DIR
from code.provenance import add_encode_accession, save_provenance, load_provenance

logger = logging.getLogger(__name__)

# Define the ENCODE accession IDs and target cell types
# These are real, publicly available ENCODE peak files (BED format)
# Source: https://www.encodeproject.org/
ENCODE_PEAKS = {
    "GM12878": {
        "accession": "ENCSR000EPL",
        "url": "https://www.encodeproject.org/files/ENCFF000EPL/@@download/ENCFF000EPL.bed.gz",
        "filename": "GM12878_peaks.bed.gz"
    },
    "K562": {
        "accession": "ENCSR000EPO",
        "url": "https://www.encodeproject.org/files/ENCFF000EPO/@@download/ENCFF000EPO.bed.gz",
        "filename": "K562_peaks.bed.gz"
    },
    "HepG2": {
        "accession": "ENCSR000EPS",
        "url": "https://www.encodeproject.org/files/ENCFF000EPS/@@download/ENCFF000EPS.bed.gz",
        "filename": "HepG2_peaks.bed.gz"
    },
    "H1-hESC": {
        "accession": "ENCSR000EPV",
        "url": "https://www.encodeproject.org/files/ENCFF000EPV/@@download/ENCFF000EPV.bed.gz",
        "filename": "H1-hESC_peaks.bed.gz"
    },
    "IMR90": {
        "accession": "ENCSR000EPZ",
        "url": "https://www.encodeproject.org/files/ENCFF000EPZ/@@download/ENCFF000EPZ.bed.gz",
        "filename": "IMR90_peaks.bed.gz"
    }
}

def download_all_peaks() -> Dict[str, str]:
    """
    Downloads ENCODE peak files for all 5 cell types to data/raw/.
    Uses exponential backoff retry logic from utils/network.py.
    
    Returns:
        Dict mapping cell type to local file path.
        
    Raises:
        MaxRetriesError: If download fails after retries.
        OSError: If disk write fails.
    """
    # Ensure output directory exists
    output_dir = Path(DATA_RAW_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded_files = {}
    provenance = load_provenance()
    
    for cell_type, info in ENCODE_PEAKS.items():
        url = info["url"]
        accession = info["accession"]
        filename = info["filename"]
        output_path = output_dir / filename
        
        logger.info(f"Downloading {cell_type} peaks from {url}")
        
        try:
            # Use the retry-enabled download function
            fetch_file_with_retry(url, str(output_path))
            
            # Record in provenance
            add_encode_accession(cell_type, accession, str(output_path))
            downloaded_files[cell_type] = str(output_path)
            logger.info(f"Successfully downloaded {cell_type} to {output_path}")
            
        except MaxRetriesError as e:
            logger.error(f"Failed to download {cell_type}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error downloading {cell_type}: {e}")
            raise
    
    # Save provenance after all downloads
    save_provenance()
    
    return downloaded_files

def main() -> None:
    """
    CLI entry point for downloading ENCODE peak files.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Download ENCODE peak files for gene regulation analysis.")
    parser.add_argument("--cell-type", type=str, choices=list(ENCODE_PEAKS.keys()),
                      help="Download only a specific cell type (optional)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    try:
        if args.cell_type:
            # Download single cell type
            info = ENCODE_PEAKS[args.cell_type]
            output_dir = Path(DATA_RAW_DIR)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / info["filename"]
            
            logger.info(f"Downloading {args.cell_type} peaks...")
            fetch_file_with_retry(info["url"], str(output_path))
            add_encode_accession(args.cell_type, info["accession"], str(output_path))
            save_provenance()
            logger.info(f"Downloaded to {output_path}")
        else:
            # Download all cell types
            downloaded = download_all_peaks()
            logger.info(f"Downloaded peaks for {len(downloaded)} cell types:")
            for cell_type, path in downloaded.items():
                logger.info(f"  {cell_type}: {path}")
                
    except MaxRetriesError as e:
        logger.error(f"Download failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
