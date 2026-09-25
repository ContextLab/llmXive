import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from zenodo_client import DataUnavailableError, DataInsufficientError, fetch_from_zenodo
from config.config import get_config

# Configure logging to create logs/ directory if missing
def setup_logging():
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "ingest.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def validate_tg_range(df) -> bool:
    """Basic validation that Tg values are positive."""
    if 'Tg' not in df.columns:
        return False
    # Check if any Tg values are non-positive or NaN
    return df['Tg'].notna().all() and (df['Tg'] > 0).all()

def fetch_from_zenodo_wrapper(logger: logging.Logger) -> Tuple[Optional[Path], str]:
    """
    Fetches data from Zenodo using primary DOI, falling back to secondary.
    Returns (local_path, source_doi).
    Raises DataUnavailableError if both fail.
    """
    config = get_config()
    primary_doi = os.getenv("ZENODO_PRIMARY_DOI", config.get("zenodo_primary_doi"))
    fallback_doi = os.getenv("ZENODO_FALLBACK_DOI", config.get("zenodo_fallback_doi"))
    
    raw_dir = project_root / "data" / "raw"
    raw_dir.mkdir(exist_ok=True)
    
    # Attempt primary
    try:
        logger.info(f"Attempting to fetch from primary DOI: {primary_doi}")
        local_path = fetch_from_zenodo(primary_doi, raw_dir)
        logger.info(f"Successfully fetched from primary DOI: {primary_doi}")
        return local_path, primary_doi
    except Exception as e:
        logger.warning(f"Primary DOI {primary_doi} failed: {e}")
    
    # Attempt fallback
    try:
        logger.info(f"Attempting to fetch from fallback DOI: {fallback_doi}")
        local_path = fetch_from_zenodo(fallback_doi, raw_dir)
        logger.info(f"Successfully fetched from fallback DOI: {fallback_doi}")
        return local_path, fallback_doi
    except Exception as e:
        logger.error(f"Fallback DOI {fallback_doi} also failed: {e}")
        raise DataUnavailableError("Both primary and fallback Zenodo DOIs are unreachable.")

def load_and_validate_data(file_path: Path, logger: logging.Logger) -> Any:
    """
    Loads CSV data and performs basic validation.
    Uses chunked reading if necessary to handle large files, though pandas default is usually fine for <100MB.
    """
    import pandas as pd
    
    logger.info(f"Loading data from {file_path}")
    
    # Check file size to decide on chunking strategy if needed
    # For this specific task, we assume standard pandas load is sufficient unless specified otherwise
    # but we verify row count immediately.
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Failed to load CSV: {e}")
    
    raw_count = len(df)
    logger.info(f"Loaded {raw_count} rows.")
    
    if raw_count == 0:
        raise DataInsufficientError("Dataset contains 0 rows.")
    
    if raw_count < 50:
        logger.warning(f"Dataset contains only {raw_count} rows (threshold 50). Proceeding with caution.")
    
    if 'Tg' not in df.columns:
        raise ValueError("Dataset missing 'Tg' column.")
    
    if 'composition' not in df.columns:
        raise ValueError("Dataset missing 'composition' column.")
        
    return df

def clean_data(df: Any, logger: logging.Logger) -> Tuple[Any, int, int]:
    """
    Drops records missing Tg or composition.
    Returns (cleaned_df, raw_count, cleaned_count).
    """
    raw_count = len(df)
    
    # Drop rows where Tg is null
    df_tg = df.dropna(subset=['Tg'])
    
    # Drop rows where composition is null or empty string
    df_comp = df_tg.dropna(subset=['composition'])
    df_comp = df_comp[df_comp['composition'].str.strip() != ""]
    
    cleaned_count = len(df_comp)
    dropped_count = raw_count - cleaned_count
    
    logger.info(f"Cleaning complete. Dropped {dropped_count} rows. Retained {cleaned_count} rows.")
    
    if cleaned_count == 0:
        raise DataInsufficientError("No valid rows remaining after cleaning.")
    
    return df_comp, raw_count, cleaned_count

def save_cleaned_data(df: Any, output_path: Path, logger: logging.Logger):
    """Saves the cleaned dataframe to CSV."""
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned data to {output_path}")

def write_ingestion_stats(stats: Dict[str, Any], output_path: Path, logger: logging.Logger):
    """Writes ingestion statistics to JSON."""
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Saved ingestion stats to {output_path}")

def main():
    logger = setup_logging()
    logger.info("Starting data ingestion pipeline.")
    
    try:
        # 1. Fetch Data
        file_path, source_doi = fetch_from_zenodo_wrapper(logger)
        
        # 2. Load Data
        df = load_and_validate_data(file_path, logger)
        
        # 3. Clean Data
        cleaned_df, raw_count, cleaned_count = clean_data(df, logger)
        
        # 4. Save Cleaned Data (T014 Requirement)
        processed_dir = project_root / "data" / "processed"
        processed_dir.mkdir(exist_ok=True)
        cleaned_output_path = processed_dir / "cleaned_mg.csv"
        save_cleaned_data(cleaned_df, cleaned_output_path, logger)
        
        # 5. Write Ingestion Stats (T014 Requirement)
        retention_rate = cleaned_count / raw_count if raw_count > 0 else 0.0
        stats = {
            "source_doi": source_doi,
            "raw_count": raw_count,
            "cleaned_count": cleaned_count,
            "retention_rate": retention_rate
        }
        stats_path = project_root / "data" / "ingestion_stats.json"
        write_ingestion_stats(stats, stats_path, logger)
        
        logger.info(f"Ingestion complete. Retention rate: {retention_rate:.4f}")
        
    except DataUnavailableError as e:
        logger.critical(f"Data unavailable: {e}")
        sys.exit(1)
    except DataInsufficientError as e:
        logger.critical(f"Data insufficient: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()
