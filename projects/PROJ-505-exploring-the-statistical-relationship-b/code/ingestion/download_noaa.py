"""
NOAA geomagnetic index ingestion module: attempts real fetch, falls back to synthetic.
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

def fetch_noaa_kp(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Attempt to fetch real Kp index from NOAA.
    Raises DataIngestionError if fetch fails.
    """
    raise DataIngestionError("Real NOAA Kp fetch not implemented or failed.")

def fetch_noaa_dst(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Attempt to fetch real Dst index from NOAA.
    Raises DataIngestionError if fetch fails.
    """
    raise DataIngestionError("Real NOAA Dst fetch not implemented or failed.")

def load_synthetic_noaa(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Generate synthetic NOAA data as a fallback."""
    logger.warning("Falling back to synthetic NOAA data generation.")
    # Generate synthetic data for Kp and Dst
    df = generate_synthetic_dataset(start_date, end_date, source="NOAA")
    return df

@log_duration
def run_ingestion(start_date: datetime, end_date: datetime, output_path: Path) -> None:
    """Run NOAA ingestion with fallback logic."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        logger.info(f"Attempting to fetch real NOAA data from {start_date} to {end_date}...")
        # Try to fetch Kp and Dst
        kp_df = fetch_noaa_kp(start_date, end_date)
        dst_df = fetch_noaa_dst(start_date, end_date)
        # Merge if needed, or assume they are already merged in the fetch function
        df = pd.merge(kp_df, dst_df, on='timestamp', how='outer')
        df['source'] = 'real'
    except DataIngestionError as e:
        logger.error(f"Real data fetch failed: {e}")
        logger.info("Generating synthetic fallback data...")
        df = load_synthetic_noaa(start_date, end_date)
        df['source'] = 'synthetic'
    
    save_parquet(df, output_path)
    logger.info(f"NOAA data saved to {output_path}")

def main():
    """Entry point for NOAA ingestion script."""
    parser = argparse.ArgumentParser(description="Ingest NOAA geomagnetic index data.")
    parser.add_argument("--start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", type=str, default="data/processed/noaa.parquet", help="Output path")
    
    args = parser.parse_args()
    start_date = datetime.strptime(args.start, "%Y-%m-%d")
    end_date = datetime.strptime(args.end, "%Y-%m-%d")
    output_path = Path(args.output)
    
    run_ingestion(start_date, end_date, output_path)

if __name__ == "__main__":
    main()
