import argparse
import logging
import os
import sys
import hashlib
import time
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import requests

from src.utils.logger import get_logger
from src.ingestion.logging_config import (
    log_download_status,
    log_filter_counts,
    log_harmonization_result,
    log_validation_result
)

# UK Biobank configuration
# Note: UKBB requires authentication. In production, use proper credentials.
UKBB_BASE_URL = "https://biobank.ndph.ox.ac.uk/ukb"
UKBB_DATA_FILE = "field_21022.csv"  # Dietary fiber field
UKBB_SAMPLE_FILE = "sample_info.csv"

def verify_url(url: str) -> bool:
    """Verify that a URL is accessible."""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False

def calculate_file_checksum(file_path: str) -> str:
    """
    Calculate SHA256 checksum of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        SHA256 checksum string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, output_path: str, chunk_size: int = 8192) -> str:
    """
    Download a file from URL with progress logging.
    
    Args:
        url: Download URL
        output_path: Local path to save file
        chunk_size: Chunk size for downloading
        
    Returns:
        Path to downloaded file
    """
    logger = get_logger(LOG_DOWNLOAD)
    
    log_download_status(logger, url, "STARTED")
    
    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Log progress every 10%
                    if total_size > 0 and downloaded % (total_size // 10) < chunk_size:
                        progress = (downloaded / total_size) * 100
                        logger.debug(f"Download progress: {progress:.1f}%")
        
        checksum = calculate_file_checksum(output_path)
        
        log_download_status(
            logger,
            url,
            "SUCCESS",
            file_size=downloaded,
            checksum=checksum
        )
        
        return output_path
        
    except requests.RequestException as e:
        log_download_status(logger, url, "FAILED")
        raise RuntimeError(f"Failed to download file: {e}")

def fetch_ukbb_data(output_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Fetch UK Biobank dietary data.
    
    Args:
        output_dir: Directory to save raw data files (optional)
        
    Returns:
        DataFrame with UKBB dietary data
    """
    logger = get_logger(LOG_DOWNLOAD)
    
    # In a real scenario, this would use UKBB API credentials
    # For demonstration, we'll use a placeholder URL
    # Replace with actual UKBB data access URL
    fiber_url = f"{UKBB_BASE_URL}/download/field_21022.csv"
    sample_url = f"{UKBB_BASE_URL}/download/sample_info.csv"
    
    if not verify_url(fiber_url):
        logger.warning(f"UKBB fiber data URL not accessible: {fiber_url}")
        # In production, this would raise an error
        # For now, we'll create a minimal mock to allow the pipeline to continue
        # NOTE: This is a fallback for testing; real implementation must use real data
        logger.error("UKBB data requires authentication. Please set up credentials.")
        raise RuntimeError("UKBB data access requires proper authentication")
    
    # Create output directory if specified
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Download fiber data
        fiber_file = output_path / "ukbb_fiber_data.csv"
        download_file(fiber_url, str(fiber_file))
        
        # Download sample info
        sample_file = output_path / "ukbb_sample_info.csv"
        download_file(sample_url, str(sample_file))
        
        # Load data
        fiber_df = pd.read_csv(fiber_file)
        sample_df = pd.read_csv(sample_file)
        
        # Merge datasets
        merged_df = pd.merge(fiber_df, sample_df, on='eid', how='inner')
        
        # Log filtering steps
        initial_count = len(merged_df)
        
        # Filter for valid fiber intake (0-200 g/day)
        if 'dietary_fiber_g_per_day' in merged_df.columns:
            filtered = merged_df[
                (merged_df['dietary_fiber_g_per_day'] >= 0) & 
                (merged_df['dietary_fiber_g_per_day'] <= 200)
            ]
            log_filter_counts(
                logger,
                "fiber_range",
                initial_count,
                len(filtered),
                initial_count - len(filtered),
                "Fiber intake outside 0-200 g/day range"
            )
            merged_df = filtered
        
        # Filter for missing fiber data
        if 'dietary_fiber_g_per_day' in merged_df.columns:
            no_missing = merged_df.dropna(subset=['dietary_fiber_g_per_day'])
            log_filter_counts(
                logger,
                "missing_fiber",
                len(merged_df),
                len(no_missing),
                len(merged_df) - len(no_missing),
                "Missing fiber data"
            )
            merged_df = no_missing
        
        # Save processed data
        merged_df.to_csv(output_path / "ukbb_processed.tsv", sep='\t', index=False)
        
        log_harmonization_result(
            logger,
            "UKBB",
            {"eid": "sample_id", "dietary_fiber_g_per_day": "fiber_g_per_day"},
            {"fiber": "g/day"}
        )
        
        log_validation_result(
            logger,
            "UKBB download",
            True,
            f"Retrieved {len(merged_df)} samples"
        )
        
        return merged_df
    
    else:
        # Return empty dataframe if no output dir specified
        return pd.DataFrame()

def build_arg_parser() -> argparse.ArgumentParser:
    """Build argument parser for UKBB loader."""
    parser = argparse.ArgumentParser(description="Download UKBB data")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw/ukbb",
        help="Directory to save raw UKBB data"
    )
    return parser

def main():
    """Main entry point for UKBB loader."""
    parser = build_arg_parser()
    args = parser.parse_args()
    
    logger = get_logger(LOG_DOWNLOAD)
    logger.info("Starting UKBB data download")
    
    try:
        df = fetch_ukbb_data(args.output_dir)
        if not df.empty:
            print(f"Successfully downloaded UKBB data: {len(df)} samples")
    except Exception as e:
        log_validation_result(logger, "UKBB download", False, str(e))
        logger.error(f"Failed to download UKBB data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
