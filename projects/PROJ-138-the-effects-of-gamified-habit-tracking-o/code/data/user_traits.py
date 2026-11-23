"""
Extract user-level traits from the raw/synthetic data to prepare for merging.

This script reads the raw generated data (from T013a) and extracts the static
user attributes (gamified_status, conscientiousness_score, need_for_achievement)
into a separate CSV file `data/processed/user_traits.csv`.

This is a prerequisite for T017 (merge) because the raw data contains
longitudinal logs where user traits are repeated per row. We aggregate them
to unique users to avoid redundancy and ensure a clean 1:N merge.
"""
import os
import sys
import pandas as pd
from code.utils.logging import pipeline_logger
from code.utils.config import set_random_seed

INPUT_PATH = "data/raw/synthetic_data.csv"
OUTPUT_PATH = "data/processed/user_traits.csv"

def extract_user_traits():
    """
    Extracts unique user traits from the raw dataset.
    """
    set_random_seed(42)
    logger = pipeline_logger

    logger.info(f"Loading raw data from {INPUT_PATH}")
    if not os.path.exists(INPUT_PATH):
        raise FileNotFoundError(
            f"Input file {INPUT_PATH} not found. "
            "Please ensure T013a (synthetic_generator) has run successfully."
        )
    
    df_raw = pd.read_csv(INPUT_PATH)

    # Identify user-level columns
    # Based on T013a output: User_ID, gamified_status, conscientiousness_score, need_for_achievement
    # plus log-level columns: date, event_type
    
    user_level_cols = ['User_ID', 'gamified_status', 'conscientiousness_score', 'need_for_achievement']
    missing_cols = [col for col in user_level_cols if col not in df_raw.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required user-level columns in raw data: {missing_cols}")

    # Select only user-level columns and drop duplicates
    logger.info("Extracting unique user records...")
    df_users = df_raw[user_level_cols].drop_duplicates(subset=['User_ID'])

    # Ensure types are consistent
    df_users['User_ID'] = df_users['User_ID'].astype(str)
    
    # Validate non-nulls for critical traits
    if df_users['gamified_status'].isnull().any():
        logger.warning("Found null gamified_status values. Dropping those users.")
        df_users = df_users.dropna(subset=['gamified_status'])
    
    if df_users['conscientiousness_score'].isnull().any():
        logger.warning("Found null conscientiousness_score values. Dropping those users.")
        df_users = df_users.dropna(subset=['conscientiousness_score'])

    if df_users['need_for_achievement'].isnull().any():
        logger.warning("Found null need_for_achievement values. Dropping those users.")
        df_users = df_users.dropna(subset=['need_for_achievement'])

    # Write to disk
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df_users.to_csv(OUTPUT_PATH, index=False)

    logger.info(f"Successfully wrote user traits to {OUTPUT_PATH}")
    logger.info(f"Total unique users: {len(df_users)}")

    return df_users

def main():
    """Entry point for the user traits extraction script."""
    try:
        extract_user_traits()
        return 0
    except Exception as e:
        pipeline_logger.error(f"User traits extraction failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
