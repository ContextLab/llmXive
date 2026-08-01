"""
Task T001c: Create data/results directory.

This script ensures the existence of the `data/results/` directory
as required by the project's data organization structure.
"""
import os
import sys
import logging
from pathlib import Path

# Ensure we can import from the project root if this script is run directly
# In a standard setup, the project root is in sys.path
try:
    from config import get_config, ensure_dirs
    from utils import setup_logging, log_info, log_warning
except ImportError:
    # Fallback for direct execution if path is not set correctly
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import get_config, ensure_dirs
    from utils import setup_logging, log_info, log_warning


def create_results_directory():
    """
    Creates the `data/results/` directory if it does not exist.
    
    Returns:
        bool: True if the directory was created or already exists, False on error.
    """
    config = get_config()
    if not config:
        log_error("Configuration could not be loaded.")
        return False

    # Define the path relative to the project root or data root
    # Typically data/results is a subdirectory of the data folder
    data_root = config.get('data_root', 'data')
    results_path = Path(data_root) / 'results'

    log_info(f"Ensuring existence of results directory: {results_path}")
    
    try:
        ensure_dirs([results_path])
        log_info(f"Successfully created or verified: {results_path}")
        return True
    except Exception as e:
        log_error(f"Failed to create results directory {results_path}: {e}")
        return False


def main():
    """Main entry point for the task."""
    # Setup logging
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    setup_logging(level=log_level)
    
    log_info("Starting T001c: Create data/results directory")
    
    success = create_results_directory()
    
    if success:
        log_info("T001c completed successfully.")
        return 0
    else:
        log_error("T001c failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
