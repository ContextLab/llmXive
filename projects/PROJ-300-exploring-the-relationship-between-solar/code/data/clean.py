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
PROJECT_ROOT = Path(__file__).parent.parent.parent

def clean_and_resample(df_sw: pd.DataFrame, df_ey: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Remove NaN values and resample both DataFrames to a common regular cadence.
    
    Args:
        df_sw: Solar wind DataFrame with columns [timestamp, Vsw, Bz]
        df_ey: THEMIS DataFrame with columns [timestamp, Ey]
        
    Returns:
        Tuple of (cleaned_sw_df, cleaned_ey_df) with aligned indices
    """
    logger.info("Cleaning and resampling data...")
    
    # Ensure timestamp is datetime and set as index
    if 'timestamp' in df_sw.columns:
        df_sw['timestamp'] = pd.to_datetime(df_sw['timestamp'])
        df_sw = df_sw.set_index('timestamp')
    
    if 'timestamp' in df_ey.columns:
        df_ey['timestamp'] = pd.to_datetime(df_ey['timestamp'])
        df_ey = df_ey.set_index('timestamp')
    
    # Drop rows with NaN values
    df_sw_clean = df_sw.dropna()
    df_ey_clean = df_ey.dropna()
    
    # Resample to 5-minute intervals
    df_sw_clean = df_sw_clean.resample('5T').mean()
    df_ey_clean = df_ey_clean.resample('5T').mean()
    
    # Re-align indices
    common_index = df_sw_clean.index.intersection(df_ey_clean.index)
    df_sw_clean = df_sw_clean.loc[common_index]
    df_ey_clean = df_ey_clean.loc[common_index]
    
    # Drop any remaining NaNs after alignment
    df_sw_clean = df_sw_clean.dropna()
    df_ey_clean = df_ey_clean.dropna()
    
    logger.info(f"Cleaned data shapes: SW={df_sw_clean.shape}, EY={df_ey_clean.shape}")
    
    return df_sw_clean, df_ey_clean

def handle_gaps(df: pd.DataFrame, max_gap_minutes: int = 30) -> pd.DataFrame:
    """
    Flag or truncate series with gaps exceeding max_gap_minutes.
    
    Args:
        df: DataFrame with datetime index
        max_gap_minutes: Maximum allowed gap in minutes
        
    Returns:
        DataFrame with gaps handled (truncated at large gaps)
    """
    logger.info(f"Checking for gaps > {max_gap_minutes} minutes...")
    
    if df.empty:
        return df
    
    # Calculate time differences
    time_diffs = df.index.to_series().diff()
    
    # Identify gaps
    gap_mask = time_diffs > timedelta(minutes=max_gap_minutes)
    gap_indices = df.index[gap_mask]
    
    if len(gap_indices) > 0:
        logger.warning(f"Found {len(gap_indices)} gaps exceeding {max_gap_minutes} minutes")
        
        # Truncate at the first large gap
        first_gap_idx = gap_indices[0]
        df = df.loc[:first_gap_idx]
        
        logger.info(f"Truncated data at first large gap: {first_gap_idx}")
    
    return df
