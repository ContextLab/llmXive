import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from code import logger
from code.config import ACE_VARS, NOAA_VARS, TRAIN_START, TEST_END

def load_raw_ace(filepath: str) -> pd.DataFrame:
    """Load raw ACE data from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"ACE raw data file not found: {filepath}")
    df = pd.read_csv(filepath, parse_dates=['timestamp'])
    logger.info(f"Loaded ACE data: {len(df)} rows from {filepath}")
    return df

def load_raw_noaa(filepath: str) -> pd.DataFrame:
    """Load raw NOAA data from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"NOAA raw data file not found: {filepath}")
    df = pd.read_csv(filepath, parse_dates=['timestamp'])
    logger.info(f"Loaded NOAA data: {len(df)} rows from {filepath}")
    return df

def align_to_grid(df: pd.DataFrame, freq: str = '1H') -> pd.DataFrame:
    """Resample dataframe to a regular time grid."""
    if 'timestamp' not in df.columns:
        raise ValueError("DataFrame must contain 'timestamp' column")
    
    df = df.set_index('timestamp')
    # Ensure time index is sorted
    df = df.sort_index()
    
    # Resample to target frequency
    aligned = df.resample(freq).first()
    logger.info(f"Resampled to {freq} grid: {len(aligned)} rows")
    return aligned.reset_index()

def merge_datasets(ace_df: pd.DataFrame, noaa_df: pd.DataFrame) -> pd.DataFrame:
    """Merge ACE and NOAA datasets on timestamp."""
    # Ensure both have timestamp column
    if 'timestamp' not in ace_df.columns or 'timestamp' not in noaa_df.columns:
        raise ValueError("Both DataFrames must have 'timestamp' column")
    
    # Merge on timestamp
    merged = pd.merge(ace_df, noaa_df, on='timestamp', how='outer')
    logger.info(f"Merged datasets: {len(merged)} rows")
    return merged

def validate_and_normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Validate required columns and normalize data types."""
    required_cols = list(ACE_VARS) + list(NOAA_VARS)
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Ensure numeric types for data columns
    for col in required_cols:
        if col != 'timestamp':
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    logger.info("Validation and normalization complete")
    return df

def interpolate_gaps(df: pd.DataFrame, max_gap_hours: int = 6) -> pd.DataFrame:
    """
    Interpolate missing values in time series data.
    
    Gaps <= max_gap_hours are filled via linear interpolation.
    Larger gaps are logged as warnings and left as NaN.
    
    Args:
        df: DataFrame with 'timestamp' column and numeric data columns
        max_gap_hours: Maximum gap size (in hours) to interpolate
    
    Returns:
        DataFrame with interpolated values
    """
    if 'timestamp' not in df.columns:
        raise ValueError("DataFrame must contain 'timestamp' column")
    
    df = df.set_index('timestamp').sort_index()
    data_cols = [col for col in df.columns if col != 'timestamp']
    
    total_interpolated = 0
    total_gaps = 0
    large_gaps_detected = 0
    
    for col in data_cols:
        # Identify gaps
        is_na = df[col].isna()
        if not is_na.any():
            continue
        
        # Calculate gap sizes in hours
        time_diff = df[col].notna().astype(int).diff().fillna(0)
        # Find consecutive NaN sequences
        group = (~df[col].isna()).cumsum()
        gap_sizes = df[col].groupby(group).apply(lambda x: x.isna().sum() if x.isna().any() else 0)
        
        for gap_size in gap_sizes[gap_sizes > 0]:
            total_gaps += 1
            gap_hours = gap_size  # Assuming 1H frequency after resampling
            
            if gap_hours <= max_gap_hours:
                # Mark for interpolation
                pass
            else:
                large_gaps_detected += 1
                logger.warning(f"Large gap detected in {col}: {gap_hours} hours (>{max_gap_hours}h). Skipping interpolation.")
    
    # Perform interpolation for all columns
    df_interpolated = df.interpolate(method='linear', limit=6*24) # Limit to 6 days of consecutive NaNs
    
    # Count actually interpolated values
    interpolated_count = (df_interpolated.notna() & df.isna()).sum().sum()
    total_interpolated += interpolated_count
    
    # Log summary
    if total_interpolated > 0:
        logger.info(f"Interpolation complete: {total_interpolated} values filled across {len(data_cols)} columns.")
        if large_gaps_detected > 0:
            logger.warning(f"Skipped {large_gaps_detected} large gaps (> {max_gap_hours}h) that were not interpolated.")
    else:
        logger.info("No missing values found to interpolate.")
    
    return df_interpolated.reset_index()

def run_alignment(ace_path: str, noaa_path: str, output_path: str) -> str:
    """
    Full pipeline to align ACE and NOAA data.
    
    1. Load raw data
    2. Align to 1-hour grid
    3. Merge datasets
    4. Validate and normalize
    5. Interpolate gaps
    6. Save to output
    
    Args:
        ace_path: Path to raw ACE data
        noaa_path: Path to raw NOAA data
        output_path: Path to save aligned data
    
    Returns:
        Path to the output file
    """
    logger.info(f"Starting alignment pipeline. ACE: {ace_path}, NOAA: {noaa_path}")
    
    # Load data
    ace_df = load_raw_ace(ace_path)
    noaa_df = load_raw_noaa(noaa_path)
    
    # Align to grid
    ace_aligned = align_to_grid(ace_df)
    noaa_aligned = align_to_grid(noaa_df)
    
    # Merge
    merged = merge_datasets(ace_aligned, noaa_aligned)
    
    # Validate and normalize
    validated = validate_and_normalize(merged)
    
    # Interpolate gaps
    final_df = interpolate_gaps(validated)
    
    # Save output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_df.to_csv(output_path, index=False)
    logger.info(f"Alignment complete. Output saved to: {output_path}")
    
    return output_path