import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np

from src.utils.config import get_data_root, get_state_root, resolve_path, ensure_dir
from src.utils.logging import get_logger
from src.utils.state_manager import compute_file_hash, update_state_artifact

logger = get_logger(__name__)

def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse date strings into datetime objects.
    Handles common formats: YYYY-MM-DD, MM/DD/YYYY, etc.
    """
    logger.info("Parsing date formats in dataset...")
    df = df.copy()
    date_col = 'date'
    
    # Ensure date column exists
    if date_col not in df.columns:
        raise ValueError(f"Expected column '{date_col}' not found in dataset")
    
    # Try parsing with pandas (handles many formats automatically)
    try:
        df[date_col] = pd.to_datetime(df[date_col])
    except Exception as e:
        logger.error(f"Failed to parse dates: {e}")
        raise
    
    # Drop rows with invalid dates
    invalid_dates = df[date_col].isna().sum()
    if invalid_dates > 0:
        logger.warning(f"Dropped {invalid_dates} rows with invalid dates")
        df = df.dropna(subset=[date_col])
    
    return df

def bin_to_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Bin poll data into weekly intervals.
    Creates a 'week_start' column representing the Monday of the week.
    """
    logger.info("Binning data into weekly intervals...")
    df = df.copy()
    
    # Ensure date column is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
    
    # Calculate week start (Monday)
    df['week_start'] = df['date'] - pd.to_timedelta(df['date'].dt.weekday, unit='D')
    
    # Sort by week start
    df = df.sort_values('week_start')
    
    return df

def check_data_sufficiency(df: pd.DataFrame, election_date: datetime, window_days: int = 30, min_polls: int = 5, min_cycles: int = 3) -> Tuple[bool, str]:
    """
    FR-008: Data sufficiency check.
    
    Halts with warning if:
    - Fewer than `min_polls` (default 5) in the `window_days` (default 30) preceding `election_date`
    - Fewer than `min_cycles` (default 3) distinct election cycles represented in the data
    
    Returns (is_sufficient, message)
    """
    logger.info(f"Checking data sufficiency (window={window_days}d, min_polls={min_polls}, min_cycles={min_cycles})...")
    
    if df.empty:
        return False, "Dataset is empty."
    
    # Ensure date column is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
    
    # 1. Check recent polls (within window_days before election_date)
    cutoff_date = election_date - timedelta(days=window_days)
    recent_polls = df[(df['date'] >= cutoff_date) & (df['date'] <= election_date)]
    recent_count = len(recent_polls)
    
    if recent_count < min_polls:
        msg = (f"Data sufficiency check FAILED: Only {recent_count} polls found in the "
               f"{window_days} days preceding the election ({election_date.date()}). "
               f"Minimum required: {min_polls}. Pipeline will halt.")
        logger.warning(msg)
        return False, msg
    
    logger.info(f"Recent poll check passed: {recent_count} polls found in last {window_days} days.")
    
    # 2. Check distinct cycles
    # Assuming 'cycle' or 'election_year' column exists. If not, try to infer from date.
    cycle_col = None
    if 'cycle' in df.columns:
        cycle_col = 'cycle'
    elif 'election_year' in df.columns:
        cycle_col = 'election_year'
    elif 'year' in df.columns:
        cycle_col = 'year'
    
    if cycle_col is None:
        # Infer from date year if no explicit cycle column
        logger.warning("No explicit cycle column found. Inferring from year.")
        df['inferred_cycle'] = df['date'].dt.year
        cycle_col = 'inferred_cycle'
    
    distinct_cycles = df[cycle_col].nunique()
    
    if distinct_cycles < min_cycles:
        msg = (f"Data sufficiency check FAILED: Only {distinct_cycles} distinct election cycles found. "
               f"Minimum required: {min_cycles}. Pipeline will halt.")
        logger.warning(msg)
        return False, msg
    
    logger.info(f"Cycle check passed: {distinct_cycles} distinct cycles found.")
    
    return True, "Data sufficiency check passed."

def check_global_poll_count(df: pd.DataFrame, min_total: int = 500) -> Tuple[bool, str]:
    """
    FR-010: Global poll count check.
    
    Halts with error if total count across all ingested election cycles is < `min_total` (default 500).
    
    Returns (is_sufficient, message)
    """
    logger.info(f"Checking global poll count (min={min_total})...")
    
    total_count = len(df)
    
    if total_count < min_total:
        msg = (f"Global poll count check FAILED: Total {total_count} polls found. "
               f"Minimum required: {min_total}. Pipeline will halt.")
        logger.error(msg)
        return False, msg
    
    logger.info(f"Global poll count check passed: {total_count} polls found.")
    return True, "Global poll count check passed."

def harmonize_data(raw_data_path: str, output_path: str, election_date: Optional[datetime] = None) -> pd.DataFrame:
    """
    Main harmonization pipeline:
    1. Load raw CSVs
    2. Parse dates
    3. Bin to weekly
    4. Run data sufficiency checks (FR-008, FR-010)
    5. Save cleaned data
    """
    logger.info(f"Starting harmonization from {raw_data_path}")
    
    # Load data
    if os.path.isdir(raw_data_path):
        files = [f for f in os.listdir(raw_data_path) if f.endswith('.csv')]
        if not files:
            raise FileNotFoundError(f"No CSV files found in {raw_data_path}")
        dfs = []
        for f in files:
            path = os.path.join(raw_data_path, f)
            try:
                dfs.append(pd.read_csv(path))
                logger.info(f"Loaded {path}")
            except Exception as e:
                logger.warning(f"Failed to load {path}: {e}")
        df = pd.concat(dfs, ignore_index=True)
    else:
        df = pd.read_csv(raw_data_path)
        logger.info(f"Loaded {raw_data_path}")
    
    # Parse dates
    df = parse_dates(df)
    
    # Bin to weekly
    df = bin_to_weekly(df)
    
    # Determine election date if not provided
    if election_date is None:
        # Try to infer from max date or specific column
        if 'election_date' in df.columns:
            election_date = pd.to_datetime(df['election_date'].max())
        else:
            election_date = df['date'].max() + timedelta(days=7) # Fallback
        logger.info(f"Inferred election date: {election_date}")
    
    # Run sufficiency checks
    suff_ok, suff_msg = check_data_sufficiency(df, election_date)
    if not suff_ok:
        # Log as warning but raise to halt pipeline as per spec
        raise RuntimeError(suff_msg)
    
    global_ok, global_msg = check_global_poll_count(df)
    if not global_ok:
        # Log as error and raise to halt pipeline
        raise RuntimeError(global_msg)
    
    # Ensure output directory exists
    ensure_dir(os.path.dirname(output_path))
    
    # Save cleaned data
    df.to_csv(output_path, index=False)
    logger.info(f"Saved harmonized data to {output_path}")
    
    return df

def update_state_with_hashes(output_files: List[str], project_id: str = "PROJ-206"):
    """
    Compute SHA-256 hashes for output files and update state.
    """
    state_root = get_state_root()
    state_file = state_root / f"projects/{project_id}.yaml"
    
    logger.info(f"Updating state file: {state_file}")
    
    artifacts = {}
    for file_path in output_files:
        if os.path.exists(file_path):
          artifacts[file_path] = compute_file_hash(file_path)
        else:
          logger.warning(f"File not found for hashing: {file_path}")
    
    update_state_artifact(state_file, "harmonization", artifacts)

def main():
    """
    Entry point for harmonization script.
    """
    logging.basicConfig(level=logging.INFO)
    
    data_root = get_data_root()
    raw_path = data_root / "raw"
    processed_path = data_root / "processed"
    
    # Default election date (can be overridden via config or args in full pipeline)
    # For this script, we assume a generic check or rely on data max date
    election_date = None 
    
    output_file = processed_path / "poll_data_cleaned.csv"
    
    try:
        df = harmonize_data(str(raw_path), str(output_file), election_date)
        
        # Update state with hashes
        update_state_with_hashes([str(output_file)])
        
        logger.info("Harmonization completed successfully.")
    except RuntimeError as e:
        logger.error(f"Pipeline halted due to data insufficiency: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during harmonization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()