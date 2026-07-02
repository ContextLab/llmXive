import pandas as pd
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from config import load_config, ensure_directories, set_seed
from logging_config import setup_logging
from exceptions import PowerLimitationError

def load_cleaned_data(input_path: Path) -> pd.DataFrame:
    """
    Load cleaned data from a CSV file.
    
    Args:
        input_path: Path to the CSV file
        
    Returns:
        DataFrame with the loaded data
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Loading data from {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
    return df

def validate_cleaned_data(df: pd.DataFrame) -> bool:
    """
    Validate that cleaned data meets minimum requirements.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        True if validation passes
        
    Raises:
        PowerLimitationError: If sample size is below threshold
    """
    logger = logging.getLogger(__name__)
    
    # Check for required columns
    required_cols = ['news_exposure_freq', 'anxiety_score', 'baseline_anxiety', 'age', 'gender']
    missing = [col for col in required_cols if col not in df.columns]
    
    if missing:
        raise ValueError(f"Missing required columns in cleaned data: {missing}")
    
    # Check for null values in key columns
    key_cols = ['news_exposure_freq', 'anxiety_score']
    null_counts = df[key_cols].isna().sum()
    if null_counts.any():
        logger.warning(f"Null values found in key columns after cleaning: {null_counts.to_dict()}")
    
    # Power check (Spec FR-002)
    n = len(df)
    if n < 30:
        error_msg = f"Power limitation: Sample size ({n}) is below minimum threshold of 30."
        logger.error(error_msg)
        raise PowerLimitationError(error_msg)
    elif n < 100:
        warning_msg = f"Low power warning: Sample size ({n}) is between 30 and 100."
        logger.warning(warning_msg)
        logger.warning("Plan guideline suggests N >= 130 for higher power.")
    
    return True

def save_cleaned_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save cleaned data to a CSV file.
    
    Args:
        df: DataFrame to save
        output_path: Path where the cleaned data will be saved
    """
    logger = logging.getLogger(__name__)
    df.to_csv(output_path, index=False)
    logger.info(f"Cleaned data saved to {output_path}")
    logger.info(f"Saved {len(df)} rows and {len(df.columns)} columns")

def main():
    """Main entry point for data cleaning pipeline."""
    logger = setup_logging()
    config = load_config()
    
    # Ensure directories exist
    ensure_directories()
    
    # Set random seed for reproducibility
    set_seed(config.get('random_seed', 42))
    
    # Define input and output paths
    raw_data_path = Path(config.get('paths', {}).get('raw_data', 'data/raw/')) / 'raw_survey_data.csv'
    processed_data_path = Path(config.get('paths', {}).get('processed_data', 'data/processed/')) / 'analysis_data.csv'
    
    try:
        # Step 1: Load raw data
        logger.info("Starting data cleaning pipeline...")
        df = load_cleaned_data(raw_data_path)
        
        # Log initial statistics
        initial_rows = len(df)
        logger.info(f"Initial dataset size: {initial_rows} rows")
        
        # Log missing value statistics
        key_columns = ['news_exposure_freq', 'anxiety_score', 'baseline_anxiety', 'age', 'gender']
        missing_stats = {}
        for col in key_columns:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                missing_pct = (missing_count / len(df)) * 100
                missing_stats[col] = {'count': int(missing_count), 'percent': round(missing_pct, 2)}
                logger.info(f"Missing values in '{col}': {missing_count} ({missing_pct:.2f}%)")
        
        # Step 2: Perform listwise deletion
        df_clean = df.dropna(subset=['news_exposure_freq', 'anxiety_score'])
        
        final_rows = len(df_clean)
        deleted_rows = initial_rows - final_rows
        logger.info(f"After listwise deletion: {final_rows} rows ({deleted_rows} rows removed)")
        
        # Step 3: Validate cleaned data (includes power check)
        validate_cleaned_data(df_clean)
        
        # Step 4: Save cleaned data
        save_cleaned_data(df_clean, processed_data_path)
        
        # Final summary logging
        logger.info("Data cleaning pipeline completed successfully.")
        logger.info(f"Final dataset shape: {df_clean.shape}")
        logger.info(f"Columns: {list(df_clean.columns)}")
        
    except (PowerLimitationError, ValueError, FileNotFoundError) as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during pipeline execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()