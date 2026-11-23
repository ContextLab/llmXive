"""
Data cleaning module for the Perspective-Taking Moral Outrage study.

This module implements the data cleaning pipeline according to:
- FR-003: Data cleaning and participant exclusion criteria
- Constitution Principle VI: Consent handling overrides narrower criteria
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from config import DATA_RAW_DIR, DATA_PROCESSED_DIR

# Configure logging
logger = logging.getLogger(__name__)

def load_raw_data(file_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load raw participant data from a CSV file.

    Args:
        file_path: Path to the raw CSV file. If None, looks for default location.

    Returns:
        pd.DataFrame: Loaded raw data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty or has no valid rows.
    """
    if file_path is None:
        file_path = DATA_RAW_DIR / "raw_participants.csv"
    else:
        file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {file_path}")

    logger.info(f"Loading raw data from {file_path}")
    df = pd.read_csv(file_path)

    if df.empty:
        raise ValueError("Loaded dataset is empty.")

    logger.info(f"Loaded {len(df)} rows from {file_path}")
    return df

def filter_consent(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter participants based on consent.

    Implements Constitution Principle VI: Participants must have given consent.
    This overrides the narrower exclusion criteria in FR-003 regarding consent.

    Args:
        df: Input DataFrame with participant data.

    Returns:
        pd.DataFrame: Filtered DataFrame containing only participants who gave consent.
    """
    logger.info("Filtering participants by consent...")
    
    # Ensure the column exists and handle case sensitivity
    consent_col = None
    for col in df.columns:
        if col.lower() == 'consent_given':
            consent_col = col
            break
    
    if consent_col is None:
        logger.warning("Column 'consent_given' not found. Checking for 'consent' or similar.")
        # Fallback to common variations
        for col in df.columns:
            if col.lower() in ['consent', 'agreed', 'participant_agreed']:
                consent_col = col
                break
    
    if consent_col is None:
        raise KeyError("No consent column found in the dataset. Expected 'consent_given'.")
    
    # Filter for true consent (handle boolean, string, or numeric representations)
    initial_count = len(df)
    df_consent = df[df[consent_col].isin([True, 'true', 'True', 1, '1'])]
    filtered_count = len(df_consent)
    
    logger.info(f"Consent filter: {initial_count} -> {filtered_count} participants")
    
    if filtered_count == 0:
        logger.warning("No participants with consent found. Returning empty DataFrame.")
    
    return df_consent

def filter_attention_checks(df: pd.DataFrame, max_fails: int = 1) -> pd.DataFrame:
    """
    Filter participants who failed more than the allowed number of attention checks.

    Args:
        df: Input DataFrame with participant data.
        max_fails: Maximum number of attention check failures allowed (default: 1).

    Returns:
        pd.DataFrame: Filtered DataFrame excluding participants with > max_fails attention check failures.
    """
    logger.info(f"Filtering participants with > {max_fails} attention check failures...")
    
    # Identify attention check columns (common naming patterns)
    attention_cols = []
    for col in df.columns:
        if 'attention' in col.lower() or 'check' in col.lower():
            attention_cols.append(col)
    
    if not attention_cols:
        logger.warning("No attention check columns found. Skipping attention filter.")
        return df
    
    # Assume 'fail' or 'incorrect' indicates a failed check. 
    # We need to count failures. Let's assume boolean True = fail, or specific string values.
    # Standardizing: Count how many attention checks are 'failed' or False (if True=pass).
    # Let's assume the data encodes 'failed' as True for failure, or specific values.
    # To be robust, we'll look for columns that have 'fail' or 'incorrect' in the value or name.
    # A safer approach for this specific study: assume columns named attention_1, attention_2 etc.
    # and values like 'correct', 'incorrect'.
    
    # Let's try a generic approach: count 'fail' or 'incorrect' or False (if True is pass)
    # We will assume that for attention checks, a value of 'fail', 'incorrect', or False (if True is pass) counts as a failure.
    # However, without knowing the exact encoding, we'll assume a standard: 
    # If the column name contains 'fail', then True/1 is a failure. 
    # If the column name contains 'pass' or 'correct', then False/0 is a failure.
    # If ambiguous, we'll count non-True values as failures if the column is boolean-like.
    
    # Simplified robust approach: Count failures based on common patterns.
    # Pattern 1: Column name has 'fail', value is True/1.
    # Pattern 2: Column name has 'pass'/'correct', value is False/0.
    # Pattern 3: Generic boolean, assume False is failure? Or True? 
    # Given the task, let's assume the data has columns like 'attention_1_pass' (True=pass) or 'attention_1_fail' (True=fail).
    
    failure_counts = pd.Series(0, index=df.index)
    
    for col in attention_cols:
        if 'fail' in col.lower():
            # True or 1 means failure
            failure_counts += df[col].astype(bool)
        elif 'pass' in col.lower() or 'correct' in col.lower():
            # False or 0 means failure
            failure_counts += (~df[col].astype(bool))
        else:
            # Ambiguous: assume True is failure if column name has 'attention' and no pass/fail
            # Or assume False is failure. Let's assume the data is clean and has 'fail' or 'pass' in name.
            # If not, we skip or warn.
            logger.warning(f"Ambiguous attention check column: {col}. Skipping failure count.")
    
    # Filter
    initial_count = len(df)
    df_filtered = df[failure_counts <= max_fails]
    filtered_count = len(df_filtered)
    
    logger.info(f"Attention filter (max {max_fails} fails): {initial_count} -> {filtered_count} participants")
    
    return df_filtered

def detect_straightlining(df: pd.DataFrame, scale_items: List[str], min_variance: float = 0.0) -> pd.DataFrame:
    """
    Detect and exclude participants exhibiting straight-lining behavior.

    Straight-lining is defined as zero variance across the specified scale items.

    Args:
        df: Input DataFrame with participant data.
        scale_items: List of column names representing the 7-item Moral Outrage Scale.
        min_variance: Minimum variance threshold to be considered valid (default: 0.0, strict).

    Returns:
        pd.DataFrame: Filtered DataFrame excluding straight-liners.
    """
    logger.info("Detecting straight-lining behavior...")
    
    # Check if all scale items exist
    missing_items = [item for item in scale_items if item not in df.columns]
    if missing_items:
        raise KeyError(f"Missing scale items in dataset: {missing_items}")
    
    # Calculate variance for each participant across the scale items
    # We calculate variance row-wise (axis=1)
    variance = df[scale_items].var(axis=1, ddof=1) # ddof=1 for sample variance
    
    # Identify straight-liners (variance == 0)
    straightliners = variance == min_variance
    
    initial_count = len(df)
    df_filtered = df[~straightliners]
    filtered_count = len(df_filtered)
    num_straightliners = initial_count - filtered_count
    
    logger.info(f"Straight-lining filter: {initial_count} -> {filtered_count} participants ({num_straightliners} excluded)")
    
    return df_filtered

def calculate_mean_outrage(df: pd.DataFrame, scale_items: List[str]) -> pd.DataFrame:
    """
    Calculate the mean moral outrage score for each participant.

    Args:
        df: Input DataFrame with participant data.
        scale_items: List of column names representing the 7-item Moral Outrage Scale.

    Returns:
        pd.DataFrame: DataFrame with an additional 'mean_outrage' column.
    """
    logger.info("Calculating mean moral outrage scores...")
    
    # Check if all scale items exist
    missing_items = [item for item in scale_items if item not in df.columns]
    if missing_items:
        raise KeyError(f"Missing scale items in dataset for calculation: {missing_items}")
    
    # Calculate mean across the scale items
    df['mean_outrage'] = df[scale_items].mean(axis=1)
    
    logger.info("Mean outrage scores calculated.")
    return df

def run_cleaning_pipeline(
    raw_file_path: Optional[str] = None,
    output_file_path: Optional[str] = None,
    scale_items: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Execute the full data cleaning pipeline.

    Steps:
    1. Load raw data.
    2. Filter by consent (Constitution Principle VI).
    3. Filter by attention checks.
    4. Detect and exclude straight-liners.
    5. Calculate mean outrage scores.
    6. Save cleaned data.

    Args:
        raw_file_path: Path to raw CSV. Defaults to DATA_RAW_DIR/raw_participants.csv.
        output_file_path: Path for cleaned CSV. Defaults to DATA_PROCESSED_DIR/cleaned_participants.csv.
        scale_items: List of column names for the 7-item Moral Outrage Scale.
                    Defaults to ['outrage_1', 'outrage_2', ..., 'outrage_7'].

    Returns:
        pd.DataFrame: The cleaned dataset.
    """
    logger.info("Starting data cleaning pipeline...")
    
    # Default scale items if not provided
    if scale_items is None:
        scale_items = [f'outrage_{i}' for i in range(1, 8)]
    
    # 1. Load
    df = load_raw_data(raw_file_path)
    
    # 2. Consent Filter
    df = filter_consent(df)
    if df.empty:
        logger.warning("Pipeline stopped: No participants passed consent filter.")
        return df
    
    # 3. Attention Check Filter
    df = filter_attention_checks(df)
    if df.empty:
        logger.warning("Pipeline stopped: No participants passed attention checks.")
        return df
    
    # 4. Straight-lining Detection
    df = detect_straightlining(df, scale_items)
    if df.empty:
        logger.warning("Pipeline stopped: No participants passed straight-lining check.")
        return df
    
    # 5. Calculate Mean Outrage
    df = calculate_mean_outrage(df, scale_items)
    
    # 6. Save
    if output_file_path is None:
        output_file_path = DATA_PROCESSED_DIR / "cleaned_participants.csv"
    else:
        output_file_path = Path(output_file_path)
    
    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file_path, index=False)
    
    logger.info(f"Cleaned data saved to {output_file_path}")
    logger.info(f"Final dataset size: {len(df)} participants")
    
    # Warning if N < 240 (from T009b power analysis)
    if len(df) < 240:
        logger.warning(f"Final N ({len(df)}) is below the target sample size of 240.")
    
    return df

# Example usage for direct execution
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Default paths
    raw_path = DATA_RAW_DIR / "raw_participants.csv"
    out_path = DATA_PROCESSED_DIR / "cleaned_participants.csv"
    
    # Check if input file exists
    if not raw_path.exists():
        print(f"Error: Raw data file not found at {raw_path}")
        sys.exit(1)
    
    # Run pipeline
    cleaned_df = run_cleaning_pipeline(raw_file_path=str(raw_path), output_file_path=str(out_path))
    print(f"Pipeline complete. Processed {len(cleaned_df)} participants.")