"""
Data Cleaning Module for US3 (User Story 3).

Implements straight-lining detection and participant exclusion logic
as defined in task T045.

Logic:
- Exclude participants if variance of ratings < 0.1
- Exclude participants if >90% of their ratings are identical
"""
import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Tuple, Set

import pandas as pd
import numpy as np

# Import project configuration
from config import seed_everything
from logging_config import setup_logging, get_logger

# Ensure reproducibility
seed_everything(42)

def load_survey_data(input_path: Path) -> pd.DataFrame:
    """
    Load raw survey responses from CSV.
    
    Args:
        input_path: Path to the input CSV file.
        
    Returns:
        DataFrame containing the survey responses.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If required columns are missing.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    required_cols = ['participant_id', 'rating']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    return df

def detect_straight_lining(df: pd.DataFrame, variance_threshold: float = 0.1, 
                           identical_ratio_threshold: float = 0.90) -> Tuple[pd.DataFrame, Set[int]]:
    """
    Detect and exclude straight-lining participants.
    
    Logic:
    1. Group by participant_id.
    2. Calculate variance of ratings for each participant.
    3. Calculate the ratio of the most frequent rating to the total count for each participant.
    4. Exclude participants where:
       - variance < variance_threshold (e.g., 0.1)
       - OR max_identical_ratio > identical_ratio_threshold (e.g., 0.90)
    
    Args:
        df: DataFrame with 'participant_id' and 'rating'.
        variance_threshold: Minimum variance required to keep a participant.
        identical_ratio_threshold: Maximum ratio of identical ratings allowed.
        
    Returns:
        Tuple of (cleaned_df, set_of_excluded_participant_ids).
    """
    # Ensure rating is numeric
    df = df.copy()
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
    df = df.dropna(subset=['rating'])
    
    if df.empty:
        logging.warning("No valid ratings found in input data.")
        return df, set()

    # Group by participant
    participant_stats = df.groupby('participant_id')['rating'].agg(['var', 'count'])
    
    # Calculate mode count (most frequent value count) to determine identical ratio
    # We need to apply a custom function to get the max count of any single rating
    def max_identical_count(group):
        return group.value_counts().max()
    
    max_counts = df.groupby('participant_id')['rating'].apply(max_identical_count)
    participant_stats['max_identical_count'] = max_counts
    participant_stats['identical_ratio'] = participant_stats['max_identical_count'] / participant_stats['count']
    
    # Identify excluded participants
    # Condition 1: Variance < threshold
    low_variance = participant_stats[participant_stats['var'] < variance_threshold].index
    
    # Condition 2: Identical ratio > threshold
    high_identical = participant_stats[participant_stats['identical_ratio'] > identical_ratio_threshold].index
    
    excluded_ids = set(low_variance.union(high_identical))
    
    logging.info(f"Detected {len(excluded_ids)} straight-lining participants out of {participant_stats.shape[0]}")
    
    if excluded_ids:
        logging.warning(f"Excluding participants: {sorted(list(excluded_ids))}")
    
    # Filter the original dataframe
    cleaned_df = df[~df['participant_id'].isin(excluded_ids)].reset_index(drop=True)
    
    return cleaned_df, excluded_ids

def save_cleaned_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the cleaned dataframe to CSV.
    
    Args:
        df: Cleaned DataFrame.
        output_path: Path to save the output CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logging.info(f"Saved cleaned data to {output_path} ({len(df)} rows)")

def main():
    """
    Main entry point for T045: Execute Data Cleaning.
    
    Reads from data/survey/pilot_responses_real.csv
    Writes to data/processed/cleaned_responses.csv
    """
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    # Define paths
    base_dir = Path(__file__).parent.parent
    input_path = base_dir / "data" / "survey" / "pilot_responses_real.csv"
    output_path = base_dir / "data" / "processed" / "cleaned_responses.csv"
    
    parser = argparse.ArgumentParser(description="Execute Data Cleaning (T045)")
    parser.add_argument("--input", type=str, default=str(input_path), 
                        help="Path to input CSV (default: data/survey/pilot_responses_real.csv)")
    parser.add_argument("--output", type=str, default=str(output_path),
                        help="Path to output CSV (default: data/processed/cleaned_responses.csv)")
    parser.add_argument("--var-threshold", type=float, default=0.1,
                        help="Variance threshold for straight-lining detection")
    parser.add_argument("--identical-threshold", type=float, default=0.90,
                        help="Identical rating ratio threshold")
    
    args = parser.parse_args()
    
    input_p = Path(args.input)
    output_p = Path(args.output)
    
    if not input_p.exists():
        logger.error(f"Input file not found: {input_p}")
        logger.error("Ensure pilot data has been collected (T026a) before running this task.")
        sys.exit(1)
    
    try:
        logger.info(f"Loading data from {input_p}")
        df = load_survey_data(input_p)
        logger.info(f"Loaded {len(df)} rows")
        
        logger.info(f"Running straight-lining detection (var < {args.var_threshold}, identical > {args.identical_threshold})")
        cleaned_df, excluded_ids = detect_straight_lining(
            df, 
            variance_threshold=args.var_threshold, 
            identical_ratio_threshold=args.identical_threshold
        )
        
        if len(excluded_ids) > 0:
            logger.warning(f"Excluded {len(excluded_ids)} participants due to straight-lining.")
        else:
            logger.info("No straight-lining participants detected.")
        
        logger.info(f"Saving cleaned data to {output_p}")
        save_cleaned_data(cleaned_df, output_p)
        
        logger.info("Data cleaning completed successfully.")
        
    except Exception as e:
        logger.error(f"Data cleaning failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
