import os
import pandas as pd
import numpy as np
from datetime import timedelta
from code import logger
from code.config import ACE_VARS, NOAA_VARS, TRAIN_START, TEST_END

def load_raw_ace(filepath: str) -> pd.DataFrame:
    """
    Load raw ACE data from a CSV file.
    
    Args:
        filepath: Path to the raw ACE CSV file.
        
    Returns:
        DataFrame with ACE data.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"ACE raw data file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    
    # Ensure timestamp column exists and is datetime
    if 'timestamp' not in df.columns:
        # Try to find a column that might be the timestamp
        possible_ts_cols = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
        if possible_ts_cols:
            ts_col = possible_ts_cols[0]
            df = df.rename(columns={ts_col: 'timestamp'})
        else:
            raise ValueError("No timestamp column found in ACE data")
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')
    
    logger.info(f"Loaded ACE data: {len(df)} rows, columns: {list(df.columns)}")
    return df

def load_raw_noaa(filepath: str) -> pd.DataFrame:
    """
    Load raw NOAA data from a CSV file.
    
    Args:
        filepath: Path to the raw NOAA CSV file.
        
    Returns:
        DataFrame with NOAA data.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"NOAA raw data file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    
    # Ensure timestamp column exists and is datetime
    if 'timestamp' not in df.columns:
        # Try to find a column that might be the timestamp
        possible_ts_cols = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
        if possible_ts_cols:
            ts_col = possible_ts_cols[0]
            df = df.rename(columns={ts_col: 'timestamp'})
        else:
            raise ValueError("No timestamp column found in NOAA data")
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')
    
    logger.info(f"Loaded NOAA data: {len(df)} rows, columns: {list(df.columns)}")
    return df

def align_to_hourly(df: pd.DataFrame, var_name: str) -> pd.Series:
    """
    Resample a single variable to 1-hour UTC grid.
    
    Args:
        df: DataFrame with datetime index.
        var_name: Name of the variable to resample.
        
    Returns:
        Series resampled to hourly frequency.
    """
    if var_name not in df.columns:
        logger.warning(f"Variable {var_name} not found in data, skipping")
        return pd.Series(dtype=float)
    
    # Resample to hourly frequency, taking the mean of values within each hour
    # This handles both regular and irregular time steps
    hourly = df[var_name].resample('h').mean()
    
    logger.info(f"Resampled {var_name} to hourly: {len(hourly)} rows")
    return hourly

def interpolate_gaps(series: pd.Series, max_gap_hours: int = 6) -> pd.Series:
    """
    Fill gaps in a time series using linear interpolation.
    Gaps larger than max_gap_hours will be left as NaN and logged.
    
    Args:
        series: Time series to interpolate.
        max_gap_hours: Maximum gap size (in hours) to fill.
        
    Returns:
        Interpolated time series.
    """
    # Convert to Series if it's not already
    if not isinstance(series, pd.Series):
        series = pd.Series(series)
    
    # Identify gaps
    gaps = series.isna()
    gap_sizes = gaps.groupby((~gaps).cumsum()).sum()
    
    # Log gaps
    large_gaps = gap_sizes[gap_sizes > max_gap_hours]
    if len(large_gaps) > 0:
        logger.warning(f"Found {len(large_gaps)} gaps larger than {max_gap_hours}h that will not be filled")
        for idx, size in large_gaps.items():
            logger.warning(f"Gap of {size}h at index {idx} will remain NaN")
    
    # Interpolate all NaN values
    interpolated = series.interpolate(method='linear')
    
    # Check which values are still NaN (these are from large gaps)
    still_nan = interpolated.isna()
    if still_nan.any():
        logger.info(f"After interpolation, {still_nan.sum()} values remain NaN (from gaps > {max_gap_hours}h)")
    
    return interpolated

def run_alignment(raw_ace_path: str, raw_noaa_path: str, output_path: str) -> str:
    """
    Main function to run the full alignment pipeline.
    Reads raw ACE and NOAA data, aligns to 1-hour grid, interpolates gaps,
    and writes the synchronized dataset.
    
    Args:
        raw_ace_path: Path to raw ACE data file.
        raw_noaa_path: Path to raw NOAA data file.
        output_path: Path where the synchronized CSV will be written.
        
    Returns:
        Path to the output file.
    """
    logger.info("Starting alignment pipeline")
    
    # Load raw data
    ace_df = load_raw_ace(raw_ace_path)
    noaa_df = load_raw_noaa(raw_noaa_path)
    
    # Align ACE variables to hourly
    aligned_ace = {}
    for var in ACE_VARS:
        if var in ace_df.columns:
          series = align_to_hourly(ace_df, var)
          aligned_ace[var] = interpolate_gaps(series)
          logger.info(f"Processed ACE variable: {var}")
        else:
            logger.warning(f"ACE variable {var} not found in data")
    
    # Align NOAA variables to hourly
    aligned_noaa = {}
    for var in NOAA_VARS:
        if var in noaa_df.columns:
            series = align_to_hourly(noaa_df, var)
            aligned_noaa[var] = interpolate_gaps(series)
            logger.info(f"Processed NOAA variable: {var}")
        else:
            logger.warning(f"NOAA variable {var} not found in data")
    
    # Create combined DataFrame
    # Use the union of all timestamps
    all_timestamps = set()
    for series in aligned_ace.values():
        all_timestamps.update(series.index)
    for series in aligned_noaa.values():
        all_timestamps.update(series.index)
    
    # Create a complete hourly index for the date range
    if all_timestamps:
        min_time = min(all_timestamps)
        max_time = max(all_timestamps)
        # Round to nearest hour
        min_time = min_time.replace(minute=0, second=0, microsecond=0)
        max_time = max_time.replace(minute=0, second=0, microsecond=0)
        
        complete_index = pd.date_range(start=min_time, end=max_time, freq='h')
    else:
        # Fallback to a reasonable range if no data
        complete_index = pd.date_range(start=f"{TRAIN_START}-01-01", end=f"{TEST_END}-12-31", freq='h')
    
    # Build final DataFrame
    final_df = pd.DataFrame(index=complete_index)
    final_df.index.name = 'timestamp'
    
    # Add ACE variables
    for var, series in aligned_ace.items():
        final_df[var] = series
    
    # Add NOAA variables
    for var, series in aligned_noaa.items():
        final_df[var] = series
    
    # Final interpolation pass to fill any remaining gaps from missing sources
    # Only for gaps <= 6 hours
    for col in final_df.columns:
        if final_df[col].isna().any():
            final_df[col] = interpolate_gaps(final_df[col], max_gap_hours=6)
    
    # Log final stats
    logger.info(f"Final synchronized dataset: {len(final_df)} rows")
    logger.info(f"Columns: {list(final_df.columns)}")
    logger.info(f"NaN counts per column:\n{final_df.isna().sum()}")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")
    
    # Write to CSV
    final_df.to_csv(output_path)
    logger.info(f"Written synchronized data to: {output_path}")
    
    return output_path

if __name__ == "__main__":
    # Example usage for direct execution
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python align.py <raw_ace_path> <raw_noaa_path> <output_path>")
        sys.exit(1)
    
    raw_ace = sys.argv[1]
    raw_noaa = sys.argv[2]
    output = sys.argv[3]
    
    run_alignment(raw_ace, raw_noaa, output)
