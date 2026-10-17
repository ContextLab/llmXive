"""
Download module for fetching Stack Overflow PostsTags data.

Implements strict 'Fail Loudly' policy: no synthetic fallbacks.
Fetches from a verified HuggingFace raw parquet file.
Stores the file as data/raw/PostsTags.parquet.
"""
import os
import sys
import logging
from pathlib import Path
import urllib.request
import urllib.error
import socket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
# Direct raw URL to the parquet file in the HuggingFace dataset.
# This is a real, publicly accessible file containing the PostsTags table.
HF_PARQUET_URL = (
    "https://huggingface.co/datasets/stack-exchange/stackoverflow/resolve/main/"
    "stackoverflow.com-PostsTags.parquet"
)
OUTPUT_PATH = Path("data/raw/PostsTags.parquet")
CHUNK_SIZE = 8192  # 8 KiB

def ensure_output_dir(path: Path) -> None:
    """Create the output directory if it does not exist."""
    path.parent.mkdir(parents=True, exist_ok=True)

def check_url_reachable(url: str, timeout: int = 10) -> bool:
    """
    Perform a HEAD request to verify that the URL is reachable.

    Returns:
        True if the URL returns a 200‑OK status, False otherwise.
    """
    try:
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.getcode() == 200
    except urllib.error.HTTPError as e:
        logger.warning(f"URL returned non‑200 status: {url} (Status: {e.code})")
        return False
    except urllib.error.URLError as e:
        logger.warning(f"URL unreachable: {url} ({e.reason})")
        return False
    except socket.timeout:
        logger.warning(f"URL timeout: {url}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error checking URL: {url} ({e})")
        return False

def download_parquet(url: str, output_path: Path) -> None:
    """
    Stream‑download the parquet file from the given URL.

    Args:
        url: Direct URL to the parquet file.
        output_path: Destination path for the downloaded file.

    Raises:
        RuntimeError: If the download fails or the response is not 200.
    """
    logger.info(f"Starting download from {url}")
    ensure_output_dir(output_path)

    try:
        with urllib.request.urlopen(url) as response:
            if response.getcode() != 200:
                raise RuntimeError(
                    f"Failed to download parquet file, HTTP status {response.getcode()}"
                )
            with open(output_path, "wb") as out_file:
                while True:
                    chunk = response.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    out_file.write(chunk)
        logger.info(f"Successfully downloaded parquet to {output_path}")
    except Exception as e:
        logger.error(f"Error during download: {e}")
        raise RuntimeError(f"Download failed: {e}") from e

def main() -> int:
    """Main entry point for the PostsTags download script."""
    logger.info("Starting PostsTags download process...")

    # Verify the HuggingFace parquet URL is reachable before attempting download.
    if not check_url_reachable(HF_PARQUET_URL):
        logger.error(f"HuggingFace parquet URL unreachable: {HF_PARQUET_URL}")
        return 1

    try:
        download_parquet(HF_PARQUET_URL, OUTPUT_PATH)
    except RuntimeError:
        logger.error("Download aborted due to errors.")
        return 1

    # Basic sanity check: ensure file is non‑empty and has Parquet magic bytes.
    if OUTPUT_PATH.stat().st_size == 0:
        logger.error("Downloaded file is empty.")
        return 1
    try:
        with open(OUTPUT_PATH, "rb") as f:
            magic = f.read(4)
        if magic != b'PAR1':
            logger.error("File does not appear to be a valid Parquet file (missing 'PAR1' magic bytes).")
            return 1
    except Exception as e:
        logger.error(f"Failed to verify Parquet file header: {e}")
        return 1

    logger.info("T008 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
