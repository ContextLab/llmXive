"""
Script to execute the Preprocessing Pipeline (T027).

This script is invoked by the quickstart run-book to generate
data/processed/alloys_raw.csv.
"""

import logging
import sys
from pathlib import Path

# Add code to path if not already present
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.preprocessing.preprocess_pipeline import main as run_pipeline
from src.utils.logging_config import setup_logging

def main():
    """Main entry point for the script."""
    setup_logging(log_file=Path("data/logs/run_preprocessing.log"))
    logger = logging.getLogger(__name__)
    
    logger.info("Executing Preprocessing Pipeline (T027)...")
    try:
        run_pipeline()
        logger.info("Preprocessing Pipeline executed successfully.")
    except Exception as e:
        logger.error(f"Preprocessing Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()