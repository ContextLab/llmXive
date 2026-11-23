"""
Script to execute the atlas download and verification process.
This script is called by the main pipeline or can be run standalone.
"""
import sys
import os
import logging
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.download_atlas import main

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    exit_code = main()
    sys.exit(exit_code)