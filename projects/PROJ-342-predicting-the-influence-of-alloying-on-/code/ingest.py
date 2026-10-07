import os
import sys
import logging
import json
import hashlib
import time
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from zenodo_client import DataUnavailableError, DataInsufficientError, fetch_from_zenodo
from resource_monitor import resource_monitor, ResourceLimitExceeded

def setup_logging():
    """Configure logging for the ingest module."""
    project_root = get_project_root()
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / "ingest.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def get_project_root():
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_tg_range(df: pd.DataFrame) -> bool:
    """Check if Tg values are within a reasonable range (e.g., 100K to 1500K)."""
    if 'Tg' not in df.columns:
        return False
    # Filter out non-numeric or NaN for check
    valid_tg = df['Tg'].dropna()
    if len(valid_tg) == 0:
        return False
    return valid_tg.min() > 50 and valid_tg.max() < 2000

def fetch_from_zenodo_wrapper(primary_doi: str, fallback_doi: str) -> Tuple[pd.DataFrame, str]:
    """
    Fetch data from Zenodo. Try primary DOI first, then fallback.
    Returns (DataFrame, used_doi).
    """
    logger = logging.getLogger(__name__)
    data_dir = get_project_root() / "data" / "raw"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    primary_path = data_dir / f"zenodo_{primary_doi.split('.')[-1]}.csv"
    fallback_path = data_dir / f"zenodo_{fallback_doi.split('.')[-1]}.csv"

    # Check local cache first
    if primary_path.exists():
        logger.info(f"Primary file found locally: {primary_path}")
        try:
            df = pd.read_csv(primary_path)
            if validate_tg_range(df) and len(df) > 0:
                return df, primary_doi
            else:
                logger.warning("Local primary file invalid. Re-fetching.")
        except Exception as e:
            logger.warning(f"Error reading local primary file: {e}. Re-fetching.")

    if fallback_path.exists():
        logger.info(f"Fallback file found locally: {fallback_path}")
        try:
            df = pd.read_csv(fallback_path)
            if validate_tg_range(df) and len(df) > 0:
                logger.warning("FALLBACK_USED: Using cached fallback data.")
                return df, fallback_doi
            else:
                logger.warning("Local fallback file invalid. Re-fetching.")
        except Exception as e:
            logger.warning(f"Error reading local fallback file: {e}. Re-fetching.")

    # Fetch from API
    logger.info(f"Attempting to fetch from Zenodo DOI: {primary_doi}")
    try:
        df = fetch_from_zenodo(primary_doi)
        df.to_csv(primary_path, index=False)
        logger.info(f"Primary DOI data saved to {primary_path}")
        return df, primary_doi
    except DataUnavailableError as e:
        logger.warning(f"Primary DOI {primary_doi} failed: {e}")
        logger.info(f"Attempting fallback DOI: {fallback_doi}")
        try:
            df = fetch_from_zenodo(fallback_doi)
            df.to_csv(fallback_path, index=False)
            logger.warning("FALLBACK_USED: Fallback DOI succeeded.")
            return df, fallback_doi
        except DataUnavailableError:
            raise DataUnavailableError("Both primary and fallback DOIs are unavailable.")
    except Exception as e:
        logger.error(f"Unexpected error fetching primary DOI: {e}")
        # Try fallback on unexpected error too
        logger.info(f"Attempting fallback DOI due to error: {fallback_doi}")
        try:
            df = fetch_from_zenodo(fallback_doi)
            df.to_csv(fallback_path, index=False)
            logger.warning("FALLBACK_USED: Fallback DOI succeeded after error.")
            return df, fallback_doi
        except Exception as e2:
            raise DataUnavailableError(f"Primary failed: {e}. Fallback also failed: {e2}")

def load_and_validate_data(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    """Validate and clean data."""
    if len(df) < 1:
        raise DataInsufficientError("Dataset has fewer than 1 row.")
    
    # Check for critical columns
    if 'Tg' not in df.columns:
        raise ValueError("Dataset missing 'Tg' column.")
    
    # Drop rows with missing Tg or composition
    initial_count = len(df)
    df_clean = df.dropna(subset=['Tg'])
    
    # Assuming 'composition' or similar exists, drop if missing
    # Adjust column name based on actual data structure if needed
    if 'composition' in df.columns:
        df_clean = df_clean.dropna(subset=['composition'])
    
    cleaned_count = len(df_clean)
    retention_rate = cleaned_count / initial_count if initial_count > 0 else 0.0
    
    logger.info(f"Raw rows: {initial_count}, Cleaned rows: {cleaned_count}, Retention rate: {retention_rate:.2%}")
    
    if cleaned_count < 1:
        raise DataInsufficientError("No valid rows remaining after cleaning.")
    
    return df_clean, retention_rate, initial_count, cleaned_count

def save_cleaned_data(df: pd.DataFrame, output_path: Path, logger: logging.Logger):
    """Save cleaned data to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Cleaned data saved to {output_path}")

def write_ingestion_stats(source_doi: str, retention_rate: float, raw_count: int, cleaned_count: int, project_root: Path):
    """Write ingestion statistics to JSON."""
    stats = {
        "source_doi": source_doi,
        "retention_rate": retention_rate,
        "raw_count": raw_count,
        "cleaned_count": cleaned_count
    }
    stats_path = project_root / "data" / "ingestion_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)

@resource_monitor(runtime_limit_h=2.0, memory_limit_gb=7.0)
def run_ingestion():
    """Main ingestion pipeline."""
    logger = setup_logging()
    project_root = get_project_root()
    
    # Config
    primary_doi = "10.5281/zenodo.10043838"
    fallback_doi = "10.5281/zenodo.11023456"
    
    try:
        df, used_doi = fetch_from_zenodo_wrapper(primary_doi, fallback_doi)
        logger.info(f"Data fetched successfully from {used_doi}")
        
        df_clean, rate, raw, clean = load_and_validate_data(df, logger)
        
        output_path = project_root / "data" / "processed" / "cleaned_mg.csv"
        save_cleaned_data(df_clean, output_path, logger)
        
        write_ingestion_stats(used_doi, rate, raw, clean, project_root)
        logger.info("Ingestion complete.")
        
    except DataUnavailableError as e:
        logger.error(f"DATA_UNAVAILABLE: {e}")
        raise
    except DataInsufficientError as e:
        logger.error(f"DATA_INSUFFICIENT: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {e}")
        raise

def main():
    run_ingestion()

if __name__ == "__main__":
    main()
