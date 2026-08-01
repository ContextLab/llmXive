"""
Generate the final binned learners dataset (T026).

This script orchestrates the loading of learner intervals, assignment of
feedback groups, and saving of the final `data/processed/learners_binned.csv`.
"""
import os
import sys
from pathlib import Path

# Ensure the code directory is in the path for relative imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from bin_feedback_groups import load_learner_intervals, assign_feedback_group, bin_feedback_groups, save_binned_data
from logging_config import get_logger, info, error, warning

# Project root relative to code/
PROJECT_ROOT = code_dir.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Output file path as per tasks.md
OUTPUT_FILE = DATA_PROCESSED_DIR / "learners_binned.csv"

# Input file path (produced by T023/T024/T025 pipeline)
INPUT_FILE = DATA_PROCESSED_DIR / "learner_intervals.csv"

def main():
    logger = get_logger(__name__)
    info("Starting T026: Generate binned learners dataset")

    # Ensure output directory exists
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if not INPUT_FILE.exists():
        error(f"Input file not found: {INPUT_FILE}. "
              "Please run compute_intervals.py and compute_learner_medians.py first.")
        sys.exit(1)

    try:
        # 1. Load learner intervals (median calculated per learner)
        # The bin_feedback_groups module expects a dataframe with 'learner_id' and 'median_interval'
        df_intervals = load_learner_intervals(INPUT_FILE)
        
        if df_intervals is None or df_intervals.empty:
            error("No data loaded from intervals file.")
            sys.exit(1)

        info(f"Loaded {len(df_intervals)} learner records with intervals.")

        # 2. Assign feedback groups based on median intervals
        # This applies the logic: <2h -> Immediate, 2h-48h -> Delayed, >48h -> Variable
        df_binned = bin_feedback_groups(df_intervals)

        # 3. Save the final dataset
        save_binned_data(df_binned, str(OUTPUT_FILE))

        info(f"Successfully generated {OUTPUT_FILE} with {len(df_binned)} records.")
        
        # Quick validation
        if 'feedback_group' not in df_binned.columns:
            error("Output missing 'feedback_group' column.")
            sys.exit(1)
        
        unique_groups = df_binned['feedback_group'].unique()
        info(f"Feedback groups assigned: {sorted(unique_groups)}")

    except Exception as e:
        error(f"Failed to generate binned learners: {e}")
        raise

if __name__ == "__main__":
    main()
