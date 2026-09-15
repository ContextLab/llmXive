import pandas as pd
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from config import load_config, ensure_directories, set_seed
from exceptions import PowerLimitationError

logger = logging.getLogger(__name__)

def load_cleaned_data(input_path: Path) -> pd.DataFrame:
    """Loads the cleaned data from the processed directory."""
    if not input_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found at {input_path}")
    return pd.read_csv(input_path)

def validate_cleaned_data(df: pd.DataFrame) -> bool:
    """
    Validates the cleaned data.
    Checks for sufficient sample size (Power Limitation).
    """
    n = len(df)
    logger.info(f"Validating cleaned data: N = {n}")
    
    # Spec FR-002: HALT if N < 30
    if n < 30:
        msg = f"Power limitation: Sample size N={n} is below the minimum threshold of 30."
        logger.error(msg)
        raise PowerLimitationError(msg)
    
    # Log warning if 30 <= N < 100 (as per task description)
    if 30 <= n < 100:
        logger.warning(f"Low Power Warning: Sample size N={n} is between 30 and 100.")
    
    # Log Plan's stricter guideline (N < 130) as a comment/log
    if n < 130:
        logger.info("Note: Sample size N={n} is below the stricter guideline of 130 suggested in the plan.")

    return True

def save_cleaned_data(df: pd.DataFrame, output_path: Path) -> None:
    """Saves the cleaned dataframe to the specified path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Cleaned data saved to {output_path}")

def main():
    """
    Main entry point for the cleaning pipeline.
    Orchestrates loading, validation, and saving.
    """
    config = load_config()
    ensure_directories(config)
    
    input_path = Path(config['paths']['processed_data']) / "analysis_data.csv"
    output_path = Path(config['paths']['processed_data']) / "analysis_data.csv" 
    # Note: In a multi-step pipeline, this might load from raw_cleaned and save to processed_final
    # But for this task, we assume the ingest.py already did the cleaning and saved it,
    # and this script validates the result and logs power stats.
    # Alternatively, if ingest.py just downloads, this script loads raw, cleans, validates, saves.
    # Given T012 says "Implement listwise deletion in code/clean.py", we assume this script does the work.
    
    # Re-reading T012/T013: 
    # T012: Implement listwise deletion in code/clean.py
    # T013: Save cleaned dataset to data/processed/analysis_data.csv
    # So clean.py should load raw, clean, validate, save.
    
    raw_path = Path(config['paths']['raw_data']) / "survey_data.csv"
    
    if not raw_path.exists():
        logger.error(f"Raw data not found at {raw_path}. Run ingest.py first.")
        sys.exit(1)
    
    df = pd.read_csv(raw_path)
    original_n = len(df)
    logger.info(f"Loaded raw data: {original_n} rows.")
    
    # Perform listwise deletion
    # Columns to check for missing values (predictors and outcome)
    required_cols = ['news_exposure_freq', 'anxiety_score', 'baseline_anxiety']
    
    # Log missing stats
    missing_counts = df[required_cols].isnull().sum()
    logger.info("Missing value statistics in raw data:")
    for col, count in missing_counts.items():
        logger.info(f"  {col}: {count}")
    
    # Drop rows with missing values in required columns
    df_clean = df.dropna(subset=required_cols)
    cleaned_n = len(df_clean)
    dropped_n = original_n - cleaned_n
    
    logger.info(f"Listwise deletion: Dropped {dropped_n} rows.")
    logger.info(f"Remaining rows: {cleaned_n}")
    
    # Validate power (T012 requirement)
    try:
        validate_cleaned_data(df_clean)
    except PowerLimitationError as e:
        logger.critical(str(e))
        sys.exit(1)
    
    # Save
    save_cleaned_data(df_clean, output_path)

if __name__ == "__main__":
    from logging_config import setup_logging
    setup_logging()
    main()