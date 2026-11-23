"""
Task T013a: Download External Base
Downloads the 'ca-AstroPh' dataset from the official SNAP URL.

This task satisfies the Constitution's Reproducibility Requirements by ensuring
the raw data is fetched from the authoritative source on every run.

The downloaded dataset is saved to data/raw/ca-AstroPh.txt.
If the download fails, this script raises an error and does not fall back to
synthetic data.
"""
import os
import sys
import logging
import urllib.request
from pathlib import Path

# Project root relative to this script (assuming script is in code/)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_FILE = DATA_RAW_DIR / "ca-AstroPh.txt"

# SNAP Dataset URL for ca-AstroPh
# This is the official mirror for the SNAP dataset collection.
SNAP_URL = "https://snap.stanford.edu/data/ca-AstroPh.txt.gz"
# We will download the .gz and decompress it on the fly or save as .txt
# The task requires output at data/raw/ca-AstroPh.txt
# SNAP provides a .txt.gz. We will download and decompress.
SNAP_URL_GZ = "https://snap.stanford.edu/data/ca-AstroPh.txt.gz"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("T013a_Download")

def ensure_directory(path: Path):
    """Ensure the directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def download_and_decompress(url: str, output_path: Path):
    """
    Downloads a gzipped file from the URL and writes the decompressed content
    to output_path.
    
    Raises:
        RuntimeError: If the download fails or the file is empty.
        ConnectionError: If network access fails.
    """
    logger.info(f"Starting download from {url}")
    logger.info(f"Target path: {output_path}")
    
    ensure_directory(output_path.parent)
    
    try:
        # Open the URL (handles gzip automatically if we read binary and decompress)
        # However, urllib.request.urlretrieve is simpler for raw download, 
        # but we need to decompress. Let's use urlopen and gzip.
        import gzip
        
        with urllib.request.urlopen(url, timeout=60) as response:
            # Check content type or just read
            # The SNAP site usually serves the raw bytes.
            # If it's gzipped, we decompress.
            # To be safe against network variations, we'll read the bytes and try to decompress.
            
            data = response.read()
            
            if len(data) == 0:
                raise RuntimeError("Downloaded file is empty.")
            
            # Try to decompress if it looks gzipped (starts with 1f 8b)
            if data[:2] == b'\x1f\x8b':
                logger.info("Detected gzip format, decompressing...")
                decompressed_data = gzip.decompress(data)
            else:
                logger.info("File appears to be plain text.")
                decompressed_data = data
            
            with open(output_path, 'wb') as f_out:
                f_out.write(decompressed_data)
                
            logger.info(f"Successfully downloaded and saved to {output_path}")
            logger.info(f"File size: {output_path.stat().st_size} bytes")
            
            if output_path.stat().st_size == 0:
                raise RuntimeError("Saved file is empty after decompression.")
                
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP Error {e.code}: {e.reason}")
        raise RuntimeError(f"Download failed with HTTP {e.code}. The data source may be unavailable.") from e
    except urllib.error.URLError as e:
        logger.error(f"URL Error: {e.reason}")
        raise ConnectionError(f"Network error while downloading: {e.reason}") from e
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        raise RuntimeError(f"Failed to download or process data: {e}") from e

def main():
    logger.info("Task T013a: Downloading ca-AstroPh dataset...")
    
    if OUTPUT_FILE.exists():
        logger.warning(f"Output file {OUTPUT_FILE} already exists. Overwriting.")
    
    try:
        download_and_decompress(SNAP_URL_GZ, OUTPUT_FILE)
        logger.info("Task T013a completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Task T013a failed: {e}")
        # Fail loudly as per constraints
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
