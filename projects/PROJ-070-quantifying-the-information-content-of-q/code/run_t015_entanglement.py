"""
Runner script for T015: Bipartite Entanglement Entropy Calculation.
This script aggregates wavefunctions from data/raw (produced by T013/T014)
and computes entanglement entropy, writing results to data/processed/entanglement_metrics.csv.
"""
import sys
import os

# Ensure project root is in path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from metrics import main as run_entanglement_calculation
from logging_config import setup_logging, logger

def main():
    setup_logging()
    logger.info("Executing T015 Runner Script")
    try:
        run_entanglement_calculation()
        logger.info("T015 Execution Successful")
    except Exception as e:
        logger.error(f"T015 Execution Failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
