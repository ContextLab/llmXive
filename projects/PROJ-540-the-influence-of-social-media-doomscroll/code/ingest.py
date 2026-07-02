import pandas as pd
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from config import load_config, ensure_directories, get_dataset_url, set_seed
from logging_config import setup_logging
from exceptions import DataValidationError, PowerLimitationError

# Required columns for schema validation
REQUIRED_COLUMNS = [
    'news_exposure_freq',
    'anxiety_score',
    'baseline_anxiety',
    'age',
    'gender'
]

def download_data(url: str, output_path: Path) -> pd.DataFrame:
    """
    Download dataset from URL and save to raw data directory.
    
    Args:
        url: URL to the dataset
        output_path: Path where the raw data will be saved
        
    Returns:
        DataFrame with the downloaded data
        
    Raises:
        DataValidationError: If download fails or file is empty
    """
    logger = logging.getLogger(__name__)
    
    logger.info(f"Downloading data from {url}")
    try:
        # Try to read CSV directly from URL (works for many public datasets)
        df = pd.read_csv(url)
        df.to_csv(output_path, index=False)
        logger.info(f"Data downloaded successfully. Shape: {df.shape}")
        return df
    except Exception as e:
        # Fallback: try JSON or other formats
        logger.warning(f"CSV download failed: {e}. Attempting alternative methods...")
        try:
            df = pd.read_json(url)
            df.to_csv(output_path, index=False)
            logger.info(f"Data downloaded successfully (JSON). Shape: {df.shape}")
            return df
        except Exception as e2:
            logger.error(f"Failed to download data: {e2}")
            raise DataValidationError(f"Could not download data from {url}: {e2}")

def validate_schema(df: pd.DataFrame) -> None:
    """
    Validate that all required columns exist in the DataFrame.
    
    Args:
        df: DataFrame to validate
        
    Raises:
        DataValidationError: If any required column is missing
    """
    logger = logging.getLogger(__name__)
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    
    if missing_columns:
        error_msg = f"Missing required columns: {missing_columns}"
        logger.error(error_msg)
        raise DataValidationError(error_msg)
    
    logger.info("Schema validation passed. All required columns present.")

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform listwise deletion for missing predictor/outcome values.
    Enforce power check: HALT if N < 30, warn if 30 <= N < 100.
    
    Args:
        df: Raw DataFrame
        
    Returns:
        Cleaned DataFrame
        
    Raises:
        PowerLimitationError: If resulting N < 30
    """
    logger = logging.getLogger(__name__)
    
    # Log initial row count
    initial_rows = len(df)
    logger.info(f"Initial dataset size: {initial_rows} rows")
    
    # Identify key columns for missing value check
    key_columns = ['news_exposure_freq', 'anxiety_score']
    
    # Log missing value statistics before deletion
    missing_stats = {}
    for col in key_columns:
        if col in df.columns:
            missing_count = df[col].isna().sum()
            missing_pct = (missing_count / len(df)) * 100
            missing_stats[col] = {'count': int(missing_count), 'percent': round(missing_pct, 2)}
            logger.info(f"Missing values in '{col}': {missing_count} ({missing_pct:.2f}%)")
    
    # Log overall missing value summary
    total_missing = df[key_columns].isna().any(axis=1).sum()
    logger.info(f"Total rows with any missing values in key columns: {total_missing}")
    
    # Perform listwise deletion (drop rows with any NaN in key columns)
    df_clean = df.dropna(subset=key_columns)
    
    final_rows = len(df_clean)
    deleted_rows = initial_rows - final_rows
    logger.info(f"After listwise deletion: {final_rows} rows ({deleted_rows} rows removed)")
    
    # Power check (Spec FR-002)
    if final_rows < 30:
        error_msg = f"Power limitation: Final sample size ({final_rows}) is below minimum threshold of 30."
        logger.error(error_msg)
        raise PowerLimitationError(error_msg)
    elif final_rows < 100:
        warning_msg = f"Low power warning: Final sample size ({final_rows}) is between 30 and 100. Proceeding with caution."
        logger.warning(warning_msg)
        logger.warning("Plan guideline suggests N >= 130 for higher power.")
    
    return df_clean

def main():
    """Main entry point for data ingestion pipeline."""
    logger = setup_logging()
    config = load_config()
    
    # Ensure directories exist
    ensure_directories()
    
    # Set random seed for reproducibility
    set_seed(config.get('random_seed', 42))
    
    # Get dataset URL
    dataset_url = get_dataset_url()
    if not dataset_url:
        logger.error("No dataset URL configured. Please check config.yaml.")
        sys.exit(1)
    
    # Define output path
    raw_data_path = Path(config.get('paths', {}).get('raw_data', 'data/raw/')) / 'raw_survey_data.csv'
    
    try:
        # Step 1: Download data
        logger.info("Starting data ingestion pipeline...")
        df = download_data(dataset_url, raw_data_path)
        
        # Step 2: Validate schema
        validate_schema(df)
        
        # Step 3: Clean data (listwise deletion + power check)
        df_clean = clean_data(df)
        
        # Step 4: Save cleaned data
        processed_data_path = Path(config.get('paths', {}).get('processed_data', 'data/processed/')) / 'analysis_data.csv'
        df_clean.to_csv(processed_data_path, index=False)
        logger.info(f"Cleaned data saved to {processed_data_path}")
        
        # Final summary logging
        logger.info("Data ingestion pipeline completed successfully.")
        logger.info(f"Final dataset shape: {df_clean.shape}")
        logger.info(f"Columns: {list(df_clean.columns)}")
        
    except (DataValidationError, PowerLimitationError) as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during pipeline execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
