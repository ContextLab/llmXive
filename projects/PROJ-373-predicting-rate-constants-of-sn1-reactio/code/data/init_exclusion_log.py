import os
import sys
import logging
from pathlib import Path
from config import ensure_dirs, DataConfig
from utils.logger import get_logger

def initialize_exclusion_log():
    """
    Initialize the exclusion log file with the required header.
    This ensures the file exists and is ready for appending by downstream tasks.
    """
    config = DataConfig()
    output_path = Path(config.processed_dir) / "exclusion_raw.log"
    
    # Ensure directory exists
    ensure_dirs()
    
    # Setup logger
    logger = get_logger("init_exclusion_log")
    
    # Check if file already exists
    if output_path.exists():
        logger.warning(f"Exclusion log {output_path} already exists. Overwriting to ensure clean state.")
    else:
        logger.info(f"Creating new exclusion log at {output_path}")
    
    # Write header explicitly
    # Using CSV format as per schema: row_index,reason,original_smiles
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            f.write("row_index,reason,original_smiles\n")
        logger.info("Successfully initialized exclusion log with headers.")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize exclusion log: {e}")
        return False

def main():
    """
    Entry point for the script.
    """
    logger = get_logger("init_exclusion_log")
    logger.info("Starting exclusion log initialization...")
    
    success = initialize_exclusion_log()
    
    if success:
        logger.info("Exclusion log initialization completed successfully.")
        sys.exit(0)
    else:
        logger.error("Exclusion log initialization failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
