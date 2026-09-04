import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import pandas as pd
import numpy as np

# Import from project modules as per API surface
from zenodo_client import fetch_dataset, DataUnavailableError
from config.config import get_config
from checksums import calculate_file_checksum

# --- Constants ---
# Physically plausible range for Glass Transition Temperature (Tg) in Kelvin
# Metallic glasses typically form between 300K and 1000K.
# We allow a slightly wider safety margin (200K - 1200K) for outlier detection.
MIN_TG_K = 200.0
MAX_TG_K = 1200.0
Tg_COLUMN = 'Tg'

# --- Logging Setup ---
def setup_logging():
    """Configure logging for the ingestion pipeline."""
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

# --- Helper Functions ---

def validate_tg_range(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[int], Dict[str, Any]]:
    """
    Validates Tg values against physically plausible bounds.
    
    Args:
        df: Input dataframe containing Tg column.
        
    Returns:
        Tuple of:
            - Cleaned dataframe (rows with invalid Tg removed)
            - List of indices flagged as outliers
            - Stats dictionary with counts
    """
    if Tg_COLUMN not in df.columns:
        logger.warning(f"Column '{Tg_COLUMN}' not found in dataframe. Skipping Tg validation.")
        return df, [], {"total": 0, "invalid": 0, "flagged_indices": []}

    # Identify rows where Tg is outside the valid range
    # We treat NaN/None as missing data (handled by clean_data), 
    # but here we specifically check for values that are physically impossible.
    invalid_mask = (df[Tg_COLUMN] < MIN_TG_K) | (df[Tg_COLUMN] > MAX_TG_K)
    
    # Also check for NaN in this specific context if not already handled, 
    # though clean_data handles general missingness.
    # We focus on the numeric range violation here.
    
    flagged_indices = df[invalid_mask].index.tolist()
    count_invalid = len(flagged_indices)
    total_count = len(df)
    
    stats = {
        "total_records_checked": total_count,
        "invalid_tg_count": count_invalid,
        "flagged_indices": flagged_indices,
        "min_valid_tg": float(df.loc[~invalid_mask, Tg_COLUMN].min()) if not df.loc[~invalid_mask].empty else None,
        "max_valid_tg": float(df.loc[~invalid_mask, Tg_COLUMN].max()) if not df.loc[~invalid_mask].empty else None,
        "threshold_min": MIN_TG_K,
        "threshold_max": MAX_TG_K
    }
    
    if count_invalid > 0:
        logger.warning(f"Found {count_invalid} records with Tg outside [{MIN_TG_K}, {MAX_TG_K}] K. Flagging for review.")
        # Log specific values for debugging
        invalid_rows = df.loc[invalid_mask, [Tg_COLUMN, 'Composition']] # Assuming Composition exists for context
        logger.debug(invalid_rows.head().to_string())
        
        # Remove invalid rows from the dataframe to ensure downstream physics consistency
        df_cleaned = df[~invalid_mask].reset_index(drop=True)
    else:
        logger.info("All Tg values are within physically plausible range.")
        df_cleaned = df

    return df_cleaned, flagged_indices, stats

def fetch_from_zenodo_wrapper(primary_doi: str, fallback_doi: str, output_dir: Path) -> Path:
    """
    Fetches dataset from Zenodo, trying primary then fallback DOI.
    Returns path to the saved CSV file.
    """
    logger.info(f"Attempting to fetch data from Zenodo DOI: {primary_doi}")
    try:
        file_path = fetch_dataset(primary_doi, output_dir)
        logger.info(f"Successfully fetched from primary DOI: {primary_doi}")
        return file_path
    except DataUnavailableError:
        logger.warning(f"Primary DOI {primary_doi} unavailable. Trying fallback: {fallback_doi}")
        try:
            file_path = fetch_dataset(fallback_doi, output_dir)
            logger.warning(f"Fallback DOI {fallback_doi} used successfully.")
            return file_path
        except DataUnavailableError:
            logger.error(f"Both primary ({primary_doi}) and fallback ({fallback_doi}) DOIs are unavailable.")
            raise DataUnavailableError("Both Zenodo DOIs failed to provide data.")

def load_and_validate_data(file_path: Path) -> pd.DataFrame:
    """Load CSV and perform basic schema checks."""
    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    logger.info(f"Loading data from {file_path}")
    df = pd.read_csv(file_path)
    
    # Basic schema check: ensure Tg column exists
    if Tg_COLUMN not in df.columns:
        raise ValueError(f"Required column '{Tg_COLUMN}' missing in {file_path}")
    
    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop records missing Tg or full composition.
    (Standard cleaning logic from T013)
    """
    initial_count = len(df)
    
    # Drop rows with missing Tg
    df = df.dropna(subset=[Tg_COLUMN])
    
    # Assuming 'Composition' or similar column exists; if not, we assume other logic handles it.
    # Based on T013 description: "drop records missing Tg or full composition"
    # We check for a 'Composition' column if it exists, otherwise just Tg.
    if 'Composition' in df.columns:
        df = df.dropna(subset=['Composition'])
    
    final_count = len(df)
    logger.info(f"Cleaned data: {initial_count} -> {final_count} rows.")
    return df

def save_cleaned_data(df: pd.DataFrame, output_path: Path):
    """Save cleaned dataframe to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned data to {output_path}")

def write_ingestion_stats(stats: Dict[str, Any], output_path: Path):
    """Write ingestion statistics to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Wrote ingestion stats to {output_path}")

def main():
    """
    Main entry point for the ingestion pipeline.
    Implements T012, T013, T014, T015, T016, and T063 (Tg validation).
    """
    config = get_config()
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    stats_path = Path("data/ingestion_stats.json")
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    # DOIs from config or defaults
    primary_doi = os.getenv("ZENODO_PRIMARY_DOI", "10.5281/zenodo.10043838")
    fallback_doi = os.getenv("ZENODO_FALLBACK_DOI", "10.5281/zenodo.11023456")
    
    source_doi = None
    file_path = None
    
    # 1. Fetch Data (T012, T015)
    try:
        file_path = fetch_from_zenodo_wrapper(primary_doi, fallback_doi, raw_dir)
        source_doi = primary_doi if str(file_path).endswith(primary_doi.split('/')[-1]) else fallback_doi
    except DataUnavailableError as e:
        logger.critical(str(e))
        sys.exit(1)
    
    # 2. Load Data (T012)
    try:
        df = load_and_validate_data(file_path)
    except (FileNotFoundError, ValueError) as e:
        logger.error(str(e))
        sys.exit(1)
    
    # 3. Tg Range Validation (T063 - NEW)
    # This step flags and removes physically impossible Tg values BEFORE general cleaning
    df, invalid_indices, tg_validation_stats = validate_tg_range(df)
    
    # 4. General Cleaning (T013)
    df = clean_data(df)
    
    # 5. Save Cleaned Data (T014)
    output_csv = processed_dir / "cleaned_mg.csv"
    save_cleaned_data(df, output_csv)
    
    # 6. Calculate Retention Rate (T014, T016)
    # We need the original count before any cleaning to calculate retention
    # Since we didn't store original count in a variable easily accessible here, 
    # we assume the input file row count was the starting point.
    # Let's re-calculate based on the file we read.
    original_count = len(pd.read_csv(file_path))
    retention_rate = len(df) / original_count if original_count > 0 else 0.0
    
    # 7. Write Stats (T012, T014, T016)
    ingestion_stats = {
        "source_doi": source_doi,
        "original_row_count": original_count,
        "cleaned_row_count": len(df),
        "retention_rate": retention_rate,
        "tg_validation": tg_validation_stats,
        "checksum": calculate_file_checksum(file_path)
    }
    write_ingestion_stats(ingestion_stats, stats_path)
    
    logger.info("Ingestion pipeline completed successfully.")

if __name__ == "__main__":
    main()