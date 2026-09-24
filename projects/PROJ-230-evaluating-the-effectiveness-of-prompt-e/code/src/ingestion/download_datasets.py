"""
Dataset Ingestion Module for PROJ-230.

This module handles the fetching of raw code translation datasets from HuggingFace
and caching them to the local filesystem before any preprocessing occurs.

Datasets:
- codeparrot/code-trans-py-js (Python to JavaScript translation pairs)
- bigcode/evaluation (Reference evaluation set, filtered for py-js pairs if available)

Outputs:
- data/raw/codeparrot_py_js.parquet (Cached raw dataset)
- data/raw/bigcode_eval_py_js.parquet (Cached raw dataset, if valid pairs found)
"""
import os
import sys
import logging
import traceback
from pathlib import Path
from datasets import load_dataset, DatasetDict
import pandas as pd

# Configure logging for the ingestion process
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Project root relative to this file (assuming code/src/ingestion/ structure)
# We navigate up to the project root to find data/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

# Dataset identifiers
DATASET_IDS = [
    "codeparrot/code-trans-py-js",
    # "bigcode/evaluation" # Note: bigcode/evaluation is often a suite of tasks.
                          # We will attempt to load the specific subset if known,
                          # or skip if it doesn't contain direct py-js pairs in the root.
                          # For now, we focus on the primary codeparrot source which is verified.
                          # If bigcode/evaluation has a specific 'py-js' split, it would be:
                          # load_dataset("bigcode/evaluation", "py-js")
]

def ensure_dirs():
    """Create the data/raw directory if it does not exist."""
    try:
        DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {DATA_RAW_DIR}")
    except Exception as e:
        logger.error(f"Failed to create directory {DATA_RAW_DIR}: {e}")
        raise

def fetch_dataset(dataset_id: str, cache_dir: Path):
    """
    Fetch a dataset from HuggingFace and cache it locally.

    Args:
        dataset_id: The HuggingFace dataset identifier.
        cache_dir: The directory where the dataset should be cached.

    Returns:
        The loaded dataset object.

    Raises:
        Exception: If the dataset cannot be loaded or does not contain required columns.
    """
    logger.info(f"Fetching dataset: {dataset_id}")
    try:
        # Load dataset with caching enabled explicitly
        # We use streaming=False initially to ensure we get the full structure for validation
        # but we will process in chunks later if needed.
        # For T013, we cache the raw data.
        ds = load_dataset(
            dataset_id,
            split="train", # Default to train if not specified, adjust if needed
            trust_remote_code=True,
            cache_dir=str(cache_dir / dataset_id.replace("/", "_"))
        )
        logger.info(f"Successfully loaded {dataset_id}. Size: {len(ds)} entries.")
        return ds
    except Exception as e:
        logger.error(f"Failed to fetch dataset {dataset_id}: {e}")
        logger.error(traceback.format_exc())
        raise

def extract_code_columns(dataset, output_path: Path):
    """
    Extract 'python_code' and 'javascript_code' columns from the dataset
    and save to a Parquet file.

    Args:
        dataset: The loaded HuggingFace dataset.
        output_path: The path to save the extracted data.

    Raises:
        ValueError: If required columns are missing.
    """
    required_columns = ["python_code", "javascript_code"]
    
    # Check if columns exist
    missing_cols = [col for col in required_columns if col not in dataset.column_names]
    if missing_cols:
        raise ValueError(f"Dataset missing required columns: {missing_cols}. "
                         f"Available columns: {dataset.column_names}")

    logger.info(f"Extracting columns {required_columns}...")
    
    # Select only the required columns
    extracted = dataset.select_columns(required_columns)
    
    # Convert to Pandas for robust saving (Parquet)
    df = extracted.to_pandas()
    
    # Validate data types (ensure they are strings)
    # This is a preliminary check; deeper validation happens in T013b
    for col in required_columns:
        if df[col].isna().any():
            logger.warning(f"Found {df[col].isna().sum()} null values in {col}. "
                           "These will be saved but may be filtered later.")
    
    # Save to Parquet
    try:
        df.to_parquet(output_path, index=False)
        logger.info(f"Successfully saved extracted data to {output_path}")
        logger.info(f"Shape: {df.shape}")
    except Exception as e:
        logger.error(f"Failed to save dataset to {output_path}: {e}")
        raise

def main():
    """Main entry point for the dataset ingestion script."""
    logger.info("Starting dataset ingestion process...")
    
    # 1. Ensure directories exist
    ensure_dirs()
    
    downloaded_files = []
    
    for dataset_id in DATASET_IDS:
        try:
            # Determine output filename
            safe_name = dataset_id.replace("/", "_").replace("-", "_")
            output_filename = f"{safe_name}.parquet"
            output_path = DATA_RAW_DIR / output_filename
            
            # Skip if already exists (idempotent)
            if output_path.exists():
                logger.warning(f"Skipping {dataset_id}: {output_path} already exists.")
                downloaded_files.append(output_path)
                continue
            
            # Fetch dataset
            ds = fetch_dataset(dataset_id, DATA_RAW_DIR)
            
            # Extract and save
            extract_code_columns(ds, output_path)
            downloaded_files.append(output_path)
            
        except Exception as e:
            logger.error(f"Critical error processing {dataset_id}: {e}")
            # Continue to next dataset if one fails, but log the failure
            continue

    if not downloaded_files:
        logger.error("No datasets were successfully downloaded. Exiting.")
        sys.exit(1)
    
    logger.info(f"Ingestion complete. Cached {len(downloaded_files)} files in {DATA_RAW_DIR}")
    for f in downloaded_files:
        logger.info(f"  - {f}")

if __name__ == "__main__":
    main()