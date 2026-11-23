"""
Script to run the alpha sensitivity analysis (T035).
This script is intended to be run after the LMM analysis (T025/T026) has produced results.
It reads the model results and generates data/processed/sensitivity_analysis.csv.
"""
import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.models.metrics import main as run_sensitivity_main
from code.config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting Alpha Sensitivity Analysis (T035)...")
    
    # Run the main logic from metrics.py
    try:
        run_sensitivity_main()
        logger.info("Sensitivity analysis completed successfully.")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()