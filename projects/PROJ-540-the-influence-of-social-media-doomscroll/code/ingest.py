"""
Data ingestion module for the Doomscrolling Anxiety study.
Handles downloading, parsing, and initial validation of raw survey data.
"""
import pandas as pd
import logging
import sys
import requests
from pathlib import Path
from typing import Optional, Dict, Any

from config import load_config, get_dataset_url, ensure_directories
from exceptions import DataValidationError

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
    Fetches data from a remote URL and saves it to the specified output path.

    Args:
        url: The URL to download data from.
        output_path: Local path where the data will be saved.

    Returns:
        Path: The path to the downloaded file.

    Raises:
        RuntimeError: If the download fails (404, timeout, etc.).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Downloading data from {url}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Data successfully saved to {output_path}")
        return output_path
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to download data from {url}: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

def parse_and_validate(raw_path: Path) -> pd.DataFrame:
    """
    Reads a raw data file, validates the schema, and returns a DataFrame.

    Args:
        raw_path: Path to the raw data file.

    Returns:
        pd.DataFrame: Validated DataFrame.

    Raises:
        DataValidationError: If required columns are missing or file cannot be read.
    """
    logger.info(f"Reading and validating data from {raw_path}")
    
    try:
        if raw_path.suffix.lower() == '.csv':
            df = pd.read_csv(raw_path)
        elif raw_path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(raw_path)
        else:
            raise DataValidationError(f"Unsupported file format: {raw_path.suffix}")
    except Exception as e:
        error_msg = f"Failed to parse data file {raw_path}: {str(e)}"
        logger.error(error_msg)
        raise DataValidationError(error_msg) from e

    # Validate schema
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        error_msg = f"Missing required columns: {missing_cols}. Found: {list(df.columns)}"
        logger.error(error_msg)
        raise DataValidationError(error_msg)

    logger.info(f"Schema validation passed. Columns: {list(df.columns)}")
    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Performs initial cleaning: drops rows with missing values in required columns.
    Note: Full listwise deletion with power checks is handled in clean.py.
    This function is a helper for basic null removal before downstream processing.

    Args:
        df: Input DataFrame.

    Returns:
        pd.DataFrame: Cleaned DataFrame with no nulls in required columns.
    """
    initial_count = len(df)
    df_clean = df.dropna(subset=REQUIRED_COLUMNS)
    dropped_count = initial_count - len(df_clean)
    
    if dropped_count > 0:
        logger.info(f"Dropped {dropped_count} rows with missing values in required columns.")
    
    return df_clean

def main():
    """
    Main entry point for the ingestion pipeline.
    """
    config = load_config()
    ensure_directories()
    
    raw_url = get_dataset_url()
    raw_output = Path(config['paths']['raw_data']) / 'raw_survey.csv'
    parsed_output = Path(config['paths']['raw_data']) / 'parsed_data.csv'
    
    # Download
    download_data(raw_url, raw_output)
    
    # Parse and Validate
    df = parse_and_validate(raw_output)
    
    # Basic Clean
    df_clean = clean_data(df)
    
    # Save parsed data for downstream steps
    df_clean.to_csv(parsed_output, index=False)
    logger.info(f"Parsed and cleaned data saved to {parsed_output}")

if __name__ == '__main__':
    main()
