import requests
import json
import os
import sys
import hashlib
import logging
import pandas as pd
from datasets import load_dataset
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from config import DATA_ROOT, RANDOM_SEED

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(DATA_ROOT, 'interim', 'ingest.log'))
    ]
)
logger = logging.getLogger(__name__)

# Retry decorator for network requests
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type((requests.exceptions.RequestException, ConnectionError))
)
def retry_request(url, max_retries=3):
    """
    Execute a GET request with exponential backoff retry logic.
    
    Args:
        url (str): The URL to request.
        max_retries (int): Maximum number of retry attempts (unused due to decorator, kept for signature).
        
    Returns:
        requests.Response: The response object if successful.
        
    Raises:
        requests.exceptions.RequestException: If all retries fail.
    """
    logger.info(f"Requesting URL: {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response

def compute_sha256(file_path):
    """
    Compute the SHA256 hash of a file.
    
    Args:
        file_path (str): Path to the file.
        
    Returns:
        str: Hexadecimal string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def extract_resistance_column(dataset):
    """
    Extract the 'resistance' column from the dataset.
    
    Args:
        dataset (datasets.Dataset): The loaded dataset.
        
    Returns:
        pd.Series: The resistance column as a pandas Series.
        
    Raises:
        ValueError: If 'resistance' column is missing or non-numeric.
    """
    if 'resistance' not in dataset.column_names:
        logger.error("Dataset columns: %s", dataset.column_names)
        raise ValueError("No quantifiable resistance metric found")
    
    resistance_col = dataset['resistance']
    try:
        resistance_series = pd.Series(resistance_col, dtype=float)
    except (ValueError, TypeError):
        logger.error("Resistance column contains non-numeric values: %s", resistance_col[:5])
        raise ValueError("No quantifiable resistance metric found")
    
    return resistance_series

def convert_categorical_to_ordinal(df):
    """
    Convert categorical resistance values to ordinal integers.
    Mapping: Low=1, Medium=2, High=3.
    
    Args:
        df (pd.DataFrame): DataFrame with a 'resistance' column.
        
    Returns:
        pd.DataFrame: DataFrame with updated 'resistance' column.
    """
    mapping = {"Low": 1, "Medium": 2, "High": 3}
    logger.info("Categorical to ordinal mapping: %s", mapping)
    
    # Log mapping to file
    log_path = os.path.join(DATA_ROOT, 'interim', 'ordinal_mapping.log')
    with open(log_path, 'w') as f:
        f.write(json.dumps(mapping))
    
    df['resistance'] = df['resistance'].map(mapping)
    
    # Check for unmapped values
    if df['resistance'].isna().any():
        logger.warning("Some resistance values could not be mapped to ordinal integers.")
        # Keep original string if mapping fails, but for this task we assume valid categories
        # or we raise an error if strictness is required. Here we log and proceed.
    
    return df

def check_herbivore_density_normalization(df):
    """
    Check if 'herbivore_density' column exists. If missing, log metadata.
    
    Args:
        df (pd.DataFrame): The dataset DataFrame.
    """
    metadata = {}
    if 'herbivore_density' not in df.columns:
        logger.warning("herbivore_density column is missing.")
        metadata["herbivore_density_missing"] = True
    
    if metadata:
        metadata_path = os.path.join(DATA_ROOT, 'interim', 'metadata.json')
        # Load existing if any, then update
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                existing_meta = json.load(f)
            existing_meta.update(metadata)
            metadata = existing_meta
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info("Updated metadata at %s", metadata_path)

def load_raw_dataset():
    """
    Load the raw dataset from HuggingFace using streaming.
    
    Returns:
        pd.DataFrame: The loaded dataset as a DataFrame.
    """
    dataset_name = "plant-metabolomics/herbivore-resistance-v1"
    logger.info(f"Loading dataset: {dataset_name}")
    
    try:
        # Use streaming to avoid loading full dataset into memory immediately
        ds = load_dataset(dataset_name, split="train", streaming=True)
        
        # Convert to DataFrame
        # Since streaming yields batches, we need to collect them
        # For a robust implementation, we iterate and build chunks
        chunks = []
        for batch in ds:
            chunks.append(pd.DataFrame(batch))
        
        if not chunks:
            raise ValueError("Dataset is empty")
        
        df = pd.concat(chunks, ignore_index=True)
        logger.info(f"Loaded {len(df)} rows from dataset.")
        return df
        
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def harmonize_dataset(df):
    """
    Perform harmonization steps:
    1. Ensure resistance is numeric/ordinal.
    2. Check herbivore density.
    3. Create imputation_flag column (initially 0 for no missing data in raw, 
       but prepared for future steps).
    
    Args:
        df (pd.DataFrame): Raw dataset DataFrame.
        
    Returns:
        pd.DataFrame: Harmonized DataFrame.
    """
    logger.info("Starting harmonization process...")
    
    # 1. Handle Resistance
    # Check if categorical or numeric
    if df['resistance'].dtype == 'object':
        logger.info("Resistance is categorical, converting to ordinal.")
        df = convert_categorical_to_ordinal(df)
    else:
        logger.info("Resistance is numeric, ensuring float type.")
        df['resistance'] = pd.to_numeric(df['resistance'], errors='raise')
    
    # 2. Check Herbivore Density
    check_herbivore_density_normalization(df)
    
    # 3. Create Imputation Flag
    # Initially, we assume no imputation has been done on raw data.
    # We mark rows that have missing values in metabolite columns for future steps.
    # Identify metabolite columns (assume they start with 'metabolite_')
    metabolite_cols = [col for col in df.columns if col.startswith('metabolite_')]
    
    if not metabolite_cols:
        logger.warning("No metabolite columns found starting with 'metabolite_'.")
    
    # Create flag: 1 if any metabolite is NaN, 0 otherwise
    if metabolite_cols:
        df['imputation_flag'] = df[metabolite_cols].isna().any(axis=1).astype(int)
    else:
        df['imputation_flag'] = 0
    
    logger.info("Harmonization complete.")
    return df

def save_harmonized_dataset(df, output_path):
    """
    Save the harmonized dataset to CSV.
    
    Args:
        df (pd.DataFrame): The harmonized DataFrame.
        output_path (str): Path to save the CSV.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved harmonized dataset to {output_path}")

def main():
    """
    Main entry point for the ingestion and harmonization pipeline.
    """
    # Ensure directories exist
    os.makedirs(os.path.join(DATA_ROOT, 'raw'), exist_ok=True)
    os.makedirs(os.path.join(DATA_ROOT, 'interim'), exist_ok=True)
    
    # 1. Load Raw Data (T010)
    # Assuming T014 has saved raw_dataset.csv, we can load from there or re-fetch.
    # Per T010 description, we fetch. Per T014, we saved. Let's load from the saved file
    # to ensure we are processing the verified artifact, unless T014 didn't run.
    # The task T015 says "Save harmonized dataset", implying input is available.
    # We will try to load from data/raw/raw_dataset.csv first.
    
    raw_csv_path = os.path.join(DATA_ROOT, 'raw', 'raw_dataset.csv')
    
    if os.path.exists(raw_csv_path):
        logger.info(f"Loading raw data from {raw_csv_path}")
        df = pd.read_csv(raw_csv_path)
    else:
        logger.warning(f"{raw_csv_path} not found. Fetching fresh from HuggingFace.")
        df = load_raw_dataset()
        # Save to raw as per T014 if it wasn't there
        save_raw_path = os.path.join(DATA_ROOT, 'raw', 'raw_dataset.csv')
        df.to_csv(save_raw_path, index=False)
        # Compute checksum
        checksum = compute_sha256(save_raw_path)
        with open(save_raw_path + '.sha256', 'w') as f:
            f.write(checksum)
    
    # 2. Harmonize Data (T015)
    df_harmonized = harmonize_dataset(df)
    
    # 3. Save Output
    output_path = os.path.join(DATA_ROOT, 'interim', 'harmonized.csv')
    save_harmonized_dataset(df_harmonized, output_path)
    
    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
