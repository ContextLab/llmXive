import os
import sys
import logging
from pathlib import Path
from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning

def create_stimuli_directory():
    """
    Creates the data/stimuli/ directory if it does not exist.
    Returns the Path object of the created directory.
    """
    config = get_config()
    data_root = config.get('paths', {}).get('data', 'data')
    stimuli_path = Path(data_root) / 'stimuli'
    
    log_info(f"Ensuring stimuli directory exists at: {stimuli_path}")
    
    # ensure_dirs creates the directory structure if it doesn't exist
    ensure_dirs([stimuli_path])
    
    if not stimuli_path.exists():
        log_error(f"Failed to create stimuli directory: {stimuli_path}")
        return None
    
    log_info(f"Stimuli directory ready: {stimuli_path}")
    return stimuli_path

def main():
    """Entry point for task T001e execution."""
    # Setup logging
    log_level = get_config().get('logging', {}).get('level', 'INFO')
    logger = setup_logging(level=log_level)
    
    log_info("Starting task T001e: Create stimuli directory")
    
    result_path = create_stimuli_directory()
    
    if result_path:
        log_info("Task T001e completed successfully.")
        return 0
    else:
        log_error("Task T001e failed to create the stimuli directory.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
