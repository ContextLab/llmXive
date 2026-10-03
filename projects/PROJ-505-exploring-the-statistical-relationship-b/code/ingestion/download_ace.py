"""
ACE data ingestion module: attempts real fetch, falls back to synthetic if failed.
"""
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import logging

import pandas as pd
import numpy as np

from utils.logging import DataIngestionError, get_logger, log_duration
from utils.io import save_parquet
from ingestion.generate_synthetic_data import generate_synthetic_dataset

logger = get_logger(__name__)

def fetch_ace_data(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Attempt to fetch real ACE data from CDAWeb.
    Raises DataIngestionError if fetch fails.
    """
    # Placeholder for real fetch logic
    # In a real implementation, this would use requests or a specific API client
    # to download from CDAWeb
    raise DataIngestionError("Real ACE data fetch not implemented or failed.")

def load_synthetic_ace(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Generate synthetic ACE data as a fallback."""
    logger.warning("Falling back to synthetic ACE data generation.")
    return generate_synthetic_dataset(start_date, end_date, source="ACE")

@log_duration
def run_ingestion(start_date: datetime, end_date: datetime, output_path: Path) -> None:
    """Run ACE ingestion with fallback logic."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        logger.info(f"Attempting to fetch real ACE data from {start_date} to {end_date}...")
        df = fetch_ace_data(start_date, end_date)
        df['source'] = 'real'
    except DataIngestionError as e:
        logger.error(f"Real data fetch failed: {e}")
        logger.info("Generating synthetic fallback data...")
        df = load_synthetic_ace(start_date, end_date)
        df['source'] = 'synthetic'
    
    save_parquet(df, output_path)
    logger.info(f"ACE data saved to {output_path}")

def main():
    """Entry point for ACE ingestion script."""
    parser = argparse.ArgumentParser(description="Ingest ACE solar wind data.")
    parser.add_argument("--start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", type=str, default="data/processed/ace.parquet", help="Output path")
    
    args = parser.parse_args()
    start_date = datetime.strptime(args.start, "%Y-%m-%d")
    end_date = datetime.strptime(args.end, "%Y-%m-%d")
    output_path = Path(args.output)
    
    run_ingestion(start_date, end_date, output_path)

if __name__ == "__main__":
    main()
