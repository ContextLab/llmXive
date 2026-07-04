"""
apply_exclusions.py

Implements logic to filter learners based on specific criteria:
1. Exclude learners with no recorded forum interactions (T018).
2. Save filtered data to disk.

This file is extended to support T020's requirement to generate the final CSV.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from logging_config import get_logger, info, error, warning

def load_raw_learner_data(data_path=None, df=None):
    """
    Load raw learner data.
    If df is provided, returns it. If data_path is provided, loads from CSV.
    """
    if df is not None:
        return df
    if data_path and os.path.exists(data_path):
        return pd.read_csv(data_path)
    return None

def filter_no_forum_interactions(df_learners):
    """
    T018: Exclude learners with no recorded forum interactions.
    
    Assumes the dataframe contains columns indicating forum activity, 
    e.g., 'id_forum_post' or a flag 'has_forum_interaction'.
    If the column 'id_forum_post' exists, we keep rows where it is not null.
    If the dataframe is aggregated per student, we check for a count > 0.
    
    Logic:
    - If 'id_forum_post' is in columns: Keep rows where it is not NaN.
    - If 'forum_interaction_count' is in columns: Keep rows where count > 0.
    - Otherwise, assume all are valid (log warning).
    """
    logger = get_logger("apply_exclusions")
    original_count = len(df_learners)
    
    if 'id_forum_post' in df_learners.columns:
        # Filter out rows where forum post ID is missing
        # Note: This might be a row-level filter if the data is event-level,
        # or if it's student-level, it means the student had at least one post.
        # Assuming student-level data where 'id_forum_post' is the first post or a flag.
        # If it's a list or NaN, we drop NaNs.
        df_filtered = df_learners.dropna(subset=['id_forum_post'])
        excluded_count = original_count - len(df_filtered)
        info(logger, f"Excluded {excluded_count} learners with no forum interactions (id_forum_post null).")
        return df_filtered
    
    elif 'forum_interaction_count' in df_learners.columns:
        df_filtered = df_learners[df_learners['forum_interaction_count'] > 0]
        excluded_count = original_count - len(df_filtered)
        info(logger, f"Excluded {excluded_count} learners with no forum interactions (count=0).")
        return df_filtered
    
    else:
        warning(logger, "No forum interaction column found. Assuming all learners have interactions.")
        return df_learners

def save_filtered_data(df, output_path):
    """
    Saves the filtered dataframe to a CSV file.
    """
    logger = get_logger("apply_exclusions")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    info(logger, f"Saved filtered data to {output_path} ({len(df)} rows).")

def main():
    # Standalone execution for testing
    logger = get_logger("apply_exclusions_main")
    info(logger, "Running apply_exclusions as main (test mode).")
    # This would typically load from a path provided by T020
    return 0

if __name__ == "__main__":
    sys.exit(main())
