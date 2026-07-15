"""
Data cleaning and resampling module for solar wind and geomagnetic data.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/data/clean.py
"""
import pandas as pd
import numpy as np
from typing import Tuple
from datetime import timedelta

def clean_and_resample(df1: pd.DataFrame, df2: pd.DataFrame, target_freq: str = '5min') -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Clean NaN values and resample two DataFrames to a fixed cadence.
    
    Args:
        df1: First DataFrame (e.g., Solar Wind data) with 'timestamp' column.
        df2: Second DataFrame (e.g., THEMIS data) with 'timestamp' column.
        freq: Resampling frequency string (default '5min').
        
    Returns:
        Tuple of (cleaned_df1, cleaned_df2) aligned on timestamp index.
    """
    def process_single(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        
        # Ensure timestamp is datetime and set as index
        if 'timestamp' in df.columns:
            df = df.copy()
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
        
        # Remove rows where all data columns are NaN
        df = df.dropna(how='all')
        
        # Resample to fixed frequency (forward fill then backward fill for gaps)
        df = df.resample(freq).mean()
        df = df.ffill().bfill()
        
        return df

    cleaned1 = process_single(df1)
    cleaned2 = process_single(df2)
    
    # Align indices
    common_index = cleaned1.index.intersection(cleaned2.index)
    cleaned1 = cleaned1.loc[common_index]
    cleaned2 = cleaned2.loc[common_index]
    
    return cleaned1, cleaned2
