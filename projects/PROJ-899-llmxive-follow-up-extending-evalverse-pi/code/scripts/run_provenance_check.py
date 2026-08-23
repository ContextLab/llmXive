"""
Script to run the provenance verification check for the EvalVerse dataset.

This script is invoked by the pipeline to verify that the downloaded dataset
matches the expected DOI and URL configuration.
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
    Wrapper function for the provenance check script.
    Sets up logging and calls the main verification function.
    """
    setup_logging(level="INFO")
    return main()


if __name__ == "__main__":
    exit_code = main_wrapper()
    sys.exit(exit_code)
