"""
Merge neuroimaging features with behavioral scores.

This module joins the preprocessed neuroimaging data (parcellated time-series
or derived metrics) with the NIH Toolbox Dimensional Change Card Sort (DCCS)
scores from the HCP behavioral dataset.

It ensures that only subjects present in both datasets are retained,
validates data types, and writes the merged result to the processed directory.
"""

import os
import logging
import pandas as pd
from typing import Optional, Tuple

from code.data.paths import get_processed_path, get_raw_path, ensure_dir
from code.utils.logging import log_error, log_warning, init_logging

# Initialize logger
logger = logging.getLogger(__name__)

def load_neuro_features(file_path: str) -> pd.DataFrame:
    """
    Load neuroimaging features from a CSV file.

    Expected columns: Subject_ID (str), and potentially other features
    (e.g., Mean_FD, or pre-computed variability metrics if available).

    Args:
        file_path: Path to the CSV file containing neuro features.

    Returns:
        DataFrame with neuro features.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Neuro features file not found: {file_path}")

    df = pd.read_csv(file_path)

    if 'Subject_ID' not in df.columns:
        raise ValueError(f"Neuro features file missing required column 'Subject_ID': {file_path}")

    # Ensure Subject_ID is string for consistent merging
    df['Subject_ID'] = df['Subject_ID'].astype(str).str.strip()

    logger.info(f"Loaded neuro features: {len(df)} subjects from {file_path}")
    return df

def load_behavioral_scores(file_path: str) -> pd.DataFrame:
    """
    Load behavioral scores from the HCP behavioral CSV.

    Specifically extracts the Dimensional Change Card Sort (DCCS) score.
    In HCP 1200 release, this is typically in the 'NIH_DCCS_TotalScore' column
    or similar. We look for the standard NIH Toolbox DCCS column.

    Args:
        file_path: Path to the behavioral CSV file.

    Returns:
        DataFrame with Subject_ID and Flexibility_Score (DCCS).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Behavioral file not found: {file_path}")

    df = pd.read_csv(file_path)

    # HCP 1200 behavioral data column names for DCCS
    # Commonly: 'NIH_DCCS_TotalScore' or 'DCCS_TotalScore'
    # We check for the most standard HCP naming convention.
    target_cols = ['NIH_DCCS_TotalScore', 'DCCS_TotalScore', 'DCCS_Total_Score']
    found_col = None
    for col in target_cols:
        if col in df.columns:
            found_col = col
            break

    if not found_col:
        # Fallback: try to find any column containing 'DCCS' and 'Total'
        candidates = [c for c in df.columns if 'DCCS' in c.upper() and 'Total' in c]
        if candidates:
            found_col = candidates[0]
            log_warning(f"Using non-standard DCCS column: {found_col}")
        else:
            raise ValueError(
                f"Could not find DCCS score column in {file_path}. "
                f"Searched for: {target_cols}. Available columns: {list(df.columns)}"
            )

    # Select relevant columns
    if 'Subject' in df.columns:
        subject_col = 'Subject'
    elif 'Subject_ID' in df.columns:
        subject_col = 'Subject_ID'
    else:
        raise ValueError(f"Behavioral file missing Subject_ID column. Available: {list(df.columns)}")

    result = df[[subject_col, found_col]].copy()
    result.columns = ['Subject_ID', 'Flexibility_Score']

    # Clean Subject_ID
    result['Subject_ID'] = result['Subject_ID'].astype(str).str.strip()

    # Ensure Flexibility_Score is numeric
    result['Flexibility_Score'] = pd.to_numeric(result['Flexibility_Score'], errors='coerce')

    logger.info(f"Loaded behavioral scores: {len(result)} subjects from {file_path}")
    return result

def merge_datasets(
    neuro_df: pd.DataFrame,
    behavioral_df: pd.DataFrame,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Merge neuroimaging features and behavioral scores on Subject_ID.

    Performs an inner join to keep only subjects present in both datasets.
    Logs excluded subjects if necessary (though T015/T017 handle specific exclusion logging).

    Args:
        neuro_df: DataFrame with neuro features.
        behavioral_df: DataFrame with behavioral scores.
        output_path: Optional path to save the merged CSV.

    Returns:
        Merged DataFrame.
    """
    if neuro_df.empty:
        raise ValueError("Neuro features DataFrame is empty.")
    if behavioral_df.empty:
        raise ValueError("Behavioral scores DataFrame is empty.")

    # Merge
    merged = pd.merge(
        neuro_df,
        behavioral_df,
        on='Subject_ID',
        how='inner'
    )

    logger.info(f"Merged dataset size: {len(merged)} subjects (inner join)")

    # Log counts for transparency
    total_neuro = len(neuro_df)
    total_behav = len(behavioral_df)
    merged_count = len(merged)
    missing_in_neuro = total_behav - merged_count
    missing_in_behav = total_neuro - merged_count

    logger.info(f"Subjects in Neuro but missing in Behavioral: {missing_in_neuro}")
    logger.info(f"Subjects in Behavioral but missing in Neuro: {missing_in_behav}")

    if output_path:
        ensure_dir(output_path)
        merged.to_csv(output_path, index=False)
        logger.info(f"Merged data saved to {output_path}")

    return merged

def run_merge_pipeline(
    neuro_input_path: Optional[str] = None,
    behavioral_input_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Run the full merge pipeline.

    1. Load neuro features (default: data/processed/neuro_features.csv or similar).
    2. Load behavioral scores (default: data/raw/behavioral_data.csv).
    3. Merge on Subject_ID.
    4. Save to data/processed/merged_data.csv.

    Args:
        neuro_input_path: Path to neuro features CSV. If None, uses default.
        behavioral_input_path: Path to behavioral CSV. If None, uses default.
        output_path: Path to save merged CSV. If None, uses default.

    Returns:
        Merged DataFrame.
    """
    # Defaults based on project structure
    if neuro_input_path is None:
        # Assuming T013 produces a file like 'parcellated_features.csv' or similar
        # We need to be flexible here. Let's assume the output of T013 is
        # 'data/processed/parcellated_time_series_stats.csv' or similar.
        # However, T014 description says "join neuroimaging features".
        # Let's assume a standard intermediate file name for now.
        # If T013 hasn't produced a specific file yet, we might need to look for
        # the most recent output or a specific naming convention.
        # For now, we'll assume the output of T013 is 'data/processed/roi_metrics.csv'
        # or the user provides the path.
        # Since T013 is "preprocess.py" which parcellates, the output is likely
        # a CSV of time series or summary stats.
        # Let's assume the task expects us to merge the *output* of T013.
        # If T013 outputs a specific file, we should use that.
        # Let's use a generic name that T013 might produce if not specified.
        # Actually, looking at T013 description: "apply Schaefer atlas parcellation".
        # It likely outputs a CSV of subject-level stats or time series.
        # Let's assume the file is 'data/processed/parcellated_subjects.csv'.
        # If it doesn't exist, the loader will fail loudly (per constraints).
        neuro_input_path = os.path.join(get_processed_path(), "parcellated_subjects.csv")

    if behavioral_input_path is None:
        behavioral_input_path = os.path.join(get_raw_path(), "behavioral_data.csv")

    if output_path is None:
        output_path = os.path.join(get_processed_path(), "merged_data.csv")

    try:
        neuro_df = load_neuro_features(neuro_input_path)
        behavioral_df = load_behavioral_scores(behavioral_input_path)
        merged_df = merge_datasets(neuro_df, behavioral_df, output_path)
        return merged_df
    except FileNotFoundError as e:
        log_error(f"Data file missing: {e}")
        raise
    except ValueError as e:
        log_error(f"Data validation error: {e}")
        raise
    except Exception as e:
        log_error(f"Unexpected error during merge: {e}")
        raise

if __name__ == "__main__":
    # Initialize logging
    init_logging()
    logger.info("Starting merge pipeline (T014)...")
    run_merge_pipeline()
    logger.info("Merge pipeline completed.")
