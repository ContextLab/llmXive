"""
Cleaning Pipeline Runner for T032.

This script aggregates the cleaning steps (PII removal and incomplete record handling)
implemented in code/analysis.py to produce the final cleaned dataset CSV.

It depends on:
- T033: Checks validation status via 'data/processed/validation_report.json'.
- T032a/T032b: Utilizes functions from code/analysis.py.
"""

import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Import cleaning logic from analysis module
# Based on API surface: from analysis import validate_input_data, handle_incomplete_records, save_cleaned_dataset_csv
from code.analysis import (
    load_json_file,
    remove_pii,
    handle_incomplete_records,
    save_cleaned_dataset_csv
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_validation_status(validation_report_path: str) -> bool:
    """
    Checks if the validation report indicates success.
    Blocks pipeline if validation failed (T033 dependency).
    """
    if not os.path.exists(validation_report_path):
        logger.error(f"Validation report not found at {validation_report_path}. "
                     "Did T033 run successfully?")
        return False

    try:
        with open(validation_report_path, 'r') as f:
            report = json.load(f)

        status = report.get('status', 'unknown')
        if status == 'passed':
            logger.info("Validation check passed. Proceeding with cleaning.")
            return True
        else:
            logger.error(f"Validation check FAILED with status: {status}. "
                         "Aborting cleaning pipeline.")
            return False
    except Exception as e:
        logger.error(f"Error reading validation report: {e}")
        return False

def run_cleaning_pipeline(
    raw_data_path: str,
    cleaned_output_path: str,
    validation_report_path: str
) -> bool:
    """
    Executes the cleaning pipeline:
    1. Verify validation passed.
    2. Load raw data.
    3. Remove PII (T032a).
    4. Handle incomplete records (T032b).
    5. Save to CSV.
    """
    # 1. Check Validation
    if not check_validation_status(validation_report_path):
        return False

    if not os.path.exists(raw_data_path):
        logger.error(f"Raw data file not found at {raw_data_path}.")
        return False

    logger.info(f"Loading raw data from {raw_data_path}...")
    try:
        raw_data = load_json_file(raw_data_path)
    except Exception as e:
        logger.error(f"Failed to load raw data: {e}")
        return False

    if not raw_data:
        logger.warning("Raw data is empty. Creating empty cleaned dataset.")
        # Create empty CSV with headers if possible, or just return success
        # Assuming standard headers based on spec
        save_cleaned_dataset_csv([], cleaned_output_path)
        return True

    # 2. Remove PII (T032a)
    logger.info("Removing PII...")
    try:
        cleaned_data = remove_pii(raw_data)
    except Exception as e:
        logger.error(f"Failed during PII removal: {e}")
        return False

    # 3. Handle Incomplete Records (T032b)
    logger.info("Handling incomplete records...")
    try:
        final_data, dropouts = handle_incomplete_records(cleaned_data)
        logger.info(f"Processed {len(cleaned_data)} records. "
                    f"Kept {len(final_data)} for analysis. "
                    f"Flagged {len(dropouts)} as dropouts.")
    except Exception as e:
        logger.error(f"Failed during incomplete record handling: {e}")
        return False

    # 4. Save to CSV (T032 Output)
    logger.info(f"Saving cleaned dataset to {cleaned_output_path}...")
    try:
        save_cleaned_dataset_csv(final_data, cleaned_output_path)
        logger.info("Cleaning pipeline completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to save cleaned dataset: {e}")
        return False

def main():
    """
    Main entry point for the cleaning pipeline.
    Uses default paths defined in the project structure.
    """
    # Define paths relative to project root
    # Ensure we are running from the project root or adjust paths accordingly
    base_dir = Path(__file__).parent.parent
    data_dir = base_dir / "data"
    
    raw_data_path = str(data_dir / "raw" / "participant_logs.json")
    cleaned_output_path = str(data_dir / "processed" / "cleaned_dataset.csv")
    validation_report_path = str(data_dir / "processed" / "validation_report.json")

    success = run_cleaning_pipeline(
        raw_data_path=raw_data_path,
        cleaned_output_path=cleaned_output_path,
        validation_report_path=validation_report_path
    )

    if not success:
        sys.exit(1)
    else:
        print(f"Pipeline finished. Output written to {cleaned_output_path}")

if __name__ == "__main__":
    main()
