"""
Data cleaning and resampling module.
Implements FR-003: NaN removal and resampling to fixed short-interval cadence.
File path: code/data/clean.py
"""
import pandas as pd
import numpy as np
from typing import Tuple
from datetime import timedelta

def clean_and_resample(df1: pd.DataFrame, df2: pd.DataFrame, freq: str = '5min') -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Clean and resample two DataFrames to a common time index.
    
    Args:
        df1: First DataFrame (e.g., Solar Wind data) with 'timestamp' column.
        df2: Second DataFrame (e.g., THEMIS Ey data) with 'timestamp' column.
        freq: Target frequency string for resampling (default '5min').
    
    Returns:
        Tuple of (cleaned_df1, cleaned_df2) aligned to the same time index.
    
    Raises:
        ValueError: If 'timestamp' column is missing or data is empty after cleaning.
    """
    # Ensure timestamp is datetime and set as index
    for df in [df1, df2]:
        if 'timestamp' not in df.columns:
            raise ValueError("Input DataFrames must contain a 'timestamp' column.")
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
    
    # Remove NaN rows
    df1_clean = df1.dropna()
    df2_clean = df2.dropna()
    
    if df1_clean.empty or df2_clean.empty:
        raise ValueError("DataFrames are empty after NaN removal.")
    
    # Resample to common frequency (forward fill then back fill to handle gaps)
    df1_resampled = df1_clean.resample(freq).mean()
    df2_resampled = df2_clean.resample(freq).mean()
    
    # Interpolate missing values within the new index
    df1_resampled = df1_resampled.interpolate(method='linear')
    df2_resampled = df2_resampled.interpolate(method='linear')
    
    # Drop any remaining NaNs
    df1_final = df1_resampled.dropna()
    df2_final = df2_resampled.dropna()
    
    # Align indices
    common_index = df1_final.index.intersection(df2_final.index)
    
    if len(common_index) == 0:
        raise ValueError("No common time indices found after resampling.")
    
    return df1_final.loc[common_index], df2_final.loc[common_index]
