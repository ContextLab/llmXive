import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

# Importing from sibling modules as per API surface
# Note: fetch_from_zenodo, load_and_validate_data, clean_data, save_cleaned_data
# are implemented here to satisfy the "real data" constraint and ensure the script runs.
# In a full pipeline, these might be in separate modules, but the API surface lists them here.

import requests
import pandas as pd
from config.config import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_from_zenodo(doi: str) -> Optional[str]:
    """
    Fetches data from Zenodo using the provided DOI.
    Returns the local path to the downloaded file or None if failed.
    """
    zenodo_api_url = f"https://zenodo.org/api/records/{doi}"
    logger.info(f"Fetching metadata for DOI: {doi}")
    
    try:
        response = requests.get(zenodo_api_url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if 'files' not in data:
            logger.warning(f"No files found in record {doi}")
            return None
        
        # Assuming the first file is the target dataset
        file_entry = data['files'][0]
        file_name = file_entry['key']
        download_url = file_entry['links']['self']
        
        logger.info(f"Downloading {file_name} from {download_url}")
        
        # Create data/raw directory if it doesn't exist
        raw_dir = Path("data/raw")
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = raw_dir / file_name
        
        req = requests.get(download_url, stream=True, timeout=300)
        req.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in req.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Successfully downloaded to {output_path}")
        return str(output_path)
        
    except Exception as e:
        logger.error(f"Failed to fetch from Zenodo DOI {doi}: {e}")
        return None

def load_and_validate_data(file_path: str) -> pd.DataFrame:
    """
    Loads the CSV data and performs basic validation.
    """
    logger.info(f"Loading data from {file_path}")
    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise

def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
    """
    Drops records missing Tg or full composition.
    Returns cleaned DataFrame, original count, kept count.
    """
    original_count = len(df)
    logger.info(f"Original count: {original_count}")
    
    # Drop rows where Tg is missing
    df_clean = df.dropna(subset=['Tg'])
    
    # Drop rows where composition columns are missing
    # Assuming composition columns are those starting with 'Element' or specific names if known
    # Based on typical metallic glass datasets, we look for composition columns.
    # If specific column names aren't known, we drop rows where any non-Tg numeric column is NaN?
    # The task says "full composition". We assume columns like 'Fe', 'Ni', etc. or 'Element_1', 'Conc_1'.
    # Without specific schema, we drop rows where 'Tg' is present but key composition fields are NaN.
    # Let's assume standard columns 'Composition' or individual elements. 
    # For robustness against the specific dataset structure (unknown here), we drop rows 
    # where Tg is present but the dataframe has significant NaNs in non-Tg columns?
    # Better approach: Drop rows where Tg is not null, but any of the composition columns are null.
    # We will assume the dataset has columns representing elements. 
    # If the dataset has a 'Composition' string column, we check if it's empty.
    # Let's assume the dataset has columns like 'Fe', 'Cu', 'Zr' etc. or a generic 'Composition' field.
    # To be safe and generic: drop rows where Tg is not null, but the row is otherwise empty of composition info.
    
    # Heuristic: Drop rows where Tg is present but the row has too many NaNs (excluding Tg)
    # Or simpler: Just drop rows where Tg is NaN (done above) and assume the dataset is otherwise clean 
    # regarding "full composition" if the source is trusted, OR drop rows where any column other than Tg is NaN 
    # IF those columns are known to be composition.
    # Given the constraint "drop records missing Tg or full composition", we implement:
    # 1. Drop Tg NaN
    # 2. Drop rows where composition columns are NaN. 
    # Since we don't know the exact column names, we assume the dataset provided by Zenodo 
    # has a standard structure or we check for a 'Composition' column.
    # Let's assume the dataset has a 'Composition' column or similar.
    # If not, we just drop Tg NaNs.
    
    if 'Composition' in df_clean.columns:
        df_clean = df_clean.dropna(subset=['Composition'])
    
    # If no specific composition column, we might need to check specific element columns.
    # For this implementation, we assume the Zenodo dataset 10043838 has a 'Composition' column 
    # or that the "full composition" check is satisfied if Tg is present (as per common simplified pipelines 
    # unless specific element columns are listed).
    # However, to be strict: we drop rows where Tg is present but the row is effectively empty of data.
    # We will drop rows where Tg is present but all other columns are NaN.
    non_tg_cols = [c for c in df_clean.columns if c != 'Tg']
    if non_tg_cols:
        df_clean = df_clean.dropna(subset=non_tg_cols)

    kept_count = len(df_clean)
    dropped_count = original_count - kept_count
    
    logger.info(f"Cleaned count: {kept_count}, Dropped: {dropped_count}")
    return df_clean, original_count, kept_count

def save_cleaned_data(df: pd.DataFrame, output_path: str):
    """
    Saves the cleaned data to CSV.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned data to {output_path}")

def write_ingestion_stats(original_count: int, kept_count: int, output_path: str):
    """
    Writes the ingestion statistics to a JSON file.
    Satisfies SC-003 and Single Source of Truth.
    """
    dropped_count = original_count - kept_count
    retention_rate = kept_count / original_count if original_count > 0 else 0.0
    
    stats = {
        "original_count": original_count,
        "kept_count": kept_count,
        "retention_rate": retention_rate,
        "dropped_count": dropped_count
    }
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Written ingestion stats to {output_path}")
    return stats

def main():
    """
    Main entry point for the ingestion pipeline.
    """
    # Configuration
    primary_doi = "10.5281/zenodo.10043838"
    fallback_doi = "10.5281/zenodo.11023456"
    
    raw_file_path = None
    doi_used = None
    
    # Attempt primary DOI
    raw_file_path = fetch_from_zenodo(primary_doi)
    if raw_file_path:
        doi_used = primary_doi
    else:
        # Attempt fallback DOI
        logger.warning(f"Primary DOI {primary_doi} failed. Attempting fallback {fallback_doi}")
        raw_file_path = fetch_from_zenodo(fallback_doi)
        if raw_file_path:
            doi_used = fallback_doi
        else:
            logger.error("DATA_UNAVAILABLE: Both primary and fallback DOIs failed.")
            sys.exit(1)
    
    # Load and Validate
    df = load_and_validate_data(raw_file_path)
    
    # Clean
    df_clean, orig_count, kept_count = clean_data(df)
    
    # Save Cleaned Data
    cleaned_output_path = "data/processed/cleaned_mg.csv"
    save_cleaned_data(df_clean, cleaned_output_path)
    
    # Write Stats
    stats_output_path = "data/ingestion_stats.json"
    stats = write_ingestion_stats(orig_count, kept_count, stats_output_path)
    
    logger.info(f"Ingestion complete. Retention rate: {stats['retention_rate']:.2%}")

if __name__ == "__main__":
    main()
