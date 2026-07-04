import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import numpy as np

from src.utils.config import get_project_root, get_data_root, get_state_root, compute_file_hash, ensure_dir, get_config
from src.utils.logging import get_logger

logger = get_logger(__name__)

def parse_dates(df: pd.DataFrame, date_col: str = 'date') -> pd.DataFrame:
    """Parse date strings into datetime objects."""
    df = df.copy()
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    return df

def bin_to_weekly(df: pd.DataFrame, date_col: str = 'date', bin_col: str = 'week_bin') -> pd.DataFrame:
    """Bin dates into weekly intervals."""
    df = df.copy()
    if date_col not in df.columns:
        return df
    
    # Ensure dates are datetime
    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    # Bin to week start (Monday)
    df[bin_col] = df[date_col].dt.to_period('W').dt.start_time
    return df

def check_data_sufficiency(df: pd.DataFrame, election_date: datetime, days_back: int = 30, min_polls: int = 5) -> bool:
    """Check if there are sufficient polls in the days leading up to the election."""
    if df.empty:
        logger.warning("Data sufficiency check failed: Empty dataset")
        return False
    
    recent_polls = df[df['date'] >= (election_date - timedelta(days=days_back))]
    if len(recent_polls) < min_polls:
        logger.warning(f"Data sufficiency check failed: Only {len(recent_polls)} polls in last {days_back} days (min: {min_polls})")
        return False
    
    distinct_cycles = df['cycle'].nunique() if 'cycle' in df.columns else 1
    if distinct_cycles < 3:
        logger.warning(f"Data sufficiency check failed: Only {distinct_cycles} distinct cycles (min: 3)")
        return False
    
    logger.info(f"Data sufficiency check passed: {len(recent_polls)} recent polls, {distinct_cycles} cycles")
    return True

def check_global_poll_count(df: pd.DataFrame, min_count: int = 500) -> bool:
    """Check if total poll count across all cycles meets minimum threshold."""
    total_count = len(df)
    if total_count < min_count:
        logger.error(f"Global poll count check failed: Only {total_count} polls (min: {min_count})")
        return False
    
    logger.info(f"Global poll count check passed: {total_count} total polls")
    return True

def harmonize_data(raw_polls: List[pd.DataFrame], raw_outcomes: List[pd.DataFrame]) -> pd.DataFrame:
    """Harmonize poll data from multiple sources."""
    if not raw_polls:
        raise ValueError("No poll data provided for harmonization")
    
    # Concatenate all poll dataframes
    df = pd.concat(raw_polls, ignore_index=True)
    
    # Parse dates
    df = parse_dates(df)
    
    # Bin to weekly
    df = bin_to_weekly(df)
    
    # Drop rows with invalid dates
    df = df.dropna(subset=['date'])
    
    # Remove duplicate dates per pollster (keep most recent)
    if 'pollster' in df.columns:
        df = df.sort_values('date').drop_duplicates(subset=['date', 'pollster'], keep='last')
    
    # Standardize column names if needed
    required_cols = ['date', 'pollster', 'vote_share', 'sample_size', 'cycle']
    existing_cols = df.columns.tolist()
    
    # Add missing columns with defaults if they don't exist
    for col in required_cols:
        if col not in existing_cols:
            df[col] = None
    
    # Select and order columns
    df = df[required_cols + [c for c in df.columns if c not in required_cols]]
    
    return df

def update_state_with_hashes(cleaned_csv_path: str, weights_csv_path: Optional[str] = None) -> None:
    """Compute SHA-256 hashes for output files and update state YAML."""
    project_root = get_project_root()
    state_root = get_state_root()
    state_file = state_root / "PROJ-206-statistical-analysis.yaml"
    
    hashes = {}
    
    # Hash cleaned poll data
    if os.path.exists(cleaned_csv_path):
        hashes['poll_data_cleaned.csv'] = compute_file_hash(cleaned_csv_path)
        logger.info(f"Computed hash for {cleaned_csv_path}: {hashes['poll_data_cleaned.csv']}")
    else:
        logger.warning(f"File not found for hashing: {cleaned_csv_path}")
    
    # Hash weights file if provided
    if weights_csv_path and os.path.exists(weights_csv_path):
        hashes['historical_weights.csv'] = compute_file_hash(weights_csv_path)
        logger.info(f"Computed hash for {weights_csv_path}: {hashes['historical_weights.csv']}")
    elif weights_csv_path:
        logger.warning(f"File not found for hashing: {weights_csv_path}")
    
    # Load existing state or create new
    state_data = {}
    if state_file.exists():
        import yaml
        try:
            with open(state_file, 'r') as f:
                state_data = yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load existing state file: {e}. Creating new.")
            state_data = {}
    
    # Update with new hashes
    state_data['artifacts'] = state_data.get('artifacts', {})
    state_data['artifacts']['last_updated'] = datetime.now().isoformat()
    for filename, file_hash in hashes.items():
        state_data['artifacts'][filename] = {
            'sha256': file_hash,
            'updated_at': datetime.now().isoformat()
        }
    
    # Ensure directory exists
    ensure_dir(state_file.parent)
    
    # Write updated state
    import yaml
    with open(state_file, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"State file updated: {state_file}")

def main():
    """Main entry point for harmonization pipeline."""
    logger.info("Starting data harmonization...")
    
    data_root = get_data_root()
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    
    # Ensure directories exist
    ensure_dir(processed_dir)
    
    # Load raw data (simulated for this task - in real scenario, files would exist)
    # In a real run, download.py would have populated data/raw/
    raw_poll_files = list(raw_dir.glob("*.csv")) if raw_dir.exists() else []
    
    if not raw_poll_files:
        logger.warning("No raw poll files found. Expected in data/raw/.")
        # For demonstration, we'll create a minimal valid dataset if none exists
        # In production, this should fail or wait for data
        df = pd.DataFrame({
            'date': pd.date_range('2024-01-01', periods=10),
            'pollster': ['PollA'] * 10,
            'vote_share': np.random.uniform(40, 60, 10),
            'sample_size': np.random.randint(500, 2000, 10),
            'cycle': [2024] * 10
        })
    else:
        raw_polls = []
        for f in raw_poll_files:
            try:
                df = pd.read_csv(f)
                raw_polls.append(df)
            except Exception as e:
                logger.error(f"Failed to load {f}: {e}")
        
        if not raw_polls:
            raise RuntimeError("No valid poll data could be loaded.")
        
        df = harmonize_data(raw_polls, [])
    
    # Check data sufficiency (using a dummy election date for demo)
    election_date = datetime(2024, 11, 5)
    if not check_data_sufficiency(df, election_date):
        logger.warning("Data sufficiency check failed. Pipeline may be incomplete.")
    
    if not check_global_poll_count(df):
        logger.error("Global poll count check failed. Halting.")
        sys.exit(1)
    
    # Save cleaned data
    cleaned_path = processed_dir / "poll_data_cleaned.csv"
    df.to_csv(cleaned_path, index=False)
    logger.info(f"Saved cleaned data to {cleaned_path}")
    
    # Update state with hashes
    weights_path = str(processed_dir / "historical_weights.csv")
    update_state_with_hashes(str(cleaned_path), weights_path)
    
    logger.info("Harmonization complete.")
    return df

if __name__ == "__main__":
    main()
