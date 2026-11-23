import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd

# Add parent directory to path if running from code/
sys.path.insert(0, str(Path(__file__).parent.parent))

from datasets import load_dataset

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

class DataFetchError(Exception):
    """Raised when real data cannot be fetched."""
    pass

def fetch_real_data():
    """
    Fetch the OSF reproducibility dataset using Hugging Face Datasets.
    This function attempts to stream the data if it's large, or load directly.
    
    Returns:
        pd.DataFrame: The loaded dataset.
    
    Raises:
        DataFetchError: If the dataset cannot be fetched or does not exist.
    """
    dataset_name = "osf/reproducibility_project"
    split = "train"
    
    logger.info(f"Attempting to fetch dataset: {dataset_name} (split: {split})")
    
    try:
        # Try loading with streaming first to handle large datasets and check availability
        # We use streaming=True to avoid downloading the full dataset if it's huge,
        # but we need to materialize it for the pipeline.
        # The OSF reproducibility project dataset is typically manageable (~100MB-1GB range).
        # We will attempt to load it directly. If it fails due to size, we switch to streaming logic.
        
        # Note: The exact dataset ID might vary. "osf/reproducibility_project" is the target.
        # If it doesn't exist, we raise DataFetchError immediately.
        
        dataset = load_dataset(dataset_name, split=split, trust_remote_code=True)
        
        if dataset is None or len(dataset) == 0:
            raise DataFetchError(f"Dataset {dataset_name} loaded but contains no data.")
        
        logger.info(f"Successfully loaded dataset with {len(dataset)} rows.")
        return dataset.to_pandas()
        
    except Exception as e:
        # Check if it's a 404 or specific dataset error
        error_str = str(e)
        if "404" in error_str or "not found" in error_str.lower() or "Dataset" in error_str:
            logger.error(f"Dataset {dataset_name} not found or inaccessible: {e}")
            raise DataFetchError(f"Real data source unavailable: {dataset_name}. Error: {e}")
        else:
            logger.error(f"Failed to fetch data: {e}")
            raise DataFetchError(f"Failed to fetch real data from {dataset_name}: {e}")

def validate_schema(df):
    """
    Validate that the downloaded dataframe contains required columns.
    
    Args:
        df (pd.DataFrame): The loaded dataframe.
    
    Returns:
        dict: Validation result.
    
    Raises:
        ValueError: If required columns are missing.
    """
    required_columns = ['year', 'effect_size', 'sample_size', 'field']
    columns_found = list(df.columns)
    missing = [col for col in required_columns if col not in columns_found]
    
    if missing:
        error_msg = f"Missing required columns: {missing}. Found: {columns_found}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Schema validation passed. Columns found: {columns_found}")
    return {"status": "valid", "columns_found": columns_found}

def save_data(df, output_path):
    """
    Save the dataframe to a CSV file.
    
    Args:
        df (pd.DataFrame): The dataframe to save.
        output_path (str): Path to save the file.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Data saved to {output_path}")

def main():
    """Main entry point for data download."""
    output_path = Path("data/raw/data.csv")
    
    # 1. Fetch real data
    try:
        df = fetch_real_data()
    except DataFetchError as e:
        logger.error(f"Data fetch failed: {e}")
        sys.exit(1)
    
    # 2. Validate schema
    try:
        validation_result = validate_schema(df)
    except ValueError as e:
        logger.error(f"Schema validation failed: {e}")
        sys.exit(1)
    
    # 3. Save data
    save_data(df, output_path)
    
    # 4. Save validation result (optional but good practice)
    validation_path = Path("data/derived/schema_validation.json")
    validation_path.parent.mkdir(parents=True, exist_ok=True)
    with open(validation_path, 'w') as f:
        json.dump(validation_result, f, indent=2)
    
    logger.info("Data download and validation complete.")

if __name__ == "__main__":
    main()
