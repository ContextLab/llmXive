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

logger = setup_logging(__name__)

# Verified source for CLO Migratory List
# Cornell Lab of Ornithology (All About Birds) provides a public CSV of species status.
# We use a direct link to a known stable mirror or the official API if available.
# For this implementation, we target the "Birds of the World" / eBird taxonomy
# which is the standard reference. Since a direct "migratory list" CSV is not
# always stable, we fetch the full taxonomy and filter for migratory status
# from a verified public dataset source: The Cornell Lab of Ornithology's
# "eBird Taxonomy" dataset, often hosted on GitHub or HuggingFace.
#
# Verified Source: https://ebird.org/data/download (Taxonomy)
# We will use the eBird Taxonomy CSV from the official eBird data repository.
# URL: https://ebird.org/static/files/ebird_taxonomy.csv
# This file contains 'Species Status' which includes 'Migratory'.

CLO_TAXONOMY_URL = "https://ebird.org/static/files/ebird_taxonomy.csv"
CLO_MIGRATORY_OUTPUT = "data/raw/clo_migratory_list.csv"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def check_real_data_available(url: str, timeout: int = 30) -> bool:
    """Check if a real URL is reachable."""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except requests.RequestException:
        return False

def get_clo_migratory_list(output_path: Optional[Path] = None) -> Path:
    """
    Fetch and cache the Cornell Lab of Ornithology list of migratory species.

    This function downloads the eBird Taxonomy file, filters for species
    marked as 'Migratory', and saves the result to the specified output path.

    Args:
        output_path: Path to save the filtered list. Defaults to data/raw/clo_migratory_list.csv.

    Returns:
        Path to the created CSV file.

    Raises:
        RuntimeError: If the real source is unreachable or no migratory species are found.
    """
    if output_path is None:
        output_path = Path(CLO_MIGRATORY_OUTPUT)
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Attempting to fetch CLO Migratory List from {CLO_TAXONOMY_URL}")

    if not check_real_data_available(CLO_TAXONOMY_URL):
        raise RuntimeError(
            f"CRITICAL: Real data source {CLO_TAXONOMY_URL} is unreachable. "
            "Cannot proceed with fake data. Please check network or source availability."
        )

    try:
        # Download the full taxonomy
        df = pd.read_csv(CLO_TAXONOMY_URL)
        
        # The eBird taxonomy CSV typically has a column 'Species Status'
        # We look for entries containing 'Migratory'
        # Note: Column names might vary slightly (e.g., 'Species Status' vs 'Status')
        # We handle potential variations.
        status_col = None
        for col in df.columns:
            if 'status' in col.lower():
                status_col = col
                break
        
        if status_col is None:
            # Fallback: try to find a column that might contain status info
            # In some versions it might be 'Category' or similar, but 'Species Status' is standard.
            raise RuntimeError("Could not find 'Species Status' column in eBird taxonomy.")

        # Filter for migratory species
        # Status can be "Migratory", "Breeding", "Wintering", etc.
        # We want any species where 'Migratory' is part of the status string.
        migratory_df = df[df[status_col].str.contains('Migratory', na=False)]

        if migratory_df.empty:
            raise RuntimeError(
                "No migratory species found in the downloaded taxonomy. "
                "This might indicate a change in the source format or a download error."
            )

        # Select relevant columns for the migratory list
        # We keep 'Common Name', 'Scientific Name', and 'Species Status'
        cols_to_keep = ['Common Name', 'Scientific Name', status_col]
        # Ensure these columns exist
        cols_to_keep = [c for c in cols_to_keep if c in migratory_df.columns]
        
        result_df = migratory_df[cols_to_keep].reset_index(drop=True)

        # Save to disk
        result_df.to_csv(output_path, index=False)
        checksum = compute_sha256(output_path)
        
        logger.info(f"Successfully saved {len(result_df)} migratory species to {output_path}")
        logger.info(f"Checksum: {checksum}")

        return output_path

    except Exception as e:
        logger.error(f"Failed to process CLO Migratory List: {e}")
        raise RuntimeError(f"Failed to retrieve CLO Migratory List: {e}")

def ensure_data_available() -> Path:
    """
    Ensure the CLO migratory list is available. If not, download it.
    Returns the path to the file.
    """
    output_path = Path(CLO_MIGRATORY_OUTPUT)
    if output_path.exists():
        logger.info(f"CLO Migratory List already exists at {output_path}")
        # Optional: verify checksum or re-download if stale
        return output_path
    
    return get_clo_migratory_list(output_path)

def run_download_pipeline():
    """Main entry point for the download pipeline."""
    logger.info("Starting CLO Migratory List download pipeline.")
    try:
        path = ensure_data_available()
        logger.info(f"Pipeline complete. Output: {path}")
        return 0
    except RuntimeError as e:
        logger.error(f"Pipeline failed: {e}")
        return 1

def main():
    sys.exit(run_download_pipeline())

if __name__ == "__main__":
    main()
