import os
import pandas as pd
import numpy as np
from datetime import timedelta
from code import logger
from code.config import ACE_VARS, NOAA_VARS, TRAIN_START, TEST_END

def load_raw_ace(filepath: str) -> pd.DataFrame:
    """Load raw ACE data from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"ACE raw data file not found: {filepath}")
    df = pd.read_csv(filepath, parse_dates=['timestamp'])
    return df

def load_raw_noaa(filepath: str) -> pd.DataFrame:
    """Load raw NOAA data from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"NOAA raw data file not found: {filepath}")
    df = pd.read_csv(filepath, parse_dates=['timestamp'])
    return df

def align_to_hourly(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """Resample data to 1-hour UTC grid."""
    if df.empty:
        logger.warning(f"Empty dataframe provided for {source_name}, returning empty.")
        return df

    df = df.set_index('timestamp')
    
    # Resample to hourly frequency
    # Using '1h' frequency ensures alignment to UTC hours
    resampled = df.resample('1h').first()
    
    logger.info(f"Resampled {source_name} to {len(resampled)} hourly records.")
    return resampled

def interpolate_gaps(df: pd.DataFrame, max_gap_hours: int = 6) -> pd.DataFrame:
    """
    Perform linear interpolation for gaps <= max_gap_hours.
    Logs interpolated intervals.
    
    Args:
        df: DataFrame with DatetimeIndex
        max_gap_hours: Maximum gap size (in hours) to interpolate
    
    Returns:
        DataFrame with gaps filled
    """
    if df.empty:
        return df

    # Identify gaps
    # Calculate time differences between consecutive rows
    time_diffs = df.index.to_series().diff()
    
    # Convert to hours to identify gap size
    gap_hours = time_diffs / pd.Timedelta(hours=1)
    
    # Identify gaps larger than threshold
    large_gaps = gap_hours > max_gap_hours
    
    # Log large gaps (warning)
    if large_gaps.any():
        large_gap_indices = df.index[large_gaps]
        for idx in large_gap_indices:
            gap_size = gap_hours[large_gaps][large_gaps.get_loc(idx)]
            logger.warning(f"Large gap detected at {idx}: {gap_size:.1f} hours (exceeds {max_gap_hours}h limit). Skipping interpolation for this segment.")
    
    # Identify gaps to interpolate (<= max_gap_hours)
    # We need to find segments where the gap is <= max_gap_hours
    # Create a mask for gaps that are valid for interpolation
    valid_gaps_mask = gap_hours <= max_gap_hours
    
    # We need to be careful: we want to interpolate between points where the gap is small
    # but NOT across large gaps.
    
    # Strategy:
    # 1. Create a copy
    # 2. Identify segments separated by large gaps
    # 3. Interpolate within each segment
    
    result = df.copy()
    
    # Find indices where gaps are too large
    large_gap_idx = large_gaps[large_gaps].index
    
    if len(large_gap_idx) == 0:
        # No large gaps, interpolate everything
        logger.info(f"Interpolating {len(result)} rows for all variables (no large gaps).")
        result = result.interpolate(method='linear', limit_direction='forward')
        return result
    
    # Split by large gaps
    # Create groups: each time we hit a large gap, we start a new group
    # Shift the large_gap_mask to mark the start of a new segment
    segment_start = large_gaps.shift(1).fillna(False)
    segment_id = segment_start.cumsum()
    
    total_interpolated = 0
    interpolated_vars = set()
    
    for seg_id in segment_id.unique():
        seg_mask = segment_id == seg_id
        seg_df = result[seg_mask]
        
        if len(seg_df) < 2:
            continue
        
        # Check if this segment has any NaNs that need interpolation
        if seg_df.isnull().any().any():
            # Interpolate this segment
            old_nulls = seg_df.isnull().sum().sum()
            seg_df_interp = seg_df.interpolate(method='linear', limit_direction='forward')
            new_nulls = seg_df_interp.isnull().sum().sum()
            
            interpolated_count = old_nulls - new_nulls
            if interpolated_count > 0:
                total_interpolated += interpolated_count
                # Track which variables were interpolated
                for col in seg_df.columns:
                    if seg_df[col].isnull().any() and not seg_df_interp[col].isnull().all():
                        interpolated_vars.add(col)
            
            result.loc[seg_mask] = seg_df_interp
    
    if total_interpolated > 0:
        logger.info(f"Interpolated {total_interpolated} values across {len(interpolated_vars)} variables: {list(interpolated_vars)}. Gaps > {max_gap_hours}h were skipped.")
    else:
        logger.info("No interpolation performed (no gaps found or all gaps were too large).")
        
    return result

def run_alignment(raw_ace_path: str, raw_noaa_path: str, output_path: str) -> str:
    """
    Main orchestration function for data alignment.
    1. Load raw ACE and NOAA data
    2. Align to hourly grid
    3. Interpolate gaps (<= 6h)
    4. Merge and save to output
    
    Args:
        raw_ace_path: Path to raw ACE CSV
        raw_noaa_path: Path to raw NOAA CSV
        output_path: Path for final synced CSV
    
    Returns:
        Path to the output file
    """
    logger.info(f"Starting alignment process. ACE: {raw_ace_path}, NOAA: {raw_noaa_path}")
    
    # Load data
    df_ace = load_raw_ace(raw_ace_path)
    df_noaa = load_raw_noaa(raw_noaa_path)
    
    # Select required columns
    # ACE
    ace_cols = ['timestamp'] + ACE_VARS
      # Check if columns exist
    missing_ace = [c for c in ace_cols if c not in df_ace.columns]
    if missing_ace:
        raise ValueError(f"Missing ACE columns: {missing_ace}")
    df_ace = df_ace[ace_cols]
    
    # NOAA
    noaa_cols = ['timestamp'] + NOAA_VARS
    missing_noaa = [c for c in noaa_cols if c not in df_noaa.columns]
    if missing_noaa:
        raise ValueError(f"Missing NOAA columns: {missing_noaa}")
    df_noaa = df_noaa[noaa_cols]
    
    # Align to hourly
    df_ace_hourly = align_to_hourly(df_ace, "ACE")
    df_noaa_hourly = align_to_hourly(df_noaa, "NOAA")
    
    # Interpolate gaps
    df_ace_interp = interpolate_gaps(df_ace_hourly)
    df_noaa_interp = interpolate_gaps(df_noaa_hourly)
    
    # Merge on timestamp
    # Reset index to merge on 'timestamp' column
    df_ace_reset = df_ace_interp.reset_index()
    df_noaa_reset = df_noaa_interp.reset_index()
    
    # Merge
    merged = pd.merge(df_ace_reset, df_noaa_reset, on='timestamp', how='outer')
    
    # Final interpolation for any remaining gaps after merge
    merged = merged.set_index('timestamp')
    merged = interpolate_gaps(merged)
    merged = merged.reset_index()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save
    merged.to_csv(output_path, index=False)
    logger.info(f"Alignment complete. Output saved to {output_path} ({len(merged)} rows).")
    
    return output_path