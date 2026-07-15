"""
Data Cleaning and Resampling Module.

Handles NaN removal and resampling to a fixed cadence.

File path: code/data/clean.py
"""
import pandas as pd
import numpy as np
from typing import Tuple
from datetime import timedelta

def clean_and_resample(df1: pd.DataFrame, df2: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Cleans two DataFrames by removing NaNs and resampling to a common 5-minute cadence.
    
    Args:
        df1: First DataFrame (e.g., Solar Wind).
        df2: Second DataFrame (e.g., THEMIS Ey).
        
    Returns:
        Tuple of (cleaned_df1, cleaned_df2) with aligned indices.
    """
    # Ensure timestamp is index
    if 'timestamp' in df1.columns:
        df1 = df1.set_index('timestamp')
    if 'timestamp' in df2.columns:
        df2 = df2.set_index('timestamp')
        
    # Sort index
    df1 = df1.sort_index()
    df2 = df2.sort_index()
    
    # Resample to 5 minutes
    # Using 'mean' for numeric columns
    df1_resampled = df1.resample('5min').mean()
    df2_resampled = df2.resample('5min').mean()
    
    # Drop NaN rows
    df1_clean = df1_resampled.dropna()
    df2_clean = df2_resampled.dropna()
    
    # Align indices (intersection)
    common_idx = df1_clean.index.intersection(df2_clean.index)
    
    return df1_clean.loc[common_idx], df2_clean.loc[common_idx]
