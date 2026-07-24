"""
Entry point script to execute the checksumming process on the initial data structure.

This script imports the main execution logic from the data_checksum_manager module
and runs it to verify the integrity of files in the data/ directory.

Usage:
    python code/run_checksums.py
"""

import sys
import logging
from pathlib import Path

# Ensure the code directory is in the path for imports
# This allows importing modules relative to the project root if run from there
# or relative to the code directory if run directly.
# Given the project structure, we assume this script is run from the project root.

# Import the main function from the data_checksum_manager module
# The path is relative to the project root, but since this file is in code/,
# we need to handle imports carefully.
# The provided API surface shows 'from data_checksum_manager import main'.
# This implies data_checksum_manager is in the code/ directory.

try:
    from data_checksum_manager import main as checksum_main
except ImportError:
    # Fallback if run as a script from code/ directory directly
    # Adjust sys.path to include the current directory
    sys.path.insert(0, str(Path(__file__).parent))
    from data_checksum_manager import main as checksum_main

def main():
    """
    Main entry point for the checksum execution script.
    
    Calls the checksum_main function from data_checksum_manager to
    compute and store checksums for all files in the data/ directory.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting checksum verification on initial data structure...")
    
    try:
        # Execute the checksumming logic
        checksum_main()
        logger.info("Checksum verification completed successfully.")
    except Exception as e:
        logger.error(f"Checksum verification failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()