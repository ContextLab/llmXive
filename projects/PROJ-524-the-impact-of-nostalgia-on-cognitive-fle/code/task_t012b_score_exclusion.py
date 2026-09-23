"""
T012b: Score Exclusion Task

Filters the age-filtered dataset for non-null `perseverative_errors` and `categories_completed`.
Writes filtered data to `data/processed/cleaned_score_filtered.csv`.
Updates `data/processed/exclusion_counts.json` with key `ERR_MISSING_SCORE`.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path
from utils import setup_logging, log_info, log_warning, log_error

# Constants
INPUT_FILE = Path("data/processed/cleaned_age_filtered.csv")
OUTPUT_FILE = Path("data/processed/cleaned_score_filtered.csv")
EXCLUSION_COUNTS_FILE = Path("data/processed/exclusion_counts.json")
LOG_KEY = "ERR_MISSING_SCORE"

def load_age_filtered_dataset() -> pd.DataFrame:
    """Load the age-filtered dataset."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")
    return pd.read_csv(INPUT_FILE)

def filter_by_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter dataframe for non-null `perseverative_errors` and `categories_completed`.
    """
    initial_count = len(df)
    # Filter for non-null values in both columns
    mask = df["perseverative_errors"].notna() & df["categories_completed"].notna()
    filtered_df = df[mask]
    final_count = len(filtered_df)
    excluded_count = initial_count - final_count
    
    log_info(f"Score filtering: {excluded_count} records excluded due to missing scores.")
    return filtered_df, excluded_count

def save_filtered_dataset(df: pd.DataFrame) -> None:
    """Save the filtered dataset to CSV."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    log_info(f"Saved filtered dataset to {OUTPUT_FILE}")

def update_exclusion_counts(excluded_count: int) -> None:
    """Update the exclusion counts JSON file."""
    counts = {"ERR_MISSING_AGE_FIELD": 0, "ERR_MISSING_SCORE": 0, "ERR_MMSE_IMPAIRED": 0}
    
    if EXCLUSION_COUNTS_FILE.exists():
        try:
            with open(EXCLUSION_COUNTS_FILE, "r") as f:
                counts = json.load(f)
        except json.JSONDecodeError:
            log_warning(f"Invalid JSON in {EXCLUSION_COUNTS_FILE}, resetting counts.")
    
    counts[LOG_KEY] = excluded_count
    
    with open(EXCLUSION_COUNTS_FILE, "w") as f:
        json.dump(counts, f, indent=2)
    
    log_info(f"Updated exclusion counts: {counts}")

def main():
    """Main entry point for T012b."""
    setup_logging()
    log_info("Starting T012b: Score Exclusion")
    
    try:
        # Load data
        log_info(f"Loading data from {INPUT_FILE}")
        df = load_age_filtered_dataset()
        
        # Filter by score
        filtered_df, excluded_count = filter_by_score(df)
        
        # Save output
        save_filtered_dataset(filtered_df)
        
        # Update exclusion counts
        update_exclusion_counts(excluded_count)
        
        log_info("T012b completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        log_error(f"File not found: {e}")
        return 1
    except Exception as e:
        log_error(f"Error during score exclusion: {e}")
        raise

if __name__ == "__main__":
    exit(main())
