"""
T011d: Initialize the exclusion raw log file.

Logic:
1. Create an empty CSV file with headers: row_index, reason, original_smiles.
2. Explicitly write the header row.
3. Guard: Check data/processed/.pipeline_status.
   - If 'ABORTED', exit with code 1 (do not create the file).
   - If 'OK', proceed.
   - If missing, treat as fatal error (pipeline not started).
4. Output: data/processed/exclusion_raw.log
"""
import os
import sys
import logging
import csv
from pathlib import Path

# Import config utilities
from config import ensure_dirs, DataConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_pipeline_status() -> bool:
    """
    Checks the pipeline status file.
    Returns True if status is 'OK', False otherwise.
    """
    status_path = Path("data/processed/.pipeline_status")
    if not status_path.exists():
        logger.error("Pipeline status file not found. Pipeline has not been initialized.")
        return False
    
    try:
        status = status_path.read_text().strip()
        if status == 'ABORTED':
            logger.error("Pipeline status is ABORTED. Stopping initialization.")
            return False
        if status == 'OK':
            return True
        logger.warning(f"Unknown pipeline status: '{status}'. Proceeding with caution.")
        return True
    except Exception as e:
        logger.error(f"Error reading pipeline status: {e}")
        return False

def initialize_exclusion_log() -> bool:
    """
    Main logic to initialize the exclusion log.
    """
    # Guard: Check pipeline status first
    if not check_pipeline_status():
        return False

    output_path = Path("data/processed/exclusion_raw.log")
    
    # Ensure directory exists
    ensure_dirs(output_path.parent)

    logger.info(f"Initializing exclusion log at: {output_path}")
    
    try:
        # Write the header row explicitly
        with open(output_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['row_index', 'reason', 'original_smiles'])
        
        logger.info(f"Successfully initialized exclusion log with headers.")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize exclusion log: {e}")
        return False

def main():
    """
    CLI entry point.
    """
    logger.info("Starting exclusion log initialization...")
    
    success = initialize_exclusion_log()
    
    if success:
        logger.info("Exclusion log initialization completed successfully.")
        sys.exit(0)
    else:
        logger.error("Exclusion log initialization failed or was aborted.")
        sys.exit(1)

if __name__ == "__main__":
    main()
