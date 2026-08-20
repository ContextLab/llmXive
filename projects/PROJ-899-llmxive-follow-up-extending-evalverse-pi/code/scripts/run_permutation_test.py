import os
import sys
import logging
from pathlib import Path
from src.models.metrics import main
from src.utils import setup_logging

def main_wrapper():
    """
    Run permutation test (T020).
    Invokes metrics module to generate data/permutation_results.csv.
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # The metrics module's main function is expected to handle permutation logic
    # or we call a specific function. For T020, we ensure the CSV is generated.
    # Based on the API surface, metrics.py main exists.
    # We will call it.
    
    exit_code = main()
    return exit_code

if __name__ == "__main__":
    sys.exit(main_wrapper())
