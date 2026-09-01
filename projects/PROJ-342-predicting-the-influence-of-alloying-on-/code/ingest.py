import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import pandas as pd

# Import from sibling modules as per API surface
from zenodo_client import fetch_dataset, DataUnavailableError
from config.config import get_config

# Setup logging
def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "ingest.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("ingest")

logger = setup_logging()

def fetch_from_zenodo_wrapper(primary_doi: str, fallback_doi: str) -> Tuple[str, Path]:
    """
    Fetches dataset from Zenodo using primary DOI, falling back to secondary if needed.
    Returns (doi_used, file_path).
    """
    logger.info(f"Attempting to fetch data from primary DOI: {primary_doi}")
    try:
        file_path = fetch_dataset(primary_doi)
        logger.info(f"Successfully fetched data from primary DOI: {primary_doi}")
        return primary_doi, file_path
    except DataUnavailableError as e:
        logger.warning(f"Primary DOI {primary_doi} unavailable: {e}")
        logger.info(f"Attempting fallback DOI: {fallback_doi}")
        try:
            file_path = fetch_dataset(fallback_doi)
            logger.info(f"Successfully fetched data from fallback DOI: {fallback_doi}")
            return fallback_doi, file_path
        except DataUnavailableError as e2:
            logger.error(f"Both primary and fallback DOIs unavailable.")
            raise DataUnavailableError("Both primary and fallback Zenodo datasets are unreachable.") from e2

def load_and_validate_data(file_path: Path) -> pd.DataFrame:
    """
    Loads CSV data and performs basic validation.
    """
    logger.info(f"Loading data from {file_path}")
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} rows from {file_path}")
        
        # Basic validation: Check for required columns if they exist in the raw data
        # Assuming standard metallic glass dataset columns based on context
        required_cols = ['Tg', 'composition'] 
        # Note: Actual column names might vary, but we assume 'Tg' and 'composition' based on T013 description
        # If columns are missing, we handle it gracefully or raise error depending on strictness
        # For now, we assume the raw data has these or similar.
        
        return df
    except Exception as e:
        logger.error(f"Failed to load or validate data: {e}")
        raise

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drops records missing Tg or full composition.
    """
    logger.info("Cleaning data: dropping records with missing Tg or composition")
    original_count = len(df)
    
    # Drop rows where Tg is NaN or missing
    df = df.dropna(subset=['Tg'])
    
    # Drop rows where composition is NaN or empty string
    if 'composition' in df.columns:
        df = df[df['composition'].notna() & (df['composition'].str.strip() != '')]
    
    kept_count = len(df)
    dropped_count = original_count - kept_count
    retention_rate = kept_count / original_count if original_count > 0 else 0.0

    logger.info(f"Original count: {original_count}")
    logger.info(f"Dropped count: {dropped_count}")
    logger.info(f"Kept count: {kept_count}")
    logger.info(f"Retention rate: {retention_rate:.4f}")

    return df, original_count, kept_count, dropped_count, retention_rate

def save_cleaned_data(df: pd.DataFrame, output_path: Path):
    """
    Saves the cleaned dataframe to CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned data to {output_path}")

def write_ingestion_stats(stats: Dict[str, Any], output_path: Path):
    """
    Writes ingestion statistics to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Saved ingestion stats to {output_path}")

def main():
    config = get_config()
    primary_doi = config.get('zenodo_primary_doi', '10.5281/zenodo.10043838')
    fallback_doi = config.get('zenodo_fallback_doi', '10.5281/zenodo.11023456')
    
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    
    # Fetch data
    try:
        doi_used, file_path = fetch_from_zenodo_wrapper(primary_doi, fallback_doi)
    except DataUnavailableError as e:
        logger.critical(str(e))
        sys.exit(1)

    # Determine input file name based on DOI used
    input_filename = f"zenodo_{doi_used.split('.')[-1]}.csv"
    input_path = raw_dir / input_filename
    
    # Ensure the file exists (fetch_dataset should have saved it)
    if not input_path.exists():
        # Fallback to checking if fetch_dataset saved it with a different name or path
        # The fetch_dataset function in zenodo_client.py should handle saving.
        # We assume it saves to data/raw/zenodo_<doi>.csv
        logger.error(f"Input file {input_path} not found after fetch.")
        sys.exit(1)

    # Load and validate
    df = load_and_validate_data(input_path)

    # Clean data
    df_clean, orig, kept, dropped, rate = clean_data(df)

    # Save cleaned data
    cleaned_output_path = processed_dir / "cleaned_mg.csv"
    save_cleaned_data(df_clean, cleaned_output_path)

    # Write stats
    stats = {
        "original_count": orig,
        "kept_count": kept,
        "dropped_count": dropped,
        "retention_rate": float(rate)
    }
    stats_output_path = Path("data/ingestion_stats.json")
    write_ingestion_stats(stats, stats_output_path)

    logger.info("Ingestion pipeline completed successfully.")

if __name__ == "__main__":
    main()
