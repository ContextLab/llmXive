"""
Data cleaning and resampling module.
Implements FR-003: NaN removal and resampling to fixed short-interval cadence.
File: projects/PROJ-300-exploring-the-relationship-between-solar/code/data/clean.py
"""
import pandas as pd
import numpy as np
from typing import Tuple
from datetime import timedelta

def clean_and_resample(df1: pd.DataFrame, df2: pd.DataFrame, freq: str = "5min") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Clean two DataFrames by removing NaNs and resampling to a fixed frequency.
    
    Args:
        df1: First DataFrame (e.g., Solar Wind data) with 'timestamp' column.
        df2: Second DataFrame (e.g., THEMIS data) with 'timestamp' column.
        freq: Target frequency string for resampling (default "5min").
    
    Returns:
        Tuple of (cleaned_df1, cleaned_df2) aligned on timestamp.
    """
    def process_df(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        
        # Ensure timestamp is datetime
        if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        df = df.set_index('timestamp')
        
        # Resample to target frequency (forward fill then drop NaNs to handle gaps)
        # Using mean for numeric columns, but drop any resulting NaNs from empty bins
        df_resampled = df.resample(freq).mean()
        df_clean = df_resampled.dropna()
        
        return df_clean.reset_index()

    cleaned1 = process_df(df1.copy())
    cleaned2 = process_df(df2.copy())

    # Merge on timestamp to ensure alignment
    merged = pd.merge(cleaned1, cleaned2, on='timestamp', how='inner')
    
    if merged.empty:
        raise ValueError("No overlapping time data found between the two datasets after cleaning.")

    return merged, merged
