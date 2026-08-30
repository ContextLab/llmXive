"""
Ingestion module for metallic glass datasets.
Handles fetching from Zenodo, validation, cleaning, and statistics logging.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import pandas as pd

from zenodo_client import DataUnavailableError, fetch_dataset
from config.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_from_zenodo_wrapper(
    primary_doi: str,
    fallback_doi: str,
    output_path: Path
) -> pd.DataFrame:
    """
    Fetches dataset from Zenodo. Attempts primary DOI, then fallback.
    Raises DataUnavailableError if both fail.
    """
    logger.info(f"Attempting to fetch data from primary DOI: {primary_doi}")
    try:
        df = fetch_dataset(primary_doi, output_path)
        logger.info(f"Successfully fetched data from {primary_doi}")
        return df
    except DataUnavailableError as e:
        logger.warning(f"Primary DOI failed: {e}")
        logger.info(f"Attempting fallback DOI: {fallback_doi}")
        try:
            df = fetch_dataset(fallback_doi, output_path)
            logger.info(f"Successfully fetched data from {fallback_doi}")
            return df
        except DataUnavailableError as e:
            logger.error(f"Fallback DOI also failed: {e}")
            raise DataUnavailableError(
                f"Both primary ({primary_doi}) and fallback ({fallback_doi}) DOIs are unavailable."
            ) from e

def load_and_validate_data(file_path: Path) -> pd.DataFrame:
    """
    Loads CSV data and performs basic validation.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    logger.info(f"Loaded {len(df)} rows from {file_path}")
    
    # Basic validation: ensure required columns exist
    required_cols = ['Tg', 'composition']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    return df

def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int, int, float]:
    """
    Cleans the dataset:
    1. Drops rows with missing Tg values.
    2. Drops rows with missing or empty composition strings.
    
    Returns:
        Tuple of (cleaned_df, original_count, kept_count, dropped_count, retention_rate)
    """
    original_count = len(df)
    logger.info(f"Starting cleaning process on {original_count} rows")
    
    # Drop rows with missing Tg
    df_clean = df.dropna(subset=['Tg'])
    
    # Drop rows with missing or empty composition
    df_clean = df_clean[df_clean['composition'].notna() & (df_clean['composition'].str.strip() != '')]
    
    kept_count = len(df_clean)
    dropped_count = original_count - kept_count
    retention_rate = kept_count / original_count if original_count > 0 else 0.0
    
    logger.info(f"Cleaning complete. Kept: {kept_count}, Dropped: {dropped_count}, Retention Rate: {retention_rate:.2%}")
    
    return df_clean, original_count, kept_count, dropped_count, retention_rate

def save_cleaned_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Saves the cleaned dataframe to CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned data to {output_path}")

def write_ingestion_stats(
    original_count: int,
    kept_count: int,
    dropped_count: int,
    retention_rate: float,
    stats_path: Path
) -> None:
    """
    Writes ingestion statistics to a JSON file.
    """
    stats_path.parent.mkdir(parents=True, exist_ok=True)
    stats = {
        "original_count": original_count,
        "kept_count": kept_count,
        "retention_rate": retention_rate,
        "dropped_count": dropped_count
    }
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Saved ingestion stats to {stats_path}")

def main() -> None:
    """
    Main entry point for the ingestion pipeline.
    Executes the full flow: fetch, validate, clean, save, and log stats.
    """
    config = get_config()
    
    primary_doi = config.get('zenodo', {}).get('primary_doi', '10.5281/zenodo.10043838')
    fallback_doi = config.get('zenodo', {}).get('fallback_doi', '10.5281/zenodo.11023456')
    
    # Ensure output directories exist
    Path('data/raw').mkdir(parents=True, exist_ok=True)
    Path('data/processed').mkdir(parents=True, exist_ok=True)
    
    raw_output = Path('data/raw/zenodo_10043838.csv')
    cleaned_output = Path('data/processed/cleaned_mg.csv')
    stats_output = Path('data/ingestion_stats.json')
    
    try:
        # Fetch
        logger.info("Starting data fetch from Zenodo...")
        df_raw = fetch_from_zenodo_wrapper(primary_doi, fallback_doi, raw_output)
        
        # Validate
        logger.info("Validating fetched data...")
        df_validated = load_and_validate_data(raw_output)
        
        # Clean
        logger.info("Cleaning data...")
        df_clean, orig, kept, dropped, rate = clean_data(df_validated)
        
        # Save cleaned data
        save_cleaned_data(df_clean, cleaned_output)
        
        # Write stats
        write_ingestion_stats(orig, kept, dropped, rate, stats_output)
        
        logger.info("Ingestion pipeline completed successfully.")
        logger.info(f"Raw data saved to: {raw_output}")
        logger.info(f"Cleaned data saved to: {cleaned_output}")
        logger.info(f"Stats saved to: {stats_output}")
        
    except DataUnavailableError as e:
        logger.critical(f"Data unavailable: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()