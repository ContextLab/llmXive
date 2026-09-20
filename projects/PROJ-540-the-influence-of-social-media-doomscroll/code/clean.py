"""
Data cleaning module for the Doomscrolling Anxiety study.
Implements listwise deletion and power checks.
"""
import pandas as pd
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from config import load_config, ensure_directories
from exceptions import PowerLimitationError

logger = logging.getLogger(__name__)

PREDICTORS = ['news_exposure_freq', 'baseline_anxiety', 'age', 'gender']
OUTCOME = 'anxiety_score'
REQUIRED_FOR_POWER = PREDICTORS + [OUTCOME]

MIN_POWER_THRESHOLD = 130
LOW_POWER_WARNING_THRESHOLD = 200

def load_cleaned_data(input_path: Path) -> pd.DataFrame:
    """
    Loads data from a CSV file.

    Args:
        input_path: Path to the input CSV file.

    Returns:
        pd.DataFrame: Loaded DataFrame.
    """
    logger.info(f"Loading data from {input_path}")
    return pd.read_csv(input_path)

def validate_cleaned_data(df: pd.DataFrame) -> None:
    """
    Validates that the DataFrame contains necessary columns for cleaning.

    Args:
        df: DataFrame to validate.

    Raises:
        ValueError: If required columns are missing.
    """
    missing = [col for col in REQUIRED_FOR_POWER if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for cleaning: {missing}")

def save_cleaned_data(df: pd.DataFrame, output_path: Path) -> Path:
    """
    Saves the cleaned DataFrame to a CSV file.

    Args:
        df: DataFrame to save.
        output_path: Path to save the file.

    Returns:
        Path: The path where the file was saved.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Cleaned data saved to {output_path}")
    return output_path

def apply_listwise_deletion(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs listwise deletion on rows with missing values in predictor/outcome columns.
    Enforces power constraints as per the project plan.

    Args:
        df: Input DataFrame.

    Returns:
        pd.DataFrame: Cleaned DataFrame.

    Raises:
        PowerLimitationError: If resulting N < 130.
    """
    validate_cleaned_data(df)
    
    initial_n = len(df)
    df_clean = df.dropna(subset=REQUIRED_FOR_POWER)
    final_n = len(df_clean)
    dropped = initial_n - final_n

    logger.info(f"Initial N: {initial_n}, Dropped: {dropped}, Final N: {final_n}")
    logger.info(f"INFO: Rows dropped: {dropped}")
    logger.info(f"INFO: Final N: {final_n}")

    if final_n < MIN_POWER_THRESHOLD:
        error_msg = f"Power limitation. N ({final_n}) < {MIN_POWER_THRESHOLD}. Analysis cannot proceed."
        logger.error(error_msg)
        raise PowerLimitationError(error_msg)
    elif final_n < LOW_POWER_WARNING_THRESHOLD:
        logger.warning(f"WARNING: Low Power (N < {LOW_POWER_WARNING_THRESHOLD})")

    return df_clean

def main():
    """
    Main entry point for the cleaning pipeline.
    """
    config = load_config()
    ensure_directories()
    
    input_path = Path(config['paths']['raw_data']) / 'parsed_data.csv'
    output_path = Path(config['paths']['processed_data']) / 'analysis_data.csv'
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. Run ingest.py first.")
    
    df = load_cleaned_data(input_path)
    df_clean = apply_listwise_deletion(df)
    save_cleaned_data(df_clean, output_path)

if __name__ == '__main__':
    main()
