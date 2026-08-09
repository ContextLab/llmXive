"""
Task T020c: Generate Blocked Diversity Artifact.

This script is triggered when T012a (Data Feasibility) or T012d (Schema Verification) fails.
It creates a placeholder CSV file at data/processed/diversity_results.csv indicating
that the pipeline could not proceed due to missing data.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd

# Ensure the project root is in the path to import config if needed,
# though this script writes a static file structure.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def generate_blocked_diversity_artifact():
    """
    Creates the blocked diversity results CSV.
    """
    logger.info("Starting generation of blocked diversity artifact (T020c).")

    # Ensure directory exists
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    output_path = DATA_PROCESSED_DIR / "diversity_results.csv"

    # Define the required columns for the blocked state
    # The task description specifies: status, reason, and empty diversity columns (shannon, simpson, observed_otus).
    # We will also include sample_id to match the schema of a real diversity result file.
    columns = [
        "sample_id",
        "shannon",
        "simpson",
        "observed_otus",
        "status",
        "reason"
    ]

    # Create an empty DataFrame with the specified columns
    # We do not add any data rows; the file represents a "blocked" state with 0 valid samples.
    df = pd.DataFrame(columns=columns)

    # Add the metadata row (optional but helpful for human verification of the block state)
    # Some pipelines prefer a single row explaining the block, others an empty file with headers.
    # The task says "empty diversity columns", implying no data rows.
    # However, to make the "status" and "reason" visible in a CSV reader, we might add one metadata row
    # or rely on the file header and a separate JSON report.
    # Given the strict requirement "Create ... with status: 'blocked', reason: '...', and empty diversity columns",
    # we will create a file with headers and NO data rows, as data rows imply samples.
    # The status/reason are structural properties of the file's existence and content state.
    # If a row is strictly required to carry the status, we add one row with sample_id="BLOCKED_STATUS".
    
    # Re-reading the task: "Create ... with status: 'blocked', reason: '...', and empty diversity columns".
    # This implies the columns exist. Let's add a single metadata row to ensure the status is readable
    # if the file is opened as a table, as "empty file with headers" might be ambiguous.
    # We'll use a special ID to denote this is a status record, not a sample.
    
    blocked_row = {
        "sample_id": "BLOCKED_STATUS",
        "shannon": None,
        "simpson": None,
        "observed_otus": None,
        "status": "blocked",
        "reason": "No verified data source found"
    }
    df = pd.DataFrame([blocked_row])

    # Write to CSV
    try:
        df.to_csv(output_path, index=False)
        logger.info(f"Successfully wrote blocked diversity artifact to {output_path}")
        
        # Verify file exists
        if output_path.exists():
            logger.info("Verification: File exists on disk.")
            # Log file size
            size = output_path.stat().st_size
            logger.info(f"Verification: File size is {size} bytes.")
        else:
            logger.error("Verification failed: File does not exist after write.")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Failed to write blocked diversity artifact: {e}")
        return False

def main():
    success = generate_blocked_diversity_artifact()
    if not success:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()