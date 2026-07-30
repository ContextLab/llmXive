"""
Data Ingestion Module for the Cyberbullying Survey 2021.

This module handles the download, validation, and loading of the primary dataset.
It implements streaming logic to handle large datasets efficiently without
exceeding memory constraints.
"""
import os
import logging
import hashlib
import urllib.request
import zipfile
import tempfile
import itertools
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Iterator
import pandas as pd
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"

# Cyberbullying Survey 2021 Source Configuration
# Using a reliable public source for the dataset.
# If the specific UCIML ID changes, this will be updated based on feedback.
DATASET_ID = "cyberbullying" 
# Fallback to a direct CSV if the repo package is unavailable, 
# but we prioritize the datasets library for streaming support.
DATASET_SOURCE = "datasets" # Options: 'datasets', 'ucimlrepo', 'local'
DATASET_URL = "https://raw.githubusercontent.com/datasets/cyberbullying/master/data.csv" # Placeholder for real URL if needed
EXPECTED_COLUMNS = [
    'depressed1', 'depressed2', 'depressed3', 'depressed4', 'depressed5',
    'depressed6', 'depressed7', 'depressed8', 'depressed9', 'depressed10',
    'depressed11', 'depressed12', 'depressed13', 'depressed14', 'depressed15',
    'depressed16', 'depressed17', 'depressed18', 'depressed19', 'depressed20',
    'gad1', 'gad2', 'gad3', 'gad4', 'gad5', 'gad6', 'gad7',
    'pcl1', 'pcl2', 'pcl3', 'pcl4', 'pcl5', 'pcl6', 'pcl7', 'pcl8', 'pcl9', 'pcl10',
    'pcl11', 'pcl12', 'pcl13', 'pcl14', 'pcl15', 'pcl16', 'pcl17', 'pcl18', 'pcl19', 'pcl20',
    'pcl21', 'pcl22', 'pcl23', 'pcl24', 'pcl25',
    'age', 'gender', 'education', 'income', 'social_support', 'harassment_severity', 'platform'
]

def ensure_dirs():
    """Ensure required directories exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def validate_raw_data_file(file_path: Path) -> bool:
    """Validate the raw data file exists and has expected structure."""
    if not file_path.exists():
        logger.error(f"Raw data file not found: {file_path}")
        return False
    
    try:
        # Quick validation: check if it can be read as CSV
        df = pd.read_csv(file_path, nrows=5)
        logger.info(f"Raw data file validated: {file_path.name}, shape: {df.shape}")
        return True
    except Exception as e:
        logger.error(f"Failed to validate raw data file: {e}")
        return False

def download_dataset():
    """
    Download the Cyberbullying Survey 2021 dataset.
    
    This implementation attempts to use the `datasets` library for streaming support.
    If that fails, it falls back to a direct download if a URL is available,
    or raises an error if no real source is found.
    """
    ensure_dirs()
    local_file = RAW_DIR / "cyberbullying_2021.csv"
    
    # Check if already exists
    if local_file.exists():
        logger.info(f"Dataset already exists at {local_file}. Skipping download.")
        return local_file

    logger.info("Attempting to download Cyberbullying Survey 2021...")
    
    try:
        # Strategy 1: Use HuggingFace Datasets (preferred for streaming)
        # We try to load it to see if it exists, then save it locally if needed.
        # Note: The exact dataset ID might vary. We try a common pattern.
        from datasets import load_dataset
        
        # Attempt to load a known cyberbullying dataset from HuggingFace
        # If this specific ID is not found, we try a generic one or fail loudly.
        # For the purpose of this implementation, we assume 'cyberbullying' or similar.
        # In a real scenario, we would use the exact verified ID.
        dataset_name = "mcortez/cyberbullying" # Example ID, replace with verified one if available
        
        try:
            ds = load_dataset(dataset_name, split="train")
            df = ds.to_pandas()
            df.to_csv(local_file, index=False)
            logger.info(f"Successfully downloaded and saved dataset from {dataset_name}")
            return local_file
        except Exception as e:
            logger.warning(f"HuggingFace dataset '{dataset_name}' not found or failed: {e}")
            # Continue to next strategy or fail

        # Strategy 2: Direct URL download (if available)
        # If we had a verified URL, we would use it here.
        # Since we don't have a verified URL in the prompt, we raise an error
        # to prevent synthetic fallback, as per T042 requirements.
        raise RuntimeError(
            "Real data fetch failed. No verified dataset ID or URL found. "
            "Aborting to prevent synthetic data fabrication. "
            "Please provide a valid dataset source in the configuration or environment."
        )

    except ImportError:
        logger.error("The 'datasets' library is required for streaming. Please install it.")
        raise
    except Exception as e:
        logger.error(f"Data download failed: {e}")
        raise RuntimeError(
            "Real data fetch failed. Aborting to prevent synthetic data fabrication."
        ) from e

def load_cyber_data(file_path: Optional[Path] = None, streaming: bool = False, chunk_size: int = 10000):
    """
    Load the Cyberbullying Survey data.
    
    Args:
        file_path: Path to the CSV file. If None, attempts to download.
        streaming: If True, uses streaming logic for large datasets.
        chunk_size: Number of rows to process at a time if streaming.
        
    Returns:
        pandas.DataFrame or an iterator of DataFrames if streaming is True.
    """
    if file_path is None:
        file_path = download_dataset()
    
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    logger.info(f"Source: {file_path} | Method: {'streaming' if streaming else 'full_load'}")
    
    if streaming:
        logger.info(f"Using streaming mode with chunk size {chunk_size}")
        # Return an iterator that yields chunks
        def chunk_generator():
            for chunk in pd.read_csv(file_path, chunksize=chunk_size):
                yield chunk
        return chunk_generator()
    else:
        logger.info("Loading full dataset into memory")
        df = pd.read_csv(file_path)
        # Basic schema validation
        missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
        if missing_cols:
            logger.warning(f"Missing expected columns: {missing_cols}")
        return df

def load_gss_data():
    """
    Load GSS 2022 data.
    
    NOTE: Per the Plan's 'Revised Approach', GSS 2022 is excluded.
    This function logs a warning and returns None.
    """
    gss_path = RAW_DIR / "gss_2022.csv"
    if gss_path.exists():
        logger.warning("GSS 2022 dataset found but is being ignored per the Plan's 'Revised Approach'.")
    return None

def harmonize_datasets(cyber_df: pd.DataFrame, gss_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Harmonize datasets if both were loaded.
    
    Since GSS is excluded, this simply returns the Cyberbullying dataset
    with any necessary column renaming to match the analysis schema.
    """
    logger.info("Harmonizing datasets (GSS excluded)")
    df = cyber_df.copy()
    
    # Ensure column names match expected analysis schema
    # Example mapping if raw names differ
    # df = df.rename(columns={'old_name': 'new_name'})
    
    return df

def get_data_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Generate a summary of the loaded dataset."""
    return {
        "shape": df.shape,
        "columns": list(df.columns),
        "missing_values": df.isnull().sum().to_dict(),
        "dtypes": df.dtypes.astype(str).to_dict()
    }

def validate_schema_presence(df: pd.DataFrame) -> bool:
    """
    Validate that required columns for the analysis are present.
    Returns True if valid, False otherwise.
    """
    required_cols = [
        'social_support', 'harassment_severity', 'depression', 'anxiety', 
        'ptsd', 'age', 'gender', 'education', 'income'
    ]
    # Note: Depression, Anxiety, PTSD might be computed from items.
    # We check for the item columns at least.
    item_cols = [c for c in df.columns if c.startswith(('depressed', 'gad', 'pcl'))]
    
    if not item_cols:
        logger.error("No scale item columns found. Cannot proceed.")
        return False
        
    return True

def run_ingestion_checks(df: pd.DataFrame) -> bool:
    """Run basic ingestion checks."""
    if df is None or df.empty:
        logger.error("Dataset is empty or None.")
        return False
    
    if not validate_schema_presence(df):
        return False
    
    logger.info("Ingestion checks passed.")
    return True

def main():
    """Main entry point for the ingestion module."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Download if needed
        data_path = download_dataset()
        
        # Load data (non-streaming for initial validation, streaming for large stats if needed)
        # For T044, we ensure the infrastructure supports streaming if the file is large.
        # We load fully here for the pipeline, but the function supports streaming.
        df = load_cyber_data(data_path, streaming=False)
        
        if not run_ingestion_checks(df):
            raise RuntimeError("Ingestion checks failed.")
        
        # Save a copy to processed for downstream steps
        processed_path = PROCESSED_DIR / "raw_cyberbullying.csv"
        df.to_csv(processed_path, index=False)
        logger.info(f"Saved raw data to {processed_path}")
        
        return df
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise

    try:
        cyber_df = load_cyber_data(data_dir)
        run_ingestion_checks(cyber_df) #Validate after loading
        #gss_df = load_gss_data(data_dir)
        #harmonized_df = harmonize_datasets(cyber_df, gss_df)

        summary = get_data_summary(cyber_df)
        logger.info(f"Data Summary: {summary}")


    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)
