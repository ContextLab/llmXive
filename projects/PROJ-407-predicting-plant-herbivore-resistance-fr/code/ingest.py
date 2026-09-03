import requests
import json
import os
import sys
import hashlib
import logging
import pandas as pd
from datasets import load_dataset
from tenacity import retry, stop_after_attempt, wait_exponential
from config import DATA_ROOT, RANDOM_SEED

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/interim/ingest.log')
    ]
)
logger = logging.getLogger(__name__)

def retry_request(url, max_retries=3):
    """Retry logic with exponential backoff for network requests."""
    @retry(stop=stop_after_attempt(max_retries), wait=wait_exponential(multiplier=1, min=1, max=4))
    def _request():
        response = requests.get(url)
        response.raise_for_status()
        return response
    return _request()

def compute_sha256(filepath):
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_raw_dataset():
    """Load the raw dataset from HuggingFace using streaming."""
    logger.info("Loading raw dataset from HuggingFace...")
    try:
        # Use streaming to handle large datasets
        dataset = load_dataset("plant-metabolomics/herbivore-resistance-v1", streaming=True)
        logger.info("Dataset loaded successfully.")
        return dataset
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def extract_resistance_column(dataset):
    """Extract and validate the resistance column."""
    logger.info("Extracting resistance column...")
    # Convert streaming dataset to a dataframe for easier manipulation
    # Note: In a real large-scale scenario, we would process chunks.
    # For this task, we assume the dataset fits in memory or is sampled.
    df = dataset['train'].to_pandas()
    
    if 'resistance' not in df.columns:
        raise ValueError("No quantifiable resistance metric found")
    
    # Ensure resistance is numeric
    if not pd.api.types.is_numeric_dtype(df['resistance']):
        # Attempt conversion if it's categorical
        logger.warning("Resistance column is not numeric. Attempting to log mapping...")
        # This function handles the conversion if needed, but here we just check
        if df['resistance'].dtype == 'object':
            logger.info(f"Resistance dtype: {df['resistance'].dtype}")
            # We rely on convert_categorical_to_ordinal to handle the actual conversion
            # but we raise if it's not convertible or missing
            pass
        else:
            raise ValueError("No quantifiable resistance metric found")
    
    return df

def convert_categorical_to_ordinal(df):
    """Convert categorical resistance to ordinal values."""
    logger.info("Converting categorical resistance to ordinal...")
    mapping = {"Low": 1, "Medium": 2, "High": 3}
    
    # Check if conversion is needed
    if df['resistance'].dtype == 'object':
        # Log the mapping to the specific file
        log_path = os.path.join(DATA_ROOT, 'interim', 'ordinal_mapping.log')
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'w') as f:
            f.write(json.dumps(mapping))
        logger.info(f"Ordinal mapping logged to {log_path}")
        
        df['resistance'] = df['resistance'].map(mapping)
        
        if df['resistance'].isna().any():
            raise ValueError("Some resistance values could not be mapped to ordinal values.")
    else:
        logger.info("Resistance is already numeric.")
    
    return df

def check_herbivore_density_normalization(df):
    """Check for herbivore_density column and log metadata if missing."""
    logger.info("Checking herbivore density normalization...")
    metadata_path = os.path.join(DATA_ROOT, 'interim', 'metadata.json')
    os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
    
    # Load existing metadata if exists
    metadata = {}
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
    
    if 'herbivore_density' not in df.columns:
        metadata['herbivore_density_missing'] = True
        logger.warning("herbivore_density column is missing.")
    else:
        metadata['herbivore_density_missing'] = False
        logger.info("herbivore_density column found.")
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return df

def harmonize_dataset(df):
    """
    Harmonize the dataset:
    1. Ensure resistance is ordinal.
    2. Add imputation_flag column (initially False, will be set by preprocess if needed, 
       but for this task we prepare the structure).
    3. Clean and standardize column names.
    """
    logger.info("Harmonizing dataset...")
    
    # Ensure resistance is ordinal (handled in previous steps, but ensure type)
    if not pd.api.types.is_numeric_dtype(df['resistance']):
        raise ValueError("Resistance column must be numeric before harmonization.")
    
    # Add imputation_flag column
    # Initially set to False. Preprocess.py will update this if imputation occurs.
    df['imputation_flag'] = False
    
    # Standardize column names (lowercase, replace spaces)
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    
    return df

def save_harmonized_dataset(df, output_path):
    """Save the harmonized dataset to CSV."""
    logger.info(f"Saving harmonized dataset to {output_path}")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info("Harmonized dataset saved.")

def main():
    """Main execution flow for T015."""
    # Load raw dataset
    dataset = load_raw_dataset()
    df = extract_resistance_column(dataset)
    
    # Convert categorical to ordinal if necessary
    df = convert_categorical_to_ordinal(df)
    
    # Check herbivore density
    df = check_herbivore_density_normalization(df)
    
    # Harmonize
    df = harmonize_dataset(df)
    
    # Save output
    output_path = os.path.join(DATA_ROOT, 'interim', 'harmonized.csv')
    save_harmonized_dataset(df, output_path)
    
    logger.info("Task T015 completed successfully.")

if __name__ == "__main__":
    main()
