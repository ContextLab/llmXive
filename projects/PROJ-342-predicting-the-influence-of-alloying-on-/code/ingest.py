import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import pandas as pd
import requests

from config.config import get_config
from contracts.schema_loader import DatasetSchemaLoader, SchemaValidationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PRIMARY_DOI = "10.5281/zenodo.10043838"
FALLBACK_DOI = "10.5281/zenodo.11023456"
ZENOORD_API_URL = "https://zenodo.org/api/records"
DATASET_COLUMNS = [
    'Tg', 'composition', 'element_1', 'element_2', 'element_3', 
    'element_4', 'element_5', 'at_percent_1', 'at_percent_2', 
    'at_percent_3', 'at_percent_4', 'at_percent_5'
]

def fetch_from_zenodo(doi: str) -> Optional[pd.DataFrame]:
    """
    Fetch data from Zenodo using a DOI.
    
    Args:
        doi: The DOI of the dataset.
        
    Returns:
        A pandas DataFrame containing the dataset, or None if fetch fails.
    """
    logger.info(f"Attempting to fetch data for DOI: {doi}")
    
    try:
        # Zenodo API expects the record ID, not the full DOI string
        # The record ID is usually the number after zenodo. in the DOI
        # e.g., 10.5281/zenodo.10043838 -> 10043838
        record_id = doi.split('.')[-1]
        url = f"{ZENOORD_API_URL}/{record_id}"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # Check if files are available
        if 'files' not in data:
            logger.warning(f"No files found for DOI {doi}")
            return None
        
        # Find the CSV file
        csv_file = None
        for file_entry in data['files']:
            if file_entry['key'].endswith('.csv'):
                csv_file = file_entry
                break
        
        if not csv_file:
            logger.warning(f"No CSV file found for DOI {doi}")
            return None
        
        # Download the CSV file
        download_url = csv_file['links']['self']
        file_response = requests.get(download_url, timeout=60)
        file_response.raise_for_status()
        
        # Save to temporary location and read
        temp_path = Path(f"/tmp/zenodo_{record_id}.csv")
        with open(temp_path, 'wb') as f:
            f.write(file_response.content)
        
        df = pd.read_csv(temp_path)
        temp_path.unlink()  # Clean up
        
        logger.info(f"Successfully fetched {len(df)} rows for DOI {doi}")
        return df
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data for DOI {doi}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching data for DOI {doi}: {e}")
        return None

def load_and_validate_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate the loaded data against the schema.
    
    Args:
        df: The raw DataFrame.
        
    Returns:
        The validated DataFrame.
        
    Raises:
        SchemaValidationError: If the data does not match the schema.
    """
    logger.info("Validating data against schema...")
    
    # Basic validation: check for required columns
    required_cols = ['Tg', 'composition']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise SchemaValidationError(f"Missing required columns: {missing_cols}")
    
    # Check for at least some data
    if len(df) == 0:
        raise SchemaValidationError("Dataframe is empty after loading")
    
    logger.info(f"Data validation passed. {len(df)} rows loaded.")
    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the data by dropping records missing Tg or full composition.
    
    This implements FR-001: Drop records missing Tg or full composition.
    
    Args:
        df: The raw DataFrame.
        
    Returns:
        The cleaned DataFrame with missing values removed.
    """
    logger.info("Starting data cleaning...")
    initial_count = len(df)
    
    # Drop records missing Tg
    df_clean = df.dropna(subset=['Tg'])
    dropped_tg = initial_count - len(df_clean)
    if dropped_tg > 0:
        logger.info(f"Dropped {dropped_tg} records missing Tg values.")
    
    # Drop records missing full composition
    # A full composition is considered present if the 'composition' field is not null/empty
    # and all element/at_percent columns that are present in the row have values
    # For simplicity, we drop rows where 'composition' is null or empty string
    df_clean = df_clean[df_clean['composition'].notna()]
    df_clean = df_clean[df_clean['composition'].str.strip() != '']
    
    dropped_comp = len(df) - len(df_clean) - dropped_tg
    if dropped_comp > 0:
        logger.info(f"Dropped {dropped_comp} records missing full composition.")
    
    # Additionally, if there are specific element columns, ensure they are populated
    # This handles cases where composition string exists but element data is missing
    element_cols = [col for col in df.columns if col.startswith('element_')]
    if element_cols:
        # Check if any element column has null values in the remaining rows
        # If an alloy is defined by these elements, we might need them all
        # For now, we assume if 'composition' is valid, the elements are too
        # But we can add a check if needed based on specific schema requirements
        pass
    
    final_count = len(df_clean)
    retention_rate = final_count / initial_count if initial_count > 0 else 0.0
    
    logger.info(f"Data cleaning complete. Retained {final_count} out of {initial_count} rows "
               f"(retention rate: {retention_rate:.2%}).")
    
    return df_clean

def save_cleaned_data(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the cleaned data to a CSV file.
    
    Args:
        df: The cleaned DataFrame.
        output_path: The path to save the CSV file.
    """
    logger.info(f"Saving cleaned data to {output_path}")
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def write_ingestion_stats(stats: Dict[str, Any], output_path: str) -> None:
    """
    Write ingestion statistics to a JSON file.
    
    Args:
        stats: The statistics dictionary.
        output_path: The path to save the JSON file.
    """
    logger.info(f"Writing ingestion stats to {output_path}")
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Saved ingestion stats to {output_path}")

def main():
    """
    Main entry point for the data ingestion pipeline.
    """
    config = get_config()
    
    # Determine output paths
    processed_dir = Path(config.get('data', {}).get('processed_dir', 'data/processed'))
    stats_path = Path(config.get('data', {}).get('stats_path', 'data/ingestion_stats.json'))
    cleaned_path = processed_dir / 'cleaned_mg.csv'
    
    # Fetch data from primary DOI
    df = fetch_from_zenodo(PRIMARY_DOI)
    
    # If primary fails, try fallback
    if df is None:
        logger.warning(f"Primary DOI {PRIMARY_DOI} failed. Attempting fallback...")
        df = fetch_from_zenodo(FALLBACK_DOI)
    
    # If both fail, halt
    if df is None:
        logger.error(f"Both primary and fallback DOIs failed. Halting execution.")
        sys.exit(1)
    
    try:
        # Validate data
        df = load_and_validate_data(df)
        
        # Clean data
        df_clean = clean_data(df)
        
        # Save cleaned data
        save_cleaned_data(df_clean, str(cleaned_path))
        
        # Calculate and save stats
        stats = {
            'primary_doi': PRIMARY_DOI,
            'fallback_doi': FALLBACK_DOI,
            'initial_rows': len(df),
            'cleaned_rows': len(df_clean),
            'retention_rate': len(df_clean) / len(df) if len(df) > 0 else 0.0,
            'dropped_missing_tg': len(df) - len(df_clean) - (len(df) - len(df[df['composition'].notna() & (df['composition'].str.strip() != '')])),
            'dropped_missing_composition': len(df[df['composition'].notna() & (df['composition'].str.strip() != '')]) - len(df_clean)
        }
        # Recalculate dropped counts more accurately
        initial_count = len(df)
        after_tg = len(df.dropna(subset=['Tg']))
        after_comp = len(df.dropna(subset=['Tg']).loc[df.dropna(subset=['Tg'])['composition'].notna()])
        after_comp = len(after_comp.loc[after_comp['composition'].str.strip() != ''])
        
        stats = {
            'primary_doi': PRIMARY_DOI,
            'fallback_doi': FALLBACK_DOI,
            'initial_rows': initial_count,
            'cleaned_rows': after_comp,
            'retention_rate': after_comp / initial_count if initial_count > 0 else 0.0,
            'dropped_missing_tg': initial_count - after_tg,
            'dropped_missing_composition': after_tg - after_comp
        }
        
        write_ingestion_stats(stats, str(stats_path))
        
        logger.info("Data ingestion and cleaning completed successfully.")
        
    except SchemaValidationError as e:
        logger.error(f"Schema validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during data processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()