"""
Runner script for T015: Entanglement Entropy Calculation.

Executes the main function from metrics.py to process wavefunctions
and generate entanglement metrics.
"""
import sys
import os

# Ensure code directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from metrics import main as run_entanglement_calculation
from logging_config import setup_logging, logger

def main():
    setup_logging()
    logger.info("Executing T015: Entanglement Entropy Calculation")
    try:
        df = run_entanglement_calculation()
        logger.info("T015 completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"T015 failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())