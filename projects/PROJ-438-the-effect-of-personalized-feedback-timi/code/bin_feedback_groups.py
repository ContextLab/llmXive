"""
Bin students into feedback timing groups based on their median feedback interval.

Task: T025
User Story: US2
Description: Implement binning logic to assign "Immediate" (<2h), "Delayed" (2h–48h), or "Variable" (>48h) groups.
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Import from sibling modules as defined in API surface
from logging_config import get_logger, info, warning, error
from config import load_config, get_config_value

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
INPUT_FILE = DATA_PROCESSED_DIR / "learners_raw.csv"
OUTPUT_FILE = DATA_PROCESSED_DIR / "learners_binned.csv"

# Default thresholds (can be overridden by config)
DEFAULT_IMMEDIATE_THRESHOLD_HOURS = 2.0
DEFAULT_DELAYED_THRESHOLD_HOURS = 48.0

logger = get_logger(__name__)


def load_learner_intervals(input_path: Path) -> pd.DataFrame:
    """
    Load the raw learner data containing median feedback intervals.
    
    Args:
        input_path: Path to the input CSV file.
        
    Returns:
        DataFrame with learner records.
        
    Raises:
        FileNotFoundError: If input file does not exist.
        ValueError: If required columns are missing.
    """
    if not input_path.exists():
        error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    required_cols = ['learner_id', 'median_interval_hours']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        error(f"Missing required columns in {input_path}: {missing_cols}")
        raise ValueError(f"Missing required columns: {missing_cols}")
        
    logger.info(f"Loaded {len(df)} learner records from {input_path}")
    return df


def assign_feedback_group(row: pd.Series, immediate_thresh: float, delayed_thresh: float) -> str:
    """
    Assign a feedback timing group based on median interval.
    
    Rules:
    - "Immediate": < 2 hours
    - "Delayed": 2 hours <= x <= 48 hours
    - "Variable": > 48 hours
    
    Args:
        row: DataFrame row.
        immediate_thresh: Upper bound for Immediate group (hours).
        delayed_thresh: Upper bound for Delayed group (hours).
        
    Returns:
        String label for the group.
    """
    interval = row['median_interval_hours']
    
    if pd.isna(interval):
        return np.nan
        
    if interval < immediate_thresh:
        return "Immediate"
    elif interval <= delayed_thresh:
        return "Delayed"
    else:
        return "Variable"


def bin_feedback_groups(df: pd.DataFrame, immediate_thresh: float, delayed_thresh: float) -> pd.DataFrame:
    """
    Apply binning logic to the dataframe.
    
    Args:
        df: Input dataframe with median intervals.
        immediate_thresh: Threshold for Immediate group.
        delayed_thresh: Threshold for Delayed group.
        
    Returns:
        DataFrame with added 'feedback_group' column.
    """
    logger.info(f"Binning learners with thresholds: Immediate < {immediate_thresh}h, Delayed <= {delayed_thresh}h")
    
    df['feedback_group'] = df.apply(
        lambda row: assign_feedback_group(row, immediate_thresh, delayed_thresh), 
        axis=1
    )
    
    # Count distribution
    group_counts = df['feedback_group'].value_counts(dropna=False)
    info(f"Binning distribution:\n{group_counts}")
    
    total = len(df)
    for group, count in group_counts.items():
        pct = (count / total) * 100
        info(f"Group '{group}': {count} ({pct:.2f}%)")
        
    return df


def save_binned_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the binned dataframe to CSV.
    
    Args:
        df: DataFrame to save.
        output_path: Path to output file.
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
    df.to_csv(output_path, index=False)
    logger.info(f"Saved binned data to {output_path} ({len(df)} records)")


def main():
    """Main entry point for the binning script."""
    logger.info("Starting feedback group binning (Task T025)")
    
    # Load configuration
    config = load_config()
    immediate_thresh = get_config_value(config, 'binning.immediate_threshold_hours', DEFAULT_IMMEDIATE_THRESHOLD_HOURS)
    delayed_thresh = get_config_value(config, 'binning.delayed_threshold_hours', DEFAULT_DELAYED_THRESHOLD_HOURS)
    
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    try:
        df = load_learner_intervals(INPUT_FILE)
    except (FileNotFoundError, ValueError) as e:
        error(f"Failed to load data: {e}")
        sys.exit(1)
        
    # Bin groups
    df_binned = bin_feedback_groups(df, immediate_thresh, delayed_thresh)
    
    # Save output
    try:
        save_binned_data(df_binned, OUTPUT_FILE)
    except Exception as e:
        error(f"Failed to save output: {e}")
        sys.exit(1)
        
    logger.info("Feedback group binning completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
