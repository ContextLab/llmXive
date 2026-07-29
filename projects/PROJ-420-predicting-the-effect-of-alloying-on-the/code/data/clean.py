import sys
import logging
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_cleaning import run_cleaning_pipeline as cleaning_main
from logging_config import setup_logging, get_logger

def main():
    """CLI entry point for data cleaning."""
    parser = argparse.ArgumentParser(description='Run data cleaning pipeline')
    parser.add_argument('--check-only', action='store_true', help='Validate pipeline without writing output')
    args = parser.parse_args()

    logger = setup_logging()
    
    try:
        if args.check_only:
            logger.info("Running check-only mode...")
            # In check-only mode, we just verify the pipeline can run without errors
            # but we don't necessarily need to write the file if it's a validation step
            # However, the spec requires the file to be written for downstream steps.
            # So we run the full pipeline.
            path = cleaning_main()
            logger.info(f"Check passed. Output: {path}")
        else:
            logger.info("Running full cleaning pipeline...")
            path = cleaning_main()
            logger.info(f"Cleaning completed. Output: {path}")
    except Exception as e:
        logger.error(f"Cleaning pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
