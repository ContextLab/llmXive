"""
Module to save the cleaned dataset to the processed directory.

This module implements task T013: Save cleaned dataset to `data/processed/analysis_data.csv`.
It loads the cleaned data (which has already undergone listwise deletion and power checks
in `code/clean.py`), performs a final validation, and writes it to the specified output path.
"""
import pandas as pd
import logging
from pathlib import Path
import sys
from typing import Optional, Dict, Any

# Local imports matching the project API surface
from config import load_config, ensure_directories, get_dataset_url
from logging_config import setup_logging
from exceptions import DataValidationError

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    'news_exposure_freq',
    'anxiety_score',
    'baseline_anxiety',
    'age',
    'gender'
]

def load_cleaned_data(input_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the cleaned data from the raw/processed intermediate file.
    
    Args:
        input_path: Optional path to the cleaned CSV. If None, uses default config.
        
    Returns:
        pd.DataFrame: The cleaned dataset.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file cannot be read as CSV.
    """
    config = load_config()
    if input_path is None:
        # Assuming the clean.py task writes to a temporary location or we need to
        # read from the standard intermediate location. 
        # Based on task T012, clean.py performs listwise deletion. 
        # We assume the output of T012 is at data/raw/cleaned_intermediate.csv 
        # or similar, but typically T012 writes to a temp file and T013 moves/finalizes.
        # However, to be robust, let's look for the standard "cleaned" output.
        # Since T012 is "Implement listwise deletion", it likely writes to a temp file.
        # Let's assume the standard flow: ingest -> raw -> clean -> processed.
        # We will try to load from a standard intermediate path if not provided.
        input_path = Path(config.get('paths', {}).get('cleaned_intermediate', 'data/raw/cleaned_intermediate.csv'))
    
    if not input_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found at {input_path}. "
                                f"Ensure T012 (clean.py) has run successfully.")
    
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
        return df
    except Exception as e:
        logger.error(f"Failed to load CSV from {input_path}: {e}")
        raise

def validate_cleaned_data(df: pd.DataFrame) -> bool:
    """
    Validate that the cleaned data meets the requirements for T013.
    
    Checks:
    1. All required columns are present.
    2. No null values in primary predictor (news_exposure_freq) or outcome (anxiety_score).
    3. Sample size is sufficient (though T012 should have already enforced this).
    
    Args:
        df: The dataframe to validate.
        
    Returns:
        bool: True if valid.
        
    Raises:
        DataValidationError: If validation fails.
    """
    # Check columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise DataValidationError(f"Missing required columns: {missing_cols}")
    
    # Check nulls in critical columns
    critical_nulls = {}
    for col in ['news_exposure_freq', 'anxiety_score']:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            critical_nulls[col] = null_count
    
    if critical_nulls:
        raise DataValidationError(f"Critical columns contain null values: {critical_nulls}. "
                                  "Listwise deletion in T012 should have removed these.")
    
    # Check sample size (re-verify T012 logic)
    if len(df) < 30:
        raise DataValidationError(f"Sample size {len(df)} is below the minimum threshold of 30. "
                                  "This indicates a failure in the listwise deletion power check (T012).")
    
    logger.info(f"Validation passed. Rows: {len(df)}, Columns: {list(df.columns)}")
    return True

def save_cleaned_data(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Save the validated cleaned dataset to the processed directory.
    
    This implements the core requirement of T013.
    
    Args:
        df: The validated dataframe.
        output_path: Optional output path. Defaults to data/processed/analysis_data.csv.
        
    Returns:
        Path: The path to the saved file.
    """
    config = load_config()
    if output_path is None:
        output_path = Path(config.get('paths', {}).get('processed_data', 'data/processed/analysis_data.csv'))
    
    # Ensure directory exists
    ensure_directories()
    
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved cleaned dataset to {output_path}")
        logger.info(f"Saved {len(df)} rows and {len(df.columns)} columns")
        return output_path
    except Exception as e:
        logger.error(f"Failed to save dataset to {output_path}: {e}")
        raise

def main():
    """
    Main entry point for the T013 task.
    
    Executes the full pipeline: load -> validate -> save.
    """
    # Setup logging
    setup_logging()
    logger.info("Starting T013: Save Cleaned Data")
    
    try:
        # 1. Load cleaned data (output of T012)
        logger.info("Loading cleaned data...")
        df = load_cleaned_data()
        
        # 2. Validate data
        logger.info("Validating cleaned data...")
        validate_cleaned_data(df)
        
        # 3. Save to processed directory
        logger.info("Saving to data/processed/analysis_data.csv...")
        output_path = save_cleaned_data(df)
        
        logger.info(f"T013 completed successfully. Output: {output_path}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        return 1
    except DataValidationError as e:
        logger.error(f"Data validation failed: {e}")
        return 2
    except Exception as e:
        logger.exception(f"Unexpected error during T013: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())