import pandas as pd
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from config import load_config, ensure_directories, set_seed
from exceptions import PowerLimitationError

logger = logging.getLogger(__name__)

def load_cleaned_data(input_path: Path) -> pd.DataFrame:
    """Load data from a CSV file."""
    logger.info(f"Loading data from {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return pd.read_csv(input_path)

def validate_cleaned_data(df: pd.DataFrame) -> bool:
    """
    Validate that the cleaned data meets minimum requirements.
    Specifically, checks for the presence of required columns and
    logs missing value statistics again if needed.
    """
    required_cols = ['news_exposure_freq', 'anxiety_score', 'baseline_anxiety', 'age', 'gender']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns in cleaned data: {missing}")
        return False
    
    # Log missing value statistics for the cleaned data
    for col in required_cols:
        missing_count = df[col].isna().sum()
        if missing_count > 0:
            logger.warning(f"Cleaned data still has {missing_count} missing values in '{col}'.")
    
    logger.info("Cleaned data validation passed.")
    return True

def save_cleaned_data(df: pd.DataFrame, output_path: Path) -> None:
    """Save the cleaned dataframe to a CSV file."""
    logger.info(f"Saving cleaned data to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info("Data saved successfully.")

def main():
    """
    Main entry point for the cleaning pipeline.
    This function performs listwise deletion and enforces power checks.
    """
    config = load_config()
    ensure_directories(config)
    set_seed(config.get('random_seed', 42))
    
    input_path = Path(config.get('paths', {}).get('processed_data', 'data/processed')) / 'analysis_data.csv'
    output_path = input_path # Overwrite or save to a new file? T013 says save to analysis_data.csv.
    # Assuming the input here is the raw data after initial schema check, 
    # and we are saving the final cleaned version.
    # However, T010-T013 flow suggests ingest.py does the download and initial clean.
    # If clean.py is a separate step, it might take raw and output processed.
    # Let's assume it takes the raw data (if ingest didn't save) or the intermediate.
    # To be safe and align with T012 (listwise deletion), we read raw, clean, save processed.
    
    # Re-adjusting for T012 context: T010 downloads, T011 validates schema, T012 cleans.
    # If ingest.py handles T010-T013, then clean.py might be redundant or a refinement.
    # But T012 explicitly says "Implement listwise deletion in code/clean.py".
    # So, we assume ingest.py downloads and validates, and clean.py loads, cleans, saves.
    
    raw_data_path = Path(config.get('paths', {}).get('raw_data', 'data/raw')) / 'raw_survey_data.csv'
    processed_data_path = Path(config.get('paths', {}).get('processed_data', 'data/processed')) / 'analysis_data.csv'
    
    # If raw_data_path doesn't exist, try to load from the expected processed path if it's a re-run
    if not raw_data_path.exists():
        logger.warning(f"Raw data not found at {raw_data_path}. Trying processed path as source.")
        if not processed_data_path.exists():
            logger.error("No data source found.")
            sys.exit(1)
        df = pd.read_csv(processed_data_path)
    else:
        df = pd.read_csv(raw_data_path)
        
    logger.info(f"Loaded data with shape: {df.shape}")
    
    # T012: Listwise deletion for missing predictor/outcome
    primary_cols = ['news_exposure_freq', 'anxiety_score']
    initial_rows = len(df)
    df_clean = df.dropna(subset=primary_cols)
    final_rows = len(df_clean)
    
    # Log row counts and missing stats (T014 requirement)
    logger.info(f"Listwise deletion: Removed {initial_rows - final_rows} rows.")
    logger.info(f"Final row count: {final_rows}")
    
    for col in primary_cols:
        missing = df_clean[col].isna().sum()
        if missing > 0:
            logger.warning(f"Still {missing} missing values in '{col}' after deletion.")
    
    # T012: Power Check
    if final_rows < 30:
        logger.error(f"Power Limitation Error: N={final_rows} < 30. Halting.")
        raise PowerLimitationError(f"Insufficient sample size: N={final_rows} < 30")
    elif 30 <= final_rows < 100:
        logger.warning(f"Low Power Warning: N={final_rows} is between 30 and 100.")
    else:
        logger.info(f"Power Check OK: N={final_rows} >= 100.")
    
    # Save
    save_cleaned_data(df_clean, processed_data_path)
    
    logger.info("Cleaning pipeline completed.")

if __name__ == "__main__":
    main()
