import os
import sys
import logging
from pathlib import Path
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp
from config import get_config, ensure_dirs

def create_contracts_directory():
    """
    Creates the contracts/ directory structure if it does not exist.
    This directory will hold schema definitions (dataset.schema.yaml, output.schema.yaml).
    
    Returns:
        Path: The absolute path to the created contracts directory.
    """
    config = get_config()
    contracts_dir = config.get('contracts_dir', Path('contracts'))
    
    # Ensure the parent directory exists (project root)
    if not contracts_dir.parent.exists():
        contracts_dir.parent.mkdir(parents=True, exist_ok=True)
        log_info(f"Created project root directory: {contracts_dir.parent}")
    
    # Create the contracts directory
    contracts_dir.mkdir(parents=True, exist_ok=True)
    log_info(f"Contracts directory created/verified: {contracts_dir}")
    
    # Create subdirectories for schema versions if needed (future-proofing)
    # For now, we keep schemas at the root of contracts/
    return contracts_dir

def main():
    """
    Main entry point for T007: Setup contracts directory structure.
    """
    logger = setup_logging("T007_setup_contracts")
    log_info(f"Starting T007: Setup contracts directory structure at {get_timestamp()}")
    
    try:
        contracts_dir = create_contracts_directory()
        log_info(f"T007 completed successfully. Contracts directory: {contracts_dir}")
        return 0
    except Exception as e:
        log_error(f"T007 failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
