"""
T026: Generate data/processed/learners_binned.csv with interval and group columns.

This script orchestrates the binning of learner intervals into feedback timing groups
(Immediate, Delayed, Variable) and saves the result to the processed data directory.

It relies on the output of T023 (compute_intervals.py) which produces learner-level
median intervals.
"""
import os
import sys
from pathlib import Path

# Ensure the code directory is in the path for imports
code_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(code_dir))

from bin_feedback_groups import load_learner_intervals, assign_feedback_group, bin_feedback_groups, save_binned_data
from logging_config import get_logger, info, error, warning

logger = get_logger(__name__)

def main():
    """
    Main entry point for generating the binned learners dataset.
    
    1. Loads learner intervals from data/processed/learners_intervals.csv (produced by T023).
    2. Assigns feedback groups based on median intervals.
    3. Saves the result to data/processed/learners_binned.csv.
    """
    logger.info("Starting generation of binned learners dataset (T026)...")
    
    # Define paths relative to project root
    # Assuming project root is parent of 'code' directory
    project_root = code_dir.parent
    input_path = project_root / "data" / "processed" / "learners_intervals.csv"
    output_path = project_root / "data" / "processed" / "learners_binned.csv"
    
    # Validate input file existence
    if not input_path.exists():
        error(f"Input file not found: {input_path}. Please run compute_intervals.py (T023) first.")
        sys.exit(1)
    
    info(f"Loading learner intervals from: {input_path}")
    try:
        learner_intervals_df = load_learner_intervals(str(input_path))
    except Exception as e:
        error(f"Failed to load learner intervals: {e}")
        sys.exit(1)
    
    if learner_intervals_df.empty:
        error("Loaded learner intervals dataframe is empty. Cannot proceed with binning.")
        sys.exit(1)
    
    info(f"Loaded {len(learner_intervals_df)} learner records for binning.")
    
    # Perform binning
    info("Assigning feedback timing groups...")
    binned_df = bin_feedback_groups(learner_intervals_df)
    
    if binned_df is None or binned_df.empty:
        error("Binning process resulted in an empty or None dataframe.")
        sys.exit(1)
    
    # Validate output columns
    required_cols = ['learner_id', 'median_interval_hours', 'feedback_group']
    missing_cols = [col for col in required_cols if col not in binned_df.columns]
    if missing_cols:
        error(f"Binned dataframe missing required columns: {missing_cols}")
        sys.exit(1)
    
    info(f"Binning complete. {len(binned_df)} records assigned to groups.")
    info(f"Group distribution:\n{binned_df['feedback_group'].value_counts()}")
    
    # Save output
    info(f"Saving binned learners to: {output_path}")
    try:
        save_binned_data(binned_df, str(output_path))
    except Exception as e:
        error(f"Failed to save binned learners data: {e}")
        sys.exit(1)
    
    info(f"Successfully generated {output_path}")
    logger.info("T026 task completed successfully.")

if __name__ == "__main__":
    main()