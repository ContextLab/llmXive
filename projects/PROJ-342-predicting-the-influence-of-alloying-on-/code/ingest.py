import os
import sys
import logging
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import requests

# Import from existing modules (API Surface)
from zenodo_client import fetch_from_zenodo, DataUnavailableError, DataInsufficientError
from config.config import get_config

# Constants
PRIMARY_DOI = "10.5281/zenodo.10043838"
FALLBACK_DOI = "10.5281/zenodo.11023456"
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
LOGS_DIR = Path("logs")
INGESTION_STATS_PATH = Path("data/ingestion_stats.json")
CHUNK_SIZE = 1000

def setup_logging():
    """Configure logging to file and console."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / "ingest.log"
    
    # Ensure log file exists
    if not log_file.exists():
        log_file.touch()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode='a'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_tg_range(df: pd.DataFrame) -> pd.DataFrame:
    """Filter out Tg values outside a physically plausible range (e.g., 200K - 2000K)."""
    if 'Tg' not in df.columns:
        return df
    # Log warning for out-of-range values
    out_of_range = df[(df['Tg'] < 200) | (df['Tg'] > 2000)]
    if not out_of_range.empty:
        logging.warning(f"Found {len(out_of_range)} records with Tg outside [200, 2000] range. Filtering them out.")
        df = df[(df['Tg'] >= 200) & (df['Tg'] <= 2000)]
    return df

def fetch_from_zenodo_wrapper(doi: str, logger: logging.Logger) -> Tuple[Optional[pd.DataFrame], bool]:
    """
    Fetch data from Zenodo for a given DOI.
    Returns (DataFrame, success_flag).
    Handles chunked reading if necessary, but since Zenodo API returns a file URL,
    we download the file first then read in chunks.
    """
    logger.info(f"Attempting to fetch data from Zenodo DOI: {doi}")
    try:
        # fetch_from_zenodo returns the file path or raises an error
        file_path = fetch_from_zenodo(doi)
        if file_path is None:
            logger.error(f"Failed to fetch data for DOI: {doi}")
            return None, False
        
        logger.info(f"Successfully downloaded file: {file_path}")
        
        # Read in chunks to handle large files without loading entirely into RAM
        chunks = []
        total_rows = 0
        for chunk in pd.read_csv(file_path, chunksize=CHUNK_SIZE):
            chunks.append(chunk)
            total_rows += len(chunk)
        
        df = pd.concat(chunks, ignore_index=True)
        logger.info(f"Loaded {total_rows} rows from {doi}")
        
        # Validate Tg range
        df = validate_tg_range(df)
        
        # Check for empty dataframe after validation
        if df.empty:
            logger.warning(f"Dataset from DOI {doi} is empty after validation.")
            return df, True # Return empty df, caller handles logic
        
        return df, True
    except Exception as e:
        logger.error(f"Error fetching data for DOI {doi}: {str(e)}")
        return None, False

def load_and_validate_data(logger: logging.Logger) -> Tuple[pd.DataFrame, str]:
    """
    Load data from Zenodo with fallback logic.
    Returns (DataFrame, source_doi).
    """
    # Check local files first
    primary_path = RAW_DIR / f"zenodo_{PRIMARY_DOI.replace('.', '_')}.csv"
    fallback_path = RAW_DIR / f"zenodo_{FALLBACK_DOI.replace('.', '_')}.csv"
    
    # Ensure raw directory exists
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check primary file
    if primary_path.exists():
        logger.info(f"Found local primary file: {primary_path}")
        # Verify checksum (simplified: assume valid if exists, or re-fetch if checksums module is used)
        # For now, trust local file if exists, but we should check checksum against stored manifest if available
        # If checksum mismatch logic is needed, we would compare with data/processed/checksum_report.json
        # For this task, we attempt to load it. If it fails, we fall back.
        try:
            df = pd.read_csv(primary_path)
            if not df.empty:
                logger.info("Loaded data from primary local file.")
                return df, PRIMARY_DOI
            else:
                logger.warning("Primary local file is empty. Re-fetching.")
        except Exception as e:
            logger.warning(f"Error reading primary local file: {e}. Re-fetching.")
    
    # Try fetching from primary DOI
    df, success = fetch_from_zenodo_wrapper(PRIMARY_DOI, logger)
    if success and not df.empty:
        # Save to local file
        primary_path = RAW_DIR / f"zenodo_{PRIMARY_DOI.replace('.', '_')}.csv"
        df.to_csv(primary_path, index=False)
        logger.info(f"Saved fetched data to {primary_path}")
        return df, PRIMARY_DOI
    
    # Fallback logic
    logger.warning(f"Primary DOI {PRIMARY_DOI} failed or returned empty data. Attempting fallback: {FALLBACK_DOI}")
    logger.warning("FALLBACK_USED: Switching to fallback DOI.")
    
    df, success = fetch_from_zenodo_wrapper(FALLBACK_DOI, logger)
    if success:
        if df.empty:
            logger.error(f"Fallback DOI {FALLBACK_DOI} returned empty data.")
            raise DataInsufficientError(f"Fallback DOI returned empty dataset.")
        
        # Save to local file
        fallback_path = RAW_DIR / f"zenodo_{FALLBACK_DOI.replace('.', '_')}.csv"
        df.to_csv(fallback_path, index=False)
        logger.info(f"Saved fetched data to {fallback_path}")
        return df, FALLBACK_DOI
    
    # Both failed
    logger.error(f"Both primary ({PRIMARY_DOI}) and fallback ({FALLBACK_DOI}) DOIs failed.")
    raise DataUnavailableError("All data sources unavailable.")

def clean_data(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Clean data by dropping records missing Tg or full composition.
    """
    raw_count = len(df)
    logger.info(f"Starting cleaning. Raw count: {raw_count}")
    
    # Drop rows with missing Tg
    if 'Tg' in df.columns:
        df = df.dropna(subset=['Tg'])
    
    # Drop rows with missing composition (assuming 'composition' column exists)
    # The exact column name might vary, but based on T013 description: "drop records missing Tg or full composition"
    # We assume 'composition' is the column name. If not, we might need to adapt.
    # Let's check for common composition column names or assume 'composition'.
    composition_cols = [col for col in df.columns if 'composition' in col.lower()]
    if composition_cols:
        # Assume the first one is the main composition column
        comp_col = composition_cols[0]
        df = df.dropna(subset=[comp_col])
        # Also drop empty strings if any
        df = df[df[comp_col].str.strip() != '']
    else:
        # If no composition column found, log warning but proceed (maybe it's encoded differently)
        logger.warning("No 'composition' column found. Skipping composition null check.")
    
    cleaned_count = len(df)
    retention_rate = cleaned_count / raw_count if raw_count > 0 else 0.0
    
    logger.info(f"Cleaning complete. Raw: {raw_count}, Cleaned: {cleaned_count}, Retention Rate: {retention_rate:.4f}")
    
    # Validation for dataset size
    if cleaned_count == 0:
        logger.error("Cleaned dataset is empty.")
        raise DataInsufficientError("Cleaned dataset has 0 rows.")
    elif cleaned_count < 50:
        logger.warning(f"DataInsufficientWarning: Cleaned dataset has {cleaned_count} rows (< 50).")
        # Do NOT halt, just warn as per T012 requirements
    
    return df, raw_count, cleaned_count, retention_rate

def save_cleaned_data(df: pd.DataFrame, logger: logging.Logger) -> Path:
    """Save cleaned data to data/processed/cleaned_mg.csv"""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DIR / "cleaned_mg.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned data to {output_path}")
    return output_path

def write_ingestion_stats(source_doi: str, raw_count: int, cleaned_count: int, retention_rate: float, logger: logging.Logger):
    """Write ingestion stats to data/ingestion_stats.json"""
    stats = {
        "source_doi": source_doi,
        "raw_count": raw_count,
        "cleaned_count": cleaned_count,
        "retention_rate": retention_rate
    }
    with open(INGESTION_STATS_PATH, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Saved ingestion stats to {INGESTION_STATS_PATH}")

def main():
    """Main entry point for data ingestion."""
    logger = setup_logging()
    logger.info("Starting data ingestion pipeline (T012).")
    
    try:
        # Load and validate data from Zenodo
        df, source_doi = load_and_validate_data(logger)
        
        if df.empty:
            logger.error("Loaded dataset is empty. Halting.")
            sys.exit(1)
        
        # Clean data
        df, raw_count, cleaned_count, retention_rate = clean_data(df, logger)
        
        # Save cleaned data
        save_cleaned_data(df, logger)
        
        # Write ingestion stats
        write_ingestion_stats(source_doi, raw_count, cleaned_count, retention_rate, logger)
        
        logger.info("Data ingestion pipeline completed successfully.")
        
    except DataUnavailableError as e:
        logger.critical(f"DATA_UNAVAILABLE: {str(e)}")
        sys.exit(1)
    except DataInsufficientError as e:
        logger.critical(f"DataInsufficientError: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error during ingestion: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
