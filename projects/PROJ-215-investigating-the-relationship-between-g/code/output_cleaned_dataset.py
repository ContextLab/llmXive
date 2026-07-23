import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

from config import get_output_path
from preprocessing import run_preprocessing

def load_preprocessed_data(file_path):
    """Loads the preprocessed dataset from a CSV file."""
    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        logging.error(f"Preprocessed data not found at {file_path}")
        raise

def merge_and_filter(df):
    """Merges required columns and filters for valid rows."""
    # Assuming the dataframe has alpha diversity metrics (e.g., Shannon, Simpson)
    # and other relevant metadata.  Adjust column names as needed.
    if 'Shannon' not in df.columns or 'PHQ9' not in df.columns:
        logging.error("Required columns ('Shannon', 'PHQ9') missing.")
        raise ValueError("Required columns are missing from the dataframe.")

    # Filter out rows with any missing values in key columns
    df = df.dropna(subset=['Shannon', 'PHQ9'])
    return df


def verify_retention(original_rows, filtered_rows):
    """Verifies that at least 80% of the original data is retained."""
    retention_rate = (filtered_rows / original_rows) * 100
    if retention_rate < 80:
        logging.warning(f"Retention rate is below 80%: {retention_rate:.2f}%")
        return False
    else:
        return True

def main():
    """Main function to output the cleaned dataset and verify retention."""
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    processed_data_path = Path("data/processed/preprocessed_dataset.csv") # Assuming this is the output from T016
    if not processed_data_path.exists():
        logger.error(f"Preprocessed data file not found: {processed_data_path}")
        sys.exit(1)

    try:
      df = load_preprocessed_data(processed_data_path)
    except Exception as e:
        logger.error(f"Error loading preprocessed data: {e}")
        sys.exit(1)


    original_rows = len(df)

    try:
        cleaned_df = merge_and_filter(df.copy())  # Work on a copy to avoid modifying the original dataframe
    except Exception as e:
        logger.error(f"Error merging and filtering data: {e}")
        sys.exit(1)

    valid_rows = len(cleaned_df)


    if valid_rows < 100:
        logger.warning(f"Number of valid rows is less than 100: {valid_rows}")

    retention_successful = verify_retention(original_rows, valid_rows)

    output_path = get_output_path("cleaned_dataset.csv") # Get output path from config
    try:
        cleaned_df.to_csv(output_path, index=False)
        logger.info(f"Cleaned dataset saved to {output_path}")
    except Exception as e:
        logger.error(f"Error saving cleaned dataset: {e}")
        sys.exit(1)

    if retention_successful and valid_rows >= 100:
        logger.info("Task completed successfully.")
    else:
        logger.warning("Task completed with warnings (retention or row count).")

if __name__ == "__main__":
    main()