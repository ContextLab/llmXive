"""
T012b: SCORE EXCLUSION
Filter data/processed/cleaned_age_filtered.csv for non-null perseverative_errors and categories_completed.
Write filtered data to data/processed/cleaned_score_filtered.csv.
Write exclusion count to data/processed/exclusion_counts.json with key ERR_MISSING_SCORE.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path

from utils import setup_logging, log_info, log_warning, log_error

# Configure logging
logger = setup_logging("T012b_SCORE_EXCLUSION")

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "cleaned_age_filtered.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "cleaned_score_filtered.csv"
EXCLUSION_COUNTS_FILE = PROJECT_ROOT / "data" / "processed" / "exclusion_counts.json"

REQUIRED_COLUMNS = ["perseverative_errors", "categories_completed"]

def load_age_filtered_dataset() -> pd.DataFrame:
    """Load the age-filtered dataset."""
    if not INPUT_FILE.exists():
        log_error(logger, f"Input file not found: {INPUT_FILE}")
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")
    
    log_info(logger, f"Loading age-filtered dataset from {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    log_info(logger, f"Loaded {len(df)} records")
    return df

def filter_by_score(df: pd.DataFrame) -> pd.DataFrame:
    """Filter for non-null perseverative_errors and categories_completed."""
    initial_count = len(df)
    
    # Check for required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        log_error(logger, f"Missing required columns: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Filter for non-null values in both columns
    mask = df[REQUIRED_COLUMNS].notna().all(axis=1)
    filtered_df = df[mask]
    
    excluded_count = initial_count - len(filtered_df)
    
    log_info(logger, f"Filtered {excluded_count} records with missing scores")
    log_info(logger, f"Remaining records: {len(filtered_df)}")
    
    return filtered_df, excluded_count

def save_filtered_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """Save the filtered dataset."""
    df.to_csv(output_path, index=False)
    log_info(logger, f"Saved filtered dataset to {output_path}")

def update_exclusion_counts(excluded_count: int) -> None:
    """Update the exclusion counts JSON file."""
    # Load existing counts or initialize
    if EXCLUSION_COUNTS_FILE.exists():
        with open(EXCLUSION_COUNTS_FILE, 'r') as f:
            counts = json.load(f)
    else:
        counts = {
            "ERR_MISSING_AGE_FIELD": 0,
            "ERR_MISSING_SCORE": 0,
            "ERR_MMSE_IMPAIRED": 0
        }
    
    # Update the specific exclusion count
    counts["ERR_MISSING_SCORE"] = excluded_count
    
    # Save updated counts
    with open(EXCLUSION_COUNTS_FILE, 'w') as f:
        json.dump(counts, f, indent=2)
    
    log_info(logger, f"Updated exclusion counts: {counts}")

def main() -> int:
    """Main entry point for T012b."""
    try:
        # Load the age-filtered dataset
        df = load_age_filtered_dataset()
        
        # Filter by score (non-null perseverative_errors and categories_completed)
        filtered_df, excluded_count = filter_by_score(df)
        
        # Save the filtered dataset
        save_filtered_dataset(filtered_df, OUTPUT_FILE)
        
        # Update exclusion counts
        update_exclusion_counts(excluded_count)
        
        log_info(logger, "T012b completed successfully")
        return 0
        
    except Exception as e:
        log_error(logger, f"T012b failed with error: {e}")
        raise

if __name__ == "__main__":
    exit(main())
