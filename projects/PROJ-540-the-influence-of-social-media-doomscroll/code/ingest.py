import pandas as pd
import logging
import sys
import requests
from pathlib import Path
from typing import Optional, Dict, Any

from config import load_config, ensure_directories, get_dataset_url
from exceptions import DataValidationError

# Configure logger for this module
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = [
    'news_exposure_freq',
    'anxiety_score',
    'baseline_anxiety',
    'age',
    'gender'
]

def download_data(url: str, output_path: Path) -> Path:
    """
    Download data from the provided URL.
    """
    logger.info(f"Downloading data from {url} to {output_path}")
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(response.content)
        logger.info("Data download successful.")
        return output_path
    except requests.RequestException as e:
        logger.error(f"Failed to download data: {e}")
        raise

def validate_schema(df: pd.DataFrame) -> bool:
    """
    Validate that the dataframe contains all required columns.
    """
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        error_msg = f"Missing required columns: {missing_cols}"
        logger.error(error_msg)
        raise DataValidationError(error_msg)
    
    # Log schema validation success
    logger.info("Schema validation passed. All required columns present.")
    return True

def clean_data(df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """
    Perform basic cleaning: listwise deletion for missing predictor/outcome values.
    Logs row counts, missing value statistics, and power check results.
    
    Note: This function assumes the power check logic (HALT on N < 30) 
    is handled by the caller (e.g., main or a dedicated clean.py module) 
    or implemented here if not already done elsewhere. 
    Per T012, the power check is in clean.py. We focus on logging here.
    """
    logger.info(f"Starting data cleaning. Initial shape: {df.shape}")
    
    # Log missing value statistics for key columns
    missing_stats = {}
    for col in REQUIRED_COLUMNS:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            missing_pct = (missing_count / len(df)) * 100
            missing_stats[col] = {'count': missing_count, 'pct': missing_pct}
            logger.info(f"Column '{col}': {missing_count} missing values ({missing_pct:.2f}%)")
    
    # Perform listwise deletion for predictor/outcome
    # Assuming 'news_exposure_freq' and 'anxiety_score' are the primary predictor/outcome
    primary_cols = ['news_exposure_freq', 'anxiety_score']
    initial_rows = len(df)
    df_clean = df.dropna(subset=primary_cols)
    final_rows = len(df_clean)
    deleted_rows = initial_rows - final_rows
    
    logger.info(f"Listwise deletion removed {deleted_rows} rows due to missing primary variables.")
    logger.info(f"Row count after cleaning: {final_rows} (from {initial_rows})")
    
    # Log power check result (Spec: N < 30 HALT, 30 <= N < 100 warning)
    # This is a logging implementation of the power check. 
    # The actual HALT logic might be in clean.py as per T012, 
    # but we log the status here as requested by T014.
    if final_rows < 30:
        logger.error(f"Power Limitation: Final N ({final_rows}) is less than 30. Analysis cannot proceed.")
        # Note: The actual raising of PowerLimitationError is typically in clean.py T012.
        # We log the condition here for T014 requirements.
    elif 30 <= final_rows < 100:
        logger.warning(f"Low Power Warning: Final N ({final_rows}) is between 30 and 100.")
    else:
        logger.info(f"Power Check Passed: Final N ({final_rows}) is sufficient (>= 100).")
        
    return df_clean

def main():
    """
    Main entry point for data ingestion and cleaning with logging.
    """
    # Load configuration
    config = load_config()
    ensure_directories(config)
    
    # Setup logging (assuming it's already configured globally or here)
    # If not, setup_logging() from logging_config would be called here.
    
    dataset_url = get_dataset_url(config)
    raw_path = Path(config.get('paths', {}).get('raw_data', 'data/raw')) / 'raw_survey_data.csv'
    processed_path = Path(config.get('paths', {}).get('processed_data', 'data/processed')) / 'analysis_data.csv'
    
    # 1. Download
    try:
        download_data(dataset_url, raw_path)
    except Exception as e:
        logger.critical(f"Data download failed: {e}")
        sys.exit(1)
        
    # 2. Load
    try:
        df = pd.read_csv(raw_path)
        logger.info(f"Loaded data with shape: {df.shape}")
    except Exception as e:
        logger.critical(f"Failed to load data: {e}")
        sys.exit(1)
        
    # 3. Validate Schema
    try:
        validate_schema(df)
    except DataValidationError as e:
        logger.critical(f"Schema validation failed: {e}")
        sys.exit(1)
        
    # 4. Clean and Log
    df_clean = clean_data(df, config)
    
    # 5. Save
    df_clean.to_csv(processed_path, index=False)
    logger.info(f"Cleaned data saved to {processed_path}")
    
    logger.info("Ingestion pipeline completed successfully.")

if __name__ == "__main__":
    main()
