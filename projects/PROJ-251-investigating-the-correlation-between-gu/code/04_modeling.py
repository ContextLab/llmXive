import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any, Union
import pandas as pd
import numpy as np

# Import from local utils
from utils.config import (
    get_seroconversion_threshold,
    get_hai_threshold,
    get_processed_path,
    get_output_path,
    ensure_directories,
    get_lod_handling_methods,
    get_lod_exclude_threshold
)
from utils.logging_config import get_logger, log_error_context

# Setup logger
logger = get_logger(__name__)

def load_processed_data() -> pd.DataFrame:
    """
    Load the preprocessed dataset from the standard location.
    Expects: data/processed/cleared_with_diversity.csv
    """
    path = get_processed_path() / "cleared_with_diversity.csv"
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found at {path}")
    
    logger.info(f"Loading processed data from {path}")
    df = pd.read_csv(path)
    
    # Ensure titer columns are numeric
    titer_cols = ['titer_baseline', 'titer_post']
    for col in titer_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

def calculate_seroconversion_status(df: pd.DataFrame, threshold: Optional[float] = None) -> pd.Series:
    """
    Calculate seroconversion status based on 4-fold rise in titer.
    
    Logic: post_titer >= threshold * baseline_titer
    Default threshold is 4.0 (configurable via get_seroconversion_threshold).
    
    Returns: Boolean series indicating seroconversion status.
    """
    if threshold is None:
        threshold = get_seroconversion_threshold()
    
    logger.info(f"Calculating seroconversion status with threshold: {threshold}")
    
    if 'titer_baseline' not in df.columns or 'titer_post' not in df.columns:
        raise ValueError("Required columns 'titer_baseline' and 'titer_post' not found in dataset")
    
    # Handle missing values
    # If baseline is missing, we cannot calculate fold rise -> False
    # If post is missing, we cannot calculate fold rise -> False
    
    baseline = df['titer_baseline'].fillna(0)
    post = df['titer_post'].fillna(0)
    
    # Avoid division by zero for baseline
    # If baseline is 0, any post > 0 could be considered infinite fold rise
    # However, in practice, we treat baseline=0 as requiring post > 0 for seroconversion
    # A more robust approach: if baseline == 0, seroconvert if post > some minimal detectable level
    # For this implementation, we'll use: if baseline == 0, seroconvert if post > 0
    
    seroconversion = pd.Series(False, index=df.index)
    
    # Case 1: baseline > 0
    valid_baseline = baseline > 0
    seroconversion[valid_baseline] = post[valid_baseline] >= (threshold * baseline[valid_baseline])
    
    # Case 2: baseline == 0 (treat as seroconversion if post > 0)
    zero_baseline = baseline == 0
    seroconversion[zero_baseline] = post[zero_baseline] > 0
    
    return seroconversion

def calculate_absolute_titer_status(df: pd.DataFrame, threshold: Optional[float] = None) -> pd.Series:
    """
    Calculate responder status based on absolute titer threshold (e.g., HAI >= 40).
    
    Logic: post_titer >= threshold
    Default threshold is 40.0 (configurable via get_hai_threshold).
    
    Returns: Boolean series indicating responder status.
    """
    if threshold is None:
        threshold = get_hai_threshold()
    
    logger.info(f"Calculating absolute titer status with threshold: {threshold}")
    
    if 'titer_post' not in df.columns:
        raise ValueError("Required column 'titer_post' not found in dataset")
    
    post = df['titer_post'].fillna(0)
    return post >= threshold

def define_responder_labels(df: pd.DataFrame) -> Tuple[pd.Series, str]:
    """
    Apply responder definition to dataset.
    
    Priority:
    1. If 'titer_baseline' exists and has non-null values: Use seroconversion (4-fold rise)
    2. Else: Use absolute titer threshold (HAI >= 40)
    
    Returns: Tuple of (responder_status series, method_used string)
    """
    logger.info("Defining responder labels")
    
    # Check if we have baseline titers
    has_baseline = 'titer_baseline' in df.columns and df['titer_baseline'].notna().any()
    
    if has_baseline:
        logger.info("Baseline titers found. Using seroconversion definition (4-fold rise).")
        responder_status = calculate_seroconversion_status(df)
        method_used = "seroconversion"
    else:
        logger.info("No baseline titers found. Using absolute titer definition (HAI >= 40).")
        responder_status = calculate_absolute_titer_status(df)
        method_used = "absolute_titer"
    
    return responder_status, method_used

def save_responder_labels(df: pd.DataFrame, responder_status: pd.Series, method_used: str, output_path: Optional[Path] = None) -> Path:
    """
    Save responder labels to CSV file.
    
    Output format:
    - subject_id
    - responder_status (True/False or 1/0)
    
    Also saves a metadata file with the method used.
    """
    if output_path is None:
        output_dir = get_output_path() / "processed"
        ensure_directories([output_dir])
        output_path = output_dir / "responder_labels.csv"
    
    logger.info(f"Saving responder labels to {output_path}")
    
    # Create output dataframe
    output_df = pd.DataFrame({
        'subject_id': df['subject_id'],
        'responder_status': responder_status
    })
    
    # Write to CSV
    output_df.to_csv(output_path, index=False)
    
    # Save metadata
    metadata_path = output_path.parent / "responder_labels_metadata.json"
    import json
    metadata = {
        'method_used': method_used,
        'total_subjects': len(output_df),
        'responders': int(responder_status.sum()),
        'non_responders': int(len(output_df) - responder_status.sum()),
        'response_rate': float(responder_status.mean())
    }
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Saved {len(output_df)} responder labels. Response rate: {metadata['response_rate']:.2%}")
    return output_path

def run_responder_definition() -> Path:
    """
    Main function to run the responder definition pipeline.
    
    1. Load processed data
    2. Define responder labels based on available data
    3. Save results to CSV
    
    Returns: Path to the output CSV file
    """
    logger.info("Starting responder definition pipeline")
    
    # Load data
    df = load_processed_data()
    
    # Define responder labels
    responder_status, method_used = define_responder_labels(df)
    
    # Save results
    output_path = save_responder_labels(df, responder_status, method_used)
    
    return output_path

def main():
    """
    Entry point for the responder definition module.
    """
    try:
        output_path = run_responder_definition()
        logger.info(f"Responser definition complete. Output: {output_path}")
        return 0
    except Exception as e:
        logger.error(f"Responser definition failed: {e}")
        log_error_context(e)
        return 1

if __name__ == "__main__":
    sys.exit(main())
