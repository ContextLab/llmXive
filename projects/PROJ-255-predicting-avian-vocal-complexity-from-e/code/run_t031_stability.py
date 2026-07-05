import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.analysis.stability import main
from src.utils.logging import setup_logger

def main_wrapper():
    """Wrapper for T031 stability analysis execution."""
    logger = setup_logger("T031_Stability")
    logger.info("Starting T031: Stability Metric Calculation")
    
    try:
        result_path = main()
        logger.info(f"T031 completed successfully. Output: {result_path}")
        return 0
    except Exception as e:
        logger.error(f"T031 failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main_wrapper())