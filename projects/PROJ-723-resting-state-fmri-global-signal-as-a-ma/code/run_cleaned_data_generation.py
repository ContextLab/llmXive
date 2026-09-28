"""
Script to execute the generation of cleaned_data.csv.
This script orchestrates the final steps of the US1 pipeline:
1. Ensures output directories exist.
2. Calls generate_cleaned_data() from ingestion.py.
3. Writes the final DataFrame to data/processed/cleaned_data.csv.
"""
import os
import sys
import logging
from pathlib import Path

from config import ensure_directories
from ingestion import generate_cleaned_data

def main():
    logger = logging.getLogger(__name__)
    logger.info("Starting cleaned data generation (T016).")

    # Ensure output directory exists
    output_path = Path("data/processed/cleaned_data.csv")
    ensure_directories(output_path)

    # Generate the cleaned dataset
    # This function assumes all previous steps (T009-T015) have been executed
    # and the intermediate data is available or re-computed as needed within ingestion.py.
    try:
        df = generate_cleaned_data()
        
        if df is None or df.empty:
            logger.error("generate_cleaned_data returned an empty or None DataFrame.")
            sys.exit(1)

        # Write to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote cleaned data to {output_path}")
        logger.info(f"Output shape: {df.shape}")
        logger.info(f"Columns: {list(df.columns)}")
        
    except Exception as e:
        logger.error(f"Failed to generate cleaned data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()
