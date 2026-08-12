import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PRIMARY_DOI = "10.5281/zenodo.10043838"
FALLBACK_DOI = "10.5281/zenodo.11023456"
DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"

def fetch_from_zenodo(doi: str) -> Optional[pd.DataFrame]:
    """
    Fetch data from Zenodo using the provided DOI.
    Returns a DataFrame if successful, None otherwise.
    """
    try:
        from datasets import load_dataset
        logger.info(f"Attempting to fetch data from Zenodo DOI: {doi}")
        # Zenodo data is often hosted on Hugging Face Hub with a specific pattern
        # or directly downloadable. We attempt to load via HF datasets if it maps there,
        # or handle raw download if needed.
        # For this specific project context, we assume the dataset is available via HF
        # or a direct link derived from DOI.
        # If the dataset is not on HF, we might need to use requests to download the CSV.
        
        # Attempt 1: Try loading via Hugging Face datasets (common for Zenodo mirrors)
        # The dataset ID usually follows 'zenodo/<doi>' or similar, but we need to be careful.
        # Since we don't have a guaranteed HF mapping for every DOI, we try a generic approach.
        # However, the task description implies a real source exists.
        # Let's try to construct a URL if it's a direct file, or use a known pattern.
        
        # Fallback strategy: If the DOI is known to be in a specific format, we might need
        # to handle it specifically. For now, we assume a generic loader that might fail
        # if the DOI isn't mapped in HF.
        
        # Given the constraints of "real data only", we must use the real source.
        # If the DOI 10.5281/zenodo.10043838 corresponds to a specific dataset,
        # we need to find its real location.
        # Let's assume the dataset is available via `load_dataset` with a specific config
        # or by downloading the file directly if it's a CSV.
        
        # Since I cannot browse the web to find the exact HF mapping for this DOI,
        # and I must not fabricate, I will implement the logic to attempt a fetch
        # and let it fail loudly if the source is unreachable, as per instructions.
        
        # However, for the purpose of this implementation, I will assume the dataset
        # is available via a standard HF path if it's a known research dataset,
        # or I will try to download the CSV directly from Zenodo's API.
        
        # Zenodo API URL pattern: https://zenodo.org/api/records/{id}
        # We need to extract the record ID from the DOI.
        # DOI 10.5281/zenodo.XXXXX -> Record ID is XXXXX
        
        record_id = doi.split('/')[-1]
        api_url = f"https://zenodo.org/api/records/{record_id}"
        
        import requests
        response = requests.get(api_url)
        if response.status_code != 200:
            logger.warning(f"Failed to fetch record metadata from Zenodo API: {response.status_code}")
            return None
        
        metadata = response.json()
        
        # Find the file with .csv extension
        files = metadata.get('files', [])
        csv_file = None
        for f in files:
            if f.get('key', '').endswith('.csv'):
                csv_file = f
                break
        
        if not csv_file:
            logger.warning("No CSV file found in Zenodo record files.")
            return None
        
        download_url = csv_file['links']['self']
        logger.info(f"Downloading CSV from: {download_url}")
        
        file_response = requests.get(download_url)
        if file_response.status_code != 200:
            logger.warning(f"Failed to download file: {file_response.status_code}")
            return None
        
        # Save temporarily to read with pandas
        temp_path = Path(f"/tmp/zenodo_{record_id}.csv")
        with open(temp_path, 'wb') as f:
            f.write(file_response.content)
        
        df = pd.read_csv(temp_path)
        temp_path.unlink() # Clean up
        
        return df

    except Exception as e:
        logger.error(f"Error fetching from Zenodo DOI {doi}: {str(e)}")
        return None

def load_and_validate_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Basic validation: check for essential columns.
    """
    required_cols = ['Tg', 'composition'] # Assuming these based on context
    # If composition is a string or a complex object, we handle it.
    # The task says "drop records missing Tg or full composition".
    
    # Check if required columns exist
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop records missing Tg or full composition (FR-001).
    """
    logger.info(f"Cleaning data. Initial shape: {df.shape}")
    
    # Drop rows where Tg is missing or NaN
    df_clean = df.dropna(subset=['Tg'])
    
    # Drop rows where composition is missing or NaN
    # Assuming 'composition' is a column name. If it's a list of dicts, we check for empty.
    if 'composition' in df_clean.columns:
        df_clean = df_clean[df_clean['composition'].notna()]
        # If composition is a string representation of a list, check if empty
        # This depends on the exact format. Assuming standard CSV parsing.
        # If it's a JSON string or similar, we might need to parse.
        # For now, just drop NaNs.
    
    logger.info(f"Cleaning complete. Final shape: {df_clean.shape}")
    return df_clean

def save_cleaned_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save cleaned data to CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Cleaned data saved to {output_path}")

def write_ingestion_stats(stats: Dict[str, Any], output_path: Path) -> None:
    """
    Write ingestion statistics to JSON.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Ingestion stats saved to {output_path}")

def main() -> None:
    """
    Main entry point for data ingestion and cleaning.
    """
    logger.info("Starting data ingestion and cleaning process.")
    
    # Fetch data
    df = fetch_from_zenodo(PRIMARY_DOI)
    
    if df is None:
        logger.warning(f"Primary DOI {PRIMARY_DOI} failed. Trying fallback...")
        df = fetch_from_zenodo(FALLBACK_DOI)
        if df is None:
            logger.error("Both primary and fallback DOIs failed. Halting with DATA_UNAVAILABLE.")
            # Raise an exception to halt execution as per FR-001
            raise SystemExit("DATA_UNAVAILABLE: Could not fetch data from any DOI.")
    
    # Validate
    df = load_and_validate_data(df)
    
    # Clean
    df_clean = clean_data(df)
    
    # Calculate retention rate
    original_count = len(df)
    cleaned_count = len(df_clean)
    retention_rate = cleaned_count / original_count if original_count > 0 else 0.0
    
    logger.info(f"Retention rate: {retention_rate:.2%} ({cleaned_count}/{original_count})")
    
    # Save cleaned data
    cleaned_data_path = PROCESSED_DIR / "cleaned_mg.csv"
    save_cleaned_data(df_clean, cleaned_data_path)
    
    # Write stats
    stats = {
        "original_count": original_count,
        "cleaned_count": cleaned_count,
        "retention_rate": retention_rate,
        "primary_doi": PRIMARY_DOI,
        "fallback_doi": FALLBACK_DOI,
        "output_file": str(cleaned_data_path)
    }
    stats_path = DATA_DIR / "ingestion_stats.json"
    write_ingestion_stats(stats, stats_path)
    
    logger.info("Data ingestion and cleaning completed successfully.")

if __name__ == "__main__":
    main()