"""
Task T001b: Create data directory: data/processed/

This script creates the 'data/processed' directory if it does not already exist.
It relies on the configuration and directory setup utilities defined in the project.
"""
import os
import sys
import logging
from pathlib import Path

from config import get_config, ensure_dirs
from utils import setup_logging, log_info

def create_processed_directory():
    """
    Creates the 'data/processed' directory structure.

    Returns:
        Path: The path to the created directory.
    """
    config = get_config()
    # Ensure the base data directory exists first
    data_root = config.get('data_root', 'data')
    base_path = Path(data_root)
    
    # Ensure base data directory exists
    if not base_path.exists():
        base_path.mkdir(parents=True, exist_ok=True)
        log_info(f"Created base data directory: {base_path}")

    processed_dir = base_path / "processed"
    
    if not processed_dir.exists():
        processed_dir.mkdir(parents=True, exist_ok=True)
        log_info(f"Successfully created directory: {processed_dir}")
    else:
        log_info(f"Directory already exists: {processed_dir}")
        
    return processed_dir

def main():
    """
    Entry point for the T001b task execution.
    """
    # Setup logging
    log_level = get_config().get('log_level', 'INFO')
    setup_logging(level=log_level)
    
    log_info("Starting T001b: Create data/processed/ directory")
    
    try:
        result_path = create_processed_directory()
        log_info(f"T001b completed successfully. Path: {result_path}")
        return 0
    except Exception as e:
        log_info(f"T001b failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
