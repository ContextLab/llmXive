"""
Script to initialize the project directory structure.
Creates all required directories for the llmXive pipeline.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.utils.logging import setup_logging, get_logger
from code.utils.directories import create_all_directories

def main():
    """Initialize the project directory structure."""
    logger = setup_logging()
    logger.info("Starting directory structure initialization...")
    
    # Create all required directories
    create_all_directories()
    
    logger.info("Directory structure initialization completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
