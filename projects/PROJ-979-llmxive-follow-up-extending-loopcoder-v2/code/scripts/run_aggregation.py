"""
Script to run T016: Aggregate results.
Executes the aggregation module to merge entropy, convergence, exclusion,
and significance data into a single analysis_summary.json.
"""
import os
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from aggregation import main as run_aggregation

def main():
    """Entry point for aggregation script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting T016: Aggregate Results")
    
    try:
        run_aggregation()
        logger.info("T016 completed successfully")
        return 0
    except Exception as e:
        logger.error(f"T016 failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())