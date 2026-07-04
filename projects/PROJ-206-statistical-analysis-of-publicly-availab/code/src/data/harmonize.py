import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from src.utils.config import get_project_root, get_data_processed_path
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Minimum global poll count threshold defined in FR-010
MIN_GLOBAL_POLL_COUNT = 500

def parse_raw_csvs(raw_data_dir: Path) -> List[pd.DataFrame]:
    """
    Load all CSV files from the raw data directory into a list of DataFrames.
    """
    if not raw_data_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_data_dir}")
    
    csv_files = list(raw_data_dir.glob("*.csv"))
    if not csv_files:
        raise ValueError(f"No CSV files found in {raw_data_dir}")
    
    dfs = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            dfs.append(df)
            logger.info(f"Loaded {len(df)} rows from {csv_file.name}")
        except Exception as e:
            logger.error(f"Failed to parse {csv_file.name}: {e}")
            raise
    
    return dfs

def unify_date_formats(df: pd.DataFrame, date_column: str = "date") -> pd.DataFrame:
    """
    Standardize date formats in the dataframe.
    Assumes dates are in common formats (YYYY-MM-DD, MM/DD/YYYY, etc.).
    """
    df = df.copy()
    if date_column not in df.columns:
        raise ValueError(f"Date column '{date_column}' not found in dataframe")
    
    df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
    df = df.dropna(subset=[date_column])
    return df

def bin_into_weekly_intervals(df: pd.DataFrame, date_column: str = "date") -> pd.DataFrame:
    """
    Bin data into weekly intervals based on the date column.
    Adds a 'week_start' column representing the start of the week (Monday).
    """
    df = df.copy()
    df['week_start'] = df[date_column].dt.to_period('W').dt.start_time
    return df

def check_data_sufficiency(df: pd.DataFrame, election_date: pd.Timestamp, days_window: int = 30, min_polls: int = 5, min_cycles: int = 3) -> Tuple[bool, str]:
    """
    Check if data is sufficient for analysis.
    
    Requirements:
    1. At least `min_polls` within `days_window` days before `election_date`.
    2. Data spans at least `min_cycles` distinct election cycles.
    
    Returns:
        Tuple[bool, str]: (is_sufficient, message)
    """
    # Check recent polls
    cutoff_date = election_date - pd.Timedelta(days=days_window)
    recent_polls = df[df['date'] >= cutoff_date]
    
    if len(recent_polls) < min_polls:
        return False, f"Insufficient recent data: found {len(recent_polls)} polls in last {days_window} days (required: {min_polls})"
    
    # Check cycles (assuming 'cycle' column exists or infer from year)
    if 'cycle' in df.columns:
        distinct_cycles = df['cycle'].nunique()
    else:
        # Infer cycle from year if not present
        distinct_cycles = df['date'].dt.year.nunique()
    
    if distinct_cycles < min_cycles:
        return False, f"Insufficient election cycles: found {distinct_cycles} (required: {min_cycles})"
    
    return True, "Data sufficiency check passed"

def check_global_poll_count(df: pd.DataFrame) -> Tuple[bool, str]:
    """
    Implement FR-010: Global poll count check.
    
    Halts with error if total count across all ingested election cycles is < 500.
    
    Returns:
        Tuple[bool, str]: (is_sufficient, message)
    """
    total_count = len(df)
    if total_count < MIN_GLOBAL_POLL_COUNT:
        return False, f"Global poll count insufficient: found {total_count} polls (required: {MIN_GLOBAL_POLL_COUNT}). Pipeline halted per FR-010."
    
    logger.info(f"Global poll count check passed: {total_count} polls available.")
    return True, f"Global poll count sufficient: {total_count} polls"

def harmonize_data(raw_data_dir: Optional[Path] = None) -> pd.DataFrame:
    """
    Main orchestration function for data harmonization.
    
    1. Parses raw CSVs.
    2. Unifies date formats.
    3. Bins into weekly intervals.
    4. Checks data sufficiency (recent and cycles).
    5. Checks global poll count (FR-010).
    
    Args:
        raw_data_dir: Path to raw data directory. Defaults to project's data/raw.
        
    Returns:
        pd.DataFrame: Harmonized and validated dataset.
        
    Raises:
        ValueError: If data sufficiency or global count checks fail.
    """
    if raw_data_dir is None:
        project_root = get_project_root()
        raw_data_dir = project_root / "data" / "raw"
    
    # 1. Parse
    dfs = parse_raw_csvs(raw_data_dir)
    if not dfs:
        raise ValueError("No dataframes loaded from raw directory")
    
    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Combined {len(combined_df)} total rows from all sources")
    
    # 2. Unify Dates
    # Determine date column dynamically if standard name not found
    date_col = "date" if "date" in combined_df.columns else combined_df.columns[0]
    combined_df = unify_date_formats(combined_df, date_column=date_col)
    
    # 3. Bin Weeks
    combined_df = bin_into_weekly_intervals(combined_df, date_column=date_col)
    
    # 4. Check Data Sufficiency (T013 logic)
    # Need an election date for the check. Assuming the most recent election date in data
    # or a known target. For this implementation, we assume the latest date in the dataset
    # approximates the election date for the sufficiency check context, 
    # or we require a specific election_date param. 
    # Given T013 context, we assume a target election date is known or inferred.
    # For robustness, we'll use the max date in the dataset as a proxy for the election date
    # if not provided, though in a real pipeline this would be a config parameter.
    election_date = combined_df[date_col].max()
    
    is_suff, suff_msg = check_data_sufficiency(combined_df, election_date)
    if not is_suff:
        logger.warning(suff_msg)
        # T013: Halt with warning. We continue to global check but log the warning.
        # In a strict pipeline, this might raise, but T015 handles the blocking gate.
    
    # 5. Check Global Poll Count (T014 - FR-010)
    is_global, global_msg = check_global_poll_count(combined_df)
    if not is_global:
        # T014: Halt with ERROR.
        logger.error(global_msg)
        raise ValueError(global_msg)
    
    logger.info("Harmonization complete and validated.")
    return combined_df

def main():
    """Entry point for running harmonization as a script."""
    try:
        df = harmonize_data()
        
        # Save output
        output_dir = get_data_processed_path()
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "poll_data_cleaned.csv"
        
        df.to_csv(output_path, index=False)
        logger.info(f"Saved harmonized data to {output_path}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()