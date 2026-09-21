import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List
import pandas as pd
from zenodo_client import DataUnavailableError, fetch_dataset

# Configure logging path
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def setup_logging():
    """Configure logging for the ingestion module."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_DIR / "ingest.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def validate_tg_range(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """Validate Tg values are within a reasonable range (e.g., > 0 and < 2000 K)."""
    if 'Tg' not in df.columns:
        raise ValueError("Dataset must contain 'Tg' column.")
    
    # Filter out obviously invalid Tg values
    valid_mask = (df['Tg'] > 0) & (df['Tg'] < 2000)
    dropped = len(df) - valid_mask.sum()
    if dropped > 0:
        logger.warning(f"Dropped {dropped} records with invalid Tg values.")
    
    return df[valid_mask].copy()

def fetch_from_zenodo_wrapper(logger: logging.Logger, primary_doi: str, fallback_doi: str) -> Tuple[str, Path]:
    """
    Fetch dataset from Zenodo using primary DOI, falling back to secondary if needed.
    Returns (doi_used, local_path).
    """
    logger.info(f"Attempting to fetch dataset from primary DOI: {primary_doi}")
    try:
        path = fetch_dataset(primary_doi)
        logger.info(f"Successfully fetched data from primary DOI: {primary_doi}")
        return primary_doi, path
    except DataUnavailableError as e:
        logger.warning(f"Primary DOI {primary_doi} failed: {e}. Attempting fallback...")
        try:
            path = fetch_dataset(fallback_doi)
            logger.warning(f"Fallback DOI {fallback_doi} succeeded.")
            return fallback_doi, path
        except DataUnavailableError as e2:
            logger.error(f"Both DOIs failed. Primary: {primary_doi}, Fallback: {fallback_doi}.")
            raise DataUnavailableError(f"Data unavailable from both sources. Primary: {e}, Fallback: {e2}")

def load_and_validate_data(file_path: Path, logger: logging.Logger, chunksize: int = 10000) -> pd.DataFrame:
    """
    Load data from CSV using chunked reading to prevent OOM.
    Aggregates statistics and validates data integrity.
    """
    logger.info(f"Loading data from {file_path} in chunks of {chunksize} rows.")
    
    chunks = []
    raw_count = 0
    null_tg_count = 0
    null_comp_count = 0
    
    # Use chunked reading
    for chunk in pd.read_csv(file_path, chunksize=chunksize):
        raw_count += len(chunk)
        
        # Count nulls for stats
        null_tg_count += chunk['Tg'].isna().sum()
        null_comp_count += chunk['composition'].isna().sum()
        
        chunks.append(chunk)
    
    if not chunks:
        raise ValueError("Dataset is empty after loading.")
    
    df = pd.concat(chunks, ignore_index=True)
    
    logger.info(f"Raw row count: {raw_count}")
    logger.info(f"Null Tg count: {null_tg_count}")
    logger.info(f"Null composition count: {null_comp_count}")
    
    return df

def clean_data(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """
    Clean data by dropping records missing Tg or composition.
    """
    initial_count = len(df)
    
    # Drop rows with missing Tg or composition
    df_clean = df.dropna(subset=['Tg', 'composition'])
    
    final_count = len(df_clean)
    retention_rate = final_count / initial_count if initial_count > 0 else 0.0
    
    logger.info(f"Cleaned data: {initial_count} -> {final_count} rows. Retention rate: {retention_rate:.2%}")
    
    return df_clean

def save_cleaned_data(df: pd.DataFrame, output_path: Path, logger: logging.Logger):
    """Save cleaned dataframe to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Cleaned data saved to {output_path}")

def write_ingestion_stats(stats: Dict[str, Any], output_path: Path, logger: logging.Logger):
    """Write ingestion statistics to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Ingestion stats saved to {output_path}")

def main():
    logger = setup_logging()
    logger.info("Starting data ingestion pipeline.")
    
    # Configuration
    primary_doi = os.getenv("ZENODO_PRIMARY_DOI", "10.5281/zenodo.10043838")
    fallback_doi = os.getenv("ZENODO_FALLBACK_DOI", "10.5281/zenodo.11023456")
    
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Fetch data
    try:
        doi_used, local_path = fetch_from_zenodo_wrapper(logger, primary_doi, fallback_doi)
    except DataUnavailableError as e:
        logger.error(f"Data unavailable: {e}")
        sys.exit(1)
    
    # Load data with streaming/chunking
    df = load_and_validate_data(local_path, logger)
    
    # Validate Tg range
    df = validate_tg_range(df, logger)
    
    # Clean data
    df_clean = clean_data(df, logger)
    
    if len(df_clean) == 0:
        logger.error("No valid data remaining after cleaning.")
        sys.exit(1)
    
    # Save cleaned data
    cleaned_path = processed_dir / "cleaned_mg.csv"
    save_cleaned_data(df_clean, cleaned_path, logger)
    
    # Write stats
    stats = {
        "source_doi": doi_used,
        "raw_count": len(df),
        "cleaned_count": len(df_clean),
        "retention_rate": len(df_clean) / len(df)
    }
    stats_path = Path("data/ingestion_stats.json")
    write_ingestion_stats(stats, stats_path, logger)
    
    logger.info("Ingestion pipeline completed successfully.")

if __name__ == "__main__":
    main()