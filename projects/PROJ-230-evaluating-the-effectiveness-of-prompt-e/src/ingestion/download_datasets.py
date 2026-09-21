"""
Dataset ingestion module for fetching and caching code translation pairs.

Fetches data from codeparrot/code-trans-py-js and bigcode/evaluation,
caches raw data to data/raw/, and extracts python_code and javascript_code columns.
"""
import os
import sys
import logging
import traceback
from pathlib import Path
from datasets import load_dataset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root is assumed to be the parent of 'src'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

def ensure_dirs():
    """Ensure the data/raw directory exists."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured data directory exists at: {DATA_RAW_DIR}")

def fetch_dataset(dataset_name, config_name=None, split="train", streaming=False):
    """
    Fetch a dataset from HuggingFace.
    
    Args:
        dataset_name: Name of the dataset on HuggingFace Hub
        config_name: Optional configuration name
        split: Which split to load (default: "train")
        streaming: If True, stream the dataset instead of loading fully into memory
        
    Returns:
        The loaded dataset object
        
    Raises:
        RuntimeError: If the dataset cannot be fetched
    """
    logger.info(f"Fetching dataset: {dataset_name}")
    if config_name:
        logger.info(f"Using config: {config_name}")
    
    try:
        if streaming:
            logger.info("Loading dataset in streaming mode")
            ds = load_dataset(
                dataset_name, 
                name=config_name, 
                split=split, 
                streaming=True
            )
        else:
            logger.info("Loading dataset fully into memory")
            ds = load_dataset(
                dataset_name, 
                name=config_name, 
                split=split
            )
        
        logger.info(f"Successfully loaded dataset: {dataset_name}")
        return ds
    except Exception as e:
        logger.error(f"Failed to fetch dataset {dataset_name}: {str(e)}")
        traceback.print_exc()
        raise RuntimeError(f"Failed to fetch dataset {dataset_name}: {str(e)}") from e

def extract_code_columns(dataset, python_col="python_code", js_col="javascript_code", output_path=None):
    """
    Extract python_code and javascript_code columns from a dataset and save to CSV.
    
    Args:
        dataset: The loaded dataset object
        python_col: Name of the Python code column
        js_col: Name of the JavaScript code column
        output_path: Optional path to save the extracted data
        
    Returns:
        List of dictionaries containing the extracted code pairs
        
    Raises:
        RuntimeError: If required columns are missing or extraction fails
    """
    logger.info(f"Extracting columns: {python_col}, {js_col}")
    
    extracted_data = []
    count = 0
    
    try:
        # Check if columns exist
        if hasattr(dataset, 'column_names'):
            if python_col not in dataset.column_names or js_col not in dataset.column_names:
                available_cols = dataset.column_names if hasattr(dataset, 'column_names') else "Unknown"
                raise RuntimeError(
                    f"Dataset does not contain required columns '{python_col}' and '{js_col}'. "
                    f"Available columns: {available_cols}"
                )
        
        # Iterate through dataset
        logger.info("Iterating through dataset entries...")
        for idx, entry in enumerate(dataset):
            if python_col in entry and js_col in entry:
                python_code = entry[python_col]
                js_code = entry[js_col]
                
                # Basic validation - ensure they are strings
                if isinstance(python_code, str) and isinstance(js_code, str):
                    if python_code.strip() and js_code.strip():
                        extracted_data.append({
                            "python_code": python_code,
                            "javascript_code": js_code,
                            "source_idx": idx
                        })
                        count += 1
                        
                        # Log progress every 100 entries
                        if count % 100 == 0:
                            logger.info(f"Processed {count} valid entries...")
                else:
                    logger.debug(f"Skipping entry {idx}: non-string types")
                    
            else:
                logger.debug(f"Skipping entry {idx}: missing columns")
        
        logger.info(f"Extracted {count} valid code pairs")
        
        # Save to CSV if output path provided
        if output_path:
            import csv
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ["python_code", "javascript_code", "source_idx"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(extracted_data)
            logger.info(f"Saved {count} entries to {output_path}")
        
        return extracted_data
        
    except Exception as e:
        logger.error(f"Failed to extract code columns: {str(e)}")
        traceback.print_exc()
        raise RuntimeError(f"Failed to extract code columns: {str(e)}") from e

def main():
    """
    Main function to fetch datasets and extract code columns.
    
    This function:
    1. Ensures data/raw directory exists
    2. Fetches codeparrot/code-trans-py-js dataset
    3. Extracts python_code and javascript_code columns
    4. Caches raw data to data/raw/code_trans_py_js.csv
    """
    logger.info("Starting dataset download and extraction process")
    
    # Ensure directories exist
    ensure_dirs()
    
    # Define output paths
    raw_output_path = DATA_RAW_DIR / "code_trans_py_js.csv"
    
    try:
        # Fetch the dataset
        # Using streaming to avoid memory issues with large datasets
        dataset = fetch_dataset(
            dataset_name="codeparrot/code-trans-py-js",
            config_name=None,
            split="train",
            streaming=True
        )
        
        # Extract code columns and save to raw data directory
        extracted_data = extract_code_columns(
            dataset=dataset,
            python_col="python_code",
            js_col="javascript_code",
            output_path=raw_output_path
        )
        
        if not extracted_data:
            logger.warning("No valid entries extracted from dataset")
            return 1
        
        logger.info(f"Successfully downloaded and cached {len(extracted_data)} code pairs to {raw_output_path}")
        return 0
        
    except Exception as e:
        logger.error(f"Dataset download failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
