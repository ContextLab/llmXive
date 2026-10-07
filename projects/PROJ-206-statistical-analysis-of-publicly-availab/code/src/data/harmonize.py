import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

import pandas as pd
import numpy as np

from src.utils.config import get_data_root, get_project_root, resolve_path
from src.utils.logging import get_logger
from src.utils.state_manager import update_state_artifact

logger = get_logger(__name__)

def parse_dates(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """
    Parse date strings into datetime objects.
    Supports multiple common formats.
    """
    df = df.copy()
    date_formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%m-%d-%Y",
        "%d-%m-%Y",
    ]
    
    def try_parse(date_str):
        if pd.isna(date_str):
            return pd.NaT
        date_str = str(date_str).strip()
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        # Try pandas parser as fallback
        try:
            return pd.to_datetime(date_str)
        except:
            return pd.NaT

    df[date_col] = df[date_col].apply(try_parse)
    df = df.dropna(subset=[date_col])
    return df

def bin_to_weekly(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """
    Bin dates into weekly intervals.
    Adds a 'week_start' column representing the Monday of that week.
    """
    df = df.copy()
    df["week_start"] = df[date_col].dt.to_period("W").dt.start_time
    return df

def check_data_sufficiency(df: pd.DataFrame, election_date: datetime, days_before: int = 30, min_polls: int = 5) -> Tuple[bool, str]:
    """
    Check if there are enough polls in the specified window before the election.
    
    Returns:
        Tuple of (is_sufficient, message)
    """
    cutoff_date = election_date - timedelta(days=days_before)
    recent_polls = df[df["date"] >= cutoff_date]
    
    if len(recent_polls) < min_polls:
        return False, f"Insufficient data: only {len(recent_polls)} polls in last {days_before} days (minimum: {min_polls})"
    
    return True, f"Sufficient data: {len(recent_polls)} polls in last {days_before} days"

def check_global_poll_count(df: pd.DataFrame, min_total: int = 500) -> Tuple[bool, str]:
    """
    Check if total poll count across all cycles meets minimum threshold.
    
    Returns:
        Tuple of (is_sufficient, message)
    """
    total_count = len(df)
    if total_count < min_total:
        return False, f"Global poll count too low: {total_count} (minimum: {min_total})"
    return True, f"Global poll count sufficient: {total_count} polls"

def harmonize_data(raw_dir: Optional[Path] = None, output_dir: Optional[Path] = None) -> pd.DataFrame:
    """
    Main harmonization pipeline:
    1. Load all CSV files from raw_dir
    2. Parse dates
    3. Bin to weekly intervals
    4. Check data sufficiency
    5. Output cleaned dataset
    
    Returns:
        Cleaned DataFrame
    """
    data_root = get_data_root()
    raw_dir = raw_dir or data_root / "raw"
    output_dir = output_dir or data_root / "processed"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load all CSV files
    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {raw_dir}")
    
    logger.info(f"Found {len(csv_files)} CSV files to process")
    
    dfs = []
    for csv_file in csv_files:
        logger.info(f"Loading {csv_file.name}")
        df = pd.read_csv(csv_file)
        dfs.append(df)
    
    # Concatenate all data
    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Combined dataset has {len(combined_df)} rows")
    
    # Parse dates
    combined_df = parse_dates(combined_df)
    logger.info(f"After date parsing: {len(combined_df)} rows")
    
    # Bin to weekly
    combined_df = bin_to_weekly(combined_df)
    
    # Ensure required columns exist
    required_cols = ["date", "pollster", "vote_share", "sample_size"]
    for col in required_cols:
        if col not in combined_df.columns:
            logger.warning(f"Column '{col}' not found, creating with default values")
            combined_df[col] = 0 if col != "pollster" else "unknown"
    
    # Select and order columns
    output_cols = ["date", "pollster", "vote_share", "sample_size", "week_start"]
    available_cols = [c for c in output_cols if c in combined_df.columns]
    combined_df = combined_df[available_cols]
    
    # Remove duplicates (same pollster, same week)
    combined_df = combined_df.drop_duplicates(subset=["pollster", "week_start"], keep="last")
    logger.info(f"After deduplication: {len(combined_df)} rows")
    
    # Check data sufficiency (placeholder election date - would be configured)
    # For now, just log the check
    election_date = datetime(2024, 11, 5)  # Example election date
    is_sufficient, msg = check_data_sufficiency(combined_df, election_date)
    logger.info(msg)
    
    # Check global count
    is_global_ok, global_msg = check_global_poll_count(combined_df)
    logger.info(global_msg)
    
    # Save cleaned data
    output_file = output_dir / "poll_data_cleaned.csv"
    combined_df.to_csv(output_file, index=False)
    logger.info(f"Saved cleaned data to {output_file}")
    
    # Update state with hash
    update_state_artifact(
        "poll_data_cleaned.csv",
        output_file,
        description="Harmonized and cleaned poll data with weekly binning"
    )
    
    return combined_df

def main():
    """CLI entry point for data harmonization."""
    logger.info("Starting data harmonization")
    try:
        df = harmonize_data()
        logger.info(f"HARMONIZATION COMPLETE: {len(df)} rows processed")
    except Exception as e:
        logger.error(f"HARMONIZATION FAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
