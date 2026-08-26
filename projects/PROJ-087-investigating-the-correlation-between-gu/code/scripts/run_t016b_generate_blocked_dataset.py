"""
T016b: Generate Blocked Cleaned Dataset.
Triggered automatically when T012a (Data Feasibility Check) or T012d (Schema Verification) fails.

This script creates a placeholder CSV file with the expected schema but marks the dataset as blocked.
It ensures that downstream tasks (T020a, T025, T031) have a file to reference, even if the data pipeline
could not proceed due to missing real data sources.

Output: data/processed/cleaned_microbiome_sleep.csv
"""
import os
import sys
import logging
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add parent directory to path to allow imports if run as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def generate_blocked_cleaned_dataset(output_dir: str, reason: str = "No verified data source found") -> Path:
    """
    Generate a blocked cleaned dataset CSV with the required schema.
    
    Args:
        output_dir: Directory to save the CSV file.
        reason: The reason for the block status.
        
    Returns:
        Path to the generated CSV file.
        
    Raises:
        RuntimeError: If the output directory cannot be created.
    """
    # Define the required columns based on task description
    columns = [
        'sample_id',
        'age',
        'bmi',
        'antibiotic_use_last_3m',
        'sleep_efficiency',
        'sleep_duration_hours',
        'shannon',
        'simpson',
        'observed_otus'
    ]
    
    # Create an empty DataFrame with the correct schema and a 'status' column
    df = pd.DataFrame(columns=columns + ['status', 'block_reason'])
    
    # Add the blocked status to every row (though there are none)
    # The file will be empty of data rows but have the correct header
    # We will add a single comment row or just rely on the header + metadata file
    # Per spec: "empty rows" -> 0 data rows.
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    csv_path = output_path / "cleaned_microbiome_sleep.csv"
    
    # Write the CSV with the header only (no data rows)
    # We include the status and reason in the header or a separate metadata file?
    # The task says: "Create ... with status: 'blocked', reason: '...', and empty rows."
    # Best practice: Write header + 0 rows, and ensure the ingestion_report.json (T017b) carries the reason.
    # However, to be explicit in the CSV as requested, we can add a row with NA values and status.
    # But "empty rows" usually implies 0 data rows. Let's stick to 0 data rows but ensure the file exists.
    # The "status" and "reason" are primarily for the ingestion report, but if we must put them in CSV:
    # We will write the header, and 0 rows. The existence of the file with this schema signals the block.
    
    df.to_csv(csv_path, index=False)
    
    logger.info(f"Generated blocked dataset at {csv_path} with {len(df)} rows.")
    logger.info(f"Reason for block: {reason}")
    
    return csv_path

def main():
    """Main entry point for T016b."""
    config = load_config()
    output_dir = config.get('OUTPUT_DIR', 'data/processed')
    reason = config.get('BLOCK_REASON', "No verified data source found")
    
    logger.info(f"Starting T016b: Generate Blocked Cleaned Dataset")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Block reason: {reason}")
    
    try:
        csv_path = generate_blocked_cleaned_dataset(output_dir, reason)
        logger.info(f"SUCCESS: Blocked dataset created at {csv_path}")
        return 0
    except Exception as e:
        logger.error(f"FAILED: Could not generate blocked dataset: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())