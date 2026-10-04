import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

from utils.logging import get_logger
from config import get_config

def get_logger_wrapper(func):
    """Decorator to add logger to function context."""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        return func(logger, *args, **kwargs)
    return wrapper

@get_logger_wrapper
def calculate_missing_ratio(
    logger: logging.Logger,
    participant_data: pd.DataFrame,
    gaze_column: str = "gaze_coordinates"
) -> float:
    """
    Calculate the ratio of missing gaze data for a single participant's record.
    
    Args:
        logger: Logger instance.
        participant_data: DataFrame containing gaze records for one participant.
        gaze_column: Name of the column containing gaze coordinates.
        
    Returns:
        float: Ratio of missing values (0.0 to 1.0).
    """
    if participant_data.empty:
        logger.warning("Participant data is empty. Returning 1.0 missing ratio.")
        return 1.0
    
    # Check if the column exists
    if gaze_column not in participant_data.columns:
        logger.error(f"Column '{gaze_column}' not found in participant data.")
        return 1.0
    
    # Count non-null entries
    non_null_count = participant_data[gaze_column].notna().sum()
    total_count = len(participant_data)
    
    if total_count == 0:
        return 1.0
        
    missing_ratio = 1.0 - (non_null_count / total_count)
    return missing_ratio

@get_logger_wrapper
def evaluate_participant_exclusion(
    logger: logging.Logger,
    data_path: Path,
    exclusion_threshold: float = 0.20,
    gaze_column: str = "gaze_coordinates"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Evaluate participants for exclusion based on missing gaze data ratio.
    
    Excludes participants where the ratio of missing gaze data exceeds the threshold.
    
    Args:
        logger: Logger instance.
        data_path: Path to the processed features CSV.
        exclusion_threshold: Maximum allowed ratio of missing data (default 0.20).
        gaze_column: Column name to check for missing values.
        
    Returns:
        Tuple containing:
            - Filtered DataFrame with excluded participants removed.
            - Dictionary with exclusion statistics.
    """
    logger.info(f"Loading data from {data_path}")
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
        
    df = pd.read_csv(data_path)
    
    if df.empty:
        logger.warning("Input DataFrame is empty.")
        return df, {"excluded_count": 0, "total_count": 0, "exclusion_rate": 0.0}
    
    # Ensure participant_id column exists
    if "participant_id" not in df.columns:
        # If no participant_id, assume each row is a participant or fail
        # Based on typical eye-tracking structure, we group by a unique ID.
        # If the data is already aggregated per participant in rows, we check the row directly.
        # Assuming 'participant_id' is present as per data-model.md requirements for US1.
        logger.error("Missing 'participant_id' column in features data.")
        raise ValueError("Data must contain 'participant_id' column for exclusion logic.")
    
    # Group by participant to calculate missing ratio per participant
    # We assume the data is in long format (multiple rows per participant)
    # or wide format where we need to aggregate.
    # Standard approach: Calculate missing ratio per participant_id group.
    
    participant_stats = []
    
    for pid, group in df.groupby("participant_id"):
        missing_ratio = calculate_missing_ratio(logger, group, gaze_column)
        participant_stats.append({
            "participant_id": pid,
            "missing_ratio": missing_ratio,
            "total_records": len(group)
        })
    
    stats_df = pd.DataFrame(participant_stats)
    
    # Identify excluded participants
    excluded_mask = stats_df["missing_ratio"] > exclusion_threshold
    excluded_participants = stats_df.loc[excluded_mask, "participant_id"].tolist()
    included_participants = stats_df.loc[~excluded_mask, "participant_id"].tolist()
    
    logger.info(f"Total participants: {len(stats_df)}")
    logger.info(f"Excluded participants (>{exclusion_threshold*100}% missing): {len(excluded_participants)}")
    logger.info(f"Included participants: {len(included_participants)}")
    
    if excluded_participants:
        logger.warning(f"Excluding participants: {excluded_participants}")
    
    # Filter the main dataframe
    filtered_df = df[df["participant_id"].isin(included_participants)].reset_index(drop=True)
    
    exclusion_rate = len(excluded_participants) / len(stats_df) if len(stats_df) > 0 else 0.0
    
    stats_summary = {
        "total_participants": len(stats_df),
        "excluded_count": len(excluded_participants),
        "included_count": len(included_participants),
        "exclusion_rate": exclusion_rate,
        "threshold_used": exclusion_threshold,
        "excluded_ids": excluded_participants,
        "included_ids": included_participants
    }
    
    return filtered_df, stats_summary

@get_logger_wrapper
def run_exclusion_pipeline(
    logger: logging.Logger,
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    stats_output_path: Optional[Path] = None,
    exclusion_threshold: float = 0.20
) -> None:
    """
    Main entry point for the participant exclusion pipeline.
    
    Reads processed features, applies exclusion logic, saves cleaned data and stats.
    """
    config = get_config()
    
    if input_path is None:
        input_path = config.PROCESSED_FEATURES_PATH
    if output_path is None:
        output_path = config.PROCESSED_FEATURES_PATH.with_name("features_cleaned.csv")
    if stats_output_path is None:
        stats_output_path = config.PROCESSED_FEATURES_PATH.with_name("exclusion_stats.json")
        
    logger.info(f"Starting exclusion pipeline for {input_path}")
    
    try:
        cleaned_df, stats = evaluate_participant_exclusion(
            logger, 
            input_path, 
            exclusion_threshold=exclusion_threshold
        )
        
        # Save cleaned data
        logger.info(f"Saving cleaned data to {output_path}")
        cleaned_df.to_csv(output_path, index=False)
        
        # Save statistics
        logger.info(f"Saving exclusion stats to {stats_output_path}")
        with open(stats_output_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Exclusion pipeline complete. Exclusion rate: {stats['exclusion_rate']:.2%}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

def main():
    """CLI entry point."""
    setup_logging()
    logger = get_logger(__name__)
    run_exclusion_pipeline(logger)

if __name__ == "__main__":
    # Ensure logging is set up before running main
    from utils.logging import setup_logging
    setup_logging()
    main()
