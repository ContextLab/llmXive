"""
Data Ingestion Module for Macaron-A2UI Study.

This module fetches the raw A2UI-Bench dataset from Hugging Face
and outputs a raw CSV file to the data directory.
"""
import os
import sys
import argparse
from pathlib import Path

import pandas as pd
from datasets import load_dataset

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from config import DATA_DIR, RANDOM_SEED
from utils.logging import get_experiment_logger, log_error, log_info

# Initialize logger
logger = get_experiment_logger(__name__)

# Constants
DATASET_NAME = "macaron-a2ui/a2ui-bench"
OUTPUT_FILENAME = "raw_a2ui_bench.csv"
REQUIRED_COLUMNS = ["query", "intent", "context"]  # Expected columns from the dataset

def load_dataset_from_hf() -> pd.DataFrame:
    """
    Load the A2UI-Bench dataset from Hugging Face.

    Returns:
        pd.DataFrame: The loaded dataset as a DataFrame.

    Raises:
        RuntimeError: If the dataset cannot be fetched or processed.
                    This function fails loudly with no synthetic fallback.
    """
    logger.info(f"Fetching dataset: {DATASET_NAME}")
    try:
        # Load the dataset using the streaming flag to handle potential size issues
        # We load the 'train' split by default, but this can be adjusted if the dataset structure differs
        dataset = load_dataset(DATASET_NAME, split="train", streaming=False)
        
        # Convert to pandas DataFrame
        df = dataset.to_pandas()
        
        if df.empty:
            error_msg = f"Dataset {DATASET_NAME} loaded successfully but returned an empty DataFrame."
            log_error(logger, error_msg)
            raise RuntimeError(error_msg)
        
        logger.info(f"Successfully loaded {len(df)} rows from {DATASET_NAME}")
        return df
    except Exception as e:
        error_msg = f"Failed to fetch or process dataset {DATASET_NAME}: {str(e)}"
        log_error(logger, error_msg)
        # Fail loudly as per Data Hygiene rules - no synthetic fallback
        raise RuntimeError(error_msg) from e

def validate_dataframe(df: pd.DataFrame) -> bool:
    """
    Validate that the DataFrame contains necessary columns.
    
    Args:
        df: The DataFrame to validate.
        
    Returns:
        bool: True if valid, False otherwise.
    """
    if df.empty:
        logger.warning("Loaded dataset is empty.")
        return False
    
    # Check for at least one column that looks like a query
    if "query" not in df.columns:
        # Try to find a column that might be the query (common aliases)
        possible_query_cols = [c for c in df.columns if "query" in c.lower() or "text" in c.lower()]
        if not possible_query_cols:
            logger.error(f"Could not identify a 'query' column. Available columns: {list(df.columns)}")
            return False
        else:
            logger.info(f"Mapping column '{possible_query_cols[0]}' to 'query'.")
            df["query"] = df[possible_query_cols[0]]
    
    return True

def save_raw_csv(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the DataFrame to a CSV file.
    
    Args:
        df: The DataFrame to save.
        output_path: The path to save the CSV file.
    """
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved raw dataset to {output_path}")

def main():
    """Main entry point for data ingestion."""
    parser = argparse.ArgumentParser(description="Ingest A2UI-Bench dataset.")
    parser.add_argument(
        "--output", 
        type=str, 
        default=None, 
        help="Optional custom output path for the CSV file."
    )
    args = parser.parse_args()

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = DATA_DIR / OUTPUT_FILENAME

    logger.info(f"Ingesting dataset to: {output_path}")

    try:
        # 1. Load data
        df = load_dataset_from_hf()
        
        # 2. Validate data
        if not validate_dataframe(df):
            raise ValueError("Dataset validation failed. Check logs for details.")
        
        # 3. Save data
        save_raw_csv(df, output_path)
        
        logger.info("Ingestion completed successfully.")
        
    except Exception as e:
        log_error(logger, f"Ingestion failed: {str(e)}")
        # Re-raise to ensure the script exits with non-zero status
        raise

if __name__ == "__main__":
    main()