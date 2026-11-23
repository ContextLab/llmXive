import os
import pandas as pd
import numpy as np
from datetime import timedelta
from code import logger
from code.config import ACE_VARS, NOAA_VARS, TRAIN_START, TEST_END, STREAMING_CHUNK_SIZE

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

def run_alignment_chunked(ace_filepath: str, noaa_filepath: str, output_path: str, chunk_size: int = None) -> None:
    """
    Runs the alignment pipeline in temporal chunks to handle large files (e.g. > 1 year).
    
    This function processes the raw data in chunks (default: by year) to avoid memory spikes
    when aligning multi-decadal datasets. It performs resampling and interpolation per chunk,
    then concatenates the results before writing the final output.
    
    Args:
        ace_filepath: Path to raw ACE CSV.
        noaa_filepath: Path to raw NOAA CSV.
        output_path: Path to write the final synced CSV.
        chunk_size: Number of rows per chunk. If None, defaults to STREAMING_CHUNK_SIZE from config.
    """
    if chunk_size is None:
        chunk_size = STREAMING_CHUNK_SIZE
    
    logger.info(f"Starting chunked alignment with chunk_size={chunk_size}")
    
    # Load raw data
    ace_df = load_raw_ace(ace_filepath)
    noaa_df = load_raw_noaa(noaa_filepath)
    
    # Rename ACE columns
    ace_df = ace_df.rename(columns={
        'N_p': 'proton_density',
        'T_p': 'temperature',
        'He2+_ratio': 'helium_abundance'
    })
    
    # Ensure timestamp is datetime
    ace_df['timestamp'] = pd.to_datetime(ace_df['timestamp'])
    noaa_df['timestamp'] = pd.to_datetime(noaa_df['timestamp'])
    
    # Determine date range for chunking
    min_date = min(ace_df['timestamp'].min(), noaa_df['timestamp'].min())
    max_date = max(ace_df['timestamp'].max(), noaa_df['timestamp'].max())
    
    # Create date boundaries for yearly chunks
    current_date = min_date
    chunks = []
    
    while current_date <= max_date:
        next_date = current_date.replace(year=current_date.year + 1)
        if next_date > max_date:
            next_date = max_date + timedelta(days=1)
        
        logger.info(f"Processing chunk: {current_date} to {next_date}")
        
        # Filter data for this chunk
        ace_chunk = ace_df[(ace_df['timestamp'] >= current_date) & (ace_df['timestamp'] < next_date)].copy()
        noaa_chunk = noaa_df[(noaa_df['timestamp'] >= current_date) & (noaa_df['timestamp'] < next_date)].copy()
        
        if ace_chunk.empty or noaa_chunk.empty:
            logger.warning(f"No data found for chunk {current_date} to {next_date}, skipping.")
            current_date = next_date
            continue
        
        # Merge chunk
        merged_chunk = pd.merge(ace_chunk, noaa_chunk, on='timestamp', how='outer')
        
        # Resample to hourly
        merged_chunk = align_to_hourly(merged_chunk)
        
        # Interpolate gaps
        merged_chunk = interpolate_gaps(merged_chunk)
        
        chunks.append(merged_chunk)
        
        current_date = next_date
    
    if not chunks:
        raise ValueError("No data chunks were processed. Check input data range.")
    
    # Concatenate all chunks
    final_df = pd.concat(chunks, axis=0)
    
    # Reset index to make timestamp a column
    if isinstance(final_df.index, pd.DatetimeIndex):
        final_df = final_df.reset_index()
    
    # Ensure correct column order and names
    expected_columns = ['timestamp', 'proton_density', 'temperature', 'helium_abundance', 'Kp', 'Dst']
    final_df = final_df[expected_columns]
    
    # Final NaN check
    if final_df.isnull().sum().sum() > 0:
        raise ValueError(f"Final dataframe contains NaNs after chunked processing.")
    
    # Write output
    write_synced_csv(final_df, output_path)

def read_synced_in_chunks(filepath: str, chunksize: int = 100000):
    """
    Reads a synced CSV file in chunks for memory-efficient processing.
    
    Args:
        filepath: Path to the CSV file.
        chunksize: Number of rows per chunk.
        
    Yields:
        pandas.DataFrame chunks.
    """
    for chunk in pd.read_csv(filepath, chunksize=chunksize):
        yield chunk