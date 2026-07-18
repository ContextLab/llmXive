import os
import pandas as pd
import numpy as np
from datetime import timedelta
from code import logger
from code.config import ACE_VARS, NOAA_VARS, TRAIN_START, TEST_END

# Constants for gap handling
MAX_GAP_HOURS = 6

def load_raw_ace(file_path: str) -> pd.DataFrame:
    """
    Load raw ACE data from a CSV file.
    
    Args:
        file_path: Path to the ACE raw CSV file.
        
    Returns:
        DataFrame with ACE data.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"ACE raw data file not found: {file_path}")
    
    df = pd.read_csv(file_path, parse_dates=['timestamp'])
    logger.info(f"Loaded ACE data from {file_path}: {len(df)} rows")
    return df

def load_raw_noaa(file_path: str) -> pd.DataFrame:
    """
    Load raw NOAA data from a CSV file.
    
    Args:
        file_path: Path to the NOAA raw CSV file.
        
    Returns:
        DataFrame with NOAA data.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"NOAA raw data file not found: {file_path}")
    
    df = pd.read_csv(file_path, parse_dates=['timestamp'])
    logger.info(f"Loaded NOAA data from {file_path}: {len(df)} rows")
    return df

def align_to_hourly(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """
    Resample data to 1-hour UTC grid.
    
    Args:
        df: Input DataFrame with a 'timestamp' column.
        source_name: Name of the data source for logging.
        
    Returns:
        DataFrame resampled to hourly frequency.
    """
    if df.empty:
        logger.warning(f"Empty DataFrame provided for {source_name} alignment")
        return df
    
    # Ensure timestamp is datetime and set as index
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')
    
    # Resample to hourly frequency, taking the mean for numeric columns
    # Use '1h' to ensure UTC alignment
    hourly_df = df.resample('1h').mean()
    
    logger.info(f"Resampled {source_name} data to hourly: {len(hourly_df)} rows")
    return hourly_df

def interpolate_gaps(df: pd.DataFrame, max_gap_hours: int = MAX_GAP_HOURS) -> pd.DataFrame:
    """
    Perform linear interpolation for gaps <= max_gap_hours.
    
    This function detects gaps in the time series and fills them using linear
    interpolation if the gap size is within the specified threshold.
    
    Args:
        df: Input DataFrame with a datetime index and numeric columns.
        max_gap_hours: Maximum gap size in hours to interpolate.
        
    Returns:
        DataFrame with interpolated gaps and a log of interpolated intervals.
    """
    if df.empty:
        logger.warning("Empty DataFrame provided for interpolation")
        return df
    
    # Ensure the index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # Identify gaps by checking for NaN values
    # Create a boolean mask for NaN values
    nan_mask = df.isna()
    
    # If no NaNs, return the original dataframe
    if not nan_mask.any().any():
        logger.info("No gaps detected in the data")
        return df
    
    # Log the start of interpolation process
    logger.info(f"Starting interpolation for gaps <= {max_gap_hours} hours")
    
    # Create a copy to avoid modifying the original
    df_interp = df.copy()
    
    # For each column, identify and interpolate gaps
    interpolated_intervals = []
    
    for col in df_interp.columns:
        if df_interp[col].isna().all():
            logger.warning(f"Column {col} is entirely NaN, skipping interpolation")
            continue
        
        # Get the series for this column
        series = df_interp[col]
        
        # Identify groups of consecutive NaNs
        # Create a boolean series indicating NaN
        is_nan = series.isna()
        
        if not is_nan.any():
            continue
        
        # Create groups of consecutive NaNs
        # A new group starts when is_nan changes from False to True
        group_id = (~is_nan).cumsum()
        
        # Get the groups that are NaN
        nan_groups = group_id[is_nan]
        
        if nan_groups.empty:
            continue
        
        # Process each group of consecutive NaNs
        for group_val in nan_groups.unique():
            group_mask = (group_id == group_val) & is_nan
            start_idx = group_mask.idxmax()
            end_idx = group_mask[group_mask].index[-1]
            
            # Calculate the gap duration
            # Find the previous non-NaN value
            prev_non_nan_idx = series[:start_idx].last_valid_index()
            next_non_nan_idx = series[end_idx:].first_valid_index()
            
            if prev_non_nan_idx is None or next_non_nan_idx is None:
                # Cannot interpolate at the edges
                logger.warning(f"Cannot interpolate gap in {col} from {start_idx} to {end_idx}: missing boundary values")
                continue
            
            gap_duration = next_non_nan_idx - prev_non_nan_idx
            gap_hours = gap_duration.total_seconds() / 3600
            
            if gap_hours <= max_gap_hours:
                # Perform interpolation
                # Use linear interpolation between the boundary values
                df_interp.loc[prev_non_nan_idx:next_non_nan_idx, col] = series[prev_non_nan_idx:next_non_nan_idx].interpolate(method='linear')
                
                interpolated_intervals.append({
                    'column': col,
                    'start': prev_non_nan_idx,
                    'end': next_non_nan_idx,
                    'gap_hours': gap_hours,
                    'method': 'linear'
                })
                
                logger.info(f"Interpolated {col} gap: {prev_non_nan_idx} to {next_non_nan_idx} ({gap_hours:.2f} hours)")
            else:
                logger.warning(f"Gap in {col} from {prev_non_nan_idx} to {next_non_nan_idx} ({gap_hours:.2f} hours) exceeds threshold ({max_gap_hours}h), skipping interpolation")
    
    # Log summary of interpolated intervals
    if interpolated_intervals:
        logger.info(f"Interpolated {len(interpolated_intervals)} gaps in total")
        for interval in interpolated_intervals:
            logger.debug(f"  - {interval['column']}: {interval['start']} to {interval['end']} ({interval['gap_hours']:.2f}h, {interval['method']})")
    else:
        logger.info("No gaps were interpolated (either no gaps or all gaps exceeded threshold)")
    
    # Check if there are any remaining NaNs
    if df_interp.isna().any().any():
        remaining_nans = df_interp.isna().sum().sum()
        logger.warning(f"Remaining NaNs after interpolation: {remaining_nans}")
    else:
        logger.info("All gaps successfully interpolated")
    
    return df_interp

def run_alignment(ace_file: str, noaa_file: str, output_file: str) -> str:
    """
    Run the full alignment pipeline: load, resample, and interpolate.
    
    Args:
        ace_file: Path to ACE raw data file.
        noaa_file: Path to NOAA raw data file.
        output_file: Path to write the synchronized output.
        
    Returns:
        Path to the output file.
    """
    logger.info(f"Starting alignment pipeline: ACE={ace_file}, NOAA={noaa_file}")
    
    # Load raw data
    ace_df = load_raw_ace(ace_file)
    noaa_df = load_raw_noaa(noaa_file)
    
    # Validate that required columns exist
    from code.data.validate import validate_columns
    validate_columns(ace_df, ACE_VARS)
    validate_columns(noaa_df, NOAA_VARS)
    
    # Align to hourly
    ace_hourly = align_to_hourly(ace_df, "ACE")
    noaa_hourly = align_to_hourly(noaa_df, "NOAA")
    
    # Merge the datasets on timestamp
    # Reset index to make timestamp a column for merging
    ace_hourly = ace_hourly.reset_index()
    noaa_hourly = noaa_hourly.reset_index()
    
    # Merge on timestamp
    merged_df = pd.merge(ace_hourly, noaa_hourly, on='timestamp', how='outer')
    merged_df = merged_df.set_index('timestamp')
    
    logger.info(f"Merged dataset: {len(merged_df)} rows, {len(merged_df.columns)} columns")
    
    # Interpolate gaps
    interpolated_df = interpolate_gaps(merged_df)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Write to CSV
    interpolated_df.to_csv(output_file)
    logger.info(f"Alignment complete. Output written to {output_file}")
    
    return output_file

# Main execution for testing
if __name__ == "__main__":
    # Example usage
    ace_path = "data/raw/ace_raw.csv"
    noaa_path = "data/raw/noaa_raw.csv"
    output_path = "data/processed/synced.csv"
    
    if os.path.exists(ace_path) and os.path.exists(noaa_path):
        run_alignment(ace_path, noaa_path, output_path)
    else:
        logger.info("Raw data files not found. Skipping alignment.")