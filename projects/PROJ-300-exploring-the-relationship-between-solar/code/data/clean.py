"""
Data cleaning and resampling module.

File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/data/clean.py
"""
import pandas as pd
import numpy as np
from typing import Tuple
from datetime import timedelta
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

def clean_and_resample(df_sw: pd.DataFrame, df_ey: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Remove NaN values and resample both DataFrames to a common regular cadence (5 minutes).
    
    Args:
        df_sw: Solar wind DataFrame with 'timestamp', 'Vsw', 'Bz'
        df_ey: THEMIS DataFrame with 'timestamp', 'Ey'
        
    Returns:
        tuple: (df_sw_clean, df_ey_clean) resampled DataFrames
    """
    # Set timestamp as index
    df_sw = df_sw.set_index('timestamp').sort_index()
    df_ey = df_ey.set_index('timestamp').sort_index()
    
    # Drop rows where timestamp or value is NaN
    df_sw = df_sw.dropna()
    df_ey = df_ey.dropna()
    
    # Resample to 5-minute intervals using mean
    df_sw_resampled = df_sw.resample('5T').mean()
    df_ey_resampled = df_ey.resample('5T').mean()
    
    # Re-align indices to the union of both time series
    common_index = df_sw_resampled.index.union(df_ey_resampled.index)
    
    df_sw_clean = df_sw_resampled.reindex(common_index)
    df_ey_clean = df_ey_resampled.reindex(common_index)
    
    # Drop rows where either Vsw or Ey is NaN (after alignment)
    mask = df_sw_clean['Vsw'].notna() & df_ey_clean['Ey'].notna()
    df_sw_clean = df_sw_clean[mask]
    df_ey_clean = df_ey_clean[mask]
    
    logger.info(f"Resampled data to 5-minute cadence. Remaining points: {len(df_sw_clean)}")
    
    return df_sw_clean.reset_index(), df_ey_clean.reset_index()

def handle_gaps(df: pd.DataFrame, max_gap_minutes: int = 30) -> pd.DataFrame:
    """
    Identify gaps > max_gap_minutes and truncate the series at the gap.
    
    Args:
        df: DataFrame with 'timestamp' column
        max_gap_minutes: Maximum allowed gap in minutes
        
    Returns:
        pd.DataFrame: Truncated DataFrame
    """
    if df.empty:
        return df
        
    df = df.set_index('timestamp').sort_index()
    df.index = pd.to_datetime(df.index)
    
    # Calculate time differences
    time_diffs = df.index.to_series().diff()
    
    # Identify gaps
    gap_mask = time_diffs > timedelta(minutes=max_gap_minutes)
    
    if gap_mask.any():
        # Find the first gap
        first_gap_idx = gap_mask.idxmax()
        logger.warning(f"Large gap detected at {first_gap_idx}. Truncating series.")
        
        # Truncate before the gap
        df = df.loc[:first_gap_idx - timedelta(minutes=1)]
        
        # Log warning
        warnings_log_path = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'quality_log.json'
        if warnings_log_path.exists():
            with open(warnings_log_path, 'r') as f:
                log_data = json.load(f)
        else:
            log_data = {"entries": []}
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "warning": f"Gap > {max_gap_minutes} minutes detected at {first_gap_idx}. Series truncated."
        }
        log_data["entries"].append(log_entry)
        
        with open(warnings_log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    return df.reset_index()
