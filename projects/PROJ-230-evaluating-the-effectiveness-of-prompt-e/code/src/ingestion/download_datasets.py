import os
import sys
import logging
import traceback
from pathlib import Path
from datasets import load_dataset
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/dataset_download.log')
    ]
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / 'data' / 'raw'

def ensure_dirs():
    """Ensure the data/raw directory exists."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured data directory exists at: {DATA_RAW_DIR}")

def fetch_dataset(dataset_name: str, split: str = "train", cache_dir: str = None):
    """
    Fetch a dataset from HuggingFace.
    
    Args:
        dataset_name: The HuggingFace dataset identifier (e.g., 'codeparrot/code-trans-py-js')
        split: The dataset split to load (default: 'train')
        cache_dir: Optional cache directory for datasets
    
    Returns:
        The loaded dataset object
    
    Raises:
        Exception: If the dataset cannot be fetched (fails loudly, no synthetic fallback)
    """
    logger.info(f"Fetching dataset: {dataset_name}, split: {split}")
    try:
        # Load dataset with explicit streaming to manage memory if large
        # We use streaming=True initially to check availability, then load normally if small enough
        # or process in chunks if large. For this specific task, we assume the dataset is manageable
        # but we use trust_remote_code=False for safety unless needed.
        dataset = load_dataset(
            dataset_name,
            split=split,
            trust_remote_code=False,
            cache_dir=cache_dir
        )
        logger.info(f"Successfully fetched dataset: {dataset_name}, size: {len(dataset)}")
        return dataset
    except Exception as e:
        logger.error(f"Failed to fetch dataset {dataset_name}: {e}")
        raise e

def extract_code_columns(dataset, output_path: Path):
    """
    Extract 'python_code' and 'javascript_code' columns from the dataset
    and save them to a CSV file.
    
    Args:
        dataset: The loaded HuggingFace dataset
        output_path: Path to the output CSV file
    """
    logger.info(f"Extracting code columns to: {output_path}")
    
    # Convert dataset to pandas DataFrame for easier manipulation
    # This is safe for the expected size of the code-trans-py-js dataset
    try:
        df = dataset.to_pandas()
    except Exception as e:
        logger.error(f"Failed to convert dataset to pandas: {e}")
        raise e
    
    # Validate and filter for required columns
    required_columns = ['python_code', 'javascript_code']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"Dataset missing required columns: {missing_columns}. "
                       f"Available columns: {list(df.columns)}")
    
    # Filter out rows where code columns are missing or not strings
    initial_count = len(df)
    df = df.dropna(subset=required_columns)
    df = df[df['python_code'].apply(lambda x: isinstance(x, str) and len(x.strip()) > 0)]
    df = df[df['javascript_code'].apply(lambda x: isinstance(x, str) and len(x.strip()) > 0)]
    
    filtered_count = len(df)
    excluded_count = initial_count - filtered_count
    
    logger.info(f"Initial entries: {initial_count}, Excluded invalid entries: {excluded_count}, "
              f"Valid entries: {filtered_count}")
    
    if filtered_count == 0:
        raise ValueError("No valid entries found in the dataset after filtering.")
    
    # Select only the required columns
    df = df[required_columns]
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {filtered_count} valid entries to {output_path}")

def main():
    """
    Main function to download, cache, and extract code columns from the dataset.
    """
    ensure_dirs()
    
    # Define dataset source and output path
    dataset_name = "codeparrot/code-trans-py-js"
    output_filename = "code_trans_py_js_raw.csv"
    output_path = DATA_RAW_DIR / output_filename
    
    # Check if already downloaded (checksum logic would be applied here in a full pipeline)
    if output_path.exists():
        logger.warning(f"Output file {output_path} already exists. Skipping download.")
        # In a real pipeline, we might verify checksums here
        return
    
    # Fetch the dataset
    try:
        dataset = fetch_dataset(dataset_name)
        extract_code_columns(dataset, output_path)
        logger.info("Dataset download and extraction completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()