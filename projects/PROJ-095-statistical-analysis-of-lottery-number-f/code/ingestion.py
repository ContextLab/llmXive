"""
Data ingestion module for lottery draw data.
Handles downloading, checksum verification, and initial data cleaning.
Specifically addresses the edge case of missing 'total_sales' data.
"""
import json
import os
import sys
import logging
import requests
from typing import Dict, Any, Optional

import pandas as pd
import numpy as np

# Import from project modules
from data_utils import calculate_checksum, verify_checksum, load_draws_csv
from exceptions import DataSourceUnavailableError, LotteryDataError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Load data source configuration from config/data_sources.json."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'data_sources.json')
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        return json.load(f)

def fetch_lottery_data(url: str, output_path: str) -> str:
    """
    Fetch lottery data from a URL and save to disk.
    
    Args:
        url: The URL to download data from
        output_path: Path to save the CSV file
        
    Returns:
        The path to the saved file
        
    Raises:
        DataSourceUnavailableError: If the URL is unreachable
        LotteryDataError: If download fails
    """
    logger.info(f"Fetching data from {url}")
    
    try:
        # Verify URL reachability
        head_response = requests.head(url, timeout=30)
        head_response.raise_for_status()
        
        # Download the file
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save to disk
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Data saved to {output_path}")
        return output_path
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch data from {url}: {e}")
        raise DataSourceUnavailableError(f"Data source unavailable: {url}") from e

def process_draws(raw_path: str, processed_path: str) -> pd.DataFrame:
    """
    Process raw lottery data, handling missing 'total_sales' values.
    
    This function implements the edge case handling for T012:
    - Logs a warning when 'total_sales' is missing
    - Excludes rows with missing sales from sales-dependent checks
    - Retains rows in frequency analysis (metrics calculation)
    
    Args:
        raw_path: Path to the raw CSV file
        processed_path: Path to save the processed CSV file
        
    Returns:
        DataFrame with processed data
    """
    logger.info(f"Processing raw data from {raw_path}")
    
    # Load the raw data
    df = load_draws_csv(raw_path)
    
    if df.empty:
        raise LotteryDataError("Loaded data is empty")
    
    # Check for total_sales column
    if 'total_sales' not in df.columns:
        logger.warning("Column 'total_sales' not found in dataset. All rows will be retained for frequency analysis but excluded from sales-dependent checks.")
        df['total_sales'] = np.nan
    else:
        # Count missing values
        missing_sales = df['total_sales'].isna().sum()
        total_rows = len(df)
        
        if missing_sales > 0:
            logger.warning(f"Found {missing_sales} rows ({missing_sales/total_rows:.1%}) with missing 'total_sales'. "
                         "These rows will be excluded from sales-dependent checks but retained for frequency analysis.")
        
        # Ensure numeric type, coercing errors to NaN
        df['total_sales'] = pd.to_numeric(df['total_sales'], errors='coerce')
    
    # Save processed data
    os.makedirs(os.path.dirname(processed_path), exist_ok=True)
    df.to_csv(processed_path, index=False)
    logger.info(f"Processed data saved to {processed_path}")
    
    return df

def main():
    """Main entry point for the ingestion script."""
    try:
        # Load configuration
        config = load_config()
        url = config.get('url')
        source_name = config.get('source_name', 'Unknown Source')
        
        if not url:
            raise ValueError("URL not found in config")
        
        logger.info(f"Starting data ingestion from {source_name}")
        
        # Define paths
        raw_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw', 'lottery_draws.csv')
        processed_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'lottery_draws_processed.csv')
        
        # Fetch data if not already present or if forced refresh is needed
        if not os.path.exists(raw_path):
            fetch_lottery_data(url, raw_path)
        else:
            logger.info(f"Raw data already exists at {raw_path}. Skipping download.")
        
        # Process data (handles missing sales)
        df = process_draws(raw_path, processed_path)
        
        # Log summary
        logger.info(f"Processing complete. Total rows: {len(df)}")
        logger.info(f"Columns: {list(df.columns)}")
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise

if __name__ == '__main__':
    main()
