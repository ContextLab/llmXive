"""
Data cleaning and resampling module.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/data/clean.py
"""
import pandas as pd
import numpy as np
from typing import Tuple
from datetime import timedelta

def clean_and_resample(df1: pd.DataFrame, df2: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Clean two DataFrames by removing NaNs and resampling to a fixed cadence (5 minutes).
    
    Args:
        df1: Solar wind data (Vsw, Bz) with 'timestamp' column.
        df2: THEMIS data (Ey) with 'timestamp' column.
        
    Returns:
        Tuple of (cleaned_df1, cleaned_df2) aligned on timestamp.
    """
    # Ensure timestamp is datetime
    for df in [df1, df2]:
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        else:
            raise ValueError("Input DataFrames must have a 'timestamp' column")
    
    # Sort by timestamp
    df1 = df1.sort_values('timestamp')
    df2 = df2.sort_values('timestamp')
    
    # Resample to 5-minute intervals
    # We assume the index is timestamp for resampling, so set it
    df1 = df1.set_index('timestamp')
    df2 = df2.set_index('timestamp')
    
    # Resample: mean for numeric columns
    df1_resampled = df1.resample('5T').mean()
    df2_resampled = df2.resample('5T').mean()
    
    # Drop NaNs resulting from resampling (gaps in original data)
    df1_clean = df1_resampled.dropna()
    df2_clean = df2_resampled.dropna()
    
    # Reset index to make 'timestamp' a column again for merging later
    df1_clean = df1_clean.reset_index()
    df2_clean = df2_clean.reset_index()
    
    return df1_clean, df2_clean
