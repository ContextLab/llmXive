"""
Ground Truth Labeling Module for User Story 3.

Implements logic to label cognitive load based on search time (median split)
when independent ground truth is unavailable. Handles 'UNFULFILLABLE' proxies
by excluding them from labeling and logging the exclusion.
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path for imports if running as script
if 'code' not in sys.path:
    code_root = Path(__file__).resolve().parent.parent
    if code_root.exists():
        sys.path.insert(0, str(code_root))

from config import load_config
from logging_config import get_logger

logger = get_logger(__name__)

# Constants
FEATURES_PATH = Path("data/processed/features.csv")
LABELED_OUTPUT_PATH = Path("data/processed/labeled_features.csv")
LIMITATIONS_PATH = Path("results/limitations.md")
METRICS_PATH = Path("results/classification_metrics.csv")


def load_config() -> Dict[str, Any]:
    """
    Load configuration from code/config.yaml.
    Returns empty dict if file missing (caller should handle defaults).
    """
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        return {}
    return load_config()


def load_search_time_data() -> Optional[pd.DataFrame]:
    """
    Load the preprocessed features dataset containing search_time.
    Returns None if file is missing or invalid.
    """
    if not FEATURES_PATH.exists():
        logger.error(f"Features file not found: {FEATURES_PATH}")
        return None

    try:
        df = pd.read_csv(FEATURES_PATH)
        logger.info(f"Loaded {len(df)} rows from {FEATURES_PATH}")
        return df
    except Exception as e:
        logger.error(f"Failed to load features data: {e}")
        return None


def label_by_median_split(df: pd.DataFrame, column: str = "search_time") -> pd.DataFrame:
    """
    Label rows based on a median split of the specified column.
    - If value > median: Label = 1 (High Load)
    - If value <= median: Label = 0 (Low Load)
    - If value is NaN, 'UNFULFILLABLE', or missing: Label = -1 (Excluded)

    Args:
        df: Input DataFrame.
        column: The column to use for splitting (default: 'search_time').

    Returns:
        DataFrame with a new 'load_label' column.
    """
    if column not in df.columns:
        logger.error(f"Column '{column}' not found in DataFrame. Available: {list(df.columns)}")
        df['load_label'] = -1
        return df

    # Create a copy to avoid SettingWithCopyWarning
    df = df.copy()

    # Identify valid numeric values
    # Handle potential string representations of 'UNFULFILLABLE' or NaN
    valid_mask = df[column].notna() & (df[column] != 'UNFULFILLABLE')
    
    if valid_mask.sum() == 0:
        logger.warning(f"All values in '{column}' are invalid or missing. No labels generated.")
        df['load_label'] = -1
        return df

    valid_values = df.loc[valid_mask, column].astype(float)
    median_val = valid_values.median()
    logger.info(f"Calculated median for '{column}': {median_val:.4f}")

    # Initialize labels as -1 (Excluded)
    df['load_label'] = -1

    # Apply median split logic
    # High Load: strictly greater than median
    high_load_mask = valid_mask & (valid_values > median_val)
    df.loc[high_load_mask, 'load_label'] = 1

    # Low Load: less than or equal to median
    low_load_mask = valid_mask & (valid_values <= median_val)
    df.loc[low_load_mask, 'load_label'] = 0

    # Log exclusion stats
    excluded_count = (df['load_label'] == -1).sum()
    logger.info(f"Labeling complete. High Load: {high_load_mask.sum()}, Low Load: {low_load_mask.sum()}, Excluded: {excluded_count}")

    return df


def save_labeled_data(df: pd.DataFrame, output_path: Path = LABELED_OUTPUT_PATH) -> bool:
    """
    Save the labeled DataFrame to CSV.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Labeled data saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save labeled data: {e}")
        return False


def write_limitations_note(output_path: Path = LIMITATIONS_PATH) -> bool:
    """
    Write the limitations documentation file.
    """
    content = """# Limitations: Ground Truth Proxy

This project uses search-time as a proxy for cognitive load during visual search tasks.

**Reason for Proxy**: An independent, direct measure of cognitive load (e.g., dual-task performance, subjective rating) was not available in the source dataset.

**Labeling Method**: Ground truth labels for classification were generated via a median split of the `search_time` metric.
- **High Load (1)**: Search time > Median
- **Low Load (0)**: Search time <= Median

**Implications**: 
- This is a relative measure, not an absolute ground truth.
- The classification performance reflects the model's ability to distinguish between faster and slower search trials based on pupil dynamics, rather than an absolute cognitive load state.
- Results should be interpreted as "Search-Time Estimation" capabilities.
"""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
        logger.info(f"Limitations note written to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to write limitations note: {e}")
        return False


def update_classification_metrics(metrics_path: Path = METRICS_PATH) -> bool:
    """
    Update the classification metrics CSV headers to include 'ground_truth_source'.
    If the file exists, ensures the column is present. If not, creates it with headers.
    """
    try:
        if not metrics_path.exists():
            # Create new file with headers
            df = pd.DataFrame(columns=['threshold', 'accuracy', 'precision', 'recall', 'auc', 'ground_truth_source'])
            df.to_csv(metrics_path, index=False)
            logger.info(f"Created new metrics file at {metrics_path}")
        else:
            # Check if column exists
            df = pd.read_csv(metrics_path)
            if 'ground_truth_source' not in df.columns:
                df['ground_truth_source'] = "Search-Time Estimation"
                df.to_csv(metrics_path, index=False)
                logger.info(f"Updated metrics file at {metrics_path} with 'ground_truth_source' column")
            else:
                logger.info(f"Metrics file at {metrics_path} already has 'ground_truth_source' column")
        return True
    except Exception as e:
        logger.error(f"Failed to update classification metrics: {e}")
        return False


def main():
    """
    Main entry point for ground truth labeling.
    1. Load config (for defaults if needed).
    2. Load features data.
    3. Handle 'UNFULFILLABLE' search_time (log exclusion).
    4. Perform median split labeling.
    5. Save labeled data.
    6. Write limitations documentation.
    7. Update metrics schema.
    """
    logger.info("Starting Ground Truth Labeling (T029)...")
    
    # 1. Load Config
    config = load_config()
    
    # 2. Load Data
    df = load_search_time_data()
    if df is None:
        logger.error("Cannot proceed without feature data.")
        sys.exit(1)

    # 3 & 4. Label by Median Split
    # The function handles 'UNFULFILLABLE' strings and NaNs internally
    labeled_df = label_by_median_split(df, column="search_time")

    # 5. Save Labeled Data
    if not save_labeled_data(labeled_df):
        logger.error("Failed to save labeled data.")
        sys.exit(1)

    # 6. Write Limitations
    if not write_limitations_note():
        logger.warning("Failed to write limitations note (non-fatal).")

    # 7. Update Metrics Schema
    if not update_classification_metrics():
        logger.warning("Failed to update metrics schema (non-fatal).")

    logger.info("Ground Truth Labeling (T029) completed successfully.")


if __name__ == "__main__":
    main()