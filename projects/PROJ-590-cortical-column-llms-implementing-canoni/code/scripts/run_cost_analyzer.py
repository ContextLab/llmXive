"""
Script to run the Cost Analyzer (T076).
Executes the computation of cost metrics and writes to data/results/cost_metrics.json.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.experiments.cost_analyzer import main as cost_analyzer_main

def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting Cost Analyzer (T076)...")
    
    exit_code = cost_analyzer_main()
    
    if exit_code == 0:
        logger.info("Cost analysis completed successfully.")
    else:
        logger.error("Cost analysis failed.")
    
    return exit_code

if __name__ == "__main__":
    sys.exit(main())