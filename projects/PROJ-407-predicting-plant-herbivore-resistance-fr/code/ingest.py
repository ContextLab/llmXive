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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException)
)
def retry_request(url, max_retries=3):
    """
    Execute a GET request with exponential backoff retry logic.
    
    Args:
        url: The URL to fetch.
        max_retries: Maximum number of retry attempts (passed for compatibility, 
                     actual retries handled by tenacity decorator).
                     
    Returns:
        requests.Response object.
        
    Raises:
        requests.exceptions.RequestException: If all retries fail.
    """
    response = requests.get(url)
    response.raise_for_status()
    return response

def compute_sha256(filepath):
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_raw_dataset():
    """
    Load the raw dataset from HuggingFace using streaming.
    
    Returns:
        datasets.Dataset object containing the raw data.
    """
    logger.info("Loading raw dataset from plant-metabolomics/herbivore-resistance-v1...")
    try:
        dataset = load_dataset("plant-metabolomics/herbivore-resistance-v1", streaming=True)
        # Convert streaming dataset to a list for easier processing if needed, 
        # or iterate directly. For T015 we need to process it to a dataframe.
        # Since we need to save to CSV, we'll iterate and build a dataframe.
        # Note: In a real production scenario with massive data, we might stream directly 
        # to disk, but for this pipeline we assume it fits in memory for the interim step.
        
        # We need to materialize it to process it.
        # If the dataset is too large, this might fail, but the task requires 
        # saving the harmonized dataset which implies processing.
        raw_data = list(dataset['train']) # Assuming 'train' split or adjust based on actual dataset
        logger.info(f"Loaded {len(raw_data)} rows from raw dataset.")
        return pd.DataFrame(raw_data)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def extract_resistance_column(df):
    """
    Extract and validate the resistance column.
    
    Args:
        df: pandas DataFrame with raw data.
        
    Returns:
        pandas Series of resistance values.
        
    Raises:
        ValueError: If resistance column is missing or non-numeric.
    """
    if 'resistance' not in df.columns:
        logger.error("Column 'resistance' not found in dataset.")
        raise ValueError("No quantifiable resistance metric found")
    
    resistance = pd.to_numeric(df['resistance'], errors='coerce')
    if resistance.isna().all():
        logger.error("All resistance values are non-numeric.")
        raise ValueError("No quantifiable resistance metric found")
    
    return resistance

def convert_categorical_to_ordinal(df):
    """
    Convert categorical resistance values to ordinal.
    
    Args:
        df: pandas DataFrame.
        
    Returns:
        pandas DataFrame with 'resistance_ordinal' column.
    """
    mapping = {"Low": 1, "Medium": 2, "High": 3}
    
    # Log the mapping
    log_path = os.path.join(DATA_ROOT, 'interim', 'ordinal_mapping.log')
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w') as f:
        f.write(json.dumps(mapping))
    logger.info(f"Logged ordinal mapping to {log_path}")
    
    df['resistance_ordinal'] = df['resistance'].map(mapping)
    
    # Check for unmapped values if original was categorical
    if df['resistance_ordinal'].isna().any() and not pd.api.types.is_numeric_dtype(df['resistance']):
        logger.warning("Some resistance values could not be mapped to ordinal.")
        
    return df

def check_herbivore_density_normalization(df):
    """
    Check for herbivore_density column. If missing, log to metadata.json.
    
    Args:
        df: pandas DataFrame.
        
    Returns:
        pandas DataFrame.
    """
    metadata_path = os.path.join(DATA_ROOT, 'interim', 'metadata.json')
    os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
    
    metadata = {}
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
    
    if 'herbivore_density' not in df.columns:
        metadata['herbivore_density_missing'] = True
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.warning("herbivore_density column missing. Updated metadata.json.")
    else:
        metadata['herbivore_density_missing'] = False
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
    return df

def harmonize_dataset(df):
    """
    Perform harmonization steps:
    1. Ensure resistance is numeric (or ordinal).
    2. Handle missing values in metabolite columns (placeholder for T019 logic if needed here, 
       but T019 says apply KNN in preprocess). 
       However, T015 requires an 'imputation_flag' column. 
       We will flag rows that currently have missing values in any metabolite column.
    
    Args:
        df: pandas DataFrame.
        
    Returns:
        pandas DataFrame with harmonized data and imputation_flag.
    """
    # Ensure resistance is numeric
    if 'resistance' in df.columns:
        df['resistance'] = pd.to_numeric(df['resistance'], errors='coerce')
    
    # Identify metabolite columns (assuming they start with 'metabolite_')
    metabolite_cols = [col for col in df.columns if col.startswith('metabolite_')]
    
    if metabolite_cols:
        # Create imputation flag: True if ANY metabolite is missing
        df['imputation_flag'] = df[metabolite_cols].isna().any(axis=1)
    else:
        # If no metabolite columns found, assume no imputation needed
        df['imputation_flag'] = False
        
    # Drop rows with missing resistance as they cannot be used for modeling
    if 'resistance' in df.columns:
        df = df.dropna(subset=['resistance'])
        
    return df

def save_harmonized_dataset(df, output_path):
    """
    Save the harmonized dataset to CSV.
    
    Args:
        df: pandas DataFrame.
        output_path: Path to save the CSV.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved harmonized dataset to {output_path}")

def main():
    """Main execution function for T015."""
    logger.info("Starting T015: Save harmonized dataset")
    
    # Load raw data
    df = load_raw_dataset()
    
    # Extract resistance (validates existence)
    extract_resistance_column(df)
    
    # Convert categorical to ordinal if necessary (logs mapping)
    df = convert_categorical_to_ordinal(df)
    
    # Check herbivore density
    df = check_herbivore_density_normalization(df)
    
    # Harmonize and add imputation flag
    df = harmonize_dataset(df)
    
    # Save output
    output_path = os.path.join(DATA_ROOT, 'interim', 'harmonized.csv')
    save_harmonized_dataset(df, output_path)
    
    logger.info("T015 completed successfully.")

if __name__ == "__main__":
    main()
