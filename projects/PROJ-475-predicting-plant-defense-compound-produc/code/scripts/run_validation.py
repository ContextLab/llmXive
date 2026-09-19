"""
Script to run the Validation Pipeline (T013, T014, T015).
"""
import sys
import logging
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import configure_root_logger
from data.validation import run_validation_pipeline

def main():
    configure_root_logger()
    logger = logging.getLogger(__name__)
    logger.info("Running Validation Pipeline (T013, T014, T015)...")
    
    try:
        run_validation_pipeline()
        logger.info("Validation Pipeline completed successfully.")
        return 0
    except SystemExit as e:
        if str(e) == "E-DATA-INSUFFICIENT":
            logger.error("Validation failed: Retention below threshold.")
            return 1
        raise
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())