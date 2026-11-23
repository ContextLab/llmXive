"""
Script to generate T027 Sensitivity Analysis.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd

code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

from src.models.evaluate import load_sensitivity_sweep_data, calculate_stability_and_flip_rate, flag_threshold_sensitive, generate_sensitivity_analysis
from src.utils import get_logger

def main():
    logger = get_logger(__name__)
    logger.info("Generating Sensitivity Analysis (T027)")
    try:
        generate_sensitivity_analysis()
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
