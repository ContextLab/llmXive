"""
Data Ingestion Utilities.
Handles loading, validation, and missingness detection.
"""
import os
import sys
import logging
import hashlib
import pandas as pd
import numpy as np
from typing import List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_gss_data_subset(file_path: str) -> pd.DataFrame:
    """Load GSS data from a CSV file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} rows from {file_path}")
    return df

def ensure_design_columns(df: pd.DataFrame) -> bool:
    """Check for presence of design columns. Returns True if all present."""
    required = ['weight', 'psu', 'strata']
    missing = [c for c in required if c not in df.columns]
    if missing:
        logger.error(f"Missing design columns: {missing}")
        return False
    return True

def detect_missingness(df: pd.DataFrame, threshold: float = 0.3) -> List[str]:
    """
    Detect variables with missingness above the threshold.
    Returns a list of variable names exceeding the threshold.
    """
    missing_rates = df.isnull().mean()
    high_missing = missing_rates[missing_rates > threshold].index.tolist()
    if high_missing:
        logger.warning(f"Variables with >{threshold*100}% missingness: {high_missing}")
    return high_missing

def ingest_and_save(source_url: str, output_path: str, cache_dir: str):
    """
    Wrapper to fetch and save data, ensuring design columns.
    Delegates to data_fetcher logic but ensures the specific output path is used.
    """
    from data_fetcher import fetch_and_save_data
    fetch_and_save_data(source_url, output_path, cache_dir, "gss")

def compute_checksum(file_path: str) -> str:
    """Compute SHA-256 checksum."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """CLI for ingestion."""
    import argparse
    parser = argparse.ArgumentParser(description="Ingest GSS data.")
    parser.add_argument("--url", type=str, required=True)
    parser.add_argument("--output", type=str, required=True)
    parser.add_argument("--cache", type=str, default="data/raw/cache")
    args = parser.parse_args()
    ingest_and_save(args.url, args.output, args.cache)

if __name__ == "__main__":
    main()
