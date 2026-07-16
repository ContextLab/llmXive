"""
Task T023: Merge Gaze and Synthetic Data Streams with Outlier Capping.

This script merges the preprocessed gaze data (from T018) with the synthetic
raw data (from T022) on participant_id and headline_id. It immediately applies
outlier capping to the cognitive_reflection_score at the 1st and 99th percentiles
as required by the specification.
"""
import os
import sys
import logging
from pathlib import Path

import pandas as pd
import numpy as np

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent))

from utils.environment_manager import setup_logging, get_paths

def load_gaze_data(gaze_path: Path) -> pd.DataFrame:
    """Load preprocessed gaze data from T018."""
    if not gaze_path.exists():
        raise FileNotFoundError(
            f"Required gaze data file not found: {gaze_path}. "
            "Ensure T018 (preprocessed_gaze.csv) has completed successfully."
        )
    logging.info(f"Loading gaze data from {gaze_path}")
    df = pd.read_csv(gaze_path)
    required_cols = ['participant_id', 'headline_id', 'fixation_duration']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Gaze data missing required columns: {missing}")
    return df

def load_synthetic_data(synthetic_path: Path) -> pd.DataFrame:
    """Load synthetic raw data from T022."""
    if not synthetic_path.exists():
        raise FileNotFoundError(
            f"Required synthetic data file not found: {synthetic_path}. "
            "Ensure T022 (synthetic_raw_data.csv) has completed successfully."
        )
    logging.info(f"Loading synthetic data from {synthetic_path}")
    df = pd.read_csv(synthetic_path)
    required_cols = ['participant_id', 'headline_id', 'belief_rating', 'cognitive_reflection_score', 'headline_text']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Synthetic data missing required columns: {missing}")
    return df

def merge_datasets(gaze_df: pd.DataFrame, synthetic_df: pd.DataFrame) -> pd.DataFrame:
    """Merge gaze and synthetic data on participant_id and headline_id."""
    logging.info("Merging datasets on participant_id and headline_id")
    # Inner join to ensure we only keep rows where both data sources exist
    merged = pd.merge(
        gaze_df,
        synthetic_df,
        on=['participant_id', 'headline_id'],
        how='inner'
    )
    logging.info(f"Merged dataset shape: {merged.shape}")
    if merged.empty:
        raise ValueError("Merge resulted in an empty dataframe. Check key alignment.")
    return merged

def apply_outlier_capping(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply outlier capping to cognitive_reflection_score at 1st and 99th percentiles.
    This is done in-place on the dataframe copy.
    """
    col = 'cognitive_reflection_score'
    if col not in df.columns:
        raise ValueError(f"Column {col} not found in merged dataframe for capping.")

    lower_bound = df[col].quantile(0.01)
    upper_bound = df[col].quantile(0.99)

    logging.info(f"Applying outlier capping to {col}: [{lower_bound:.4f}, {upper_bound:.4f}]")
    
    # Count outliers before capping
    outliers_before = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
    if outliers_before > 0:
        logging.warning(f"Found {outliers_before} outliers in {col}. Capping values.")
    
    df = df.copy()
    df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
    
    return df

def main():
    # Setup logging
    log_path = get_paths().get('log_dir', Path('logs'))
    setup_logging(log_level=logging.INFO)

    # Get paths
    paths = get_paths()
    # T018 output
    gaze_path = paths.get('preprocessed_gaze', paths['derived_dir'] / 'preprocessed_gaze.csv')
    # T022 output
    synthetic_path = paths.get('synthetic_raw', paths['derived_dir'] / 'synthetic_raw_data.csv')
    # T023 output
    output_path = paths['derived_dir'] / 'merged_dataset.csv'

    try:
        # 1. Load Data
        gaze_df = load_gaze_data(gaze_path)
        synthetic_df = load_synthetic_data(synthetic_path)

        # 2. Merge
        merged_df = merge_datasets(gaze_df, synthetic_df)

        # 3. Apply Outlier Capping (Immediate)
        merged_df = apply_outlier_capping(merged_df)

        # 4. Save Output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        merged_df.to_csv(output_path, index=False)
        logging.info(f"Successfully saved merged dataset to {output_path}")
        logging.info(f"Final shape: {merged_df.shape}")

    except FileNotFoundError as e:
        logging.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logging.error(f"Unexpected error during merge: {e}")
        raise

if __name__ == "__main__":
    main()