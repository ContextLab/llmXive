"""
T016: Generate cleaned_data.csv
Orchestrates the final join and filtering steps to produce the cleaned dataset.
"""
import os
import sys
import logging
from pathlib import Path

# Ensure parent directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import ensure_directories
from ingestion import generate_cleaned_data
from utils import get_logger

def main():
    """
    Main entry point for T016.
    Loads intermediate data, applies final filters (zero-variance), and writes cleaned_data.csv.
    """
    logger = get_logger("T016_CleanedDataGeneration")
    logger.info("Starting T016: Generating cleaned_data.csv")

    # Ensure output directories exist
    ensure_directories()
    output_path = Path("data/processed/cleaned_data.csv")

    try:
        # Call the ingestion function that performs the join, motion exclusion,
        # and zero-variance checks, returning the final DataFrame.
        # This function logs exclusions to data/logs/exclusions.log internally.
        df_clean = generate_cleaned_data()

        if df_clean is None or df_clean.empty:
            logger.error("No data remaining after exclusions. Aborting write.")
            sys.exit(1)

        # Verify required columns exist
        required_cols = [
            "Subject_ID", "Global_Signal_SD", "MWQ_Score",
            "Age", "Sex", "Mean_FD", "Mean_DVARS"
        ]
        missing_cols = [c for c in required_cols if c not in df_clean.columns]
        if missing_cols:
            logger.error(f"Missing required columns in output: {missing_cols}")
            sys.exit(1)

        # Select and order columns
        df_output = df_clean[required_cols]

        # Write to disk
        df_output.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote {len(df_output)} rows to {output_path}")
        logger.info("T016 completed successfully.")

    except Exception as e:
        logger.error(f"Failed to generate cleaned data: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
