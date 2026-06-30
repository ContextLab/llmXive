"""
code/data/clean.py
Implements data cleaning and resampling.
"""
import pandas as pd
import numpy as np
from typing import Tuple
from datetime import timedelta


def clean_and_resample(df1: pd.DataFrame, df2: pd.DataFrame, cadence_minutes: int = 5) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Cleans two DataFrames by removing NaNs and resampling to a fixed cadence.
    
    Args:
        df1: First DataFrame (e.g., Vsw).
        df2: Second DataFrame (e.g., Ey).
        cadence_minutes: Target cadence in minutes.
        
    Returns:
        Tuple of (cleaned_df1, cleaned_df2) aligned to common timestamps.
    """
    # Ensure timestamp columns are datetime
    df1 = df1.copy()
    df2 = df2.copy()
    
    df1['timestamp'] = pd.to_datetime(df1['timestamp'])
    df2['timestamp'] = pd.to_datetime(df2['timestamp'])
    
    # Set index
    df1 = df1.set_index('timestamp')
    df2 = df2.set_index('timestamp')
    
    # Resample
    df1_resampled = df1.resample(f'{cadence_minutes}T').mean()
    df2_resampled = df2.resample(f'{cadence_minutes}T').mean()
    
    # Drop NaNs
    df1_clean = df1_resampled.dropna()
    df2_clean = df2_resampled.dropna()
    
    # Align indices
    common_idx = df1_clean.index.intersection(df2_clean.index)
    
    return df1_clean.loc[common_idx].reset_index(), df2_clean.loc[common_idx].reset_index()