import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Set
import sys
import pandas as pd
import numpy as np

from config import get_project_root, get_raw_data_dir, get_processed_data_dir
from logging_config import setup_logging, get_logger, log_pipeline_step, log_exclusion

def load_stimuli() -> pd.DataFrame:
    """
    Load the stimuli dataset from data/raw/stimuli.csv.
    Returns a DataFrame containing stimulus metadata.
    """
    root = get_project_root()
    raw_dir = get_raw_data_dir(root)
    stimuli_path = raw_dir / "stimuli.csv"
    
    if not stimuli_path.exists():
        raise FileNotFoundError(f"Stimuli file not found at {stimuli_path}. "
                                "Please run 01_generate_stimuli.py first.")
    
    return pd.read_csv(stimuli_path)

def load_ratings() -> pd.DataFrame:
    """
    Load the ratings dataset from data/raw/ratings.csv.
    Returns a DataFrame containing participant ratings.
    """
    root = get_project_root()
    raw_dir = get_raw_data_dir(root)
    ratings_path = raw_dir / "ratings.csv"
    
    if not ratings_path.exists():
        raise FileNotFoundError(f"Ratings file not found at {ratings_path}. "
                                "Please run 02_simulate_ratings.py first.")
    
    return pd.read_csv(ratings_path)

def detect_straight_lining(stimuli_df: pd.DataFrame, ratings_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Detect participants who provided identical ratings across all stimuli (straight-lining).
    
    A participant is flagged if:
    1. They have ratings for the full set of stimuli (24 in this study).
    2. The variance of their ratings is exactly 0.0.
    
    Args:
        stimuli_df: DataFrame with stimulus metadata (must contain 'stimulus_id').
        ratings_df: DataFrame with ratings (must contain 'prolific_id', 'stimulus_id', 'rating').
        
    Returns:
        List of dictionaries with exclusion details for flagged participants.
    """
    logger = get_logger()
    log_pipeline_step(logger, "Starting straight-lining detection")
    
    # Ensure we are working with the expected columns
    required_cols = {'prolific_id', 'stimulus_id', 'rating'}
    if not required_cols.issubset(ratings_df.columns):
        raise ValueError(f"Ratings DataFrame missing required columns: {required_cols - set(ratings_df.columns)}")
    
    # Determine the total number of unique stimuli expected
    total_stimuli_count = stimuli_df['stimulus_id'].nunique()
    logger.info(f"Total unique stimuli expected: {total_stimuli_count}")
    
    # Group by participant
    straight_liners = []
    
    # Group by participant and check variance
    # We calculate variance per participant
    participant_stats = ratings_df.groupby('prolific_id').agg(
        n_stimuli=('stimulus_id', 'nunique'),
        rating_variance=('rating', 'var')
    ).reset_index()
    
    # Filter for participants who rated all stimuli AND have zero variance
    # Note: var() returns NaN for single value, but we expect 24 values here.
    # We check for exactly 0.0 variance.
    flagged = participant_stats[
        (participant_stats['n_stimuli'] == total_stimuli_count) & 
        (participant_stats['rating_variance'] == 0.0)
    ]
    
    for _, row in flagged.iterrows():
        pid = row['prolific_id']
        reason = f"Straight-lining detected: Zero variance across {total_stimuli_count} stimuli."
        straight_liners.append({
            "prolific_id": pid,
            "exclusion_reason": reason,
            "n_stimuli_rated": int(row['n_stimuli']),
            "rating_variance": float(row['rating_variance'])
        })
        log_exclusion(logger, pid, reason)
    
    log_pipeline_step(logger, f"Straight-lining detection complete. Flagged {len(straight_liners)} participants.")
    return straight_liners

def save_cleaning_log(exclusion_records: List[Dict[str, Any]]) -> Path:
    """
    Save the cleaning log (exclusion records) to data/processed/cleaning_log.csv.
    
    Args:
        exclusion_records: List of dictionaries containing exclusion details.
        
    Returns:
        Path to the saved CSV file.
    """
    root = get_project_root()
    proc_dir = get_processed_data_dir(root)
    log_path = proc_dir / "cleaning_log.csv"
    
    if not exclusion_records:
        # Create an empty file with headers if no exclusions
        with open(log_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["prolific_id", "exclusion_reason", "n_stimuli_rated", "rating_variance"])
            writer.writeheader()
        logger = get_logger()
        log_pipeline_step(logger, "No exclusions found. Empty cleaning log created.")
    else:
        with open(log_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["prolific_id", "exclusion_reason", "n_stimuli_rated", "rating_variance"])
            writer.writeheader()
            writer.writerows(exclusion_records)
    
    logger = get_logger()
    log_pipeline_step(logger, f"Cleaning log saved to {log_path}")
    return log_path

def main():
    """
    Main entry point for the data cleaning pipeline.
    Loads stimuli and ratings, detects straight-lining, and saves the cleaning log.
    """
    setup_logging()
    logger = get_logger()
    logger.info("Starting data cleaning pipeline (T016)")
    
    try:
        # Load data
        logger.info("Loading stimuli...")
        stimuli_df = load_stimuli()
        
        logger.info("Loading ratings...")
        ratings_df = load_ratings()
        
        # Detect straight-lining
        logger.info("Running straight-lining detection...")
        exclusion_records = detect_straight_lining(stimuli_df, ratings_df)
        
        # Save results
        logger.info("Saving cleaning log...")
        output_path = save_cleaning_log(exclusion_records)
        
        logger.info(f"Pipeline complete. Output: {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
