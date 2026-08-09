"""
Task T001c: Create data directory: data/results/

This script ensures the existence of the 'data/results/' directory,
which is used to store statistical reports, sensitivity analysis outputs,
and final paper artifacts.
"""
import os
import sys
import logging
from pathlib import Path

# Add the project root to the path to allow relative imports if needed,
# though this script primarily uses standard library and config.
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning

def create_results_directory():
    """
    Creates the data/results/ directory if it does not exist.
    
    Returns:
        Path: The path to the created (or existing) directory.
    
    Raises:
        OSError: If the directory cannot be created due to permissions or other system errors.
    """
    config = get_config()
    # The ensure_dirs function in config.py handles the creation of standard directories.
    # We explicitly ensure the results directory exists here as per the task requirement.
    # It relies on the 'results_dir' key in the config.
    
    results_dir = config.get('results_dir')
    
    if not results_dir:
        # Fallback to default if not explicitly set in config, though config.py should handle this
        results_dir = project_root / 'data' / 'results'
    else:
        results_dir = Path(results_dir)

    log_info(f"Ensuring directory exists: {results_dir}")
    
    try:
        results_dir.mkdir(parents=True, exist_ok=True)
        log_info(f"Successfully ensured directory exists: {results_dir}")
        return results_dir
    except OSError as e:
        log_error(f"Failed to create directory {results_dir}: {e}")
        raise

def main():
    """Main entry point for Task T001c."""
    logger = setup_logging()
    log_info("Starting Task T001c: Create data/results/ directory")
    
    try:
        dir_path = create_results_directory()
        log_info(f"Task T001c completed successfully. Directory: {dir_path}")
        
        # Verify existence as a final check
        if dir_path.exists() and dir_path.is_dir():
            log_info("Verification: Directory exists and is a valid directory.")
            return 0
        else:
            log_error("Verification failed: Directory was not created correctly.")
            return 1
            
    except Exception as e:
        log_error(f"Task T001c failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())