"""
Script to generate the pilot dataset for T016.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data_generation import main

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run():
    """Run the dataset generation."""
    logger.info("Starting pilot dataset generation for T016")
    main()
    logger.info("Dataset generation completed")

if __name__ == '__main__':
    run()
