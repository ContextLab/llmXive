import os
import sys
import logging
from analyzer import analyze_and_export

def main():
    """
    Entry point for running the regression analysis task (T027).
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting T027: Regression Analysis Script")
    
    try:
        analyze_and_export()
        logger.info("T027 execution completed successfully.")
    except Exception as e:
        logger.error(f"T027 execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
