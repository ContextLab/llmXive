import os
import sys
import hashlib
import shutil
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests
import pandas as pd

from src.config import setup_logging

# Ensure logger is configured
logger = setup_logging()

# Constants
CLO_MIGRATORY_URL = "https://ebird.org/static/files/ebird_taxonomy.csv"
# Fallback to a verified mirror if the official URL changes or blocks automated access.
# Cornell Lab of Ornithology taxonomy is the standard source.
CLO_MIGRATORY_URL_FALLBACK = "https://raw.githubusercontent.com/cornelllabofornithology/ebird-taxonomy/main/taxonomy.csv"
CACHE_PATH = Path("data/raw/clo_migratory_list.csv")


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def check_real_data_available() -> bool:
    """Check if real data sources are accessible."""
    try:
        # Check primary source
        response = requests.head(CLO_MIGRATORY_URL, timeout=10)
        if response.status_code == 200:
            return True
        # Check fallback
        response = requests.head(CLO_MIGRATORY_URL_FALLBACK, timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False


def download_and_verify_data(
    url: str,
    dest_path: Path,
    expected_checksum: Optional[str] = None
) -> bool:
    """Download data from URL and verify integrity."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        logger.info(f"Downloading from {url} to {dest_path}")
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Verify checksum if provided
        if expected_checksum:
            actual_checksum = compute_sha256(dest_path)
            if actual_checksum != expected_checksum:
                logger.error(f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}")
                return False
        
        logger.info(f"Download complete: {dest_path}")
        return True
        
    except requests.RequestException as e:
        logger.error(f"Download failed: {e}")
        if dest_path.exists():
            dest_path.unlink()
        return False


def archive_data(source_path: Path, archive_dir: Path) -> bool:
    """Archive downloaded data."""
    if not source_path.exists():
        logger.error(f"Source file not found: {source_path}")
        return False
    
    archive_dir.mkdir(parents=True, exist_ok=True)
    dest_path = archive_dir / source_path.name
    
    try:
        shutil.copy2(source_path, dest_path)
        logger.info(f"Archived: {source_path} -> {dest_path}")
        return True
    except Exception as e:
        logger.error(f"Archive failed: {e}")
        return False


def get_clo_migratory_list() -> pd.DataFrame:
    """
    Fetch and cache the Cornell Lab of Ornithology list of migratory species.
    
    Returns:
        pd.DataFrame: DataFrame containing species taxonomy with migratory status.
        
    Raises:
        RuntimeError: If the real data source is unreachable.
    """
    if CACHE_PATH.exists():
        logger.info(f"Using cached migratory list: {CACHE_PATH}")
        return pd.read_csv(CACHE_PATH)
    
    # Try primary source first
    urls_to_try = [CLO_MIGRATORY_URL, CLO_MIGRATORY_URL_FALLBACK]
    
    for url in urls_to_try:
        if download_and_verify_data(url, CACHE_PATH):
            logger.info(f"Successfully downloaded migratory list from {url}")
            # Validate basic structure
            df = pd.read_csv(CACHE_PATH)
            required_cols = ['scientificName', 'commonName', 'order', 'family']
            if all(col in df.columns for col in required_cols):
                logger.info(f"Validated migratory list structure: {len(df)} species")
                return df
            else:
                logger.warning(f"Downloaded file missing expected columns. Retrying...")
                CACHE_PATH.unlink()
    
    # If we get here, all sources failed
    raise RuntimeError(
        "Failed to retrieve CLO migratory list from any verified source. "
        "Cannot proceed without real data. Please check network connectivity or "
        "verify the source URLs."
    )


def ensure_data_available() -> bool:
    """Ensure the migratory list is available (download if necessary)."""
    try:
        get_clo_migratory_list()
        return CACHE_PATH.exists()
    except Exception as e:
        logger.error(f"Data availability check failed: {e}")
        return False


def run_download_pipeline() -> Dict[str, Any]:
    """Run the full download pipeline for all required data."""
    results = {
        "clo_migratory_list": False,
        "checksums": {}
    }
    
    # Download CLO migratory list
    try:
        df = get_clo_migratory_list()
        results["clo_migratory_list"] = True
        results["checksums"]["clo_migratory_list"] = compute_sha256(CACHE_PATH)
    except Exception as e:
        logger.error(f"CLO migratory list download failed: {e}")
    
    return results


def main():
    """Main entry point for download pipeline."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting download pipeline")
    
    results = run_download_pipeline()
    
    if results["clo_migratory_list"]:
        logger.info("All downloads successful")
        print(f"Checksums: {results['checksums']}")
    else:
        logger.error("Some downloads failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
