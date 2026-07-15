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
    Remove NaN values and resample two DataFrames to a fixed cadence.
    
    Args:
        df1: First DataFrame (e.g., OMNI solar wind data) with 'timestamp' column.
        df2: Second DataFrame (e.g., THEMIS electric field data) with 'timestamp' column.
        target_freq: Target frequency string for resampling (default '5min').
    
    Returns:
        Tuple of (cleaned_df1, cleaned_df2) aligned to the target frequency.
    """
    def _process_df(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        
        # Ensure timestamp is datetime and set as index
        if 'timestamp' in df.columns:
            df = df.copy()
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
        
        # Remove rows where any column is NaN
        df_clean = df.dropna()
        
        # Resample to target frequency (mean for numeric data)
        df_resampled = df_clean.resample(target_freq).mean()
        
        # Drop any remaining NaNs introduced by resampling (e.g., empty bins)
        df_resampled = df_resampled.dropna()
        
        return df_resampled

    processed_df1 = _process_df(df1)
    processed_df2 = _process_df(df2)

    # Align indices by taking the intersection of timestamps
    common_index = processed_df1.index.intersection(processed_df2.index)
    
    if len(common_index) == 0:
        # Return empty frames with correct columns if no overlap
        return processed_df1.iloc[:0], processed_df2.iloc[:0]

    aligned_df1 = processed_df1.loc[common_index]
    aligned_df2 = processed_df2.loc[common_index]

    return aligned_df1, aligned_df2
