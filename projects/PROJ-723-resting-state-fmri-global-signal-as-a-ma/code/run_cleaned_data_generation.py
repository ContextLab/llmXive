"""
Script to generate the cleaned dataset for User Story 1.

This script executes the final steps of the ingestion pipeline:
1. Loads pre-processed data (after motion exclusion and zero-variance checks).
2. Selects the required columns.
3. Writes the final `data/processed/cleaned_data.csv`.

Dependencies:
- ingestion.py: Provides `generate_cleaned_data` which assumes upstream steps
  (motion exclusion T014, zero-variance T015) have been applied.
- config.py: Provides paths.
- utils.py: Provides logging and file I/O.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import ensure_directories
from ingestion import generate_cleaned_data
from utils import get_logger

def main():
    logger = get_logger("cleaned_data_generation")
    logger.info("Starting cleaned data generation (Task T016).")

    # Ensure output directories exist
    ensure_directories()

    # The generate_cleaned_data function in ingestion.py is designed to:
    # 1. Read the intermediate data (post-exclusion).
    # 2. Ensure columns match the schema: Subject_ID, Global_Signal_SD, MWQ_Score, Age, Sex, Mean_FD, Mean_DVARS.
    # 3. Write to data/processed/cleaned_data.csv.
    # It relies on the fact that T014 (motion exclusion) and T015 (zero-variance)
    # have already been executed to filter the data before this step.
    
    try:
        output_path = generate_cleaned_data()
        logger.info(f"Successfully generated cleaned data at: {output_path}")
        
        # Verify the file exists and is not empty
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output file {output_path} was not created.")
        
        import pandas as pd
        df = pd.read_csv(output_path)
        logger.info(f"Output verification: {len(df)} rows, columns: {list(df.columns)}")
        
        return 0
    except Exception as e:
        logger.error(f"Failed to generate cleaned data: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
