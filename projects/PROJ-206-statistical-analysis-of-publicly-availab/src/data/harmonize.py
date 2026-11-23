import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

import pandas as pd
import numpy as np

from src.utils.config import get_data_root, get_state_root, resolve_path
from src.utils.logging import get_logger
from src.utils.state_manager import compute_file_hash, update_state_artifact

logger = get_logger(__name__)

def parse_dates(df: pd.DataFrame, date_col: str = 'date') -> pd.DataFrame:
    """
    Parse date column to datetime and ensure consistency.
    Handles multiple common formats found in poll data.
    """
    logger.info(f"Parsing dates in column '{date_col}'")
    
    # Try common formats
    formats = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%m-%d-%Y',
        '%Y/%m/%d',
        '%d-%m-%Y',
        '%d/%m/%Y'
    ]
    
    parsed = False
    for fmt in formats:
        try:
            df[date_col] = pd.to_datetime(df[date_col], format=fmt)
            parsed = True
            break
        except (ValueError, TypeError):
            continue
    
    if not parsed:
        # Fallback to pandas infer
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        if df[date_col].isna().any():
            logger.warning(f"Some dates could not be parsed: {df[date_col].isna().sum()} rows")
    
    return df

def bin_to_weekly(df: pd.DataFrame, date_col: str = 'date') -> pd.DataFrame:
    """
    Bin data into weekly intervals based on the date column.
    Adds a 'week_start' column representing the Monday of each week.
    """
    logger.info("Binning data into weekly intervals")
    
    # Ensure date column is datetime
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df = parse_dates(df, date_col)
    
    # Calculate week start (Monday)
    df['week_start'] = df[date_col] - pd.to_timedelta(df[date_col].dt.dayofweek, unit='D')
    
    return df

def check_data_sufficiency(df: pd.DataFrame, election_date: datetime, days_window: int = 30, min_polls: int = 5, min_cycles: int = 3) -> Tuple[bool, str]:
    """
    Check if there are enough polls in the specified window before the election.
    
    Args:
        df: DataFrame with poll data
        election_date: The election date
        days_window: Number of days before election to check
        min_polls: Minimum number of polls required
        min_cycles: Minimum number of distinct election cycles required
    
    Returns:
        Tuple of (is_sufficient, message)
    """
    logger.info(f"Checking data sufficiency: min {min_polls} polls in {days_window} days, min {min_cycles} cycles")
    
    # Filter for the window before election
    window_start = election_date - timedelta(days=days_window)
    recent_polls = df[(df['date'] >= window_start) & (df['date'] <= election_date)]
    
    poll_count = len(recent_polls)
    
    # Check distinct cycles (assuming 'cycle' or 'election_year' column exists)
    cycle_col = 'cycle' if 'cycle' in df.columns else ('election_year' if 'election_year' in df.columns else None)
    
    if cycle_col:
        distinct_cycles = recent_polls[cycle_col].nunique()
    else:
        # Fallback: use unique pollster combinations as proxy for cycles
        distinct_cycles = recent_polls['pollster'].nunique()
    
    is_sufficient = poll_count >= min_polls and distinct_cycles >= min_cycles
    
    if not is_sufficient:
        msg = (f"Data insufficiency detected: {poll_count} polls in last {days_window} days "
               f"(required: {min_polls}), {distinct_cycles} distinct cycles "
               f"(required: {min_cycles})")
        logger.warning(msg)
        return False, msg
    
    logger.info(f"Data sufficiency check passed: {poll_count} polls, {distinct_cycles} cycles")
    return True, "Data sufficiency check passed"

def check_global_poll_count(df: pd.DataFrame, min_total_polls: int = 500) -> Tuple[bool, str]:
    """
    FR-010: Check if the total count of polls across all ingested election cycles meets the minimum.
    
    Args:
        df: DataFrame with all poll data
        min_total_polls: Minimum total number of polls required (default 500)
    
    Returns:
        Tuple of (is_sufficient, message)
    
    Raises:
        ValueError: If total poll count is below the threshold
    """
    total_polls = len(df)
    
    if total_polls < min_total_polls:
        error_msg = (f"GLOBAL POLL COUNT CHECK FAILED: Total polls ({total_polls}) "
                     f"is below the required minimum ({min_total_polls}). "
                     f"The pipeline cannot proceed with insufficient data.")
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Global poll count check passed: {total_polls} total polls (min: {min_total_polls})")
    return True, f"Global poll count check passed: {total_polls} total polls"

def harmonize_data(raw_dfs: List[pd.DataFrame], election_dates: Dict[str, datetime]) -> pd.DataFrame:
    """
    Main harmonization pipeline: parse dates, bin weekly, check sufficiency, and global count.
    
    Args:
        raw_dfs: List of DataFrames from different sources
        election_dates: Dict mapping cycle name to election date
    
    Returns:
        Harmonized DataFrame
    """
    logger.info(f"Starting harmonization of {len(raw_dfs)} datasets")
    
    if not raw_dfs:
        raise ValueError("No data provided for harmonization")
    
    # Concatenate all data
    df = pd.concat(raw_dfs, ignore_index=True)
    logger.info(f"Concatenated data shape: {df.shape}")
    
    # Parse dates
    df = parse_dates(df)
    
    # Bin to weekly
    df = bin_to_weekly(df)
    
    # Check global poll count (FR-010) - This will raise if insufficient
    is_sufficient, msg = check_global_poll_count(df)
    
    # Check data sufficiency for each election
    for cycle, election_date in election_dates.items():
        cycle_data = df[df.get('cycle', df.get('election_year', '')) == cycle]
        if len(cycle_data) > 0:
            check_data_sufficiency(cycle_data, election_date)
    
    # Ensure required columns exist
    required_cols = ['date', 'pollster', 'vote_share', 'sample_size']
    for col in required_cols:
        if col not in df.columns:
            # Create placeholder if missing (should not happen with real data)
            logger.warning(f"Column '{col}' missing, creating placeholder")
            if col == 'vote_share':
                df[col] = 0.0
            elif col == 'sample_size':
                df[col] = 0
            else:
                df[col] = ''
    
    logger.info(f"Harmonization complete. Final shape: {df.shape}")
    return df

def update_state_with_hashes(output_path: str, state_file: Optional[str] = None) -> None:
    """
    Compute SHA-256 hash of the output file and update state management.
    """
    if not os.path.exists(output_path):
        logger.error(f"Output file not found: {output_path}")
        return
    
    file_hash = compute_file_hash(output_path)
    logger.info(f"Computed hash for {output_path}: {file_hash}")
    
    if state_file is None:
        state_root = get_state_root()
        state_file = str(state_root / 'projects' / 'PROJ-206-statistical-analysis-of-publicly-availab.yaml')
    
    update_state_artifact(state_file, output_path, file_hash)

def main():
    """
    Entry point for the harmonization script.
    Downloads raw data, harmonizes it, and saves to data/processed/.
    """
    logger.info("Starting harmonization pipeline")
    
    data_root = get_data_root()
    raw_dir = data_root / 'raw'
    processed_dir = data_root / 'processed'
    
    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # In a real run, we would load from raw_dir
    # For now, we assume download.py has populated raw_dir
    raw_files = list(raw_dir.glob('*.csv'))
    
    if not raw_files:
        logger.warning("No raw CSV files found in data/raw/. Skipping harmonization.")
        # In a real pipeline, this might raise an error
        return
    
    dfs = []
    for f in raw_files:
        logger.info(f"Loading {f}")
        try:
            df = pd.read_csv(f)
            dfs.append(df)
        except Exception as e:
            logger.error(f"Failed to load {f}: {e}")
    
    if not dfs:
        logger.error("No valid data loaded. Cannot proceed.")
        return
    
    # Define election dates (example for 2020, 2016, etc.)
    # In production, this would come from config or metadata
    election_dates = {
        '2020': datetime(2020, 11, 3),
        '2016': datetime(2016, 11, 8),
        '2012': datetime(2012, 11, 6),
        '2008': datetime(2008, 11, 4)
    }
    
    # Harmonize
    try:
        harmonized_df = harmonize_data(dfs, election_dates)
    except ValueError as e:
        logger.error(f"Data sufficiency check failed: {e}")
        sys.exit(1)
    
    # Save output
    output_path = processed_dir / 'poll_data_cleaned.csv'
    harmonized_df.to_csv(output_path, index=False)
    logger.info(f"Saved harmonized data to {output_path}")
    
    # Update state with hash
    update_state_with_hashes(str(output_path))
    
    logger.info("Harmonization pipeline completed successfully")

if __name__ == '__main__':
    main()