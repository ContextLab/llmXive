import pandas as pd
import logging
import sys
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from config import load_config, ensure_directories, get_dataset_url, set_seed
from exceptions import DataValidationError

logger = logging.getLogger(__name__)

def download_data(url: str, output_path: Path) -> Path:
    """Download the dataset from the given URL."""
    logger.info(f"Downloading data from {url} to {output_path}")
    ensure_directories(output_path)
    
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Successfully downloaded {len(response.content)} bytes to {output_path}")
        return output_path
    except requests.RequestException as e:
        logger.error(f"Failed to download data: {e}")
        raise

def validate_schema(df: pd.DataFrame) -> bool:
    """Validate that the dataframe contains the required columns."""
    required_columns = {
        'news_exposure_freq',
        'anxiety_score',
        'baseline_anxiety',
        'age',
        'gender'
    }
    
    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        error_msg = f"Schema validation failed. Missing columns: {missing}"
        logger.error(error_msg)
        raise DataValidationError(error_msg)
    
    logger.info("Schema validation passed.")
    return True

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Basic data cleaning: type conversion and initial checks."""
    logger.info("Performing basic data cleaning...")
    
    # Ensure numeric types
    numeric_cols = ['news_exposure_freq', 'anxiety_score', 'baseline_anxiety', 'age']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Ensure gender is categorical or string
    if 'gender' in df.columns:
        df['gender'] = df['gender'].astype(str)
    
    return df

def main() -> None:
    """Main entry point for the ingestion pipeline."""
    config = load_config()
    seed = config.get('random_seed')
    set_seed(seed)
    
    url = get_dataset_url(config)
    output_path = Path(config['paths']['raw_data'])
    
    try:
        # Download
        downloaded_path = download_data(url, output_path)
        
        # Load
        df = pd.read_csv(downloaded_path)
        logger.info(f"Loaded {len(df)} rows for validation.")
        
        # Validate
        validate_schema(df)
        
        # Clean
        df_clean = clean_data(df)
        
        # Save raw clean version for next stage (ingest -> clean stage)
        # Note: The actual listwise deletion happens in clean.py
        df_clean.to_csv(output_path, index=False)
        logger.info("Ingestion pipeline completed successfully.")
        
    except DataValidationError as e:
        logger.critical(f"Ingestion halted due to schema error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
