"""
Data cleaning and resampling module.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/data/clean.py
"""
import pandas as pd
import numpy as np
from typing import Tuple
from datetime import timedelta

def clean_and_resample(df1: pd.DataFrame, df2: pd.DataFrame, freq: str = '5min') -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Removes NaNs and resamples both DataFrames to a fixed cadence.
    
    Args:
        df1: DataFrame with solar wind data (must have 'timestamp' or datetime index)
        df2: DataFrame with THEMIS data
        freq: Resampling frequency (default '5min')
    
    Returns:
        Tuple of (cleaned_df1, cleaned_df2) aligned on timestamp
    """
    # Ensure timestamp columns are datetime and set as index
    for df in [df1, df2]:
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
        elif not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("Input DataFrames must have a 'timestamp' column or a DatetimeIndex.")
    
    # Resample to fixed frequency (forward fill then drop NaNs to handle gaps)
    df1_resampled = df1.resample(freq).mean()
    df2_resampled = df2.resample(freq).mean()
    
    # Drop rows with NaNs in key columns
    # Assuming key columns are Vsw for df1 and Ey for df2
    key_cols_1 = [c for c in ['Vsw', 'Bz'] if c in df1_resampled.columns]
    key_cols_2 = [c for c in ['Ey'] if c in df2_resampled.columns]
    
    df1_clean = df1_resampled.dropna(subset=key_cols_1)
    df2_clean = df2_resampled.dropna(subset=key_cols_2)
    
    # Align indices
    common_index = df1_clean.index.intersection(df2_clean.index)
    
    return df1_clean.loc[common_index], df2_clean.loc[common_index]
