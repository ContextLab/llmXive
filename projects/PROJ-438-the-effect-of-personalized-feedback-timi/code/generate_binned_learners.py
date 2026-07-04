"""
Task T026: Generate data/processed/learners_binned.csv with interval and group columns.

This script loads the learner-level intervals computed by compute_intervals.py,
applies the binning logic defined in bin_feedback_groups.py, and saves the
final binned dataset required for User Story 2.

Output: data/processed/learners_binned.csv
"""
import os
import sys
import pandas as pd
from pathlib import Path

# Import from sibling modules using the defined API surface
from bin_feedback_groups import load_learner_intervals, assign_feedback_group, bin_feedback_groups, save_binned_data
from logging_config import get_logger, info, error, warning

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Input/Output paths
INPUT_FILE = DATA_PROCESSED_DIR / "learners_intervals.csv"
OUTPUT_FILE = DATA_PROCESSED_DIR / "learners_binned.csv"

def main():
    logger = get_logger(__name__)
    info("Starting T026: Generate binned learners dataset")
    
    # Ensure output directory exists
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if input file exists
    if not INPUT_FILE.exists():
        error(f"Input file not found: {INPUT_FILE}")
        error("Please run compute_intervals.py (T023) first to generate learners_intervals.csv")
        sys.exit(1)
    
    info(f"Loading interval data from {INPUT_FILE}")
    try:
        df_intervals = load_learner_intervals(INPUT_FILE)
    except Exception as e:
        error(f"Failed to load interval data: {e}")
        sys.exit(1)
    
    if df_intervals.empty:
        error("Loaded data is empty. Cannot proceed with binning.")
        sys.exit(1)
    
    info(f"Loaded {len(df_intervals)} learner records with intervals")
    
    # Apply binning logic
    # The bin_feedback_groups function expects a dataframe with a 'median_interval_hours' column
    # and returns a dataframe with 'feedback_group' added
    info("Applying feedback group binning (<2h: Immediate, 2-48h: Delayed, >48h: Variable)")
    try:
        df_binned = bin_feedback_groups(df_intervals)
    except Exception as e:
        error(f"Binning logic failed: {e}")
        sys.exit(1)
    
    # Verify required columns exist
    required_cols = ['learner_id', 'median_interval_hours', 'feedback_group']
    missing_cols = [c for c in required_cols if c not in df_binned.columns]
    if missing_cols:
        error(f"Missing required columns after binning: {missing_cols}")
        sys.exit(1)
    
    # Save the output
    info(f"Saving binned data to {OUTPUT_FILE}")
    try:
        save_binned_data(df_binned, OUTPUT_FILE)
    except Exception as e:
        error(f"Failed to save binned data: {e}")
        sys.exit(1)
    
    # Summary statistics
    group_counts = df_binned['feedback_group'].value_counts()
    info("Binning distribution:")
    for group, count in group_counts.items():
        info(f"  {group}: {count} learners ({100*count/len(df_binned):.1f}%)")
    
    info(f"T026 Complete: Generated {OUTPUT_FILE} with {len(df_binned)} records")

if __name__ == "__main__":
    main()