import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import pandas as pd
import requests

from src.utils.logger import get_logger
from src.ingestion.logging_config import (
    log_download_status,
    log_filter_counts,
    log_harmonization_result,
    log_validation_result
)

# Qiita API configuration
QIITA_BASE_URL = "https://api.qiita.ucdavis.edu"
AGP_STUDY_ID = "10317"  # American Gut Project study ID

def verify_url(url: str) -> bool:
    """Verify that a URL is accessible."""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False

def ensure_qiita_token() -> Optional[str]:
    """
    Ensure Qiita API token is available.
    
    Returns:
        Token string if available, None otherwise
    """
    token = os.environ.get("QIITA_API_TOKEN")
    if not token:
        logger = get_logger(LOG_DOWNLOAD)
        logger.warning("QIITA_API_TOKEN not set in environment")
    return token

def fetch_sample_mapping(study_id: str, token: str) -> pd.DataFrame:
    """
    Fetch sample mapping data from Qiita.
    
    Args:
        study_id: Qiita study ID
        token: Qiita API token
        
    Returns:
        DataFrame with sample mapping information
    """
    logger = get_logger(LOG_DOWNLOAD)
    url = f"{QIITA_BASE_URL}/api/v1/studies/{study_id}/mapping"
    
    headers = {"Authorization": f"Bearer {token}"}
    
    log_download_status(logger, f"Qiita study {study_id}", "STARTED")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        df = pd.DataFrame(data.get("sample_mapping", []))
        
        log_download_status(
            logger, 
            f"Qiita study {study_id}", 
            "SUCCESS",
            file_size=len(response.content),
            checksum=None  # Would compute actual checksum
        )
        
        return df
    except requests.RequestException as e:
        log_download_status(logger, f"Qiita study {study_id}", "FAILED")
        raise RuntimeError(f"Failed to fetch sample mapping: {e}")

def fetch_otu_table(study_id: str, token: str) -> pd.DataFrame:
    """
    Fetch OTU table from Qiita.
    
    Args:
        study_id: Qiita study ID
        token: Qiita API token
        
    Returns:
        DataFrame with OTU table data
    """
    logger = get_logger(LOG_DOWNLOAD)
    url = f"{QIITA_BASE_URL}/api/v1/studies/{study_id}/otu_table"
    
    headers = {"Authorization": f"Bearer {token}"}
    
    log_download_status(logger, f"Qiita OTU table {study_id}", "STARTED")
    
    try:
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        df = pd.DataFrame(data.get("otu_table", []))
        
        log_download_status(
            logger,
            f"Qiita OTU table {study_id}",
            "SUCCESS",
            file_size=len(response.content)
        )
        
        return df
    except requests.RequestException as e:
        log_download_status(logger, f"Qiita OTU table {study_id}", "FAILED")
        raise RuntimeError(f"Failed to fetch OTU table: {e}")

def fetch_agp_data(output_dir: Optional[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fetch all AGP data from Qiita.
    
    Args:
        output_dir: Directory to save raw data files (optional)
        
    Returns:
        Tuple of (sample_mapping_df, otu_table_df)
    """
    logger = get_logger(LOG_DOWNLOAD)
    token = ensure_qiita_token()
    
    if not token:
        raise RuntimeError("Qiita API token required. Set QIITA_API_TOKEN environment variable.")
    
    sample_mapping = fetch_sample_mapping(AGP_STUDY_ID, token)
    otu_table = fetch_otu_table(AGP_STUDY_ID, token)
    
    # Log filtering steps if output_dir is provided
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        initial_count = len(sample_mapping)
        # Example filter: remove samples with missing fiber data
        fiber_col = "dietary_fiber_g_per_day"
        if fiber_col in sample_mapping.columns:
            filtered = sample_mapping.dropna(subset=[fiber_col])
            log_filter_counts(
                logger,
                "missing_fiber_data",
                initial_count,
                len(filtered),
                initial_count - len(filtered),
                "Missing fiber data"
            )
            sample_mapping = filtered
        
        sample_mapping.to_csv(output_path / "agp_sample_mapping.tsv", sep='\t', index=False)
        otu_table.to_csv(output_path / "agp_otu_table.tsv", sep='\t', index=False)
        
        log_harmonization_result(
            logger,
            "AGP",
            {"sample_id": "sample_id", "dietary_fiber_g_per_day": "fiber_g_per_day"},
            {"fiber": "g/day"}
        )
    
    return sample_mapping, otu_table

def build_arg_parser() -> argparse.ArgumentParser:
    """Build argument parser for AGP loader."""
    parser = argparse.ArgumentParser(description="Download AGP data from Qiita")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw/agp",
        help="Directory to save raw AGP data"
    )
    parser.add_argument(
        "--study-id",
        type=str,
        default=AGP_STUDY_ID,
        help="Qiita study ID"
    )
    return parser

def main():
    """Main entry point for AGP loader."""
    parser = build_arg_parser()
    args = parser.parse_args()
    
    logger = get_logger(LOG_DOWNLOAD)
    logger.info("Starting AGP data download")
    
    try:
        sample_mapping, otu_table = fetch_agp_data(args.output_dir)
        log_validation_result(logger, "AGP download", True, f"Retrieved {len(sample_mapping)} samples")
        print(f"Successfully downloaded AGP data: {len(sample_mapping)} samples")
    except Exception as e:
        log_validation_result(logger, "AGP download", False, str(e))
        logger.error(f"Failed to download AGP data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
