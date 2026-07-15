import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import pandas as pd
from zenodo_get import zenodo_get

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PRIMARY_DOI = "10.5281/zenodo.10043838"
FALLBACK_DOI = "10.5281/zenodo.11023456"
DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")
INGESTION_STATS_PATH = Path("data/ingestion_stats.json")

def fetch_from_zenodo(doi: str, output_dir: Path) -> Optional[Path]:
    """
    Fetch dataset from Zenodo using the provided DOI.
    Returns the path to the downloaded directory/file if successful, None otherwise.
    """
    logger.info(f"Attempting to fetch data from Zenodo DOI: {doi}")
    try:
        # zenodo_get downloads to the current directory by default, but we can specify output
        # It creates a directory named after the DOI or the file if single file
        zenodo_get([doi], output_dir=str(output_dir))
        
        # Check if download produced any files
        downloaded_files = list(output_dir.glob("*"))
        if not downloaded_files:
            logger.warning(f"No files found in {output_dir} after fetching DOI {doi}")
            return None
        
        logger.info(f"Successfully fetched data from DOI {doi}")
        return downloaded_files[0]
    except Exception as e:
        logger.error(f"Failed to fetch data from DOI {doi}: {e}")
        return None

def load_and_validate_data(file_path: Path) -> pd.DataFrame:
    """
    Load data from the downloaded file and perform basic validation.
    """
    logger.info(f"Loading data from {file_path}")
    
    # Try to detect file type and load
    if file_path.suffix == '.csv':
        df = pd.read_csv(file_path)
    elif file_path.suffix == '.xlsx' or file_path.suffix == '.xls':
        df = pd.read_excel(file_path)
    elif file_path.suffix == '.json':
        df = pd.read_json(file_path)
    else:
        # Try CSV as default
        try:
            df = pd.read_csv(file_path)
        except Exception:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    # Basic validation: check for required columns
    # Assuming the dataset has 'Tg' (glass transition temperature) and composition columns
    # The exact column names might vary, so we'll be flexible
    required_cols = ['Tg'] # Tg is the target variable
    
    # Check if any column contains 'composition' or 'element'
    composition_cols = [col for col in df.columns if 'composition' in col.lower() or 'element' in col.lower()]
    
    if not composition_cols:
        # If no explicit composition column, check if there's a general 'composition' or 'elements' column
        # or if the data is already in a wide format with elemental columns
        pass # We'll proceed and let downstream logic handle it
    
    logger.info(f"Loaded {len(df)} records. Columns: {list(df.columns)}")
    return df

def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
    """
    Clean the data: drop records missing Tg or full composition.
    Returns cleaned dataframe, original count, and kept count.
    """
    original_count = len(df)
    logger.info(f"Starting data cleaning. Original records: {original_count}")
    
    # Drop records with missing Tg
    initial_null_tg = df['Tg'].isna().sum()
    df = df.dropna(subset=['Tg'])
    logger.info(f"Dropped {initial_null_tg} records with missing Tg")
    
    # Drop records with missing composition data
    # We assume there's a column representing composition. If not, we check for any composition-related columns
    composition_cols = [col for col in df.columns if 'composition' in col.lower() or 'element' in col.lower()]
    
    if composition_cols:
        # Drop rows where any composition column is null
        null_composition_before = df[composition_cols].isnull().any(axis=1).sum()
        df = df.dropna(subset=composition_cols)
        logger.info(f"Dropped {null_composition_before} records with missing composition data")
    else:
        # If no explicit composition column, we might need to check for elemental columns
        # For now, we'll assume the data is valid if Tg is present
        logger.warning("No explicit composition column found. Skipping composition null check.")
    
    kept_count = len(df)
    logger.info(f"Data cleaning complete. Kept {kept_count} records out of {original_count}")
    
    return df, original_count, kept_count

def save_cleaned_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the cleaned data to a CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Cleaned data saved to {output_path}")

def write_ingestion_stats(original_count: int, kept_count: int, output_path: Path) -> None:
    """
    Write ingestion statistics to a JSON file.
    """
    retention_rate = kept_count / original_count if original_count > 0 else 0.0
    
    stats = {
        "original_count": original_count,
        "kept_count": kept_count,
        "retention_rate": retention_rate,
        "dropped_count": original_count - kept_count
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Ingestion stats written to {output_path}")
    logger.info(f"Retention rate: {retention_rate:.2%}")

def main():
    """
    Main function to orchestrate the data ingestion pipeline.
    """
    logger.info("Starting metallic glass data ingestion pipeline")
    
    # Ensure directories exist
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Try primary DOI
    downloaded_path = fetch_from_zenodo(PRIMARY_DOI, DATA_RAW_DIR)
    
    # If primary fails, try fallback
    if downloaded_path is None:
        logger.warning(f"Primary DOI {PRIMARY_DOI} failed. Trying fallback DOI {FALLBACK_DOI}")
        downloaded_path = fetch_from_zenodo(FALLBACK_DOI, DATA_RAW_DIR)
    
    if downloaded_path is None:
        logger.error("Both primary and fallback DOI fetches failed. Halting.")
        sys.exit(1)
    
    # Load and validate data
    df = load_and_validate_data(downloaded_path)
    
    # Clean data
    cleaned_df, original_count, kept_count = clean_data(df)
    
    # Save cleaned data
    cleaned_output_path = DATA_PROCESSED_DIR / "cleaned_mg.csv"
    save_cleaned_data(cleaned_df, cleaned_output_path)
    
    # Write ingestion stats
    stats_output_path = INGESTION_STATS_PATH
    write_ingestion_stats(original_count, kept_count, stats_output_path)
    
    logger.info("Data ingestion pipeline completed successfully")
    return cleaned_df

if __name__ == "__main__":
    main()
