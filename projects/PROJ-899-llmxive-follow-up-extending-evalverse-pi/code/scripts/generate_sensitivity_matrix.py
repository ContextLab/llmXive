"""
Script to generate T028 Sensitivity Matrix.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd

code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

from src.models.evaluate import generate_full_sensitivity_matrix
from src.utils import get_logger

def main():
    logger = get_logger(__name__)
    logger.info("Generating Sensitivity Matrix (T028)")
    try:
        generate_full_sensitivity_matrix()
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()