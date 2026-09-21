import os
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple

from utils.logging import setup_logger
from utils.config import get_config

logger = setup_logger(__name__)

def load_metadata(metadata_path: str) -> pd.DataFrame:
    """
    Load the raw metadata CSV file.
    
    Args:
        metadata_path: Path to the raw metadata CSV file.
        
    Returns:
        DataFrame containing the raw metadata.
        
    Raises:
        FileNotFoundError: If the metadata file does not exist.
        ValueError: If the file is empty or has no valid data.
    """
    path = Path(metadata_path)
    if not path.exists():
        raise FileNotFoundError(f"Metadata file not found at {metadata_path}")
    
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError("Metadata file is empty or contains no valid data.")
    
    logger.info(f"Loaded metadata with {len(df)} rows and {len(df.columns)} columns.")
    return df

def extract_behavioral_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract and calculate behavioral metrics from the raw metadata.
    
    Ensures the presence of required columns:
    - subject_id
    - pre_motor_score
    - post_motor_score
    - age
    - sex
    
    Calculates:
    - improvement_score = post_motor_score - pre_motor_score
    
    Args:
        df: Raw metadata DataFrame.
        
    Returns:
        DataFrame with extracted and calculated behavioral metrics.
        
    Raises:
        ValueError: If required columns are missing.
    """
    required_columns = ['subject_id', 'pre_motor_score', 'post_motor_score', 'age', 'sex']
    missing_cols = [col for col in required_columns if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required columns in metadata: {missing_cols}")
    
    # Create a copy to avoid modifying the original
    result_df = df[required_columns].copy()
    
    # Calculate improvement score
    result_df['improvement_score'] = result_df['post_motor_score'] - result_df['pre_motor_score']
    
    # Ensure subject_id is treated as string for consistency
    result_df['subject_id'] = result_df['subject_id'].astype(str)
    
    # Drop rows with any missing values in required columns
    initial_count = len(result_df)
    result_df = result_df.dropna(subset=required_columns + ['improvement_score'])
    dropped_count = initial_count - len(result_df)
    
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows due to missing behavioral data.")
    
    logger.info(f"Extracted behavioral metrics for {len(result_df)} subjects.")
    return result_df

def save_behavioral_metrics(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the extracted behavioral metrics to a CSV file.
    
    Args:
        df: DataFrame containing behavioral metrics.
        output_path: Path where the output CSV will be saved.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(path, index=False)
    logger.info(f"Saved behavioral metrics to {output_path} ({len(df)} rows).")

def run_behavioral_extraction() -> Tuple[pd.DataFrame, str]:
    """
    Main entry point for the behavioral extraction pipeline.
    
    1. Loads metadata from the configured raw path.
    2. Extracts behavioral metrics.
    3. Saves the result to the configured processed path.
    
    Returns:
        Tuple of (DataFrame, output_path)
        
    Raises:
        FileNotFoundError: If input metadata is missing.
        ValueError: If required columns are missing.
    """
    config = get_config()
    input_path = config.dataset.raw_metadata_path
    output_path = config.output_paths.behavioral_scores_path
    
    logger.info(f"Starting behavioral extraction from {input_path}")
    
    df = load_metadata(input_path)
    processed_df = extract_behavioral_metrics(df)
    save_behavioral_metrics(processed_df, output_path)
    
    return processed_df, output_path

def main():
    """CLI entry point."""
    try:
        df, path = run_behavioral_extraction()
        logger.info(f"Behavioral extraction complete. Output: {path}")
    except Exception as e:
        logger.error(f"Behavioral extraction failed: {e}")
        raise

if __name__ == "__main__":
    main()
