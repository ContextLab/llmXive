"""
Preprocessing module for Solar Irradiance reconstruction.

Handles gap filling for GSN data based on duration thresholds (FR-002),
detects solar cycle boundaries, and outputs the final preprocessed dataset.
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import pandas as pd
import numpy as np
from scipy import interpolate

from code.config import ensure_directories
from code.env_manager import get_data_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for gap filling logic (FR-002)
GAP_THRESHOLD_YEARS = 1.0
DAYS_IN_YEAR = 365.25
GAP_THRESHOLD_DAYS = int(GAP_THRESHOLD_YEARS * DAYS_IN_YEAR)

# Official SILSO Cycle Start Dates (approximate, used for boundary detection)
# Source: SILSO historical data
SILSO_CYCLE_STARTS = {
    1: "1755-03-01",
    2: "1766-06-01",
    3: "1775-10-01",
    4: "1784-12-01",
    5: "1798-07-01",
    6: "1810-02-01",
    7: "1823-07-01",
    8: "1837-03-01",
    9: "1843-11-01",
    10: "1855-12-01",
    11: "1867-03-01",
    12: "1878-06-01",
    13: "1890-09-01",
    14: "1902-09-01",
    15: "1913-08-01",
    16: "1923-08-01",
    17: "1933-02-01",
    18: "1944-03-01",
    19: "1957-04-01",
    20: "1968-05-01",
    21: "1976-03-01",
    22: "1986-09-01",
    23: "1996-05-01",
    24: "2008-12-01",
    25: "2019-12-01"
}

def load_raw_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads the raw GSN and TSI data downloaded by ingestion.py.
    
    Returns:
        Tuple of (gsn_df, tsi_df)
    """
    raw_dir = get_data_path("raw")
    gsn_path = raw_dir / "gsn_monthly.csv"
    tsi_path = raw_dir / "tsi_monthly.csv"

    if not gsn_path.exists():
        raise FileNotFoundError(f"Raw GSN data not found at {gsn_path}. Run ingestion first.")
    if not tsi_path.exists():
        raise FileNotFoundError(f"Raw TSI data not found at {tsi_path}. Run ingestion first.")

    logger.info(f"Loading GSN data from {gsn_path}")
    gsn_df = pd.read_csv(gsn_path)
    gsn_df['Date'] = pd.to_datetime(gsn_df['Date'])
    gsn_df = gsn_df.sort_values('Date').reset_index(drop=True)

    logger.info(f"Loading TSI data from {tsi_path}")
    tsi_df = pd.read_csv(tsi_path)
    tsi_df['Date'] = pd.to_datetime(tsi_df['Date'])
    tsi_df = tsi_df.sort_values('Date').reset_index(drop=True)

    return gsn_df, tsi_df

def detect_cycle_boundaries(dates: pd.Series) -> pd.Series:
    """
    Assigns a Solar Cycle ID to each date based on SILSO start dates.
    
    Args:
        dates: Series of datetime objects.
        
    Returns:
        Series of cycle IDs (int).
    """
    cycle_ids = []
    sorted_starts = sorted(SILSO_CYCLE_STARTS.items(), key=lambda x: x[1])
    
    for date in dates:
        cycle_id = 1
        for cid, start_str in sorted_starts:
            start_date = pd.to_datetime(start_str)
            if date >= start_date:
                cycle_id = cid
            else:
                break
        cycle_ids.append(cycle_id)
    
    return pd.Series(cycle_ids, index=dates.index)

def fill_gaps(gsn_df: pd.DataFrame) -> pd.DataFrame:
    """
    Implements FR-002 gap filling logic:
    1. Linear interpolation for gaps < 1 year.
    2. GSN=0 proxy for gaps >= 1 year.
    
    Args:
        gsn_df: DataFrame with 'Date' and 'GSN' columns.
        
    Returns:
        DataFrame with filled 'GSN' column.
    """
    df = gsn_df.copy()
    
    # Identify gaps
    # Calculate time difference in days between consecutive rows
    df['date_diff'] = df['Date'].diff().dt.days
    
    # Identify gaps > 1 year (approx 365 days)
    # Note: The first row will be NaN, treat as 0 diff for logic
    df['date_diff'] = df['date_diff'].fillna(0)
    
    # We need to find the start and end of gaps to apply logic
    # A gap is defined as a sequence of NaNs in the GSN column
    # However, the task implies we are looking at the time delta between 
    # available data points. If the delta > 365 days, the missing chunk is >= 1 year.
    
    # Strategy:
    # 1. Identify indices where data exists.
    # 2. Calculate delta between consecutive existing data points.
    # 3. If delta > 365, fill the interval between them with 0.
    # 4. If delta <= 365, linear interpolate the interval.
    
    valid_mask = ~df['GSN'].isna()
    valid_indices = df[valid_mask].index
    
    # Create a copy for filling
    filled_gsn = df['GSN'].copy()
    
    for i in range(len(valid_indices) - 1):
        idx_start = valid_indices[i]
        idx_end = valid_indices[i+1]
        
        # Get the dates
        date_start = df.loc[idx_start, 'Date']
        date_end = df.loc[idx_end, 'Date']
        
        days_gap = (date_end - date_start).days
        
        # Check if there are actually missing rows between them
        if days_gap > 1:
            # Determine fill strategy
            if days_gap >= GAP_THRESHOLD_DAYS:
                # FR-002: Gaps >= 1 year -> GSN = 0
                logger.info(f"Found gap of {days_gap} days (>= {GAP_THRESHOLD_DAYS}). Applying GSN=0 proxy.")
                mask = (df.index > idx_start) & (df.index < idx_end)
                filled_gsn.loc[mask] = 0
            else:
                # FR-002: Gaps < 1 year -> Linear Interpolation
                logger.debug(f"Found gap of {days_gap} days (< {GAP_THRESHOLD_DAYS}). Applying linear interpolation.")
                # Use pandas interpolation which handles linear by default
                # We only want to interpolate this specific segment to avoid leaking across large gaps
                # But since we are iterating segments, we can just interpolate the whole column 
                # AFTER handling the 0-fills, or handle segment by segment.
                # Simpler approach: Interpolate the whole column, then overwrite the large gaps with 0?
                # No, interpolation would fill large gaps with non-zero values.
                # Correct approach:
                # 1. Identify large gaps.
                # 2. Set those specific missing values to 0.
                # 3. Interpolate the remaining gaps (which are now < 1 year).
                pass
    
    # Refined Strategy:
    # 1. Create a mask for "large gaps" (where the time difference to the next valid point > 365).
    # 2. Set those specific missing values to 0.
    # 3. Interpolate the rest.
    
    # Step 1: Identify indices that are part of a large gap
    large_gap_mask = pd.Series(False, index=df.index)
    
    for i in range(len(valid_indices) - 1):
        idx_start = valid_indices[i]
        idx_end = valid_indices[i+1]
        date_start = df.loc[idx_start, 'Date']
        date_end = df.loc[idx_end, 'Date']
        days_gap = (date_end - date_start).days
        
        if days_gap >= GAP_THRESHOLD_DAYS:
            # Mark all indices strictly between start and end as large gap
            mask = (df.index > idx_start) & (df.index < idx_end)
            large_gap_mask.loc[mask] = True
    
    # Step 2: Apply GSN=0 for large gaps
    # Only apply where the value is currently NaN
    filled_gsn = df['GSN'].copy()
    filled_gsn.loc[large_gap_mask & filled_gsn.isna()] = 0
    
    # Step 3: Linear interpolation for remaining gaps (which are < 1 year)
    # We can safely interpolate now because the large gaps are filled with 0
    filled_gsn = filled_gsn.interpolate(method='linear')
    
    # Edge case: leading/trailing NaNs?
    # Usually we don't extrapolate. Let's fill leading/trailing with nearest valid or 0?
    # Task doesn't specify, assume data starts/ends with valid points or we leave as NaN?
    # Standard practice: forward/backward fill or leave NaN. 
    # Given "reconstruction", we might need to fill. Let's forward/backward fill if possible, else 0.
    filled_gsn = filled_gsn.ffill().bfill()
    # If still NaN (no data at all), set to 0
    filled_gsn = filled_gsn.fillna(0)
    
    df['GSN'] = filled_gsn
    df = df.drop(columns=['date_diff']) # Clean up helper column
    
    return df

def merge_datasets(gsn_df: pd.DataFrame, tsi_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merges GSN and TSI data on date.
    
    Args:
        gsn_df: Preprocessed GSN dataframe.
        tsi_df: Raw TSI dataframe.
        
    Returns:
        Merged dataframe.
    """
    # Merge on 'Date'
    merged = pd.merge(gsn_df, tsi_df[['Date', 'TSI']], on='Date', how='inner')
    logger.info(f"Merged dataset shape: {merged.shape}")
    return merged

def run_preprocessing() -> str:
    """
    Main entry point for the preprocessing pipeline.
    
    1. Loads raw data.
    2. Detects cycle boundaries.
    3. Fills GSN gaps per FR-002.
    4. Merges with TSI.
    5. Saves to data/processed/preprocessed_data.parquet.
    
    Returns:
        Path to the output file.
    """
    ensure_directories()
    processed_dir = get_data_path("processed")
    output_path = processed_dir / "preprocessed_data.parquet"
    
    logger.info("Starting preprocessing pipeline...")
    
    # Load
    gsn_df, tsi_df = load_raw_data()
    
    # Detect Cycle Boundaries
    logger.info("Detecting solar cycle boundaries...")
    gsn_df['Cycle_ID'] = detect_cycle_boundaries(gsn_df['Date'])
    
    # Fill Gaps
    logger.info("Filling GSN gaps...")
    gsn_df = fill_gaps(gsn_df)
    
    # Merge
    logger.info("Merging GSN and TSI datasets...")
    final_df = merge_datasets(gsn_df, tsi_df)
    
    # Ensure Cycle_ID is integer
    final_df['Cycle_ID'] = final_df['Cycle_ID'].astype(int)
    
    # Save
    logger.info(f"Saving preprocessed data to {output_path}...")
    final_df.to_parquet(output_path, index=False)
    
    logger.info("Preprocessing complete.")
    return str(output_path)

if __name__ == "__main__":
    run_preprocessing()