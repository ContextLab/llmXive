import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np

from config import get_config
from utils.logging import get_logger

# Constants
MISSING_THRESHOLD = 0.20  # Exclude if >20% missing gaze data


def get_logger_wrapper():
    """Wrapper to get logger for this module."""
    return get_logger(__name__)


def calculate_missing_ratio(gaze_data: pd.Series) -> float:
    """
    Calculate the ratio of missing (NaN) gaze data points.
    
    Args:
        gaze_data: Series containing gaze coordinates or fixation data.
        
    Returns:
        Float between 0.0 and 1.0 representing the proportion of missing data.
    """
    if gaze_data is None or len(gaze_data) == 0:
        return 1.0
    
    missing_count = gaze_data.isna().sum()
    total_count = len(gaze_data)
    
    if total_count == 0:
        return 1.0
        
    return float(missing_count / total_count)


def evaluate_participant_exclusion(
    df: pd.DataFrame,
    gaze_columns: List[str],
    participant_col: str = 'participant_id',
    threshold: float = MISSING_THRESHOLD
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Evaluate participants for exclusion based on missing gaze data ratio.
    
    Args:
        df: DataFrame containing participant data.
        gaze_columns: List of column names representing gaze data points.
        participant_col: Name of the column identifying participants.
        threshold: Maximum allowed missing ratio (default 0.20).
        
    Returns:
        Tuple of (filtered_df, exclusion_stats)
    """
    logger = get_logger_wrapper()
    
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty result.")
        return df, {
            'total_participants': 0,
            'excluded_count': 0,
            'kept_count': 0,
            'exclusion_rate': 0.0,
            'threshold': threshold,
            'excluded_participants': []
        }
    
    # Calculate missing ratio per participant
    missing_ratios = []
    participant_ids = df[participant_col].unique()
    exclusion_details = {}
    
    for pid in participant_ids:
        participant_data = df[df[participant_col] == pid]
        
        # Aggregate missing data across all gaze columns for this participant
        all_gaze_values = pd.concat([participant_data[col] for col in gaze_columns if col in participant_data.columns], ignore_index=True)
        
        ratio = calculate_missing_ratio(all_gaze_values)
        missing_ratios.append(ratio)
        
        exclusion_details[pid] = {
            'missing_ratio': ratio,
            'excluded': ratio > threshold
        }
    
    # Determine which participants to keep
    excluded_pids = [pid for pid, details in exclusion_details.items() if details['excluded']]
    kept_pids = [pid for pid, details in exclusion_details.items() if not details['excluded']]
    
    # Filter DataFrame
    filtered_df = df[df[participant_col].isin(kept_pids)].reset_index(drop=True)
    
    # Calculate statistics
    total_count = len(participant_ids)
    excluded_count = len(excluded_pids)
    kept_count = len(kept_pids)
    exclusion_rate = excluded_count / total_count if total_count > 0 else 0.0
    
    stats = {
        'total_participants': total_count,
        'excluded_count': excluded_count,
        'kept_count': kept_count,
        'exclusion_rate': exclusion_rate,
        'threshold': threshold,
        'excluded_participants': excluded_pids,
        'details': exclusion_details
    }
    
    logger.info(f"Participant Exclusion Summary:")
    logger.info(f"  Total participants: {total_count}")
    logger.info(f"  Excluded (>{threshold*100}% missing): {excluded_count}")
    logger.info(f"  Kept: {kept_count}")
    logger.info(f"  Exclusion rate: {exclusion_rate:.2%}")
    
    if excluded_count > 0:
        logger.warning(f"Excluded participants: {excluded_pids}")
    
    return filtered_df, stats


def run_exclusion_pipeline(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    stats_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the participant exclusion pipeline on the raw dataset.
    
    Args:
        input_path: Path to input dataset (defaults to data/raw/processed_data.csv).
        output_path: Path to save filtered dataset (defaults to data/processed/filtered_data.csv).
        stats_path: Path to save exclusion statistics (defaults to data/processed/exclusion_stats.json).
        
    Returns:
        Dictionary containing exclusion statistics.
    """
    logger = get_logger_wrapper()
    config = get_config()
    
    # Resolve paths
    if input_path is None:
        input_path = str(config.DATA_PROCESSED_DIR / "raw_data_cleaned.csv")
    if output_path is None:
        output_path = str(config.DATA_PROCESSED_DIR / "filtered_data.csv")
    if stats_path is None:
        stats_path = str(config.DATA_PROCESSED_DIR / "exclusion_stats.json")
    
    # Ensure output directories exist
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(stats_path).parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading data from: {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                              "Please ensure data download and validation steps are complete.")
    
    # Load data
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load input data: {e}")
    
    if df.empty:
        logger.warning("Input data is empty.")
        return {
            'total_participants': 0,
            'excluded_count': 0,
            'kept_count': 0,
            'exclusion_rate': 0.0,
            'threshold': MISSING_THRESHOLD,
            'excluded_participants': [],
            'error': 'Empty input data'
        }
    
    # Identify gaze columns (columns containing 'gaze' or 'fixation' in name, or numeric columns with NaN)
    # Common gaze column patterns in eye-tracking data
    gaze_candidates = [col for col in df.columns if any(keyword in col.lower() for keyword in ['gaze', 'fixation', 'x', 'y', 'px', 'py', 'coord'])]
    
    # If no specific gaze columns found, assume all numeric columns are relevant
    if not gaze_candidates:
        gaze_candidates = [col for col in df.select_dtypes(include=[np.number]).columns]
    
    # Fallback to all columns if still empty (unlikely)
    if not gaze_candidates:
        gaze_candidates = list(df.columns)
        logger.warning(f"No specific gaze columns detected. Using all columns for missing data calculation: {gaze_candidates}")
    
    logger.info(f"Checking missing data in columns: {gaze_candidates}")
    
    # Run exclusion logic
    filtered_df, stats = evaluate_participant_exclusion(
        df=df,
        gaze_columns=gaze_candidates,
        participant_col='participant_id',
        threshold=MISSING_THRESHOLD
    )
    
    # Save filtered data
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Filtered data saved to: {output_path}")
    
    # Save statistics
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2, default=str)
    logger.info(f"Exclusion statistics saved to: {stats_path}")
    
    return stats


def main():
    """Main entry point for the exclusion script."""
    logger = get_logger_wrapper()
    logger.info("Starting participant exclusion pipeline...")
    
    try:
        stats = run_exclusion_pipeline()
        logger.info("Participant exclusion pipeline completed successfully.")
        logger.info(f"Final exclusion rate: {stats['exclusion_rate']:.2%}")
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    sys.exit(main())
