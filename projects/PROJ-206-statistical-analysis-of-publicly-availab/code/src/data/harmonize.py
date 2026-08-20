import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

import pandas as pd
import numpy as np

from src.utils.config import get_data_root, get_state_root, resolve_path, compute_file_hash
from src.utils.logging import get_logger
from src.utils.state_manager import update_state_artifact

logger = get_logger(__name__)

def parse_dates(df: pd.DataFrame, date_col: str = 'date') -> pd.DataFrame:
    """
    Parse date strings into datetime objects.
    Handles common formats used in poll data.
    """
    df = df.copy()
    # Try common formats
    date_formats = [
        '%Y-%m-%d',
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%Y/%m/%d',
        '%m-%d-%Y',
        '%d-%m-%Y'
    ]
    
    parsed = False
    for fmt in date_formats:
        try:
            df[date_col] = pd.to_datetime(df[date_col], format=fmt, errors='raise')
            parsed = True
            break
        except (ValueError, TypeError):
            continue
    
    if not parsed:
        # Fallback to pandas inference
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        if df[date_col].isna().all():
            raise ValueError(f"Could not parse dates in column '{date_col}'")
    
    return df

def bin_to_weekly(df: pd.DataFrame, date_col: str = 'date', bin_col: str = 'week_bin') -> pd.DataFrame:
    """
    Bin dates into weekly intervals.
    Uses the start of the week (Monday) as the bin anchor.
    """
    df = df.copy()
    if date_col not in df.columns:
        raise ValueError(f"Column '{date_col}' not found in dataframe")
    
    # Ensure date column is datetime
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df = parse_dates(df, date_col)
    
    # Bin to week start (Monday)
    df[bin_col] = df[date_col].dt.to_period('W').dt.start_time
    return df

def check_data_sufficiency(
    df: pd.DataFrame,
    election_date_col: str = 'election_date',
    date_col: str = 'date',
    min_polls_30d: int = 5,
    min_cycles: int = 3,
    election_date: Optional[datetime] = None
) -> Tuple[bool, str]:
    """
    FR-008: Data sufficiency check.
    
    Halts with warning if:
    1. < 5 polls in the 30 days preceding the election day
    2. < 3 distinct election cycles represented in the data
    
    Args:
        df: DataFrame containing poll data
        election_date_col: Column name for election dates
        date_col: Column name for poll dates
        min_polls_30d: Minimum required polls in 30 days before election
        min_cycles: Minimum required distinct election cycles
        election_date: Specific election date to check (if None, checks all unique election dates)
    
    Returns:
        Tuple of (is_sufficient, message)
    """
    if df.empty:
        return False, "Dataframe is empty; insufficient data."
    
    # Ensure date columns are datetime
    df_check = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_check[date_col]):
        df_check = parse_dates(df_check, date_col)
    
    if election_date_col in df_check.columns and not pd.api.types.is_datetime64_any_dtype(df_check[election_date_col]):
        df_check[election_date_col] = pd.to_datetime(df_check[election_date_col], errors='coerce')
    
    # Check distinct cycles
    if election_date_col in df_check.columns:
        unique_cycles = df_check[election_date_col].dropna().dt.year.nunique()
    else:
        # Fallback: use poll date year as cycle proxy if no election date
        unique_cycles = df_check[date_col].dt.year.nunique()
    
    if unique_cycles < min_cycles:
        return False, f"Data sufficiency check FAILED: Only {unique_cycles} distinct election cycles found. Required: {min_cycles}."
    
    # Check polls in 30 days preceding election
    if election_date is None:
        # If no specific election date provided, check the most recent election date in the data
        if election_date_col in df_check.columns:
            election_dates = df_check[election_date_col].dropna().unique()
            if len(election_dates) == 0:
                return False, "No election dates found in data to perform sufficiency check."
            election_date = max(election_dates)
        else:
            return False, "No election_date_col found and no election_date provided for sufficiency check."
    
    cutoff_date = election_date - timedelta(days=30)
    
    # Count polls in the 30-day window
    polls_in_window = df_check[
        (df_check[date_col] >= cutoff_date) & 
        (df_check[date_col] <= election_date)
    ]
    
    poll_count = len(polls_in_window)
    
    if poll_count < min_polls_30d:
        return False, f"Data sufficiency check FAILED: Only {poll_count} polls found in the 30 days preceding {election_date.date()}. Required: {min_polls_30d}."
    
    return True, f"Data sufficiency check PASSED: {unique_cycles} cycles and {poll_count} polls in the 30-day window."

def check_global_poll_count(df: pd.DataFrame, min_total_polls: int = 500, count_col: str = None) -> Tuple[bool, str]:
    """
    FR-010: Global poll count check.
    
    Halts with error if total count across all ingested election cycles is < 500.
    
    Args:
        df: DataFrame containing poll data
        min_total_polls: Minimum required total polls
        count_col: Column to count (if None, counts all rows)
    
    Returns:
        Tuple of (is_sufficient, message)
    """
    if df.empty:
        return False, "Dataframe is empty; insufficient data."
    
    total_polls = len(df) if count_col is None else df[count_col].sum()
    
    if total_polls < min_total_polls:
        return False, f"Global poll count check FAILED: Only {total_polls} total polls found. Required: {min_total_polls}."
    
    return True, f"Global poll count check PASSED: {total_polls} total polls found."

def harmonize_data(
    raw_data_path: str,
    output_path: str,
    election_date_col: str = 'election_date',
    date_col: str = 'date',
    check_sufficiency: bool = True,
    election_date: Optional[datetime] = None
) -> pd.DataFrame:
    """
    Main function to harmonize poll data.
    
    1. Loads raw data
    2. Parses dates
    3. Bins to weekly intervals
    4. Runs data sufficiency checks (FR-008, FR-010)
    5. Saves cleaned data
    
    Args:
        raw_data_path: Path to raw poll data CSV
        output_path: Path to save cleaned data
        election_date_col: Column name for election dates
        date_col: Column name for poll dates
        check_sufficiency: Whether to run sufficiency checks
        election_date: Specific election date for 30-day check
    
    Returns:
        Cleaned DataFrame
    """
    logger.info(f"Loading raw data from {raw_data_path}")
    df = pd.read_csv(raw_data_path)
    
    logger.info(f"Parsing dates in column '{date_col}'")
    df = parse_dates(df, date_col)
    
    logger.info("Binning data into weekly intervals")
    df = bin_to_weekly(df, date_col)
    
    # Run data sufficiency checks if enabled
    if check_sufficiency:
        logger.info("Running data sufficiency checks (FR-008)")
        is_sufficient, msg = check_data_sufficiency(
            df, 
            election_date_col=election_date_col, 
            date_col=date_col, 
            election_date=election_date
        )
        logger.info(msg)
        
        if not is_sufficient:
            # FR-008: Halt with warning (raise exception to stop pipeline)
            raise RuntimeError(f"Pipeline halted due to data insufficiency: {msg}")
        
        logger.info("Running global poll count check (FR-010)")
        is_sufficient_global, msg_global = check_global_poll_count(df)
        logger.info(msg_global)
        
        if not is_sufficient_global:
            raise RuntimeError(f"Pipeline halted due to insufficient global poll count: {msg_global}")
    
    # Ensure required columns exist for downstream tasks
    required_cols = ['date', 'pollster', 'vote_share', 'sample_size', 'week_bin']
    for col in required_cols:
        if col not in df.columns:
            # Create placeholder if missing (will be filled by weights or other steps)
            if col == 'vote_share':
                df[col] = 0.0
            elif col == 'sample_size':
                df[col] = 0
            else:
                df[col] = None
    
    logger.info(f"Saving cleaned data to {output_path}")
    df.to_csv(output_path, index=False)
    
    return df

def update_state_with_hashes(
    artifacts: List[str],
    project_id: str = "PROJ-206"
) -> None:
    """
    Compute SHA-256 hashes for artifacts and update state file.
    
    Args:
        artifacts: List of file paths to hash
        project_id: Project identifier for state file
    """
    state_root = get_state_root()
    state_file = state_root / "projects" / f"{project_id}.yaml"
    
    artifact_hashes = {}
    for artifact_path in artifacts:
        path = Path(artifact_path)
        if path.exists():
            hash_val = compute_file_hash(path)
            artifact_hashes[str(path)] = hash_val
            logger.info(f"Computed hash for {path}: {hash_val}")
        else:
            logger.warning(f"Artifact not found for hashing: {path}")
    
    if artifact_hashes:
        update_state_artifact(state_file, artifact_hashes)
        logger.info(f"Updated state file: {state_file}")

def main():
    """
    Entry point for running harmonization with sufficiency checks.
    """
    data_root = get_data_root()
    raw_path = data_root / "raw" / "fivethirtyeight_polls.csv"
    output_path = data_root / "processed" / "poll_data_cleaned.csv"
    
    if not raw_path.exists():
        logger.error(f"Raw data file not found: {raw_path}")
        sys.exit(1)
    
    try:
        df = harmonize_data(
            raw_data_path=str(raw_path),
            output_path=str(output_path),
            check_sufficiency=True
        )
        logger.info(f"Harmonization complete. Output: {output_path}")
        
        # Update state with hashes
        update_state_with_hashes([str(output_path)])
        
    except RuntimeError as e:
        logger.error(f"Pipeline halted: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during harmonization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()