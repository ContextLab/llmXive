import os
import sys
import logging
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_and_verify_behavioral_scores(raw_data_dir: str, processed_data_path: str):
    """
    Extracts behavioral scores from parquet files in the raw data directory and saves them to a CSV file.
    Verifies the existence of the 'wcst_perseverative_errors' column before extraction.

    Args:
        raw_data_dir (str): Path to the directory containing raw parquet files.
        processed_data_path (str): Path to save the processed behavioral scores CSV file.
    """
    try:
        # Find all parquet files in the raw data directory
        parquet_files = list(Path(raw_data_dir).glob("*.parquet"))

        if not parquet_files:
            logger.warning("No parquet files found in the raw data directory.")
            return

        # Read the first parquet file to check for 'wcst_perseverative_errors' column
        first_file = parquet_files[0]
        try:
            df = pd.read_parquet(first_file)
            if 'wcst_perseverative_errors' not in df.columns:
                logger.error("The 'wcst_perseverative_errors' column is missing in the dataset.")
                raise ValueError("Missing required variable")  # Raise exception to halt execution

        except Exception as e:
            logger.error(f"Error reading parquet file {first_file}: {e}")
            return

        # Extract behavioral scores from all parquet files
        all_scores = []
        for file in parquet_files:
            try:
                df = pd.read_parquet(file)
                # Select relevant columns (adjust as needed based on actual data)
                behavioral_data = df[['subject_id', 'age', 'wcst_perseverative_errors']]
                all_scores.append(behavioral_data)

            except Exception as e:
                logger.error(f"Error reading parquet file {file}: {e}")

        if not all_scores:
            logger.warning("No behavioral scores extracted.")
            return

        # Concatenate all dataframes
        combined_df = pd.concat(all_scores, ignore_index=True)

        # Save the combined dataframe to a CSV file
        combined_df.to_csv(processed_data_path, index=False)
        logger.info(f"Behavioral scores saved to: {processed_data_path}")

    except Exception as e:
        logger.error(f"An error occurred during behavioral score extraction and verification: {e}")


if __name__ == "__main__":
    raw_data_dir = "data/raw/"  # Replace with your raw data directory
    processed_data_path = "data/processed/behavioral_scores.csv"
    extract_and_verify_behavioral_scores(raw_data_dir, processed_data_path)