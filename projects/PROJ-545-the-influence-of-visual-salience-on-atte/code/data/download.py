"""
Data download utilities for the Visual Salience project.

This module handles the retrieval of the Moral Machine dataset.
It implements the full fetch, stratified subsetting, and saving logic
as required by Task T013.
"""
import os
import sys
import hashlib
import logging
import requests
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

# Configure logger
logger = logging.getLogger(__name__)

# Project root detection
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

# Moral Machine dataset source
# Source: HuggingFace Datasets (Open Science)
# Dataset: moral-machine
# File: moral_machine_data.csv
MORAL_MACHINE_URL = "https://huggingface.co/datasets/moralmachine/moral_machine_data/resolve/main/moral_machine_data.csv"
# If HuggingFace is not reachable, fallback to the direct GitHub raw link if available,
# or fail loudly as per constraints.
MORAL_MACHINE_GITHUB_RAW = "https://raw.githubusercontent.com/rajan-moralmachine/moral-machine-data/main/moral_machine_data.csv"

def download_from_url(url: str, dest_path: Path, chunk_size: int = 8192) -> bool:
    """
    Downloads a file from a URL to a destination path.
    
    Args:
        url: The source URL.
        dest_path: The local destination path.
        chunk_size: Size of chunks to read.
        
    Returns:
        True if successful, False otherwise.
    """
    logger.info(f"Attempting download from {url}...")
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        logger.info(f"Downloading... Total size: {total_size / 1024 / 1024:.2f} MB")
        
        with open(dest_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        if downloaded % (chunk_size * 100) == 0:
                            logger.debug(f"Progress: {progress:.1f}%")
        
        logger.info(f"Download complete: {dest_path}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download from {url}: {e}")
        return False

def verify_checksum(file_path: Path, expected_hash: str, algorithm: str = "sha256") -> bool:
    """
    Verify the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to verify.
        expected_hash: The expected hex digest.
        algorithm: Hash algorithm (default sha256).
        
    Returns:
        True if the hash matches, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File not found for checksum verification: {file_path}")
        return False

    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    
    actual_hash = hasher.hexdigest()
    if actual_hash.lower() == expected_hash.lower():
        logger.info(f"Checksum verified for {file_path}")
        return True
    else:
        logger.error(f"Checksum mismatch for {file_path}. Expected {expected_hash}, got {actual_hash}")
        return False

def subset_csv(
    input_path: Path, 
    output_path: Path, 
    max_rows: int = 50000, 
    seed: int = 42, 
    stratify_columns: Optional[List[str]] = None
) -> Tuple[int, int]:
    """
    Subsets a CSV file using stratified sampling.
    
    Args:
        input_path: Path to the source CSV.
        output_path: Path to save the subset.
        max_rows: Maximum number of rows to keep.
        seed: Random seed for reproducibility.
        stratify_columns: Columns to use for stratified sampling.
        
    Returns:
        Tuple of (original_count, subset_count).
    """
    import pandas as pd
    
    logger.info(f"Loading data from {input_path}...")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        raise
    
    original_count = len(df)
    logger.info(f"Loaded {original_count} rows.")
    
    if original_count <= max_rows:
        logger.info("Original dataset is already within the row limit. Saving as is.")
        df.to_csv(output_path, index=False)
        return (original_count, original_count)
    
    logger.info(f"Subsetting to {max_rows} rows with seed={seed}...")
    
    # Determine stratification columns
    # Task T013 specifies: stratify by outcome and species
    # We need to map generic column names to the Moral Machine schema if possible.
    # Common Moral Machine columns: 'outcome' (who died), 'species' (if applicable), 'gender', 'age', etc.
    # If specific columns don't exist, we fall back to random sampling without stratification
    # but log a warning.
    
    available_cols = df.columns.tolist()
    stratify_cols = []
    
    # Heuristic mapping for Moral Machine dataset
    outcome_col = None
    species_col = None
    
    # Look for 'outcome' or similar
    for col in ['outcome', 'decision', 'choice']:
        if col in available_cols:
            outcome_col = col
            break
    
    # Look for 'species' or similar (often encoded in 'who_died' or specific columns)
    # In the standard Moral Machine dataset, 'who_died' indicates the category of the dead party.
    # We will try to use 'who_died' or 'outcome' for stratification.
    for col in ['who_died', 'species', 'category']:
        if col in available_cols:
            species_col = col
            break
    
    if outcome_col:
        stratify_cols.append(outcome_col)
    if species_col and species_col != outcome_col:
        stratify_cols.append(species_col)
    
    if not stratify_cols:
        logger.warning("Could not find stratification columns (outcome/species). Falling back to random sampling.")
        # Random sample without stratification
        subset_df = df.sample(n=max_rows, random_state=seed)
    else:
        logger.info(f"Stratifying by columns: {stratify_cols}")
        # Ensure we don't have more strata than rows requested (which would cause sample size issues)
        # pandas sample with stratify handles this by taking proportional representation.
        # We must ensure the sample size is valid for the smallest stratum.
        try:
            subset_df = df.sample(n=max_rows, random_state=seed, stratify=df[stratify_cols])
        except ValueError as e:
            logger.warning(f"Stratified sampling failed: {e}. Falling back to random sampling.")
            subset_df = df.sample(n=max_rows, random_state=seed)
    
    subset_count = len(subset_df)
    subset_df.to_csv(output_path, index=False)
    
    logger.info(f"Subset saved to {output_path} with {subset_count} rows.")
    return (original_count, subset_count)

def download_moral_machine_data(
    output_path: Optional[Path] = None, 
    max_rows: int = 50000, 
    seed: int = 42
) -> Path:
    """
    Orchestrates the download and subsetting of the Moral Machine dataset.
    
    Args:
        output_path: Optional specific output path. Defaults to data/raw/moral_machine_subset.csv.
        max_rows: Target number of rows for the subset.
        seed: Random seed for sampling.
        
    Returns:
        Path to the resulting CSV file.
    """
    if output_path is None:
        output_path = RAW_DATA_DIR / "moral_machine_subset.csv"
        
    logger.info(f"Starting Moral Machine data download process...")
    logger.info(f"Target output: {output_path}")
    logger.info(f"Target rows: {max_rows}, Seed: {seed}")
    
    # Step 1: Download the full dataset
    # We download to a temporary full file first
    temp_full_path = RAW_DATA_DIR / "moral_machine_full.csv"
    
    success = False
    # Try primary source
    if download_from_url(MORAL_MACHINE_URL, temp_full_path):
        success = True
    # Try fallback source
    elif download_from_url(MORAL_MACHINE_GITHUB_RAW, temp_full_path):
        success = True
    
    if not success:
        logger.error("Failed to download the Moral Machine dataset from all known sources.")
        raise RuntimeError("Unable to fetch real data. Aborting.")
    
    # Step 2: Subset the data
    try:
        subset_csv(
            input_path=temp_full_path,
            output_path=output_path,
            max_rows=max_rows,
            seed=seed,
            stratify_columns=['outcome', 'who_died'] # Attempt to use common column names
        )
    except Exception as e:
        logger.error(f"Subsetting failed: {e}")
        # Clean up temp file if subset fails? No, keep it for debugging.
        raise
    
    # Step 3: Clean up full file (optional, but good practice for large files)
    if temp_full_path.exists():
        logger.info("Removing full dataset file to save space.")
        temp_full_path.unlink()
    
    logger.info(f"Download and subsetting complete. Output: {output_path}")
    return output_path

def main():
    """
    Entry point for the download module.
    Runs the full download and subsetting process.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Executing code/data/download.py (T013 Implementation)")
    
    try:
        output_file = download_moral_machine_data()
        logger.info(f"Download process completed successfully. Output at: {output_file}")
    except Exception as e:
        logger.error(f"Download process failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
