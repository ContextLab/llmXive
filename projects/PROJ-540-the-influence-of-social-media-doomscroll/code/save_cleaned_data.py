"""
Module to save cleaned data to the processed directory.
Implements T013: Save cleaned dataset to data/processed/analysis_data.csv
"""
import pandas as pd
import logging
from pathlib import Path
import sys
from typing import Optional, Dict, Any

from config import load_config, ensure_directories, get_dataset_url
from exceptions import PowerLimitationError

logger = logging.getLogger(__name__)

def load_cleaned_data(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Load the cleaned data from the raw directory (output of ingest/clean steps).
    For this implementation, we assume the cleaning happens in a previous step
    or is performed here if the raw file exists but isn't yet cleaned.
    
    Since T012 (listwise deletion) is a prerequisite, we expect the data 
    to be available in a temporary cleaned state or perform the cleaning here
    to ensure the output file is generated correctly.
    
    NOTE: In a strict pipeline, this would load from a temporary cleaned file.
    Here, to satisfy T013 as a standalone artifact that produces the output,
    we re-implement the minimal cleaning logic (listwise deletion) if the 
    'cleaned' file doesn't exist, or load the raw and clean it.
    """
    raw_path = Path(config['paths']['raw_data'])
    # Check if a pre-cleaned file exists (from a previous run of T012 logic)
    # If not, we must process the raw data.
    # Assuming the raw data is the output of T010/T011.
    
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data file not found at {raw_path}. "
                                "Run data ingestion (T010) first.")
    
    df = pd.read_csv(raw_path)
    logger.info(f"Loaded raw data with {len(df)} rows.")
    
    # Perform listwise deletion for required columns (T012 logic embedded for completeness)
    required_cols = ['news_exposure_freq', 'anxiety_score', 'baseline_anxiety', 'age', 'gender']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in raw data: {missing_cols}")
    
    # Drop rows with missing values in predictor/outcome variables
    initial_count = len(df)
    df_clean = df.dropna(subset=required_cols)
    final_count = len(df_clean)
    
    logger.info(f"Listwise deletion: {initial_count} -> {final_count} rows.")
    
    # Power check (T012 requirement)
    if final_count < 30:
        raise PowerLimitationError(f"Sample size ({final_count}) is below the minimum threshold of 30.")
    elif final_count < 100:
        logger.warning(f"Low Power Warning: Sample size ({final_count}) is between 30 and 100.")
    
    return df_clean

def validate_cleaned_data(df: pd.DataFrame, config: Dict[str, Any]) -> bool:
    """
    Validate the cleaned dataframe schema and basic integrity.
    """
    required_cols = ['news_exposure_freq', 'anxiety_score', 'baseline_anxiety', 'age', 'gender']
    
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Validation failed: Missing column '{col}'")
            return False
        if df[col].isnull().any():
            logger.error(f"Validation failed: Column '{col}' contains null values.")
            return False
    
    logger.info("Cleaned data validation passed.")
    return True

def save_cleaned_data(df: pd.DataFrame, config: Dict[str, Any]) -> Path:
    """
    Save the cleaned and validated dataframe to data/processed/analysis_data.csv.
    This fulfills task T013.
    """
    output_dir = Path(config['paths']['processed_data'])
    ensure_directories([output_dir])
    
    output_path = output_dir / "analysis_data.csv"
    
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Saved cleaned data to {output_path} ({len(df)} rows).")
        return output_path
    except Exception as e:
        logger.error(f"Failed to save cleaned data: {e}")
        raise

def main():
    """
    Main entry point to execute the cleaning and saving pipeline for T013.
    """
    config = load_config()
    setup_logging(config)
    
    try:
        # 1. Load and Clean (re-uses logic to ensure data is ready)
        df = load_cleaned_data(config)
        
        # 2. Validate
        if not validate_cleaned_data(df, config):
            raise ValueError("Data validation failed.")
        
        # 3. Save
        save_cleaned_data(df, config)
        
        logger.info("T013 completed successfully.")
        
    except PowerLimitationError as e:
        logger.critical(f"Power limitation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        sys.exit(1)

def setup_logging(config: Dict[str, Any]):
    """
    Helper to setup logging if not already done by the main pipeline.
    """
    log_path = Path(config['paths']['log_file'])
    ensure_directories([log_path.parent])
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )

if __name__ == "__main__":
    main()
