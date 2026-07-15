"""
Data cleaning and resampling module for solar wind and geomagnetic data.
File: projects/PROJ-300-exploring-the-relationship-between-solar/code/data/clean.py
"""
import pandas as pd
import numpy as np
from typing import Tuple
from datetime import timedelta

def clean_and_resample(df1: pd.DataFrame, df2: pd.DataFrame, freq: str = "5min") -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Clean NaN values and resample two DataFrames to a fixed cadence.
    
    Args:
        df1: First DataFrame (e.g., Solar Wind: Vsw, Bz) with 'timestamp' column.
        df2: Second DataFrame (e.g., THEMIS: Ey) with 'timestamp' column.
        freq: Target frequency string for pandas resample (default '5min').
    
    Returns:
        Tuple of (cleaned_df1, cleaned_df2) aligned on timestamp index.
    
    Raises:
        ValueError: If input DataFrames are empty or lack required columns.
    """
    if df1.empty or df2.empty:
        raise ValueError("Input DataFrames cannot be empty.")
    
    if 'timestamp' not in df1.columns or 'timestamp' not in df2.columns:
        raise ValueError("Both DataFrames must contain a 'timestamp' column.")

    # Ensure timestamp is datetime
    df1 = df1.copy()
    df2 = df2.copy()
    df1['timestamp'] = pd.to_datetime(df1['timestamp'])
    df2['timestamp'] = pd.to_datetime(df2['timestamp'])

    # Set timestamp as index
    df1 = df1.set_index('timestamp')
    df2 = df2.set_index('timestamp')

    # Resample and forward fill then drop remaining NaNs
    # Using mean for numeric aggregation to handle resampling
    df1_resampled = df1.resample(freq).mean()
    df2_resampled = df2.resample(freq).mean()

    # Drop rows where all values are NaN after resampling
    df1_resampled = df1_resampled.dropna(how='all')
    df2_resampled = df2_resampled.dropna(how='all')

    # Align indices
    common_index = df1_resampled.index.intersection(df2_resampled.index)
    
    df1_clean = df1_resampled.loc[common_index]
    df2_clean = df2_resampled.loc[common_index]

    # Final drop of any remaining NaNs in critical columns
    # Assuming Vsw is in df1 and Ey is in df2 based on task context
    # We drop rows where ANY value is NaN to ensure strict alignment for correlation
    df1_clean = df1_clean.dropna()
    df2_clean = df2_clean.dropna()

    return df1_clean, df2_clean
