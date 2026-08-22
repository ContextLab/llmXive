"""
Script to run the provenance verification check.
This script invokes the verify_provenance module and handles logging setup.
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.verify_provenance import main
from src.utils import setup_logging


def main_wrapper():
    """
    Wrapper function to set up logging and run the provenance check.
    """
    # Set up logging
    setup_logging(level="INFO")
    
    # Run the provenance check
    main()


if __name__ == "__main__":
    main_wrapper()
