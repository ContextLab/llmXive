import os
import sys
import logging
import yaml
import requests
import pandas as pd
from pathlib import Path

# Import utilities from sibling module
from utils import log_setup, checksum_file, causal_language_scanner

# Import config constants
from config import DATA_ROOT, RESULTS_ROOT, RANDOM_SEED

def load_schema_contract(schema_path: str) -> dict:
    """Load and return the dataset schema contract."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema contract not found at {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_structure(data: pd.DataFrame, schema: dict) -> bool:
    """Validate that the dataframe matches the expected schema columns."""
    required_cols = schema.get('required_columns', [])
    missing = [col for col in required_cols if col not in data.columns]
    if missing:
        logging.error(f"Missing required columns: {missing}")
        return False
    return True

def download_data(url: str, output_path: str) -> bool:
    """Download data from a verified public URL."""
    logging.info(f"Downloading data from {url} to {output_path}")
    try:
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(response.content)
        logging.info(f"Download complete. Checksum: {checksum_file(output_path)}")
        return True
    except Exception as e:
        logging.error(f"Failed to download data: {e}")
        raise

def process_hilda(raw_path: str) -> pd.DataFrame:
    """Parse HILDA raw file and extract required columns."""
    logging.info(f"Parsing HILDA data from {raw_path}")
    try:
        df = pd.read_csv(raw_path)
        # Map HILDA specific columns to standard schema if necessary
        # Assuming raw columns match schema for this implementation
        logging.info(f"HILDA data loaded: {len(df)} rows, {len(df.columns)} columns")
        return df
    except Exception as e:
        logging.error(f"Failed to parse HILDA data: {e}")
        raise

def process_ess(raw_path: str) -> pd.DataFrame:
    """Parse ESS raw file and extract required columns."""
    logging.info(f"Parsing ESS data from {raw_path}")
    try:
        df = pd.read_csv(raw_path)
        logging.info(f"ESS data loaded: {len(df)} rows, {len(df.columns)} columns")
        return df
    except Exception as e:
        logging.error(f"Failed to parse ESS data: {e}")
        raise

def process_addhealth(raw_path: str) -> pd.DataFrame:
    """Parse AddHealth raw file and extract required columns."""
    logging.info(f"Parsing AddHealth data from {raw_path}")
    try:
        df = pd.read_csv(raw_path)
        logging.info(f"AddHealth data loaded: {len(df)} rows, {len(df.columns)} columns")
        return df
    except Exception as e:
        logging.error(f"Failed to parse AddHealth data: {e}")
        raise

def validate_and_save(df: pd.DataFrame, schema: dict, output_path: str):
    """Validate dataframe against schema and save to disk."""
    logging.info(f"Validating dataframe against schema...")
    if not validate_schema_structure(df, schema):
        raise ValueError("Schema validation failed")
    
    logging.info(f"Saving processed data to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logging.info(f"Data saved successfully. Total rows: {len(df)}")

def main():
    """Main entry point for data ingestion."""
    # Setup logging as per T020 requirement
    logger = log_setup(level=logging.INFO, destination='stdout')
    
    logging.info("Starting data ingestion pipeline")
    
    # Define paths
    schema_path = "contracts/dataset.schema.yaml"
    raw_dir = Path(DATA_ROOT) / "raw"
    processed_dir = Path(DATA_ROOT) / "processed"
    
    # Ensure directories exist
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    
    # Load schema
    try:
        schema = load_schema_contract(schema_path)
        logging.info("Schema contract loaded successfully")
    except Exception as e:
        logging.error(f"Failed to load schema: {e}")
        sys.exit(1)
    
    # Example: Process a hypothetical downloaded file
    # In a real run, download_data would be called first
    raw_file = raw_dir / "hilda_data.csv"
    if not raw_file.exists():
        logging.warning(f"Raw file {raw_file} not found. Skipping ingestion.")
        return

    # Process data
    df = process_hilda(str(raw_file))
    
    # Validate and save
    output_file = processed_dir / "participants_cleaned.csv"
    validate_and_save(df, schema, str(output_file))
    
    logging.info("Data ingestion pipeline completed successfully")

if __name__ == "__main__":
    main()
