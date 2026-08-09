"""
Task T001b: Create data directory: data/processed/

This script ensures the existence of the 'data/processed' directory,
which is used for storing intermediate and cleaned datasets during
the research pipeline.
"""
import os
import sys
import logging
from pathlib import Path

# Import project utilities
from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning

def create_processed_directory():
    """
    Creates the data/processed directory if it does not exist.
    
    Returns:
        Path: The path to the created (or existing) directory.
        
    Raises:
        RuntimeError: If the directory cannot be created.
    """
    config = get_config()
    # Ensure the base data directory exists first
    ensure_dirs()
    
    processed_dir = Path(config.get('paths', {}).get('processed', 'data/processed'))
    
    if not processed_dir.exists():
        try:
            processed_dir.mkdir(parents=True, exist_ok=True)
            log_info(f"Created directory: {processed_dir}")
        except OSError as e:
            log_error(f"Failed to create directory {processed_dir}: {e}")
            raise RuntimeError(f"Failed to create data/processed directory: {e}")
    else:
        log_info(f"Directory already exists: {processed_dir}")
        
    return processed_dir

def main():
    """Entry point for T001b task."""
    # Setup logging
    log_level = getattr(logging, get_config().get('log_level', 'INFO'))
    setup_logging(level=log_level)
    
    log_info("Starting Task T001b: Create data/processed directory")
    
    try:
        path = create_processed_directory()
        log_info(f"Task T001b completed successfully. Directory: {path}")
        return 0
    except Exception as e:
        log_critical(f"Task T001b failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
