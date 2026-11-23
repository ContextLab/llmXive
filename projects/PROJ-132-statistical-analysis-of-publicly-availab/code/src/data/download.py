import os
import sys
import hashlib
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
import pandas as pd
from src.config import setup_logging

# Configure logging
logger = setup_logging()

# Constants
CLO_MIGRATORY_URL = "https://ebird.org/sites/default/files/clo_migratory_species_list.csv"
# Fallback mirror if the primary URL is unavailable (Cornell Lab of Ornithology)
# Note: The actual URL structure for CLO lists often requires authentication or specific
# endpoints. We use a direct download link if available, otherwise we rely on a verified
# mirror or a standard public dataset that contains this mapping.
# For this implementation, we attempt the direct CLO URL. If it fails (403/404),
# we raise an error as per the "Fail loudly" constraint.
CACHE_DIR = Path("data/raw")
CACHE_FILE = CACHE_DIR / "clo_migratory_list.csv"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_clo_migratory_list(force_download: bool = False) -> pd.DataFrame:
    """
    Fetch and cache the Cornell Lab of Ornithology (CLO) list of migratory species.

    This function attempts to download the official CLO migratory species list.
    If the file exists in the cache and force_download is False, it returns the cached version.
    If the download fails, it raises a RuntimeError (fail loudly).

    Args:
        force_download (bool): If True, re-download the file even if it exists in cache.

    Returns:
        pd.DataFrame: A DataFrame containing the list of migratory species.
                      Expected columns: 'scientific_name', 'common_name', 'species_code'.

    Raises:
        RuntimeError: If the download fails or the file is not found.
        FileNotFoundError: If the cached file is missing and download fails.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Check cache
    if not force_download and CACHE_FILE.exists():
        logger.info(f"Using cached CLO migratory list from {CACHE_FILE}")
        try:
            df = pd.read_csv(CACHE_FILE)
            # Basic validation
            required_cols = ['scientific_name']
            if not all(col in df.columns for col in required_cols):
                logger.warning("Cached file missing expected columns, re-downloading...")
                return get_clo_migratory_list(force_download=True)
            return df
        except Exception as e:
            logger.warning(f"Failed to read cached file: {e}, re-downloading...")
            return get_clo_migratory_list(force_download=True)

    logger.info(f"Downloading CLO migratory list from {CLO_MIGRATORY_URL}...")
    try:
        # Attempt download
        response = requests.get(CLO_MIGRATORY_URL, timeout=60)
        response.raise_for_status()

        # Save to cache
        with open(CACHE_FILE, 'wb') as f:
            f.write(response.content)

        logger.info(f"Downloaded and cached CLO migratory list to {CACHE_FILE}")

        # Verify checksum (conceptually, we'd have a known hash, but here we just ensure file integrity)
        checksum = compute_sha256(CACHE_FILE)
        logger.info(f"Checksum of downloaded file: {checksum}")

        # Load and validate
        df = pd.read_csv(CACHE_FILE)

        # Ensure we have the necessary columns for filtering
        # The CLO list typically has 'scientificName' or 'species'.
        # We normalize to 'scientific_name' for consistency with downstream tasks.
        if 'scientificName' in df.columns:
            df = df.rename(columns={'scientificName': 'scientific_name'})
        elif 'species' in df.columns:
            df = df.rename(columns={'species': 'scientific_name'})

        if 'scientific_name' not in df.columns:
            # If the column is not found, we raise an error because we cannot proceed
            # without a valid list of species names.
            raise ValueError("Downloaded file does not contain 'scientific_name' column.")

        logger.info(f"Successfully loaded {len(df)} migratory species.")
        return df

    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to download CLO migratory list from {CLO_MIGRATORY_URL}: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error while processing CLO migratory list: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

def ensure_data_available() -> bool:
    """
    Ensure the CLO migratory list is available in the cache.
    Returns True if available, False otherwise.
    """
    if CACHE_FILE.exists():
        try:
            pd.read_csv(CACHE_FILE)
            return True
        except Exception:
            return False
    return False

def run_download_pipeline() -> None:
    """
    Main entry point for the download pipeline.
    Downloads the CLO migratory list and verifies it.
    """
    try:
        df = get_clo_migratory_list()
        logger.info("CLO Migratory List download pipeline completed successfully.")
        logger.info(f"Output file: {CACHE_FILE}")
    except Exception as e:
        logger.error(f"CLO Migratory List download pipeline failed: {e}")
        sys.exit(1)

def main():
    """CLI entry point."""
    run_download_pipeline()

if __name__ == "__main__":
    main()
