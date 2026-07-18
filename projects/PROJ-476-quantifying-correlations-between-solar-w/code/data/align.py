import os
import pandas as pd
import numpy as np
from datetime import timedelta
from code import logger
from code.config import ACE_VARS, NOAA_VARS, TRAIN_START, TEST_END

def load_raw_ace(file_path: str) -> pd.DataFrame:
    """
    Load raw ACE data from a CSV file.
    
    Args:
        file_path: Path to the raw ACE CSV file.
        
    Returns:
        DataFrame with ACE data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or has no valid data.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"ACE raw data file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    
    if df.empty:
        raise ValueError(f"ACE raw data file is empty: {file_path}")
    
    # Ensure timestamp column is datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    else:
        raise ValueError("ACE data must contain a 'timestamp' column")
        
    return df

def load_raw_noaa(file_path: str) -> pd.DataFrame:
    """
    Load raw NOAA data from a CSV file.
    
    Args:
        file_path: Path to the raw NOAA CSV file.
        
    Returns:
        DataFrame with NOAA data.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or has no valid data.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"NOAA raw data file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    
    if df.empty:
        raise ValueError(f"NOAA raw data file is empty: {file_path}")
    
    # Ensure timestamp column is datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    else:
        raise ValueError("NOAA data must contain a 'timestamp' column")
        
    return df

def align_to_hourly(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """
    Resample data to 1-hour UTC grid.
    
    Args:
        df: DataFrame with a 'timestamp' column.
        source_name: Name of the data source ('ACE' or 'NOAA') for logging.
        
    Returns:
        DataFrame resampled to hourly intervals.
    """
    if df.empty:
        logger.warning(f"{source_name} data is empty, returning empty aligned DataFrame")
        return df
    
    # Set timestamp as index
    df = df.set_index('timestamp')
    
    # Determine frequency based on data density
    # ACE typically provides 1-hour or 1-minute data, NOAA Kp is 3-hourly
    # We'll resample to 1-hour for both to align them
    
    # Identify numeric columns to resample
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        logger.warning(f"No numeric columns found in {source_name} data")
        return df.reset_index()
    
    # Resample to 1-hour frequency, taking the mean of values within each hour
    # This handles both higher frequency data (averaging) and lower frequency (forward fill then average)
    resampled = df[numeric_cols].resample('h').mean()
    
    # Log the resampling operation
    original_count = len(df)
    resampled_count = len(resampled)
    logger.info(f"{source_name} data resampled: {original_count} -> {resampled_count} hourly records")
    
    # Reset index to make timestamp a column again
    resampled = resampled.reset_index()
    
    return resampled

def interpolate_gaps(df: pd.DataFrame, max_gap_hours: int = 6) -> pd.DataFrame:
    """
    Fill gaps in time series data using linear interpolation.
    Gaps larger than max_gap_hours are left as NaN and logged.
    
    Args:
        df: DataFrame with a 'timestamp' column and numeric data columns.
        max_gap_hours: Maximum gap size (in hours) to interpolate.
        
    Returns:
        DataFrame with interpolated gaps.
    """
    if df.empty:
        logger.warning("Empty DataFrame provided for interpolation")
        return df
    
    # Set timestamp as index for resampling operations
    df = df.set_index('timestamp')
    
    # Identify numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        logger.warning("No numeric columns found for interpolation")
        return df.reset_index()
    
    # Count NaNs before interpolation
    nan_count_before = df[numeric_cols].isna().sum().sum()
    logger.info(f"Total NaN values before interpolation: {nan_count_before}")
    
    # Interpolate all numeric columns using linear method
    # This will fill all NaNs, but we'll handle large gaps separately
    interpolated = df[numeric_cols].interpolate(method='linear', limit_direction='both')
    
    # Check for gaps that might be too large
    # We'll check the time differences between non-NaN values
    for col in numeric_cols:
        original_series = df[col]
        interp_series = interpolated[col]
        
        # Find where we still have NaNs after interpolation
        still_nan = original_series.isna() & interp_series.isna()
        
        if still_nan.any():
            # Check the time gaps around these NaNs
            nan_indices = still_nan[still_nan].index
            logger.warning(f"Found {still_nan.sum()} values in column '{col}' that could not be interpolated (likely gaps > {max_gap_hours}h)")
            
            # Log specific large gaps
            for idx in nan_indices[:5]:  # Log first 5 as examples
                logger.warning(f"  Large gap detected at {idx} in column '{col}'")
    
    # Combine interpolated data with non-numeric columns
    result = df.copy()
    result[numeric_cols] = interpolated
    
    # Count NaNs after interpolation
    nan_count_after = result[numeric_cols].isna().sum().sum()
    logger.info(f"Total NaN values after interpolation: {nan_count_after}")
    logger.info(f"Interpolated {nan_count_before - nan_count_after} values")
    
    # Reset index
    result = result.reset_index()
    
    return result

def run_alignment(ace_file: str, noaa_file: str, output_file: str) -> pd.DataFrame:
    """
    Main function to align ACE and NOAA data to 1-hour UTC grid.
    
    This function:
    1. Loads raw ACE and NOAA data
    2. Resamples both to 1-hour intervals
    3. Merges the datasets on timestamp
    4. Interpolates small gaps (<= 6 hours)
    5. Writes the result to the specified output file
    
    Args:
        ace_file: Path to raw ACE data CSV.
        noaa_file: Path to raw NOAA data CSV.
        output_file: Path where the aligned CSV will be written.
        
    Returns:
        DataFrame containing the aligned and synchronized data.
        
    Raises:
        FileNotFoundError: If input files don't exist.
        ValueError: If data validation fails.
    """
    logger.info("Starting alignment process...")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created output directory: {output_dir}")
    
    # Load raw data
    logger.info(f"Loading ACE data from {ace_file}")
    ace_df = load_raw_ace(ace_file)
    logger.info(f"Loaded {len(ace_df)} ACE records")
    
    logger.info(f"Loading NOAA data from {noaa_file}")
    noaa_df = load_raw_noaa(noaa_file)
    logger.info(f"Loaded {len(noaa_df)} NOAA records")
    
    # Align to hourly
    logger.info("Resampling ACE data to hourly")
    ace_hourly = align_to_hourly(ace_df, "ACE")
    
    logger.info("Resampling NOAA data to hourly")
    noaa_hourly = align_to_hourly(noaa_df, "NOAA")
    
    # Merge datasets on timestamp
    logger.info("Merging ACE and NOAA data on timestamp")
    merged_df = pd.merge(
        ace_hourly,
        noaa_hourly,
        on='timestamp',
        how='outer',
        suffixes=('_ace', '_noaa')
    )
    
    logger.info(f"Merged dataset has {len(merged_df)} records")
    
    # Interpolate gaps
    logger.info("Interpolating gaps (max 6 hours)")
    aligned_df = interpolate_gaps(merged_df)
    
    # Final check for remaining NaNs
    nan_count = aligned_df.select_dtypes(include=[np.number]).isna().sum().sum()
    if nan_count > 0:
        logger.warning(f"Final dataset still contains {nan_count} NaN values (gaps > 6h)")
    else:
        logger.info("Final dataset contains no NaN values")
    
    # Write to output file
    logger.info(f"Writing aligned data to {output_file}")
    aligned_df.to_csv(output_file, index=False)
    logger.info(f"Successfully wrote {len(aligned_df)} records to {output_file}")
    
    return aligned_df

if __name__ == "__main__":
    # Default paths relative to project root
    ace_path = "data/raw/ace_raw.csv"
    noaa_path = "data/raw/noaa_raw.csv"
    output_path = "data/processed/synced.csv"
    
    # Run the alignment pipeline
    result_df = run_alignment(ace_path, noaa_path, output_path)
    logger.info("Alignment pipeline completed successfully")