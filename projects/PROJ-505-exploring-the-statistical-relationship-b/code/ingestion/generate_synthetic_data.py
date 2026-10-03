"""
Synthetic data generator for ACE and NOAA datasets.
Used as a fallback when real data fetch fails.
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

from utils.logging import get_logger

logger = get_logger(__name__)

def generate_temporal_structure(start_date: datetime, end_date: datetime, freq: str = 'h') -> pd.DatetimeIndex:
    """Generate a regular time index."""
    return pd.date_range(start=start_date, end=end_date, freq=freq)

def generate_synthetic_dataset(start_date: datetime, end_date: datetime, source: str = "ACE") -> pd.DataFrame:
    """
    Generate a multi-year hourly dataset mimicking ACE/WIND composition and NOAA indices distributions.
    Seeded for reproducibility.
    """
    np.random.seed(42)  # Reproducibility
    time_index = generate_temporal_structure(start_date, end_date)
    n_rows = len(time_index)
    
    df = pd.DataFrame({'timestamp': time_index})
    
    if source == "ACE":
        # ACE solar wind composition
        df['V'] = np.random.normal(400, 50, n_rows)  # Solar wind speed km/s
        df['Bz'] = np.random.normal(0, 5, n_rows)    # IMF Bz nT
        df['By'] = np.random.normal(0, 5, n_rows)    # IMF By nT
        df['Bt'] = np.abs(np.sqrt(df['Bz']**2 + df['By']**2))
        df['O/Fe'] = np.random.lognormal(mean=-2, sigma=0.5, size=n_rows)
        df['He/H'] = np.random.lognormal(mean=-1.5, sigma=0.3, size=n_rows)
        df['C/O'] = np.random.lognormal(mean=-0.5, sigma=0.4, size=n_rows)
        df['instrument'] = np.random.choice(['SWICS', 'SWICS-2'], n_rows)
    elif source == "NOAA":
        # NOAA geomagnetic indices
        df['Kp'] = np.random.beta(2, 5, n_rows) * 9  # Kp index 0-9
        df['Dst'] = np.random.normal(-20, 15, n_rows) # Dst index nT
    else:
        raise ValueError(f"Unknown source: {source}")
    
    return df

def main():
    """Entry point for synthetic data generation."""
    parser = argparse.ArgumentParser(description="Generate synthetic solar wind/geomagnetic data.")
    parser.add_argument("--start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--source", type=str, default="ACE", help="Data source (ACE or NOAA)")
    parser.add_argument("--output", type=str, required=True, help="Output path")
    
    args = parser.parse_args()
    start_date = datetime.strptime(args.start, "%Y-%m-%d")
    end_date = datetime.strptime(args.end, "%Y-%m-%d")
    output_path = Path(args.output)
    
    df = generate_synthetic_dataset(start_date, end_date, source=args.source)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Synthetic {args.source} data saved to {output_path}")

if __name__ == "__main__":
    main()
