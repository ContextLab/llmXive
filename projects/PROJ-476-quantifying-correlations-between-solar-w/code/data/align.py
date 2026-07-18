import os
import pandas as pd
import numpy as np
from datetime import timedelta
from code import logger
from code.config import ACE_VARS, NOAA_VARS, TRAIN_START, TEST_END

def load_raw_ace(filepath: str) -> pd.DataFrame:
    """Loads raw ACE data from a CSV file."""
    try:
        df = pd.read_csv(filepath)
        return df
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        raise

def load_raw_noaa(filepath: str) -> pd.DataFrame:
    """Loads raw NOAA data from a CSV file."""
    try:
        df = pd.read_csv(filepath)
        return df
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        raise

def align_to_hourly(df: pd.DataFrame, target_freq: str='1h') -> pd.DataFrame:
    """Resamples the DataFrame to an hourly frequency."""
    df = df.set_index('timestamp')
    df = df.resample(target_freq).mean()
    return df

def interpolate_gaps(df: pd.DataFrame, max_gap_hours: int=6) -> pd.DataFrame:
    """Interpolates missing values in the DataFrame."""
    # Check for gaps larger than 6 hours and log a warning
    if df.isnull().sum().any():
        gaps = df.diff().isnull().sum()
        large_gaps = gaps[gaps > max_gap_hours]
        if not large_gaps.empty:
            logger.warning(f"Gaps larger than {max_gap_hours} hours detected in columns: {large_gaps.index.tolist()}")

    df = df.interpolate()  # Linear interpolation
    assert df.isnull().sum().sum() == 0, "DataFrame still contains NaNs after interpolation."
    return df


def run_alignment(ace_filepath: str, noaa_filepath: str) -> pd.DataFrame:
    """Runs the entire alignment pipeline."""

    ace_df = load_raw_ace(ace_filepath)
    noaa_df = load_raw_noaa(noaa_filepath)

    # Rename ACE columns to match output schema
    ace_df = ace_df.rename(columns={
        'N_p': 'proton_density',
        'T_p': 'temperature',
        'He2+_ratio': 'helium_abundance'
    })

    # Merge the DataFrames based on timestamp
    merged_df = pd.merge(ace_df, noaa_df, on='timestamp')

    aligned_df = align_to_hourly(merged_df)
    interpolated_df = interpolate_gaps(aligned_df)
    return interpolated_df


def write_synced_csv(df: pd.DataFrame, output_path: str) -> None:
    """Writes the synced DataFrame to a CSV file.
    
    Ensures columns are renamed to the canonical schema and asserts 
    data integrity (no NaNs, correct columns) before writing.
    """
    # 1. Ensure timestamp is a column, not just index (if it was set previously)
    if isinstance(df.index, pd.DatetimeIndex):
        df = df.reset_index()

    # 2. Explicitly rename columns to match the output schema
    # This handles cases where the input might still have raw ACE names
    rename_map = {
        'N_p': 'proton_density',
        'T_p': 'temperature',
        'He2+_ratio': 'helium_abundance'
    }
    df = df.rename(columns=rename_map)

    # 3. Assert that the DataFrame keys are exactly as expected
    expected_columns = ['timestamp', 'proton_density', 'temperature', 'helium_abundance', 'Kp', 'Dst']
    
    # Ensure the column order matches exactly
    if list(df.columns) != expected_columns:
        # Attempt to reorder if columns are present but in wrong order
        missing_cols = set(expected_columns) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        df = df[expected_columns]

    # 4. Verify the output contains no NaNs before writing
    nan_count = df.isnull().sum().sum()
    if nan_count > 0:
        raise ValueError(f"DataFrame contains {nan_count} NaN values before writing. Interpolation may have failed.")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df.to_csv(output_path, index=False)
    logger.info(f"Synced data written to: {output_path}")