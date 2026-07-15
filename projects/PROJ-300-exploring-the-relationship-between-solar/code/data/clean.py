"""
Data cleaning and resampling module for solar wind and geomagnetic data.
This file is part of the PROJ-300 solar wind reconnection analysis pipeline.
"""
import pandas as pd
import numpy as np
from typing import Tuple
from datetime import timedelta


def clean_and_resample(df_omni: pd.DataFrame, df_themis: pd.DataFrame, target_freq: str = '5T') -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Clean data by removing NaN values and resample to a fixed time interval.

    This function implements FR-003: Data cleaning and resampling.

    Parameters:
    -----------
    df_omni : pd.DataFrame
        OMNI solar wind data with columns ['timestamp', 'Vsw', 'Bz']
    df_themis : pd.DataFrame
        THEMIS magnetotail data with columns ['timestamp', 'Ey']
    target_freq : str
        Target frequency for resampling (default: '5T' for 5 minutes)

    Returns:
    --------
    Tuple[pd.DataFrame, pd.DataFrame]
        Cleaned and resampled OMNI and THEMIS DataFrames with aligned timestamps
    """
    # Handle empty inputs
    if df_omni.empty or df_themis.empty:
        return df_omni.copy(), df_themis.copy()

    # Ensure timestamp columns are datetime
    df_omni = df_omni.copy()
    df_themis = df_themis.copy()
    df_omni['timestamp'] = pd.to_datetime(df_omni['timestamp'])
    df_themis['timestamp'] = pd.to_datetime(df_themis['timestamp'])

    # Set timestamp as index for resampling
    df_omni = df_omni.set_index('timestamp')
    df_themis = df_themis.set_index('timestamp')

    # Remove rows with any NaN values
    df_omni_clean = df_omni.dropna()
    df_themis_clean = df_themis.dropna()

    # Check if either DataFrame is empty after cleaning
    if df_omni_clean.empty or df_themis_clean.empty:
        # Return empty DataFrames with correct structure
        return df_omni_clean, df_themis_clean

    # Resample to target frequency using mean aggregation
    df_omni_resampled = df_omni_clean.resample(target_freq).mean()
    df_themis_resampled = df_themis_clean.resample(target_freq).mean()

    # Align both DataFrames to the same time index (intersection)
    common_index = df_omni_resampled.index.intersection(df_themis_resampled.index)
    df_omni_aligned = df_omni_resampled.loc[common_index]
    df_themis_aligned = df_themis_resampled.loc[common_index]

    # Remove any remaining NaN values that might occur after alignment
    df_omni_final = df_omni_aligned.dropna()
    df_themis_final = df_themis_aligned.dropna()

    # Reset index to make timestamp a column again
    df_omni_final = df_omni_final.reset_index()
    df_themis_final = df_themis_final.reset_index()

    return df_omni_final, df_themis_final
